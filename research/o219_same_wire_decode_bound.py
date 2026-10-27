#!/usr/bin/env python3
"""O219: same-wire index decode + O218 strict scan ceiling, NOT a Reader benchmark.
Frozen question: docs/v031-research/2026-10-27-o219-index-decode-bound-prereg.md.
"""
import argparse
import gc
import hashlib
import json
import random
import statistics
import sys
import tempfile
import time
from pathlib import Path

import msgpack
from o218_native_validator_oracle import fixture, load_native, strong_python, o216_like_python

HERE = Path(__file__).resolve().parent
PROFILES = [(65536,1), (65536,65536), (262144,1), (262144,262144)]
NAMES = ["o216_like", "native", "strong_py"]

def clock():
    return time.perf_counter_ns(), time.process_time_ns()

def observe(payload, declared, op, name, n, unique, repeat):
    t0, c0 = clock()
    parsed = msgpack.unpackb(payload, raw=False, strict_map_key=False)
    t1, c1 = clock()
    answer = op(parsed["r"], parsed["b"], declared)
    t2, c2 = clock()
    if answer is not True:
        raise AssertionError("valid same-wire input rejected: " + name)
    return {
        "n": n, "unique": unique, "repeat": repeat, "method": name,
        "decode_wall_ns": t1-t0, "decode_cpu_ns": c1-c0,
        "check_wall_ns": t2-t1, "check_cpu_ns": c2-c1,
        "total_wall_ns": t2-t0, "total_cpu_ns": c2-c0,
    }

def run(path, repeats):
    if repeats < 8 or repeats > 100:
        raise ValueError("repeats must be 8..100")
    cases, samples = [], []
    with tempfile.TemporaryDirectory(prefix="o219-") as folder:
        native, compiler = load_native(folder)
        methods = {"strong_py": strong_python,
                   "o216_like": o216_like_python,
                   "native": native.scan_refs}
        old_gc = gc.isenabled()
        if old_gc:
            gc.disable()
        try:
            for n, unique in PROFILES:
                refs, blobs, declared, wire_bytes, wire_sha = fixture(n, unique)
                payload = msgpack.packb({"r": refs, "b": blobs}, use_bin_type=True)
                if len(payload) != wire_bytes or hashlib.sha256(payload).hexdigest() != wire_sha:
                    raise AssertionError("original O218 wire identity changed")
                for name, op in methods.items():
                    if op(refs, blobs, declared) is not True:
                        raise AssertionError(name + " rejected direct control")
                cases.append({"n": n, "unique": unique, "wire_bytes": len(payload),
                              "wire_sha256": wire_sha, "declared": declared})
                # Same messagepack wire. Warm every arm; randomize paired order per repeat.
                for method, op in methods.items():
                    for _ in range(2):
                        observe(payload, declared, op, method, n, unique, -1)
                rng = random.Random(219*1000000+n+unique)
                for repeat in range(repeats):
                    order = list(NAMES)
                    rng.shuffle(order)
                    for name in order:
                        samples.append(observe(payload, declared, methods[name],
                                               name, n, unique, repeat))
        finally:
            if old_gc:
                gc.enable()
    summary = []
    for n, unique in PROFILES:
        med = {}
        for name in NAMES:
            rows = [s for s in samples if (s["n"], s["unique"], s["method"]) == (n, unique, name)]
            if len(rows) != repeats:
                raise AssertionError("missing paired samples")
            med[name] = {key: statistics.median(r[key] for r in rows)/1e6
                         for key in ("total_wall_ns","total_cpu_ns","decode_wall_ns",
                                     "check_wall_ns")}
        ratio = med["o216_like"]["total_wall_ns"] / med["native"]["total_wall_ns"]
        decode_fraction = (med["o216_like"]["decode_wall_ns"] /
                           med["o216_like"]["total_wall_ns"])
        summary.append({"n":n,"unique":unique,"methods":med,
                        "total_wall_ratio_py_over_native":ratio,
                        "baseline_decode_fraction":decode_fraction})
    decision = ("WHOLE_INDEX_ORACLE_AT_LEAST_2X"
                if all(s["total_wall_ratio_py_over_native"] >= 2.0 for s in summary)
                else "WHOLE_INDEX_ORACLE_BELOW_2X")
    result = {"schema":"O219_index_decode_v1", "tier":"same-wire in-process decode+admission oracle",
              "product_credit":False, "decision":decision, "python":sys.version,
              "source_pr":577, "base_sha":"6372e780be99a31f5ea21b7a3c74fde92cf0bc45",
              "prereg_commit":"c76e0b2f5b54ecbaffafa0adf0e14759b2c52a37",
              "o218_c_sha256":hashlib.sha256((HERE/"o218_fastscan.c").read_bytes()).hexdigest(),
              "o218_python_sha256":hashlib.sha256((HERE/"o218_native_validator_oracle.py").read_bytes()).hexdigest(),
              "compiler":compiler,"repeats":repeats,"cases":cases,
              "samples":samples,"summary":summary,
              "limitations":["no full Reader open, data-record IO, mmap, decompression or process startup",
                             "o216_like is a proxy, not O216 source-level full-product comparator",
                             "native wheel/ABI/platform and RSS charges excluded",
                             "GC disabled equally for all measured methods"]}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps({"decision":decision,"summary":summary,
                      "sample_count":len(samples)},sort_keys=True))
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--repeats", type=int, default=17)
    args = p.parse_args()
    run(args.output,args.repeats)
