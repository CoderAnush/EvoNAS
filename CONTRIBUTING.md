# Contributing to EvoNAS

Thanks for contributing. **`idea.md` is the architectural authority.** If a PR conflicts with `idea.md`, change the PR — not the authority — unless the maintainers explicitly amend the spec.

## Setup

```bash
pip install -e ".[dev]"
pytest -q
ruff check src tests
mypy src/evonas
```

## Rules

1. Do **not** rewrite Standard PSO / SAPSO equations without a research RFC + version bump.  
2. Prefer ports/protocols for new adapters.  
3. Keep `domain/` free of torch/tensorflow.  
4. Add tests for behaviour changes.  
5. Update CHANGELOG for user-visible changes.  

## PR Checklist

- [ ] Tests pass  
- [ ] ruff / mypy clean  
- [ ] Docs updated if behaviour changes  
- [ ] No secrets / large artifacts committed  

## Scope Discipline

Phase 8+ features (deploy, dashboard, API) should land in dedicated PRs after the v0.7.0 freeze.
