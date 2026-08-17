from __future__ import annotations

import hashlib

import pytest

from experiments import entropygraph_v030_bitplane_algebra as BPA


def test_bitshuffle_has_hand_derived_uint16_vector() -> None:
    # Eight little-endian uint16 values 0..7 have low three bit planes 0xAA, 0xCC, 0xF0 and every
    # higher plane zero.  This expected vector is derived independently of the inverse implementation.
    raw = b"".join(value.to_bytes(2, "little") for value in range(8))
    expected = bytes((0xAA, 0xCC, 0xF0)) + bytes(13)
    assert BPA._bitshuffle_body(raw, 2) == expected
    assert BPA._bitunshuffle_body(expected, 2) == raw


def test_xor_shift_basis_is_exact_for_all_declared_options() -> None:
    seeds = (0, 1, 2, 3, 0x55AA, 0xA55A, 0xFFFF, 0x1234)
    for bits in (16, 32, 64):
        mask = (1 << bits) - 1
        values = [value & mask for value in seeds] + [int.from_bytes(hashlib.sha256(str(bits).encode()).digest()[: bits // 8], "little")]
        for direction, shift in BPA._basis_options(bits):
            for value in values:
                encoded = BPA._xor_shift_forward(value, bits, direction, shift)
                assert BPA._xor_shift_inverse(encoded, bits, direction, shift) == value


def test_predictors_round_trip_word_sequences() -> None:
    words = [0x1234, 0x1235, 0x1201, 0xFFFF, 0x0001, 0x0101, 0x0101, 0xABCD]
    raw = b"".join(value.to_bytes(2, "little") for value in words)
    for predictor in BPA.PREDICTORS:
        encoded = BPA._predict_forward(raw, 2, predictor)
        assert BPA._predict_inverse(encoded, 2, predictor) == raw


def test_full_bpa_transform_round_trips_prefix_body_and_tail() -> None:
    body = b"".join(((index * 257) & 0xFFFF).to_bytes(2, "little") for index in range(80))
    raw = b"X" + body + b"TAIL!"
    for predictor in BPA.PREDICTORS:
        for basis in (("none", 0), ("right", 1), ("left", 4)):
            encoded = BPA.forward(raw, 2, 1, predictor, basis)
            assert len(encoded) == len(raw) + 8
            assert BPA.inverse(encoded, len(raw)) == raw


def test_alignment_sketch_finds_hidden_uint16_boundary() -> None:
    # Alignment 1 yields a low-entropy high byte and an intentionally varied low byte. Alignment 0 mixes
    # neighboring word bytes together, raising the summed lane entropy.  No filename/type signal exists.
    words = b"".join(bytes(((index * 73) & 0xFF, 0x2A)) for index in range(20000))
    raw = b"!" + words
    ranked = BPA.rank_alignments(raw, 2)
    assert ranked[0] == 1


def test_forward_rejects_nodes_above_inherited_ceiling() -> None:
    raw = bytes(BPA.MAX_NODE_BYTES + 1)
    with pytest.raises(ValueError, match="ceiling"):
        BPA.forward(raw, 2, 0, "identity", ("none", 0))


def test_inverse_rejects_invalid_basis_descriptor() -> None:
    raw = b"".join(value.to_bytes(2, "little") for value in range(64))
    encoded = bytearray(BPA.forward(raw, 2, 0, "identity", ("none", 0)))
    encoded[7] = 0x86  # left-shift 32 is invalid for a 16-bit word.
    with pytest.raises(RuntimeError, match="basis"):
        BPA.inverse(bytes(encoded), len(raw))


def test_resource_contract_keeps_exact_search_bounded() -> None:
    assert BPA.RESOURCE_LIMITS["max_node_bytes"] == 512 * 1024
    assert BPA.RESOURCE_LIMITS["max_alignments_per_width"] <= 2
    assert BPA.RESOURCE_LIMITS["max_exact_finalists"] <= 4
    assert BPA.RESOURCE_LIMITS["screen_sample_bytes"] <= 64 * 1024
