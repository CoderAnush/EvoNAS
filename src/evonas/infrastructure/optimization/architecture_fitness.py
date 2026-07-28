"""Architecture fitness evaluator — train/eval path for PSO (expensive)."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Sequence

from evonas.domain.architecture.complexity import estimate_complexity
from evonas.domain.common.enums import Split
from evonas.domain.fitness.calculator import FitnessCalculator
from evonas.domain.fitness.types import Fitness, FitnessConfig
from evonas.domain.optimization.adapter import SearchSpaceAdapter
from evonas.domain.optimization.cache import EvaluationCache
from evonas.domain.training.types import TrainConfig
from evonas.infrastructure.training.pytorch_evaluator import PyTorchEvaluationEngine
from evonas.infrastructure.training.pytorch_trainer import PyTorchTrainingEngine
from evonas.ports.dataset import IDatasetManager
from evonas.ports.training import IEvaluationEngine, ITrainingEngine

logger = logging.getLogger(__name__)


class ArchitectureFitnessEvaluator:
    """Decode position → build → train → evaluate → Fitness.

    Uses Phase 2/3 engines; PSO remains framework-agnostic.
    """

    def __init__(
        self,
        adapter: SearchSpaceAdapter,
        dataset_manager: IDatasetManager,
        *,
        train_config: TrainConfig | None = None,
        fitness_config: FitnessConfig | None = None,
        trainer: ITrainingEngine | None = None,
        evaluator: IEvaluationEngine | None = None,
        cache: EvaluationCache | None = None,
        subset_fraction: float = 1.0,
        subset_seed: int = 42,
    ) -> None:
        self._adapter = adapter
        self._data = dataset_manager
        self._train_config = train_config or TrainConfig(epochs=2, batch_size=32, seed=42)
        self._fitness_calc = FitnessCalculator(fitness_config or FitnessConfig())
        self._trainer = trainer or PyTorchTrainingEngine()
        self._evaluator = evaluator or PyTorchEvaluationEngine()
        self._cache = cache or EvaluationCache()
        self._subset_fraction = float(subset_fraction)
        self._subset_seed = int(subset_seed)
        self._train_hash = self._hash_train_config()
        self.last_eval_seconds: float = 0.0

    def _hash_train_config(self) -> str:
        blob = json.dumps(self._train_config.to_dict(), sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def evaluate(self, position: Sequence[float], *, particle_id: str | None = None) -> Fitness:
        """Full architecture evaluation with caching and fail-soft behavior."""
        started = time.perf_counter()
        try:
            spec = self._adapter.decode(position, name=particle_id or "particle")
            cached = self._cache.get(spec.arch_id(), self._train_hash)
            if cached is not None:
                logger.info("Cache hit arch_id=%s particle=%s", spec.arch_id()[:12], particle_id)
                self.last_eval_seconds = time.perf_counter() - started
                return cached.fitness

            train_h = self._data.load(Split.TRAIN)
            val_h = self._data.load(Split.VAL)
            if self._subset_fraction < 1.0:
                train_h = self._data.subset(Split.TRAIN, self._subset_fraction, self._subset_seed)

            artifact = self._trainer.train(
                spec,
                train_h,
                val_h,
                self._train_config,
                run_context={"particle_id": particle_id, "source": "pso"},
            )
            if artifact.val_metrics is not None:
                metrics = artifact.val_metrics
            else:
                # Fallback: evaluate latest weights path is owned by trainer; use train metrics.
                metrics = artifact.train_metrics

            complexity = estimate_complexity(spec)
            fitness = self._fitness_calc.compute(metrics, complexity)
            self._cache.put(
                spec.arch_id(),
                fitness,
                train_hash=self._train_hash,
                metrics=metrics.to_dict(),
            )
            self.last_eval_seconds = time.perf_counter() - started
            logger.info(
                "Evaluated particle=%s fitness=%.4f arch=%s seconds=%.2f",
                particle_id,
                fitness.value,
                spec.arch_id()[:12],
                self.last_eval_seconds,
            )
            return fitness
        except Exception as exc:  # noqa: BLE001
            logger.warning("Architecture evaluation failed particle=%s: %s", particle_id, exc)
            self.last_eval_seconds = time.perf_counter() - started
            return self._fitness_calc.fail(str(exc), particle_id=particle_id)

    def cache_stats(self) -> dict[str, Any]:
        """Return cache hit/miss statistics."""
        return self._cache.stats()
