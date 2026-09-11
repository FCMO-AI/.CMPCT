from __future__ import annotations

"""Transfer-only falsifier for a marginal-cost Crystallization admission model.

This does not modify the writer. One isolated calibration construction per generic relation
family estimates the fixed local representation term K in `predicted_delta = K - n`.
The frozen evaluation matrix then attacks sign safety around the observed crossover and
larger serialization/authentication boundaries.
"""

import json
from pathlib import Path
import tempfile
from typing import Any

from benchmarks.one.one_g02_crystallization_wire_economics_geometry import _row

CALIBRATION_LENGTH = 23
LENGTHS = (
    2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17,
    31, 32, 33, 63, 64, 65, 127, 128, 129, 255, 256, 257,
    511, 512, 513, 1023, 1024, 1025, 4095, 4096, 4097,
    16383, 16384, 16385,
)
FAMILIES = ("exact_reuse", "add8", "xor", "fill")
BOUNDARY_LENGTHS = frozenset({9, 10, 11, 12, 15, 16, 17, 4095, 4096, 4097, 16383, 16384, 16385})
OUT = Path("one-g02-crystallization-marginal-cost-model.json")


def _calibrate(parent: Path, family: str) -> dict[str, Any]:
    row = _row(parent / "calibration", family, CALIBRATION_LENGTH)
    k_bytes = int(row["candidate_minus_control_bytes"]) + CALIBRATION_LENGTH
    return {
        "family": family,
        "calibration_length": CALIBRATION_LENGTH,
        "actual_delta_bytes": int(row["candidate_minus_control_bytes"]),
        "k_bytes": k_bytes,
        "semantic_exact": bool(row["semantic_exact"]),
        "deterministic_wire": bool(row["deterministic_wire"]),
        "generic_reader_ontology_only": bool(row["generic_reader_ontology_only"]),
        "reader_structure_ok": bool(row["reader_structure_evidence"]["ok"]),
    }


def _predict_delta(length: int, k_bytes: int) -> int:
    return int(k_bytes) - int(length)


def _evaluate_row(parent: Path, family: str, length: int, k_bytes: int) -> dict[str, Any]:
    measured = _row(parent / "evaluation", family, length)
    actual = int(measured["candidate_minus_control_bytes"])
    predicted = _predict_delta(length, k_bytes)
    predicted_admit = predicted <= 0
    actual_non_regressing = actual <= 0
    return {
        "family": family,
        "length": length,
        "k_bytes": k_bytes,
        "predicted_delta_bytes": predicted,
        "actual_delta_bytes": actual,
        "prediction_residual_bytes": actual - predicted,
        "predicted_admit": predicted_admit,
        "actual_non_regressing": actual_non_regressing,
        "false_admit": predicted_admit and not actual_non_regressing,
        "false_reject": (not predicted_admit) and actual_non_regressing,
        "sign_correct": predicted_admit == actual_non_regressing,
        "semantic_exact": bool(measured["semantic_exact"]),
        "deterministic_wire": bool(measured["deterministic_wire"]),
        "generic_reader_ontology_only": bool(measured["generic_reader_ontology_only"]),
        "reader_structure_ok": bool(measured["reader_structure_evidence"]["ok"]),
        "candidate_wire_bytes": int(measured["candidate_wire_bytes"]),
        "control_wire_bytes": int(measured["control_wire_bytes"]),
    }


def _boundary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["length"] in BOUNDARY_LENGTHS]


def _decision(calibrations: list[dict[str, Any]], rows: list[dict[str, Any]]) -> str:
    calibration_ok = all(
        row["semantic_exact"]
        and row["deterministic_wire"]
        and row["generic_reader_ontology_only"]
        and row["reader_structure_ok"]
        for row in calibrations
    )
    structural_ok = all(
        row["semantic_exact"]
        and row["deterministic_wire"]
        and row["generic_reader_ontology_only"]
        and row["reader_structure_ok"]
        for row in rows
    )
    false_admits = [row for row in rows if row["false_admit"]]
    boundary_false_rejects = [row for row in _boundary_rows(rows) if row["false_reject"]]
    binary_admit = all(
        any(row["family"] == family and row["predicted_admit"] for row in rows)
        for family in ("add8", "xor")
    )
    if not calibration_ok or not structural_ok or false_admits:
        return "RETIRE_OR_REPAIR_MARGINAL_COST_ADMISSION_MODEL"
    # A false reject is safe for bytes but violates preregistered H2 sign fidelity at an
    # explicitly attacked boundary. Preserve that as HOLD rather than laundering it into
    # ADVANCE merely because the model was conservative.
    if boundary_false_rejects or not binary_admit:
        return "HOLD_MARGINAL_COST_ADMISSION_MODEL"
    return "ADVANCE_MARGINAL_COST_ADMISSION_MODEL"


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-marginal-cost-") as td:
        parent = Path(td)
        calibrations = [_calibrate(parent, family) for family in FAMILIES]
        constants = {row["family"]: int(row["k_bytes"]) for row in calibrations}
        rows = [
            _evaluate_row(parent, family, length, constants[family])
            for family in FAMILIES
            for length in LENGTHS
        ]

    false_admits = [row for row in rows if row["false_admit"]]
    false_rejects = [row for row in rows if row["false_reject"]]
    sign_errors = [row for row in rows if not row["sign_correct"]]
    boundary = _boundary_rows(rows)
    boundary_false_admits = [row for row in boundary if row["false_admit"]]
    boundary_false_rejects = [row for row in boundary if row["false_reject"]]
    residuals_by_family = {
        family: sorted({int(row["prediction_residual_bytes"]) for row in rows if row["family"] == family})
        for family in FAMILIES
    }
    max_abs_residual_by_family = {
        family: max(abs(int(row["prediction_residual_bytes"])) for row in rows if row["family"] == family)
        for family in FAMILIES
    }
    decision = _decision(calibrations, rows)
    payload = {
        "schema": "cmpct-one-g02-crystallization-marginal-cost-model-v2",
        "experimental_version": "ONE-G0.2",
        "claim_boundary": "synthetic transfer marginal-cost sign model only; not a product threshold, writer change, or Genesis result",
        "calibration_policy": "one isolated length-23 construction per generic family; length 23 is excluded from the frozen evaluation matrix",
        "calibration_length": CALIBRATION_LENGTH,
        "lengths": list(LENGTHS),
        "families": list(FAMILIES),
        "boundary_lengths": sorted(BOUNDARY_LENGTHS),
        "calibrations": calibrations,
        "k_bytes": constants,
        "rows": rows,
        "false_admit_count": len(false_admits),
        "false_reject_count": len(false_rejects),
        "sign_error_count": len(sign_errors),
        "false_admits": false_admits,
        "false_rejects": false_rejects,
        "residuals_by_family": residuals_by_family,
        "max_abs_residual_by_family": max_abs_residual_by_family,
        "boundary_false_admit_count": len(boundary_false_admits),
        "boundary_false_reject_count": len(boundary_false_rejects),
        "boundary_sign_error_count": len(boundary_false_admits) + len(boundary_false_rejects),
        "binary_law_admission_demonstrated": {
            family: any(row["family"] == family and row["predicted_admit"] for row in rows)
            for family in ("add8", "xor")
        },
        "decision": decision,
        "genesis_inputs_executed": False,
        "genesis_comparison_executed": False,
        "genesis_scoring_executed": False,
        "genesis_winner_selected": False,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
