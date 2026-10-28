#!/usr/bin/env python3
"""J24K06 component-only source-exact ABBA: price mode2 prefix proof fairly.

This is a single-process representation-component cost court, NOT product/CLI
performance credit. Exact historical function is compiled from the frozen
parent source and exercises identical in-memory recipe/content/get_stream.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import time
import tracemalloc
import zipfile
import zlib

from cmpct.codec import range_vzip as candidate


def _baseline(parent: Path):
    path = parent / "src/cmpct/codec.py"
    code = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    fn = next(n for n in code.body if isinstance(n, ast.FunctionDef) and n.name == "range_vzip")
    ns = {"zipfile": zipfile}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), ns)
    return ns["range_vzip"]


def _compress(data: bytes):
    co = zlib.compressobj(6, zlib.DEFLATED, -15)
    return co.compress(data) + co.flush()


def _case(name: str):
    n = 1024 * 1024
    if name == "repeated":
        raws = [((b"alpha-beta-gamma-" * (n // 17 + 1))[:n]),
                ((b"delta-epsilon-" * (n // 14 + 1))[:n])]
    else:
        rnd = random.Random(12648430)
        raws = [rnd.randbytes(n), rnd.randbytes(n)]
    cp = [_compress(b) for b in raws]
    lit = [b"HEAD", b"BETWEEN", b"TAIL"]
    skeleton = b"".join(lit)
    truth = lit[0] + cp[0] + lit[1] + cp[1] + lit[2]
    recipe = [0, list(map(len, lit)),
              [[1, zipfile.ZIP_DEFLATED, 2, 1, len(cp[0]), 6],
               [2, zipfile.ZIP_DEFLATED, 2, 2, len(cp[1]), 6]],
              hashlib.sha256(truth).digest(), len(truth), zlib.crc32(truth)]
    contents = {0: skeleton, 1: raws[0], 2: raws[1]}

    def sources():
        stats = {"stream_calls": 0, "raw_bytes_recompressed": 0, "stream_bytes": 0}
        def blob(i):
            return contents[i]
        def stream(mode, i, level):
            assert mode == 2 and level == 6
            data = contents[i]
            result = _compress(data)
            stats["stream_calls"] += 1
            stats["raw_bytes_recompressed"] += len(data)
            stats["stream_bytes"] += len(result)
            return result
        return blob, stream, stats

    ranges = {
        "prefix": (0, 2),
        "overlap-first": (len(lit[0]) + len(cp[0]) // 2, 32),
        "suffix": (len(truth) - 2, 2),
    }
    return recipe, truth, sources, ranges, [len(x) for x in cp]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    base = _baseline(a.parent)
    all_results = []
    for kind in ("repeated", "incompressible"):
        recipe, truth, sources, ranges, sizes = _case(kind)
        for label, (begin, count) in ranges.items():
            rows = {"parent": [], "candidate": []}
            for _ in range(4):
                for name, impl in (("parent", base), ("candidate", candidate),
                                   ("candidate", candidate), ("parent", base)):
                    blob, stream, counters = sources()
                    cpu0, wall0 = time.process_time_ns(), time.perf_counter_ns()
                    got = impl(recipe, blob, stream, begin, count)
                    wall = time.perf_counter_ns() - wall0
                    cpu = time.process_time_ns() - cpu0
                    assert got == truth[begin:begin+count], (kind, label, name)
                    if label == "prefix":
                        assert counters["stream_calls"] == 0
                    if label == "suffix":
                        assert counters["stream_calls"] == (2 if name == "candidate" else 0)
                    if label == "overlap-first":
                        assert counters["stream_calls"] == 1
                    rows[name].append({"wall_ns": wall, "cpu_ns": cpu, **counters})
            # Use the same fully prepared data but a distinct instrument for
            # Python allocation peaks. These are not process RSS.
            peaks = {}
            for name, impl in (("parent", base), ("candidate", candidate)):
                blob, stream, _ = sources()
                tracemalloc.start()
                got = impl(recipe, blob, stream, begin, count)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                assert got == truth[begin:begin+count]
                peaks[name] = peak
            med = {}
            for arm in ("parent","candidate"):
                med[arm] = {
                    "wall_ns": statistics.median(x["wall_ns"] for x in rows[arm]),
                    "cpu_ns": statistics.median(x["cpu_ns"] for x in rows[arm]),
                    "peak_python_alloc_bytes": peaks[arm],
                }
            all_results.append({
                "case": kind, "range": label,
                "input_raw_bytes": 2 * 1024 * 1024,
                "stream_lengths": sizes,
                "returned_bytes": count,
                "candidate_over_parent_wall_ratio": med["candidate"]["wall_ns"] / max(1, med["parent"]["wall_ns"]),
                "median": med,
                "raw_observations": rows,
            })
    receipt = {
        "claim": "J24K06 component-only source-exact ABBA cost",
        "experiment_source_sha": os.environ.get("SOURCE_SHA", "local-unbound"),
        "engine": "installed candidate CMPCT codec versus frozen parent range_vzip AST",
        "not_product_credit": True,
        "not_rss": True,
        "cases": all_results,
        "decision": "CORRECTNESS_PASS_WITH_EXPLICIT_PREFIX_REGENERATION_COST",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for r in all_results:
        print("J24K06_COMPONENT_ABBA=" + json.dumps({
            "case": r["case"], "range": r["range"], "wall_ratio": r["candidate_over_parent_wall_ratio"],
            "median": r["median"],
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
