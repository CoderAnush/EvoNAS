"""Registry search — filter governed metadata records."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def search_records(
    records: list[dict[str, Any]],
    *,
    q: str | None = None,
    kind: str | None = None,
    optimizer: str | None = None,
    dataset_version: str | None = None,
    metric_key: str | None = None,
    metric_min: float | None = None,
    metric_max: float | None = None,
    tags: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    version: str | None = None,
    status: str | None = None,
    lifecycle_state: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Filter records; does not alter source data."""
    out: list[dict[str, Any]] = []
    q_lower = q.lower() if q else None
    tag_set = {t.lower() for t in (tags or [])}
    for rec in records:
        if kind and str(rec.get("kind", "")) != kind:
            continue
        if optimizer and str(rec.get("optimizer", "")).lower() != optimizer.lower():
            continue
        if dataset_version and str(rec.get("dataset_version", "")) != dataset_version:
            continue
        if version and str(rec.get("version", "")) != version:
            continue
        if status and str(rec.get("status", rec.get("stage", ""))) != status:
            continue
        if lifecycle_state and str(rec.get("lifecycle_state", "")) != lifecycle_state:
            continue
        if tag_set:
            rec_tags = {str(t).lower() for t in (rec.get("tags") or [])}
            if not tag_set.issubset(rec_tags):
                continue
        if metric_key:
            metrics = rec.get("metrics") or {}
            if not isinstance(metrics, dict) or metric_key not in metrics:
                continue
            try:
                value = float(metrics[metric_key])
            except (TypeError, ValueError):
                continue
            if metric_min is not None and value < metric_min:
                continue
            if metric_max is not None and value > metric_max:
                continue
        if date_from or date_to:
            ts = str(rec.get("created_at") or rec.get("timestamp") or "")
            if not _in_range(ts, date_from, date_to):
                continue
        if q_lower:
            blob = " ".join(
                str(rec.get(k, ""))
                for k in (
                    "id",
                    "object_id",
                    "model_id",
                    "experiment_id",
                    "name",
                    "optimizer",
                    "dataset_version",
                    "status",
                    "lifecycle_state",
                    "tags",
                    "path",
                )
            ).lower()
            if q_lower not in blob:
                continue
        out.append(rec)
        if len(out) >= limit:
            break
    return out


def _in_range(ts: str, date_from: str | None, date_to: str | None) -> bool:
    if not ts:
        return False
    try:
        value = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return False
    if date_from:
        try:
            start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            if value < start:
                return False
        except ValueError:
            return False
    if date_to:
        try:
            end = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            if value > end:
                return False
        except ValueError:
            return False
    return True
