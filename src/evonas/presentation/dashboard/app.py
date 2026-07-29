"""Streamlit app entry — imports deferred so `import app` is light."""

from __future__ import annotations


def main() -> None:
    """Streamlit multipage operations console."""
    import os

    import streamlit as st

    from evonas.presentation.dashboard.components.chrome import inject_theme, sidebar_nav
    from evonas.presentation.dashboard.services.facade import DashboardContext, DashboardService
    from evonas.presentation.dashboard.views.pages import RENDERERS

    st.set_page_config(
        page_title="EvoNAS Operations",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    page, demo = sidebar_nav()
    if os.environ.get("EVONAS_DASHBOARD_DEMO", "").strip() in {"1", "true", "True"}:
        demo = True
    ctx = DashboardContext(demo_mode=bool(demo))
    svc = DashboardService(ctx)
    renderer = RENDERERS.get(page)
    if renderer is None:
        st.error(f"Unknown page: {page}")
        return
    renderer(svc)


if __name__ == "__main__":
    main()
