"""Release-product binding for the split historical-causality / canonical-product-parity ablation.

The underlying harness deliberately keeps its historical research imports because those exact bytes define the
immutable 137,501,815-byte v0.29 causality substrate. Only its *product parity* loader is rebound here to the
single release product front door.

Footnote: replacing the historical engines with the product API would destroy the benchmark's causal identity;
replacing only the product loader keeps both questions honest and non-interchangeable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_ablation_canonical as B
from experiments import entropygraph_v030_release_product as PRODUCT

B._load_product_module = lambda: PRODUCT


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["product_engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-product-ablation-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-product-ablation.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": result.get("gate"), "historical": result.get("historical_causality", {}).get("totals"), "product": result.get("canonical_product_parity", {}).get("totals")}, indent=2), flush=True)
    gate = result.get("gate", {})
    if isinstance(gate, dict) and gate.get("passed") is False:
        raise SystemExit("v0.30 product-bound ablation gate failed")


if __name__ == "__main__":
    main()
