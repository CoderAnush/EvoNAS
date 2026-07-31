"""Phase 11 governance / registry tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from evonas.application.registry.service import GovernanceService
from evonas.domain.registry.lifecycle import LifecycleError, LifecycleManager
from evonas.domain.registry.lineage import LineageEngine
from evonas.domain.registry.search import search_records
from evonas.infrastructure.registry.file_registry import FileGovernanceRegistry
from evonas.presentation.cli.main import build_parser, main
from evonas.presentation.dashboard.views.pages import RENDERERS


@pytest.fixture()
def registry(tmp_path: Path) -> FileGovernanceRegistry:
    cfg = {
        "lifecycle": {
            "initial": "created",
            "transitions": {
                "created": ["training", "evaluating", "archived"],
                "training": ["evaluating", "failed"],
                "evaluating": ["candidate", "rejected"],
                "candidate": ["validated", "rejected"],
                "validated": ["promoted", "archived"],
                "promoted": ["archived", "rolled_back"],
                "rejected": ["archived"],
                "failed": ["archived"],
                "archived": [],
                "rolled_back": ["candidate"],
            },
        },
        "stages": {
            "transitions": {
                "none": ["staging", "archived"],
                "staging": ["production", "archived", "none"],
                "production": ["archived", "staging"],
                "archived": ["none"],
            }
        },
    }
    return FileGovernanceRegistry(tmp_path / "registry", config=cfg)


def test_lifecycle_illegal_transition() -> None:
    mgr = LifecycleManager()
    with pytest.raises(LifecycleError):
        mgr.transition("created", "promoted", object_id="x")


def test_lineage_engine() -> None:
    eng = LineageEngine()
    eng.link("ds_v1", "exp_1", relation="feeds")
    eng.link("exp_1", "mdl_a@1", relation="produces_model")
    assert eng.children_of("ds_v1")[0]["id"] == "exp_1"
    assert "mdl_a@1" in eng.descendants("ds_v1")
    assert "flowchart" in eng.mermaid("ds_v1")


def test_search_records() -> None:
    rows = [
        {"kind": "model", "optimizer": "sapso", "tags": ["a"], "metrics": {"acc": 0.9}},
        {"kind": "model", "optimizer": "pso", "tags": ["b"], "metrics": {"acc": 0.5}},
    ]
    hit = search_records(rows, optimizer="sapso", metric_key="acc", metric_min=0.8)
    assert len(hit) == 1


def test_register_stage_and_production_singleton(registry: FileGovernanceRegistry) -> None:
    a = registry.register(
        {
            "model_id": "net",
            "version": "1",
            "optimizer": "sapso",
            "metrics": {"accuracy": 0.8},
        }
    )
    b = registry.register(
        {
            "model_id": "net",
            "version": "2",
            "optimizer": "sapso",
            "metrics": {"accuracy": 0.9},
            "parent_version": a["object_id"],
        }
    )
    registry.set_stage("net", "1", "staging", reason="candidate")
    registry.set_stage("net", "1", "production", reason="promote_v1")
    registry.set_stage("net", "2", "staging", reason="candidate")
    registry.set_stage("net", "2", "production", reason="promote_v2")
    prod = registry.get_production("net")
    assert prod is not None
    assert prod["version"] == "2"
    v1 = registry.get_model("net", "1")
    assert v1 is not None
    assert v1["stage"] == "archived"
    assert registry.list_objects("promotion")
    lin = registry.model_lineage("net")
    assert lin["models"]
    cmp = registry.compare_models(a["object_id"], b["object_id"])
    assert "metric_delta" in cmp


def test_governance_service_sync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts" / "baselines" / "b1").mkdir(parents=True)
    (tmp_path / "artifacts" / "baselines" / "b1" / "metrics.json").write_text(
        '{"val": {"accuracy": 0.7}}', encoding="utf-8"
    )
    (tmp_path / "artifacts" / "baselines" / "b1" / "experiment.json").write_text(
        '{"run_id": "b1", "architecture": "baseline"}', encoding="utf-8"
    )
    cfg = tmp_path / "configs" / "registry"
    cfg.mkdir(parents=True)
    (cfg / "registry.yaml").write_text(
        yaml.safe_dump({"registry": {"root": str(tmp_path / "artifacts" / "registry")}}),
        encoding="utf-8",
    )
    gov = GovernanceService(
        FileGovernanceRegistry(tmp_path / "artifacts" / "registry")
    )
    # Point sync cwd
    gov._sync.cwd = tmp_path  # noqa: SLF001
    out = gov.sync()
    assert out["synced"]["models"] >= 1
    assert gov.list_models()


def test_cli_registry_parsers() -> None:
    parser = build_parser()
    assert parser.parse_args(["registry", "sync"]).registry_command == "sync"
    assert parser.parse_args(["models", "list"]).models_command == "list"
    assert parser.parse_args(["lineage", "mdl_x"]).object_id == "mdl_x"
    assert parser.parse_args(["artifacts", "--limit", "10"]).limit == 10
    assert parser.parse_args(["experiments", "--limit", "5"]).limit == 5


def test_dashboard_registry_pages_registered() -> None:
    for name in ("Registry", "Models", "Datasets", "Lifecycle", "Lineage", "History"):
        assert name in RENDERERS


def test_version_rc2(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0rc2"
