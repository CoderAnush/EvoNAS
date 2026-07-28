"""ArchitectureGenerator encode/decode and smoke training tests."""

from __future__ import annotations

import numpy as np
import pytest

from evonas.domain.architecture.generator import ArchitectureGenerator
from evonas.domain.search_space.space import SearchSpace
from evonas.infrastructure.training.pytorch_builder import PyTorchModelBuilder


def test_search_space_yaml_load() -> None:
    space = SearchSpace.from_yaml("configs/search_spaces/cnn_quick.yaml")
    assert space.name == "cnn_quick"
    assert space.dimension == 6


def test_encode_decode_roundtrip_within_tolerance() -> None:
    gen = ArchitectureGenerator(SearchSpace.cnn_quick())
    rng = np.random.default_rng(0)
    for i in range(20):
        x = gen.random_genotype(rng)
        spec = gen.decode(x, name=f"rt_{i}")
        y = gen.encode(spec)
        # Re-decode encoded vector — discrete genes must match after quantization.
        spec2 = gen.decode(y, name=f"rt2_{i}")
        assert gen.validate(spec2).ok
        # Channel / block structure preserved via discrete decode
        assert sum(1 for layer in spec.resolved_layers() if layer.type == "conv2d") == sum(
            1 for layer in spec2.resolved_layers() if layer.type == "conv2d"
        )


def test_repair_invalid_output_units() -> None:
    from evonas.domain.architecture.layers import dense, flatten
    from evonas.domain.common.enums import TaskType
    from evonas.domain.model.architecture_spec import ArchitectureSpec

    gen = ArchitectureGenerator()
    broken = ArchitectureSpec(
        name="broken",
        version="1",
        task_type=TaskType.IMAGE_CLASSIFICATION,
        input_shape=(8, 8, 1),
        num_classes=3,
        layers=(flatten(), dense(99)),
    )
    repaired = gen.repair(broken)
    assert repaired.resolved_layers()[-1].get("units") == 3
    assert gen.validate(repaired).ok


def test_random_genotypes_smoke_train_ratio() -> None:
    """idea.md: 100 random genotypes → ≥95% successfully train 1-epoch smoke."""
    torch = pytest.importorskip("torch")
    from torch import nn

    gen = ArchitectureGenerator(SearchSpace.cnn_quick())
    builder = PyTorchModelBuilder()
    rng = np.random.default_rng(123)
    ok = 0
    n = 100
    x = torch.randn(8, 8, 8, 1)
    y = torch.randint(0, 3, (8,))
    for i in range(n):
        genotype = gen.random_genotype(rng)
        try:
            spec = gen.decode(genotype, name=f"smoke_{i}")
            assert gen.validate(spec).ok
            model = builder.build(spec)
            model.train()
            opt = torch.optim.Adam(model.parameters(), lr=1e-3)
            opt.zero_grad()
            logits = model(x)
            loss = nn.functional.cross_entropy(logits, y)
            loss.backward()
            opt.step()
            ok += 1
        except Exception:  # noqa: BLE001
            continue
    ratio = ok / n
    assert ratio >= 0.95, f"smoke success ratio {ratio:.2%} < 95% ({ok}/{n})"
