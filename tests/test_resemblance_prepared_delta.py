from __future__ import annotations

import random

import pytest

from cmpct.resemblance import (
    delta_decode,
    delta_encode,
    delta_encode_prepared,
    prepare_delta_base,
)


def _mutate(rng: random.Random, base: bytes, case: int) -> bytes:
    target = bytearray(base)
    if target and case % 2 == 0:
        pos = rng.randrange(len(target))
        span = min(rng.randrange(1, 33), len(target) - pos)
        target[pos:pos + span] = rng.randbytes(span)
    if case % 5 == 0:
        pos = rng.randrange(len(target) + 1)
        target[pos:pos] = rng.randbytes(rng.randrange(0, 33))
    if target and case % 7 == 0:
        pos = rng.randrange(len(target))
        del target[pos:pos + min(rng.randrange(0, 33), len(target) - pos)]
    return bytes(target)


def test_prepared_delta_matches_historical_randomized() -> None:
    rng = random.Random(0xD371A)
    for case in range(250):
        size = rng.randrange(0, 4097)
        base = bytearray(rng.randbytes(size))
        if size >= 256 and case % 3 == 0:
            repeated = b"ABCD" * 16
            for offset in range(0, size - len(repeated) + 1, 256):
                base[offset:offset + len(repeated)] = repeated
        base_bytes = bytes(base)
        target = _mutate(rng, base_bytes, case)

        historical = delta_encode(base_bytes, target)
        prepared = delta_encode_prepared(prepare_delta_base(base_bytes), target)

        assert prepared == historical
        assert delta_decode(base_bytes, prepared.payload, expected_size=len(target)) == target


def test_prepared_delta_preserves_first_offset_tie_rule() -> None:
    # Two identical 64-byte anchors deliberately collide on the same weak key.
    base = (b"A" * 64) + (b"B" * 64) + (b"A" * 64)
    target = b"A" * 64

    historical = delta_encode(base, target)
    prepared = delta_encode_prepared(prepare_delta_base(base), target)

    assert prepared == historical
    assert delta_decode(base, prepared.payload, expected_size=len(target)) == target


@pytest.mark.parametrize("block", [0, 1, 15])
def test_prepare_delta_base_preserves_block_bound(block: int) -> None:
    with pytest.raises(ValueError, match="block size too small"):
        prepare_delta_base(b"x" * 1024, block=block)


def test_prepare_delta_base_preserves_index_size_bound() -> None:
    with pytest.raises(ValueError, match="base exceeds delta index limit"):
        prepare_delta_base(b"x" * 4097, max_base_index=4096)
