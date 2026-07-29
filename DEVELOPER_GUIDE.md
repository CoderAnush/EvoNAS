# DEVELOPER_GUIDE.md

## Quick Start

```bash
git clone https://github.com/CoderAnush/EvoNAS.git
cd EvoNAS
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
# optional NN stack
pip install -e ".[pytorch,dev]"
evonas doctor
pytest -q
```

## Layout

| Path | Role |
|---|---|
| `idea.md` | Sole architectural authority |
| `src/evonas/domain` | Pure logic |
| `src/evonas/application` | Use-cases / orchestration |
| `src/evonas/infrastructure` | Adapters |
| `src/evonas/ports` | Protocols |
| `src/evonas/presentation/cli` | CLI |
| `configs/` | YAML contracts |
| `tests/` | pytest suite |
| `docs/` | Phase + RC1 docs |

## Coding Rules

1. Do not put framework imports in `domain/`  
2. Extend via ports — do not rewrite frozen engines  
3. Prefer config over hardcoded thresholds  
4. Add tests with unique filenames under the right package folder  

## Useful Commands

```bash
ruff check src tests
mypy src/evonas
pytest -q
evonas --help
```

## Onboarding Path

1. Read `docs/SYSTEM_WORKFLOW.md`  
2. Run `docs/demo/CLI_COMMANDS.md`  
3. Read `docs/rc1/ARCHITECTURE_FREEZE.md` before changing cores  
