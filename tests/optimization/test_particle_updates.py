"""PSO particle / velocity / position unit tests."""

from __future__ import annotations

import numpy as np

from evonas.domain.optimization.particle import Particle
from evonas.domain.optimization.position import project_to_bounds, update_position
from evonas.domain.optimization.velocity import VelocityConfig, update_velocity


def test_particle_personal_best_update() -> None:
    p = Particle.from_vectors("p0", [0.0, 0.0], [0.0, 0.0], fitness=0.1)
    p.ensure_personal_best()
    assert p.pbest_fitness == 0.1
    p.fitness = 0.5
    assert p.update_personal_best(maximize=True) is True
    assert p.pbest_fitness == 0.5
    p.fitness = 0.2
    assert p.update_personal_best(maximize=True) is False


def test_velocity_and_position_update() -> None:
    rng = np.random.default_rng(0)
    p = Particle.from_vectors("p0", [0.0, 0.0], [1.0, -1.0], fitness=0.0)
    gbest = Particle.from_vectors("g", [2.0, 2.0], [0.0, 0.0], fitness=1.0).position
    cfg = VelocityConfig(w=0.7, c1=1.5, c2=1.5, kappa=1.0)
    update_velocity(p, gbest, [-5.0, -5.0], [5.0, 5.0], cfg, rng)
    assert len(p.velocity) == 2
    update_position(p)
    project_to_bounds(p, [-5.0, -5.0], [5.0, 5.0])
    assert all(-5.0 <= x <= 5.0 for x in p.position.as_list())
