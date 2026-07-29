"""Launch helpers for API / combined serve."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def launch_api(
    *,
    host: str | None = None,
    port: int | None = None,
    reload: bool = False,
    config: str | None = None,
) -> int:
    """Start uvicorn serving the FastAPI control plane."""
    try:
        import uvicorn
    except ImportError:
        print(
            "FastAPI/uvicorn not installed. Run: pip install 'evonas[api]'",
            file=sys.stderr,
        )
        return 1

    if config:
        os.environ["EVONAS_API_CONFIG"] = config

    from evonas.application.platform.container import PlatformSettings, reset_container

    settings = PlatformSettings.from_yaml_and_env(config)
    reset_container(settings)
    bind_host = host or settings.host
    bind_port = port or settings.port

    uvicorn.run(
        "evonas.presentation.api.app:create_app",
        factory=True,
        host=bind_host,
        port=bind_port,
        reload=reload or settings.reload,
        log_level=settings.log_level.lower(),
    )
    return 0


def _wait_health(url: str, *, timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    health = url.rstrip("/") + "/api/v1/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.4)
    return False


def launch_serve(
    *,
    api_port: int = 8000,
    dashboard_port: int = 8501,
    demo: bool = False,
    headless: bool = False,
    skip_dashboard: bool = False,
) -> int:
    """Start API then dashboard (dashboard talks to API only)."""
    os.environ["EVONAS_API_URL"] = f"http://127.0.0.1:{api_port}"
    os.environ["EVONAS_API_PORT"] = str(api_port)
    if demo:
        os.environ["EVONAS_DASHBOARD_DEMO"] = "1"

    api_proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "evonas.presentation.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
        ],
        cwd=str(Path.cwd()),
    )
    try:
        if not _wait_health(f"http://127.0.0.1:{api_port}"):
            logger.error("API failed to become healthy")
            api_proc.terminate()
            return 1
        if demo:
            try:
                req = urllib.request.Request(
                    f"http://127.0.0.1:{api_port}/api/v1/dashboard/demo",
                    data=b'{"demo": true}',
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=5)  # noqa: S310
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                logger.warning("Could not enable API demo mode: %s", exc)

        if skip_dashboard:
            return api_proc.wait()

        from evonas.presentation.dashboard.launcher import launch_dashboard

        code = launch_dashboard(port=dashboard_port, demo=demo, headless=headless)
        return int(code)
    finally:
        if api_proc.poll() is None:
            api_proc.terminate()
            try:
                api_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_proc.kill()


def fetch_status(api_url: str | None = None) -> dict[str, Any]:
    """HTTP GET /api/v1/status for CLI."""
    import json

    base = (api_url or os.environ.get("EVONAS_API_URL") or "http://127.0.0.1:8000").rstrip("/")
    with urllib.request.urlopen(base + "/api/v1/status", timeout=5) as resp:  # noqa: S310
        data: Any = json.loads(resp.read().decode("utf-8"))
        return data if isinstance(data, dict) else {"raw": data}
