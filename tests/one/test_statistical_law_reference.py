from __future__ import annotations

import hashlib
import math
import random

import pytest

from experiments.one.statistical_law_reference import (
    MAX_BLOCK_BYTES,
    StatisticalLawError,
    decode_block,
    decode_verified_block,
    encode_block,
)


def _exact_kt_bits(source: bytes) -> float:
    if not source:
        return 0.0
    counts = [[0] * 256 for _ in range(256)]
    totals = [0] * 256
    bits = 8.0
    previous = source[0]
    for symbol in source[1:]:
        bits -= math.log2(
            (counts[previous][symbol] + 0.5) / (totals[previous] + 128.0)
        )
        counts[previous][symbol] += 1
        totals[previous] += 1
        previous = symbol
    return bits


@pytest.mark.parametrize(
    ("source", "expected_hex"),
    [
        (b"a", "61"),
        (b"aa", "616140"),
        (b"ab", "616240"),
        (b"abc", "61626340"),
        (bytes((0, 1, 0, 1, 0, 1)), "00010000fe10"),
        (b"banana bandana", "62616e616e4550a13970932868"),
        (bytes(range(16)), "000102030405060708090a0b0c0d0e0f40"),
    ],
)
def test_semantic_vectors(source: bytes, expected_hex: str) -> None:
    payload = encode_block(source)
    assert payload.hex() == expected_hex
    assert decode_block(payload, len(source)) == source
    assert encode_block(source) == payload


def test_deterministic_hostile_round_trips() -> None:
    rng = random.Random(0xC0A3_0003)
    vectors = [
        bytes((0,)) * 4096,
        bytes((0, 1)) * 2048,
        bytes(range(256)) * 16,
        b"Law+Surprise|" * 315,
        rng.randbytes(4096),
    ]
    for source in vectors:
        payload = encode_block(source)
        assert decode_block(payload, len(source)) == source
        assert encode_block(source) == payload


def test_real_bitstream_tracks_exact_kt_codelength() -> None:
    rng = random.Random(7)
    vectors = [
        bytes((0,)) * 4096,
        bytes((0, 1)) * 2048,
        b"Law+Surprise|" * 315,
        rng.randbytes(4096),
    ]
    for source in vectors:
        realized_bits = len(encode_block(source)) * 8
        ideal_bits = _exact_kt_bits(source)
        # Arithmetic finalization/byte padding is allowed, but the concrete
        # format must not silently turn a good probability model into a poor
        # bitstream before any container charges are considered.
        assert realized_bits >= ideal_bits - 1e-9
        assert realized_bits - ideal_bits <= 16.0


def test_exact_maximum_block_round_trip() -> None:
    source = bytes((0,)) * MAX_BLOCK_BYTES
    payload = encode_block(source)
    assert decode_block(payload, len(source)) == source
    # This is a semantic/resource vector, not a density gate.  It also catches
    # accidental state carry across the fixed 64 KiB restart contract.
    assert len(payload) == 168


def test_verified_envelope_rejects_length_and_corruption() -> None:
    source = b"bounded statistical law " * 80
    payload = encode_block(source)
    digest = hashlib.sha256(source).digest()
    assert (
        decode_verified_block(
            payload,
            len(source),
            digest,
            declared_payload_length=len(payload),
        )
        == source
    )

    with pytest.raises(StatisticalLawError, match="physical payload length"):
        decode_verified_block(
            payload[:-1],
            len(source),
            digest,
            declared_payload_length=len(payload),
        )

    damaged = bytearray(payload)
    damaged[max(1, len(damaged) // 2)] ^= 0x01
    with pytest.raises(StatisticalLawError, match="digest mismatch"):
        decode_verified_block(
            bytes(damaged),
            len(source),
            digest,
            declared_payload_length=len(damaged),
        )


def test_resource_bounds_fail_before_decode() -> None:
    for length in (0, MAX_BLOCK_BYTES + 1, 1 << 31):
        with pytest.raises(StatisticalLawError, match="block length"):
            decode_block(b"x", length)
    with pytest.raises(StatisticalLawError, match="block length"):
        encode_block(b"")
    with pytest.raises(StatisticalLawError, match="block length"):
        encode_block(bytes(MAX_BLOCK_BYTES + 1))
