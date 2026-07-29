"""HTTP client — dashboard consumes REST API only (no direct artifact IO)."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, cast
from urllib.parse import quote, urlencode

logger = logging.getLogger(__name__)


def _as_dict(data: Any) -> dict[str, Any]:
    return cast(dict[str, Any], data) if isinstance(data, dict) else {}


def _as_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return cast(list[dict[str, Any]], data)
    return []


class ApiDashboardService:
    """Drop-in replacement for DashboardService backed by /api/v1/dashboard/*."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        demo_mode: bool = False,
        timeout_s: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("EVONAS_API_URL")
            or "http://127.0.0.1:8000"
        ).rstrip("/")
        self.demo_mode = demo_mode
        self.timeout_s = timeout_s
        self._demo_synced = False

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API {method} {path} failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach EvoNAS API at {self.base_url} ({exc.reason}). "
                "Start it with `evonas api` or `evonas serve`."
            ) from exc

    def _ensure_demo(self) -> None:
        if self._demo_synced:
            return
        if self.demo_mode:
            self._request("POST", "/api/v1/dashboard/demo", body={"demo": True})
        self._demo_synced = True

    def _get(self, path: str) -> Any:
        self._ensure_demo()
        return self._request("GET", path)

    def landing(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/landing"))

    def optimization_summary(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/optimization"))

    def sapso_analytics(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/sapso"))

    def lifecycle(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/lifecycle"))

    def continuous(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/continuous"))

    def training(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/training"))

    def architecture(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/architecture"))

    def experiments(self) -> list[dict[str, Any]]:
        return _as_list(self._get("/api/v1/dashboard/experiments"))

    def comparison(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/comparison"))

    def browse_artifacts(self, root_key: str = "artifacts") -> list[dict[str, Any]]:
        qs = urlencode({"root": root_key})
        return _as_list(self._get(f"/api/v1/artifacts?{qs}"))

    def read_artifact(self, abs_path: str) -> dict[str, Any]:
        return _as_dict(
            self._request(
                "POST",
                "/api/v1/artifacts/preview",
                body={"path": abs_path},
            )
        )

    def settings(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/settings"))

    def health(self) -> dict[str, Any]:
        return _as_dict(self._get("/api/v1/dashboard/health"))

    def replay_steps(self, source: str = "lifecycle") -> list[dict[str, Any]]:
        data = _as_dict(self._get(f"/api/v1/replay/{quote(source, safe='')}"))
        return _as_list(data.get("steps"))

    def list_optimization_runs(self) -> list[str]:
        return []

    def list_loop_runs(self) -> list[str]:
        return []

    def list_cl_runs(self) -> list[str]:
        return []

    def list_baseline_runs(self) -> list[str]:
        return []
