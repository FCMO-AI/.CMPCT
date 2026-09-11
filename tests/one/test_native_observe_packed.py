from __future__ import annotations

import random
import zlib

import pytest

from experiments.one.native_observe import observe_native
from experiments.one.native_observe_view import observe_native_packed


def _families() -> tuple[bytes, ...]:
    rng = random.Random(0x0C02)
    random_bytes = bytes(rng.randrange(256) for _ in range(32 * 1024))
    structured = (b"ONE-LAW-" * 256) + (b"A" * 4096) + (b"ONE-LAW-" * 256)
    compressed_like = zlib.compress((b"cmpct-packed-observer-" * 4096) + random_bytes, level=9)
    near_repeat = bytearray(bytes(range(64)) * 512)
    for i in range(31, len(near_repeat), 997):
        near_repeat[i] ^= 0x5A
    return b"", b"tiny", structured, random_bytes, compressed_like, bytes(near_repeat)


@pytest.mark.parametrize("data", _families())
def test_packed_observer_materializes_exact_native_reference(data: bytes) -> None:
    reference = observe_native(data)
    packed = observe_native_packed(data)
    assert packed.materialize() == reference
    assert packed.run_count == len(reference.runs)
    assert packed.reuse_count == len(reference.reuse)
    assert packed.retained_output_bytes == packed.native_output_used_bytes
    assert packed.retained_output_bytes <= packed.native_output_capacity_bytes


def test_packed_observer_releases_empty_output_capacity() -> None:
    # A low-opportunity root should not carry the source-sized scratch arena forward.
    data = random.Random(0x5150).randbytes(1 << 20)
    packed = observe_native_packed(data)
    assert packed.native_output_capacity_bytes > 3 * len(data)
    assert packed.retained_output_bytes == 0
    assert packed.materialize() == observe_native(data)


def test_packed_observer_retains_only_used_prefix_on_structured_input() -> None:
    data = (b"ONE|LAW|" * ((1 << 20) // 8 + 1))[: 1 << 20]
    packed = observe_native_packed(data)
    assert packed.run_count + packed.reuse_count > 1000
    assert 0 < packed.retained_output_bytes < packed.native_output_capacity_bytes
    assert packed.retained_output_bytes * 4 < packed.native_output_capacity_bytes


def test_packed_observer_preserves_parameter_semantics() -> None:
    data = (b"Z" * 71) + (bytes(range(16)) * 32) + (b"Z" * 71)
    kwargs = {"min_run": 7, "chunk_size": 16, "max_index_entries": 23}
    assert observe_native_packed(data, **kwargs).materialize() == observe_native(data, **kwargs)


@pytest.mark.parametrize("bad", [bytearray(b"x"), memoryview(b"x"), "x"])
def test_packed_observer_rejects_non_bytes(bad) -> None:
    with pytest.raises(TypeError):
        observe_native_packed(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_run": 0},
        {"chunk_size": 0},
        {"max_index_entries": 0},
        {"min_run": True},
    ],
)
def test_packed_observer_rejects_invalid_limits(kwargs) -> None:
    with pytest.raises(ValueError):
        observe_native_packed(b"abc", **kwargs)
