"""Experiment matrix expansion — algorithm × dataset × seed × config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator


@dataclass(frozen=True, slots=True)
class MatrixCell:
    """One concrete experiment cell."""

    algorithm: str
    dataset: str
    seed: int
    config_id: str
    landscape: str
    space_path: str
    extras: dict[str, Any]


def expand_matrix(spec: dict[str, Any]) -> list[MatrixCell]:
    """Expand a YAML matrix block into cells."""
    algorithms = list(spec.get("algorithms") or ["standard_pso", "sapso"])
    datasets = list(spec.get("datasets") or [{"id": "sphere", "landscape": "sphere"}])
    seeds = _seeds(spec)
    configs = list(spec.get("configurations") or [{"id": "default"}])
    default_space = str(
        spec.get("search_space", {}).get("path", "configs/search_spaces/sphere_2d.yaml")
        if isinstance(spec.get("search_space"), dict)
        else spec.get("search_space") or "configs/search_spaces/sphere_2d.yaml"
    )
    cells: list[MatrixCell] = []
    for algo in algorithms:
        for ds in datasets:
            if isinstance(ds, str):
                ds_id, landscape, space = ds, ds, default_space
                extras: dict[str, Any] = {}
            else:
                ds_id = str(ds.get("id", ds.get("name", "dataset")))
                landscape = str(ds.get("landscape", ds_id))
                space = str(ds.get("space_path", default_space))
                extras = {k: v for k, v in ds.items() if k not in {"id", "name", "landscape", "space_path"}}
            for cfg in configs:
                cfg_id = str(cfg.get("id", "default")) if isinstance(cfg, dict) else str(cfg)
                cfg_extras = dict(cfg) if isinstance(cfg, dict) else {}
                for seed in seeds:
                    cells.append(
                        MatrixCell(
                            algorithm=str(algo),
                            dataset=ds_id,
                            seed=int(seed),
                            config_id=cfg_id,
                            landscape=landscape,
                            space_path=space,
                            extras={**extras, **cfg_extras},
                        )
                    )
    return cells


def iter_matrix(spec: dict[str, Any]) -> Iterator[MatrixCell]:
    yield from expand_matrix(spec)


def _seeds(spec: dict[str, Any]) -> list[int]:
    block = dict(spec.get("seeds") or spec.get("comparison") or {})
    if "list" in block:
        return [int(s) for s in block["list"]]
    if "values" in block:
        return [int(s) for s in block["values"]]
    n = int(block.get("n", spec.get("n_seeds", 5)))
    base = int(block.get("base", spec.get("seed", 42)))
    return [base + i for i in range(n)]
