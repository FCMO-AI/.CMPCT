from __future__ import annotations

import random

from experiments import entropygraph_v030_bounded_drift_v1 as BD


def _historical_find_resync(base: bytes, target: bytes, i: int, j: int) -> tuple[int, int]:
    rem_b, rem_t = len(base) - i, len(target) - j
    for k in range(1, min(BD.MAX_RESYNC_BYTES, rem_b, rem_t) + 1):
        if min(rem_b - k, rem_t - k) < BD.SYNC_BYTES:
            break
        if base[i + k : i + k + BD.SYNC_BYTES] == target[j + k : j + k + BD.SYNC_BYTES]:
            return k, k

    candidates: list[tuple[int, int]] = []
    if rem_b >= BD.SYNC_BYTES:
        token = base[i : i + BD.SYNC_BYTES]
        p = target.find(token, j + 1, min(len(target), j + BD.MAX_RESYNC_BYTES + BD.SYNC_BYTES))
        if p >= 0:
            candidates.append((0, p - j))
    if rem_t >= BD.SYNC_BYTES:
        token = target[j : j + BD.SYNC_BYTES]
        p = base.find(token, i + 1, min(len(base), i + BD.MAX_RESYNC_BYTES + BD.SYNC_BYTES))
        if p >= 0:
            candidates.append((p - i, 0))
    if candidates:
        return min(candidates, key=lambda x: (x[0] + x[1], max(x), x))
    step = min(256, rem_b, rem_t)
    return (step, step) if step else (rem_b, rem_t)


def _diagonal_case(k: int, *, seed: int) -> tuple[bytes, bytes]:
    rng = random.Random(seed)
    n = BD.MAX_RESYNC_BYTES + BD.SYNC_BYTES + 64
    # Make every pre-k diagonal byte provably unequal. Independent random
    # prefixes can accidentally create an earlier SYNC_BYTES window when the
    # injected token overlaps it (for k=48, k-1 needs only one random byte to
    # collide), which tests the fixture rather than the resync algorithm.
    base = bytearray(b"\x00" * n)
    target = bytearray(b"\x01" * n)
    token = rng.randbytes(BD.SYNC_BYTES)
    base[k : k + BD.SYNC_BYTES] = token
    target[k : k + BD.SYNC_BYTES] = token
    return bytes(base), bytes(target)


def test_hybrid_resync_matches_historical_boundaries_and_no_match() -> None:
    for k in (1, 2, 47, 48, 49, 255, 256, 1023, 1024):
        base, target = _diagonal_case(k, seed=0xBD00 + k)
        assert _historical_find_resync(base, target, 0, 0) == (k, k)
        assert BD._find_resync(base, target, 0, 0) == (k, k)

    rng = random.Random(0xBD0F)
    base = rng.randbytes(BD.MAX_RESYNC_BYTES + BD.SYNC_BYTES + 64)
    target = rng.randbytes(len(base))
    assert BD._find_resync(base, target, 0, 0) == _historical_find_resync(base, target, 0, 0)


def test_hybrid_resync_matches_historical_randomized_domain() -> None:
    rng = random.Random(0xBD15)
    for _ in range(1000):
        n = rng.randrange(0, 2200)
        m = rng.randrange(0, 2200)
        base = rng.randbytes(n)
        target = rng.randbytes(m)
        i = rng.randrange(n + 1)
        j = rng.randrange(m + 1)
        assert BD._find_resync(base, target, i, j) == _historical_find_resync(base, target, i, j)


def test_hybrid_encode_program_is_byte_identical_to_historical_reference(monkeypatch) -> None:
    rng = random.Random(0xBD16)
    candidate_find = BD._find_resync

    for _ in range(200):
        seed = rng.randbytes(rng.randrange(512, 4096))
        target = bytearray(seed)
        for _ in range(rng.randrange(1, 7)):
            if not target:
                target.extend(rng.randbytes(rng.randrange(1, 64)))
                continue
            pos = rng.randrange(len(target))
            delete_n = rng.randrange(0, min(64, len(target) - pos) + 1)
            insert = rng.randbytes(rng.randrange(0, 64))
            target[pos : pos + delete_n] = insert
        target_b = bytes(target)

        monkeypatch.setattr(BD, "_find_resync", _historical_find_resync)
        expected = BD.encode_program(seed, target_b)
        monkeypatch.setattr(BD, "_find_resync", candidate_find)
        actual = BD.encode_program(seed, target_b)

        assert actual == expected
        assert BD.decode_program(seed, actual) == target_b
