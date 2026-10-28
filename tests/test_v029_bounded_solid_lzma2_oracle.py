from experiments.entropygraph_v029_bounded_solid_lzma2_oracle import (
    MAX_MEMBER_AMPLIFICATION,
    _pack_adjacent,
)


def _row(record_id: int, logical_bytes: int) -> dict:
    return {"record_id": record_id, "logical_bytes": logical_bytes}


def test_pack_adjacent_never_exceeds_limit_or_amplification() -> None:
    rows = [_row(0, 128 * 1024), _row(1, 128 * 1024), _row(2, 256 * 1024), _row(3, 512 * 1024)]
    groups = _pack_adjacent(rows, 512 * 1024)
    assert groups
    for group in groups:
        total = sum(int(row["logical_bytes"]) for row in group)
        assert total <= 512 * 1024
        assert len(group) >= 2
        assert max(total / int(row["logical_bytes"]) for row in group) <= MAX_MEMBER_AMPLIFICATION


def test_tiny_member_that_would_break_random_access_stays_out_of_group() -> None:
    rows = [_row(0, 8 * 1024), _row(1, 256 * 1024), _row(2, 256 * 1024)]
    groups = _pack_adjacent(rows, 1 << 20)
    assert all(0 not in [int(row["record_id"]) for row in group] for group in groups)


def test_singletons_are_not_solid_clusters() -> None:
    assert _pack_adjacent([_row(0, 128 * 1024)], 1 << 20) == []
