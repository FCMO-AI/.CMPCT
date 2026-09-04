from __future__ import annotations

"""Release-product binding for the frozen v0.30 paired runtime gate.

Thresholds remain owned by ``v030_release_performance``. The fresh-process worker imports the one promoted
v0.30 product front door, so create/extract/RSS/selective evidence cannot accidentally benchmark an integration
checkpoint that the final CLI will not ship.

The paired gate also keeps its two evidence identities separate: accepted v0.29 remains in the frozen historical
content-tree domain, while canonical v0.30 is checked against the r24/r25 product user-tree semantic identity.
This changes neither the timed operation nor any threshold; it only prevents two different hashes of the same
source from being treated as though they were supposed to be byte-equal.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B
from experiments import entropygraph_v030_release_product as CANON

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_canonical.py"


def _canonical_expected_tree(engine: str, source: Path, historical_expected: str) -> str:
    if engine == "v030":
        return CANON.treehash(source)
    return historical_expected


B._expected_tree_for_engine = _canonical_expected_tree


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["worker"] = "benchmarks/v030_perf_worker_canonical.py"
    result["tree_identity_binding"] = {
        "v029": "frozen historical benchmark content-tree",
        "v030": "canonical r24/r25 product user-tree semantic identity",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-runtime-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-runtime.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 runtime promotion gate failed")


if __name__ == "__main__":
    main()
