from __future__ import annotations

"""Release-product binding for the frozen v0.30 paired runtime gate.

Thresholds remain owned by ``v030_release_performance``. The fresh-process worker imports the one promoted
v0.30 product front door, so create/extract/RSS/selective evidence cannot accidentally benchmark an integration
checkpoint that the final CLI will not ship.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_canonical.py"


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["worker"] = "benchmarks/v030_perf_worker_canonical.py"
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
