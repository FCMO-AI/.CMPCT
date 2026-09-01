from __future__ import annotations

import hashlib
import random

import pytest

from experiments import entropygraph_v030_bounded_drift_v1 as BD


def _mutate(seed: bytes, *, offset: int, delete_n: int, insert: bytes) -> bytes:
    return seed[:offset] + insert + seed[offset + delete_n:]


def test_base_selection_is_content_only_and_order_invariant() -> None:
    members = [b"b" * 9000, b"a" * 9000, b"c" * 9000]
    expected = min(members, key=lambda x: (hashlib.sha256(x).digest(), x))
    assert BD.select_base(members) == expected
    assert BD.select_base(list(reversed(members))) == expected


def test_round_trip_replacements_insertions_deletions_and_tail_changes() -> None:
    seed = (b"0123456789abcdef" * 8192)[:120000]
    members = [
        seed,
        _mutate(seed, offset=1200, delete_n=7, insert=b"REPLACED"),
        _mutate(seed, offset=50000, delete_n=0, insert=b"INSERTION" * 5),
        _mutate(seed, offset=90000, delete_n=113, insert=b""),
        seed[:-37] + b"tail-change",
    ]
    base, programs = BD.encode_family(members)
    assert [BD.decode_program(base, p) for p in programs] == members
    assert all(p.records > 0 for p in programs)


def test_random_bounded_drift_round_trips_without_path_or_fixture_identity() -> None:
    rng = random.Random(0xC030)
    seed = bytes(rng.randrange(256) for _ in range(64000))
    members = [seed]
    for _ in range(12):
        value = bytearray(seed)
        for _ in range(8):
            pos = rng.randrange(1000, len(value) - 1000)
            n = rng.randrange(1, 80)
            value[pos:pos+n] = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 100)))
        members.append(bytes(value))
    base, programs = BD.encode_family(members)
    rebuilt = [BD.decode_program(base, p) for p in programs]
    assert rebuilt == members
    assert sum(p.copied_bytes for p in programs) > sum(len(x) for x in members) // 2


def test_corruption_fails_closed() -> None:
    base = b"abc123" * 10000
    target = base[:12345] + b"X" * 40 + base[12360:]
    program = BD.encode_program(base, target)
    raw = bytearray(program.raw)
    raw[-1] ^= 1
    corrupt = BD.EditProgram(bytes(raw), program.logical_size, program.sha256, program.records, program.copied_bytes, program.deleted_bytes, program.inserted_bytes)
    with pytest.raises(ValueError):
        BD.decode_program(base, corrupt)


def test_resource_and_malformed_inputs_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(BD, "MAX_DECODE_UNIT", 1024)
    with pytest.raises(ValueError):
        BD.encode_program(b"x" * 1025, b"x" * 1025)
    with pytest.raises(ValueError):
        BD.decode_program(
            b"abc",
            BD.EditProgram(b"\x01\x04\x00\x00", 4, hashlib.sha256(b"abcd").digest(), 1, 0, 0, 0),
        )
