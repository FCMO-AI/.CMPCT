from __future__ import annotations

import pytest

from experiments import entropygraph_v030_sequence_microprograms as LTM
from experiments import entropygraph_v030_sequence_microprograms_safe as SAFE  # noqa: F401


def _varint(value: int) -> bytes:
    out = bytearray()
    LTM._put_varint(out, value)
    return bytes(out)


def test_fixed_bitpack_round_trips_declared_widths() -> None:
    for width in (0, 1, 2, 5, 8, 13, 32, 64):
        if width == 0:
            values = [0] * 17
        else:
            mask = (1 << width) - 1
            values = [((index * 0x9E3779B1) ^ (index << 3)) & mask for index in range(17)]
        packed = LTM._pack_fixed(values, width)
        assert LTM._unpack_fixed(packed, len(values), width) == values


def test_affine_microprogram_beats_generic_integer_stream_and_round_trips() -> None:
    values = [17 + 13 * index for index in range(4096)]
    model = LTM._encode_int_model(values)
    assert model[0] == LTM.INT_AFFINE
    assert LTM._decode_int_model(model, len(values)) == values


def test_residualized_affine_preserves_sparse_realistic_anomalies() -> None:
    values = [1000 + 7 * index for index in range(2048)]
    # Three anomalies are well below the <=1/16 residual budget and are deliberately non-periodic.
    for index, delta in ((37, 901), (811, -233), (1703, 77)):
        values[index] += delta
    model = LTM._encode_int_model(values)
    assert model[0] == LTM.INT_AFFINE
    assert LTM._decode_int_model(model, len(values)) == values
    # The model must remain dramatically smaller than spelling every integer as an independent varint.
    generic = LTM._pack_model_values(values, LTM.INT_VARINT)
    assert generic is not None
    assert len(model) * 8 < len(generic)


def test_sawtooth_microprogram_matches_public_latency_shape() -> None:
    values = [8 + (index * 13) % 820 for index in range(6000)]
    model = LTM._encode_int_model(values)
    assert model[0] == LTM.INT_SAWTOOTH
    assert LTM._decode_int_model(model, len(values)) == values


def test_residualized_sawtooth_keeps_sparse_exceptions_exact() -> None:
    values = [8 + (index * 13) % 820 for index in range(4096)]
    values[333] = 777
    values[1444] = 12
    values[3001] = 456
    model = LTM._encode_int_model(values)
    assert model[0] == LTM.INT_SAWTOOTH
    assert LTM._decode_int_model(model, len(values)) == values


def test_zero_padded_lexical_integer_renderer_is_byte_exact() -> None:
    values = [f"tenant=T{index % 380:04d}".encode() for index in range(1520)]
    payload = LTM._encode_lexint(values)
    assert payload is not None
    assert LTM._decode_lexint(payload, len(values)) == values


def test_signed_canonical_lexical_integer_renderer_is_byte_exact() -> None:
    values = [f"offset={index - 500}".encode() for index in range(1000)]
    payload = LTM._encode_lexint(values)
    assert payload is not None
    assert LTM._decode_lexint(payload, len(values)) == values


def test_dictionary_codelet_round_trips_low_cardinality_sequence() -> None:
    dictionary = [b"INFO", b"WARN", b"DEBUG", b"TRACE"]
    values = [dictionary[(index * 7) % len(dictionary)] for index in range(5000)]
    payload = LTM._encode_dictionary(values)
    assert payload is not None
    assert LTM._decode_dictionary(payload, len(values)) == values


def test_restricted_alphabet_codelet_round_trips_hex_identifiers() -> None:
    values = [f"{(index * 2654435761) & ((1 << 48) - 1):012x}".encode() for index in range(3000)]
    payload = LTM._encode_alphabet(values)
    assert payload is not None
    assert LTM._decode_alphabet(payload, len(values)) == values


def test_period_codelet_round_trips_nonsemantic_byte_cycle() -> None:
    seed = [b"\x00A", b"\xffB", b"\x7fC", b"\x01D", b"\x80E"]
    values = [seed[index % len(seed)] for index in range(2000)]
    payload = LTM._encode_period(values)
    assert payload is not None
    assert LTM._decode_period(payload, len(values)) == values


def test_full_ltm_transform_round_trips_schema_blind_rows() -> None:
    rows = []
    for index in range(4096):
        rows.append(
            f"2026-07-01T00:{(index // 60) % 60:02d}:{index % 60:02d}+00:00 "
            f"INFO worker={index % 32:02d} tenant=T{index % 380:04d} "
            f"route={('/api/jobs','/api/files','/api/search','/health')[index % 4]} "
            f"latency_ms={8 + (index * 13) % 820} request={(index * 0x9e3779b1) & ((1 << 48) - 1):012x}"
        )
    raw = ("\n".join(rows) + "\n").encode()
    transformed, stats = LTM.build_transform(raw, ord("\n"), ord(" "))
    assert stats["rows"] == len(rows) + 1
    assert sum(stats["codelet_counts"].values()) == stats["max_fields"]
    assert LTM.inverse(transformed, len(raw)) == raw


def test_lexint_rejects_arbitrary_precision_decimal_before_python_bigint_work() -> None:
    huge = b"9" * (SAFE.MAX_DECIMAL_DIGITS + 1000)
    values = [b"x=" + huge for _ in range(8)]
    assert LTM._encode_lexint(values) is None


def test_safe_decoder_rejects_exception_fraction_above_writer_policy() -> None:
    # count=16 => <=1 exception allowed.  Two authenticated exceptions must fail closed rather than creating
    # a broader reader grammar than the writer is allowed to emit.
    payload = bytearray((LTM.INT_AFFINE,))
    LTM._put_varint(payload, LTM._zigzag(0))
    LTM._put_varint(payload, LTM._zigzag(1))
    payload.extend(LTM._encode_exceptions([(1, 99), (7, 88)]))
    with pytest.raises(RuntimeError, match="exception fraction"):
        LTM._decode_int_model(bytes(payload), 16)


def test_safe_dictionary_decoder_rejects_noncanonical_bit_width() -> None:
    values = [b"a", b"b"] * 8
    payload = bytearray(LTM._encode_dictionary(values) or b"")
    assert payload
    count, pos = LTM._get_varint(payload, 0)
    assert count == 2
    dictionary_bytes, pos = LTM._get_varint(payload, pos)
    width_pos = pos + dictionary_bytes
    assert payload[width_pos] == 1
    payload[width_pos] = 2
    with pytest.raises(RuntimeError, match="dictionary bit width"):
        LTM._decode_dictionary(bytes(payload), len(values))


def test_safe_alphabet_decoder_rejects_noncanonical_symbol_table() -> None:
    values = [b"abc123"] * 20
    payload = bytearray(LTM._encode_alphabet(values) or b"")
    assert payload
    alphabet_count, pos = LTM._get_varint(payload, 0)
    assert alphabet_count >= 2
    payload[pos], payload[pos + 1] = payload[pos + 1], payload[pos]
    with pytest.raises(RuntimeError, match="alphabet"):
        LTM._decode_alphabet(bytes(payload), len(values))


def test_resource_contract_is_smaller_than_inherited_decode_envelope() -> None:
    limits = SAFE.RESOURCE_LIMITS
    assert limits["max_node_bytes"] == 512 * 1024
    assert limits["max_columns"] <= 64
    assert limits["max_dictionary_values"] <= 512
    assert limits["max_period"] <= 4096
    assert limits["max_exceptions"] <= 2048
    assert limits["signed_integer_bits"] == 64
    assert limits["max_decimal_digits"] <= 20
