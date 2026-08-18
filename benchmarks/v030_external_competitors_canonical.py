from __future__ import annotations

"""Release-product binding for the exact-tree v0.30 external competitor frontier."""

import argparse
import json
from pathlib import Path

from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release_product as CANON

B.CMPCT = CANON


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-external-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-external.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"aggregates": result["aggregates"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 external competitor gate failed")


if __name__ == "__main__":
    main()
