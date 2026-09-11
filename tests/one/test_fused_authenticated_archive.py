from __future__ import annotations

import os
from pathlib import Path

import pytest

from experiments.one.archive_envelope import CHUNK_BYTES
from experiments.one.authenticated_archive_envelope import AUTH_LEAF_BYTES, build_authenticated_archive, open_authenticated_archive
from experiments.one.fused_authenticated_archive import build_authenticated_archive_fused


def _pattern(length: int, salt: int = 0) -> bytes:
    block = bytes(((i * 37 + salt * 19 + (i >> 3)) & 255) for i in range(4096))
    return (block * ((length + len(block) - 1) // len(block)))[:length]


def _selective_invariants(stats) -> tuple:
    """Return deterministic range geometry/resource accounting, excluding clocks."""
    return (
        stats.requested_bytes,
        stats.cone_start,
        stats.cone_bytes,
        stats.packed_source_bytes,
        stats.source_read_bytes,
        stats.source_plan_write_bytes,
        stats.sink_write_bytes,
        stats.proof_payload_bytes,
        stats.proof_hash_bytes,
        stats.auth_index_bytes,
        stats.plan_commands,
        stats.fallback,
        stats.fallback_reason,
        stats.modeled_data_movement_bytes,
        stats.peak_temporary_bytes,
    )


def _make_tree(root: Path, shape: str) -> dict[str, bytes]:
    if shape == "32k":
        payloads = {"data.bin": _pattern(32 * 1024, 1)}
    elif shape == "256k":
        payloads = {"data.bin": _pattern(256 * 1024 + 73, 2)}
    elif shape == "cross_chunk":
        payloads = {"data.bin": _pattern(CHUNK_BYTES + AUTH_LEAF_BYTES * 3 + 137, 3)}
    elif shape == "multi_medium":
        payloads = {
            "a.bin": _pattern(192 * 1024 + 11, 4),
            "b.bin": _pattern(224 * 1024 + 29, 5),
            "c.bin": _pattern(320 * 1024 + 47, 6),
        }
    elif shape == "mixed":
        (root / "nested").mkdir()
        payloads = {
            "empty.bin": b"",
            "tiny.bin": b"ONE-fused-auth",
            "nested/medium.bin": _pattern(257 * 1024 + 31, 7),
            "large.bin": _pattern(CHUNK_BYTES + AUTH_LEAF_BYTES * 2 + 97, 8),
        }
    else:  # pragma: no cover - test helper guard
        raise AssertionError(shape)

    for rel, data in payloads.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    if shape == "mixed":
        try:
            os.symlink("../tiny.bin", root / "nested" / "link-to-tiny")
        except (OSError, NotImplementedError):
            pass
    return payloads


@pytest.mark.parametrize("shape", ["32k", "256k", "cross_chunk", "multi_medium", "mixed"])
def test_fused_builder_is_wire_identical_and_removes_auth_reread(tmp_path: Path, shape: str) -> None:
    src = tmp_path / shape
    src.mkdir()
    payloads = _make_tree(src, shape)

    baseline_wire, baseline = build_authenticated_archive(src)
    fused_wire, fused = build_authenticated_archive_fused(src)

    logical = sum(len(data) for data in payloads.values())
    assert baseline.logical_file_bytes == fused.logical_file_bytes == logical
    assert baseline.source_reread_bytes == logical
    assert fused.source_reread_bytes == 0
    assert fused_wire == baseline_wire
    assert fused.wire_bytes == baseline.wire_bytes
    assert fused.base_manifest_bytes == baseline.base_manifest_bytes
    assert fused.authenticated_manifest_bytes == baseline.authenticated_manifest_bytes
    assert fused.auth_manifest_delta_bytes == baseline.auth_manifest_delta_bytes
    assert fused.raw_auth_index_bytes == baseline.raw_auth_index_bytes
    assert fused.per_file_auth == baseline.per_file_auth

    baseline_open = open_authenticated_archive(baseline_wire)
    fused_open = open_authenticated_archive(fused_wire)
    assert fused_open.list_paths() == baseline_open.list_paths()

    for rel, expected in payloads.items():
        assert fused_open.read_file(rel) == baseline_open.read_file(rel) == expected
        requests = [(0, 0)]
        if expected:
            requests.extend([
                (0, min(64, len(expected))),
                (max(0, len(expected) // 2 - 31), min(127, len(expected) - max(0, len(expected) // 2 - 31))),
                (max(0, len(expected) - min(257, len(expected))), min(257, len(expected))),
            ])
            if len(expected) > AUTH_LEAF_BYTES:
                requests.append((AUTH_LEAF_BYTES - 31, min(127, len(expected) - (AUTH_LEAF_BYTES - 31))))
            if len(expected) > CHUNK_BYTES:
                requests.append((CHUNK_BYTES - 31, min(127, len(expected) - (CHUNK_BYTES - 31))))

        for start, length in requests:
            base_data, base_stats = baseline_open.read_range(rel, start, length)
            fused_data, fused_stats = fused_open.read_range(rel, start, length)
            assert fused_data == base_data == expected[start:start + length]
            assert _selective_invariants(fused_stats) == _selective_invariants(base_stats)
