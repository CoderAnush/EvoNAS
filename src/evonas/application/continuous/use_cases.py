"""Application use-cases for continuous learning CLI (Phase 7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from evonas.domain.continuous.engine import ContinuousLearningEngine
from evonas.domain.continuous.events import LearningResult
from evonas.domain.continuous.replay import ReplaySupport
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.data.factory import create_dataset_manager


class ContinuousLearningUseCase:
    """Run / detect / replay continuous-learning workflows (simulation)."""

    def __init__(self, *, config_manager: ConfigurationManager | None = None) -> None:
        self._config_manager = config_manager or ConfigurationManager()

    def learn(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        cycles: int = 1,
        advance_window: bool = True,
    ) -> dict[str, Any]:
        """Run one or more CL cycles and export artifacts."""
        path = Path(config_path)
        cfg = self._config_manager.load(path)
        dataset = None
        ds_cfg = cfg.get("dataset", {})
        if isinstance(ds_cfg, dict) and ds_cfg.get("config_path"):
            dataset = create_dataset_manager(
                str(ds_cfg["config_path"]),
                treat_as_dataset_config=True,
                config_manager=self._config_manager,
            )
            dataset.prepare()
        engine = ContinuousLearningEngine.from_config(cfg, dataset=dataset)
        if output_dir:
            engine.artifacts_root = Path(output_dir)
            engine.artifacts_root.mkdir(parents=True, exist_ok=True)
            from evonas.domain.continuous.versions import DataVersionManager

            engine.version_manager = DataVersionManager(engine.artifacts_root / "versions")

        results: list[dict[str, Any]] = []
        for i in range(max(1, int(cycles))):
            # Synthetic candidate shift for simulation when no explicit arrays
            if dataset is None:
                result = self._synthetic_cycle(engine, step=i)
            else:
                result = engine.run_cycle(advance_window=advance_window and i > 0)
            results.append(result.to_dict())

        artifacts = engine.export_artifacts(engine.artifacts_root / "run")
        from evonas.infrastructure.continuous.visualization import ContinuousLearningVisualizer

        plots = ContinuousLearningVisualizer().plot_all(
            engine.history, engine.lineage, engine.artifacts_root / "run" / "plots"
        )
        artifacts.update(plots)
        engine.lineage.export_json(engine.artifacts_root / "run" / "lineage.json")
        summary = {
            "cycles": len(results),
            "results": results,
            "last_recommendation": results[-1]["recommendation"] if results else None,
            "observation": engine.to_observation(),
            "artifacts": artifacts,
            "run_dir": str(engine.artifacts_root / "run"),
            "simulate": engine.simulate,
        }
        (engine.artifacts_root / "run" / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )
        return summary

    def detect_data(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Detect changes only (no merge/version unless arrays provided)."""
        path = Path(config_path)
        cfg = self._config_manager.load(path)
        engine = ContinuousLearningEngine.from_config(cfg)
        if output_dir:
            engine.artifacts_root = Path(output_dir)
        # Build synthetic reference/candidate from config simulation block
        sim = dict(cfg.get("simulation", {}) or {})
        n_ref = int(sim.get("n_reference", 100))
        n_new = int(sim.get("n_new", 30))
        shift = float(sim.get("feature_shift", 0.0))
        rng = np.random.default_rng(int(cfg.get("seed", 42)))
        ref_x = rng.normal(0.0, 1.0, size=(n_ref, 4))
        ref_y = rng.integers(0, 2, size=(n_ref,))
        cand_x = rng.normal(shift, 1.0, size=(n_ref + n_new, 4))
        cand_y = rng.integers(0, 2, size=(n_ref + n_new,))
        report = engine.detect_new_data(ref_x, ref_y, cand_x, cand_y)
        payload = {
            "change_report": report.to_dict(),
            "simulate": True,
            "seed": cfg.get("seed", 42),
        }
        out = engine.artifacts_root / "detect"
        out.mkdir(parents=True, exist_ok=True)
        (out / "change_report.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return payload

    def replay_learning(
        self,
        history_path: str | Path,
        *,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Deterministically replay a prior learning history."""
        replay = ReplaySupport.from_history_json(history_path)
        steps = replay.replay_all()
        out_dir = Path(output_dir) if output_dir else Path(history_path).parent / "replay"
        out_dir.mkdir(parents=True, exist_ok=True)
        replay.cursor = 0
        replay.export_json(out_dir / "replay_script.json")
        summary = {
            "steps": len(steps),
            "replay": steps,
            "run_dir": str(out_dir),
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )
        return summary

    def _synthetic_cycle(
        self, engine: ContinuousLearningEngine, *, step: int
    ) -> LearningResult:
        """Deterministic synthetic data evolution for CLI simulation."""
        rng = np.random.default_rng(engine.seed + step)
        n_ref = 80
        n_new = max(engine.policy.min_new_samples, 20)
        shift = 0.05 * step
        if engine.last_result is None or engine.last_result.dataset_version is None:
            ref_x = rng.normal(0.0, 1.0, size=(n_ref, 4))
            ref_y = rng.integers(0, 3, size=(n_ref,))
            # First cycle bootstraps reference
            return engine.run_cycle(
                candidate_features=ref_x, candidate_labels=ref_y
            )
        assert engine.version_manager is not None
        ref_x, ref_y = engine.version_manager.load_arrays(
            engine.last_result.dataset_version
        )
        cand_x = np.concatenate(
            [ref_x, rng.normal(shift, 1.0, size=(n_new, ref_x.shape[1]))], axis=0
        )
        cand_y = np.concatenate(
            [ref_y, rng.integers(0, 3, size=(n_new,))], axis=0
        )
        # Stronger shift on later steps to exercise drift recommendations
        if step >= 1:
            cand_x = cand_x + shift * 2.0
        return engine.run_cycle(
            reference_features=ref_x,
            reference_labels=ref_y,
            candidate_features=cand_x,
            candidate_labels=cand_y,
        )
