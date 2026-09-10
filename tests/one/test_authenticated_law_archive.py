from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.authenticated_archive_envelope import AUTH_LEAF_BYTES, open_authenticated_archive
from experiments.one.authenticated_law_archive import (
    CURRENT_PATH,
    PREVIOUS_PATH,
    build_authenticated_add8_pair_archive,
)
from experiments.one.ir import OneError


def _pair(n: int) -> tuple[bytes, bytes]:
    previous = bytes(((i * 71 + (i >> 4) * 13 + 19) & 255) for i in range(n))
    current = bytes(((b + 37) & 255) for b in previous)
    return previous, current


@pytest.mark.parametrize("n", [32 * 1024, 128 * 1024, 512 * 1024])
def test_authenticated_law_archive_roundtrip_and_selective_cones(n: int) -> None:
    previous, current = _pair(n)
    wire, stats = build_authenticated_add8_pair_archive(previous, current)
    opened = open_authenticated_archive(wire)

    assert opened.list_paths() == (CURRENT_PATH, PREVIOUS_PATH)
    assert opened.read_file(PREVIOUS_PATH) == previous
    assert opened.read_file(CURRENT_PATH) == current
    assert opened.program.roots["f000000"].sha256 == sha256(previous).hexdigest()
    assert opened.program.roots["f000001"].sha256 == sha256(current).hexdigest()
    assert opened.program.nodes[opened.program.roots["f000001"].ref.node].op == "add8"
    assert stats.control_integrity_bytes > 0
    assert stats.surprise_bytes < stats.logical_file_bytes

    requests = [
        (0, 0),
        (0, 64),
        (0, 4096),
        (n // 2, 4096),
        (AUTH_LEAF_BYTES - 31, 127),
        (n - 257, 257),
    ]
    for start, length in requests:
        data, sel = opened.read_range(CURRENT_PATH, start, length)
        assert data == current[start:start + length]
        assert sel.requested_bytes == length
        assert sel.cone_bytes <= AUTH_LEAF_BYTES * 2 if length <= AUTH_LEAF_BYTES else sel.cone_bytes <= length + AUTH_LEAF_BYTES * 2
        assert sel.cone_bytes <= n


def test_authenticated_law_archive_rejects_false_relation() -> None:
    previous, current = _pair(32 * 1024)
    bad = bytearray(current)
    bad[-1] ^= 1
    with pytest.raises(ValueError, match="does not satisfy"):
        build_authenticated_add8_pair_archive(previous, bytes(bad))


def test_authenticated_law_archive_detects_tamper() -> None:
    previous, current = _pair(32 * 1024)
    wire, _ = build_authenticated_add8_pair_archive(previous, current)
    damaged = bytearray(wire)
    damaged[-17] ^= 1
    with pytest.raises(OneError):
        open_authenticated_archive(bytes(damaged))
