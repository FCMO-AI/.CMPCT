from experiments.entropygraph_v029_local_pair_fusion_oracle import _candidate_pairs, _pair_admissible


def row(size: int) -> dict:
    return {"logical_bytes": size}


def test_pair_admissibility_preserves_eight_x_bound():
    assert _pair_admissible(row(100), row(700)) is True
    assert _pair_admissible(row(100), row(701)) is False


def test_candidate_search_can_skip_size_imbalanced_neighbor():
    rows = [row(512 << 10), row(8 << 10), row(480 << 10)]
    pairs = _candidate_pairs(rows)
    assert (0, 1) not in pairs
    assert (1, 2) not in pairs
    assert (0, 2) in pairs


def test_pair_search_respects_lookahead_window():
    rows = [row(256 << 10) for _ in range(10)]
    pairs = _candidate_pairs(rows)
    assert (0, 8) in pairs
    assert (0, 9) not in pairs
