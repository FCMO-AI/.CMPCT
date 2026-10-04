from __future__ import annotations

import struct

import pytest

from benchmarks import v030_shifted_joint_patch_stream_oracle as oracle


def test_patch_roundtrips_bounded_positive_and_negative_alignment() -> None:
    anchor = bytes(range(251)) * 80
    cases = []
    for shift in (-64, -17, -1, 0, 1, 23, 64):
        if shift < 0:
            target = anchor[-shift:] + b"tail"
        elif shift > 0:
            target = b"P" * shift + anchor
        else:
            target = anchor
        mutated = bytearray(target)
        if len(mutated) > 211:
            mutated[211] ^= 0x5A
        if len(mutated) > 4097:
            mutated[4097] ^= 0xA5
        cases.append(bytes(mutated))

    for target in cases:
        patch = oracle._patch(anchor, target)
        assert oracle._apply_patch(anchor, patch, len(target)) == target


def test_patch_parser_rejects_trailing_bytes() -> None:
    anchor = b"abcdefgh" * 1024
    target = b"XYZ" + anchor + b"tail"
    patch = oracle._patch(anchor, target)
    with pytest.raises(RuntimeError, match="truncated or trailing joint-edit suffix"):
        oracle._apply_patch(anchor, patch + b"x", len(target))


def test_patch_parser_rejects_anchor_range_escape() -> None:
    anchor = b"A" * 32
    # a_skip=31, empty prefix, overlap=2 -> one byte beyond the anchor.
    raw = struct.pack("<IIQI", 31, 0, 2, 0) + struct.pack("<I", 0)
    with pytest.raises(RuntimeError, match="anchor range outside anchor"):
        oracle._apply_patch(anchor, raw, 2)


def test_decode_transform_rejects_duplicate_patch_owner() -> None:
    rows_meta = [
        ("a.bin", 4, b"0" * 32),
        ("b.bin", 4, b"1" * 32),
        ("c.bin", 4, b"2" * 32),
    ]
    anchor = b"ABCD"
    patch = oracle._patch(anchor, b"ABCE")
    raw = bytearray(oracle.TRANSFORM_MAGIC)
    raw += struct.pack("<IQ", 0, len(anchor)) + anchor
    raw += struct.pack("<I", 2)
    raw += struct.pack("<IQ", 1, len(patch)) + patch
    raw += struct.pack("<IQ", 1, len(patch)) + patch
    with pytest.raises(RuntimeError, match="invalid joint-edit patch ownership"):
        oracle._decode_transform(bytes(raw), rows_meta)


def test_decode_transform_rejects_incomplete_owner_set() -> None:
    rows_meta = [
        ("a.bin", 4, b"0" * 32),
        ("b.bin", 4, b"1" * 32),
    ]
    anchor = b"ABCD"
    raw = bytearray(oracle.TRANSFORM_MAGIC)
    raw += struct.pack("<IQ", 0, len(anchor)) + anchor
    raw += struct.pack("<I", 0)
    with pytest.raises(RuntimeError, match="invalid joint-edit patch count"):
        oracle._decode_transform(bytes(raw), rows_meta)


def test_transform_roundtrips_multiple_members_exactly() -> None:
    rows = [
        ("a.bin", b"prefix" + b"A" * 2048 + b"tail"),
        ("b.bin", b"X" + b"A" * 1024 + b"B" + b"A" * 1023 + b"tail"),
        ("c.bin", b"prefix" + b"A" * 2048 + b"TAIL"),
    ]
    anchor_i = oracle._anchor(rows)
    encoded, _stats = oracle._transform(rows, anchor_i)
    meta = [(name, len(raw), b"x" * 32) for name, raw in rows]
    assert oracle._decode_transform(encoded, meta) == [raw for _name, raw in rows]


def test_structural_anchor_selection_does_not_consult_paths() -> None:
    payloads = [b"a" * 101, b"b" * 103, b"c" * 107]
    first = [(f"old-{i}", raw) for i, raw in enumerate(payloads)]
    renamed = [(f"renamed-{i}", raw) for i, raw in enumerate(payloads)]
    assert oracle._anchor(first) == oracle._anchor(renamed)
