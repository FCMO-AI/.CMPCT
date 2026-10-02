from __future__ import annotations

"""Unchanged release runtime gate with only the v0.30 fresh-process worker rebound to the bounded candidate."""
from pathlib import Path

from benchmarks import v030_release_performance_product as product_gate

product_gate.B.WORKER = Path(__file__).with_name("v030_perf_worker_compact_r24.py")

if __name__ == "__main__":
    product_gate.main()
