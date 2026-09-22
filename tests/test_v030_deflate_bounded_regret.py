from __future__ import annotations

import random
import zlib

from cmpct import codec


COMMON_FIRST = (6, 0, 1, 2, 3, 4, 5, 7, 8, 9)


def _raw_deflate(raw: bytes, level: int) -> bytes:
    co = zlib.compressobj(level, zlib.DEFLATED, -15)
    return co.compress(raw) + co.flush()


def _first_block_type(target: bytes) -> int:
    assert target
    return (target[0] >> 1) & 0b11


def test_compressed_block_tries_common_level_first_and_is_exact(monkeypatch):
    raw = (b"cmpct bounded regret " * 8192) + bytes(range(256)) * 16
    target = _raw_deflate(raw, 6)
    assert _first_block_type(target) != 0
    real = zlib.compressobj
    attempts: list[int] = []

    def observed(level, *args, **kwargs):
        attempts.append(level)
        return real(level, *args, **kwargs)

    monkeypatch.setattr(codec.zlib, "compressobj", observed)
    got = codec.deflate_level_for(raw, target)
    assert got == 6
    assert attempts == [6]
    assert _raw_deflate(raw, got) == target


def test_stored_block_level_zero_keeps_zero_regret_and_exactness(monkeypatch):
    raw = bytes(range(251)) * 4096
    target = _raw_deflate(raw, 0)
    assert _first_block_type(target) == 0
    real = zlib.compressobj
    attempts: list[int] = []

    def observed(level, *args, **kwargs):
        attempts.append(level)
        return real(level, *args, **kwargs)

    monkeypatch.setattr(codec.zlib, "compressobj", observed)
    got = codec.deflate_level_for(raw, target)
    assert got == 0
    assert attempts == [0]
    assert _raw_deflate(raw, got) == target


def test_stored_block_incompressible_level_one_keeps_canonical_prefix(monkeypatch):
    rng = random.Random(203)
    raw = bytes(rng.randrange(256) for _ in range(256 * 1024))
    target = _raw_deflate(raw, 1)
    assert _first_block_type(target) == 0
    real = zlib.compressobj
    attempts: list[int] = []

    def observed(level, *args, **kwargs):
        attempts.append(level)
        return real(level, *args, **kwargs)

    monkeypatch.setattr(codec.zlib, "compressobj", observed)
    got = codec.deflate_level_for(raw, target)
    assert got == 1
    assert attempts == [0, 1]
    assert _raw_deflate(raw, got) == target


def test_search_remains_exhaustive_for_all_zlib_level_outputs():
    raw = (bytes(range(251)) * 2048) + (b"0123456789abcdef" * 8192) + bytes(range(97)) * 257
    for source_level in range(10):
        target = _raw_deflate(raw, source_level)
        got = codec.deflate_level_for(raw, target)
        assert got is not None, source_level
        assert _raw_deflate(raw, got) == target


def test_common_first_order_is_complete_and_unique():
    assert len(COMMON_FIRST) == 10
    assert set(COMMON_FIRST) == set(range(10))
