"""Research baselines package — NOT wired into the closed-loop controller.

Implements Random Search for fair scientific comparison only (idea.md REQ-OPT-001).
"""

from evonas.benchmarks.random_search import RandomSearch, RandomSearchConfig

__all__ = ["RandomSearch", "RandomSearchConfig"]
