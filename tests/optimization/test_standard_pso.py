"""Standard PSO on synthetic landscapes."""

from __future__ import annotations

from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig
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


def test_pso_improves_on_sphere() -> None:
    space = _sphere_space()
    cfg = StandardPSOConfig(
        swarm_size=16,
        max_iterations=25,
        w=0.729,
        c1=1.49445,
        c2=1.49445,
        maximize=True,
        seed=0,
        log_particles=False,
    )
    pso = StandardPSO(cfg)
    pso.set_evaluator(MockFitnessEvaluator("sphere", maximize=True))
    pso.initialize(space, seed=0)
    initial = pso.get_history().records[0].gbest_fitness
    result = pso.run()
    assert result.best_fitness >= initial
    assert result.iterations == 25
    assert result.evaluations > 0
    # Should approach 0 from below (maximizing -||x||^2)
    assert result.best_fitness > -5.0


def test_pso_rastrigin_seeded_deterministic() -> None:
    space = _sphere_space()
    cfg = StandardPSOConfig(swarm_size=8, max_iterations=5, maximize=True, log_particles=False)

    def _run(seed: int) -> list[float]:
        pso = StandardPSO(cfg)
        pso.set_evaluator(MockFitnessEvaluator("rastrigin", maximize=True))
        pso.initialize(space, seed=seed)
        result = pso.run()
        return result.history.best_fitness_curve()

    assert _run(11) == _run(11)


def test_stopping_target_fitness() -> None:
    space = _sphere_space()
    cfg = StandardPSOConfig(
        swarm_size=10,
        max_iterations=50,
        maximize=True,
        target_fitness=-0.01,
        log_particles=False,
    )
    pso = StandardPSO(cfg)
    pso.set_evaluator(MockFitnessEvaluator("sphere", maximize=True))
    pso.initialize(space, seed=1)
    result = pso.run()
    assert result.stopped_reason in {"target_fitness", "max_iterations"}
