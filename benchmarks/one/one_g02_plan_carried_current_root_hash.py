"""ONE-G0.2 plan-carried current-root SHA-256 feasibility falsifier."""
from __future__ import annotations

import ctypes
import gc
import hashlib
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    CONTROLS,
    PRODUCTIVE,
    SIZES,
    Segment,
    SegmentStats,
    _oracle_plan,
    _plan_signature,
    _relation_cases,
)

ROUNDS = 101
MATURE_MIN = 16 * 1024
MATURE_PRODUCTIVE_MEDIAN_MAX = 1.05
MATURE_PRODUCTIVE_ROW_MAX = 1.15
FRAGMENTED_MATURE_MEDIAN_MAX = 1.10
CONTROL_MATURE_MEDIAN_MAX = 1.08


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-plan-hash-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_native_segment_plan_fusion_kernel.c"),
            str(here / "native" / "one_g02_plan_carried_current_root_hash.c"),
            "-lcrypto", "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    segment = c.one_g02_segment_plan_one_pass
    segment.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(SegmentStats),
    ]
    segment.restype = ctypes.c_int
    whole = c.one_g02_hash_target_whole
    whole.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8)]
    whole.restype = ctypes.c_int
    carried = c.one_g02_hash_current_from_plan
    carried.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8),
    ]
    carried.restype = ctypes.c_int
    return segment, whole, carried, td


def _snapshot(buf, count: int):
    return tuple(
        ("ref", int(buf[i].start), int(buf[i].length), b"")
        if int(buf[i].kind) == 0
        else ("surprise", 0, int(buf[i].length), b"")
        for i in range(count)
    )


def _time_pair(whole, carried, src, dst, n: int, seg_buf, seg_count: int):
    a = (ctypes.c_uint8 * 32)()
    b = (ctypes.c_uint8 * 32)()
    ws, cs = [], []
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for r in range(ROUNDS):
            order = (0, 1) if (r & 1) == 0 else (1, 0)
            for which in order:
                t0 = time.perf_counter_ns()
                if which == 0:
                    rc = whole(dst, n, a)
                    ws.append(time.perf_counter_ns() - t0)
                else:
                    rc = carried(src, n, dst, n, seg_buf, seg_count, b)
                    cs.append(time.perf_counter_ns() - t0)
                if rc != 0:
                    raise AssertionError(f"native SHA path failed: {rc}")
    finally:
        if enabled:
            gc.enable()
    return float(statistics.median(ws)), float(statistics.median(cs))


def run():
    segment, whole, carried, td = _build()
    rows = []
    mature_productive = []
    fragmented_mature = []
    control_mature = []
    semantic_ok = True
    oracle_ok = True
    try:
        for size in SIZES:
            for case in PRODUCTIVE + CONTROLS:
                source, target, _expected_enable, _expected_shift = _relation_cases(size)[case]
                src = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                stats = SegmentStats()
                if case in PRODUCTIVE:
                    if segment(src, dst, size, seg_buf, size, ctypes.byref(stats)) != 0:
                        raise AssertionError("native segment plan failed")
                    seg_count = int(stats.segments)
                    native_sig = _snapshot(seg_buf, seg_count)
                    oracle = _oracle_plan(source, target)
                    # Compare structural fields only; Surprise payload bytes are not materialized here.
                    oracle_sig = tuple((k, o, l, b"") for k, o, l, _p in oracle)
                    this_oracle = native_sig == oracle_sig
                else:
                    seg_count = 1
                    seg_buf[0].start = 0
                    seg_buf[0].length = size
                    seg_buf[0].kind = 1
                    this_oracle = True
                oracle_ok &= this_oracle
                if not this_oracle:
                    raise AssertionError("native plan diverged from oracle")

                w = (ctypes.c_uint8 * 32)()
                c = (ctypes.c_uint8 * 32)()
                if whole(dst, size, w) != 0 or carried(src, size, dst, size, seg_buf, seg_count, c) != 0:
                    raise AssertionError("native digest failed")
                expected = hashlib.sha256(target).digest()
                same = bytes(w) == bytes(c) == expected
                semantic_ok &= same
                if not same:
                    raise AssertionError("plan-carried current-root digest mismatch")

                whole_ns, carried_ns = _time_pair(whole, carried, src, dst, size, seg_buf, seg_count)
                ratio = carried_ns / whole_ns
                productive = case in PRODUCTIVE
                if size >= MATURE_MIN:
                    if productive:
                        mature_productive.append(ratio)
                        if case.startswith("fragmented"):
                            fragmented_mature.append(ratio)
                    else:
                        control_mature.append(ratio)
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": productive,
                    "segments": seg_count,
                    "digest_exact": same,
                    "plan_oracle_exact": this_oracle,
                    "whole_target_sha_median_ns": whole_ns,
                    "plan_carried_sha_median_ns": carried_ns,
                    "candidate_over_baseline": ratio,
                })

        prod_med = float(statistics.median(mature_productive))
        frag_med = float(statistics.median(fragmented_mature))
        ctl_med = float(statistics.median(control_mature))
        worst_prod = max(mature_productive)
        perf_ok = (
            prod_med <= MATURE_PRODUCTIVE_MEDIAN_MAX
            and worst_prod <= MATURE_PRODUCTIVE_ROW_MAX
            and frag_med <= FRAGMENTED_MATURE_MEDIAN_MAX
            and ctl_med <= CONTROL_MATURE_MEDIAN_MAX
        )
        if not semantic_ok or not oracle_ok:
            decision = "invalidate_plan_carried_current_root_hash"
        elif perf_ok:
            decision = "advance_plan_carried_current_root_hash_to_writer"
        else:
            decision = "reject_plan_carried_current_root_hash"
        return {
            "schema": "cmpct-one-g02-plan-carried-current-root-hash-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "semantic_gates_pass": semantic_ok,
            "native_plan_oracle_pass": oracle_ok,
            "mature_productive_median_ratio": prod_med,
            "mature_productive_worst_ratio": worst_prod,
            "fragmented_mature_median_ratio": frag_med,
            "control_mature_median_ratio": ctl_med,
            "decision": decision,
            "claim_boundary": "native current-root SHA carry feasibility over an already-built ONE segment plan; no full-writer, auth-tree, durability, arbitrary-discovery or comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_plan_carried_current_root_hash_to_writer" else 1)
