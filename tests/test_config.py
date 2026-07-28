"""Configuration manager tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from evonas.domain.common.errors import ConfigError
from evonas.infrastructure.config.manager import ConfigurationManager


def test_load_and_hash_stable(tmp_path: Path) -> None:
    cfg = {
        "name": "x",
        "input_shape": [2, 2, 1],
        "splits": {"train": 0.7, "val": 0.2, "test": 0.1},
        "seed": 1,
        "b": 2,
        "a": 1,
    }
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    mgr = ConfigurationManager()
    loaded = mgr.load(path)
    mgr.validate(loaded)
    h1 = mgr.hash(loaded)
    h2 = mgr.hash(
        {
            "a": 1,
            "b": 2,
            "name": "x",
            "input_shape": [2, 2, 1],
            "splits": loaded["splits"],
            "seed": 1,
        }
    )
    assert h1 == h2


def test_validate_rejects_bad_splits() -> None:
    mgr = ConfigurationManager()
    with pytest.raises(ConfigError):
        mgr.validate(
            {
                "name": "x",
                "input_shape": [1],
                "splits": {"train": 0.5, "val": 0.5, "test": 0.5},
                "seed": 1,
            }
        )


def test_get_dotted_key() -> None:
    mgr = ConfigurationManager()
    assert mgr.get("splits.train", {"splits": {"train": 0.7}}) == 0.7
