"""Training / evaluation domain types (framework-agnostic)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TrainConfig:
    """Budget and hyperparameter contract for a training run."""

    epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 1e-3
    optimizer: str = "adam"
    weight_decay: float = 0.0
    device: str = "cpu"
    seed: int = 42
    early_stopping_patience: int | None = None
    checkpoint_every: int = 1
    num_workers: int = 0
    shuffle_train: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for experiment records."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrainConfig:
        """Build from a configuration mapping."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass(slots=True)
class MetricSet:
    """Scalar and structured metrics from an evaluation pass."""

    primary: str
    values: dict[str, float]
    extras: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str, default: float | None = None) -> float | None:
        """Fetch a scalar metric by name."""
        if name in self.values:
            return self.values[name]
        return default

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics."""
        return {"primary": self.primary, "values": dict(self.values), "extras": dict(self.extras)}


@dataclass(slots=True)
class EvaluationResult:
    """Structured evaluation output consumed by experiment recording."""

    metrics: MetricSet
    loss: float
    n_samples: int
    confusion_matrix: list[list[int]]
    predictions_checksum: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize evaluation result."""
        return {
            "metrics": self.metrics.to_dict(),
            "loss": self.loss,
            "n_samples": self.n_samples,
            "confusion_matrix": self.confusion_matrix,
            "predictions_checksum": self.predictions_checksum,
        }


@dataclass(slots=True)
class EpochReport:
    """Per-epoch training / validation summary."""

    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float | None = None
    val_accuracy: float | None = None
    seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize epoch report."""
        return asdict(self)


@dataclass(slots=True)
class TrainedModelArtifact:
    """Result of a training run (idea.md Training Engine contract)."""

    weights_uri: str
    best_weights_uri: str
    architecture_name: str
    architecture_id: str
    train_metrics: MetricSet
    val_metrics: MetricSet | None
    epochs_ran: int
    stopped_reason: str
    device: str
    backend_name: str
    param_count: int
    history: list[EpochReport] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize artifact metadata (not weight tensors)."""
        return {
            "weights_uri": self.weights_uri,
            "best_weights_uri": self.best_weights_uri,
            "architecture_name": self.architecture_name,
            "architecture_id": self.architecture_id,
            "train_metrics": self.train_metrics.to_dict(),
            "val_metrics": self.val_metrics.to_dict() if self.val_metrics else None,
            "epochs_ran": self.epochs_ran,
            "stopped_reason": self.stopped_reason,
            "device": self.device,
            "backend_name": self.backend_name,
            "param_count": self.param_count,
            "history": [h.to_dict() for h in self.history],
            "metadata": self.metadata,
        }
