from __future__ import annotations

from benchmarks import v030_shifted_joint_patch_stream_oracle as JOINT
from benchmarks import v030_shifted_segmented_relation_payload_floor as SEG


def _rows() -> list[tuple[str, bytes]]:
    anchor = (b"abcdefgh" * 128) + b"tail"
    near_a = bytearray(anchor)
    near_a[17] ^= 0x31
    near_b = bytearray(anchor)
    near_b[513] ^= 0x52
    far = b"z" * len(anchor)
    return [
        ("a.bin", anchor),
        ("b.bin", bytes(near_a)),
        ("c.bin", bytes(near_b)),
        ("d.bin", far),
    ]


def test_segment_rows_is_exact_partition_and_each_unit_obeys_laws() -> None:
    rows = _rows()
    segments, stats = SEG._segment_rows(rows)

    assert segments
    flattened = [idx for segment in segments for idx in segment]
    assert sorted(flattened) == list(range(len(rows)))
    assert len(flattened) == len(set(flattened))
    assert stats["pair_evaluations"] >= len(rows) - 1
    assert stats["pair_patch_bytes"] > 0

    for indices in segments:
        selected = [rows[i] for i in indices]
        transform, _ = JOINT._transform(selected, 0)
        min_member = min(len(raw) for _name, raw in selected)
        assert len(transform) <= SEG.MAX_DECODE_UNIT
        assert len(transform) / max(1, min_member) <= SEG.MAX_LOCALITY


def test_segment_rows_does_not_use_member_names_for_grouping() -> None:
    rows = _rows()
    renamed = [(f"renamed-{len(rows) - i}.dat", raw) for i, (_name, raw) in enumerate(rows)]

    original_segments, original_stats = SEG._segment_rows(rows)
    renamed_segments, renamed_stats = SEG._segment_rows(renamed)

    assert renamed_segments == original_segments
    assert renamed_stats == original_stats


def test_segment_rows_rejects_intrinsically_oversized_singleton(monkeypatch) -> None:
    monkeypatch.setattr(SEG, "MAX_DECODE_UNIT", 64)
    monkeypatch.setattr(SEG, "MAX_LOCALITY", 8.0)
    rows = [("member.bin", b"x" * 256)]

    segments, stats = SEG._segment_rows(rows)

    assert segments == []
    assert stats["terminal_member_index"] == 0
    assert stats["terminal_singleton_bytes"] > stats["terminal_singleton_limit"]
    assert stats["terminal_singleton_limit"] == 64
