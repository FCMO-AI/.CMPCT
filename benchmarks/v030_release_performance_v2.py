from __future__ import annotations

"""Final-authority binding for the frozen v0.30 paired runtime promotion gate.

The base runtime harness owns the exact workloads, balanced ordering and immutable 1.10 / 1.25 thresholds.
This adapter only points the fresh-process v0.30 worker at ``entropygraph_v030_authoritative`` so the measured
implementation includes shared graph construction and memory-bounded PrefixGraph admission.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_v2.py"


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_authoritative.py"
    result["release_facade"] = "cmpct-v030-authoritative-v2"
    result["worker"] = "benchmarks/v030_perf_worker_v2.py"
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
        raise SystemExit("v0.30 authoritative-v2 runtime promotion gate failed")


if __name__ == "__main__":
    main()
