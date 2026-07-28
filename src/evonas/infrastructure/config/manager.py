"""YAML configuration loader with stable hashing."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import yaml

from evonas.domain.common.errors import ConfigError

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Minimal configuration manager for Phase 0/1.

    Loads YAML, validates required keys for dataset configs, and produces
    stable SHA-256 hashes of canonicalized JSON.
    """

    def load(self, path: str | Path) -> dict[str, Any]:
        """Load a YAML or JSON configuration file."""
        file_path = Path(path)
        if not file_path.exists():
            raise ConfigError(f"config file not found: {file_path}", code="EN_CFG_001")
        try:
            text = file_path.read_text(encoding="utf-8")
            if file_path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(text)
            elif file_path.suffix.lower() == ".json":
                data = json.loads(text)
            else:
                raise ConfigError(
                    f"unsupported config extension: {file_path.suffix}",
                    code="EN_CFG_001",
                )
        except ConfigError:
            raise
        except Exception as exc:  # noqa: BLE001 — translate to ConfigError
            raise ConfigError(
                f"failed to parse config {file_path}: {exc}", code="EN_CFG_001"
            ) from exc

        if not isinstance(data, dict):
            raise ConfigError("config root must be a mapping", code="EN_CFG_001")
        logger.info("Loaded config from %s", file_path)
        return data

    def validate(self, config: dict[str, Any]) -> bool:
        """Validate dataset-oriented configs used in Phase 1."""
        required = ["name", "input_shape", "splits", "seed"]
        missing = [k for k in required if k not in config]
        if missing:
            raise ConfigError(f"missing required keys: {missing}", code="EN_CFG_001")
        splits = config["splits"]
        if not isinstance(splits, dict):
            raise ConfigError("splits must be a mapping", code="EN_CFG_001")
        total = float(sum(float(v) for v in splits.values()))
        if abs(total - 1.0) > 1e-6:
            raise ConfigError(f"split ratios must sum to 1.0, got {total}", code="EN_CFG_001")
        shape = config["input_shape"]
        if not isinstance(shape, (list, tuple)) or not shape:
            raise ConfigError("input_shape must be a non-empty list", code="EN_CFG_001")
        return True

    def get(self, key: str, config: dict[str, Any] | None = None) -> Any:
        """Resolve a dotted key path from a config mapping."""
        if config is None:
            raise ConfigError("config argument is required for get()", code="EN_CFG_001")
        cur: Any = config
        for part in key.split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise ConfigError(f"key not found: {key}", code="EN_CFG_001")
            cur = cur[part]
        return cur

    def hash(self, config: dict[str, Any]) -> str:
        """Return a stable SHA-256 hex digest of canonicalized config JSON."""
        canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        logger.debug("Config hash=%s", digest[:12])
        return digest
