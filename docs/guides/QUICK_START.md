# Quick Start — EvoNAS v1.0.0

```bash
git clone https://github.com/CoderAnush/EvoNAS.git
cd EvoNAS
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -e ".[dev]"
evonas version   # expect 1.0.0
evonas doctor
```

### 60-second smoke

```bash
evonas optimize --config configs/pso/adaptive_mock.yaml --dry-run
evonas benchmark --config configs/benchmarks/default.yaml
```

### Ops UI

```bash
pip install -e ".[api,dashboard]"
evonas serve --demo
# API http://127.0.0.1:8000/docs · Dashboard http://127.0.0.1:8501
```

### Research campaign (optional)

```bash
pip install -e ".[dev,dashboard]"
python scripts/run_phase12a_campaign.py
```

Next: [Installation](INSTALLATION.md) · [CLI Guide](CLI_GUIDE.md) · [Architecture Book](../architecture/ARCHITECTURE_BOOK.md)
