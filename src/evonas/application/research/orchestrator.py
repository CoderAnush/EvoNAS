"""Scientific Experiment Orchestrator — fair multi-algorithm benchmarking."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable

from evonas import __version__
from evonas.application.research.matrix import MatrixCell, expand_matrix
from evonas.benchmarks.random_search import RandomSearch, RandomSearchConfig
from evonas.domain.optimization.adaptive import AdaptiveConfig
from evonas.domain.optimization.benchmark import BenchmarkRunner
from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig
from evonas.domain.optimization.sapso import SelfAdaptivePSO
from evonas.domain.research.figures import PublicationFigures
from evonas.domain.research.report import generate_report
from evonas.domain.research.stats import compare_paired, summarize
from evonas.domain.research.tables import write_table_bundle
from evonas.domain.search_space.space import SearchSpace
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.experiments.artifact_manager import ArtifactManager
from evonas.infrastructure.experiments.index import (
    ExperimentRegistry,
    artifact_checksum,
    config_checksum,
    git_commit,
)
from evonas.infrastructure.optimization.mock_fitness import MockFitnessEvaluator
from evonas.ports.search import IFitnessEvaluator, ISearchAlgorithm

logger = logging.getLogger(__name__)


class ExperimentOrchestrator:
    """Load experiment definitions, execute matrix cells, aggregate, export."""

    def __init__(
        self,
        *,
        config_manager: ConfigurationManager | None = None,
        registry: ExperimentRegistry | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigurationManager()
        self._registry = registry or ExperimentRegistry()
        self._runner = BenchmarkRunner()
        self._figures = PublicationFigures()

    def run(
        self,
        config_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Execute a full scientific benchmark suite from YAML."""
        cfg_path = Path(config_path)
        cfg = self._config_manager.load(cfg_path)
        started = time.perf_counter()
        experiment_id = str(cfg.get("experiment_id") or cfg.get("run_id") or "research_suite")
        out_root = Path(
            output_dir
            or cfg.get("experiment", {}).get("artifacts_root", "artifacts/research")
        )
        artifacts = ArtifactManager(root=out_root)
        run_dir = artifacts.create_run(experiment_id)
        artifacts.copy_config(run_dir, cfg_path)

        opt = dict(cfg.get("optimization", {}))
        maximize = str(cfg.get("fitness", {}).get("sense", "maximize")) == "maximize"
        landscape = str(cfg.get("fitness", {}).get("landscape", "sphere"))
        confidence = float(cfg.get("statistics", {}).get("confidence", 0.95))
        run_sig = bool(cfg.get("statistics", {}).get("significance_tests", True))
        n_trials = int(
            cfg.get("random_search", {}).get(
                "n_trials",
                int(opt.get("swarm_size", 12)) * int(opt.get("max_iterations", 20)),
            )
        )

        matrix_spec = {
            "algorithms": cfg.get("algorithms")
            or cfg.get("matrix", {}).get("algorithms")
            or ["standard_pso", "sapso", "random_search"],
            "datasets": cfg.get("datasets")
            or cfg.get("matrix", {}).get("datasets")
            or [{"id": "mock", "landscape": landscape}],
            "seeds": cfg.get("seeds") or cfg.get("comparison") or {"n": 5, "base": int(cfg.get("seed", 42))},
            "configurations": cfg.get("configurations")
            or cfg.get("matrix", {}).get("configurations")
            or [{"id": "default"}],
            "search_space": cfg.get("search_space"),
            "seed": cfg.get("seed", 42),
            "n_seeds": cfg.get("n_seeds"),
        }
        cells = expand_matrix(matrix_spec)
        # Group by (algorithm, dataset, config) for BenchmarkRunner multi-seed
        groups: dict[tuple[str, str, str], list[MatrixCell]] = {}
        for cell in cells:
            group_key = (cell.algorithm, cell.dataset, cell.config_id)
            groups.setdefault(group_key, []).append(cell)

        algorithm_reports: dict[str, Any] = {}
        failures: list[dict[str, Any]] = []
        fitness_series: dict[str, list[float]] = {}

        for (algo, dataset, config_id), group in groups.items():
            seeds = [c.seed for c in group]
            cell0 = group[0]
            space = SearchSpace.from_yaml(cell0.space_path)
            land = cell0.landscape

            def evaluator_factory(
                landscape: str = land, sense: bool = maximize
            ) -> IFitnessEvaluator:
                # Research suite defaults to mock fitness for reproducibility in CI.
                # dry_run flag reserved for future neural eval path without changing engines.
                _ = dry_run
                return MockFitnessEvaluator(landscape=landscape, maximize=sense)

            try:
                factory = self._optimizer_factory(
                    algo, opt, cfg, n_trials=n_trials, maximize=maximize
                )
                report = self._runner.run(
                    algorithm_name=algo,
                    space=space,
                    evaluator_factory=evaluator_factory,
                    optimizer_factory=factory,
                    seeds=seeds,
                    budget={"max_evaluations": n_trials} if algo == "random_search" else None,
                    maximize=maximize,
                )
                report["dataset"] = dataset
                report["config_id"] = config_id
                report["landscape"] = land
                algorithm_reports[f"{algo}::{dataset}::{config_id}"] = report
                # Collect a representative convergence curve (first seed history not stored
                # by BenchmarkRunner — synthesize flat mean curve for bar/context figures)
                fitness_series[algo] = [
                    float(r["best_fitness"]) for r in report["runs"]
                ]
                logger.info(
                    "Completed %s dataset=%s seeds=%d mean_fitness=%.6f",
                    algo,
                    dataset,
                    len(seeds),
                    report["aggregates"]["best_fitness"]["mean"],
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Cell failed algo=%s dataset=%s", algo, dataset)
                failures.append(
                    {
                        "algorithm": algo,
                        "dataset": dataset,
                        "config_id": config_id,
                        "error": str(exc),
                    }
                )

        # Aggregate stats + pairwise comparisons (honest)
        summaries: dict[str, Any] = {}
        for report_key, report in algorithm_reports.items():
            fits = [float(r["best_fitness"]) for r in report["runs"]]
            secs = [float(r["seconds"]) for r in report["runs"]]
            evals = [float(r["evaluations"]) for r in report["runs"]]
            summaries[report_key] = {
                "fitness": summarize(fits, confidence=confidence),
                "seconds": summarize(secs, confidence=confidence),
                "evaluations": summarize(evals, confidence=confidence),
            }

        pairwise: dict[str, Any] = {}
        report_keys = list(algorithm_reports.keys())
        for i, ka in enumerate(report_keys):
            for kb in report_keys[i + 1 :]:
                a_fits = [float(r["best_fitness"]) for r in algorithm_reports[ka]["runs"]]
                b_fits = [float(r["best_fitness"]) for r in algorithm_reports[kb]["runs"]]
                pairwise[f"{ka}_vs_{kb}"] = compare_paired(
                    a_fits,
                    b_fits,
                    label_a=ka,
                    label_b=kb,
                    confidence=confidence,
                    run_significance=run_sig,
                )

        winner = self._declare_winner(algorithm_reports, maximize=maximize)

        # Tables
        table_rows = []
        for _report_key, report in algorithm_reports.items():
            agg = report["aggregates"]["best_fitness"]
            table_rows.append(
                {
                    "algorithm": report["algorithm"],
                    "dataset": report.get("dataset"),
                    "mean_fitness": agg["mean"],
                    "std_fitness": agg["std"],
                    "median_fitness": agg["median"],
                    "mean_seconds": report["aggregates"]["seconds"]["mean"],
                    "mean_evaluations": float(
                        sum(float(r["evaluations"]) for r in report["runs"])
                        / max(len(report["runs"]), 1)
                    ),
                    "n_seeds": agg["n"],
                }
            )
        tables_dir = run_dir / "tables"
        table_paths = write_table_bundle(
            table_rows, tables_dir, stem="summary", title="Benchmark summary"
        )

        # Figures
        figures_dir = run_dir / "figures"
        fig_paths: list[str] = []
        if table_rows:
            labels = [str(r["algorithm"]) for r in table_rows]
            means = [float(r["mean_fitness"]) for r in table_rows]
            stds = [float(r["std_fitness"]) for r in table_rows]
            for p in self._figures.bar_comparison(
                labels,
                means,
                stds,
                figures_dir,
                title="Mean best fitness (± std)",
                ylabel="Fitness",
                stem="accuracy_fitness_comparison",
            ):
                fig_paths.append(str(p))
            for p in self._figures.bar_comparison(
                labels,
                [float(r["mean_seconds"]) for r in table_rows],
                None,
                figures_dir,
                title="Mean runtime",
                ylabel="Seconds",
                stem="runtime_comparison",
            ):
                fig_paths.append(str(p))
        if fitness_series:
            # seed-wise best fitness as a simple series plot
            for p in self._figures.fitness_convergence(
                fitness_series,
                figures_dir,
                title="Per-seed best fitness",
                ylabel="Best fitness",
            ):
                fig_paths.append(str(p))

        elapsed = time.perf_counter() - started
        cfg_hash = config_checksum(cfg_path)
        results = {
            "winner": winner,
            "algorithms": algorithm_reports,
            "failures": failures,
            "maximize": maximize,
        }
        meta = {
            "experiment_id": experiment_id,
            "evonas_version": __version__,
            "git_commit": git_commit(),
            "config_path": str(cfg_path),
            "config_hash": cfg_hash,
            "seeds": sorted({c.seed for c in cells}),
            "algorithms": sorted({c.algorithm for c in cells}),
            "space": str(cfg.get("search_space")),
            "landscape": landscape,
            "run_dir": str(run_dir),
            "figures_dir": str(figures_dir),
            "tables_dir": str(tables_dir),
            "elapsed_seconds": elapsed,
            "dry_run": dry_run,
            "matrix_cells": len(cells),
        }
        stats_payload = {"summaries": summaries, "pairwise": pairwise, "ci_method": "normal_approx"}

        artifacts.write_json(run_dir, "meta.json", meta)
        artifacts.write_json(run_dir, "results.json", results)
        artifacts.write_json(run_dir, "statistics.json", stats_payload)
        # Dashboard-compatible comparison.json (extends PSO vs SAPSO shape when present)
        comparison = self._to_comparison_json(algorithm_reports, maximize=maximize, meta=meta)
        artifacts.write_json(run_dir, "comparison.json", comparison)

        report_path = generate_report(
            {
                "meta": meta,
                "results": {"winner": winner, "table": table_rows, "failures": failures},
                "statistics": stats_payload,
            },
            run_dir / "reports" / "experiment_report.md",
        )

        # checksum key artifacts
        checksums = {
            name: artifact_checksum(run_dir / name)
            for name in ("meta.json", "results.json", "statistics.json", "comparison.json")
            if (run_dir / name).exists()
        }
        artifacts.write_json(run_dir, "checksums.json", checksums)

        seeds_raw = meta.get("seeds")
        algos_raw = meta.get("algorithms")
        seed_list = [int(s) for s in seeds_raw] if isinstance(seeds_raw, list) else []
        algo_list = [str(a) for a in algos_raw] if isinstance(algos_raw, list) else []
        registry_entry = self._registry.record(
            {
                "experiment_id": experiment_id,
                "run_dir": str(run_dir),
                "config_path": str(cfg_path),
                "config_hash": cfg_hash,
                "winner": winner,
                "algorithms": algo_list,
                "n_seeds": len(seed_list),
                "elapsed_seconds": elapsed,
                "checksums": checksums,
            }
        )

        return {
            "meta": meta,
            "results": results,
            "statistics": stats_payload,
            "tables": table_paths,
            "figures": fig_paths,
            "report": str(report_path),
            "registry": registry_entry,
            "comparison": comparison,
            "run_dir": str(run_dir),
        }

    def _optimizer_factory(
        self,
        algorithm: str,
        opt: dict[str, Any],
        cfg: dict[str, Any],
        *,
        n_trials: int,
        maximize: bool,
    ) -> Callable[[], ISearchAlgorithm]:
        name = algorithm.lower().strip()
        pso_cfg = StandardPSOConfig(
            swarm_size=int(opt.get("swarm_size", 12)),
            max_iterations=int(opt.get("max_iterations", 20)),
            w=float(opt.get("w", 0.729)),
            c1=float(opt.get("c1", 1.49445)),
            c2=float(opt.get("c2", 1.49445)),
            maximize=maximize,
            log_particles=False,
            seed=int(cfg.get("seed", 42)),
        )
        adaptive = AdaptiveConfig.from_dict(dict(cfg.get("adaptation", {})))

        if name in {"sapso", "adaptive", "self_adaptive"}:

            def sapso_factory() -> ISearchAlgorithm:
                return SelfAdaptivePSO(pso_cfg, adaptive_config=adaptive)

            return sapso_factory
        if name in {"random_search", "random", "rs"}:
            rs_cfg = RandomSearchConfig(n_trials=n_trials, maximize=maximize)

            def rs_factory() -> ISearchAlgorithm:
                return RandomSearch(rs_cfg)

            return rs_factory

        def pso_factory() -> ISearchAlgorithm:
            return StandardPSO(pso_cfg)

        return pso_factory

    @staticmethod
    def _declare_winner(reports: dict[str, Any], *, maximize: bool) -> str:
        if not reports:
            return "none"
        best_key = None
        best_val = None
        for key, report in reports.items():
            mean = float(report["aggregates"]["best_fitness"]["mean"])
            if best_val is None:
                best_key, best_val = key, mean
                continue
            better = mean > best_val if maximize else mean < best_val
            if better:
                best_key, best_val = key, mean
        assert best_key is not None
        # Detect ties
        tied = [
            k
            for k, r in reports.items()
            if float(r["aggregates"]["best_fitness"]["mean"]) == best_val
        ]
        if len(tied) > 1:
            return "tie"
        return str(reports[best_key]["algorithm"])

    @staticmethod
    def _to_comparison_json(
        reports: dict[str, Any],
        *,
        maximize: bool,
        meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Shape compatible with dashboard Benchmarks page + extended algorithms."""
        by_algo: dict[str, Any] = {}
        for report in reports.values():
            by_algo[report["algorithm"]] = report
        payload: dict[str, Any] = {
            "evonas_version": meta.get("evonas_version"),
            "seeds": meta.get("seeds"),
            "space": meta.get("space"),
            "maximize": maximize,
            "algorithms": by_algo,
            "winner": ExperimentOrchestrator._declare_winner(reports, maximize=maximize),
        }
        # Preserve legacy keys when both present
        if "standard_pso" in by_algo and "sapso" in by_algo:
            pso_mean = float(by_algo["standard_pso"]["aggregates"]["best_fitness"]["mean"])
            sapso_mean = float(by_algo["sapso"]["aggregates"]["best_fitness"]["mean"])
            payload["standard_pso"] = by_algo["standard_pso"]
            payload["sapso"] = by_algo["sapso"]
            payload["delta_mean_fitness_sapso_minus_pso"] = sapso_mean - pso_mean
        return payload
