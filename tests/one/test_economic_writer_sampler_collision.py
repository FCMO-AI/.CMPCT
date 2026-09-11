from __future__ import annotations

from benchmarks.one.one_g02_economic_writer_sampler_collision import (
    FROZEN_SAMPLE_POINTS,
    LENGTHS,
    RELATIONS,
    _oracle_sample_positions,
    run,
)


def test_frozen_matrix_has_unsampled_poison_positions() -> None:
    assert FROZEN_SAMPLE_POINTS == 16
    assert LENGTHS == (17, 32, 256, 4096)
    assert RELATIONS == ("add8", "xor")
    for length in LENGTHS:
        positions = _oracle_sample_positions(length)
        assert len(positions) == FROZEN_SAMPLE_POINTS
        assert set(range(length)) - set(positions)


def test_sampler_collision_is_real_and_false_law_never_survives() -> None:
    result = run()
    assert result["schema"] == "cmpct-one-g02-economic-writer-sampler-collision-v1"
    assert result["writer_sample_points"] == 16
    assert result["frozen_oracle_sample_points"] == 16
    assert len(result["rows"]) == len(RELATIONS) * len(LENGTHS)

    for row in result["rows"]:
        assert row["sampler_matches_frozen_oracle"] is True
        assert row["sampled_relation_holds"] is True
        assert row["poison_breaks_relation"] is True
        assert row["economic_model_admits"] is True
        assert row["current_structure"] == "surprise"
        assert row["economic_structure"] == "surprise"
        assert row["false_relation_rejected"] is True
        assert row["semantic_exact"] is True
        assert row["economic_deterministic"] is True
        assert row["generic_reader_ontology_only"] is True
        assert row["complete_bytes_non_regressing"] is True
        assert row["proof_work_nonzero"] is True
        assert row["proof_accounting_equal"] is True

    assert result["false_survivors"] == []
    assert all(result["hypotheses"].values())
    assert result["decision"] == "ADVANCE_SAMPLER_COLLISION_SAFETY_ONLY"


def test_sampler_collision_claim_boundary_excludes_genesis() -> None:
    result = run()
    assert "not Genesis" in result["claim_boundary"]
    for flag in (
        "genesis_inputs_executed",
        "genesis_comparison_executed",
        "genesis_scoring_executed",
        "genesis_winner_selected",
    ):
        assert result[flag] is False
