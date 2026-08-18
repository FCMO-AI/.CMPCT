from __future__ import annotations

"""Release-product binding for the exact-tree v0.30 external competitor frontier.

The public competitor corpus is regular-file-only and its frozen source fingerprint predates the richer r25
filesystem-manifest identity. CMPCT build/verify/extract therefore uses the promoted product API, while the
cross-format extracted-tree comparator intentionally remains the historical regular-file content fingerprint
used to freeze all 15 inputs.

Footnote: comparing ZIP/7z/tar/ZPAQ with the r25 metadata hash would be false equivalence because those formats do
not all preserve the same metadata semantics. The size frontier is credited only after exact regular-file content
round-trip, while CMPCT's richer filesystem fidelity is separately covered by canonical product parity tests.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_release as HISTORICAL_TREE

B.CMPCT = CANON
B._tree = lambda root: HISTORICAL_TREE.treehash(root)


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["source_tree_identity"] = "historical-regular-file-content-v0.29-frozen"
    result["product_fidelity_evidence"] = "canonical product parity / native portability lanes"
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
