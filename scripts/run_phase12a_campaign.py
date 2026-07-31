#!/usr/bin/env python3
"""Phase 12A experimental campaign runner.

Uses the frozen Phase 10 ExperimentOrchestrator and public optimizer APIs only.
Does not modify PSO, SAPSO, trainers, closed-loop, dashboard, API, registry, or CLI.
"""

from __future__ import annotations

import json
import logging
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import resource as _resource
except ImportError:  # Windows
    _resource = None  # type: ignore[assignment]

# Allow running from repo root without install when needed
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from evonas import __version__  # noqa: E402
from evonas.application.research.use_cases import BenchmarkUseCase  # noqa: E402
from evonas.domain.optimization.adaptive import AdaptiveConfig  # noqa: E402
from evonas.domain.optimization.pso import StandardPSO, StandardPSOConfig  # noqa: E402
from evonas.domain.optimization.sapso import SelfAdaptivePSO  # noqa: E402
from evonas.domain.research.figures import PublicationFigures  # noqa: E402
from evonas.domain.research.stats import compare_paired, summarize  # noqa: E402
from evonas.domain.research.tables import write_table_bundle  # noqa: E402
from evonas.domain.search_space.space import SearchSpace  # noqa: E402
from evonas.infrastructure.experiments.index import ExperimentRegistry, git_commit  # noqa: E402
from evonas.infrastructure.optimization.mock_fitness import MockFitnessEvaluator  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("phase12a")

SUITE_CONFIGS = [
    "configs/benchmarks/phase12a_sphere_paper.yaml",
    "configs/benchmarks/phase12a_multi_landscape.yaml",
    "configs/benchmarks/phase12a_budget_compact.yaml",
    "configs/benchmarks/phase12a_budget_extended.yaml",
]

CAMPAIGN_ID = "phase12a_campaign"


def _rss_mb() -> float | None:
    if _resource is None:
        return None
    try:
        usage = _resource.getrusage(_resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return float(usage) / (1024.0 * 1024.0)
        if sys.platform.startswith("linux"):
            return float(usage) / 1024.0
        return float(usage) / (1024.0 * 1024.0) if usage else None
    except Exception:  # noqa: BLE001
        return None


def run_suites(out_root: Path) -> list[dict[str, Any]]:
    uc = BenchmarkUseCase()
    results: list[dict[str, Any]] = []
    for cfg in SUITE_CONFIGS:
        logger.info("=== Suite %s ===", cfg)
        t0 = time.perf_counter()
        payload = uc.run(cfg, output_dir=out_root, dry_run=True)
        payload["_suite_config"] = cfg
        payload["_wall_seconds"] = time.perf_counter() - t0
        results.append(payload)
        logger.info(
            "Suite done experiment_id=%s run_dir=%s elapsed=%.2fs",
            payload.get("meta", {}).get("experiment_id"),
            payload.get("run_dir"),
            payload["_wall_seconds"],
        )
    return results


def instrument_trajectories(campaign_dir: Path) -> dict[str, Any]:
    """Generate coefficient / diversity / complexity figures via public APIs."""
    figures = PublicationFigures()
    fig_dir = campaign_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    space = SearchSpace.from_yaml("configs/search_spaces/sphere_2d.yaml")
    seed = 42
    pso_cfg = StandardPSOConfig(
        swarm_size=12,
        max_iterations=25,
        maximize=True,
        log_particles=False,
        seed=seed,
    )

    # SAPSO adaptive trajectories
    sapso = SelfAdaptivePSO(pso_cfg, adaptive_config=AdaptiveConfig())
    sapso.set_evaluator(MockFitnessEvaluator(landscape="sphere", maximize=True))
    sapso.initialize(space, seed)
    sapso.run({"max_evaluations": 12 * 25})
    adaptive = sapso.export_adaptive_history()
    records = adaptive["records"]
    # Flatten diversity onto records for diversity_evolution helper
    flat = []
    for r in records:
        entry = dict(r)
        stats = r.get("stats") or {}
        entry["diversity"] = stats.get("normalized_diversity", r.get("normalized_diversity"))
        entry["normalized_diversity"] = entry["diversity"]
        flat.append(entry)

    fig_paths: list[str] = []
    for p in figures.coefficient_evolution(flat, fig_dir):
        fig_paths.append(str(p))
    for p in figures.diversity_evolution(flat, fig_dir):
        fig_paths.append(str(p))

    # Standard PSO diversity from SwarmHistory
    pso = StandardPSO(pso_cfg)
    pso.set_evaluator(MockFitnessEvaluator(landscape="sphere", maximize=True))
    pso.initialize(space, seed)
    result = pso.run({"max_evaluations": 12 * 25})
    pso_div = [
        {"iteration": rec.iteration, "diversity": rec.diversity, "normalized_diversity": rec.diversity}
        for rec in result.history.records
    ]
    for p in figures.diversity_evolution(pso_div, fig_dir, key="diversity"):
        # rename stem collision avoided by saving again under pso prefix
        fig_paths.append(str(p))
    # Save PSO-specific copy
    if pso_div:
        import shutil

        src = fig_dir / "diversity_evolution.png"
        if src.exists():
            for ext in ("png", "svg", "pdf"):
                s = fig_dir / f"diversity_evolution.{ext}"
                d = fig_dir / f"diversity_pso.{ext}"
                if s.exists():
                    shutil.copy2(s, d)
                    fig_paths.append(str(d))

    # Complexity proxy table
    genes = [
        {
            "gene": g.name,
            "kind": g.kind,
            "low": getattr(g, "low", None),
            "high": getattr(g, "high", None),
        }
        for g in space.genes
    ]
    complexity_rows = [
        {
            "space": space.name,
            "n_genes": len(space.genes),
            "dimensionality": len(space.genes),
            "input_shape": str(space.input_shape),
            "num_classes": space.num_classes,
            "accuracy_metric": "mock_fitness_proxy",
            "training_time": None,
            "inference_cost": None,
            "memory_rss_mb": _rss_mb(),
        }
    ]
    write_table_bundle(complexity_rows, campaign_dir / "tables", stem="architecture_complexity", title="Search-space complexity proxy")
    write_table_bundle(genes, campaign_dir / "tables", stem="gene_bounds", title="Gene bounds")

    (campaign_dir / "instrumentation").mkdir(parents=True, exist_ok=True)
    (campaign_dir / "instrumentation" / "sapso_adaptive_history.json").write_text(
        json.dumps(adaptive, indent=2, default=str), encoding="utf-8"
    )
    (campaign_dir / "instrumentation" / "pso_diversity.json").write_text(
        json.dumps(pso_div, indent=2), encoding="utf-8"
    )

    return {
        "figures": fig_paths,
        "sapso_iterations": len(records),
        "pso_iterations": len(pso_div),
        "memory_rss_mb": _rss_mb(),
        "complexity": complexity_rows[0],
    }


def _mean_fitness(report: dict[str, Any]) -> float:
    return float(report["aggregates"]["best_fitness"]["mean"])


def aggregate_campaign(suite_payloads: list[dict[str, Any]], campaign_dir: Path) -> dict[str, Any]:
    summary_rows: list[dict[str, Any]] = []
    rank_rows: list[dict[str, Any]] = []
    metrics_rows: list[dict[str, Any]] = []
    pairwise_rows: list[dict[str, Any]] = []

    for payload in suite_payloads:
        meta = payload.get("meta") or {}
        results = payload.get("results") or {}
        stats = payload.get("statistics") or {}
        exp_id = meta.get("experiment_id")
        algorithms = results.get("algorithms") or {}

        # Group by dataset for ranking
        by_dataset: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for key, report in algorithms.items():
            ds = str(report.get("dataset", "unknown"))
            by_dataset.setdefault(ds, []).append((str(report["algorithm"]), report))

        for ds, items in by_dataset.items():
            ranked = sorted(items, key=lambda t: _mean_fitness(t[1]), reverse=True)
            for rank, (algo, report) in enumerate(ranked, start=1):
                agg_f = report["aggregates"]["best_fitness"]
                agg_s = report["aggregates"]["seconds"]
                mean_evals = sum(float(r["evaluations"]) for r in report["runs"]) / max(
                    len(report["runs"]), 1
                )
                row = {
                    "suite": exp_id,
                    "dataset": ds,
                    "algorithm": algo,
                    "rank": rank,
                    "mean_fitness": agg_f["mean"],
                    "median_fitness": agg_f["median"],
                    "std_fitness": agg_f["std"],
                    "mean_seconds": agg_s["mean"],
                    "mean_evaluations": mean_evals,
                    "n_seeds": agg_f["n"],
                    "accuracy_proxy": agg_f["mean"],
                    "training_time": None,
                    "optimization_time": agg_s["mean"],
                    "model_complexity_dim": 2,
                    "inference_cost": None,
                    "memory_usage": None,
                }
                summary_rows.append(row)
                rank_rows.append(
                    {
                        "suite": exp_id,
                        "dataset": ds,
                        "algorithm": algo,
                        "rank": rank,
                        "mean_fitness": agg_f["mean"],
                    }
                )
                metrics_rows.append(row)

        # Pairwise from statistics
        for pname, pdata in (stats.get("pairwise") or {}).items():
            pairwise_rows.append(
                {
                    "suite": exp_id,
                    "pair": pname,
                    "delta_mean": pdata.get("delta_mean_b_minus_a"),
                    "wilcoxon_pvalue": (pdata.get("significance") or {}).get("pvalue"),
                    "wilcoxon_available": (pdata.get("significance") or {}).get("available"),
                    "cliffs_delta": (pdata.get("effect_size") or {}).get("delta"),
                    "effect_label": (pdata.get("effect_size") or {}).get("interpretation"),
                }
            )

    tables_dir = campaign_dir / "tables"
    write_table_bundle(summary_rows, tables_dir, stem="campaign_summary", title="Phase 12A campaign summary")
    write_table_bundle(rank_rows, tables_dir, stem="rank_tables", title="Mean fitness ranks")
    write_table_bundle(metrics_rows, tables_dir, stem="metrics_full", title="Full metrics (N/A fields null)")
    write_table_bundle(pairwise_rows, tables_dir, stem="pairwise_stats", title="Pairwise statistics")

    # Cross-suite consistency: multi-landscape ranks
    consistency = _rank_consistency(rank_rows)

    return {
        "summary_rows": summary_rows,
        "rank_rows": rank_rows,
        "pairwise_rows": pairwise_rows,
        "consistency": consistency,
        "n_suites": len(suite_payloads),
    }


def _rank_consistency(rank_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Check whether algorithm order is stable across suites for same dataset."""
    # Map suite -> dataset -> ordered algorithms by rank
    orders: dict[str, dict[str, list[str]]] = {}
    for row in rank_rows:
        suite = str(row["suite"])
        ds = str(row["dataset"])
        orders.setdefault(suite, {}).setdefault(ds, [])
    # rebuild sorted
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rank_rows:
        by_key.setdefault((str(row["suite"]), str(row["dataset"])), []).append(row)
    for (suite, ds), rows in by_key.items():
        ordered = [r["algorithm"] for r in sorted(rows, key=lambda x: int(x["rank"]))]
        orders.setdefault(suite, {})[ds] = ordered

    notes: list[str] = []
    # Compare compact vs extended on shared datasets
    compact = orders.get("phase12a_budget_compact", {})
    extended = orders.get("phase12a_budget_extended", {})
    for ds in sorted(set(compact) & set(extended)):
        same = compact[ds] == extended[ds]
        notes.append(
            f"compact_vs_extended dataset={ds} identical_rank_order={same} "
            f"compact={compact[ds]} extended={extended[ds]}"
        )
    multi = orders.get("phase12a_multi_landscape", {})
    if "sphere" in multi and "rastrigin" in multi:
        notes.append(
            f"multi_landscape sphere={multi['sphere']} rastrigin={multi['rastrigin']} "
            f"identical={multi['sphere'] == multi['rastrigin']}"
        )
    return {"orders": orders, "notes": notes}


def validate_reproducibility(campaign_dir: Path) -> dict[str, Any]:
    """Smoke re-run of a tiny paired cell and compare means."""
    from evonas.domain.optimization.benchmark import BenchmarkRunner

    space = SearchSpace.from_yaml("configs/search_spaces/sphere_2d.yaml")
    seeds = [42, 43, 44]
    runner = BenchmarkRunner()
    cfg = StandardPSOConfig(swarm_size=8, max_iterations=10, maximize=True, log_particles=False)

    def pso_factory() -> StandardPSO:
        return StandardPSO(cfg)

    def sapso_factory() -> SelfAdaptivePSO:
        return SelfAdaptivePSO(cfg, adaptive_config=AdaptiveConfig())

    def eval_factory() -> MockFitnessEvaluator:
        return MockFitnessEvaluator(landscape="sphere", maximize=True)

    r1 = runner.run(
        algorithm_name="standard_pso",
        space=space,
        evaluator_factory=eval_factory,
        optimizer_factory=pso_factory,
        seeds=seeds,
        maximize=True,
    )
    r1b = runner.run(
        algorithm_name="standard_pso",
        space=space,
        evaluator_factory=eval_factory,
        optimizer_factory=pso_factory,
        seeds=seeds,
        maximize=True,
    )
    fits_a = [float(x["best_fitness"]) for x in r1["runs"]]
    fits_b = [float(x["best_fitness"]) for x in r1b["runs"]]
    bit_match = fits_a == fits_b
    sapso_r = runner.run(
        algorithm_name="sapso",
        space=space,
        evaluator_factory=eval_factory,
        optimizer_factory=sapso_factory,
        seeds=seeds,
        maximize=True,
    )
    cmp = compare_paired(
        fits_a,
        [float(x["best_fitness"]) for x in sapso_r["runs"]],
        label_a="standard_pso",
        label_b="sapso",
    )
    payload = {
        "reproducibility_bit_exact": bit_match,
        "pso_means": [r1["aggregates"]["best_fitness"]["mean"], r1b["aggregates"]["best_fitness"]["mean"]],
        "sapso_mean": sapso_r["aggregates"]["best_fitness"]["mean"],
        "paired_compare": cmp,
        "summarize_demo": summarize(fits_a),
    }
    (campaign_dir / "validation").mkdir(parents=True, exist_ok=True)
    (campaign_dir / "validation" / "reproducibility.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    return payload


def write_reports(
    campaign_dir: Path,
    suite_payloads: list[dict[str, Any]],
    aggregate: dict[str, Any],
    instrumentation: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    reports = campaign_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    # Results summary
    lines = [
        "# Phase 12A Results Summary",
        "",
        f"- **EvoNAS version:** `{__version__}`",
        f"- **Git commit:** `{git_commit()}`",
        f"- **Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        f"- **Platform:** {platform.platform()}",
        f"- **Suites executed:** {aggregate['n_suites']}",
        "",
        "## Winners (by mean fitness, maximize)",
        "",
    ]
    for payload in suite_payloads:
        meta = payload.get("meta") or {}
        results = payload.get("results") or {}
        lines.append(
            f"- `{meta.get('experiment_id')}` → winner=`{results.get('winner')}` "
            f"(cells={meta.get('matrix_cells')}, elapsed={meta.get('elapsed_seconds'):.2f}s)"
            if isinstance(meta.get("elapsed_seconds"), (int, float))
            else f"- `{meta.get('experiment_id')}` → winner=`{results.get('winner')}`"
        )
    lines.extend(["", "## Rank consistency notes", ""])
    for note in aggregate.get("consistency", {}).get("notes", []):
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Bit-exact PSO re-run: `{validation.get('reproducibility_bit_exact')}`",
            f"- Instrumentation SAPSO iterations: `{instrumentation.get('sapso_iterations')}`",
            f"- Memory RSS (MB, best-effort): `{instrumentation.get('memory_rss_mb')}`",
            "",
            "## Metric coverage",
            "",
            "| Metric | Status |",
            "|--------|--------|",
            "| Fitness / accuracy proxy | Recorded |",
            "| Optimization time | Recorded |",
            "| Evaluations / iterations | Recorded |",
            "| Model complexity (dim) | Proxy = 2 for Sphere space |",
            "| Training time | N/A (mock campaign) |",
            "| Inference cost | N/A (mock campaign) |",
            "| Memory usage | Optional RSS snapshot |",
            "",
            "See `tables/campaign_summary.*` for full numeric tables.",
            "",
        ]
    )
    (reports / "results_summary.md").write_text("\n".join(lines), encoding="utf-8")

    discussion = """# Discussion Notes — Phase 12A

## Interpretation guidelines

1. Primary endpoint is **mean best fitness** under maximize sense on mock landscapes.
2. SAPSO vs Standard PSO deltas may be small on smooth Sphere; Rastrigin is the harder control.
3. Random Search is a fairness baseline at matched evaluation count — not a production candidate.
4. Wall-clock differences on mock fitness are dominated by Python overhead, not GPU training.

## Observations to verify against tables

- Whether SAPSO ranks ≥ Standard PSO on Sphere (H1) and Rastrigin (H2).
- Whether swarm methods outrank Random Search (H3).
- Whether compact vs extended budgets preserve rank order (H4 / RQ3).
- Whether coefficient trajectories show phase-dependent w/c1/c2 movement (RQ4, descriptive).

## Honest reporting

Do not retrofit claims after inspecting results. Update hypotheses status in
`hypothesis_status.md` only with evidence citations to suite `statistics.json` files.
"""
    (reports / "discussion_notes.md").write_text(discussion, encoding="utf-8")

    threats = """# Threats to Validity — Phase 12A

## Internal validity

- Seed bases and budget sizes are researcher-chosen; other budgets may reorder methods.
- Mock fitness is deterministic given position — variance comes from stochastic search only.
- Orchestrator figure series for suites use per-seed best fitness, not full iteration curves
  (iteration curves are provided via campaign instrumentation runs).

## External validity

- Sphere / Rastrigin 2D results do not automatically transfer to CNN NAS search spaces
  (MNIST/CIFAR deferred to later neural campaigns).
- Matched evaluation budgets may still interact with algorithm-specific exploration dynamics.

## Construct validity

- “Accuracy” in this campaign is a **proxy** equal to mock fitness.
- Training time, inference cost are intentionally null — not estimated.

## Conclusion validity

- Normal-approximation confidence intervals are descriptive, not a normality claim.
- Wilcoxon requires paired identical seeds; unavailable when SciPy missing or n too small.
- Multiple pairwise tests inflate family-wise error if over-interpreted without correction.
"""
    (reports / "threats_to_validity.md").write_text(threats, encoding="utf-8")

    limitations = """# Limitations — Phase 12A

- Mock-only primary campaign (no neural training noise).
- 2D continuous search space only for primary tables.
- Publication seed counts are paper-draft scale (10–15), not camera-ready 30–50.
- Architecture complexity reduced to gene dimensionality for Sphere.
- Coefficient / diversity figures come from representative instrumentation seeds, not every suite seed.
- Dashboard / API / optimizers were not modified; campaign uses existing CLI/orchestrator surfaces.
"""
    (reports / "limitations.md").write_text(limitations, encoding="utf-8")

    future = """# Future Work — Post Phase 12A

- Neural evaluation campaign on `cnn_quick` / MNIST with frozen engines.
- Camera-ready seed counts (30–50) once neural budgets are affordable.
- Grid Search baseline for fully discrete spaces (research package only).
- Family-wise error correction for multi-comparison tables.
- Full Replay packages as paper supplements.
- Phase 12B+: paper drafting (explicitly deferred; not part of 12A).
"""
    (reports / "future_work.md").write_text(future, encoding="utf-8")


def write_hypothesis_status(campaign_dir: Path, aggregate: dict[str, Any]) -> None:
    """Derive hypothesis support from campaign rank/summary rows (honest)."""
    rows = aggregate.get("summary_rows") or []

    def means(suite: str, dataset: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in rows:
            if r["suite"] == suite and r["dataset"] == dataset:
                out[str(r["algorithm"])] = float(r["mean_fitness"])
        return out

    multi_sphere = means("phase12a_multi_landscape", "sphere")
    multi_rastrigin = means("phase12a_multi_landscape", "rastrigin")
    paper = means("phase12a_sphere_paper", "sphere")

    def ge(a: dict[str, float], left: str, right: str) -> bool | None:
        if left not in a or right not in a:
            return None
        return a[left] >= a[right]

    def beats_rs(a: dict[str, float], algo: str) -> bool | None:
        if algo not in a or "random_search" not in a:
            return None
        return a[algo] > a["random_search"]

    h1 = ge(paper, "sapso", "standard_pso") or ge(multi_sphere, "sapso", "standard_pso")
    h2 = ge(multi_rastrigin, "sapso", "standard_pso")
    h3_sphere = (
        beats_rs(multi_sphere, "sapso")
        and beats_rs(multi_sphere, "standard_pso")
        if multi_sphere
        else None
    )
    h3_rast = (
        beats_rs(multi_rastrigin, "sapso")
        and beats_rs(multi_rastrigin, "standard_pso")
        if multi_rastrigin
        else None
    )
    consistency_notes = aggregate.get("consistency", {}).get("notes", [])
    h4 = any("identical_rank_order=True" in n or "identical=True" in n for n in consistency_notes)

    status = {
        "H1_sapso_ge_pso_sphere": h1,
        "H2_sapso_ge_pso_rastrigin": h2,
        "H3_swarm_beats_rs_sphere": h3_sphere,
        "H3_swarm_beats_rs_rastrigin": h3_rast,
        "H4_rank_consistency_observed": h4,
        "means": {
            "phase12a_sphere_paper": paper,
            "multi_sphere": multi_sphere,
            "multi_rastrigin": multi_rastrigin,
        },
        "consistency_notes": consistency_notes,
    }
    (campaign_dir / "reports" / "hypothesis_status.md").write_text(
        "# Hypothesis Status\n\n```json\n"
        + json.dumps(status, indent=2, default=str)
        + "\n```\n",
        encoding="utf-8",
    )
    (campaign_dir / "hypothesis_status.json").write_text(
        json.dumps(status, indent=2, default=str), encoding="utf-8"
    )


def sync_governance() -> dict[str, Any]:
    try:
        from evonas.application.registry.service import GovernanceService

        return GovernanceService().sync()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "traceback": traceback.format_exc()}


def write_manifest(
    campaign_dir: Path,
    suite_payloads: list[dict[str, Any]],
    aggregate: dict[str, Any],
    instrumentation: dict[str, Any],
    validation: dict[str, Any],
    governance: dict[str, Any],
) -> Path:
    manifest = {
        "campaign_id": CAMPAIGN_ID,
        "protocol": "docs/research/experimental_protocol.md",
        "evonas_version": __version__,
        "git_commit": git_commit(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "suites": [
            {
                "config": p.get("_suite_config"),
                "experiment_id": (p.get("meta") or {}).get("experiment_id"),
                "run_dir": p.get("run_dir"),
                "winner": (p.get("results") or {}).get("winner"),
                "config_hash": (p.get("meta") or {}).get("config_hash"),
                "elapsed_seconds": (p.get("meta") or {}).get("elapsed_seconds"),
            }
            for p in suite_payloads
        ],
        "consistency": aggregate.get("consistency"),
        "instrumentation": {
            k: instrumentation[k]
            for k in ("sapso_iterations", "pso_iterations", "memory_rss_mb", "complexity")
            if k in instrumentation
        },
        "validation": {
            "reproducibility_bit_exact": validation.get("reproducibility_bit_exact"),
            "pso_means": validation.get("pso_means"),
            "sapso_mean": validation.get("sapso_mean"),
        },
        "governance_sync": governance,
    }
    path = campaign_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    # Also register campaign index entry
    ExperimentRegistry(root=campaign_dir.parent).record(
        {
            "experiment_id": CAMPAIGN_ID,
            "run_dir": str(campaign_dir),
            "config_path": "docs/research/experimental_protocol.md",
            "config_hash": None,
            "winner": None,
            "algorithms": ["standard_pso", "sapso", "random_search"],
            "n_seeds": None,
            "elapsed_seconds": None,
            "checksums": {},
            "kind": "campaign_index",
        }
    )
    return path


def main() -> int:
    out_root = ROOT / "artifacts" / "research"
    campaign_dir = out_root / CAMPAIGN_ID
    campaign_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Phase 12A campaign start version=%s commit=%s", __version__, git_commit())
    suite_payloads = run_suites(out_root)
    instrumentation = instrument_trajectories(campaign_dir)
    aggregate = aggregate_campaign(suite_payloads, campaign_dir)
    validation = validate_reproducibility(campaign_dir)
    write_reports(campaign_dir, suite_payloads, aggregate, instrumentation, validation)
    write_hypothesis_status(campaign_dir, aggregate)
    governance = sync_governance()
    manifest = write_manifest(
        campaign_dir, suite_payloads, aggregate, instrumentation, validation, governance
    )
    logger.info("Campaign complete manifest=%s", manifest)
    print(json.dumps({"manifest": str(manifest), "campaign_dir": str(campaign_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
