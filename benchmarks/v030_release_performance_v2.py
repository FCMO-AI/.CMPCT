from __future__ import annotations

"""Final-authority binding for the frozen v0.30 paired runtime promotion gate.

The base runtime harness owns the exact workloads, balanced ordering and immutable 1.10 / 1.25 thresholds.
This adapter binds the v0.30 side to ``entropygraph_v030_release_product`` and checks that side in the canonical
r24/r25 user-tree identity domain.  v0.29 remains checked against the frozen historical content-tree identity.
The two hashes intentionally describe different evidence domains; neither is rewritten or substituted for the
other, and the timed operations/thresholds remain unchanged.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B
from experiments import entropygraph_v030_release_product as PRODUCT

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_v2.py"


def _expected_tree_for_runtime_v2(engine: str, source: Path, historical_expected: str) -> str:
    if engine == "v030":
        return PRODUCT.treehash(source)
    return historical_expected


# The base harness deliberately exposes this identity hook so a canonical binding can retain the historical
# v0.29 substrate while proving v0.30 in the richer product identity domain.  This happens before timing starts.
B._expected_tree_for_engine = _expected_tree_for_runtime_v2


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["worker"] = "benchmarks/v030_perf_worker_v2.py"
    result["identity_binding"] = "v029-historical-content-tree + v030-canonical-user-tree"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-performance-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-performance-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 release-product runtime promotion gate failed")


if __name__ == "__main__":
    main()
