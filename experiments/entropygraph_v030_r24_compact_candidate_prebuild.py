from __future__ import annotations

"""Candidate-owned r24 prebuild worker for the compact-policy product replication.

The historical #209 launcher rebound the candidate only in its parent interpreter, while shipping
r24 bytes are produced by a fresh child that imported canonical product source. This worker makes
candidate identity explicit at that byte-owning boundary without changing canonical release code.
"""

import argparse
import json
from pathlib import Path


def _worker(root: Path, out: Path) -> None:
    from experiments import entropygraph_v030_release_product_compact_r24 as product

    stats = product._locality_bounded_r24_build(Path(root), Path(out))
    print(
        json.dumps(
            {"schema": "cmpct-v030-r24-prebuild-process-v1", "stats": stats},
            separators=(",", ":"),
            default=str,
        )
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--root", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    if not a.worker or a.root is None or a.out is None:
        p.error("worker mode requires --root and --out")
    _worker(a.root, a.out)


if __name__ == "__main__":
    main()
