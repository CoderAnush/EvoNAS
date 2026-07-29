"""Dashboard facade — re-exports platform query engine (API owns file access)."""

from __future__ import annotations

from evonas.application.platform.query_facade import DashboardContext, DashboardService

__all__ = ["DashboardContext", "DashboardService"]
