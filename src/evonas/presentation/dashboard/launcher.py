"""Launch Streamlit dashboard process."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def launch_dashboard(
    *,
    port: int = 8501,
    demo: bool = False,
    headless: bool = False,
) -> int:
    """Start Streamlit on the EvoNAS dashboard app.

    Returns process exit code. Requires optional extra: ``pip install 'evonas[dashboard]'``.
    """
    try:
        import streamlit.web.cli as stcli
    except ImportError as exc:  # pragma: no cover - env dependent
        print(
            "Streamlit is required for the dashboard.\n"
            "Install with: pip install 'evonas[dashboard]'",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    app_path = Path(__file__).resolve().parent / "app.py"
    if demo:
        os.environ["EVONAS_DASHBOARD_DEMO"] = "1"
    argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    if headless:
        argv.extend(["--server.headless", "true"])
    sys.argv = argv
    stcli.main()
    return 0
