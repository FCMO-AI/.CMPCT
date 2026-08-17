from __future__ import annotations

import pytest

from experiments import entropygraph_v030_hierarchical_geometry as H


def _varint(value: int) -> bytes:
    out = bytearray()
    H._put_varint(out, value)
    return bytes(out)


def test_plain_hierarchy_has_hand_derived_golden_vector() -> None:
    raw = b"aa=11\nbb=22"
    encoded = H.hierarchy_forward(raw, ord("\n"), ord("="), prefix_planes=False)
    # Footnote: this vector is written independently of the decoder.  It pins separator bytes, row/field
    # counts, field lengths and the field-major body, so a matching writer/reader bug cannot redefine HGT2.
    assert encoded == b"HGT2\n=\x02\x02\x02\x02\x02\x02\x02aabb1122"
    assert H.hierarchy_inverse(encoded, len(raw)) == raw


def test_prefix_planes_have_hand_derived_golden_vector() -> None:
    raw = b"aa=11\naa=12"
    encoded = H.hierarchy_forward(raw, ord("\n"), ord("="), prefix_planes=True)
    # Column 0 prefixes are [0, 2]; column 1 prefixes are [0, 1].  The suffix body is therefore aa|11|2.
    assert encoded == b"HGP2\n=\x02\x02\x02\x02\x02\x02\x02\x00\x02\x00\x01aa112"
    assert H.hierarchy_inverse(encoded, len(raw)) == raw


def test_empty_fields_and_trailing_primary_separator_round_trip() -> None:
    raw = b"a==b\n=c=\n"
    for prefix in (False, True):
        encoded = H.hierarchy_forward(raw, ord("\n"), ord("="), prefix_planes=prefix)
        assert H.hierarchy_inverse(encoded, len(raw)) == raw


def test_binary_separators_do_not_require_text_semantics() -> None:
    raw = b"A\x00B\xffA\x00C\xffA\x00D"
    for prefix in (False, True):
        encoded = H.hierarchy_forward(raw, 0xFF, 0x00, prefix_planes=prefix)
        assert H.hierarchy_inverse(encoded, len(raw)) == raw


def test_writer_rejects_rectangular_work_bomb_before_transpose() -> None:
    # One wide row plus many empty rows keeps the declared source tiny while making row_count*max_fields
    # exceed the 8x cell-work law.  This is the adversary that a simple total-byte bound would miss.
    raw = b"=" * 255 + b"\n" * 16_384
    assert len(raw) < H.G.MAX_CHUNK
    with pytest.raises(ValueError, match="cell-work budget"):
        H.hierarchy_forward(raw, ord("\n"), ord("="))


def test_reader_rejects_field_count_bomb_before_lengths() -> None:
    encoded = b"HGT2\n=" + _varint(1) + _varint(H.MAX_FIELDS_PER_ROW + 1)
    with pytest.raises(RuntimeError, match="field count out of bounds"):
        H.hierarchy_inverse(encoded, 0)


def test_content_driven_nomination_finds_structural_separators() -> None:
    rows = []
    for index in range(2_000):
        rows.append(
            f"2026-07-01T00:{index % 60:02d}:00+00:00 INFO worker={index % 32:02d} "
            f"tenant=T{index % 380:04d} route=/api/jobs latency_ms={8 + index % 820} request={index:012x}."
        )
    raw = ("\n".join(rows) + "\n").encode()
    primaries = H.primary_candidates(raw)
    assert ord("\n") in primaries or ord(".") in primaries
    nominated = set()
    for primary in primaries:
        nominated.update(H.secondary_candidates(raw.split(bytes((primary,))), primary))
    assert ord("=") in nominated


def test_audition_is_exact_fallback_and_finds_large_structured_win() -> None:
    rows = []
    for index in range(3_000):
        rows.append(
            f"step={index} account=A{index % 19000:05d} region={['n','s','e','w'][index % 4]} "
            f"product=P{(index * 7) % 1200:04d} qty={1 + index % 13} value={2.75 + (index % 191) * .91:.2f}"
        )
    raw = ("\n".join(rows) + "\n").encode()
    chosen = H.audition(raw)
    assert chosen["payload_bytes"] <= len(H.G._compress_physical(raw)[1])
    assert chosen["kind"] == "hierarchical"
    assert chosen["saving_bytes"] >= 4_096
    assert chosen["exact_finalists"] <= H.MAX_EXACT_FINALISTS
    assert H.hierarchy_inverse(chosen["physical"], len(raw)) == raw
