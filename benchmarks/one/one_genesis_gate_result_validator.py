from __future__ import annotations

"""Fail-closed structural validator for the CMPCT1 Genesis gate result.

This module performs no compression, scoring, or winner selection. It exists so the
September 11 result cannot silently omit a workload, comparator, metric family, or
negative/debt field required by the preregistered execution contract.
"""

from dataclasses import dataclass
from typing import Any

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
EXPECTED_SUITE_COUNTS = {"neutral_hostile_v1": 10, "resemblance_hostile_v1": 5}
CONTENDERS = ("cmpct1", "v0.29", "v0.30")
COMPARATORS = ("v0.29", "v0.30")
REQUIRED_MEASUREMENT_KEYS = (
    "stored_bytes",
    "creation",
    "whole_read",
    "selective_access",
    "semantics",
    "reader_burden",
)
REQUIRED_COMPARISON_KEYS = (
    "size_status",
    "creation_status",
    "read_status",
    "selective_resource_status",
    "semantic_status",
    "verdict",
)
ALLOWED_ROW_VERDICTS = {"WIN", "FALLBACK/EQUAL", "DEBT", "LOSS", "INVALID"}
ALLOWED_FINAL_DECISIONS = {
    "KEEP_CMPCT1_PRIMARY",
    "REACTIVATE_V030_PRIMARY",
    "INVALID_GATE_RESULT",
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]


def _is_unavailable(value: Any) -> bool:
    return value == "unavailable" or (
        isinstance(value, dict) and value.get("status") == "unavailable"
    )


def _require_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {}
    return value


def _validate_measurement(measurement: Any, label: str, errors: list[str]) -> None:
    m = _require_mapping(measurement, label, errors)
    if not m:
        return
    for key in REQUIRED_MEASUREMENT_KEYS:
        if key not in m:
            errors.append(f"{label} missing measurement family {key}")

    stored = m.get("stored_bytes")
    if not (_is_unavailable(stored) or (isinstance(stored, int) and stored >= 0)):
        errors.append(f"{label}.stored_bytes must be a non-negative integer or explicit unavailable")

    # Missing measurements must never be encoded as synthetic zeroes. A true measured
    # zero is permitted only when accompanied by explicit measured=true provenance.
    for family in ("creation", "whole_read", "selective_access"):
        value = m.get(family)
        if value is None:
            continue
        if _is_unavailable(value):
            continue
        obj = _require_mapping(value, f"{label}.{family}", errors)
        for metric_name, metric_value in obj.items():
            if metric_name in {"status", "notes", "process_boundary", "cache_semantics", "measured"}:
                continue
            if metric_value == 0 and obj.get("measured") is not True:
                errors.append(
                    f"{label}.{family}.{metric_name} is zero without measured=true; use unavailable for missing cells"
                )


def validate_gate_result(payload: Any) -> ValidationResult:
    errors: list[str] = []
    root = _require_mapping(payload, "result", errors)
    if not root:
        return ValidationResult(False, tuple(errors))

    if root.get("schema") != "cmpct-one-genesis-gate-result-v1":
        errors.append("unexpected or missing gate result schema")

    candidate_sha = root.get("cmpct1_candidate_sha")
    if not isinstance(candidate_sha, str) or len(candidate_sha) != 40:
        errors.append("cmpct1_candidate_sha must be a frozen 40-hex commit identity")

    frozen = _require_mapping(root.get("frozen_comparators"), "frozen_comparators", errors)
    if frozen.get("v0.29") != V029_SHA:
        errors.append("v0.29 comparator SHA differs from Genesis authority")
    if frozen.get("v0.30") != V030_SHA:
        errors.append("v0.30 comparator SHA differs from Genesis authority")

    readiness = _require_mapping(root.get("readiness_authority"), "readiness_authority", errors)
    for key in ("source_sha", "artifact_digest", "all_15_identities_exact"):
        if key not in readiness:
            errors.append(f"readiness_authority missing {key}")
    if readiness.get("all_15_identities_exact") is not True:
        errors.append("gate result is not bound to exact 15/15 readiness")

    environment = _require_mapping(root.get("environment"), "environment", errors)
    for key in ("os", "cpu", "python", "toolchain", "codec_versions", "runner_identity"):
        if key not in environment:
            errors.append(f"environment missing {key}")

    protocol = _require_mapping(root.get("measurement_protocol"), "measurement_protocol", errors)
    for key in ("repetitions", "statistic", "process_boundaries", "cache_semantics", "integrity_semantics"):
        if key not in protocol:
            errors.append(f"measurement_protocol missing {key}")

    rows = root.get("workloads")
    if not isinstance(rows, list):
        errors.append("workloads must be an array")
        rows = []
    if len(rows) != 15:
        errors.append(f"expected exactly 15 workload rows, observed {len(rows)}")

    identities: set[tuple[str, str]] = set()
    suite_counts = {key: 0 for key in EXPECTED_SUITE_COUNTS}
    for index, row_any in enumerate(rows):
        row = _require_mapping(row_any, f"workloads[{index}]", errors)
        suite = row.get("suite")
        name = row.get("name")
        if suite not in EXPECTED_SUITE_COUNTS:
            errors.append(f"workloads[{index}] has unexpected suite {suite!r}")
        else:
            suite_counts[suite] += 1
        if not isinstance(name, str) or not name:
            errors.append(f"workloads[{index}] missing workload name")
            name = f"<invalid-{index}>"
        identity = (str(suite), name)
        if identity in identities:
            errors.append(f"duplicate workload identity {identity[0]}/{identity[1]}")
        identities.add(identity)

        for key in ("files", "logical_bytes", "tree_sha256"):
            if key not in row:
                errors.append(f"{suite}/{name} missing identity field {key}")

        measurements = _require_mapping(row.get("measurements"), f"{suite}/{name}.measurements", errors)
        for contender in CONTENDERS:
            if contender not in measurements:
                errors.append(f"{suite}/{name} missing contender measurement {contender}")
            else:
                _validate_measurement(
                    measurements[contender], f"{suite}/{name}.measurements.{contender}", errors
                )

        comparisons = _require_mapping(row.get("comparisons"), f"{suite}/{name}.comparisons", errors)
        for comparator in COMPARATORS:
            comp = _require_mapping(
                comparisons.get(comparator), f"{suite}/{name}.comparisons.{comparator}", errors
            )
            for key in REQUIRED_COMPARISON_KEYS:
                if key not in comp:
                    errors.append(f"{suite}/{name}.comparisons.{comparator} missing {key}")
            verdict = comp.get("verdict")
            if verdict is not None and verdict not in ALLOWED_ROW_VERDICTS:
                errors.append(f"{suite}/{name}.comparisons.{comparator} invalid verdict {verdict!r}")

    for suite, expected in EXPECTED_SUITE_COUNTS.items():
        if suite_counts.get(suite) != expected:
            errors.append(f"expected {expected} rows for {suite}, observed {suite_counts.get(suite, 0)}")

    aggregates = _require_mapping(root.get("aggregates"), "aggregates", errors)
    for comparator in COMPARATORS:
        if comparator not in aggregates:
            errors.append(f"aggregates missing {comparator}")

    frontier = _require_mapping(root.get("v030_frontier_ledger"), "v030_frontier_ledger", errors)
    for key in ("ledger_path", "ledger_commit", "evidence_refs", "strongest_admissible_result"):
        if key not in frontier:
            errors.append(f"v030_frontier_ledger missing {key}")

    negative = _require_mapping(root.get("strongest_one_negative"), "strongest_one_negative", errors)
    for key in ("evidence_ref", "summary", "unresolved_debt"):
        if key not in negative:
            errors.append(f"strongest_one_negative missing {key}")

    final = _require_mapping(root.get("final_adjudication"), "final_adjudication", errors)
    decision = final.get("decision")
    if decision not in ALLOWED_FINAL_DECISIONS:
        errors.append(f"invalid or missing final decision {decision!r}")
    for key in ("rationale", "hostile_review", "gate_run_source_sha", "artifact_digest"):
        if key not in final:
            errors.append(f"final_adjudication missing {key}")

    return ValidationResult(not errors, tuple(errors))
