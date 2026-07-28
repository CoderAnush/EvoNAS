"""Shared enumerations for the data plane."""

from __future__ import annotations

from enum import Enum


class Split(str, Enum):
    """Dataset partition names."""

    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class TaskType(str, Enum):
    """Supported task types (Phase 1 focuses on classification)."""

    IMAGE_CLASSIFICATION = "image_classification"
    TABULAR_CLASSIFICATION = "tabular_classification"
    OTHER = "other"


class DatasetSource(str, Enum):
    """How raw samples are obtained."""

    SYNTHETIC = "synthetic"
    SYNTHETIC_MNIST_LIKE = "synthetic_mnist_like"
    SYNTHETIC_FASHION_MNIST_LIKE = "synthetic_fashion_mnist_like"
    SYNTHETIC_CIFAR10_LIKE = "synthetic_cifar10_like"
    TORCHVISION = "torchvision"
    LOCAL_FILES = "local_files"
