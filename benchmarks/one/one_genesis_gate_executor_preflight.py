from __future__ import annotations

"""Fail-closed preflight for the CMPCT1 Genesis gate executor.

This module intentionally performs no contender encoding, benchmarking, or scoring. It
freezes the exact candidate SHA, verifies the preregistered workload/comparator authority,
and emits a machine-readable execution plan that a September-11 executor can consume.

The scientific purpose is to remove execution-time freedom *before* results exist. The
plan is not gate evidence and cannot be used to claim a winner.
"""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
READINESS_SOURCE = "070d4f803c7b4441f517fc5c0b90f19214f5b05f"
READINESS_DIGEST = "sha256:a1b009dfed8deeed3a9d46ab0cc4cdaf224141c903b2c8bdcdeae32434074abd"
GATE_TZ = ZoneInfo("America/Mexico_City")
GATE_DATE = "2026-09-11"

IDENTITY_MANIFEST = ROOT / "benchmarks" / "one" / "genesis_gate_workload_identity_v1.json"
COMPARATOR_MANIFEST = ROOT / "benchmarks" / "one" / "genesis_frozen_comparator_authority_v1.json"
READINESS_RUNNER = ROOT / "benchmarks" / "one" / "one_genesis_gate_readiness.py"
RESULT_VALIDATOR = ROOT / "benchmarks" / "one" / "one_genesis_gate_result_validator.py"
EXECUTION_CONTRACT = ROOT / "docs" / "one" / "prereg" / "ONE_GENESIS_GATE_EXECUTION_CONTRACT_2026-09-10.md"

REQUIRED_FILES = (
    IDENTITY_MANIFEST,
    COMPARATOR_MANIFEST,
    READINESS_RUNNER,
    RESULT_VALIDATOR,
    EXECUTION_CONTRACT,
)


def _git_head(path: Path = ROOT) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _is_hex_sha(value: str) -> bool:
    if len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _validate_authorities(candidate_sha: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not _is_hex_sha(candidate_sha):
        errors.append("candidate SHA must be exactly 40 hexadecimal characters")

    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        errors.append(f"missing required gate authority files: {missing}")
        return errors, {"missing": missing}

    identity = _load_json(IDENTITY_MANIFEST)
    comparator = _load_json(COMPARATOR_MANIFEST)

    if identity.get("schema") != "cmpct-one-genesis-gate-workload-identity-v1":
        errors.append("unexpected workload identity manifest schema")
    rows = identity.get("workloads")
    if not isinstance(rows, list) or len(rows) != 15:
        errors.append("workload identity manifest must contain exactly 15 workloads")
    if identity.get("suite_counts") != {"neutral_hostile_v1": 10, "resemblance_hostile_v1": 5}:
        errors.append("workload identity suite counts are not the frozen 10/5 split")
    if identity.get("readiness_source_sha") != READINESS_SOURCE:
        errors.append("workload identity manifest readiness source differs from frozen authority")
    if identity.get("readiness_artifact_digest") != READINESS_DIGEST:
        errors.append("workload identity manifest readiness digest differs from frozen authority")

    if comparator.get("schema") != "cmpct-one-genesis-frozen-comparator-authority-v1":
        errors.append("unexpected frozen comparator authority schema")
    if comparator.get("frozen_v029_sha") != V029_SHA:
        errors.append("v0.29 comparator manifest SHA differs from Genesis authority")
    if comparator.get("frozen_v030_sha") != V030_SHA:
        errors.append("v0.30 comparator manifest SHA differs from Genesis authority")
    admissibility = comparator.get("admissibility", {})
    for key in (
        "no_posthoc_best_per_row_oracle",
        "carry_measured_runtime_and_resource_debt_with_each_historical_win",
        "preserve_each_historical_loss",
        "primary_15_workload_same_input_same_semantics_gate_remains_required",
        "detached_payload_results_are_not_whole_archive_scores",
    ):
        if admissibility.get(key) is not True:
            errors.append(f"frozen comparator authority missing required admissibility rule {key}")

    authority_hashes = {str(path.relative_to(ROOT)): _sha256(path) for path in REQUIRED_FILES}
    return errors, {
        "workload_identity_schema": identity.get("schema"),
        "workload_count": len(rows) if isinstance(rows, list) else None,
        "suite_counts": identity.get("suite_counts"),
        "comparator_authority_schema": comparator.get("schema"),
        "authority_sha256": authority_hashes,
    }


def build_plan(candidate_sha: str, *, now: datetime | None = None) -> dict[str, Any]:
    errors, authority = _validate_authorities(candidate_sha)
    observed_head = _git_head()
    if observed_head != candidate_sha:
        errors.append(f"candidate SHA {candidate_sha} does not equal checked-out HEAD {observed_head}")

    current = now.astimezone(GATE_TZ) if now is not None else datetime.now(GATE_TZ)
    gate_open = current.date().isoformat() >= GATE_DATE

    return {
        "schema": "cmpct-one-genesis-gate-execution-plan-v1",
        "claim_boundary": "preflight/execution plumbing only; no contender encoding, measurements, scoring, or winner selection executed",
        "experimental_version": "ONE-G0.2",
        "candidate_sha": candidate_sha,
        "checked_out_head": observed_head,
        "candidate_head_exact": observed_head == candidate_sha,
        "frozen_comparators": {"v0.29": V029_SHA, "v0.30": V030_SHA},
        "readiness_authority": {
            "source_sha": READINESS_SOURCE,
            "artifact_digest": READINESS_DIGEST,
            "required_exact_workloads": 15,
        },
        "authority": authority,
        "gate_clock": {
            "timezone": "America/Mexico_City",
            "observed_local": current.isoformat(),
            "first_allowed_date": GATE_DATE,
            "gate_open": gate_open,
        },
        "execution_order": [
            "rerun_non_scoring_readiness",
            "record_environment",
            "run_candidate_semantic_hostile_validity",
            "execute_same_tree_contenders",
            "run_selective_resource_integrity_probes",
            "persist_raw_measurements_before_interpretation",
            "derive_matrix_and_aggregates",
            "attach_frozen_v030_frontier_and_one_negative_ledgers",
            "run_fail_closed_result_validator",
            "hostile_review_and_adjudicate",
            "persist_first_result_without_rewrite",
        ],
        "prohibited_before_gate": [
            "contender_encoding",
            "comparator_encoding",
            "genesis_scoring",
            "winner_selection",
        ],
        "contender_encoding_executed": False,
        "comparator_encoding_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
        "errors": errors,
        "decision": "EXECUTOR_PREFLIGHT_READY" if not errors else "HOLD_EXECUTOR_PREFLIGHT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", default=os.environ.get("EVIDENCE_HEAD"))
    parser.add_argument("--output", type=Path, default=Path("one-genesis-gate-execution-plan.json"))
    args = parser.parse_args()

    candidate = args.candidate_sha or _git_head()
    result = build_plan(candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "candidate_sha": result["candidate_sha"],
        "gate_open": result["gate_clock"]["gate_open"],
        "errors": result["errors"],
        "scoring_executed": result["scoring_executed"],
    }, indent=2))
    if result["decision"] != "EXECUTOR_PREFLIGHT_READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
