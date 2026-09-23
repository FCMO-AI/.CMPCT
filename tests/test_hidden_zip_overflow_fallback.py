from __future__ import annotations

import stat
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.builder_hidden_zip import (
    DeferredHiddenFile, FALLBACK_HASH_CHUNK, finalize_deferred_hidden_files,
    finalize_hidden_fallback_only, hidden_cohort_within_surface_budget,
    surface_hidden_candidate, validate_surfaced_candidate,
)
from cmpct.codec import S_BLOB, sha


def _item(path: Path) -> DeferredHiddenFile:
    st = path.stat(); raw = path.read_bytes()
    return DeferredHiddenFile(surface_hidden_candidate(path.name, path, st, raw), stat.S_IMODE(st.st_mode), st.st_mtime_ns, path.suffix.lower())


def test_disabled_discovery_prefix_returns_to_ordinary_storage_without_proof(tmp_path: Path) -> None:
    builder = Builder(tmp_path)
    paths = [tmp_path / f"candidate-{i}.bin" for i in range(3)]
    for i, path in enumerate(paths): path.write_bytes(b"PK\x03\x04" + bytes([i]) * 100)
    items = [_item(path) for path in paths]
    finalize_hidden_fallback_only(builder, items)
    rows = {row[0]: row for row in builder.files}
    assert set(rows) == {path.name for path in paths}
    for path in paths:
        row = rows[path.name]
        assert row[6][0] == S_BLOB; assert row[5] == sha(path.read_bytes())


def test_streaming_snapshot_validator_handles_multi_chunk_source_and_detects_drift(tmp_path: Path) -> None:
    path = tmp_path / "candidate.bin"; path.write_bytes(b"P" * (FALLBACK_HASH_CHUNK * 2 + 17)); item = _item(path)
    assert validate_surfaced_candidate(item.candidate)
    path.write_bytes(b"Q" * (FALLBACK_HASH_CHUNK * 2 + 17))
    assert not validate_surfaced_candidate(item.candidate)


def test_discovery_finalizer_refuses_source_count_before_copying_hostile_cohort(tmp_path: Path, monkeypatch) -> None:
    builder = Builder(tmp_path); path = tmp_path / "candidate.bin"; path.write_bytes(b"PK\x03\x04payload"); item = _item(path)
    import cmpct.builder_hidden_zip as bridge
    monkeypatch.setattr(bridge, "MAX_OBSERVATION_FILES", 1)
    with pytest.raises(ValueError, match="source/byte ceiling"):
        finalize_deferred_hidden_files(builder, [item, item], min_verified_reuse=1)
    assert builder.files == []; assert builder.cands == {}; assert builder.recipes == []


def test_discovery_finalizer_refuses_aggregate_surface_bytes_before_proof(tmp_path: Path, monkeypatch) -> None:
    builder = Builder(tmp_path); a = tmp_path / "a.bin"; b = tmp_path / "b.bin"
    a.write_bytes(b"PK\x03\x04" + b"a" * 100); b.write_bytes(b"PK\x03\x04" + b"b" * 100)
    items = [_item(a), _item(b)]
    import cmpct.builder_hidden_zip as bridge
    monkeypatch.setattr(bridge, "MAX_HIDDEN_SURFACE_AGGREGATE_BYTES", a.stat().st_size + b.stat().st_size - 1)
    assert not hidden_cohort_within_surface_budget(items)
    with pytest.raises(ValueError, match="source/byte ceiling"):
        finalize_deferred_hidden_files(builder, items, min_verified_reuse=1)
    assert builder.files == []; assert builder.cands == {}; assert builder.recipes == []


def test_fallback_only_still_refuses_snapshot_drift(tmp_path: Path) -> None:
    builder = Builder(tmp_path); path = tmp_path / "candidate.bin"; path.write_bytes(b"PK\x03\x04old")
    item = _item(path); path.write_bytes(b"PK\x03\x04new")
    with pytest.raises(RuntimeError, match="changed before ordinary fallback"):
        finalize_hidden_fallback_only(builder, [item])
    assert builder.files == []; assert builder.cands == {}
