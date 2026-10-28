from __future__ import annotations

"""Authoritative entrypoint for the frozen v0.30 15-workload gate.

The underlying ``v030_release_generalization`` module owns the immutable corpus identities, v0.29 row floors and
687,783-byte release hurdle.  This adapter binds that single-sourced harness to
``experiments.entropygraph_v030_release`` so the measurement includes the release-path G0-G4 streamed
publication rehabilitation rather than the earlier research builder.

The durable JSON embeds the exact release-critical content fingerprint plus a receipt-facing summary whose fields
are derived only from the already-measured totals/gate. This does not grant release credit by itself; it makes a
genuinely green artifact eligible to serve as evidence for a receipt on the same frozen fingerprint without
manual transcription or relying on an artifact filename/CI SHA.

Footnote: this file may change *which byte-identical implementation* is measured, but it must never modify the
frozen thresholds.  Any threshold change belongs in the underlying contract and requires an explicit policy
change, not a benchmark-adapter convenience.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_generalization as B
from experiments import entropygraph_v030_release as RELEASE
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

# The harness resolves RC globals at runtime; bind it once before any corpus work starts.
B.RC = RELEASE


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release.py"
    result["release_facade"] = "cmpct-v030-authoritative-integration-v1"
    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)
    result["candidate_fingerprint"] = fingerprint
    totals = result["totals"]
    gate = result["gate"]
    result["release_receipt_facts"] = {
        "accepted_v029_bytes": int(totals["accepted_v029_bytes"]),
        "saving_vs_v029_bytes": int(totals["saving_vs_v029_bytes"]),
        "workloads_improved": int(totals["workloads_improved"]),
        "workloads_regressed": int(totals["workloads_regressed"]),
        "max_selected_member_read_amplification": float(totals["max_selected_member_read_amplification"]),
        "exact_tree_identity": bool(gate["no_tree_drift"] and gate["product_tree_verified"]),
        "exact_v029_row_identity": bool(gate["no_v029_byte_drift"] and gate["exact_v029_aggregate"]),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_fingerprint": result["candidate_fingerprint"], "totals": result["totals"], "gate": result["gate"], "release_receipt_facts": result["release_receipt_facts"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 integrated compression/generalization gate failed")


if __name__ == "__main__":
    main()
