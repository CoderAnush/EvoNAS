"""Experiment recorder — AutoML experiment metadata foundation."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.training.types import EvaluationResult, TrainConfig, TrainedModelArtifact
from evonas.infrastructure.experiments.artifact_manager import ArtifactManager

logger = logging.getLogger(__name__)


@dataclass
class ExperimentRecord:
    """Structured record for a baseline (and future AutoML) run."""

    run_id: str
    run_dir: str
    model_name: str
    architecture_id: str
    dataset_name: str
    hyperparameters: dict[str, Any]
    metrics: dict[str, Any]
    training_seconds: float
    artifact_paths: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize experiment record."""
        return {
            "run_id": self.run_id,
            "run_dir": self.run_dir,
            "model_name": self.model_name,
            "architecture_id": self.architecture_id,
            "dataset_name": self.dataset_name,
            "hyperparameters": self.hyperparameters,
            "metrics": self.metrics,
            "training_seconds": self.training_seconds,
            "artifact_paths": self.artifact_paths,
            "metadata": self.metadata,
        }


class ExperimentRecorder:
    """Record model / dataset / hyperparameters / metrics / artifact paths."""

    def __init__(self, artifacts: ArtifactManager | None = None) -> None:
        self._artifacts = artifacts or ArtifactManager()

    def start(self, run_id: str | None = None) -> Path:
        """Create a new run directory and return it."""
        return self._artifacts.create_run(run_id)

    def finalize(
        self,
        *,
        run_dir: Path,
        spec: ArchitectureSpec,
        dataset_name: str,
        train_config: TrainConfig,
        artifact: TrainedModelArtifact,
        test_result: EvaluationResult | None,
        training_seconds: float,
        extra: dict[str, Any] | None = None,
    ) -> ExperimentRecord:
        """Persist metrics.json + experiment.json and return the record."""
        metrics: dict[str, Any] = {
            "train": artifact.train_metrics.to_dict(),
            "val": artifact.val_metrics.to_dict() if artifact.val_metrics else None,
            "test": test_result.to_dict() if test_result else None,
            "history": [h.to_dict() for h in artifact.history],
            "param_count": artifact.param_count,
            "epochs_ran": artifact.epochs_ran,
            "stopped_reason": artifact.stopped_reason,
        }
        self._artifacts.write_json(run_dir, "metrics.json", metrics)
        self._artifacts.write_json(run_dir, "history.json", {"epochs": metrics["history"]})

        record = ExperimentRecord(
            run_id=run_dir.name,
            run_dir=str(run_dir),
            model_name=spec.name,
            architecture_id=spec.arch_id(),
            dataset_name=dataset_name,
            hyperparameters=train_config.to_dict(),
            metrics=metrics,
            training_seconds=float(training_seconds),
            artifact_paths={
                "weights": artifact.weights_uri,
                "best_weights": artifact.best_weights_uri,
                "metrics": str(run_dir / "metrics.json"),
                "history": str(run_dir / "history.json"),
            },
            metadata={
                "architecture": spec.to_dict(),
                "backend": artifact.backend_name,
                "device": artifact.device,
                **(extra or {}),
            },
        )
        self._artifacts.write_json(run_dir, "experiment.json", record.to_dict())
        logger.info(
            "Recorded experiment run_id=%s train_acc=%.4f seconds=%.2f",
            record.run_id,
            artifact.train_metrics.values.get("accuracy", -1.0),
            training_seconds,
        )
        return record


class Timer:
    """Simple wall-clock timer for experiment recording."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    def elapsed(self) -> float:
        """Seconds since construction."""
        return float(time.perf_counter() - self._start)
