"""Factory and drift-detector Phase 1 gap-closure tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from evonas.domain.common.enums import Split
from evonas.domain.data.statistics import compute_data_stats
from evonas.infrastructure.data import (
    DefaultDriftDetector,
    create_dataset_manager,
    resolve_dataset_config_path,
)
from evonas.ports.dataset import IDriftDetector


def test_default_drift_detector_satisfies_port() -> None:
    assert isinstance(DefaultDriftDetector(), IDriftDetector)


def test_resolve_dataset_config_from_default_yaml() -> None:
    path = resolve_dataset_config_path("configs/default.yaml")
    assert path.as_posix().endswith("configs/datasets/toy_quick.yaml")


def test_create_dataset_manager_from_app_config(tmp_path: Path) -> None:
    mgr = create_dataset_manager("configs/default.yaml")
    # Redirect manifests into tmp via treating as dataset after load would
    # still write to artifacts; use treat_as with toy override.
    from evonas.infrastructure.config.manager import ConfigurationManager

    cfg = ConfigurationManager().load("configs/datasets/toy_quick.yaml")
    cfg = dict(cfg)
    cfg["name"] = "factory_toy"
    cfg["manifest_dir"] = str(tmp_path / "factory_toy")
    cfg["num_samples"] = 60
    mgr = create_dataset_manager(cfg, treat_as_dataset_config=True)
    mgr.prepare()
    assert mgr.load(Split.TRAIN).size > 0


def test_drift_detector_flags_shift() -> None:
    rng = np.random.default_rng(1)
    ref = rng.normal(0, 1, size=(100, 4))
    cur = rng.normal(4, 1, size=(100, 4))
    labels = np.zeros(100, dtype=np.int64)
    ref_s = compute_data_stats(ref, labels, split=Split.TRAIN, checksum="a", feature_bins=8)
    cur_s = compute_data_stats(cur, labels, split=Split.VAL, checksum="b", feature_bins=8)
    report = DefaultDriftDetector(psi_threshold=0.1, ks_p_threshold=0.05).detect(
        ref_s,
        cur_s,
        reference_features=ref,
        current_features=cur,
    )
    assert report.significant is True
