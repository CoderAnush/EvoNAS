"""CLI smoke tests."""

from __future__ import annotations

from evonas.presentation.cli.main import main


def test_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "0.1.0"


def test_help_exit_zero() -> None:
    assert main([]) == 0
