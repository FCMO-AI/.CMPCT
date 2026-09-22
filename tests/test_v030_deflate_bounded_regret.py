from __future__ import annotations

import random
import zlib

from cmpct import codec


ORDER = (0, 1, 2, 6, 3, 4, 5, 7, 8, 9)


def _raw_deflate(raw: bytes, level: int) -> bytes:
    co = zlib.compressobj(level, zlib.DEFLATED, -15)
    return co.compress(raw) + co.flush()


def _observed_result(monkeypatch, raw: bytes, target: bytes):
    real = zlib.compressobj
    attempts: list[int] = []
    def observed(level, *args, **kwargs):
        attempts.append(level)
        return real(level, *args, **kwargs)
    monkeypatch.setattr(codec.zlib, "compressobj", observed)
    return codec.deflate_level_for(raw, target), attempts


def test_common_level_moves_ahead_of_expensive_middle_levels(monkeypatch):
    raw = (b"cmpct bounded regret " * 8192) + bytes(range(256)) * 16
    target = _raw_deflate(raw, 6)
    got, attempts = _observed_result(monkeypatch, raw, target)
    assert got == 6
    assert attempts == [0, 1, 2, 6]
    assert _raw_deflate(raw, got) == target


def test_level_zero_keeps_zero_regret(monkeypatch):
    raw = bytes(range(251)) * 4096
    target = _raw_deflate(raw, 0)
    got, attempts = _observed_result(monkeypatch, raw, target)
    assert got == 0
    assert attempts == [0]


def test_level_one_keeps_canonical_prefix_on_large_incompressible_data(monkeypatch):
    rng = random.Random(203)
    raw = bytes(rng.randrange(256) for _ in range(256 * 1024))
    target = _raw_deflate(raw, 1)
    got, attempts = _observed_result(monkeypatch, raw, target)
    assert got == 1
    assert attempts == [0, 1]
    assert _raw_deflate(raw, got) == target


def test_level_two_keeps_canonical_prefix_when_distinct(monkeypatch):
    rng = random.Random(204)
    raw = bytes(rng.randrange(256) for _ in range(256 * 1024))
    target = _raw_deflate(raw, 2)
    got, attempts = _observed_result(monkeypatch, raw, target)
    assert got == 2
    assert attempts == [0, 1, 2]
    assert _raw_deflate(raw, got) == target


def test_search_remains_exhaustive_for_all_zlib_level_outputs():
    raw = (bytes(range(251)) * 2048) + (b"0123456789abcdef" * 8192) + bytes(range(97)) * 257
    for source_level in range(10):
        target = _raw_deflate(raw, source_level)
        got = codec.deflate_level_for(raw, target)
        assert got is not None, source_level
        assert _raw_deflate(raw, got) == target


def test_cost_tier_order_is_complete_and_unique():
    assert len(ORDER) == 10
    assert set(ORDER) == set(range(10))
