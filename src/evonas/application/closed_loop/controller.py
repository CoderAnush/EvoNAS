"""Closed-Loop Controller — orchestrates services without owning optimization math."""

from __future__ import annotations

import logging
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from evonas import __version__
from evonas.application.closed_loop.workflow import WorkflowExecutor
from evonas.application.optimize import OptimizeUseCase
from evonas.domain.common.errors import DecisionError, EvoNASError
from evonas.domain.decision.context import BudgetSnapshot, DecisionContext
from evonas.domain.decision.engine import DecisionEngine
from evonas.domain.decision.policies import DecisionPolicy
from evonas.domain.lifecycle.history import LifecycleHistory
from evonas.domain.lifecycle.states import LifecycleState, can_transition
from evonas.domain.promotion.manager import PromotionManager
from evonas.domain.trigger.optimization_trigger import OptimizationTrigger, TriggerConfig
from evonas.domain.validation.engine import ValidationEngine
from evonas.infrastructure.closed_loop.visualization import LifecycleVisualizer
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.experiments.artifact_manager import ArtifactManager

logger = logging.getLogger(__name__)


class ClosedLoopController:
    """Orchestrator: Observe → Decide → Optimize → Validate → Promote/Reject.

    Never updates PSO equations, builds networks, trains, or computes fitness
    directly — those remain behind OptimizeUseCase / existing engines.
    """

    def __init__(
        self,
        config: dict[str, Any],
        *,
        config_path: str | Path | None = None,
        output_dir: str | Path | None = None,
        simulate: bool = False,
        dry_run: bool = False,
        config_manager: ConfigurationManager | None = None,
        decision_engine: DecisionEngine | None = None,
        trigger: OptimizationTrigger | None = None,
        validation_engine: ValidationEngine | None = None,
        promotion_manager: PromotionManager | None = None,
        optimize_use_case: OptimizeUseCase | None = None,
        continuous_learning: Any | None = None,
    ) -> None:
        self._cfg = config
        self._config_path = Path(config_path) if config_path else None
        self._simulate = bool(simulate)
        self._dry_run = bool(dry_run or simulate or config.get("simulate", False))
        self._config_manager = config_manager or ConfigurationManager()
        # Optional Phase 7 engine — consumed only via IContinuousLearningEngine.to_observation()
        self._continuous_learning = continuous_learning

        policy_path = (
            config.get("policy", {}).get("path")
            if isinstance(config.get("policy"), dict)
            else None
        )
        if policy_path:
            policy = DecisionPolicy.from_yaml(policy_path)
        else:
            policy = DecisionPolicy.from_dict(dict(config.get("policy", {}) or {}))

        loop_cfg = dict(config.get("closed_loop", {}) or {})
        self._max_cycles = int(loop_cfg.get("max_cycles", 1))
        self._monitor_interval = float(loop_cfg.get("monitor_interval_seconds", 0.0))
        self._seed = int(config.get("seed", 42))
        self._run_id = str(config.get("run_id", "closed_loop_v1"))
        self._algorithm = str(
            config.get("optimization", {}).get("algorithm", "sapso")
        ).lower()

        trigger_cfg = TriggerConfig.from_dict(dict(config.get("triggers", {}) or {}))
        self._policy = policy
        self._decisions = decision_engine or DecisionEngine(policy)
        self._trigger = trigger or OptimizationTrigger(policy, trigger_cfg)
        self._validation = validation_engine or ValidationEngine(policy)
        self._promotion = promotion_manager or PromotionManager()
        self._optimize = optimize_use_case or OptimizeUseCase(
            config_manager=self._config_manager
        )
        self._workflow = WorkflowExecutor(
            decisions=self._decisions,
            validation=self._validation,
            promotion=self._promotion,
            algorithm=self._algorithm,
        )

        artifacts_root = output_dir or config.get("experiment", {}).get(
            "artifacts_root", "artifacts/closed_loop"
        )
        self._artifacts = ArtifactManager(root=artifacts_root)
        self._run_dir = self._artifacts.create_run(self._run_id)
        if self._config_path and self._config_path.exists():
            self._artifacts.copy_config(self._run_dir, self._config_path)

        self._state = LifecycleState.IDLE
        self._history = LifecycleHistory(
            metadata={
                "evonas_version": __version__,
                "simulate": self._simulate,
                "dry_run": self._dry_run,
                "algorithm": self._algorithm,
                "seed": self._seed,
            }
        )
        self._optimizations_used = 0
        self._current_model_id = "baseline_local"
        self._current_metrics: dict[str, float] = dict(
            config.get("baseline", {}).get("metrics")
            or {"accuracy": float(config.get("baseline", {}).get("accuracy", 0.55))}
        )
        self._best_metrics = dict(self._current_metrics)
        self._opt_history: list[dict[str, Any]] = []
        self._last_opt_time: str | None = None
        self._cycles_done = 0

    @property
    def state(self) -> LifecycleState:
        """Current lifecycle state."""
        return self._state

    @property
    def history(self) -> LifecycleHistory:
        """Lifecycle history."""
        return self._history

    @property
    def run_dir(self) -> Path:
        """Artifact directory for this controller run."""
        return self._run_dir

    def transition(self, target: LifecycleState, reason: str) -> None:
        """Enforce and log a lifecycle transition."""
        if not can_transition(self._state, target):
            raise DecisionError(
                f"illegal transition {self._state.value} → {target.value}",
                code="EN_DEC_002",
            )
        logger.info(
            "Lifecycle %s → %s (%s)", self._state.value, target.value, reason
        )
        self._history.add_transition(self._state.value, target.value, reason)
        self._state = target

    def run(self, *, max_cycles: int | None = None) -> dict[str, Any]:
        """Run up to ``max_cycles`` observe→finish cycles."""
        limit = int(max_cycles if max_cycles is not None else self._max_cycles)
        summaries: list[dict[str, Any]] = []
        try:
            if self._state == LifecycleState.IDLE:
                self.transition(LifecycleState.MONITORING, "start_loop")
            for _ in range(limit):
                summary = self.run_once()
                summaries.append(summary)
                self._cycles_done += 1
                if summary.get("stop"):
                    break
                if self._monitor_interval > 0 and not self._simulate:
                    time.sleep(self._monitor_interval)
            if self._state == LifecycleState.MONITORING and can_transition(
                self._state, LifecycleState.COMPLETED
            ):
                self.transition(LifecycleState.COMPLETED, "max_cycles_reached")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Closed-loop failed: %s", exc)
            self._recover(exc)
        return self._finalize(summaries)

    def run_once(self) -> dict[str, Any]:
        """Single Observe → Decision → (Optimize…) → Monitor cycle."""
        try:
            if self._state == LifecycleState.IDLE:
                self.transition(LifecycleState.MONITORING, "observe")
            if self._state != LifecycleState.MONITORING:
                if can_transition(self._state, LifecycleState.MONITORING):
                    self.transition(LifecycleState.MONITORING, "resume_monitoring")

            ctx = self._observe()
            self.transition(LifecycleState.DECISION, "evaluate_policies")

            trigger = self._trigger.evaluate(ctx)
            ctx = replace(
                ctx,
                trigger_consider=trigger.consider,
                trigger_reasons=trigger.reasons,
            )
            self._history.add_event("trigger", **trigger.to_dict())

            d_start = self._decisions.should_start_optimization(ctx)
            self._persist_decision(d_start)

            if not d_start.outcome:
                self.transition(LifecycleState.MONITORING, "skip_optimization")
                return {
                    "optimized": False,
                    "decision": d_start.to_dict(),
                    "state": self._state.value,
                    "stop": self._optimizations_used >= self._policy.max_optimizations,
                }

            result = self._workflow.run_optimization_pipeline(
                ctx,
                transition=self.transition,
                run_optimizer=self._run_optimizer,
                extract_metrics=self._extract_candidate_metrics,
                persist_decision=self._persist_decision,
                history=self._history,
                current_model_id=self._current_model_id,
                current_metrics=self._current_metrics,
                dry_run=self._dry_run,
            )
            if result.get("accepted"):
                self._current_model_id = str(result["new_model_id"])
                self._current_metrics = dict(result["new_metrics"])
                if self._current_metrics.get("accuracy", 0) >= self._best_metrics.get(
                    "accuracy", 0
                ):
                    self._best_metrics = dict(self._current_metrics)

            self._optimizations_used += 1
            self._last_opt_time = datetime.now(timezone.utc).isoformat()
            delta = float(result["candidate_metrics"].get("accuracy", 0)) - float(
                ctx.current_metrics.get("accuracy", 0)
            )
            self._opt_history.append(
                {
                    "candidate_id": result["candidate_id"],
                    "accepted": result.get("accepted"),
                    "delta_accuracy": delta,
                    "best_fitness": result.get("optimization", {}).get("best_fitness"),
                }
            )
            self.transition(LifecycleState.MONITORING, "cycle_complete")
            result["state"] = self._state.value
            result["stop"] = self._optimizations_used >= self._policy.max_optimizations
            return result
        except EvoNASError as exc:
            self._recover(exc)
            return {
                "optimized": False,
                "error": str(exc),
                "state": self._state.value,
                "stop": True,
            }
        except Exception as exc:  # noqa: BLE001
            self._recover(exc)
            return {
                "optimized": False,
                "error": str(exc),
                "state": self._state.value,
                "stop": True,
            }

    def _observe(self) -> DecisionContext:
        """Collect metrics / drift stubs into DecisionContext."""
        hours_since = None
        if self._last_opt_time:
            try:
                last = datetime.fromisoformat(self._last_opt_time)
                hours_since = (
                    datetime.now(timezone.utc) - last
                ).total_seconds() / 3600.0
            except ValueError:
                hours_since = None
        budgets = BudgetSnapshot(
            max_optimizations=self._policy.max_optimizations,
            optimizations_used=self._optimizations_used,
            max_search_wallclock_minutes=self._policy.max_search_wallclock_minutes,
            cooldown_hours=self._policy.cooldown_hours,
            hours_since_last_optimization=hours_since,
        )
        drift_cfg = dict(self._cfg.get("observation", {}) or {})
        # Phase 7: merge published CL observation without owning data evolution logic
        if self._continuous_learning is not None and hasattr(
            self._continuous_learning, "to_observation"
        ):
            cl_obs = dict(self._continuous_learning.to_observation() or {})
            drift_cfg = {**drift_cfg, **cl_obs}
        drift_status = str(drift_cfg.get("drift_status", "none"))
        force = bool(drift_cfg.get("force_optimization", False))
        dataset_version = str(
            drift_cfg.get("dataset_version")
            or self._cfg.get("dataset", {}).get("config_path", "toy_quick")
        )
        experiment_metadata: dict[str, Any] = {
            "experiment_id": self._run_id,
            "simulate": self._simulate,
            "algorithm": self._algorithm,
        }
        if drift_cfg.get("cl_recommendation") is not None:
            experiment_metadata["cl_recommendation"] = drift_cfg.get("cl_recommendation")
            experiment_metadata["cl_reason"] = drift_cfg.get("cl_reason")
            experiment_metadata["data_availability"] = drift_cfg.get(
                "data_availability", True
            )
        ctx = DecisionContext(
            mode="simulate" if self._simulate else "quick",
            system_mode=self._state.value,
            current_model_id=self._current_model_id,
            current_metrics=dict(self._current_metrics),
            best_metrics=dict(self._best_metrics),
            dataset_version=dataset_version,
            drift_status=drift_status,
            drift_report=dict(drift_cfg.get("drift_report", {}) or {}),
            optimization_state="idle",
            optimization_history=list(self._opt_history),
            last_optimization_time=self._last_opt_time,
            budgets=budgets,
            force_optimization=force,
            accuracy_threshold=(
                float(self._policy.accuracy_floor)
                if self._policy.accuracy_floor > 0
                else None
            ),
            experiment_metadata=experiment_metadata,
        )
        self._history.add_event(
            "observe", metrics=ctx.current_metrics, drift=drift_status
        )
        return ctx

    def _run_optimizer(self) -> dict[str, Any]:
        """Delegate to OptimizeUseCase — never touch PSO internals."""
        opt_cfg = self._cfg.get("optimization", {})
        nested_path = None
        if isinstance(opt_cfg, dict):
            nested_path = opt_cfg.get("config_path")
        if nested_path:
            path = Path(str(nested_path))
        else:
            path = self._run_dir / "optimize_resolved.yaml"
            payload = {
                "run_id": f"{self._run_id}_opt_{self._optimizations_used}",
                "seed": self._seed,
                "search_space": self._cfg.get(
                    "search_space", {"path": "configs/search_spaces/sphere_2d.yaml"}
                ),
                "optimization": {
                    **dict(self._cfg.get("optimization", {}) or {}),
                    "algorithm": self._algorithm,
                    "log_particles": False,
                },
                "adaptation": dict(self._cfg.get("adaptation", {}) or {}),
                "fitness": dict(
                    self._cfg.get(
                        "fitness",
                        {"mode": "mock", "landscape": "sphere", "sense": "maximize"},
                    )
                    or {}
                ),
                "experiment": {"artifacts_root": str(self._run_dir / "optimization")},
            }
            if self._dry_run:
                payload["fitness"] = {
                    "mode": "mock",
                    "landscape": str(payload["fitness"].get("landscape", "sphere")),
                    "sense": "maximize",
                }
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

        started = time.perf_counter()
        summary = self._optimize.run(
            path,
            output_dir=self._run_dir / "optimization",
            dry_run=self._dry_run,
            verbose=False,
        )
        summary["seconds"] = time.perf_counter() - started
        return summary

    def _extract_candidate_metrics(self, opt_summary: dict[str, Any]) -> dict[str, float]:
        """Map optimizer summary to candidate accuracy for validation."""
        demo = self._cfg.get("candidate_metrics_override")
        if isinstance(demo, dict) and "accuracy" in demo:
            return {"accuracy": float(demo["accuracy"])}
        fitness = opt_summary.get("best_fitness")
        if fitness is not None:
            f = float(fitness)
            if opt_summary.get("fitness_mode") == "mock" or self._dry_run:
                base = float(self._current_metrics.get("accuracy", 0.5))
                bump = max(0.0, min(0.2, (f + 10.0) / 50.0))
                return {"accuracy": min(0.99, base + bump)}
            return {"accuracy": float(f)}
        base = float(self._current_metrics.get("accuracy", 0.5))
        improve = float(self._cfg.get("simulate_improvement", 0.02))
        return {"accuracy": base + improve}

    def _persist_decision(self, record: Any) -> None:
        self._history.add_decision(record.to_dict())

    def _recover(self, exc: Exception) -> None:
        """Failure recovery → FAILED → MONITORING safe state."""
        self._history.add_event("failure", error=str(exc), state=self._state.value)
        try:
            if self._state != LifecycleState.FAILED:
                if can_transition(self._state, LifecycleState.FAILED):
                    self.transition(LifecycleState.FAILED, f"error:{exc}")
                else:
                    self._history.add_transition(
                        self._state.value,
                        LifecycleState.FAILED.value,
                        f"forced:{exc}",
                    )
                    self._state = LifecycleState.FAILED
            if can_transition(self._state, LifecycleState.MONITORING):
                self.transition(LifecycleState.MONITORING, "recovery")
        except DecisionError:
            self._state = LifecycleState.MONITORING
            self._history.add_transition("failed", "monitoring", "recovery_fallback")

    def _finalize(self, cycle_summaries: list[dict[str, Any]]) -> dict[str, Any]:
        self._history.export_json(self._run_dir / "lifecycle_history.json")
        self._history.export_csv(self._run_dir / "lifecycle_transitions.csv")
        self._history.export_decisions_jsonl(self._run_dir / "decisions.jsonl")
        plots = LifecycleVisualizer().plot_all(self._history, self._run_dir / "plots")
        summary = {
            "run_id": self._run_id,
            "evonas_version": __version__,
            "state": self._state.value,
            "simulate": self._simulate,
            "dry_run": self._dry_run,
            "algorithm": self._algorithm,
            "cycles": self._cycles_done,
            "optimizations_used": self._optimizations_used,
            "current_model_id": self._current_model_id,
            "current_metrics": self._current_metrics,
            "best_metrics": self._best_metrics,
            "promotions": [p.to_dict() for p in self._promotion.history],
            "cycle_summaries": cycle_summaries,
            "plots": plots,
            "run_dir": str(self._run_dir),
        }
        self._artifacts.write_json(self._run_dir, "summary.json", summary)
        return summary
