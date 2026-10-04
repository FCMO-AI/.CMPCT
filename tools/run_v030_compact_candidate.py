#!/usr/bin/env python3
"""Run an existing v0.30 benchmark with the bounded compact-r24 candidate as product engine.

The benchmark source remains unchanged.  This launcher swaps only the imported release-product module
inside a fresh process, so the candidate can be falsified before mutating canonical product code.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: run_v030_compact_candidate.py BENCHMARK.py [args ...]")
    target = Path(sys.argv[1]).resolve()
    if not target.is_file():
        raise SystemExit(f"benchmark not found: {target}")

    import experiments
    from experiments import entropygraph_v030_release_product_compact_r24 as candidate

    # Benchmarks import this canonical module name.  Bind that name to the bounded candidate only in
    # this process; repository source and every other CI process remain untouched.
    sys.modules["experiments.entropygraph_v030_release_product"] = candidate
    experiments.entropygraph_v030_release_product = candidate

    sys.argv = [str(target), *sys.argv[2:]]
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
