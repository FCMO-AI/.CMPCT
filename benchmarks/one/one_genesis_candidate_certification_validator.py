from __future__ import annotations

"""Fail-closed validator for the durable ONE Genesis certification authority.

This tool performs no workload generation, contender execution, comparison, scoring, or
winner selection.  It encodes the exact pre-gate candidate identities already established
by hosted transfer evidence so the post-boundary authority transition can be checked
mechanically rather than by visual inspection.
"""

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "benchmarks" / "one" / "genesis_one_candidate_boundary_v1.json"
FROZEN_CANDIDATE_SHA = "38f17f4a45686a59a853bf62f0c840e228879e17"
CREATOR_PATH = "experiments/one/general_law_archive.py"
CREATOR_BLOB_SHA = "1f6e96092231a7c1a45ebc6322150c50f4eda70e"
READER_PATH = "experiments/one/authenticated_archive_envelope.py"
READER_BLOB_SHA = "bad59c45bbd60d99fe0ad594ab16e715a9d681c9"
RUNTIME_TREE_PATH = "experiments/one"
RUNTIME_TREE_SHA = "9245db9d6e762666a426d540f34e625242ea21bf"
CERTIFIED_STATUS = "CERTIFIED_FOR_GENESIS"

EXPECTED = {
    "candidate_sha": FROZEN_CANDIDATE_SHA,
    "creator_path": CREATOR_PATH,
    "creator_blob_sha": CREATOR_BLOB_SHA,
    "reader_path": READER_PATH,
    "reader_blob_sha": READER_BLOB_SHA,
    "runtime_tree_path": RUNTIME_TREE_PATH,
    "runtime_tree_sha": RUNTIME_TREE_SHA,
}


def _git(checkout: Path, spec: str) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), "rev-parse", spec], text=True).strip()


def _validate_checkout(checkout: Path) -> dict[str, str]:
    checkout = checkout.resolve()
    if not checkout.is_dir():
        raise RuntimeError("frozen candidate checkout is not a directory")
    observed = {
        "candidate_sha": _git(checkout, "HEAD"),
        "creator_blob_sha": _git(checkout, f"HEAD:{CREATOR_PATH}"),
        "reader_blob_sha": _git(checkout, f"HEAD:{READER_PATH}"),
        "runtime_tree_sha": _git(checkout, f"HEAD:{RUNTIME_TREE_PATH}"),
    }
    for field, value in observed.items():
        if value != EXPECTED[field]:
            raise RuntimeError(f"frozen candidate checkout {field} differs from preregistered identity")
    return observed


def validate_authority(payload: dict[str, Any], *, candidate_checkout: Path | None = None) -> dict[str, Any]:
    if payload.get("schema") != "cmpct-one-genesis-one-candidate-boundary-v1":
        raise RuntimeError("Genesis ONE candidate-boundary authority has wrong schema")
    if payload.get("experimental_version") != "ONE-G0.2":
        raise RuntimeError("Genesis ONE candidate-boundary authority is not ONE-G0.2")
    if payload.get("status") != CERTIFIED_STATUS:
        raise RuntimeError("Genesis ONE candidate-boundary authority is not CERTIFIED_FOR_GENESIS")
    if payload.get("production_eligible") is not True:
        raise RuntimeError("Genesis ONE candidate-boundary authority is not production_eligible")
    certified = payload.get("certified_candidate")
    if not isinstance(certified, dict):
        raise RuntimeError("Genesis ONE candidate-boundary authority is missing certified_candidate")
    for field, value in EXPECTED.items():
        if certified.get(field) != value:
            raise RuntimeError(f"Genesis ONE certified_candidate.{field} differs from frozen authority")
    for flag in ("genesis_inputs_executed", "comparison_executed", "scoring_executed", "winner_selected"):
        if payload.get(flag) is not False:
            raise RuntimeError(f"Genesis ONE certification must precede execution/scoring: {flag}")
    checkout_identity = _validate_checkout(candidate_checkout) if candidate_checkout is not None else None
    return {
        "schema": "cmpct-one-genesis-candidate-certification-validation-v1",
        "status": "GENESIS_CANDIDATE_CERTIFICATION_EXACT",
        "experimental_version": "ONE-G0.2",
        "certified_candidate": dict(EXPECTED),
        "candidate_checkout_verified": checkout_identity is not None,
        "candidate_checkout_identity": checkout_identity,
        "genesis_inputs_executed": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, default=AUTHORITY)
    parser.add_argument("--candidate-checkout", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.authority.read_text(encoding="utf-8"))
    result = validate_authority(payload, candidate_checkout=args.candidate_checkout)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
