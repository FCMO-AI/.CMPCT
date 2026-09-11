from __future__ import annotations

from benchmarks.one.one_g02_crystallization_marginal_cost_model import (
    BOUNDARY_LENGTHS,
    CALIBRATION_LENGTH,
    FAMILIES,
    LENGTHS,
    _decision,
    _predict_delta,
    run,
)


def _good_row(family: str = "add8", length: int = 16) -> dict[str, object]:
    return {
        "family": family,
        "length": length,
        "predicted_admit": True,
        "actual_non_regressing": True,
        "false_admit": False,
        "false_reject": False,
        "sign_correct": True,
        "semantic_exact": True,
        "deterministic_wire": True,
        "generic_reader_ontology_only": True,
        "reader_structure_ok": True,
    }


def _good_calibration(family: str) -> dict[str, object]:
    return {
        "family": family,
        "semantic_exact": True,
        "deterministic_wire": True,
        "generic_reader_ontology_only": True,
        "reader_structure_ok": True,
    }


def test_frozen_matrix_excludes_calibration_and_attacks_boundaries() -> None:
    assert CALIBRATION_LENGTH == 23
    assert CALIBRATION_LENGTH not in LENGTHS
    assert FAMILIES == ("exact_reuse", "add8", "xor", "fill")
    for length in BOUNDARY_LENGTHS:
        assert length in LENGTHS


def test_prediction_is_affine_cost_not_length_table() -> None:
    assert _predict_delta(2, 11) == 9
    assert _predict_delta(11, 11) == 0
    assert _predict_delta(16, 11) == -5
    assert _predict_delta(4097, 11) == -4086


def test_any_false_admit_retires_model() -> None:
    calibrations = [_good_calibration(family) for family in FAMILIES]
    rows = [_good_row("add8", 16), _good_row("xor", 16)]
    assert _decision(calibrations, rows) == "ADVANCE_MARGINAL_COST_ADMISSION_MODEL"
    poisoned = [dict(row) for row in rows]
    poisoned[0]["false_admit"] = True
    poisoned[0]["actual_non_regressing"] = False
    poisoned[0]["sign_correct"] = False
    assert _decision(calibrations, poisoned) == "RETIRE_OR_REPAIR_MARGINAL_COST_ADMISSION_MODEL"


def test_boundary_false_reject_is_hold_not_advance_or_retire() -> None:
    calibrations = [_good_calibration(family) for family in FAMILIES]
    rows = [_good_row("add8", 16), _good_row("xor", 16)]
    conservative = [dict(row) for row in rows]
    conservative[0]["predicted_admit"] = False
    conservative[0]["actual_non_regressing"] = True
    conservative[0]["false_reject"] = True
    conservative[0]["sign_correct"] = False
    assert _decision(calibrations, conservative) == "HOLD_MARGINAL_COST_ADMISSION_MODEL"


def test_no_binary_admission_holds_even_when_safe() -> None:
    calibrations = [_good_calibration(family) for family in FAMILIES]
    rows = []
    for family in ("add8", "xor"):
        row = _good_row(family, 8)
        row["predicted_admit"] = False
        row["actual_non_regressing"] = False
        rows.append(row)
    assert _decision(calibrations, rows) == "HOLD_MARGINAL_COST_ADMISSION_MODEL"


def test_transfer_run_is_fail_closed_and_genesis_excluded(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    payload = run()
    assert payload["schema"] == "cmpct-one-g02-crystallization-marginal-cost-model-v2"
    assert payload["calibration_length"] == CALIBRATION_LENGTH
    assert payload["boundary_lengths"] == sorted(BOUNDARY_LENGTHS)
    assert len(payload["rows"]) == len(FAMILIES) * len(LENGTHS)
    assert len(payload["calibrations"]) == len(FAMILIES)
    assert payload["decision"] in {
        "ADVANCE_MARGINAL_COST_ADMISSION_MODEL",
        "HOLD_MARGINAL_COST_ADMISSION_MODEL",
        "RETIRE_OR_REPAIR_MARGINAL_COST_ADMISSION_MODEL",
    }
    assert payload["false_admit_count"] >= 0
    assert payload["false_reject_count"] >= 0
    assert payload["boundary_sign_error_count"] == (
        payload["boundary_false_admit_count"] + payload["boundary_false_reject_count"]
    )
    for flag in (
        "genesis_inputs_executed",
        "genesis_comparison_executed",
        "genesis_scoring_executed",
        "genesis_winner_selected",
    ):
        assert payload[flag] is False
    assert (tmp_path / "one-g02-crystallization-marginal-cost-model.json").exists()
