"""Registry domain types — metadata only (never mutates experiment results)."""

from __future__ import annotations

from enum import Enum


class RegistryKind(str, Enum):
    """Governed object kinds."""

    MODEL = "model"
    EXPERIMENT = "experiment"
    DATASET = "dataset"
    ARTIFACT = "artifact"
    PROMOTION = "promotion"
    ROLLBACK = "rollback"
    LIFECYCLE_EVENT = "lifecycle_event"


class LifecycleState(str, Enum):
    """Asset lifecycle states (Phase 11 governance)."""

    CREATED = "created"
    TRAINING = "training"
    EVALUATING = "evaluating"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    PROMOTED = "promoted"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"
    FAILED = "failed"
    DELETED = "deleted"


class ModelStage(str, Enum):
    """Model registry stages (idea.md §55)."""

    NONE = "none"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
