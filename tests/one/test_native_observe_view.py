from __future__ import annotations

import random
import zlib

import pytest

from experiments.one.native_observe import observe_native
from experiments.one.native_observe_view import observe_native_view


def _families() -> tuple[bytes, ...]:
    rng = random.Random(0x0C01)
    random_bytes = bytes(rng.randrange(256) for _ in range(32 * 1024))
    structured = (b"ONE-LAW-" * 256) + (b"A" * 4096) + (b"ONE-LAW-" * 256)
    compressed_like = zlib.compress((b"cmpct-observer-view-" * 4096) + random_bytes, level=9)
    near_repeat = bytearray((bytes(range(64)) * 512))
    for i in range(31, len(near_repeat), 997):
        near_repeat[i] ^= 0x5A
    return b"", b"tiny", structured, random_bytes, compressed_like, bytes(near_repeat)


@pytest.mark.parametrize("data", _families())
def test_native_observe_view_materializes_exact_reference(data: bytes) -> None:
    reference = observe_native(data)
    view = observe_native_view(data)
    assert view.materialize() == reference
    assert view.run_count == len(reference.runs)
    assert view.reuse_count == len(reference.reuse)
    assert view.native_output_used_bytes <= view.native_output_capacity_bytes


def test_native_observe_view_preserves_parameter_semantics() -> None:
    data = (b"Z" * 71) + (bytes(range(16)) * 32) + (b"Z" * 71)
    kwargs = {"min_run": 7, "chunk_size": 16, "max_index_entries": 23}
    assert observe_native_view(data, **kwargs).materialize() == observe_native(data, **kwargs)


@pytest.mark.parametrize("bad", [bytearray(b"x"), memoryview(b"x"), "x"])
def test_native_observe_view_rejects_non_bytes(bad) -> None:
    with pytest.raises(TypeError):
        observe_native_view(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_run": 0},
        {"chunk_size": 0},
        {"max_index_entries": 0},
        {"min_run": True},
    ],
)
def test_native_observe_view_rejects_invalid_limits(kwargs) -> None:
    with pytest.raises(ValueError):
        observe_native_view(b"abc", **kwargs)
