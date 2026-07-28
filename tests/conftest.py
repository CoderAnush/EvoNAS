"""Shared pytest fixtures for Phase 1 data tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def toy_config(tmp_path: Path) -> dict:
    """Minimal synthetic dataset config writing manifests under tmp_path."""
    return {
        "name": "toy_test",
        "version": "1.0.0",
        "task_type": "image_classification",
        "source": "synthetic",
        "input_shape": [4, 4, 1],
        "num_classes": 3,
        "num_samples": 120,
        "dtype": "float32",
        "splits": {"train": 0.7, "val": 0.15, "test": 0.15},
        "seed": 11,
        "shuffle": True,
        "download": False,
        "transforms": {"normalize": True, "flatten": False},
        "statistics": {"compute_on_prepare": True, "feature_bins": 8},
        "drift": {"psi_threshold": 0.25, "ks_p_value": 0.01, "feature_bins": 8},
        "manifest_dir": str(tmp_path / "toy_test"),
    }


@pytest.fixture
def toy_config_path(tmp_path: Path, toy_config: dict) -> Path:
    """Write toy_config to a YAML file and return its path."""
    path = tmp_path / "toy_test.yaml"
    path.write_text(yaml.safe_dump(toy_config), encoding="utf-8")
    # Point manifest into tmp
    toy_config["manifest_dir"] = str(tmp_path / "datasets" / "toy_test")
    path.write_text(yaml.safe_dump(toy_config), encoding="utf-8")
    return path
