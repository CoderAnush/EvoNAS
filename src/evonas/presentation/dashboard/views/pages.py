"""Dashboard page renderers."""

from __future__ import annotations

import json
from typing import Any

from evonas.presentation.dashboard.components import charts
from evonas.presentation.dashboard.components.chrome import hero


def render_landing(svc: Any) -> None:
    """Landing dashboard."""
    import streamlit as st

    hero("EvoNAS Operations", "Autonomous closed-loop AutoML control center")
    data = svc.landing()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Version", data.get("version"))
    c2.metric("Status", data.get("status"))
    c3.metric("Lifecycle", str(data.get("lifecycle_state")))
    c4.metric("Health", str(data.get("system_health")))
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Dataset", str(data.get("dataset")))
    c6.metric("Optimizer", str(data.get("optimizer")))
    c7.metric("Architecture", str(data.get("architecture")))
    acc = data.get("accuracy")
    c8.metric("Accuracy / Fitness", f"{acc:.4f}" if isinstance(acc, (int, float)) else str(acc))
    st.info(f"CL recommendation: **{data.get('recommendation')}**")
    with st.expander("Recent activity"):
        st.write(
            {
                "last_optimization": data.get("last_optimization"),
                "last_training": data.get("last_training"),
                "last_dataset_update": data.get("last_dataset_update"),
                "demo": data.get("demo"),
            }
        )


def render_overview(svc: Any) -> None:
    """System overview pipeline."""
    import streamlit as st

    hero("System Overview", "End-to-end EvoNAS platform map")
    landing = svc.landing()
    st.markdown(
        """
```mermaid
flowchart LR
  DS[Dataset] --> ARCH[Architecture]
  ARCH --> TR[Training]
  TR --> EV[Evaluation]
  EV --> SAPSO[SAPSO / PSO]
  CL[Continuous Learning] -->|recommend| DEC[Decision Engine]
  DEC --> LOOP[Closed Loop]
  LOOP --> SAPSO
  SAPSO --> VAL[Validate]
  VAL --> PRO[Promote / Reject]
  PRO --> DS
```
"""
    )
    st.success(
        f"Live snapshot · state=`{landing.get('lifecycle_state')}` · "
        f"optimizer=`{landing.get('optimizer')}` · rec=`{landing.get('recommendation')}`"
    )


def render_optimization(svc: Any) -> None:
    """Optimization center."""
    import streamlit as st

    hero("Optimization Center", "Swarm search telemetry")
    _run_selector_opt(svc)
    data = svc.optimization_summary()
    summary = data.get("summary") or {}
    stats = data.get("stats") or {}
    cols = st.columns(5)
    cols[0].metric("Algorithm", summary.get("algorithm", "—"))
    cols[1].metric("Best fitness", _fmt(stats.get("best_fitness", summary.get("best_fitness"))))
    cols[2].metric("Iterations", stats.get("iterations", summary.get("iterations")))
    cols[3].metric("Evaluations", stats.get("evaluations", summary.get("evaluations")))
    cols[4].metric("Diversity", _fmt(stats.get("final_diversity")))
    fig = charts.fitness_from_history(data.get("history") or {})
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    cache = data.get("cache") or {}
    if cache:
        st.caption(f"Cache: {cache}")
    if data.get("run_dir"):
        st.caption(f"Run: `{data['run_dir']}`")


def render_sapso(svc: Any) -> None:
    """SAPSO analytics."""
    import streamlit as st

    hero("SAPSO Analytics", "Adaptive coefficients & swarm phases")
    _run_selector_opt(svc)
    data = svc.sapso_analytics()
    adaptive = data.get("adaptive") or {}
    records = adaptive.get("records") or []
    phase = records[-1].get("phase") if records else "—"
    st.metric("Current phase", phase)
    fig1 = charts.coefficients_from_adaptive(adaptive)
    if fig1:
        st.plotly_chart(fig1, use_container_width=True)
    fig2 = charts.diversity_from_adaptive(adaptive)
    if fig2:
        st.plotly_chart(fig2, use_container_width=True)
    transitions = adaptive.get("transitions") or []
    if transitions:
        st.subheader("State transitions")
        st.dataframe(transitions, use_container_width=True)
    if records:
        st.subheader("Coefficient table")
        st.dataframe(records, use_container_width=True, height=280)


def render_architecture(svc: Any) -> None:
    """Architecture explorer."""
    import streamlit as st

    hero("Architecture Explorer", "ArchitectureSpec inspection")
    data = svc.architecture()
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.code(data.get("summary_text") or "", language="text")
        st.markdown(f"```mermaid\n{data.get('mermaid')}\n```")
    with c2:
        st.subheader("Complexity")
        st.json(data.get("complexity") or {})
        if data.get("spec"):
            with st.expander("ArchitectureSpec JSON"):
                st.json(data["spec"])


def render_training(svc: Any) -> None:
    """Training dashboard."""
    import streamlit as st

    hero("Training Dashboard", "Baseline metrics & curves")
    data = svc.training()
    metrics = data.get("metrics") or {}
    val = metrics.get("val") or metrics.get("test") or {}
    cols = st.columns(4)
    cols[0].metric("Accuracy", _fmt(val.get("accuracy")))
    cols[1].metric("Precision", _fmt(val.get("precision")))
    cols[2].metric("Recall", _fmt(val.get("recall")))
    cols[3].metric("F1", _fmt(val.get("f1")))
    fig = charts.training_curves(data.get("history") or {})
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    cm = val.get("confusion_matrix")
    if cm:
        st.subheader("Confusion matrix")
        st.json(cm)
    if not val and not (data.get("history") or {}).get("epochs"):
        st.warning("No baseline artifacts found — enable Demo Mode or run `evonas train-baseline`.")


def render_continuous(svc: Any) -> None:
    """Continuous learning."""
    import streamlit as st

    hero("Continuous Learning", "Dataset evolution · recommendations only")
    data = svc.continuous()
    summary = data.get("summary") or {}
    st.metric("Last recommendation", summary.get("last_recommendation", "—"))
    hist = data.get("history") or {}
    fig = charts.drift_chart(hist.get("drift_reports") or [])
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Events")
        st.dataframe(hist.get("events") or [], use_container_width=True, height=260)
        st.subheader("Policy decisions")
        st.dataframe(hist.get("policy_decisions") or [], use_container_width=True, height=200)
    with c2:
        st.subheader("Versions")
        st.dataframe(hist.get("versions") or [], use_container_width=True, height=200)
        st.subheader("Lineage")
        lineage = data.get("lineage") or {}
        st.json({"edges": lineage.get("edges"), "nodes": list((lineage.get("nodes") or {}).keys())})


def render_closed_loop(svc: Any) -> None:
    """Closed-loop monitor."""
    import streamlit as st

    hero("Closed Loop Monitor", "Lifecycle · decisions · promotions")
    data = svc.lifecycle()
    summary = data.get("summary") or {}
    cols = st.columns(4)
    cols[0].metric("State", summary.get("state", "—"))
    cols[1].metric("Algorithm", summary.get("algorithm", "—"))
    cols[2].metric("Cycles", summary.get("cycles", "—"))
    cols[3].metric("Optimizations", summary.get("optimizations_used", "—"))
    hist = data.get("history") or {}
    transitions = hist.get("transitions") or []
    if transitions:
        labels = [f"{t.get('source')}→{t.get('target')}" for t in transitions]
        counts: dict[str, int] = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        st.plotly_chart(
            charts.bar_chart(
                list(counts.keys()),
                [float(v) for v in counts.values()],
                title="Transition counts",
            ),
            use_container_width=True,
        )
        st.dataframe(transitions, use_container_width=True, height=240)
    st.subheader("Decisions")
    st.dataframe(
        data.get("decisions") or hist.get("decisions") or [],
        use_container_width=True,
        height=240,
    )
    st.subheader("Promotions")
    st.dataframe(hist.get("promotions") or summary.get("promotions") or [], use_container_width=True)


def render_experiments(svc: Any) -> None:
    """Experiment explorer."""
    import streamlit as st

    hero("Experiment Explorer", "Artifacts across subsystems")
    rows = svc.experiments()
    kinds = sorted({str(r.get("kind")) for r in rows if r.get("kind")})
    kind = st.multiselect("Filter kind", kinds, default=None)
    filtered = [r for r in rows if not kind or r.get("kind") in kind]
    st.dataframe(filtered, use_container_width=True)
    if filtered:
        st.caption(f"{len(filtered)} experiments")


def render_replay(svc: Any) -> None:
    """Replay center."""
    import streamlit as st

    hero("Replay Center", "Step through recorded histories — no recompute")
    source = st.selectbox("Replay source", ["lifecycle", "learning", "optimization"])
    steps = svc.replay_steps(str(source or "lifecycle"))
    if not steps:
        st.warning("No replay frames available.")
        return
    idx = st.slider("Step", 0, max(0, len(steps) - 1), 0)
    st.progress((idx + 1) / len(steps))
    st.json(steps[idx])
    with st.expander("All steps"):
        st.dataframe(steps, use_container_width=True)


def render_benchmarks(svc: Any) -> None:
    """PSO vs SAPSO."""
    import streamlit as st

    hero("Benchmark Dashboard", "Standard PSO vs SAPSO")
    data = svc.comparison()
    if not data:
        st.warning("No comparison.json found — enable Demo Mode or run `evonas compare-optimizers`.")
        return
    st.metric("Winner", data.get("winner", "—"))
    c1, c2, c3 = st.columns(3)
    pso = data.get("standard_pso") or {}
    sapso = data.get("sapso") or {}
    c1.metric("PSO mean best", _fmt(pso.get("mean_best_fitness")))
    c2.metric("SAPSO mean best", _fmt(sapso.get("mean_best_fitness")))
    c3.metric("Δ (SAPSO−PSO)", _fmt(data.get("delta_mean_fitness_sapso_minus_pso")))
    st.plotly_chart(
        charts.bar_chart(
            ["standard_pso", "sapso"],
            [
                float(pso.get("mean_best_fitness") or 0),
                float(sapso.get("mean_best_fitness") or 0),
            ],
            title="Mean best fitness",
        ),
        use_container_width=True,
    )
    st.json(data)


def render_artifacts(svc: Any) -> None:
    """Artifact browser."""
    import streamlit as st

    hero("Artifact Browser", "Open histories, configs, and plots")
    root_key = st.selectbox(
        "Root",
        ["artifacts", "optimization", "closed_loop", "continuous_learning", "baselines", "rc1", "demo"],
    )
    files = svc.browse_artifacts(str(root_key or "artifacts"))
    st.caption(f"{len(files)} files (capped)")
    st.dataframe(files, use_container_width=True, height=280)
    abs_paths = [f.get("abs") for f in files if f.get("abs")]
    if abs_paths:
        choice = st.selectbox("Preview", abs_paths)
        preview = svc.read_artifact(str(choice))
        if preview.get("type") == "json":
            st.json(preview.get("data"))
        elif preview.get("type") in {"text", "jsonl"}:
            st.code(
                preview.get("data")
                if preview.get("type") == "text"
                else json.dumps(preview.get("data"), indent=2)
            )
        elif preview.get("type") == "image":
            image_path = preview.get("path")
            if isinstance(image_path, str) and image_path:
                st.image(image_path)
        else:
            st.write(preview)


def render_health(svc: Any) -> None:
    """System health."""
    import streamlit as st

    hero("System Health", "Runtime & artifact footprint")
    data = svc.health()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Version", data.get("version"))
    c2.metric("Artifact files", data.get("artifact_files"))
    c3.metric("Artifact MB", round((data.get("artifact_bytes") or 0) / (1024 * 1024), 2))
    c4.metric("Process RSS MB", data.get("process_memory_mb") or "n/a")
    st.write({"python": data.get("python"), "platform": data.get("platform")})
    for warning in data.get("warnings") or []:
        st.warning(warning)


def render_settings(svc: Any) -> None:
    """Read-only settings."""
    import streamlit as st

    hero("Settings", "Loaded configuration (read-only)")
    data = svc.settings()
    st.caption(f"EvoNAS {data.get('version')} · demo={data.get('demo')}")
    configs = data.get("configs") or {}
    tab_names = list(configs.keys()) or ["none"]
    tabs = st.tabs(tab_names)
    for tab, name in zip(tabs, tab_names, strict=False):
        with tab:
            st.json(configs.get(name) or {})


def _run_selector_opt(svc: Any) -> None:
    import streamlit as st

    runs = svc.list_optimization_runs()
    if not runs or svc.ctx.demo_mode:
        return
    labels = [str(r) for r in runs]
    choice = st.selectbox("Optimization run", labels, key="opt_run_select")
    svc.ctx.selected_optimization_run = next(r for r in runs if str(r) == choice)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return "—"
    return str(value)


RENDERERS = {
    "Landing": render_landing,
    "System Overview": render_overview,
    "Optimization Center": render_optimization,
    "SAPSO Analytics": render_sapso,
    "Architecture Explorer": render_architecture,
    "Training": render_training,
    "Continuous Learning": render_continuous,
    "Closed Loop Monitor": render_closed_loop,
    "Experiments": render_experiments,
    "Replay Center": render_replay,
    "Benchmarks": render_benchmarks,
    "Artifact Browser": render_artifacts,
    "System Health": render_health,
    "Settings": render_settings,
}
