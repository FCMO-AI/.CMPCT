"""ONE-G0.2 exact native Segment SWAR falsifier.

Frozen by ONE_G02_NATIVE_SEGMENT_SWAR_PREREG_2026-09-06.md.
"""
from __future__ import annotations

import ctypes
import gc
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import Segment, SegmentStats
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases

PERF_SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
VECTOR_SIZES = (1, 7, 8, 9, 31, 32, 63, 64, 65)
PRODUCTIVE = ("shift_plus1", "shift_plus1_damage_quarter", "fragmented_every96")
HOSTILE = ("all_ref", "all_surprise", "alternating", "every7", "every8", "random_mask")
ROUNDS = 63
MATURE_MIN = 16*1024
MATURE_MEDIAN_MAX = 0.55
MATURE_ROW_MAX = 0.85
SHIFT_MEDIAN_MAX = 0.45
ANY_ROW_MAX = 1.10


def _build(source_name: str, symbol: str):
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-segment-swar-")
    lib = Path(td.name) / (symbol + ".so")
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / source_name), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    fn = getattr(c, symbol)
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(SegmentStats),
    ]
    fn.restype = ctypes.c_int
    return fn, td


def _snapshot(buf, stats):
    return tuple((int(buf[i].kind), int(buf[i].start), int(buf[i].length))
                 for i in range(int(stats.segments)))


def _call(fn, src_arr, dst_arr, n, out):
    stats = SegmentStats()
    rc = fn(src_arr, dst_arr, n, out, max(1, n), ctypes.byref(stats))
    if rc != 0:
        raise RuntimeError(f"segment kernel failed: {rc}")
    return _snapshot(out, stats), int(stats.compared_target_bytes), int(stats.segments)


def _pair_time(a, b):
    aa, bb = [], []
    av = bv = None
    enabled = gc.isenabled()
    try:
        if enabled: gc.disable()
        for r in range(ROUNDS):
            order = (False, True) if r % 2 == 0 else (True, False)
            for cand in order:
                t0 = time.perf_counter_ns()
                value = b() if cand else a()
                dt = time.perf_counter_ns() - t0
                if cand: bb.append(dt); bv = value
                else: aa.append(dt); av = value
    finally:
        if enabled: gc.enable()
    return float(statistics.median(aa)), av, float(statistics.median(bb)), bv


def _masked_case(n: int, mode: str):
    rng = random.Random(0xC0DEC0DE ^ n ^ sum(map(ord, mode)))
    source = bytes(rng.randrange(256) for _ in range(n))
    target = bytearray(n)
    if n:
        # i=0 can never be Ref under canonical shifted semantics.
        target[0] = source[0] ^ 0x5A
    for i in range(1, n):
        if mode == "all_ref": ref = True
        elif mode == "all_surprise": ref = False
        elif mode == "alternating": ref = (i & 1) == 0
        elif mode == "every7": ref = ((i // 7) & 1) == 0
        elif mode == "every8": ref = ((i // 8) & 1) == 0
        elif mode == "random_mask": ref = bool(rng.getrandbits(1))
        else: raise KeyError(mode)
        if ref:
            target[i] = source[i-1]
        else:
            v = source[i-1] ^ 0xA5
            if v == source[i-1]: v ^= 1
            target[i] = v
    return source, bytes(target)


def _coverage_ok(plan, n):
    return all(length > 0 for _kind,_start,length in plan) and sum(length for _k,_s,length in plan) == n


def run():
    scalar, scalar_td = _build("one_g02_native_segment_plan_fusion_kernel.c", "one_g02_segment_plan_one_pass")
    swar, swar_td = _build("native/one_g02_segment_swar.c", "one_g02_segment_plan_swar")
    rows = []
    semantic_failures = 0
    try:
        # Untimed tiny/tail vectors across every hostile classification family.
        for n in VECTOR_SIZES:
            for case in HOSTILE:
                source, target = _masked_case(n, case)
                src = (ctypes.c_uint8 * max(1,n)).from_buffer_copy(source or b"\0")
                dst = (ctypes.c_uint8 * max(1,n)).from_buffer_copy(target or b"\0")
                aout = (Segment * max(1,n))(); bout = (Segment * max(1,n))()
                av = _call(scalar, src, dst, n, aout)
                bv = _call(swar, src, dst, n, bout)
                if av != bv or not _coverage_ok(bv[0], n):
                    semantic_failures += 1
                    raise AssertionError(f"tiny/tail Segment mismatch: {case}/{n}")

        for n in PERF_SIZES:
            repo_cases = _relation_cases(n)
            perf = [(name, *repo_cases[name][:2], True) for name in PRODUCTIVE]
            perf += [(name, *_masked_case(n, name), False) for name in HOSTILE]
            for case, source, target, productive in perf:
                src = (ctypes.c_uint8 * n).from_buffer_copy(source)
                dst = (ctypes.c_uint8 * n).from_buffer_copy(target)
                aout = (Segment * n)(); bout = (Segment * n)()
                av = _call(scalar, src, dst, n, aout)
                bv = _call(swar, src, dst, n, bout)
                if av != bv or not _coverage_ok(bv[0], n):
                    semantic_failures += 1
                    raise AssertionError(f"Segment mismatch: {case}/{n}")
                ans, at, bns, bt = _pair_time(
                    lambda f=scalar,s=src,d=dst,nn=n,o=aout: _call(f,s,d,nn,o),
                    lambda f=swar,s=src,d=dst,nn=n,o=bout: _call(f,s,d,nn,o),
                )
                if at != bt:
                    semantic_failures += 1
                    raise AssertionError("timed Segment stream changed")
                rows.append({
                    "relation_bytes": n,
                    "case": case,
                    "productive": productive,
                    "segments": bt[2],
                    "compared_target_bytes": bt[1],
                    "scalar_median_ns": ans,
                    "candidate_median_ns": bns,
                    "candidate_over_scalar": bns/ans,
                    "scalar_ns_per_input_byte": ans/n,
                    "candidate_ns_per_input_byte": bns/n,
                    "segment_stream_exact": True,
                })

        mature = [r["candidate_over_scalar"] for r in rows if r["productive"] and r["relation_bytes"] >= MATURE_MIN]
        shift = [r["candidate_over_scalar"] for r in rows if r["case"] == "shift_plus1" and r["relation_bytes"] >= MATURE_MIN]
        all_ratios = [r["candidate_over_scalar"] for r in rows]
        med = float(statistics.median(mature)); worst = max(mature)
        shift_med = float(statistics.median(shift)); any_worst = max(all_ratios)
        perf_ok = med <= MATURE_MEDIAN_MAX and worst <= MATURE_ROW_MAX and shift_med <= SHIFT_MEDIAN_MAX and any_worst <= ANY_ROW_MAX
        decision = "advance_segment_swar_to_full_writer" if semantic_failures == 0 and perf_ok else "reject_segment_swar"
        return {
            "schema": "cmpct-one-g02-native-segment-swar-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "semantic_failures": semantic_failures,
            "mature_productive_median_ratio": med,
            "mature_productive_worst_ratio": worst,
            "mature_shift_plus1_median_ratio": shift_med,
            "all_performance_rows_worst_ratio": any_worst,
            "heap_allocation_inside_candidate": False,
            "decision": decision,
            "claim_boundary": "exact native Segment microkernel only; no writer/reader/product/comparator authority",
            "rows": rows,
        }
    finally:
        scalar_td.cleanup(); swar_td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_segment_swar_to_full_writer" else 1)
