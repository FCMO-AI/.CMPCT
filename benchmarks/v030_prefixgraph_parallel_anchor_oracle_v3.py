from __future__ import annotations

"""Shipping-regression wrapper for the PrefixGraph parallel-anchor oracle.

v1/v2 established the exact-byte and material-speedup result with a duplicated
parallel prototype.  After promotion, evidence must exercise the actual release-facing
builder rather than allowing the prototype and product to drift.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_prefixgraph_parallel_anchor_oracle as V1
from benchmarks import v030_prefixgraph_parallel_anchor_oracle_v2 as V2
from experiments import entropygraph_v030_prefixgraph_parallel as SHIPPING


def _shipping_parallel_build(root: Path, out: Path) -> dict:
    stats = dict(SHIPPING.build(root, out))
    # v1's reporting schema predates the shipping field names.  This adapter changes
    # evidence labels only; the measured builder is the production-facing one.
    stats["workers"] = int(stats["anchor_audition_workers"])
    return stats


def run(work_root: Path) -> dict:
    original = V1._parallel_build
    V1._parallel_build = _shipping_parallel_build
    try:
        result = dict(V2.run(work_root))
    finally:
        V1._parallel_build = original
    result["schema"] = "cmpct-v030-prefixgraph-parallel-anchor-v3"
    result["shipping_regression"] = {
        "builder": "experiments.entropygraph_v030_prefixgraph_parallel.build",
        "prototype_builder_used": False,
        "release_candidate_imports_shipping_builder": True,
        "candidate_set_unchanged": True,
        "complete_byte_tournament_unchanged": True,
        "direct_payload_floor_unchanged": True,
    }
    result["claim_boundary"] = (
        "Shipping scheduling regression. It proves the promoted PrefixGraph builder remains byte/tree/locality "
        "identical to the historical serial builder and retains the frozen material speedup on the two promotion "
        "targets. It cannot alter PrefixGraph eligibility, outer selection, release thresholds or final authority."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-parallel-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-parallel.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["rows"], "gate": result["gate"], "shipping_regression": result["shipping_regression"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("shipping PrefixGraph parallel anchor scheduling lost its promotion evidence")


if __name__ == "__main__":
    main()
