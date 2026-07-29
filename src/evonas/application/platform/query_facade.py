"""Dashboard facade services — consume artifacts / public APIs only."""

from __future__ import annotations

import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evonas import __version__
from evonas.application.platform import demo_data
from evonas.application.platform.artifact_loaders import (
    discover_artifact_roots,
    find_named,
    list_run_dirs,
    load_yaml,
    read_json,
    read_jsonl,
    read_text,
)


@dataclass
class DashboardContext:
    """Shared dashboard session context (read-only discovery)."""

    cwd: Path = field(default_factory=Path.cwd)
    demo_mode: bool = False
    selected_optimization_run: Path | None = None
    selected_loop_run: Path | None = None
    selected_cl_run: Path | None = None
    selected_baseline_run: Path | None = None

    def roots(self) -> dict[str, Path]:
        """Artifact roots."""
        return discover_artifact_roots(self.cwd)


class DashboardService:
    """Single entry for all dashboard pages — no business-logic duplication."""

    def __init__(self, ctx: DashboardContext | None = None) -> None:
        self.ctx = ctx or DashboardContext()

    # ----- discovery -----

    def list_optimization_runs(self) -> list[Path]:
        """List optimization run directories."""
        roots = self.ctx.roots()
        runs = list_run_dirs(roots["optimization"])
        # also rc1 nested
        for extra in (roots["rc1"] / "pso", roots["rc1"] / "sapso", roots["demo"] / "pso", roots["demo"] / "sapso"):
            if extra.exists() and extra.is_dir():
                runs.append(extra)
        # dedupe
        seen: set[str] = set()
        out: list[Path] = []
        for run in runs:
            key = str(run.resolve())
            if key not in seen:
                seen.add(key)
                out.append(run)
        return out

    def list_loop_runs(self) -> list[Path]:
        """List closed-loop runs."""
        roots = self.ctx.roots()
        runs = list_run_dirs(roots["closed_loop"])
        for extra in (roots["rc1"] / "loop", roots["demo"] / "loop"):
            if extra.exists():
                # may contain nested run_id folder
                nested = list_run_dirs(extra)
                runs.extend(nested if nested else [extra])
        return runs

    def list_cl_runs(self) -> list[Path]:
        """List continuous-learning run folders (prefer .../run)."""
        roots = self.ctx.roots()
        candidates: list[Path] = []
        for base in (
            roots["continuous_learning"],
            roots["rc1"] / "cl",
            roots["demo"] / "cl",
        ):
            if (base / "run").exists():
                candidates.append(base / "run")
            elif base.exists():
                candidates.extend(list_run_dirs(base))
                if (base / "learning_history.json").exists():
                    candidates.append(base)
        # unique
        seen: set[str] = set()
        out: list[Path] = []
        for path in candidates:
            key = str(path.resolve())
            if key not in seen and path.exists():
                seen.add(key)
                out.append(path)
        return out

    def list_baseline_runs(self) -> list[Path]:
        """List baseline training runs."""
        return list_run_dirs(self.ctx.roots()["baselines"])

    def list_comparisons(self) -> list[Path]:
        """Find comparison.json files."""
        roots = self.ctx.roots()
        found: list[Path] = []
        for base in (
            roots["optimization"],
            roots.get("research", roots["artifacts"] / "research"),
            roots["rc1"] / "cmp",
            roots["demo"] / "cmp",
        ):
            if not base.exists():
                continue
            if (base / "comparison.json").exists():
                found.append(base)
            for run in list_run_dirs(base):
                if (run / "comparison.json").exists():
                    found.append(run)
        return found

    def _opt_run(self) -> Path | None:
        if self.ctx.selected_optimization_run and self.ctx.selected_optimization_run.exists():
            return self.ctx.selected_optimization_run
        runs = self.list_optimization_runs()
        return runs[0] if runs else None

    def _loop_run(self) -> Path | None:
        if self.ctx.selected_loop_run and self.ctx.selected_loop_run.exists():
            return self.ctx.selected_loop_run
        runs = self.list_loop_runs()
        return runs[0] if runs else None

    def _cl_run(self) -> Path | None:
        if self.ctx.selected_cl_run and self.ctx.selected_cl_run.exists():
            return self.ctx.selected_cl_run
        runs = self.list_cl_runs()
        return runs[0] if runs else None

    def _baseline_run(self) -> Path | None:
        if self.ctx.selected_baseline_run and self.ctx.selected_baseline_run.exists():
            return self.ctx.selected_baseline_run
        runs = self.list_baseline_runs()
        return runs[0] if runs else None

    # ----- pages -----

    def landing(self) -> dict[str, Any]:
        """Landing KPIs."""
        if self.ctx.demo_mode:
            return demo_data.demo_landing()
        loop = self._loop_run()
        opt = self._opt_run()
        cl = self._cl_run()
        loop_summary = read_json(loop / "summary.json") if loop else None
        opt_summary = read_json(opt / "summary.json") if opt else None
        cl_summary = read_json(cl / "summary.json") if cl else None
        loop_summary = loop_summary if isinstance(loop_summary, dict) else {}
        opt_summary = opt_summary if isinstance(opt_summary, dict) else {}
        cl_summary = cl_summary if isinstance(cl_summary, dict) else {}
        metrics = loop_summary.get("current_metrics") or {}
        obs = cl_summary.get("observation") or {}
        return {
            "version": __version__,
            "status": "LIVE" if (loop or opt or cl) else "NO ARTIFACTS — enable Demo Mode",
            "dataset": loop_summary.get("dataset_version")
            or obs.get("dataset_version")
            or "—",
            "optimizer": loop_summary.get("algorithm") or opt_summary.get("algorithm") or "—",
            "architecture": loop_summary.get("current_model_id")
            or opt_summary.get("best_architecture")
            or "—",
            "accuracy": metrics.get("accuracy", opt_summary.get("best_fitness")),
            "lifecycle_state": loop_summary.get("state", "—"),
            "recommendation": obs.get("cl_recommendation")
            or cl_summary.get("last_recommendation")
            or "—",
            "system_health": "healthy" if (loop or opt) else "idle",
            "last_optimization": (loop_summary.get("cycle_summaries") or [{}])[-1].get(
                "optimization", {}
            ).get("run_dir")
            if loop_summary.get("cycle_summaries")
            else (str(opt) if opt else "—"),
            "last_training": str(self._baseline_run() or "—"),
            "last_dataset_update": str(cl) if cl else "—",
            "demo": False,
        }

    def optimization_summary(self) -> dict[str, Any]:
        """Optimization center payload."""
        if self.ctx.demo_mode:
            hist = demo_data.demo_optimization_history()
            records = hist["records"]
            last = records[-1]
            return {
                "demo": True,
                "summary": {
                    "algorithm": "sapso",
                    "best_fitness": last["gbest_fitness"],
                    "iterations": last["iteration"],
                    "evaluations": last["evaluations"],
                },
                "history": hist,
                "stats": self._fitness_stats(records),
            }
        run = self._opt_run()
        if not run:
            return {"demo": False, "summary": {}, "history": {}, "stats": {}}
        summary = read_json(run / "summary.json") or {}
        history = read_json(run / "history.json") or {}
        records = history.get("records", []) if isinstance(history, dict) else []
        return {
            "demo": False,
            "run_dir": str(run),
            "summary": summary if isinstance(summary, dict) else {},
            "history": history if isinstance(history, dict) else {},
            "stats": self._fitness_stats(records if isinstance(records, list) else []),
            "cache": (summary if isinstance(summary, dict) else {}).get("cache", {}),
        }

    @staticmethod
    def _fitness_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
        if not records:
            return {}
        gbest = [float(r.get("gbest_fitness", 0)) for r in records]
        mean = [float(r.get("mean_fitness", 0)) for r in records if "mean_fitness" in r]
        return {
            "best_fitness": max(gbest) if gbest else None,
            "worst_gbest": min(gbest) if gbest else None,
            "final_gbest": gbest[-1] if gbest else None,
            "final_mean": mean[-1] if mean else None,
            "iterations": len(records),
            "evaluations": records[-1].get("evaluations"),
            "final_diversity": records[-1].get("diversity"),
        }

    def sapso_analytics(self) -> dict[str, Any]:
        """SAPSO adaptive history."""
        if self.ctx.demo_mode:
            return {"demo": True, "adaptive": demo_data.demo_adaptive_history()}
        run = self._opt_run()
        if not run:
            return {"demo": False, "adaptive": {}}
        adaptive = read_json(run / "adaptive_history.json")
        if not adaptive:
            # fall back to history coefficients
            history = read_json(run / "history.json") or {}
            records = history.get("records", []) if isinstance(history, dict) else []
            adaptive = {
                "records": [
                    {
                        "iteration": r.get("iteration"),
                        "w": r.get("w"),
                        "c1": r.get("c1"),
                        "c2": r.get("c2"),
                        "normalized_diversity": r.get("diversity"),
                        "phase": r.get("metadata", {}).get("phase", "unknown"),
                    }
                    for r in records
                    if isinstance(r, dict)
                ],
                "transitions": [],
            }
        return {"demo": False, "run_dir": str(run), "adaptive": adaptive}

    def lifecycle(self) -> dict[str, Any]:
        """Closed-loop monitor payload."""
        if self.ctx.demo_mode:
            return {
                "demo": True,
                "summary": {"state": "monitoring", "algorithm": "sapso"},
                "history": demo_data.demo_lifecycle(),
                "decisions": demo_data.demo_lifecycle()["decisions"],
            }
        run = self._loop_run()
        if not run:
            return {"demo": False, "summary": {}, "history": {}, "decisions": []}
        summary = read_json(run / "summary.json") or {}
        history = read_json(run / "lifecycle_history.json") or {}
        decisions = read_jsonl(run / "decisions.jsonl")
        return {
            "demo": False,
            "run_dir": str(run),
            "summary": summary if isinstance(summary, dict) else {},
            "history": history if isinstance(history, dict) else {},
            "decisions": decisions,
        }

    def continuous(self) -> dict[str, Any]:
        """Continuous learning page payload."""
        if self.ctx.demo_mode:
            return {
                "demo": True,
                "summary": {"last_recommendation": "OPTIMIZE_ARCH"},
                "history": demo_data.demo_learning(),
                "lineage": demo_data.demo_lineage(),
            }
        run = self._cl_run()
        if not run:
            return {"demo": False, "summary": {}, "history": {}, "lineage": {}}
        summary = read_json(run / "summary.json") or {}
        history = read_json(run / "learning_history.json") or {}
        lineage = read_json(run / "lineage.json") or {}
        return {
            "demo": False,
            "run_dir": str(run),
            "summary": summary if isinstance(summary, dict) else {},
            "history": history if isinstance(history, dict) else {},
            "lineage": lineage if isinstance(lineage, dict) else {},
        }

    def training(self) -> dict[str, Any]:
        """Training dashboard payload."""
        if self.ctx.demo_mode:
            return {
                "demo": True,
                "metrics": {
                    "val": {"accuracy": 0.91, "precision": 0.90, "recall": 0.89, "f1": 0.895}
                },
                "history": demo_data.demo_training_history(),
            }
        run = self._baseline_run()
        if not run:
            return {"demo": False, "metrics": {}, "history": {}}
        metrics = read_json(run / "metrics.json") or {}
        history = read_json(run / "history.json") or {}
        return {
            "demo": False,
            "run_dir": str(run),
            "metrics": metrics if isinstance(metrics, dict) else {},
            "history": history if isinstance(history, dict) else {},
        }

    def architecture(self) -> dict[str, Any]:
        """Architecture explorer — uses ArchitectureVisualizer when JSON present."""
        mermaid = demo_data.demo_architecture_mermaid()
        summary_text = "Enable Demo Mode or select a run with best_architecture.json / architecture.json"
        complexity: dict[str, Any] = {}
        if self.ctx.demo_mode:
            return {
                "demo": True,
                "summary_text": (
                    "Architecture: cnn_quick_best (demo)\n"
                    "input=[1,28,28] classes=10\n"
                    "Conv16 → ReLU → Pool → Conv32 → ReLU → Flatten → Dense64 → Softmax"
                ),
                "mermaid": mermaid,
                "complexity": {"depth": 6, "estimated_params": 45210},
                "spec": {"name": "cnn_quick_best", "demo": True},
            }
        run = self._opt_run() or self._baseline_run()
        spec_path = None
        if run:
            spec_path = find_named(run, "best_architecture.json", "architecture.json")
        if spec_path:
            try:
                from evonas.domain.architecture.complexity import estimate_complexity
                from evonas.domain.architecture.factory import ArchitectureFactory
                from evonas.domain.architecture.visualization import ArchitectureVisualizer

                factory = ArchitectureFactory()
                spec = (
                    factory.from_json(str(spec_path))
                    if spec_path.suffix == ".json"
                    else factory.from_yaml(str(spec_path))
                )
                summary_text = ArchitectureVisualizer().summarize(spec)
                report = estimate_complexity(spec)
                complexity = report.to_dict() if hasattr(report, "to_dict") else {
                    "depth": report.depth,
                    "estimated_params": report.estimated_params,
                }
                layers = [layer.type for layer in spec.resolved_layers()]
                mermaid = self._layers_to_mermaid(layers)
                return {
                    "demo": False,
                    "summary_text": summary_text,
                    "mermaid": mermaid,
                    "complexity": complexity,
                    "spec": spec.to_dict(),
                    "path": str(spec_path),
                }
            except Exception as exc:  # noqa: BLE001
                summary_text = f"Could not load architecture: {exc}"
        return {
            "demo": False,
            "summary_text": summary_text,
            "mermaid": mermaid,
            "complexity": complexity,
            "spec": {},
        }

    @staticmethod
    def _layers_to_mermaid(layers: list[str]) -> str:
        lines = ["flowchart TB", "  IN[Input] --> L0"]
        for i, name in enumerate(layers):
            nid = f"L{i}"
            nxt = f"L{i + 1}" if i + 1 < len(layers) else "OUT"
            label = name.replace('"', "")
            if i == 0:
                lines.append(f'  L0["{label}"] --> {nxt}')
            elif i + 1 < len(layers):
                lines.append(f'  {nid}["{label}"] --> {nxt}')
            else:
                lines.append(f'  {nid}["{label}"] --> OUT[Output]')
        if not layers:
            lines.append("  IN --> OUT[Output]")
        return "\n".join(lines)

    def experiments(self) -> list[dict[str, Any]]:
        """Experiment explorer rows."""
        rows: list[dict[str, Any]] = []
        if self.ctx.demo_mode:
            return [
                {
                    "kind": "optimization",
                    "run_id": "demo_sapso",
                    "algorithm": "sapso",
                    "metric": -0.12,
                    "path": "(demo)",
                },
                {
                    "kind": "closed_loop",
                    "run_id": "demo_loop",
                    "algorithm": "sapso",
                    "metric": 0.91,
                    "path": "(demo)",
                },
            ]
        for run in self.list_optimization_runs():
            summary = read_json(run / "summary.json")
            if isinstance(summary, dict):
                rows.append(
                    {
                        "kind": "optimization",
                        "run_id": summary.get("run_id", run.name),
                        "algorithm": summary.get("algorithm"),
                        "metric": summary.get("best_fitness"),
                        "path": str(run),
                    }
                )
        for run in self.list_loop_runs():
            summary = read_json(run / "summary.json")
            if isinstance(summary, dict):
                acc = (summary.get("current_metrics") or {}).get("accuracy")
                rows.append(
                    {
                        "kind": "closed_loop",
                        "run_id": summary.get("run_id", run.name),
                        "algorithm": summary.get("algorithm"),
                        "metric": acc,
                        "path": str(run),
                    }
                )
        research_root = self.ctx.roots().get("research")
        if research_root and research_root.exists():
            for run in list_run_dirs(research_root):
                meta = read_json(run / "meta.json")
                comparison = read_json(run / "comparison.json")
                if isinstance(meta, dict) or isinstance(comparison, dict):
                    winner = (comparison or {}).get("winner") if isinstance(comparison, dict) else None
                    rows.append(
                        {
                            "kind": "research",
                            "run_id": (meta or {}).get("experiment_id", run.name)
                            if isinstance(meta, dict)
                            else run.name,
                            "algorithm": winner,
                            "metric": None,
                            "path": str(run),
                        }
                    )
        return rows

    def comparison(self) -> dict[str, Any]:
        """Benchmark PSO vs SAPSO."""
        if self.ctx.demo_mode:
            return demo_data.demo_comparison()
        comps = self.list_comparisons()
        if not comps:
            return {}
        data = read_json(comps[0] / "comparison.json")
        return data if isinstance(data, dict) else {}

    def browse_artifacts(self, root_key: str = "artifacts") -> list[dict[str, Any]]:
        """Flat file listing under an artifact root."""
        roots = self.ctx.roots()
        root = roots.get(root_key, roots["artifacts"])
        if self.ctx.demo_mode:
            return [
                {"path": "demo/summary.json", "size": 128, "suffix": ".json"},
                {"path": "demo/history.json", "size": 2048, "suffix": ".json"},
                {"path": "demo/plots/convergence.png", "size": 4096, "suffix": ".png"},
            ]
        if not root.exists():
            return []
        files: list[dict[str, Any]] = []
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {
                ".json",
                ".csv",
                ".yaml",
                ".yml",
                ".png",
                ".txt",
                ".jsonl",
                ".md",
            }:
                try:
                    files.append(
                        {
                            "path": str(path.relative_to(root)),
                            "abs": str(path),
                            "size": path.stat().st_size,
                            "suffix": path.suffix.lower(),
                        }
                    )
                except ValueError:
                    continue
            if len(files) >= 500:
                break
        return sorted(files, key=lambda x: x["path"])

    def read_artifact(self, abs_path: str) -> dict[str, Any]:
        """Read a selected artifact for preview."""
        path = Path(abs_path)
        if not path.exists():
            return {"error": "missing"}
        if path.suffix.lower() in {".json"}:
            return {"type": "json", "data": read_json(path)}
        if path.suffix.lower() == ".jsonl":
            return {"type": "jsonl", "data": read_jsonl(path)}
        if path.suffix.lower() in {".yaml", ".yml", ".txt", ".csv", ".md"}:
            return {"type": "text", "data": read_text(path)}
        if path.suffix.lower() == ".png":
            return {"type": "image", "path": str(path)}
        return {"type": "binary", "path": str(path), "size": path.stat().st_size}

    def settings(self) -> dict[str, Any]:
        """Read-only configs."""
        configs = {
            "closed_loop": load_yaml("configs/closed_loop/default.yaml"),
            "continuous_learning": load_yaml("configs/continuous_learning/default.yaml"),
            "pso_adaptive": load_yaml("configs/pso/adaptive_mock.yaml"),
            "policy": load_yaml("configs/policies/default_policy.yaml"),
        }
        return {"version": __version__, "configs": configs, "demo": self.ctx.demo_mode}

    def health(self) -> dict[str, Any]:
        """System health panel."""
        roots = self.ctx.roots()
        artifact_bytes = 0
        file_count = 0
        art = roots["artifacts"]
        if art.exists():
            for path in art.rglob("*"):
                if path.is_file():
                    file_count += 1
                    try:
                        artifact_bytes += path.stat().st_size
                    except OSError:
                        pass
        mem_mb = None
        try:
            import psutil  # type: ignore

            mem_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
        except Exception:  # noqa: BLE001
            mem_mb = None
        warnings: list[str] = []
        if not art.exists():
            warnings.append("artifacts/ missing — enable Demo Mode for presentations")
        return {
            "version": __version__,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "artifact_bytes": artifact_bytes,
            "artifact_files": file_count,
            "process_memory_mb": mem_mb,
            "uptime_hint_s": time.time(),
            "warnings": warnings,
            "demo": self.ctx.demo_mode,
        }

    def replay_steps(self, source: str = "lifecycle") -> list[dict[str, Any]]:
        """Step-by-step replay frames from recorded histories."""
        if source == "lifecycle":
            data = self.lifecycle()
            hist = data.get("history") or {}
            return list(hist.get("transitions") or [])
        if source == "learning":
            data = self.continuous()
            hist = data.get("history") or {}
            return list(hist.get("events") or [])
        if source == "optimization":
            data = self.optimization_summary()
            hist = data.get("history") or {}
            return list(hist.get("records") or [])
        return []
