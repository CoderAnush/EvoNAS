"""Application use-case: train baseline end-to-end from YAML."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from evonas.domain.common.enums import Split
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.training.types import TrainConfig
from evonas.infrastructure.checkpoint.file_checkpoint_manager import FileCheckpointManager
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.data.factory import create_dataset_manager
from evonas.infrastructure.experiments.artifact_manager import ArtifactManager
from evonas.infrastructure.experiments.experiment_recorder import ExperimentRecorder, Timer
from evonas.infrastructure.training.model_factory import ModelFactory
from evonas.infrastructure.training.pytorch_evaluator import PyTorchEvaluationEngine
from evonas.infrastructure.training.pytorch_trainer import PyTorchTrainingEngine

logger = logging.getLogger(__name__)


class TrainBaselineUseCase:
    """Orchestrate Phase 1 data + Phase 2 train/eval/artifacts for the baseline."""

    def __init__(
        self,
        *,
        config_manager: ConfigurationManager | None = None,
        model_factory: ModelFactory | None = None,
        artifacts: ArtifactManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigurationManager()
        self._model_factory = model_factory or ModelFactory(config_manager=self._config_manager)
        self._artifacts = artifacts or ArtifactManager()
        self._recorder = ExperimentRecorder(self._artifacts)
        self._evaluator = PyTorchEvaluationEngine()

    def run(self, training_config_path: str | Path) -> dict[str, Any]:
        """Execute a full baseline training run from a training YAML path."""
        cfg_path = Path(training_config_path)
        cfg = self._config_manager.load(cfg_path)

        dataset_cfg = cfg.get("dataset", {})
        if isinstance(dataset_cfg, dict) and dataset_cfg.get("config_path"):
            data_mgr = create_dataset_manager(
                str(dataset_cfg["config_path"]),
                treat_as_dataset_config=True,
                config_manager=self._config_manager,
            )
        else:
            data_mgr = create_dataset_manager(
                str(cfg.get("app_config", "configs/default.yaml")),
                config_manager=self._config_manager,
            )

        data_mgr.prepare()
        train_h = data_mgr.load(Split.TRAIN)
        val_h = data_mgr.load(Split.VAL)
        test_h = data_mgr.load(Split.TEST)

        subset_frac = float(cfg.get("data", {}).get("subset_fraction", 1.0))
        subset_seed = int(cfg.get("data", {}).get("subset_seed", cfg.get("seed", 42)))
        if subset_frac < 1.0:
            train_h = data_mgr.subset(Split.TRAIN, subset_frac, subset_seed)
            logger.info("Using train subset fraction=%.3f n=%d", subset_frac, train_h.size)

        model_block = cfg.get("model", {}) if isinstance(cfg.get("model"), dict) else {}
        arch_path = model_block.get("architecture_path", "configs/models/baseline_cnn.yaml")
        spec = self._model_factory.load_spec(arch_path)
        schema = data_mgr.get_schema()
        if bool(model_block.get("align_with_dataset", True)):
            spec = ArchitectureSpec(
                name=spec.name,
                version=spec.version,
                task_type=spec.task_type,
                input_shape=schema.input_shape,
                num_classes=int(schema.num_classes or spec.num_classes),
                conv_blocks=spec.conv_blocks,
                dense_units=spec.dense_units,
                dropout=spec.dropout,
                metadata={**spec.metadata, "aligned_with_dataset": schema.name},
            )

        train_raw = dict(cfg.get("training", {}))
        if "seed" in cfg:
            train_raw["seed"] = int(cfg["seed"])
        train_cfg = TrainConfig.from_dict(train_raw)

        run_dir = self._recorder.start(cfg.get("run_id"))
        self._artifacts.copy_config(run_dir, cfg_path)
        (run_dir / "architecture.json").write_text(
            json.dumps(spec.to_dict(), indent=2),
            encoding="utf-8",
        )
        resolved = {
            "dataset": data_mgr.name,
            "dataset_checksums": data_mgr.checksums(),
            "architecture": spec.to_dict(),
            "training": train_cfg.to_dict(),
            "source_config": str(cfg_path),
        }
        (run_dir / "config.resolved.json").write_text(
            json.dumps(resolved, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        ckpt_mgr = FileCheckpointManager(run_dir / "checkpoints")
        trainer = PyTorchTrainingEngine(
            model_factory=self._model_factory,
            checkpoint_manager=ckpt_mgr,
        )

        timer = Timer()
        artifact = trainer.train(
            spec,
            train_h,
            val_h,
            train_cfg,
            run_context={
                "checkpoint_dir": str(run_dir / "checkpoints"),
                "run_dir": str(run_dir),
            },
        )

        model, _ = self._model_factory.create(spec, backend="pytorch")
        state = ckpt_mgr.load(artifact.best_weights_uri)
        model.load_state_dict(state["model_state"])
        eval_device = artifact.device if train_cfg.device == "auto" else train_cfg.device
        test_result = self._evaluator.evaluate(
            model,
            test_h,
            device=eval_device,
            batch_size=train_cfg.batch_size,
        )

        record = self._recorder.finalize(
            run_dir=run_dir,
            spec=spec,
            dataset_name=data_mgr.name,
            train_config=train_cfg,
            artifact=artifact,
            test_result=test_result,
            training_seconds=timer.elapsed(),
            extra={"config_hash": self._config_manager.hash(cfg)},
        )

        baseline_alias = Path("artifacts/baselines/baseline_v1")
        baseline_alias.mkdir(parents=True, exist_ok=True)
        metrics_alias = baseline_alias / "metrics.json"
        metrics_alias.write_text(
            (run_dir / "metrics.json").read_text(encoding="utf-8"), encoding="utf-8"
        )

        summary = {
            "run_id": record.run_id,
            "run_dir": str(run_dir),
            "metrics_path": str(run_dir / "metrics.json"),
            "baseline_metrics_alias": str(metrics_alias),
            "train_accuracy": artifact.train_metrics.values.get("accuracy"),
            "val_accuracy": (
                artifact.val_metrics.values.get("accuracy") if artifact.val_metrics else None
            ),
            "test_accuracy": test_result.metrics.values.get("accuracy"),
            "epochs_ran": artifact.epochs_ran,
            "param_count": artifact.param_count,
            "training_seconds": record.training_seconds,
        }
        logger.info("Baseline training finished: %s", summary)
        return summary
