"""PyTorch training engine — reusable Phase 2 trainer (idea.md ITrainingEngine)."""

from __future__ import annotations

import logging
import random
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch
from torch import nn

from evonas.domain.common.errors import TrainingError
from evonas.domain.data.models import DatasetHandle
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.training.types import EpochReport, MetricSet, TrainConfig, TrainedModelArtifact
from evonas.infrastructure.checkpoint.file_checkpoint_manager import FileCheckpointManager
from evonas.infrastructure.training.model_factory import ModelFactory
from evonas.infrastructure.training.pytorch_evaluator import PyTorchEvaluationEngine
from evonas.infrastructure.training.torch_data import make_dataloader
from evonas.ports.training import IModelBuilder, ITrainableModel

logger = logging.getLogger(__name__)

EpochCallback = Callable[[EpochReport], None]


class PyTorchTrainingEngine:
    """Production-shaped training loop over Phase 1 dataset handles.

    Responsibilities: init model, epoch/batch loops, optimizer step, validation,
    checkpointing, logging, and progress callbacks. Does not perform NAS/PSO.
    """

    backend_name = "pytorch"

    def __init__(
        self,
        *,
        model_factory: ModelFactory | None = None,
        builder: IModelBuilder | None = None,
        evaluator: PyTorchEvaluationEngine | None = None,
        checkpoint_manager: FileCheckpointManager | None = None,
        on_epoch_end: EpochCallback | None = None,
    ) -> None:
        self._factory = model_factory or ModelFactory()
        self._builder = builder or self._factory.builder("pytorch")
        self._evaluator = evaluator or PyTorchEvaluationEngine()
        self._checkpoints = checkpoint_manager
        self._on_epoch_end = on_epoch_end
        self._criterion = nn.CrossEntropyLoss()

    def train(
        self,
        spec: ArchitectureSpec,
        train_data: DatasetHandle,
        val_data: DatasetHandle | None,
        train_config: TrainConfig,
        *,
        run_context: dict[str, Any] | None = None,
    ) -> TrainedModelArtifact:
        """Train ``spec`` on ``train_data`` and optionally validate each epoch."""
        ctx = run_context or {}
        self._seed_everything(train_config.seed)
        device = torch.device(self._resolve_device(train_config.device))

        try:
            model = self._builder.build(spec)
            model = model.to(device)
            optimizer = self._build_optimizer(model, train_config)
        except TrainingError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise TrainingError(f"model/optimizer init failed: {exc}", code="EN_TRN_001") from exc

        train_loader = make_dataloader(
            train_data,
            batch_size=train_config.batch_size,
            shuffle=train_config.shuffle_train,
            num_workers=train_config.num_workers,
        )

        ckpt_root = Path(ctx.get("checkpoint_dir", "artifacts/baselines/_tmp_ckpts"))
        ckpt_mgr = self._checkpoints or FileCheckpointManager(ckpt_root)

        history: list[EpochReport] = []
        best_val = float("-inf")
        best_state: dict[str, Any] | None = None
        epochs_without_improve = 0
        stopped_reason = "max_epochs"
        latest_uri = ""
        best_uri = ""

        logger.info(
            "Training start model=%s device=%s epochs=%d batch=%d lr=%s n_train=%d",
            spec.name,
            device,
            train_config.epochs,
            train_config.batch_size,
            train_config.learning_rate,
            train_data.size,
        )

        for epoch in range(1, train_config.epochs + 1):
            t0 = time.perf_counter()
            train_loss, train_acc = self._train_one_epoch(model, train_loader, optimizer, device)
            val_loss: float | None = None
            val_acc: float | None = None
            if val_data is not None and not val_data.is_empty():
                val_result = self._evaluator.evaluate(
                    model,
                    val_data,
                    device=str(device),
                    batch_size=train_config.batch_size,
                )
                val_loss = val_result.loss
                val_acc = float(val_result.metrics.values.get("accuracy", 0.0))

            report = EpochReport(
                epoch=epoch,
                train_loss=train_loss,
                train_accuracy=train_acc,
                val_loss=val_loss,
                val_accuracy=val_acc,
                seconds=time.perf_counter() - t0,
            )
            history.append(report)
            logger.info(
                "Epoch %d/%d train_loss=%.4f train_acc=%.4f val_loss=%s val_acc=%s (%.2fs)",
                epoch,
                train_config.epochs,
                train_loss,
                train_acc,
                f"{val_loss:.4f}" if val_loss is not None else "n/a",
                f"{val_acc:.4f}" if val_acc is not None else "n/a",
                report.seconds,
            )
            if self._on_epoch_end:
                self._on_epoch_end(report)

            # Track best by validation accuracy when available, else train accuracy.
            score = val_acc if val_acc is not None else train_acc
            improved = score > best_val + 1e-12
            if improved:
                best_val = score
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                epochs_without_improve = 0
            else:
                epochs_without_improve += 1

            if epoch % max(1, train_config.checkpoint_every) == 0:
                latest_uri = ckpt_mgr.save(
                    "latest",
                    {
                        "model_state": model.state_dict(),
                        "optimizer_state": optimizer.state_dict(),
                        "epoch": epoch,
                        "architecture_id": spec.arch_id(),
                        "train_config": train_config.to_dict(),
                        "best_val": best_val,
                    },
                )
                if best_state is not None:
                    best_uri = ckpt_mgr.save(
                        "best",
                        {
                            "model_state": best_state,
                            "epoch": epoch,
                            "architecture_id": spec.arch_id(),
                            "best_val": best_val,
                            "train_config": train_config.to_dict(),
                        },
                    )

            patience = train_config.early_stopping_patience
            if patience is not None and epochs_without_improve >= patience:
                stopped_reason = "early_stopping"
                logger.info("Early stopping at epoch=%d patience=%d", epoch, patience)
                break

        if best_state is not None:
            model.load_state_dict(best_state)

        # Final train / val metric snapshots
        final_train = self._evaluator.evaluate(
            model, train_data, device=str(device), batch_size=train_config.batch_size
        )
        final_val_metrics: MetricSet | None = None
        if val_data is not None and not val_data.is_empty():
            final_val = self._evaluator.evaluate(
                model, val_data, device=str(device), batch_size=train_config.batch_size
            )
            final_val_metrics = final_val.metrics

        if not best_uri and best_state is not None:
            best_uri = ckpt_mgr.save(
                "best",
                {
                    "model_state": best_state,
                    "epoch": history[-1].epoch if history else 0,
                    "architecture_id": spec.arch_id(),
                    "best_val": best_val,
                    "train_config": train_config.to_dict(),
                },
            )
        if not latest_uri:
            latest_uri = ckpt_mgr.save(
                "latest",
                {
                    "model_state": model.state_dict(),
                    "epoch": history[-1].epoch if history else 0,
                    "architecture_id": spec.arch_id(),
                    "train_config": train_config.to_dict(),
                    "best_val": best_val,
                },
            )

        artifact = TrainedModelArtifact(
            weights_uri=latest_uri,
            best_weights_uri=best_uri or latest_uri,
            architecture_name=spec.name,
            architecture_id=spec.arch_id(),
            train_metrics=final_train.metrics,
            val_metrics=final_val_metrics,
            epochs_ran=len(history),
            stopped_reason=stopped_reason,
            device=str(device),
            backend_name=self.backend_name,
            param_count=self._builder.count_parameters(model),
            history=history,
            metadata={"run_context": ctx},
        )
        logger.info(
            "Training complete epochs=%d reason=%s train_acc=%.4f best_uri=%s",
            artifact.epochs_ran,
            stopped_reason,
            artifact.train_metrics.values.get("accuracy", 0.0),
            artifact.best_weights_uri,
        )
        return artifact

    def _train_one_epoch(
        self,
        model: ITrainableModel,
        loader: Any,
        optimizer: torch.optim.Optimizer,
        device: torch.device,
    ) -> tuple[float, float]:
        model.train(True)
        total_loss = 0.0
        correct = 0
        total = 0
        try:
            for xb, yb in loader:
                xb = xb.to(device)
                yb = yb.to(device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(xb)
                loss = self._criterion(logits, yb)
                if not torch.isfinite(loss):
                    raise TrainingError("non-finite loss encountered", code="EN_TRN_002")
                loss.backward()
                optimizer.step()
                total_loss += float(loss.item()) * int(yb.size(0))
                preds = torch.argmax(logits, dim=1)
                correct += int((preds == yb).sum().item())
                total += int(yb.size(0))
        except TrainingError:
            raise
        except RuntimeError as exc:
            if "out of memory" in str(exc).lower():
                raise TrainingError("OOM during training", code="EN_TRN_001") from exc
            raise TrainingError(f"training step failed: {exc}", code="EN_TRN_001") from exc
        except Exception as exc:  # noqa: BLE001
            raise TrainingError(f"training step failed: {exc}", code="EN_TRN_001") from exc

        mean_loss = total_loss / max(total, 1)
        acc = correct / max(total, 1)
        return mean_loss, float(acc)

    def _build_optimizer(
        self,
        model: ITrainableModel,
        cfg: TrainConfig,
    ) -> torch.optim.Optimizer:
        params = [p for p in model.parameters() if p.requires_grad]
        name = cfg.optimizer.lower()
        if name == "sgd":
            return torch.optim.SGD(params, lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
        if name == "adamw":
            return torch.optim.AdamW(params, lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
        return torch.optim.Adam(params, lr=cfg.learning_rate, weight_decay=cfg.weight_decay)

    @staticmethod
    def _resolve_device(requested: str) -> str:
        if requested == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return requested

    @staticmethod
    def _seed_everything(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
