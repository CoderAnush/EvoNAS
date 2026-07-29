"""Streamlit app entry — data exclusively via REST API (Phase 9)."""

from __future__ import annotations


def main() -> None:
    """Streamlit multipage operations console."""
    import os

    import streamlit as st

    from evonas.presentation.dashboard.components.chrome import inject_theme, sidebar_nav
    from evonas.presentation.dashboard.services.api_client import ApiDashboardService
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
    api_url = os.environ.get("EVONAS_API_URL", "http://127.0.0.1:8000")
    svc = ApiDashboardService(base_url=api_url, demo_mode=bool(demo))
    renderer = RENDERERS.get(page)
    if renderer is None:
        st.error(f"Unknown page: {page}")
        return
    try:
        renderer(svc)
    except RuntimeError as exc:
        st.error(str(exc))
        st.info("Start the control plane: `evonas api` or `evonas serve --demo`")


if __name__ == "__main__":
    main()
