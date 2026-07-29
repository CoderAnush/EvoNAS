# Release Notes — EvoNAS v0.8.0

**Date:** 2026-07-30  
**Codename:** AI Operations Dashboard  

## Highlights

EvoNAS now ships a **professional Streamlit AI Operations Dashboard** for research demos, professor presentations, and portfolio showcases. It visualizes dataset evolution, SAPSO, closed-loop decisions, continuous learning, and artifacts — in Demo Mode without retraining.

## Install & launch

```bash
pip install -e ".[dashboard,dev]"
evonas dashboard --demo
```

## Included

- Multipage dark-themed operations console  
- Demo Mode + live artifact discovery  
- Plotly charts for fitness, coefficients, diversity, drift, training  
- Architecture explorer (text + Mermaid)  
- Replay center (lifecycle / learning / optimization steps)  
- CLI `evonas dashboard`  
- Optional extra `evonas[dashboard]` (streamlit, plotly, pandas, matplotlib)

## Not included

Deployment, FastAPI, authentication, cloud infrastructure.

## Upgrade notes

- Package version **0.8.0**  
- Core AutoML engines unchanged  
- Dashboard is presentation-only
