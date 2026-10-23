#!/usr/bin/env python3
"""Source-exact attribution of bounded Deflate authentication cost.

All inputs are real revision-24 archives. The 'preflight_disabled' mode is a
scientific unsafe historical control only: it suppresses the newly introduced
verifier on unmodified source, without touching any benchmark comparator or
changing the shipping product. All resulting ZIP bytes must match exactly.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_v031_deflate_export_verified import _archive
from cmpct.reader import CMPCT


def _sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _test_case(parent, name, raw, aliases):
    path = parent / f"{name}.cmpct"
    _archive(path, raw, names=tuple(f"member_{i:03d}.txt" for i in range(aliases)))
    results = {"profile": name, "raw_bytes": len(raw), "aliases": aliases, "trials": []}
    with CMPCT(path) as archive:
        method = archive._verify_direct_deflate_blob
        outs = {}
        # In an ABBA crossover, opening and creating the archive are held outside
        # the exported product timing; this is an attribute-cost study, not a release gate.
        for label in "ABBA" * 4:
            enabled = label == "A"
            if not enabled:
                archive._verify_direct_deflate_blob = lambda _idx: None
            else:
                archive._verify_direct_deflate_blob = method
            out = parent / f"{name}-{label}.zip"
            before_cpu = time.process_time_ns()
            before_wall = time.perf_counter_ns()
            archive.export_zip(out)
            elapsed_wall = time.perf_counter_ns() - before_wall
            elapsed_cpu = time.process_time_ns() - before_cpu
            # Hashing and independent ZIP decode are outside export timing.
            digest = _sha_file(out)
            if outs and digest != next(iter(outs.values())):
                raise AssertionError("guard changed valid ZIP artifact bytes")
            outs[label] = digest
            with zipfile.ZipFile(out) as z:
                assert len(z.namelist()) == aliases
                assert z.read(z.namelist()[0]) == raw
            results["trials"].append({
                "guard": enabled,
                "wall_ms": elapsed_wall / 1e6,
                "cpu_ms": elapsed_cpu / 1e6,
                "zip_bytes": out.stat().st_size,
                "zip_sha256": digest,
            })
        archive._verify_direct_deflate_blob = method
        # The guard retains <=64 KiB decoded blocks, never a raw member-sized buffer.
        out = parent / f"{name}-bounded.zip"
        tracemalloc.start()
        try:
            archive.export_zip(out)
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        results["guard_peak_python_alloc_B"] = peak
        assert _sha_file(out) == next(iter(outs.values()))
    a = [r for r in results["trials"] if r["guard"]]
    b = [r for r in results["trials"] if not r["guard"]]
    results["median_guard_wall_ms"] = statistics.median(r["wall_ms"] for r in a)
    results["median_unsafe_copy_wall_ms"] = statistics.median(r["wall_ms"] for r in b)
    results["incremental_guard_wall_ms"] = results["median_guard_wall_ms"] - results["median_unsafe_copy_wall_ms"]
    results["median_guard_cpu_ms"] = statistics.median(r["cpu_ms"] for r in a)
    results["median_unsafe_copy_cpu_ms"] = statistics.median(r["cpu_ms"] for r in b)
    return results


def run():
    rng = random.Random(20261023)
    with tempfile.TemporaryDirectory(prefix="cmpct-direct-deflate-attribution-") as d:
        root = Path(d)
        cases = [
            ("tiny_text", b"human-readable repeated bytes\n" * 256, 1),
            ("shared_text", b"several logical aliases share one physical stream\n" * 8192, 16),
            ("zeros_32m", b"\0" * (32 * 1024 * 1024), 1),
            ("random_4m", rng.randbytes(4 * 1024 * 1024), 1),
        ]
        rows = [_test_case(root, *c) for c in cases]
        result = {
            "schema": "cmpct-v031-deflate-zip-authentication-cost-v1",
            "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "reader_blob": subprocess.check_output(["git", "hash-object", "src/cmpct/reader.py"], text=True).strip(),
            "method": "ABBA alternating on same loaded true-r24 source; suppress only guard as unsafe attribution control",
            "claim": "micro/product-path cost attribution only; not an exact-semantics release benchmark",
            "results": rows,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    out = Path("deflate-evidence")
    out.mkdir(exist_ok=True)
    (out / "cost-attribution.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    run()
