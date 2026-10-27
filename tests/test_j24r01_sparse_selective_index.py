"""J24R01: source-exact sparse selective-range lookup, genuine builder-independent r24.

This court borrows ONLY the unchanged O212 independently framed archive maker and
compares a complete logical byte oracle against the installed Reader.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive


def _o212():
    source = Path(__file__).with_name("test_o212_sparse_admission.py")
    spec = importlib.util.spec_from_file_location("_j24r01_o212_original", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("count,stride", [(1, 4), (2, 16), (4, 17), (37, 19), (129, 32)])
def test_all_ranges_bounded_genuine_r24(tmp_path, count, stride):
    base = _o212()
    extents = [[i * stride, 4, [0]] for i in range(count)]
    logical = bytearray((count - 1) * stride + 4)
    for i in range(count):
        logical[i * stride:i * stride + 4] = b"ABCD"
    wire = base._archive_bytes(extents, bytes(logical))
    location = tmp_path / "ranges.cmpct"
    location.write_bytes(wire)
    expected_wire_sha = hashlib.sha256(wire).digest()
    assert preflight_archive(location, verify_blob_headers=True)["files"] == 1
    with CMPCT(location) as reader:
        assert reader.verify() == 1
        for start in range(len(logical) + 1):
            for length in (0, 1, 2, 3, 4, 7, 19, 32, len(logical) - start):
                if length > len(logical) - start:
                    continue
                result = reader.read_range(base.PATH, start, length)
                assert result == bytes(logical[start:start + length]), (
                    count, stride, start, length, result
                )
        with pytest.raises(ValueError):
            reader.read_range(base.PATH, len(logical), 1)
    assert hashlib.sha256(location.read_bytes()).digest() == expected_wire_sha


@pytest.mark.parametrize("count", [4096, 65536])
def test_late_extent_many_small_holes_without_large_index(tmp_path, count):
    base = _o212()
    stride = 16
    extents = [[i * stride, 4, [0]] for i in range(count)]
    logical = (b"ABCD" + b"\0" * (stride - 4)) * (count - 1) + b"ABCD"
    wire = base._archive_bytes(extents, logical)
    location = tmp_path / "many-sparse.cmpct"
    location.write_bytes(wire)
    assert preflight_archive(location, verify_blob_headers=True)["files"] == 1
    with CMPCT(location) as reader:
        positions = (0, 3, 4, stride // 2, stride * (count//2),
                     stride * (count - 1) - 1, stride * (count - 1), len(logical) - 1)
        for pos in positions:
            for length in (0, 1, min(23, len(logical) - pos)):
                assert reader.read_range(base.PATH, pos, length) == logical[pos:pos+length]
        assert reader.read_range(base.PATH, len(logical), 0) == b""
        assert reader.verify() == 1
    assert hashlib.sha256(location.read_bytes()).digest() == hashlib.sha256(wire).digest()


def test_malformed_sparse_geometry_still_fails_early(tmp_path):
    base = _o212()
    cases = [
        [[8, 4, [0]], [0, 4, [0]]],
        [[0, 4, [0]], [2, 4, [0]]],
        [[0, 0, [0]]],
        [[0, 4, []]],
        [[0, 4, [999]]],
    ]
    for i, extents in enumerate(cases):
        wire = base._archive_bytes(extents, b"ABCD" + b"\0" * 12)
        path = tmp_path / f"invalid-{i}.cmpct"
        path.write_bytes(wire)
        with pytest.raises(ValidationError):
            CMPCT(path)
        assert path.read_bytes() == wire
