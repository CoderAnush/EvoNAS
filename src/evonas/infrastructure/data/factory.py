"""Factory helpers: wire application / dataset YAML into DatasetManager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from evonas.domain.common.errors import ConfigError
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.data.local_dataset_manager import DatasetManager

logger = logging.getLogger(__name__)


def resolve_dataset_config_path(
    app_config: dict[str, Any] | str | Path = "configs/default.yaml",
    *,
    config_manager: ConfigurationManager | None = None,
) -> Path:
    """Resolve the dataset YAML path from an application config.

    Expects ``dataset.config_path`` (idea.md coding task: wire config → dataset).
    """
    mgr = config_manager or ConfigurationManager()
    if isinstance(app_config, (str, Path)):
        cfg = mgr.load(app_config)
    else:
        cfg = app_config
    dataset_block = cfg.get("dataset", {})
    if not isinstance(dataset_block, dict):
        raise ConfigError("app config 'dataset' must be a mapping", code="EN_CFG_001")
    rel = dataset_block.get("config_path", "configs/datasets/toy_quick.yaml")
    path = Path(str(rel))
    logger.info("Resolved dataset config path=%s", path)
    return path


def create_dataset_manager(
    app_or_dataset_config: dict[str, Any] | str | Path = "configs/default.yaml",
    *,
    config_manager: ConfigurationManager | None = None,
    treat_as_dataset_config: bool = False,
) -> DatasetManager:
    """Create a ``DatasetManager`` from app config or a dataset YAML.

    Parameters
    ----------
    app_or_dataset_config:
        Path/dict for either the application config (default) or a dataset
        config when ``treat_as_dataset_config=True``.
    treat_as_dataset_config:
        If True, pass the argument directly to ``DatasetManager``.
        If False, resolve ``dataset.config_path`` first.
    """
    mgr = config_manager or ConfigurationManager()
    if treat_as_dataset_config:
        return DatasetManager(app_or_dataset_config, config_manager=mgr)

    if isinstance(app_or_dataset_config, dict) and "input_shape" in app_or_dataset_config:
        # Heuristic: already a dataset config mapping.
        return DatasetManager(app_or_dataset_config, config_manager=mgr)

    dataset_path = resolve_dataset_config_path(
        app_or_dataset_config,
        config_manager=mgr,
    )
    return DatasetManager(dataset_path, config_manager=mgr)
