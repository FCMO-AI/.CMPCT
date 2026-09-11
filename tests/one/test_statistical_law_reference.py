from __future__ import annotations

import hashlib
import random

import pytest

from experiments.one.statistical_law_reference import (
    MAX_BLOCK_BYTES,
    StatisticalLawError,
    decode_block,
    decode_verified_block,
    encode_block,
)


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
