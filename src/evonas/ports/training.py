"""Training / evaluation / model-builder ports (idea.md §21.9–21.10, Phase 2)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from evonas.domain.data.models import DatasetHandle
from evonas.domain.model.architecture_spec import ArchitectureSpec
from evonas.domain.training.types import (
    EvaluationResult,
    TrainConfig,
    TrainedModelArtifact,
)


@runtime_checkable
class ITrainableModel(Protocol):
    """Backend-agnostic trainable model contract.

    Trainers depend only on this interface. Future CNN / MLP / ViT models
    implement the same surface so they remain interchangeable.
    """

    def parameters(self) -> Any:
        """Return iterable of trainable parameters (framework-specific)."""

    def train(self, mode: bool = True) -> Any:
        """Set training mode."""

    def eval(self) -> Any:
        """Set evaluation mode."""

    def to(self, device: Any) -> Any:
        """Move model to a device."""

    def state_dict(self) -> dict[str, Any]:
        """Serialize weights."""

    def load_state_dict(self, state: dict[str, Any], strict: bool = True) -> Any:
        """Restore weights."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Forward pass."""


@runtime_checkable
class IModelBuilder(Protocol):
    """Build a concrete trainable model from an ArchitectureSpec."""

    def build(self, spec: ArchitectureSpec) -> ITrainableModel:
        """Instantiate a model for ``spec``."""

    def count_parameters(self, model: ITrainableModel) -> int:
        """Return number of trainable parameters."""


@runtime_checkable
class ITrainingEngine(Protocol):
    """Train a model under a budgeted TrainConfig."""

    def train(
        self,
        spec: ArchitectureSpec,
        train_data: DatasetHandle,
        val_data: DatasetHandle | None,
        train_config: TrainConfig,
        *,
        run_context: dict[str, Any] | None = None,
    ) -> TrainedModelArtifact:
        """Execute training and return a TrainedModelArtifact."""


@runtime_checkable
class IEvaluationEngine(Protocol):
    """Evaluate a trained model on a dataset handle."""

    def evaluate(
        self,
        model: ITrainableModel,
        data: DatasetHandle,
        *,
        device: str | None = None,
        batch_size: int = 32,
    ) -> EvaluationResult:
        """Return structured evaluation metrics."""


@runtime_checkable
class ICheckpointManager(Protocol):
    """Persist and restore training checkpoints."""

    def save(self, name: str, state: dict[str, Any]) -> str:
        """Save checkpoint ``name``; return URI/path."""

    def load(self, uri: str) -> dict[str, Any]:
        """Load checkpoint state from URI/path."""

    def list(self) -> list[str]:
        """List available checkpoint names/URIs."""
