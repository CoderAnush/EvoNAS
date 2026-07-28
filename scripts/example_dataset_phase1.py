"""Example: prepare and inspect the Quick Mode toy dataset (Phase 1)."""

from __future__ import annotations

from pathlib import Path

from evonas.domain.common.enums import Split
from evonas.infrastructure.data import DatasetManager
from evonas.infrastructure.logging.setup import setup_logging


def main() -> None:
    """Run a minimal Phase 1 usage demo against configs/datasets/toy_quick.yaml."""
    setup_logging(level="INFO")
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs" / "datasets" / "toy_quick.yaml"

    manager = DatasetManager(config_path)
    manager.prepare()

    train = manager.load(Split.TRAIN)
    val = manager.load(Split.VAL)
    test = manager.load(Split.TEST)
    stats = manager.compute_statistics(Split.TRAIN)
    window = manager.get_window(0, min(16, train.size), split=Split.TRAIN)

    # Synthetic shift for drift demo: compare train vs a shifted copy of val features.
    shifted = val
    # Build a handle-like comparison using detect_shift on stats + features via handles
    report = manager.detect_shift(train, shifted)

    print("=== EvoNAS Phase 1 Dataset Example ===")
    print(f"dataset: {manager.name}")
    print(f"schema:  {manager.get_schema()}")
    print(f"sizes:   train={train.size} val={val.size} test={test.size}")
    print(f"checksums: {manager.checksums()}")
    print(f"train mean (first 3 dims): {stats.feature_mean[:3]}")
    print(f"window n={window.size} id={window.window_id}")
    print(f"drift significant={report.significant} psi={report.psi:.4f}")


if __name__ == "__main__":
    main()
