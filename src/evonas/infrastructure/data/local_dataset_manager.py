"""Local filesystem DatasetManager — public IDatasetManager implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from evonas.domain.common.enums import Split
from evonas.domain.common.errors import DataError
from evonas.domain.data.drift import detect_shift
from evonas.domain.data.models import DataStats, DatasetHandle, DriftReport, Schema
from evonas.domain.data.statistics import compute_data_stats, flatten_features, rebin_to_edges
from evonas.domain.data.transforms import TransformConfig, TransformPipeline
from evonas.domain.data.validator import DatasetValidator
from evonas.infrastructure.config.manager import ConfigurationManager
from evonas.infrastructure.data.checksums import make_splits, sha256_array
from evonas.infrastructure.data.dataset_loader import DatasetLoader
from evonas.infrastructure.data.dataset_registry import DatasetRegistry

logger = logging.getLogger(__name__)


class DatasetManager:
    """Single public facade for the EvoNAS data plane (Phase 1).

    Orchestrates loader → validator → transforms → statistics → registry
    while exposing only the ``IDatasetManager`` contract to callers.
    """

    def __init__(
        self,
        config: dict[str, Any] | str | Path,
        *,
        loader: DatasetLoader | None = None,
        validator: DatasetValidator | None = None,
        registry: DatasetRegistry | None = None,
        config_manager: ConfigurationManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigurationManager()
        if isinstance(config, (str, Path)):
            self._config = self._config_manager.load(config)
        else:
            self._config = dict(config)
        self._config_manager.validate(self._config)

        # Manifests live at artifacts/datasets/<name>/manifest.json
        manifest_dir = Path(
            self._config.get("manifest_dir", f"artifacts/datasets/{self._config['name']}")
        )
        registry_root = (
            manifest_dir.parent if manifest_dir.name == self._config["name"] else manifest_dir
        )
        self._registry = registry or DatasetRegistry(registry_root)

        self._loader = loader or DatasetLoader()
        self._validator = validator or DatasetValidator()
        self._transforms = TransformPipeline(
            TransformConfig(
                normalize=bool(self._config.get("transforms", {}).get("normalize", True)),
                flatten=bool(self._config.get("transforms", {}).get("flatten", False)),
            )
        )

        self._schema: Schema | None = None
        self._split_indices: dict[Split, np.ndarray] | None = None
        self._features: np.ndarray | None = None
        self._labels: np.ndarray | None = None
        self._stats_cache: dict[Split, DataStats] = {}
        self._checksums: dict[str, str] = {}
        self._prepared = False
        self._config_hash = self._config_manager.hash(self._config)

    @property
    def name(self) -> str:
        """Configured dataset name."""
        return str(self._config["name"])

    @property
    def config_hash(self) -> str:
        """Stable hash of the resolved dataset config."""
        return self._config_hash

    def prepare(self) -> None:
        """Materialize dataset, validate, split, checksum, and write manifest."""
        logger.info("Preparing dataset name=%s", self.name)
        features, labels, schema = self._loader.load_raw(self._config)
        self._validator.require_ok(self._validator.validate_schema(schema))

        features = self._transforms.apply(features)
        seed = int(self._config["seed"])
        shuffle = bool(self._config.get("shuffle", True))
        split_ratios = {k: float(v) for k, v in self._config["splits"].items()}
        split_indices = make_splits(len(features), split_ratios, seed=seed, shuffle=shuffle)
        self._validator.require_ok(self._validator.validate_split_disjointness(split_indices))

        checksums = {
            "raw_features": sha256_array(features),
            "raw_labels": sha256_array(labels),
        }
        for split, idx in split_indices.items():
            checksums[split.value] = sha256_array(features[idx])

        # Verify stability against prior manifest when present
        if self._registry.exists(self.name):
            prior = self._registry.load(self.name)
            if prior.checksums.get("raw_features") != checksums["raw_features"]:
                if prior.config_hash == self._config_hash:
                    raise DataError(
                        "checksum mismatch for unchanged config — corrupt or nondeterministic data",
                        code="EN_DATA_001",
                    )
                logger.warning(
                    "Dataset checksum changed with config_hash change (%s -> %s)",
                    prior.config_hash[:8],
                    self._config_hash[:8],
                )

        self._features = features
        self._labels = labels
        self._schema = schema
        self._split_indices = split_indices
        self._checksums = checksums

        stats_payload: dict[str, Any] = {}
        if bool(self._config.get("statistics", {}).get("compute_on_prepare", True)):
            bins = int(self._config.get("statistics", {}).get("feature_bins", 10))
            for split in Split:
                handle = self._build_handle(split)
                stats = compute_data_stats(
                    handle.features,
                    handle.labels,
                    split=split,
                    checksum=checksums[split.value],
                    feature_bins=bins,
                )
                self._stats_cache[split] = stats
                stats_payload[split.value] = stats.to_dict()

        manifest = self._registry.build_manifest(
            name=self.name,
            version=str(self._config.get("version", "1.0.0")),
            seed=seed,
            schema=schema,
            split_sizes={s.value: int(len(idx)) for s, idx in split_indices.items()},
            checksums=checksums,
            config_hash=self._config_hash,
            statistics=stats_payload,
        )
        self._registry.save(manifest)
        self._prepared = True
        logger.info(
            "Prepared dataset=%s checksum=%s splits=%s",
            self.name,
            checksums["raw_features"][:12],
            manifest.split_sizes,
        )

    def load(self, split: Split | str) -> DatasetHandle:
        """Load a prepared split."""
        self._ensure_prepared()
        split_enum = self._coerce_split(split)
        handle = self._build_handle(split_enum)
        self._validator.require_ok(self._validator.validate_handle(handle))
        logger.info("Loaded split=%s n=%d", split_enum.value, handle.size)
        return handle

    def get_schema(self) -> Schema:
        """Return schema after prepare."""
        self._ensure_prepared()
        assert self._schema is not None
        return self._schema

    def get_window(
        self,
        start: int,
        end: int,
        *,
        split: Split | str = Split.TRAIN,
    ) -> DatasetHandle:
        """Return index window ``[start, end)`` within a split's local ordering."""
        self._ensure_prepared()
        split_enum = self._coerce_split(split)
        assert self._split_indices is not None
        full_idx = self._split_indices[split_enum]
        if start < 0 or end > len(full_idx) or start > end:
            raise DataError(
                f"invalid window [{start}, {end}) for split size {len(full_idx)}",
                code="EN_DATA_002",
            )
        if start == end:
            raise DataError("empty window is not loadable", code="EN_DATA_002")

        window_idx = full_idx[start:end]
        handle = self._build_handle_from_indices(
            split_enum,
            window_idx,
            window_id=f"{split_enum.value}:{start}:{end}",
        )
        logger.info(
            "Loaded window split=%s start=%d end=%d n=%d",
            split_enum.value,
            start,
            end,
            handle.size,
        )
        return handle

    def subset(self, split: Split | str, fraction: float, seed: int) -> DatasetHandle:
        """Deterministically subsample a fraction of a split."""
        self._ensure_prepared()
        if not 0.0 < fraction <= 1.0:
            raise DataError("fraction must be in (0, 1]", code="EN_DATA_001")
        split_enum = self._coerce_split(split)
        assert self._split_indices is not None
        full_idx = self._split_indices[split_enum]
        n = max(1, int(round(len(full_idx) * fraction)))
        rng = np.random.default_rng(seed)
        chosen = np.sort(rng.choice(full_idx, size=n, replace=False))
        return self._build_handle_from_indices(
            split_enum,
            chosen,
            window_id=f"subset:{split_enum.value}:{fraction}:{seed}",
        )

    def compute_statistics(self, split: Split | str | None = None) -> DataStats:
        """Return cached or freshly computed statistics for a split."""
        self._ensure_prepared()
        split_enum = self._coerce_split(split or Split.TRAIN)
        if split_enum in self._stats_cache:
            return self._stats_cache[split_enum]
        handle = self.load(split_enum)
        bins = int(self._config.get("statistics", {}).get("feature_bins", 10))
        stats = compute_data_stats(
            handle.features,
            handle.labels,
            split=split_enum,
            checksum=self._checksums[split_enum.value],
            feature_bins=bins,
        )
        self._stats_cache[split_enum] = stats
        return stats

    def checksums(self) -> dict[str, str]:
        """Return checksum map from the prepared dataset."""
        self._ensure_prepared()
        return dict(self._checksums)

    def detect_shift(
        self,
        reference: DataStats | DatasetHandle,
        current: DataStats | DatasetHandle,
    ) -> DriftReport:
        """Detect distribution shift between reference and current views."""
        ref_stats, ref_feat = self._coerce_stats_and_features(reference)
        cur_stats, cur_feat = self._coerce_stats_and_features(current)

        # Re-bin current onto reference edges for comparable PSI when possible.
        if ref_feat is not None and cur_feat is not None and ref_stats.bin_edges:
            rebinned = rebin_to_edges(flatten_features(cur_feat), ref_stats.bin_edges)
            cur_stats = DataStats(
                split=cur_stats.split,
                n_samples=cur_stats.n_samples,
                feature_mean=cur_stats.feature_mean,
                feature_std=cur_stats.feature_std,
                feature_min=cur_stats.feature_min,
                feature_max=cur_stats.feature_max,
                label_histogram=cur_stats.label_histogram,
                flattened_histogram=rebinned,
                bin_edges=ref_stats.bin_edges,
                checksum=cur_stats.checksum,
            )

        drift_cfg = self._config.get("drift", {})
        return detect_shift(
            ref_stats,
            cur_stats,
            reference_features=ref_feat,
            current_features=cur_feat,
            psi_threshold=float(drift_cfg.get("psi_threshold", 0.25)),
            ks_p_threshold=float(drift_cfg.get("ks_p_value", 0.01)),
        )

    def drift_report(
        self,
        reference: DataStats | DatasetHandle,
        current: DataStats | DatasetHandle,
    ) -> DriftReport:
        """Alias for ``detect_shift``."""
        return self.detect_shift(reference, current)

    def _ensure_prepared(self) -> None:
        if not self._prepared:
            self.prepare()

    def _coerce_split(self, split: Split | str) -> Split:
        if isinstance(split, Split):
            return split
        try:
            return Split(str(split))
        except ValueError as exc:
            raise DataError(f"unknown split: {split}", code="EN_DATA_001") from exc

    def _build_handle(self, split: Split) -> DatasetHandle:
        assert self._split_indices is not None
        return self._build_handle_from_indices(split, self._split_indices[split])

    def _build_handle_from_indices(
        self,
        split: Split,
        indices: np.ndarray,
        *,
        window_id: str | None = None,
    ) -> DatasetHandle:
        assert self._features is not None and self._labels is not None and self._schema is not None
        feats = self._features[indices]
        labs = self._labels[indices]
        checksum = sha256_array(feats)
        return DatasetHandle(
            split=split,
            features=feats,
            labels=labs,
            indices=np.asarray(indices, dtype=np.int64),
            schema=self._schema,
            checksum=checksum,
            window_id=window_id,
        )

    def _coerce_stats_and_features(
        self,
        obj: DataStats | DatasetHandle,
    ) -> tuple[DataStats, np.ndarray | None]:
        if isinstance(obj, DataStats):
            return obj, None
        if isinstance(obj, DatasetHandle):
            bins = int(self._config.get("drift", {}).get("feature_bins", 10))
            stats = compute_data_stats(
                obj.features,
                obj.labels,
                split=obj.split,
                checksum=obj.checksum,
                feature_bins=bins,
            )
            return stats, obj.features
        raise DataError("reference/current must be DataStats or DatasetHandle", code="EN_DATA_001")
