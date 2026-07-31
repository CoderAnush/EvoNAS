"""Shared Streamlit UI chrome / theme."""

from __future__ import annotations

from evonas import __version__

PAGES = [
    "Landing",
    "System Overview",
    "Optimization Center",
    "SAPSO Analytics",
    "Architecture Explorer",
    "Training",
    "Continuous Learning",
    "Closed Loop Monitor",
    "Experiments",
    "Replay Center",
    "Benchmarks",
    "Artifact Browser",
    "Registry",
    "Models",
    "Datasets",
    "Lifecycle",
    "Lineage",
    "Version Graph",
    "History",
    "System Health",
    "Settings",
]


def inject_theme() -> None:
    """Dark professional theme CSS."""
    import streamlit as st

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; max-width: 1200px; }
        h1, h2, h3 { letter-spacing: -0.02em; }
        div[data-testid="stMetricValue"] { font-size: 1.4rem; }
        .evonas-hero {
            background: linear-gradient(135deg, #0b1220 0%, #132238 50%, #0f766e 100%);
            border: 1px solid #1f2a3a;
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }
        .evonas-hero h1 { margin: 0; color: #e8eef7; font-size: 1.8rem; }
        .evonas-hero p { margin: 0.35rem 0 0; color: #9fb3c8; }
        .stSidebar { background-color: #0b1220; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    """Render hero banner."""
    import streamlit as st

    st.markdown(
        f'<div class="evonas-hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def sidebar_nav() -> tuple[str, bool]:
    """Sidebar navigation + demo toggle."""
    import streamlit as st

    with st.sidebar:
        st.markdown(f"**EvoNAS** `{__version__}`")
        st.caption("AI Operations Dashboard")
        demo = st.toggle("Demo Mode", value=True, help="Replay/synthetic data — no training")
        st.divider()
        page = st.radio("Navigate", PAGES, index=0)
        st.divider()
        st.caption("Read-only · via REST API control plane")
    return str(page), bool(demo)
