from __future__ import annotations

import random

from experiments.one.native_observe import observe_native
from experiments.one.native_observe_small_vector import observe_native_small_vector


def test_small_vector_empty_output_stays_empty() -> None:
    data = random.Random(0x5100).randbytes(64 * 1024)
    view = observe_native_small_vector(data)
    assert view.total_count == 0
    assert not view.uses_inline_slot
    assert not view.uses_bulk_bytes
    assert view.retained_output_bytes == 0
    assert view.materialize() == observe_native(data)


def test_small_vector_single_run_uses_inline_slot() -> None:
    data = random.Random(0x5101).randbytes(32 * 1024) + (b"Z" * 257)
    view = observe_native_small_vector(data)
    reference = observe_native(data)
    assert len(reference.runs) == 1
    assert len(reference.reuse) == 0
    assert view.total_count == 1
    assert view.uses_inline_slot
    assert not view.uses_bulk_bytes
    assert view.inline_kind == 1
    assert view.runs_bytes == b""
    assert view.reuse_bytes == b""
    assert view.materialize() == reference


def test_small_vector_bulk_path_preserves_many_opportunities() -> None:
    data = (b"ONE|LAW|" * ((128 * 1024) // 8 + 1))[: 128 * 1024]
    view = observe_native_small_vector(data)
    reference = observe_native(data)
    assert view.total_count > 1
    assert not view.uses_inline_slot
    assert view.uses_bulk_bytes
    assert view.retained_output_bytes == view.native_output_used_bytes
    assert view.retained_output_bytes < view.native_output_capacity_bytes
    assert view.materialize() == reference


def test_small_vector_parameter_semantics() -> None:
    data = (b"A" * 71) + bytes(range(64)) * 64 + (b"A" * 71)
    kwargs = {"min_run": 7, "chunk_size": 16, "max_index_entries": 31}
    assert observe_native_small_vector(data, **kwargs).materialize() == observe_native(data, **kwargs)
