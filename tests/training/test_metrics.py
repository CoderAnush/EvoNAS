"""Unit tests for classification metrics."""

from __future__ import annotations

import numpy as np

from evonas.domain.metrics import (
    Accuracy,
    F1Macro,
    PrecisionMacro,
    RecallMacro,
    compute_classification_metrics,
    confusion_matrix,
)


def test_accuracy_perfect() -> None:
    y = np.array([0, 1, 2, 1])
    assert Accuracy().compute(y, y) == 1.0


def test_confusion_and_metric_set() -> None:
    y_true = np.array([0, 0, 1, 1, 2])
    y_pred = np.array([0, 1, 1, 1, 2])
    cm = confusion_matrix(y_true, y_pred, num_classes=3)
    assert cm.shape == (3, 3)
    ms = compute_classification_metrics(y_true, y_pred, num_classes=3)
    assert "accuracy" in ms.values
    assert PrecisionMacro().compute(y_true, y_pred) >= 0.0
    assert RecallMacro().compute(y_true, y_pred) >= 0.0
    assert F1Macro().compute(y_true, y_pred) >= 0.0
