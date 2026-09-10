from __future__ import annotations

import json
import subprocess
from pathlib import Path

MANIFEST = Path("benchmarks/one/genesis_frozen_comparator_authority_v1.json")
EXPECTED_SCHEMA = "cmpct-one-genesis-frozen-comparator-authority-v1"
EXPECTED_V029 = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
EXPECTED_V030 = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def validate() -> dict[str, object]:
    payload = json.loads(MANIFEST.read_text())
    errors: list[str] = []

    if payload.get("schema") != EXPECTED_SCHEMA:
        errors.append("unexpected authority-manifest schema")
    if payload.get("frozen_v029_sha") != EXPECTED_V029:
        errors.append("frozen v0.29 authority mismatch")
    if payload.get("frozen_v030_sha") != EXPECTED_V030:
        errors.append("frozen v0.30 authority mismatch")

    for sha, label in ((EXPECTED_V029, "v0.29"), (EXPECTED_V030, "v0.30")):
        try:
            resolved = _git("rev-parse", f"{sha}^{{commit}}")
        except subprocess.CalledProcessError:
            errors.append(f"{label} frozen commit unavailable in checkout")
            continue
        if resolved != sha:
            errors.append(f"{label} frozen commit resolves to unexpected SHA {resolved}")

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append("authority manifest contains no records")
        records = []

    seen_paths: set[str] = set()
    observed: list[dict[str, str]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        path = record.get("path")
        expected_blob = record.get("blob_sha")
        role = record.get("role")
        if not isinstance(path, str) or not path:
            errors.append(f"record {index} missing path")
            continue
        if path in seen_paths:
            errors.append(f"duplicate comparator record path: {path}")
        seen_paths.add(path)
        if not isinstance(role, str) or not role:
            errors.append(f"record {path} missing role")
        if not isinstance(expected_blob, str) or len(expected_blob) != 40:
            errors.append(f"record {path} missing 40-hex blob SHA")
            continue
        try:
            actual_blob = _git("rev-parse", f"{EXPECTED_V030}:{path}")
        except subprocess.CalledProcessError:
            errors.append(f"record absent from frozen v0.30 tree: {path}")
            continue
        if actual_blob != expected_blob:
            errors.append(
                f"record blob mismatch for {path}: expected {expected_blob}, observed {actual_blob}"
            )
        observed.append({"path": path, "expected_blob": expected_blob, "observed_blob": actual_blob})

    admissibility = payload.get("admissibility")
    if not isinstance(admissibility, dict):
        errors.append("missing admissibility policy")
    else:
        for key in (
            "no_posthoc_best_per_row_oracle",
            "carry_measured_runtime_and_resource_debt_with_each_historical_win",
            "preserve_each_historical_loss",
            "primary_15_workload_same_input_same_semantics_gate_remains_required",
            "detached_payload_results_are_not_whole_archive_scores",
        ):
            if admissibility.get(key) is not True:
                errors.append(f"required admissibility law not true: {key}")
        if admissibility.get("unverified_17_97_percent_late_clustered_claim_admitted") is not False:
            errors.append("unverified late-clustered claim must remain excluded")

    roles = {record.get("role") for record in records if isinstance(record, dict)}
    if "v030_geometry_complete_artifact_positive" not in roles:
        errors.append("complete-artifact Geometry authority missing")
    if "v030_hierarchical_geometry_detached_discovery_only" not in roles:
        errors.append("detached Hierarchical Geometry discovery authority missing")

    result: dict[str, object] = {
        "schema": "cmpct-one-genesis-frozen-comparator-authority-validation-v1",
        "manifest": str(MANIFEST),
        "frozen_v029": EXPECTED_V029,
        "frozen_v030": EXPECTED_V030,
        "records_checked": len(observed),
        "records": observed,
        "ok": not errors,
        "errors": errors,
        "claim_boundary": "identity/admissibility validation only; no compression or Genesis scoring executed",
    }
    return result


def main() -> int:
    result = validate()
    Path("genesis-frozen-comparator-authority-validation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    if not result["ok"]:
        for error in result["errors"]:  # type: ignore[index]
            print(f"ERROR: {error}")
        return 1
    print(f"validated {result['records_checked']} frozen comparator evidence records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
