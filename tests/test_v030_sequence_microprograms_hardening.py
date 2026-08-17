from __future__ import annotations

import pytest

from experiments import entropygraph_v030_sequence_microprograms as LTM
from experiments import entropygraph_v030_sequence_microprograms_safe as SAFE  # noqa: F401


def _put(value: int) -> bytes:
    out = bytearray()
    LTM._put_varint(out, value)
    return bytes(out)


def test_fixed_lexical_width_bomb_is_rejected_before_render() -> None:
    model = bytes((LTM.INT_VARINT,)) + _put(LTM._zigzag(7))
    payload = bytearray((0,))  # fixed-width decimal mode
    payload += _put(0)  # prefix
    payload += _put(0)  # suffix
    payload += _put(SAFE.MAX_DECIMAL_DIGITS + 1)
    payload += _put(len(model))
    payload += model
    with pytest.raises(RuntimeError, match="fixed lexical width"):
        LTM._decode_lexint(bytes(payload), 1)


def test_fixed_lexical_mode_rejects_negative_and_width_overflow() -> None:
    negative = bytes((LTM.INT_VARINT,)) + _put(LTM._zigzag(-1))
    payload = bytes((0,)) + _put(0) + _put(0) + _put(4) + _put(len(negative)) + negative
    with pytest.raises(RuntimeError, match="negative value"):
        LTM._decode_lexint(payload, 1)

    too_wide = bytes((LTM.INT_VARINT,)) + _put(LTM._zigzag(12345))
    payload = bytes((0,)) + _put(0) + _put(0) + _put(4) + _put(len(too_wide)) + too_wide
    with pytest.raises(RuntimeError, match="exceeds declared width"):
        LTM._decode_lexint(payload, 1)


def test_decoded_integer_stream_must_stay_signed64() -> None:
    # FOR can syntactically combine SIGNED64_MAX with a positive residual. The hardened reader must reject
    # that result even though Python itself can represent the larger integer.
    payload = bytearray((LTM.INT_FOR,))
    payload += _put(LTM._zigzag(SAFE.SIGNED64_MAX))
    payload.append(1)
    payload.extend(LTM._pack_fixed([1], 1))
    with pytest.raises(RuntimeError, match="signed-64"):
        LTM._decode_int_model(bytes(payload), 1)


def test_nonzero_unused_fixed_pack_bits_are_noncanonical() -> None:
    # Three one-bit values use only the low three bits of the byte. High padding bits must stay zero.
    canonical = bytearray(LTM._pack_fixed([1, 0, 1], 1))
    assert canonical == bytearray((0b00000101,))
    canonical[0] |= 0b10000000
    with pytest.raises(RuntimeError, match="padding bits"):
        LTM._unpack_fixed(bytes(canonical), 3, 1)


def test_dictionary_decoder_rejects_duplicate_dictionary_entries() -> None:
    # dictionary_count=2, encoded dictionary contains b'a', b'a'; indices then reference entry zero.
    dictionary = LTM._encode_raw_sequence([b"a", b"a"])
    payload = bytearray()
    payload += _put(2)
    payload += _put(len(dictionary))
    payload += dictionary
    payload.append(1)
    payload.extend(LTM._pack_fixed([0, 0], 1))
    with pytest.raises(RuntimeError, match="dictionary duplicates"):
        LTM._decode_dictionary(bytes(payload), 2)


def test_writer_rejects_affine_parameters_outside_portable_signed64() -> None:
    values = [SAFE.SIGNED64_MIN, SAFE.SIGNED64_MAX, SAFE.SIGNED64_MIN, SAFE.SIGNED64_MAX]
    # Generic signed varints remain legal; a latent affine/sawtooth model with over-wide parameters must not.
    assert LTM._affine_model(values) is None
    assert LTM._sawtooth_model(values) is None


def test_hardening_contract_is_explicit() -> None:
    limits = SAFE.RESOURCE_LIMITS
    assert limits["signed_integer_bits"] == 64
    assert limits["max_decimal_digits"] == 20
    assert limits["canonical_fixed_pack_padding"] is True
    assert limits["canonical_dictionary_values"] is True
