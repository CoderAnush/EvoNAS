"""ASGI module entry: python -m evonas.presentation.api"""

from __future__ import annotations

from evonas.presentation.api.launcher import launch_api

if __name__ == "__main__":
    raise SystemExit(launch_api())
