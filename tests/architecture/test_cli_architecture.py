"""CLI commands for Phase 3 architecture tooling."""

from __future__ import annotations

import json

import pytest

from evonas.presentation.cli.main import main


def test_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "0.9.0"


def test_validate_model_ok(capsys) -> None:
    assert main(["validate-model", "--config", "configs/models/baseline.yaml"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_inspect_model(capsys) -> None:
    assert main(["inspect-model", "--config", "configs/models/baseline.yaml"]) == 0
    out = capsys.readouterr().out
    assert "Architecture:" in out
    assert "↓" in out


def test_build_model(capsys) -> None:
    pytest.importorskip("torch")
    assert main(["build-model", "--config", "configs/models/baseline.yaml"]) == 0
    out = capsys.readouterr().out
    assert "arch_id" in out
