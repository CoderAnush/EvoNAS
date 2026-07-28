"""Fitness cache, calculator, and adapter tests."""

from __future__ import annotations

from pathlib import Path

from evonas.domain.architecture.complexity import ComplexityReport
from evonas.domain.fitness.calculator import FitnessCalculator
from evonas.domain.fitness.types import Fitness, FitnessConfig
from evonas.domain.optimization.adapter import SearchSpaceAdapter
from evonas.domain.optimization.cache import EvaluationCache
from evonas.domain.optimization.particle import Particle
from evonas.domain.search_space.space import SearchSpace
from evonas.domain.training.types import MetricSet


def test_fitness_calculator_accuracy() -> None:
    calc = FitnessCalculator(FitnessConfig(accuracy_weight=1.0, param_lambda=0.0))
    fit = calc.compute(MetricSet(primary="accuracy", values={"accuracy": 0.8}))
    assert fit.value == 0.8
    fit2 = calc.compute(
        {"accuracy": 0.8},
        ComplexityReport(1000, 5, 1, 1),
    )
    assert "accuracy" in fit2.components


def test_evaluation_cache_hit(tmp_path: Path) -> None:
    cache = EvaluationCache(disk_dir=tmp_path / "cache")
    fit = Fitness(value=0.9, components={"accuracy": 0.9})
    cache.put("abc123", fit, train_hash="t1")
    hit = cache.get("abc123", "t1")
    assert hit is not None
    assert hit.fitness.value == 0.9
    assert cache.stats()["hits"] >= 1
    # second get from memory
    assert cache.get("abc123", "t1") is not None


def test_search_space_adapter_decode_encode() -> None:
    space = SearchSpace.cnn_quick()
    adapter = SearchSpaceAdapter(space)
    pos = [1.2, 16.0, 24.0, 0.2, 0.1, 32.0]
    spec = adapter.decode(pos, name="t")
    assert adapter.validate(spec)
    encoded = adapter.encode(spec)
    assert len(encoded) == space.dimension
    particle = Particle.from_vectors("p0", pos, [0.0] * space.dimension)
    adapter.repair_particle(particle)
    assert len(particle.position) == space.dimension
