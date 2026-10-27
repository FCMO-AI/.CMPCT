"""J24R04: independent short/long sparse lookup equality court (research-only).

One original O212 archive framer, no Builder policy and no hand-built fake Reader.
Covers short-vector boundary E=4/5 and held-out 2,3,8,16,37,129,4096.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random

import pytest

from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive


def _original_framer():
    source = Path(__file__).with_name("test_o212_sparse_admission.py")
    spec = importlib.util.spec_from_file_location("_j24r04_unmodified_o212", source)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("count", (1, 2, 3, 4, 5, 8, 16, 37, 129, 4096))
def test_bounded_direct_and_logarithmic_same_exact_logical_bytes(tmp_path, count):
    source = _original_framer()
    stride = 19
    physical = b"ABCD"
    extents = [[i * stride, 4, [0]] for i in range(count)]
    logical = (physical + b"\x00" * (stride - 4)) * (count - 1) + physical
    wire = source._archive_bytes(extents, logical)
    path = tmp_path / f"j24r04-{count}.cmpct"
    path.write_bytes(wire)
    sha = hashlib.sha256(wire).hexdigest()
    assert preflight_archive(path, verify_blob_headers=True)["files"] == 1
    with CMPCT(path) as reader:
        assert reader.verify() == 1
        starts = {0, 1, 3, 4, stride - 1, stride, len(logical) - 1, len(logical)}
        starts.update((count // 2) * stride + v for v in (-1, 0, 3, 4, 5))
        rng = random.Random(0x24C04 + count)
        starts.update(rng.randrange(0, len(logical) + 1) for _ in range(97))
        for start in sorted(p for p in starts if 0 <= p <= len(logical)):
            lengths = {0, 1, 2, 4, 7, 19, 20, 38, len(logical) - start}
            for length in lengths:
                if 0 <= length <= len(logical) - start:
                    assert reader.read_range(source.PATH, start, length) == logical[start:start + length]
        with pytest.raises(ValueError):
            reader.read_range(source.PATH, len(logical), 1)
        with pytest.raises(ValueError):
            reader.read_range(source.PATH, -1, 1)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha


def test_legacy_strict_sparse_geometry_rejects_under_short_vector(tmp_path):
    source = _original_framer()
    bad_cases = (
        [[0, 4, [0]], [2, 4, [0]]],
        [[8, 4, [0]], [0, 4, [0]]],
        [[0, 0, [0]]],
        [[0, 4, [999]]],
        [[0, 4, []]],
    )
    for i, extents in enumerate(bad_cases):
        wire = source._archive_bytes(extents, b"ABCD" + b"\x00" * 16)
        path = tmp_path / f"invalid-{i}.cmpct"
        path.write_bytes(wire)
        with pytest.raises(ValidationError):
            CMPCT(path)
        assert path.read_bytes() == wire
