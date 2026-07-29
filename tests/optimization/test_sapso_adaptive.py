"""Adaptive controller and SAPSO unit tests."""

from __future__ import annotations

from pathlib import Path

from evonas.domain.optimization.adaptive import (
    AdaptiveConfig,
    AdaptiveController,
    AdaptivePhase,
    SwarmBehaviorStats,
)
from evonas.domain.optimization.adaptive_history import AdaptiveHistoryRecorder
from evonas.domain.optimization.comparison import OptimizerComparison
from evonas.domain.optimization.particle import Particle
from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig
from evonas.domain.optimization.sapso import SelfAdaptivePSO
from evonas.domain.search_space.genes import GeneSpec
from evonas.domain.search_space.space import SearchSpace
from evonas.infrastructure.optimization.mock_fitness import MockFitnessEvaluator


def _sphere_space() -> SearchSpace:
    return SearchSpace(
        name="sphere_2d",
        genes=(
            GeneSpec("x0", "float", -5.0, 5.0),
            GeneSpec("x1", "float", -5.0, 5.0),
        ),
        input_shape=(1,),
        num_classes=2,
    )


def _stats(**kwargs: object) -> SwarmBehaviorStats:
    base = dict(
        iteration=10,
        max_iterations=50,
        normalized_diversity=0.2,
        mean_fitness=0.5,
        fitness_variance=0.1,
        gbest_fitness=0.6,
        gbest_improvement=0.0,
        mean_pbest_improvement=0.0,
        mean_velocity=0.1,
        improvement_rate=0.0,
        no_improve_count=0,
        convergence_rate=0.5,
    )
    base.update(kwargs)
    return SwarmBehaviorStats(**base)  # type: ignore[arg-type]


def test_adaptive_config_from_dict() -> None:
    cfg = AdaptiveConfig.from_dict(
        {
            "inertia": {"w_min": 0.3, "w_max": 0.95, "alpha": 0.4},
            "acceleration": {"c_min": 0.6, "c_max": 2.4, "delta_collapse": 0.08},
            "stagnation_iters": 10,
        }
    )
    assert cfg.w_min == 0.3
    assert cfg.w_max == 0.95
    assert cfg.delta_collapse == 0.08
    assert cfg.stagnation_iters == 10


def test_coefficient_bounds_always_respected() -> None:
    ctrl = AdaptiveController(AdaptiveConfig())
    for delta in (0.0, 0.02, 0.1, 0.5, 1.0):
        for eta in (-0.1, 0.0, 0.001, 0.02):
            params = ctrl.update(
                _stats(normalized_diversity=delta, improvement_rate=eta, no_improve_count=0)
            )
            assert AdaptiveConfig().w_min <= params.w <= AdaptiveConfig().w_max
            assert AdaptiveConfig().c_min <= params.c1 <= AdaptiveConfig().c_max
            assert AdaptiveConfig().c_min <= params.c2 <= AdaptiveConfig().c_max


def test_diversity_collapse_raises_w_and_c1() -> None:
    cfg = AdaptiveConfig(delta_collapse=0.05, w_min=0.4, w_max=0.9)
    ctrl = AdaptiveController(cfg)
    high = ctrl.update(_stats(normalized_diversity=0.4, improvement_rate=0.05, iteration=20))
    low = ctrl.update(
        _stats(
            normalized_diversity=0.01,
            improvement_rate=0.0,
            no_improve_count=10,
            iteration=20,
        )
    )
    assert low.phase == AdaptivePhase.STAGNATION_RECOVERY
    assert low.w >= high.w or low.c1 >= high.c1
    assert any("R3" in r for r in low.reasons)


def test_state_machine_stagnation() -> None:
    ctrl = AdaptiveController(AdaptiveConfig(stagnation_iters=3))
    params = ctrl.update(_stats(no_improve_count=5, normalized_diversity=0.2, iteration=15))
    assert params.phase == AdaptivePhase.STAGNATION_RECOVERY


def test_sapso_improves_on_sphere() -> None:
    space = _sphere_space()
    cfg = StandardPSOConfig(
        swarm_size=16,
        max_iterations=20,
        maximize=True,
        log_particles=False,
        seed=0,
    )
    sapso = SelfAdaptivePSO(cfg, adaptive_config=AdaptiveConfig())
    sapso.set_evaluator(MockFitnessEvaluator("sphere", maximize=True))
    sapso.initialize(space, seed=0)
    initial = sapso.get_history().records[0].gbest_fitness
    result = sapso.run()
    assert result.best_fitness >= initial
    assert result.metadata["algorithm"] == "sapso"
    hist = sapso.export_adaptive_history()
    assert len(hist["records"]) >= 1
    assert "w" in hist["curves"]
    # coefficients vary or at least stay in range across run
    assert all(0.4 <= w <= 0.9 for w in hist["curves"]["w"])


def test_standard_pso_still_fixed_coeffs() -> None:
    space = _sphere_space()
    cfg = StandardPSOConfig(
        swarm_size=8,
        max_iterations=5,
        w=0.729,
        c1=1.49445,
        c2=1.49445,
        maximize=True,
        log_particles=False,
    )
    pso = StandardPSO(cfg)
    pso.set_evaluator(MockFitnessEvaluator("sphere", maximize=True))
    pso.initialize(space, seed=1)
    pso.run()
    for record in pso.get_history().records:
        assert abs(record.w - 0.729) < 1e-12
        assert abs(record.c1 - 1.49445) < 1e-12


def test_adaptive_history_export(tmp_path: Path) -> None:
    payload = {
        "records": [
            {
                "iteration": 0,
                "w": 0.7,
                "c1": 1.5,
                "c2": 2.6,
                "phase": "exploration",
                "exploration_pressure": 0.5,
                "improvement_rate": 0.0,
                "normalized_diversity": 0.3,
            }
        ],
        "transitions": [{"iteration": 1, "from": "exploration", "to": "balanced", "reason": "x"}],
    }
    rec = AdaptiveHistoryRecorder()
    assert rec.export_json(payload, tmp_path / "a.json").exists()
    assert rec.export_csv(payload, tmp_path / "a.csv").exists()
    assert rec.export_transitions_csv(payload, tmp_path / "t.csv").exists()


def test_comparison_framework() -> None:
    space = _sphere_space()
    cfg = StandardPSOConfig(
        swarm_size=8, max_iterations=8, maximize=True, log_particles=False
    )

    def factory() -> MockFitnessEvaluator:
        return MockFitnessEvaluator("sphere", maximize=True)

    report = OptimizerComparison().compare(
        space=space,
        evaluator_factory=factory,
        seeds=[0, 1, 2],
        pso_config=cfg,
        adaptive_config=AdaptiveConfig(),
        maximize=True,
    )
    assert report["winner"] in {"sapso", "standard_pso", "tie"}
    assert "aggregates" in report["standard_pso"]
    assert "aggregates" in report["sapso"]


def test_collapsed_swarm_stats_feed_controller() -> None:
    space = _sphere_space()
    # All particles near same point → low diversity
    particles = [
        Particle.from_vectors(f"p{i}", [0.0, 0.0], [0.0, 0.0], fitness=0.1) for i in range(5)
    ]
    ctrl = AdaptiveController(AdaptiveConfig(delta_collapse=0.05))
    stats = ctrl.compute_stats(
        particles=particles,
        space=space,
        iteration=12,
        max_iterations=40,
        gbest_fitness=0.1,
        no_improve_count=0,
        previous_gbest=0.1,
        maximize=True,
    )
    assert stats.normalized_diversity < 0.05
    params = ctrl.update(stats)
    assert params.phase == AdaptivePhase.STAGNATION_RECOVERY
