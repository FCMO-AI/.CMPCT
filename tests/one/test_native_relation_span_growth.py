from __future__ import annotations

import random

from experiments.one.native_relation_span_growth import grow_relation_spans_native
from experiments.one.relation_span_growth import grow_relation_spans


def _apply(parent: bytes, op: str, value: int) -> bytes:
    return bytes(((b + value) & 0xFF) if op == "add8" else (b ^ value) for b in parent)


def _same(parent: bytes, child: bytes, op: str, value: int, nominations: tuple[int, ...], seed=64, ext=4096):
    py = grow_relation_spans(parent, child, op=op, value=value, nominations=nominations, seed_bytes=seed, extension_bytes=ext)
    native = grow_relation_spans_native(parent, child, op=op, value=value, nominations=nominations, seed_bytes=seed, extension_bytes=ext)
    assert native == py


def test_native_exact_full_and_cracks_match_oracle():
    for n in (64, 65, 4095, 4096, 4097, 65536):
        parent = bytes((i * 73 + 19) & 0xFF for i in range(n))
        for op, value in (("add8", 37), ("xor", 167)):
            child = bytearray(_apply(parent, op, value))
            nominations = tuple(range(0, max(0, n - 63), 64))
            _same(parent, bytes(child), op, value, nominations)
            if n > 64:
                for pos in {64, min(n - 1, 4095), min(n - 1, n // 2)}:
                    cracked = bytearray(child); cracked[pos] ^= 1
                    _same(parent, bytes(cracked), op, value, nominations)


def test_native_false_seed_frontier_matches_oracle():
    n = 8192
    parent = bytes((i * 17 + 3) & 0xFF for i in range(n))
    for op, value in (("add8", 11), ("xor", 91)):
        child = bytearray(_apply(parent, op, value))
        for pos in (0, 1, 15, 16, 63, 64, 4095, 4096, n - 1):
            hostile = bytearray(child); hostile[pos] ^= 1
            _same(parent, bytes(hostile), op, value, tuple(range(0, n - 63, 64)))


def test_native_nomination_normalization_matches_oracle():
    n = 16384
    parent = bytes((i * 29 + 5) & 0xFF for i in range(n))
    child = _apply(parent, "xor", 203)
    nominations = (4096, 0, 0, -64, 8192, 128, 4096, n + 64, 64)
    _same(parent, child, "xor", 203, nominations)


def test_native_random_cracks_match_oracle():
    rng = random.Random(0xC0DEC0DE)
    n = 32768
    parent = bytes(rng.randrange(256) for _ in range(n))
    for op, value in (("add8", 251), ("xor", 1)):
        child = bytearray(_apply(parent, op, value))
        for _ in range(37):
            child[rng.randrange(n)] ^= rng.randrange(1, 256)
        nominations = tuple(range(0, n - 63, 64))
        _same(parent, bytes(child), op, value, nominations)
