"""Continuous Learning Engine — data evolution only (Phase 7).

Never runs PSO/SAPSO, never authorizes optimization, never deploys models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from evonas.domain.common.enums import Split
from evonas.domain.continuous.builder import IncrementalDatasetBuilder, MergeStrategy
from evonas.domain.continuous.change_detector import ChangeReport, DatasetChangeDetector
from evonas.domain.continuous.events import (
    LearningEvent,
    LearningEventType,
    LearningRecommendation,
    LearningResult,
)
from evonas.domain.continuous.history import LearningHistory
from evonas.domain.continuous.lineage import DatasetLineage
from evonas.domain.continuous.policy import LearningPolicy
from evonas.domain.continuous.retention import RetentionPolicy, apply_retention
from evonas.domain.continuous.versions import DataVersionManager
from evonas.domain.continuous.windows import WindowCursor, WindowManager
from evonas.domain.data.models import DriftReport
from evonas.domain.data.statistics import compute_data_stats, rebin_to_edges
from evonas.domain.common.hashing import sha256_array
from evonas.ports.dataset import IDatasetManager, IDriftDetector

logger = logging.getLogger(__name__)


@dataclass
class ContinuousLearningEngine:
    """Single public entry point for continuous data evolution.

    Detect → validate → version → drift → recommend → notify (via LearningResult).
    """

    dataset: IDatasetManager | None = None
    policy: LearningPolicy = field(default_factory=LearningPolicy)
    version_manager: DataVersionManager | None = None
    change_detector: DatasetChangeDetector = field(default_factory=DatasetChangeDetector)
    builder: IncrementalDatasetBuilder = field(default_factory=IncrementalDatasetBuilder)
    lineage: DatasetLineage = field(default_factory=DatasetLineage)
    history: LearningHistory = field(default_factory=LearningHistory)
    retention: RetentionPolicy = field(default_factory=RetentionPolicy)
    drift_detector: IDriftDetector | None = None
    merge_strategy: MergeStrategy = MergeStrategy.APPEND
    window_size: int = 50
    sample_fraction: float = 1.0
    seed: int = 42
    simulate: bool = True
    artifacts_root: Path = field(default_factory=lambda: Path("artifacts/continuous_learning"))
    _last_result: LearningResult | None = field(default=None, init=False, repr=False)
    _last_retrain_time: str | None = field(default=None, init=False, repr=False)
    _window_mgr: WindowManager | None = field(default=None, init=False, repr=False)
    _reference_version: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.artifacts_root = Path(self.artifacts_root)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        if self.version_manager is None:
            self.version_manager = DataVersionManager(self.artifacts_root / "versions")
        self.history.metadata.update(
            {
                "seed": self.seed,
                "simulate": self.simulate,
                "merge_strategy": self.merge_strategy.value,
            }
        )

    @property
    def last_result(self) -> LearningResult | None:
        """Most recent LearningResult (for ClosedLoop observation mapping)."""
        return self._last_result

    def current_window(self) -> dict[str, Any] | None:
        """Return current window descriptor if a DatasetManager is attached."""
        if self._window_mgr is None:
            return None
        return self._window_mgr.cursor.to_dict()

    def recommend(
        self,
        *,
        change: ChangeReport | None = None,
        drift: DriftReport | None = None,
        data_availability: bool = True,
        confidence: float = 1.0,
    ) -> tuple[LearningRecommendation, str]:
        """Policy recommendation only — does not start optimization."""
        change = change or ChangeReport()
        psi = float(drift.psi) if drift is not None else 0.0
        significant = bool(drift.significant) if drift is not None else False
        hours = None
        if self._last_retrain_time:
            try:
                last = datetime.fromisoformat(self._last_retrain_time)
                hours = (datetime.now(timezone.utc) - last).total_seconds() / 3600.0
            except ValueError:
                hours = None
        return self.policy.recommend(
            change=change,
            drift_significant=significant,
            psi=psi,
            hours_since_last_retrain=hours,
            data_availability=data_availability,
            confidence=confidence,
        )

    def to_observation(self) -> dict[str, Any]:
        """Observation payload for ClosedLoopController (Phase 6 contract)."""
        if self._last_result is None:
            return {
                "drift_status": "unknown",
                "drift_report": {},
                "force_optimization": False,
                "data_availability": False,
            }
        return self._last_result.to_observation()

    def detect_new_data(
        self,
        reference_features: np.ndarray,
        reference_labels: np.ndarray,
        candidate_features: np.ndarray,
        candidate_labels: np.ndarray,
    ) -> ChangeReport:
        """Detect structural/content changes between reference and candidate."""
        report = self.change_detector.detect(
            reference_features,
            reference_labels,
            candidate_features,
            candidate_labels,
        )
        event = LearningEvent(
            event_type=LearningEventType.NEW_DATA_DETECTED,
            payload=report.to_dict(),
        )
        self.history.add_event(event)
        return report

    def run_cycle(
        self,
        *,
        reference_features: np.ndarray | None = None,
        reference_labels: np.ndarray | None = None,
        candidate_features: np.ndarray | None = None,
        candidate_labels: np.ndarray | None = None,
        advance_window: bool = False,
    ) -> LearningResult:
        """Full detect→version→drift→recommend cycle (simulation-friendly)."""
        events: list[LearningEvent] = []
        assert self.version_manager is not None

        ref_x, ref_y, cand_x, cand_y = self._resolve_arrays(
            reference_features,
            reference_labels,
            candidate_features,
            candidate_labels,
            advance_window=advance_window,
        )
        if cand_x is None or cand_y is None or cand_x.size == 0:
            result = LearningResult(
                recommendation=LearningRecommendation.HOLD,
                events=tuple(
                    [
                        LearningEvent(
                            event_type=LearningEventType.RETRAINING_SKIPPED,
                            payload={"reason": "empty_candidate"},
                            recommendation=LearningRecommendation.HOLD,
                        )
                    ]
                ),
                dataset_version=self._reference_version,
                parent_version=None,
                drift_status="unknown",
                drift_report={},
                change_report={},
                training_candidate={},
                data_availability=False,
                reason="empty_candidate",
            )
            self._last_result = result
            self.history.add_event(result.events[0])
            self.history.add_policy_decision("HOLD", "empty_candidate")
            return result

        if ref_x is None or ref_y is None:
            # Bootstrap reference from candidate
            parent = self.version_manager.create(
                cand_x,
                cand_y,
                parent_version=None,
                role="parent",
                metadata={"bootstrap": True},
            )
            self._reference_version = parent.version_id
            self.lineage.link(None, parent.version_id, relation="parent")
            self.history.add_version(parent.to_dict())
            events.append(
                LearningEvent(
                    event_type=LearningEventType.DATASET_VERSION_CREATED,
                    dataset_version=parent.version_id,
                    payload={"role": "parent", "bootstrap": True},
                )
            )
            result = LearningResult(
                recommendation=LearningRecommendation.HOLD,
                events=tuple(events),
                dataset_version=parent.version_id,
                parent_version=None,
                drift_status="none",
                drift_report={},
                change_report=ChangeReport(
                    reference_n=0, candidate_n=int(cand_x.shape[0])
                ).to_dict(),
                training_candidate={
                    "version_id": parent.version_id,
                    "n_samples": parent.n_samples,
                    "checksum": parent.checksum,
                },
                data_availability=True,
                reason="bootstrap_reference",
            )
            self._finalize_result(result, events)
            return result

        change = self.detect_new_data(ref_x, ref_y, cand_x, cand_y)
        events.append(
            LearningEvent(
                event_type=LearningEventType.NEW_DATA_DETECTED,
                payload=change.to_dict(),
            )
        )

        if change.schema_changed:
            events.append(
                LearningEvent(
                    event_type=LearningEventType.DATASET_REJECTED,
                    payload={"reason": "schema_changed", **change.to_dict()},
                )
            )
            # Still recommend via policy (may OPTIMIZE_ARCH)
            drift_status = "significant"
            drift_dict: dict[str, Any] = {"significant": True, "psi": 1.0, "psi_max": 1.0}
            rec, reason = self.recommend(
                change=change,
                drift=None,
                data_availability=True,
            )
            # Force optimize path for schema via policy
            if self.policy.optimize_on_schema_change:
                rec, reason = LearningRecommendation.OPTIMIZE_ARCH, "schema_changed"
            result = LearningResult(
                recommendation=rec,
                events=tuple(events),
                dataset_version=self._reference_version,
                parent_version=self._reference_version,
                drift_status=drift_status,
                drift_report=drift_dict,
                change_report=change.to_dict(),
                training_candidate={},
                data_availability=True,
                reason=reason,
            )
            self._finalize_result(result, events)
            return result

        built = self.builder.build(
            ref_x,
            ref_y,
            cand_x,
            cand_y,
            strategy=self.merge_strategy,
            window_size=self.window_size,
            sample_fraction=self.sample_fraction,
            seed=self.seed,
        )
        events.append(
            LearningEvent(
                event_type=LearningEventType.DATASET_MERGED,
                payload=built.to_dict(),
            )
        )

        version = self.version_manager.create(
            built.features,
            built.labels,
            parent_version=self._reference_version,
            role="training",
            metadata={"strategy": built.strategy.value, **built.metadata},
        )
        self.lineage.link(
            self._reference_version,
            version.version_id,
            relation="training",
            metadata={"strategy": built.strategy.value},
        )
        self.history.add_version(version.to_dict())
        events.append(
            LearningEvent(
                event_type=LearningEventType.DATASET_VERSION_CREATED,
                dataset_version=version.version_id,
                payload=version.to_dict(),
            )
        )

        drift = self._compute_drift(ref_x, ref_y, built.features, built.labels)
        drift_dict = drift.to_dict()
        drift_dict["psi_max"] = drift.psi
        self.history.add_drift(drift_dict)
        events.append(
            LearningEvent(
                event_type=LearningEventType.DRIFT_COMPUTED,
                dataset_version=version.version_id,
                payload=drift_dict,
            )
        )
        drift_status = self._map_drift_status(drift)

        rec, reason = self.recommend(
            change=change, drift=drift, data_availability=True
        )
        event_type = (
            LearningEventType.OPTIMIZE_RECOMMENDED
            if rec == LearningRecommendation.OPTIMIZE_ARCH
            else LearningEventType.RETRAINING_RECOMMENDED
            if rec == LearningRecommendation.RETRAIN_SAME_ARCH
            else LearningEventType.RETRAINING_SKIPPED
        )
        events.append(
            LearningEvent(
                event_type=event_type,
                dataset_version=version.version_id,
                recommendation=rec,
                payload={"reason": reason},
            )
        )

        retention = apply_retention(self.version_manager, self.retention)
        if retention.pruned:
            events.append(
                LearningEvent(
                    event_type=LearningEventType.RETENTION_APPLIED,
                    payload=retention.to_dict(),
                )
            )

        if rec != LearningRecommendation.HOLD:
            self._last_retrain_time = datetime.now(timezone.utc).isoformat()
            # Promote training candidate as new reference for next cycle
            self._reference_version = version.version_id

        result = LearningResult(
            recommendation=rec,
            events=tuple(events),
            dataset_version=version.version_id,
            parent_version=version.parent_version,
            drift_status=drift_status,
            drift_report=drift_dict,
            change_report=change.to_dict(),
            training_candidate={
                "version_id": version.version_id,
                "n_samples": version.n_samples,
                "checksum": version.checksum,
                "features_uri": version.features_uri,
                "labels_uri": version.labels_uri,
                "strategy": built.strategy.value,
            },
            data_availability=True,
            reason=reason,
            metadata={
                "window": self.current_window(),
                "retention": retention.to_dict(),
                "simulate": self.simulate,
            },
        )
        self._finalize_result(result, events)
        return result

    def _finalize_result(
        self, result: LearningResult, events: list[LearningEvent]
    ) -> None:
        self._last_result = result
        for event in events:
            self.history.add_event(event)
        self.history.add_policy_decision(
            result.recommendation.value, result.reason, version=result.dataset_version
        )
        logger.info(
            "CL cycle recommendation=%s reason=%s version=%s drift=%s",
            result.recommendation.value,
            result.reason,
            result.dataset_version,
            result.drift_status,
        )

    def _resolve_arrays(
        self,
        reference_features: np.ndarray | None,
        reference_labels: np.ndarray | None,
        candidate_features: np.ndarray | None,
        candidate_labels: np.ndarray | None,
        *,
        advance_window: bool,
    ) -> tuple[
        np.ndarray | None,
        np.ndarray | None,
        np.ndarray | None,
        np.ndarray | None,
    ]:
        if candidate_features is not None and candidate_labels is not None:
            cand_x, cand_y = np.asarray(candidate_features), np.asarray(candidate_labels)
        elif self.dataset is not None:
            if self._window_mgr is None:
                self._window_mgr = WindowManager(
                    self.dataset,
                    WindowCursor(window_size=self.window_size, step=max(1, self.window_size // 5)),
                )
                self._window_mgr.bootstrap()
            handle = (
                self._window_mgr.advance_handle()
                if advance_window
                else self._window_mgr.current_handle()
            )
            cand_x, cand_y = handle.features, handle.labels
            self.history.add_event(
                LearningEvent(
                    event_type=LearningEventType.WINDOW_ADVANCED
                    if advance_window
                    else LearningEventType.NEW_DATA_DETECTED,
                    payload=self._window_mgr.cursor.to_dict(),
                )
            )
        else:
            cand_x, cand_y = None, None

        if reference_features is not None and reference_labels is not None:
            ref_x, ref_y = np.asarray(reference_features), np.asarray(reference_labels)
        elif self._reference_version and self.version_manager is not None:
            try:
                ref_x, ref_y = self.version_manager.load_arrays(self._reference_version)
            except KeyError:
                ref_x, ref_y = None, None
        elif self.dataset is not None:
            # Use first half of train as reference baseline for simulation
            train = self.dataset.load(Split.TRAIN)
            mid = max(1, train.size // 2)
            ref_x = train.features[:mid]
            ref_y = train.labels[:mid]
            if self._reference_version is None and self.version_manager is not None:
                parent = self.version_manager.create(
                    ref_x, ref_y, role="parent", metadata={"source": "train_half"}
                )
                self._reference_version = parent.version_id
                self.lineage.link(None, parent.version_id, relation="parent")
                self.history.add_version(parent.to_dict())
        else:
            ref_x, ref_y = None, None

        return ref_x, ref_y, cand_x, cand_y

    def _compute_drift(
        self,
        ref_x: np.ndarray,
        ref_y: np.ndarray,
        cur_x: np.ndarray,
        cur_y: np.ndarray,
    ) -> DriftReport:
        """Reuse Phase 1 drift detector / DatasetManager — never duplicate math."""
        ref_stats = compute_data_stats(
            ref_x, ref_y, split=Split.TRAIN, checksum=sha256_array(ref_x)
        )
        cur_stats = compute_data_stats(
            cur_x, cur_y, split=Split.TRAIN, checksum=sha256_array(cur_x)
        )
        # Re-bin current onto reference edges for fair PSI
        from evonas.domain.data.models import DataStats

        rebinned = rebin_to_edges(
            cur_x.reshape(cur_x.shape[0], -1).ravel()
            if cur_x.ndim > 1
            else cur_x.ravel(),
            ref_stats.bin_edges,
        )
        cur_stats = DataStats(
            split=cur_stats.split,
            n_samples=cur_stats.n_samples,
            feature_mean=cur_stats.feature_mean,
            feature_std=cur_stats.feature_std,
            feature_min=cur_stats.feature_min,
            feature_max=cur_stats.feature_max,
            label_histogram=cur_stats.label_histogram,
            flattened_histogram=tuple(int(x) for x in rebinned),
            bin_edges=ref_stats.bin_edges,
            checksum=cur_stats.checksum,
        )

        if self.dataset is not None:
            return self.dataset.detect_shift(ref_stats, cur_stats)
        if self.drift_detector is not None:
            return self.drift_detector.detect(
                ref_stats,
                cur_stats,
                reference_features=ref_x,
                current_features=cur_x,
            )
        from evonas.domain.data.drift import detect_shift

        return detect_shift(
            ref_stats,
            cur_stats,
            reference_features=ref_x.reshape(ref_x.shape[0], -1),
            current_features=cur_x.reshape(cur_x.shape[0], -1),
            psi_threshold=self.policy.max_drift_psi,
        )

    @staticmethod
    def _map_drift_status(drift: DriftReport) -> str:
        if drift.significant:
            return "significant"
        if drift.psi >= max(0.05, drift.psi_threshold * 0.4):
            return "mild"
        return "none"

    def export_artifacts(self, run_dir: str | Path | None = None) -> dict[str, str]:
        """Export history and lineage (plots generated by application/infra layer)."""
        out = Path(run_dir) if run_dir else self.artifacts_root / "latest"
        out.mkdir(parents=True, exist_ok=True)
        paths = {
            "history_json": str(self.history.export_json(out / "learning_history.json")),
            "history_csv": str(self.history.export_csv(out / "learning_events.csv")),
            "lineage_json": str(self.lineage.export_json(out / "lineage.json")),
        }
        return paths

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        *,
        dataset: IDatasetManager | None = None,
        drift_detector: IDriftDetector | None = None,
    ) -> ContinuousLearningEngine:
        """Construct engine from YAML mapping."""
        cl = dict(config.get("continuous_learning", config.get("continuous", config)) or {})
        policy_raw = cl.get("policy", config.get("policy", {}))
        if isinstance(policy_raw, dict) and policy_raw.get("path"):
            policy = LearningPolicy.from_yaml(policy_raw["path"])
        else:
            policy = LearningPolicy.from_dict(dict(policy_raw or {}))
        retention = RetentionPolicy.from_dict(dict(cl.get("retention", {}) or {}))
        strategy = MergeStrategy(str(cl.get("merge_strategy", "append")))
        root = Path(
            cl.get("artifacts_root")
            or config.get("experiment", {}).get("artifacts_root", "artifacts/continuous_learning")
        )
        return cls(
            dataset=dataset,
            policy=policy,
            retention=retention,
            merge_strategy=strategy,
            window_size=int(cl.get("window_size", 50) or 50),
            sample_fraction=float(cl.get("sample_fraction", 1.0) or 1.0),
            seed=int(config.get("seed") or cl.get("seed") or 42),
            simulate=bool(cl.get("simulate", config.get("simulate", True))),
            artifacts_root=root,
            drift_detector=drift_detector,
        )
