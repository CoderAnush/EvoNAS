"""Demo-mode synthetic payloads for presentations (no training/optimization)."""

from __future__ import annotations

from typing import Any

from evonas import __version__


def demo_landing() -> dict[str, Any]:
    """Landing-page KPIs for demo mode."""
    return {
        "version": __version__,
        "status": "READY (Demo Mode)",
        "dataset": "toy_quick @ v1",
        "optimizer": "sapso",
        "architecture": "cnn_quick_best",
        "accuracy": 0.912,
        "lifecycle_state": "monitoring",
        "recommendation": "HOLD",
        "system_health": "healthy",
        "last_optimization": "2026-07-30T10:15:00Z",
        "last_training": "2026-07-30T10:12:00Z",
        "last_dataset_update": "2026-07-30T09:50:00Z",
        "demo": True,
    }


def demo_optimization_history() -> dict[str, Any]:
    """Synthetic swarm history for Optimization / SAPSO pages."""
    records = []
    for i in range(1, 26):
        records.append(
            {
                "iteration": i,
                "gbest_fitness": -max(0.05, 2.5 * (0.85**i)),
                "mean_fitness": -max(0.1, 3.0 * (0.88**i)),
                "diversity": max(0.05, 0.45 * (0.92**i)),
                "evaluations": i * 16,
                "w": 0.4 + 0.4 * (0.9 ** (i / 5)),
                "c1": 1.2 + 0.6 * (0.85 ** (i / 4)),
                "c2": 2.9 - (1.2 + 0.6 * (0.85 ** (i / 4))),
            }
        )
    return {
        "metadata": {"demo": True, "algorithm": "sapso"},
        "records": records,
    }


def demo_adaptive_history() -> dict[str, Any]:
    """Synthetic adaptive coefficient / phase payload."""
    hist = demo_optimization_history()
    records = []
    phases = ["exploration", "balanced", "exploitation", "stagnation_recovery"]
    for i, row in enumerate(hist["records"], start=1):
        phase = phases[min(3, (i - 1) // 7)]
        records.append(
            {
                "iteration": i,
                "w": row["w"],
                "c1": row["c1"],
                "c2": row["c2"],
                "phase": phase,
                "normalized_diversity": row["diversity"],
                "improvement_rate": 0.02 * (0.9**i),
                "exploration_pressure": 0.5 if phase == "exploration" else 0.2,
            }
        )
    return {
        "algorithm": "sapso",
        "records": records,
        "transitions": [
            {"iteration": 8, "from": "exploration", "to": "balanced", "reason": "diversity_ok"},
            {"iteration": 15, "from": "balanced", "to": "exploitation", "reason": "eta_good"},
            {
                "iteration": 22,
                "from": "exploitation",
                "to": "stagnation_recovery",
                "reason": "no_improve",
            },
        ],
        "curves": {
            "w": [r["w"] for r in records],
            "c1": [r["c1"] for r in records],
            "c2": [r["c2"] for r in records],
            "diversity": [r["normalized_diversity"] for r in records],
            "phase": [r["phase"] for r in records],
            "gbest": [hist["records"][i]["gbest_fitness"] for i in range(len(records))],
        },
    }


def demo_lifecycle() -> dict[str, Any]:
    """Synthetic closed-loop history."""
    return {
        "metadata": {"demo": True, "algorithm": "sapso"},
        "transitions": [
            {"source": "idle", "target": "monitoring", "reason": "start_loop", "timestamp": "t0"},
            {"source": "monitoring", "target": "decision", "reason": "evaluate", "timestamp": "t1"},
            {"source": "decision", "target": "optimizing", "reason": "start", "timestamp": "t2"},
            {"source": "optimizing", "target": "training", "reason": "done", "timestamp": "t3"},
            {"source": "training", "target": "evaluation", "reason": "metrics", "timestamp": "t4"},
            {"source": "evaluation", "target": "validation", "reason": "validate", "timestamp": "t5"},
            {"source": "validation", "target": "accepted", "reason": "improve", "timestamp": "t6"},
            {"source": "accepted", "target": "monitoring", "reason": "cycle", "timestamp": "t7"},
        ],
        "decisions": [
            {
                "question": "should_start_optimization",
                "outcome": True,
                "action": "START_OPTIMIZATION",
                "rationale": {"reason": "drift_significant"},
            },
            {
                "question": "should_accept_candidate",
                "outcome": True,
                "action": "ACCEPT",
                "rationale": {"delta": 0.03},
            },
        ],
        "promotions": [
            {"accepted": True, "model_id": "cand_01", "reason": "validation_ok", "metrics": {"accuracy": 0.91}}
        ],
        "events": [{"kind": "observe", "drift": "significant"}],
    }


def demo_learning() -> dict[str, Any]:
    """Synthetic continuous-learning history."""
    return {
        "metadata": {"demo": True},
        "events": [
            {
                "event_type": "NewDataDetected",
                "timestamp": "t0",
                "recommendation": None,
                "payload": {"new_samples": 40},
            },
            {
                "event_type": "DatasetVersionCreated",
                "timestamp": "t1",
                "dataset_version": "dv_demo_1",
                "recommendation": None,
            },
            {
                "event_type": "DriftComputed",
                "timestamp": "t2",
                "payload": {"psi": 0.31, "significant": True},
            },
            {
                "event_type": "OptimizeRecommended",
                "timestamp": "t3",
                "recommendation": "OPTIMIZE_ARCH",
                "payload": {"reason": "significant_drift"},
            },
        ],
        "versions": [
            {"version_id": "dv_demo_0", "n_samples": 100, "role": "parent"},
            {"version_id": "dv_demo_1", "n_samples": 140, "role": "training"},
        ],
        "drift_reports": [
            {"psi": 0.12, "significant": False, "timestamp": "tA"},
            {"psi": 0.31, "significant": True, "timestamp": "tB"},
        ],
        "policy_decisions": [
            {"recommendation": "OPTIMIZE_ARCH", "reason": "significant_drift", "timestamp": "t3"}
        ],
    }


def demo_lineage() -> dict[str, Any]:
    """Synthetic lineage graph."""
    return {
        "nodes": {
            "dv_demo_0": {"version_id": "dv_demo_0", "role": "parent"},
            "dv_demo_1": {"version_id": "dv_demo_1", "role": "training"},
        },
        "edges": [
            {
                "parent_id": "dv_demo_0",
                "child_id": "dv_demo_1",
                "relation": "training",
                "timestamp": "t1",
                "metadata": {},
            }
        ],
    }


def demo_training_history() -> dict[str, Any]:
    """Synthetic training curves."""
    epochs = []
    for e in range(1, 11):
        epochs.append(
            {
                "epoch": e,
                "train_loss": 1.2 * (0.85**e),
                "val_loss": 1.3 * (0.87**e),
                "train_accuracy": min(0.99, 0.55 + 0.04 * e),
                "val_accuracy": min(0.95, 0.50 + 0.038 * e),
            }
        )
    return {"epochs": epochs}


def demo_comparison() -> dict[str, Any]:
    """Synthetic PSO vs SAPSO comparison."""
    return {
        "winner": "sapso",
        "delta_mean_fitness_sapso_minus_pso": 0.12,
        "standard_pso": {"mean_best_fitness": -0.42, "mean_iterations": 25},
        "sapso": {"mean_best_fitness": -0.30, "mean_iterations": 22},
        "seeds": [1, 2, 3, 5, 7],
        "demo": True,
    }


def demo_architecture_mermaid() -> str:
    """Mermaid diagram for Architecture Explorer demo."""
    return """flowchart TB
  IN[Input 1x28x28] --> C1[Conv 16]
  C1 --> R1[ReLU]
  R1 --> P1[MaxPool]
  P1 --> C2[Conv 32]
  C2 --> R2[ReLU]
  R2 --> F[Flatten]
  F --> D[Dense 64]
  D --> OUT[Softmax 10]
"""
