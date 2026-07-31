"""Sync existing EvoNAS artifacts into the governance registry (read-only scan)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas.application.platform.artifact_loaders import (
    discover_artifact_roots,
    list_run_dirs,
    read_json,
)
from evonas.domain.registry.records import new_id, stamp_metadata
from evonas.domain.registry.types import LifecycleState, RegistryKind
from evonas.infrastructure.registry.file_registry import FileGovernanceRegistry

logger = logging.getLogger(__name__)


class RegistrySyncService:
    """Index baselines / optimization / research / CL / closed-loop into registry."""

    def __init__(self, registry: FileGovernanceRegistry, *, cwd: Path | None = None) -> None:
        self.registry = registry
        self.cwd = cwd or Path.cwd()

    def sync_all(self) -> dict[str, Any]:
        roots = discover_artifact_roots(self.cwd)
        counts = {
            "models": 0,
            "experiments": 0,
            "datasets": 0,
            "artifacts": 0,
            "promotions": 0,
        }
        counts["models"] += self._sync_baselines(roots["baselines"])
        counts["models"] += self._sync_optimization(roots["optimization"])
        counts["experiments"] += self._sync_research(roots.get("research", roots["artifacts"] / "research"))
        counts["datasets"] += self._sync_datasets(roots["continuous_learning"])
        counts["promotions"] += self._sync_closed_loop(roots["closed_loop"])
        counts["artifacts"] += self._index_loose_artifacts(roots["artifacts"])
        return {"synced": counts, "overview": self.registry.overview()}

    def _sync_baselines(self, root: Path) -> int:
        n = 0
        for run in list_run_dirs(root):
            metrics_raw = read_json(run / "metrics.json")
            summary_raw = read_json(run / "experiment.json")
            metrics = metrics_raw if isinstance(metrics_raw, dict) else {}
            summary = summary_raw if isinstance(summary_raw, dict) else {}
            mid = str(summary.get("run_id") or run.name)
            val_metrics = metrics.get("val") if isinstance(metrics.get("val"), dict) else metrics
            rec = self.registry.register(
                {
                    "model_id": f"baseline_{mid}",
                    "version": "1",
                    "architecture": summary.get("architecture") or "baseline",
                    "optimizer": "none",
                    "dataset_version": summary.get("dataset") or "unknown",
                    "training_config": summary,
                    "metrics": val_metrics if isinstance(val_metrics, dict) else {},
                    "artifacts": [str(run)],
                    "lifecycle_state": LifecycleState.VALIDATED.value,
                    "stage": "none",
                    "experiment_id": mid,
                    "tags": ["baseline", "synced"],
                }
            )
            self.registry.link(mid, rec["object_id"], relation="trains")
            n += 1
        return n

    def _sync_optimization(self, root: Path) -> int:
        n = 0
        for run in list_run_dirs(root):
            summary = read_json(run / "summary.json") or {}
            if not isinstance(summary, dict):
                continue
            if (run / "comparison.json").exists():
                continue
            mid = str(summary.get("run_id") or run.name)
            algo = str(summary.get("algorithm") or "pso")
            rec = self.registry.register(
                {
                    "model_id": f"opt_{mid}",
                    "version": "1",
                    "architecture": summary.get("best_architecture") or summary.get("architecture"),
                    "optimizer": algo,
                    "dataset_version": summary.get("dataset_version") or "search_space",
                    "metrics": {
                        "best_fitness": summary.get("best_fitness"),
                        "iterations": summary.get("iterations"),
                        "evaluations": summary.get("evaluations"),
                    },
                    "artifacts": [str(run)],
                    "lifecycle_state": LifecycleState.CANDIDATE.value,
                    "experiment_id": mid,
                    "tags": ["optimization", "synced", algo],
                }
            )
            exp = stamp_metadata(
                {
                    "kind": RegistryKind.EXPERIMENT.value,
                    "object_id": mid,
                    "experiment_id": mid,
                    "optimizer": algo,
                    "results": summary,
                    "path": str(run),
                    "tags": ["optimization"],
                }
            )
            self.registry.upsert(RegistryKind.EXPERIMENT.value, exp)
            self.registry.link(mid, rec["object_id"], relation="produces_model")
            n += 1
        return n

    def _sync_research(self, root: Path) -> int:
        n = 0
        if not root.exists():
            return 0
        for run in list_run_dirs(root):
            meta = read_json(run / "meta.json") or {}
            results = read_json(run / "results.json") or {}
            if not isinstance(meta, dict):
                continue
            eid = str(meta.get("experiment_id") or run.name)
            exp = stamp_metadata(
                {
                    "kind": RegistryKind.EXPERIMENT.value,
                    "object_id": eid,
                    "experiment_id": eid,
                    "optimizer": ",".join(meta.get("algorithms") or []),
                    "results": results,
                    "config_hash": meta.get("config_hash"),
                    "git_commit": meta.get("git_commit"),
                    "path": str(run),
                    "tags": ["research", "synced"],
                    "lifecycle_state": LifecycleState.VALIDATED.value,
                }
            )
            self.registry.upsert(RegistryKind.EXPERIMENT.value, exp)
            n += 1
        return n

    def _sync_datasets(self, root: Path) -> int:
        n = 0
        lineage = read_json(root / "lineage.json")
        index = read_json(root / "versions_index.json")
        versions: list[Any] = []
        if isinstance(index, dict):
            versions = list(index.get("versions") or index.get("items") or [])
        elif isinstance(lineage, dict):
            versions = list(lineage.get("versions") or lineage.get("nodes") or [])
        for item in versions:
            if isinstance(item, str):
                vid, parent = item, None
                meta: dict[str, Any] = {}
            elif isinstance(item, dict):
                vid = str(item.get("version_id") or item.get("id") or new_id("ds"))
                parent = item.get("parent_version") or item.get("parent")
                meta = item
            else:
                continue
            rec = stamp_metadata(
                {
                    "kind": RegistryKind.DATASET.value,
                    "object_id": vid,
                    "dataset_version": vid,
                    "parent_version": parent,
                    "metadata": meta,
                    "path": str(root / vid) if (root / vid).exists() else str(root),
                    "tags": ["dataset", "synced"],
                    "lifecycle_state": LifecycleState.CREATED.value,
                }
            )
            self.registry.upsert(RegistryKind.DATASET.value, rec)
            if parent:
                self.registry.link(str(parent), vid, relation="dataset_parent")
            n += 1
        if isinstance(lineage, dict):
            for edge in lineage.get("edges") or []:
                if isinstance(edge, dict) and edge.get("source") and edge.get("target"):
                    self.registry.link(
                        str(edge["source"]),
                        str(edge["target"]),
                        relation=str(edge.get("relation", "dataset_parent")),
                    )
        return n

    def _sync_closed_loop(self, root: Path) -> int:
        n = 0
        for run in list_run_dirs(root):
            summary = read_json(run / "summary.json") or {}
            if not isinstance(summary, dict):
                continue
            promotions = summary.get("promotions") or []
            for promo in promotions:
                if not isinstance(promo, dict):
                    continue
                self.registry.record_promotion(
                    {
                        **promo,
                        "source_run": str(run),
                        "tags": ["closed_loop", "synced"],
                    }
                )
                n += 1
            eid = str(summary.get("run_id") or run.name)
            self.registry.upsert(
                RegistryKind.EXPERIMENT.value,
                stamp_metadata(
                    {
                        "kind": RegistryKind.EXPERIMENT.value,
                        "object_id": eid,
                        "experiment_id": eid,
                        "optimizer": summary.get("algorithm"),
                        "results": summary,
                        "path": str(run),
                        "tags": ["closed_loop"],
                        "lifecycle_state": str(summary.get("state") or "validated"),
                    }
                ),
            )
        return n

    def _index_loose_artifacts(self, root: Path) -> int:
        n = 0
        if not root.exists():
            return 0
        suffixes = {".json", ".csv", ".png", ".pdf", ".svg", ".md", ".yaml", ".yml", ".txt", ".jsonl"}
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            if "registry" in path.parts:
                continue
            oid = f"art_{abs(hash(str(path))) % 10**10}"
            self.registry.upsert(
                RegistryKind.ARTIFACT.value,
                stamp_metadata(
                    {
                        "kind": RegistryKind.ARTIFACT.value,
                        "object_id": oid,
                        "name": path.name,
                        "path": str(path),
                        "suffix": path.suffix.lower(),
                        "size": path.stat().st_size,
                        "tags": ["artifact", "synced"],
                    }
                ),
            )
            n += 1
            if n >= 200:
                break
        return n
