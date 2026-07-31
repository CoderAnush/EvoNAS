"""File-backed governance registry — JSON indexes under artifacts/registry/."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from evonas.domain.registry.lifecycle import LifecycleError, LifecycleManager
from evonas.domain.registry.lineage import LineageEngine
from evonas.domain.registry.records import model_record, stamp_metadata
from evonas.domain.registry.search import search_records
from evonas.domain.registry.types import ModelStage, RegistryKind

logger = logging.getLogger(__name__)


class FileGovernanceRegistry:
    """Unified FS registry for models, experiments, datasets, artifacts, events."""

    def __init__(
        self,
        root: str | Path = "artifacts/registry",
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.config = dict(config or {})
        self.lifecycle = LifecycleManager(self.config)
        self.lineage = LineageEngine()
        for kind in RegistryKind:
            (self.root / kind.value).mkdir(parents=True, exist_ok=True)
        (self.root / "edges.jsonl").touch(exist_ok=True)
        (self.root / "events.jsonl").touch(exist_ok=True)
        self._reload_lineage()

    @classmethod
    def from_yaml(cls, path: str | Path = "configs/registry/registry.yaml") -> FileGovernanceRegistry:
        cfg_path = Path(path)
        raw: dict[str, Any] = {}
        if cfg_path.exists():
            loaded = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            raw = loaded if isinstance(loaded, dict) else {}
        root = Path(str(raw.get("registry", {}).get("root", "artifacts/registry")))
        return cls(root, config=raw)

    # ----- generic store -----

    def upsert(self, kind: str, record: dict[str, Any]) -> dict[str, Any]:
        payload = stamp_metadata(dict(record))
        payload["kind"] = kind
        object_id = str(payload.get("object_id") or payload.get("id"))
        payload["object_id"] = object_id
        payload["id"] = object_id
        path = self._path(kind, object_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json(path, payload)
        self._index_append(kind, object_id)
        return payload

    def get(self, kind: str, object_id: str) -> dict[str, Any] | None:
        path = self._path(kind, object_id)
        if not path.exists():
            # try sanitized lookup via index
            for item in self.list_objects(kind, limit=10_000):
                if item.get("object_id") == object_id or item.get("id") == object_id:
                    return item
            return None
        return self._read_json(path)

    def list_objects(self, kind: str, *, limit: int = 100) -> list[dict[str, Any]]:
        folder = self.root / kind
        if not folder.exists():
            return []
        files = sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        rows: list[dict[str, Any]] = []
        for path in files[:limit]:
            data = self._read_json(path)
            if data:
                rows.append(data)
        return rows

    def list_all(self, *, limit: int = 500) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for kind in RegistryKind:
            rows.extend(self.list_objects(kind.value, limit=limit))
        rows.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)
        return rows[:limit]

    def search(self, query: dict[str, Any], *, limit: int = 100) -> list[dict[str, Any]]:
        kind = query.get("kind")
        pool = self.list_objects(str(kind), limit=10_000) if kind else self.list_all(limit=10_000)
        return search_records(
            pool,
            q=query.get("q"),
            kind=query.get("kind"),
            optimizer=query.get("optimizer"),
            dataset_version=query.get("dataset_version"),
            metric_key=query.get("metric_key"),
            metric_min=query.get("metric_min"),
            metric_max=query.get("metric_max"),
            tags=query.get("tags"),
            date_from=query.get("date_from"),
            date_to=query.get("date_to"),
            version=query.get("version"),
            status=query.get("status"),
            lifecycle_state=query.get("lifecycle_state"),
            limit=limit,
        )

    # ----- model registry (IModelRegistry) -----

    def register(self, record: dict[str, Any]) -> dict[str, Any]:
        if "model_id" not in record:
            built = model_record(**{k: v for k, v in record.items() if k != "kind"})
        else:
            built = model_record(
                model_id=str(record.get("model_id")),
                version=str(record.get("version", "1")),
                architecture=record.get("architecture"),
                optimizer=record.get("optimizer"),
                dataset_version=record.get("dataset_version"),
                training_config=record.get("training_config"),
                metrics=record.get("metrics"),
                artifacts=record.get("artifacts"),
                status=record.get("status"),
                stage=str(record.get("stage", ModelStage.NONE.value)),
                lifecycle_state=str(record.get("lifecycle_state", "created")),
                experiment_id=record.get("experiment_id"),
                parent_version=record.get("parent_version"),
                genotype=record.get("genotype"),
                creator=str(record.get("creator", "evonas")),
                extra={k: v for k, v in record.items() if k not in {
                    "model_id", "version", "architecture", "optimizer", "dataset_version",
                    "training_config", "metrics", "artifacts", "status", "stage",
                    "lifecycle_state", "experiment_id", "parent_version", "genotype", "creator",
                }},
            )
        saved = self.upsert(RegistryKind.MODEL.value, built)
        parent = saved.get("parent_version")
        if parent:
            self.link(str(parent), str(saved["object_id"]), relation="parent_of")
        experiment_id = saved.get("experiment_id")
        if experiment_id:
            self.link(str(experiment_id), str(saved["object_id"]), relation="produces_model")
        return saved

    def get_model(self, model_id: str, version: str | None = None) -> dict[str, Any] | None:
        if version:
            return self.get(RegistryKind.MODEL.value, f"{model_id}@{version}")
        matches = [
            m
            for m in self.list_objects(RegistryKind.MODEL.value, limit=10_000)
            if m.get("model_id") == model_id
        ]
        if not matches:
            return None
        matches.sort(key=lambda m: str(m.get("created_at", "")), reverse=True)
        return matches[0]

    def set_stage(
        self,
        model_id: str,
        version: str,
        stage: str,
        *,
        reason: str = "",
    ) -> dict[str, Any]:
        rec = self.get_model(model_id, version)
        if rec is None:
            raise LifecycleError(f"Model not found: {model_id}@{version}")
        current = str(rec.get("stage", ModelStage.NONE.value))
        # Enforce single production pointer (idea.md)
        if stage == ModelStage.PRODUCTION.value:
            # Snapshot LKG metadata before demoting previous production
            prod = self.get_production(model_id)
            if prod and prod.get("version") != version:
                self.record_rollback(
                    {
                        "model_id": model_id,
                        "previous_version": prod.get("version"),
                        "new_version": version,
                        "reason": "lkg_snapshot_before_promote",
                        "kind_note": "metadata_only",
                    }
                )
            self._demote_other_production(model_id, keep_version=version)
        event = self.lifecycle.set_stage(
            current, stage, model_id=model_id, version=version, reason=reason
        )
        rec["stage"] = stage
        rec["status"] = stage
        if stage == ModelStage.PRODUCTION.value:
            rec["lifecycle_state"] = "promoted"
        elif stage == ModelStage.ARCHIVED.value:
            rec["lifecycle_state"] = "archived"
        saved = self.upsert(RegistryKind.MODEL.value, rec)
        self._append_event(event)
        if stage == ModelStage.PRODUCTION.value:
            self.record_promotion(
                {
                    "model_id": model_id,
                    "version": version,
                    "previous_version": event.get("from_stage"),
                    "reason": reason or "stage_to_production",
                    "metrics": rec.get("metrics") or {},
                    "accepted": True,
                }
            )
        return saved

    def get_production(self, model_id: str) -> dict[str, Any] | None:
        for m in self.list_objects(RegistryKind.MODEL.value, limit=10_000):
            if m.get("model_id") == model_id and m.get("stage") == ModelStage.PRODUCTION.value:
                return m
        return None

    def model_lineage(self, model_id: str) -> dict[str, Any]:
        versions = [
            m
            for m in self.list_objects(RegistryKind.MODEL.value, limit=10_000)
            if m.get("model_id") == model_id
        ]
        root = versions[0]["object_id"] if versions else model_id
        graph = self.lineage.subgraph(str(root), max_depth=16)
        graph["models"] = versions
        graph["mermaid"] = self.lineage.mermaid(str(root), max_depth=16)
        return graph

    # ----- lineage / events / promotion metadata -----

    def link(self, source_id: str, target_id: str, *, relation: str = "produces") -> dict[str, str]:
        edge = self.lineage.link(source_id, target_id, relation=relation)
        with (self.root / "edges.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(edge) + "\n")
        return edge

    def record_promotion(self, payload: dict[str, Any]) -> dict[str, Any]:
        rec = stamp_metadata(
            {
                "kind": RegistryKind.PROMOTION.value,
                "object_id": payload.get("object_id")
                or f"promo_{payload.get('model_id', 'x')}_{payload.get('version', '1')}",
                **payload,
            }
        )
        return self.upsert(RegistryKind.PROMOTION.value, rec)

    def record_rollback(self, payload: dict[str, Any]) -> dict[str, Any]:
        rec = stamp_metadata(
            {
                "kind": RegistryKind.ROLLBACK.value,
                "object_id": payload.get("object_id")
                or f"rb_{payload.get('model_id', 'x')}_{payload.get('previous_version', '0')}",
                "recovery": payload.get("recovery")
                or "Metadata-only rollback pointer; no live deployment mutated.",
                **payload,
            }
        )
        return self.upsert(RegistryKind.ROLLBACK.value, rec)

    def transition_lifecycle(
        self,
        kind: str,
        object_id: str,
        target: str,
        *,
        reason: str = "",
    ) -> dict[str, Any]:
        rec = self.get(kind, object_id)
        if rec is None:
            raise LifecycleError(f"Object not found: {kind}/{object_id}")
        current = str(rec.get("lifecycle_state", self.lifecycle.initial))
        event = self.lifecycle.transition(
            current, target, object_id=object_id, reason=reason
        )
        rec["lifecycle_state"] = target
        saved = self.upsert(kind, rec)
        self._append_event(event)
        self.upsert(
            RegistryKind.LIFECYCLE_EVENT.value,
            {**event, "object_id": event["event_id"], "target_object": object_id},
        )
        return saved

    def history(self, object_id: str) -> list[dict[str, Any]]:
        events = []
        path = self.root / "events.jsonl"
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if object_id in {
                    ev.get("object_id"),
                    ev.get("model_id"),
                    ev.get("target_object"),
                    f"{ev.get('model_id')}@{ev.get('version')}",
                }:
                    events.append(ev)
        return events

    def compare_models(self, left_id: str, right_id: str) -> dict[str, Any]:
        left = self.get(RegistryKind.MODEL.value, left_id) or self.get_model(left_id)
        right = self.get(RegistryKind.MODEL.value, right_id) or self.get_model(right_id)
        return {
            "left": left,
            "right": right,
            "metric_delta": _metric_delta(
                (left or {}).get("metrics") or {},
                (right or {}).get("metrics") or {},
            ),
        }

    def overview(self) -> dict[str, Any]:
        counts = {k.value: len(self.list_objects(k.value, limit=10_000)) for k in RegistryKind}
        return {
            "root": str(self.root),
            "counts": counts,
            "lifecycle_graph": self.lifecycle.graph(),
            "lifecycle_mermaid": self.lifecycle.mermaid_lifecycle(),
            "stages_mermaid": self.lifecycle.mermaid_stages(),
            "lineage": self.lineage.to_dict(),
        }

    # ----- internals -----

    def _demote_other_production(self, model_id: str, *, keep_version: str) -> None:
        for m in self.list_objects(RegistryKind.MODEL.value, limit=10_000):
            if (
                m.get("model_id") == model_id
                and m.get("stage") == ModelStage.PRODUCTION.value
                and m.get("version") != keep_version
            ):
                m["stage"] = ModelStage.ARCHIVED.value
                m["status"] = ModelStage.ARCHIVED.value
                m["lifecycle_state"] = "archived"
                self.upsert(RegistryKind.MODEL.value, m)

    def _append_event(self, event: dict[str, Any]) -> None:
        with (self.root / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, default=str) + "\n")

    def _reload_lineage(self) -> None:
        path = self.root / "edges.jsonl"
        edges: list[dict[str, Any]] = []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    edges.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        self.lineage.load_edges(edges)

    def _path(self, kind: str, object_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_@." else "_" for ch in object_id)
        return self.root / kind / f"{safe}.json"

    def _index_append(self, kind: str, object_id: str) -> None:
        idx = self.root / "index.jsonl"
        with idx.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": kind, "object_id": object_id}) + "\n")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None


def _metric_delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    keys = set(a) | set(b)
    out: dict[str, float] = {}
    for key in keys:
        try:
            out[key] = float(b.get(key, 0) or 0) - float(a.get(key, 0) or 0)
        except (TypeError, ValueError):
            continue
    return out
