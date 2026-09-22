from __future__ import annotations

import zlib

from cmpct import codec


ORDER = (6, 0, 1, 2, 3, 4, 5, 7, 8, 9)


def _raw_deflate(raw: bytes, level: int) -> bytes:
    co = zlib.compressobj(level, zlib.DEFLATED, -15)
    return co.compress(raw) + co.flush()


def test_common_level_is_one_attempt_and_exact(monkeypatch):
    raw = (b"cmpct bounded regret " * 8192) + bytes(range(256)) * 16
    target = _raw_deflate(raw, 6)
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


def test_rare_level_has_bounded_regret_and_remains_exact(monkeypatch):
    raw = bytes(range(251)) * 4096
    target = _raw_deflate(raw, 0)
    real = zlib.compressobj
    attempts: list[int] = []

    def observed(level, *args, **kwargs):
        attempts.append(level)
        return real(level, *args, **kwargs)

    monkeypatch.setattr(codec.zlib, "compressobj", observed)
    got = codec.deflate_level_for(raw, target)
    assert got == 0
    assert attempts == [6, 0]
    assert _raw_deflate(raw, got) == target


def test_search_order_is_complete_and_unique():
    assert len(ORDER) == 10
    assert set(ORDER) == set(range(10))
