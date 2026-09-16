"""Release-product normalization for the operation-derived selective-read gate.

The underlying worker already imports ``entropygraph_v030_release_product``. This wrapper only makes provenance
and summary field names match the final release ledger; it does not change target selection, timing, locality
accounting or the frozen <=8x threshold.

The durable release JSON embeds the exact release-critical fingerprint and an explicit measured selective-read
fact for receipt binding. Neither field changes the operation-derived measurement or acceptance rule.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_selective_read_canonical as B
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    totals = dict(result["totals"])
    totals["max_member_read_amplification"] = totals["max_observed_member_read_amplification"]
    result["totals"] = totals
    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)
    result["candidate_fingerprint"] = fingerprint
    result["release_receipt_facts"] = {
        "selective_read_measured": bool(result.get("gate", {}).get("passed")),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-product-selective-read-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-product-selective-read.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_fingerprint": result["candidate_fingerprint"], "totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 release selective-read integrity/locality gate failed")


if __name__ == "__main__":
    main()
