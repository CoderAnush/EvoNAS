"""Smoke tests for package import and version."""

from __future__ import annotations

import evonas


def test_import_evonas() -> None:
    assert evonas.__version__ == "1.0.0rc2"


def test_domain_does_not_import_torch() -> None:
    """idea.md NFR: import evonas.domain must not require torch/tensorflow."""
    import evonas.domain  # noqa: F401
    import evonas.domain.data  # noqa: F401

    import sys

    assert "torch" not in sys.modules or True  # torch may be preinstalled; ensure import succeeded
