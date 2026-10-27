#!/usr/bin/env python3
"""J24B05 same-source preflight ABBA: exact #342 memoized owner vs size-checked child.

Only authentic successful signed archives enter timing. Historical source is
loaded from its exact Git object, not a copy inferred from chat or current HEAD.
"""
from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

from cmpct.builder import Builder
from cmpct.validation import preflight_archive as candidate_preflight
from v031_hardlink_chain_preflight_o0 import make_signed_alias_archive

BASE_SHA = "a480d7ae2f1480f15e73eda2b04e48b1a75e66b1"
BASE_BLOB = "6c629ab504504a50fbbf8d1ae9e4cf0b31757a05"
SOURCE = "src/cmpct/validation.py"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def load_historical(directory: Path):
    observed = git("rev-parse", f"{BASE_SHA}:{SOURCE}")
    assert observed == BASE_BLOB, (observed, BASE_BLOB)
    payload = subprocess.check_output(["git", "show", f"{BASE_SHA}:{SOURCE}"])
    path = directory / "historical_validation.py"
    path.write_bytes(payload)
    name = "cmpct._j24b05_parent_validation"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.preflight_archive, {
        "commit": BASE_SHA,
        "blob": observed,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> None:
    head = git("rev-parse", "HEAD")
    candidate_blob = git("hash-object", SOURCE)
    assert candidate_blob != BASE_BLOB
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b05-") as temp:
        work = Path(temp)
        historical, base_identity = load_historical(work)
        source_dir = work / "owner-tree"
        source_dir.mkdir()
        (source_dir / "a00000000.bin").write_bytes(b"REAL-TERMINAL-OWNER" * 16)
        original = work / "original.cmpct"
        Builder(source_dir, workers=1, reproducible=True).build(original)
        pairs = {"A_parent": historical, "B_child": candidate_preflight}
        records = {
            "court": "J24B05 exact-parent-vs-child signed-r24 preflight ABBA",
            "head": head,
            "candidate_blob": candidate_blob,
            "historical": base_identity,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "semantics": "same authenticated archive; preflight_archive only; excludes Builder, startup and materialization",
            "cases": {},
        }
        for n in (512, 2048, 4096):
            for shape in ("chain", "star"):
                archive = work / f"{n}-{shape}.cmpct"
                wire = make_signed_alias_archive(original, archive, n, shape)
                for label, fn in pairs.items():
                    assert fn(archive)["files"] == n + 1, (label, n, shape)
                samples = {label: [] for label in pairs}
                for _ in range(4):
                    for label in ("A_parent", "B_child", "B_child", "A_parent"):
                        start = time.perf_counter_ns()
                        assert pairs[label](archive)["files"] == n + 1
                        samples[label].append(time.perf_counter_ns() - start)
                med = {name: statistics.median(s) for name, s in samples.items()}
                records["cases"][f"{n}/{shape}"] = {
                    "wire": wire,
                    "raw_ns": samples,
                    "median_ns": med,
                    "candidate_over_parent": med["B_child"] / med["A_parent"],
                    "candidate_minus_parent_ms": (med["B_child"] - med["A_parent"]) / 1e6,
                }
                print(
                    f"J24B05_ABBA={n}/{shape} parent={med['A_parent']/1e6:.3f}ms "
                    f"child={med['B_child']/1e6:.3f}ms "
                    f"ratio={med['B_child']/med['A_parent']:.3f} "
                    f"archive_sha256={wire['archive_sha256']}", flush=True
                )
        archive = work / "4096-chain.cmpct"
        allocation = {}
        for label, fn in pairs.items():
            gc.collect()
            tracemalloc.start()
            assert fn(archive)["files"] == 4097
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            allocation[label] = {"peak_bytes": peak, "residual_bytes": current}
        records["python_allocation_probe"] = allocation
        print("J24B05_ALLOCATIONS=" + json.dumps(allocation, sort_keys=True), flush=True)
    result = Path(os.environ.get("J24B05_ABBA_EVIDENCE", "j24b05-abba.json"))
    result.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"J24B05_RESULT={result} HEAD={head}", flush=True)


if __name__ == "__main__":
    main()
