from benchmarks.one.one_g02_native_writer_stage_owner import PROFILE_SIZES, STAGES, _decision


def _row(**shares):
    wall_share = {stage: 0.0 for stage in STAGES}
    wall_share.update(shares)
    return {"relation_bytes": 1 << 20, "wall_share": wall_share}


def test_profile_matrix_contains_tiny_256k_and_decision_scale():
    assert 4 * 1024 in PROFILE_SIZES
    assert 256 * 1024 in PROFILE_SIZES
    assert 1 << 20 in PROFILE_SIZES


def test_single_stage_owner_requires_repeated_1m_evidence():
    rows = [
        _row(native_observe=0.31, root_hash=0.15),
        _row(native_observe=0.28, canonical_emission=0.18),
    ]
    decision, counts = _decision(rows)
    assert decision == "OWNER_NATIVE_OBSERVE"
    assert counts["native_observe"] == 2


def test_adjacent_cluster_can_win_when_individual_owner_alternates():
    # Neither adjacent stage independently owns two rows, but their boundary does.
    rows = [
        _row(root_hash=0.21, native_observe=0.19, canonical_emission=0.10),
        _row(root_hash=0.19, native_observe=0.21, canonical_emission=0.10),
    ]
    decision, counts = _decision(rows)
    assert decision == "OWNER_CLUSTER_ROOT_HASH_NATIVE_OBSERVE"
    assert counts["root_hash"] == 1
    assert counts["native_observe"] == 1
    assert counts["root_hash+native_observe"] == 2


def test_no_owner_when_all_stage_and_adjacent_cluster_shares_are_below_gate():
    rows = [
        _row(**{stage: 0.14 for stage in STAGES}),
        _row(**{stage: 0.14 for stage in STAGES}),
    ]
    decision, counts = _decision(rows)
    assert decision == "NO_STABLE_OWNER_FUSE_BOUNDARY"
    assert all(count == 0 for stage, count in counts.items() if "+" not in stage)
    assert all(count == 0 for stage, count in counts.items() if "+" in stage)


def test_256k_rows_do_not_authorize_1m_owner_decision():
    row = _row(native_observe=0.90)
    row["relation_bytes"] = 256 << 10
    decision, counts = _decision([row])
    assert decision == "NO_STABLE_OWNER_FUSE_BOUNDARY"
    assert all(count == 0 for count in counts.values())
