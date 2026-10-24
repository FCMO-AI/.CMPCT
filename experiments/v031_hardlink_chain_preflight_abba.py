#!/usr/bin/env python3
"""Same-host exact-index O1 ABBA: source-exact old vs memoized CMPCT preflight.

Historical module is loaded from its exact Git blob into the installed package's
namespace, preserving the public function and excluding CLI/process startup.
No release credit without inherited gates and independent cost accounting.
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

BASE_SHA = "3494a58e0393ba922e1071f14a5ffefc5dc944ca"
BASE_BLOB = "14df3f7492fc2db8b7dc7574868a333b4fe400c4"
SOURCE = "src/cmpct/validation.py"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def load_exact_reference(directory: Path):
    try:
        blob = git("rev-parse", f"{BASE_SHA}:{SOURCE}")
    except subprocess.CalledProcessError:
        subprocess.run(["git", "fetch", "-q", "--no-tags", "origin", BASE_SHA], check=True)
        blob = git("rev-parse", f"{BASE_SHA}:{SOURCE}")
    assert blob == BASE_BLOB, (blob, BASE_BLOB)
    code = subprocess.check_output(["git", "show", f"{BASE_SHA}:{SOURCE}"])
    # Source identity is Git's blob ID; SHA-256 below provides an independent
    # payload checksum for the published research receipt.
    path = directory / "baseline_validation.py"
    path.write_bytes(code)
    name = "cmpct._exact_o1_baseline_validation"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolves the temporary module here
    spec.loader.exec_module(module)
    return module.preflight_archive, {
        "source_commit": BASE_SHA,
        "source_blob": blob,
        "source_sha256": hashlib.sha256(code).hexdigest(),
    }


def main() -> None:
    source_head = git("rev-parse", "HEAD")
    candidate_blob = git("hash-object", SOURCE)
    assert candidate_blob != BASE_BLOB, "O1 requires an actual source mutation"
    with tempfile.TemporaryDirectory(prefix="cmpct-o1-abba-") as td:
        work = Path(td)
        ref_fn, base_ident = load_exact_reference(work)
        source_tree = work / "tree"
        source_tree.mkdir()
        (source_tree / "a00000000.bin").write_bytes(b"BOUNDARY-EXACT-OWNER" * 8)
        original = work / "source.cmpct"
        Builder(source_tree, workers=1, reproducible=True).build(original)
        result = {
            "court": "signed-preflight-hardlink-O1-source-exact-same-runner-ABBA",
            "source_head": source_head,
            "baseline": base_ident,
            "candidate_blob": candidate_blob,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "units": "nanoseconds for public preflight_archive invocation; excludes archive construction and process startup",
            "cases": {},
        }
        funcs = {"A_baseline": ref_fn, "B_candidate": candidate_preflight}
        for n in (512, 2048, 4096):
            for shape in ("chain", "star"):
                archive = work / f"{shape}-{n}.cmpct"
                identity = make_signed_alias_archive(original, archive, n, shape)
                for tag, fn in funcs.items():
                    assert fn(archive)["files"] == n + 1, (tag, n, shape)
                raw = {tag: [] for tag in funcs}
                # ABBA repetitions control drift in thermal/cache pressure.
                for _ in range(4):
                    for tag in ("A_baseline", "B_candidate", "B_candidate", "A_baseline"):
                        t0 = time.perf_counter_ns()
                        assert funcs[tag](archive)["files"] == n + 1
                        raw[tag].append(time.perf_counter_ns() - t0)
                med = {tag: statistics.median(values) for tag, values in raw.items()}
                key = f"{n}/{shape}"
                result["cases"][key] = {
                    "wire": identity,
                    "raw_ns": raw,
                    "median_ns": med,
                    "baseline_over_candidate": med["A_baseline"] / med["B_candidate"],
                }
                print(
                    f"O1_ABBA={key} A_baseline_ms={med['A_baseline']/1e6:.3f} "
                    f"B_candidate_ms={med['B_candidate']/1e6:.3f} "
                    f"speedup={med['A_baseline']/med['B_candidate']:.3f} "
                    f"same_archive_sha={identity['archive_sha256']}", flush=True
                )
        # Separate, explicitly instrumented allocation probe; do not put
        # tracemalloc into the product wall-time comparison above.
        archive = work / "chain-4096.cmpct"
        allocation = {}
        for tag in ("A_baseline", "B_candidate"):
            gc.collect()
            tracemalloc.start()
            assert funcs[tag](archive)["files"] == 4097
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            allocation[tag] = {"tracemalloc_peak_bytes": peak, "tracemalloc_residual_bytes": current}
        result["python_allocation_probe"] = allocation
        print("O1_ALLOCATION_PROBE=" + json.dumps(allocation, sort_keys=True), flush=True)
    dest = Path(os.environ.get("O1_ABBA_EVIDENCE", "hardlink-graph-o1-abba.json"))
    dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"O1_ABBA_RESULT={dest} EXACT_HEAD={source_head}", flush=True)


if __name__ == "__main__":
    main()
