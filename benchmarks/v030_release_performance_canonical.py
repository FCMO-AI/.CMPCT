from __future__ import annotations

"""Canonical-byte binding for the frozen v0.30 paired runtime gate.

Thresholds remain owned by ``v030_release_performance``. This adapter changes only the v0.30 worker to the
canonical revision-25 facade so timing/RSS evidence refers to the exact on-disk profiles that can ship.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_canonical.py"


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_canonical.py"
    result["release_facade"] = "cmpct-v030-r25-v1"
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
