"""Reusable classification metrics (numpy) for trainers and future SAPSO fitness."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from evonas.domain.training.types import MetricSet


class Metric(ABC):
    """Base metric — single responsibility per concrete class."""

    name: str

    @abstractmethod
    def compute(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute scalar metric from integer label arrays."""


@dataclass(frozen=True, slots=True)
class Accuracy(Metric):
    """Classification accuracy."""

    name: str = "accuracy"

    def compute(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        if y_true.size == 0:
            return 0.0
        return float(np.mean(y_true == y_pred))


@dataclass(frozen=True, slots=True)
class PrecisionMacro(Metric):
    """Macro-averaged precision."""

    name: str = "precision_macro"

    def compute(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return _macro_prf(y_true, y_pred, kind="precision")


@dataclass(frozen=True, slots=True)
class RecallMacro(Metric):
    """Macro-averaged recall."""

    name: str = "recall_macro"

    def compute(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return _macro_prf(y_true, y_pred, kind="recall")


@dataclass(frozen=True, slots=True)
class F1Macro(Metric):
    """Macro-averaged F1 score."""

    name: str = "f1_macro"

    def compute(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return _macro_prf(y_true, y_pred, kind="f1")


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    """Compute an integer confusion matrix of shape (C, C)."""
    y_true = np.asarray(y_true, dtype=np.int64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.int64).ravel()
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred, strict=True):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            cm[t, p] += 1
    return cm


def _macro_prf(y_true: np.ndarray, y_pred: np.ndarray, *, kind: str) -> float:
    y_true = np.asarray(y_true, dtype=np.int64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.int64).ravel()
    classes = np.unique(np.concatenate([y_true, y_pred]))
    scores: list[float] = []
    for c in classes:
        tp = float(np.sum((y_pred == c) & (y_true == c)))
        fp = float(np.sum((y_pred == c) & (y_true != c)))
        fn = float(np.sum((y_pred != c) & (y_true == c)))
        if kind == "precision":
            scores.append(tp / (tp + fp) if (tp + fp) > 0 else 0.0)
        elif kind == "recall":
            scores.append(tp / (tp + fn) if (tp + fn) > 0 else 0.0)
        else:
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            scores.append(2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0)
    return float(np.mean(scores)) if scores else 0.0


DEFAULT_CLASSIFICATION_METRICS: tuple[Metric, ...] = (
    Accuracy(),
    PrecisionMacro(),
    RecallMacro(),
    F1Macro(),
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    num_classes: int,
    metrics: tuple[Metric, ...] | None = None,
    primary: str = "accuracy",
) -> MetricSet:
    """Compute a MetricSet plus confusion matrix extras."""
    metric_objs = metrics or DEFAULT_CLASSIFICATION_METRICS
    values = {m.name: float(m.compute(y_true, y_pred)) for m in metric_objs}
    cm = confusion_matrix(y_true, y_pred, num_classes)
    return MetricSet(
        primary=primary,
        values=values,
        extras={"confusion_matrix": cm.tolist()},
    )
