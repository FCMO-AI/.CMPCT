from __future__ import annotations

"""Fresh-process adapter for the bounded compact-r24 product candidate."""
import runpy
import sys
from pathlib import Path

import experiments
from experiments import entropygraph_v030_release_product_compact_r24 as candidate

sys.modules["experiments.entropygraph_v030_release_product"] = candidate
experiments.entropygraph_v030_release_product = candidate

_target = Path(__file__).with_name("v030_perf_worker_canonical.py")
runpy.run_path(str(_target), run_name="__main__")
