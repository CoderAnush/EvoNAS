"""PyTorch evaluation engine."""

from __future__ import annotations

import logging

import numpy as np
import torch
from torch import nn

from evonas.domain.common.errors import EvaluationError
from evonas.domain.data.models import DatasetHandle
from evonas.domain.metrics.classification import compute_classification_metrics
from evonas.domain.training.types import EvaluationResult, MetricSet
from evonas.infrastructure.data.checksums import sha256_array
from evonas.infrastructure.training.torch_data import make_dataloader
from evonas.ports.training import ITrainableModel

logger = logging.getLogger(__name__)


class PyTorchEvaluationEngine:
    """Evaluate a trainable model on a DatasetHandle."""

    def __init__(self, *, criterion: nn.Module | None = None) -> None:
        self._criterion = criterion or nn.CrossEntropyLoss()

    @torch.no_grad()
    def evaluate(
        self,
        model: ITrainableModel,
        data: DatasetHandle,
        *,
        device: str | None = None,
        batch_size: int = 32,
    ) -> EvaluationResult:
        """Return loss, classification metrics, and confusion matrix."""
        if data.is_empty():
            raise EvaluationError("cannot evaluate empty dataset")
        dev = torch.device(device or "cpu")
        model = model.to(dev)
        model.eval()
        loader = make_dataloader(data, batch_size=batch_size, shuffle=False, num_workers=0)

        losses: list[float] = []
        y_true: list[np.ndarray] = []
        y_pred: list[np.ndarray] = []
        try:
            for xb, yb in loader:
                xb = xb.to(dev)
                yb = yb.to(dev)
                logits = model(xb)
                loss = self._criterion(logits, yb)
                losses.append(float(loss.item()))
                preds = torch.argmax(logits, dim=1)
                y_true.append(yb.detach().cpu().numpy())
                y_pred.append(preds.detach().cpu().numpy())
        except Exception as exc:  # noqa: BLE001
            raise EvaluationError(f"evaluation failed: {exc}") from exc

        yt = np.concatenate(y_true)
        yp = np.concatenate(y_pred)
        num_classes = int(data.schema.num_classes or int(max(yt.max(), yp.max()) + 1))
        metric_set: MetricSet = compute_classification_metrics(yt, yp, num_classes=num_classes)
        mean_loss = float(np.mean(losses)) if losses else 0.0
        cm = metric_set.extras.get("confusion_matrix", [])
        result = EvaluationResult(
            metrics=metric_set,
            loss=mean_loss,
            n_samples=int(yt.shape[0]),
            confusion_matrix=cm,
            predictions_checksum=sha256_array(yp.astype(np.int64)),
        )
        logger.info(
            "Evaluated n=%d loss=%.4f accuracy=%.4f",
            result.n_samples,
            result.loss,
            result.metrics.values.get("accuracy", 0.0),
        )
        return result
