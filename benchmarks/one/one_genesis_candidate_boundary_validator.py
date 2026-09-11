from __future__ import annotations

"""Structural validator for the preregistered ONE Genesis candidate boundary.

It deliberately does not select a candidate. It rejects receipts that try to promote one
of the explicitly ineligible mechanism/reference surfaces, omit required product claims,
or imply that Genesis scoring already happened before a candidate boundary was sealed.
"""

import argparse
import json
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path("benchmarks/one/genesis_one_candidate_boundary_v1.json")

REQUIRED_PRODUCT_FLAGS = (
    "general_arbitrary_tree",
    "automatic_law_plus_surprise",
    "complete_persistent_bytes_counted",
    "whole_reconstruction_exact",
    "reader_discovery",
    "hidden_legacy_codec",
    "same_resource_boundary_as_comparators",
    "candidate_sha_frozen_before_execution",
)


def validate_candidate_receipt(receipt: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema") != "cmpct-one-genesis-one-candidate-boundary-v1":
        raise RuntimeError("unexpected ONE candidate-boundary authority schema")
    if manifest.get("experimental_version") != "ONE-G0.2":
        raise RuntimeError("candidate-boundary authority is not ONE-G0.2")

    surface = receipt.get("surface")
    if not isinstance(surface, str) or not surface:
        raise RuntimeError("candidate receipt must identify one complete product surface")
    for row in manifest.get("known_surfaces", {}).values():
        if row.get("path") == surface and row.get("genesis_general_candidate_eligible_alone") is False:
            raise RuntimeError(f"ineligible standalone ONE Genesis surface: {surface}")

    sha = receipt.get("candidate_sha")
    if not isinstance(sha, str) or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise RuntimeError("candidate receipt requires a lowercase 40-hex candidate_sha")

    claims = receipt.get("product_claims")
    if not isinstance(claims, dict):
        raise RuntimeError("candidate receipt requires product_claims")
    missing = [name for name in REQUIRED_PRODUCT_FLAGS if name not in claims]
    if missing:
        raise RuntimeError(f"candidate receipt is missing product claims: {missing}")
    required_true = (
        "general_arbitrary_tree",
        "automatic_law_plus_surprise",
        "complete_persistent_bytes_counted",
        "whole_reconstruction_exact",
        "same_resource_boundary_as_comparators",
        "candidate_sha_frozen_before_execution",
    )
    for name in required_true:
        if claims[name] is not True:
            raise RuntimeError(f"candidate product claim must be true: {name}")
    if claims["reader_discovery"] is not False:
        raise RuntimeError("ONE reader discovery is forbidden")
    if claims["hidden_legacy_codec"] is not False:
        raise RuntimeError("hidden legacy codec/mechanism dispatch is forbidden")

    metrics = receipt.get("metric_families")
    if not isinstance(metrics, dict):
        raise RuntimeError("candidate receipt requires metric_families")
    for name in ("stored_bytes", "creation", "whole_read", "selective_access", "semantics", "reader_burden"):
        if name not in metrics:
            raise RuntimeError(f"candidate boundary omits metric family: {name}")
        if metrics[name] not in ("measured", "unavailable"):
            raise RuntimeError(f"candidate metric family must be measured or unavailable: {name}")
    for name in ("stored_bytes", "creation", "whole_read", "semantics"):
        if metrics[name] != "measured":
            raise RuntimeError(f"candidate product boundary must measure {name}")

    if receipt.get("comparison_executed") is not False or receipt.get("scoring_executed") is not False:
        raise RuntimeError("candidate boundary certification must precede Genesis comparison/scoring")
    if receipt.get("winner_selected") is not False:
        raise RuntimeError("candidate boundary certification cannot select a winner")

    return {
        "schema": "cmpct-one-genesis-one-candidate-boundary-validation-v1",
        "status": "CANDIDATE_BOUNDARY_STRUCTURALLY_ELIGIBLE",
        "candidate_sha": sha,
        "surface": surface,
        "claim_boundary": "structural eligibility only; does not prove performance or execute Genesis inputs",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--authority", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.authority.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result = validate_candidate_receipt(receipt, manifest)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
