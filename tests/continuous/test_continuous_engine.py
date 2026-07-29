"""Continuous learning unit tests — versioning, changes, policy, engine."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from evonas.domain.continuous.builder import IncrementalDatasetBuilder, MergeStrategy
from evonas.domain.continuous.change_detector import DatasetChangeDetector
from evonas.domain.continuous.engine import ContinuousLearningEngine
from evonas.domain.continuous.events import LearningRecommendation, LearningResult
from evonas.domain.continuous.lineage import DatasetLineage
from evonas.domain.continuous.policy import LearningPolicy
from evonas.domain.continuous.replay import ReplaySupport
from evonas.domain.continuous.versions import DataVersionManager
from evonas.domain.continuous.change_detector import ChangeReport


def test_version_manager_immutable(tmp_path: Path) -> None:
    mgr = DataVersionManager(tmp_path / "versions")
    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 3))
    y = rng.integers(0, 2, size=(20,))
    v1 = mgr.create(x, y, role="parent")
    v2 = mgr.create(x, y, parent_version=v1.version_id, role="training")
    assert v1.version_id != v2.version_id
    assert mgr.get(v1.version_id) is not None
    loaded_x, loaded_y = mgr.load_arrays(v1.version_id)
    assert loaded_x.shape == x.shape
    assert len(mgr.list_versions()) == 2


def test_change_detector_new_and_schema() -> None:
    det = DatasetChangeDetector()
    rng = np.random.default_rng(1)
    ref_x = rng.normal(size=(50, 4))
    ref_y = rng.integers(0, 2, size=(50,))
    cand_x = np.concatenate([ref_x, rng.normal(size=(15, 4))], axis=0)
    cand_y = np.concatenate([ref_y, rng.integers(0, 2, size=(15,))], axis=0)
    report = det.detect(ref_x, ref_y, cand_x, cand_y)
    assert report.new_samples >= 15
    assert report.has_changes
    # schema change
    bad = det.detect(ref_x, ref_y, rng.normal(size=(10, 5)), rng.integers(0, 2, size=(10,)))
    assert bad.schema_changed is True


def test_builder_strategies() -> None:
    b = IncrementalDatasetBuilder()
    rng = np.random.default_rng(2)
    ref_x, ref_y = rng.normal(size=(30, 2)), rng.integers(0, 2, size=(30,))
    cand_x, cand_y = rng.normal(size=(10, 2)), rng.integers(0, 2, size=(10,))
    append = b.build(ref_x, ref_y, cand_x, cand_y, strategy=MergeStrategy.APPEND)
    assert append.n_samples == 40
    replace = b.build(ref_x, ref_y, cand_x, cand_y, strategy="replace")
    assert replace.n_samples == 10
    roll = b.build(
        ref_x, ref_y, cand_x, cand_y, strategy=MergeStrategy.ROLLING_WINDOW, window_size=25
    )
    assert roll.n_samples == 25
    sample = b.build(
        ref_x, ref_y, cand_x, cand_y, strategy=MergeStrategy.SAMPLING, sample_fraction=0.5, seed=0
    )
    assert sample.n_samples == 20


def test_learning_policy_recommendations() -> None:
    policy = LearningPolicy(min_new_samples=10, max_drift_psi=0.2, mild_drift_psi=0.05)
    hold, reason = policy.recommend(
        change=ChangeReport(), drift_significant=False, psi=0.0
    )
    assert hold == LearningRecommendation.HOLD
    opt, _ = policy.recommend(
        change=ChangeReport(schema_changed=True, new_samples=0),
        drift_significant=False,
        psi=0.0,
    )
    assert opt == LearningRecommendation.OPTIMIZE_ARCH
    retrain, _ = policy.recommend(
        change=ChangeReport(new_samples=20, feature_changed=True),
        drift_significant=False,
        psi=0.08,
    )
    assert retrain == LearningRecommendation.RETRAIN_SAME_ARCH


def test_lineage_history() -> None:
    lin = DatasetLineage()
    lin.link(None, "a", relation="parent")
    lin.link("a", "b", relation="training")
    lin.link("b", "c", relation="candidate")
    assert lin.history("c") == ["c", "b", "a"]
    assert lin.children_of("a") == ["b"]


def test_engine_cycle_and_observation(tmp_path: Path) -> None:
    engine = ContinuousLearningEngine(
        artifacts_root=tmp_path,
        policy=LearningPolicy(min_new_samples=5, max_drift_psi=0.15),
        seed=7,
    )
    rng = np.random.default_rng(7)
    ref_x, ref_y = rng.normal(size=(40, 3)), rng.integers(0, 2, size=(40,))
    boot = engine.run_cycle(candidate_features=ref_x, candidate_labels=ref_y)
    assert boot.reason == "bootstrap_reference"
    cand_x = np.concatenate([ref_x, rng.normal(2.0, 1.0, size=(20, 3))], axis=0)
    cand_y = np.concatenate([ref_y, rng.integers(0, 2, size=(20,))], axis=0)
    result = engine.run_cycle(
        reference_features=ref_x,
        reference_labels=ref_y,
        candidate_features=cand_x,
        candidate_labels=cand_y,
    )
    assert result.dataset_version is not None
    assert result.recommendation in {
        LearningRecommendation.HOLD,
        LearningRecommendation.RETRAIN_SAME_ARCH,
        LearningRecommendation.OPTIMIZE_ARCH,
    }
    obs = engine.to_observation()
    assert "drift_status" in obs
    assert "psi_max" in obs["drift_report"] or obs["drift_report"] == {}
    paths = engine.export_artifacts(tmp_path / "out")
    assert Path(paths["history_json"]).exists()


def test_learning_result_roundtrip() -> None:
    engine = ContinuousLearningEngine(artifacts_root=Path("artifacts/_tmp_cl"))
    rng = np.random.default_rng(3)
    x, y = rng.normal(size=(10, 2)), rng.integers(0, 2, size=(10,))
    result = engine.run_cycle(candidate_features=x, candidate_labels=y)
    restored = LearningResult.from_dict(result.to_dict())
    assert restored.recommendation == result.recommendation
    assert restored.to_observation()["cl_recommendation"] == result.recommendation.value


def test_replay_from_history(tmp_path: Path) -> None:
    engine = ContinuousLearningEngine(
        artifacts_root=tmp_path, policy=LearningPolicy(min_new_samples=5), seed=1
    )
    rng = np.random.default_rng(1)
    x, y = rng.normal(size=(30, 2)), rng.integers(0, 2, size=(30,))
    engine.run_cycle(candidate_features=x, candidate_labels=y)
    cand = np.concatenate([x, rng.normal(size=(12, 2))], axis=0)
    engine.run_cycle(
        reference_features=x,
        reference_labels=y,
        candidate_features=cand,
        candidate_labels=np.concatenate([y, rng.integers(0, 2, size=(12,))]),
    )
    hist = engine.history.export_json(tmp_path / "learning_history.json")
    replay = ReplaySupport.from_history_json(hist)
    steps = replay.replay_all()
    assert len(steps) >= 1
