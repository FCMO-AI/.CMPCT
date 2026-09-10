from __future__ import annotations

from benchmarks.one.one_g02_second_stage_relation_falsifier import (
    FROZEN_SAMPLE_POINTS,
    KINDS,
    LENGTHS,
    RELATIONS,
    _oracle_primary_positions,
    _oracle_second_positions,
    run,
)


def test_second_stage_geometry_is_frozen_disjoint_and_has_dual_space() -> None:
    assert FROZEN_SAMPLE_POINTS == 16
    assert LENGTHS == (32, 256, 4096, 16384)
    assert RELATIONS == ("add8", "xor")
    assert KINDS == ("true", "stage2_collision", "dual_collision")

    for length in LENGTHS:
        primary = _oracle_primary_positions(length)
        second = _oracle_second_positions(primary)
        assert len(primary) == FROZEN_SAMPLE_POINTS
        assert second
        assert not (set(primary) & set(second))
        assert set(range(length)) - set(primary) - set(second)


def test_second_stage_oracle_retains_truth_kills_single_collision_and_preserves_dual_cost() -> None:
    result = run()
    assert result["schema"] == "cmpct-one-g02-second-stage-relation-falsifier-v1"
    assert len(result["rows"]) == len(RELATIONS) * len(LENGTHS) * len(KINDS)

    for row in result["rows"]:
        assert row["primary_matches_writer"] is True
        assert row["second_nonempty"] is True
        assert row["second_disjoint"] is True
        assert row["dual_position_available"] is True

        if row["kind"] == "true":
            assert row["primary_pass"] is True
            assert row["second_pass"] is True
            assert row["exact_pass"] is True
            assert row["candidate_exact_proof_bytes"] == row["baseline_remaining_bytes"]
            assert row["remaining_delta_bytes"] == row["second_stage_bytes"]
        elif row["kind"] == "stage2_collision":
            assert row["primary_pass"] is True
            assert row["second_pass"] is False
            assert row["exact_pass"] is False
            assert row["candidate_exact_proof_bytes"] == 0
            assert row["exact_proof_bytes_avoided"] == row["baseline_remaining_bytes"]
            assert row["candidate_remaining_bytes"] < row["baseline_remaining_bytes"]
            assert row["stage2_kill_speedup_by_modeled_bytes"] > 1.0
        elif row["kind"] == "dual_collision":
            assert row["primary_pass"] is True
            assert row["second_pass"] is True
            assert row["exact_pass"] is False
            assert row["candidate_exact_proof_bytes"] == row["baseline_remaining_bytes"]
            assert row["remaining_delta_bytes"] == row["second_stage_bytes"]
        else:
            raise AssertionError(row["kind"])

    assert all(result["hypotheses"].values())
    assert result["decision"] == "ADVANCE_SECOND_STAGE_FALSIFIER_ORACLE_ONLY"


def test_second_stage_summary_keeps_benefit_and_debt_separate() -> None:
    result = run()
    summary = result["summary"]
    expected_stage2_rows = len(RELATIONS) * len(LENGTHS)
    assert summary["stage2_kill_rows"] == expected_stage2_rows
    assert summary["stage2_total_exact_proof_bytes_avoided"] > summary["stage2_total_candidate_remaining_bytes"]
    assert summary["dual_total_added_sparse_bytes"] > 0
    assert summary["true_total_added_sparse_bytes"] == summary["dual_total_added_sparse_bytes"]
    assert summary["min_stage2_kill_speedup_by_modeled_bytes"] > 1.0
    assert summary["max_stage2_kill_speedup_by_modeled_bytes"] >= summary["min_stage2_kill_speedup_by_modeled_bytes"]


def test_second_stage_claim_boundary_excludes_runtime_and_genesis() -> None:
    result = run()
    assert "no product runtime claim" in result["claim_boundary"]
    assert "not Genesis" in result["claim_boundary"]
    for flag in (
        "genesis_inputs_executed",
        "genesis_comparison_executed",
        "genesis_scoring_executed",
        "genesis_winner_selected",
    ):
        assert result[flag] is False
