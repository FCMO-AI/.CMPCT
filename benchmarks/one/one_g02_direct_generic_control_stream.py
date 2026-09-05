"""ONE-G0.2 direct generic Ref/Surprise control streaming vs transient segment plan."""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
CASES = ("shift_plus1_damage_quarter", "fragmented_every96")
ROUNDS = 101
MAX_ANY_RATIO = 1.03
MAX_FRAGMENTED_LARGE_RATIO = 0.90
MAX_MEDIAN_RATIO = 0.95


class Segment(ctypes.Structure):
    _fields_ = [("start", ctypes.c_uint32), ("length", ctypes.c_uint32), ("kind", ctypes.c_uint8)]


class Stats(ctypes.Structure):
    _fields_ = [
        ("compared_target_bytes", ctypes.c_uint64),
        ("segments", ctypes.c_uint64),
        ("emitted_bytes", ctypes.c_uint64),
        ("transient_plan_bytes", ctypes.c_uint64),
    ]


def _build():
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-direct-control-")
    lib = Path(td.name) / "lib.so"
    src = Path(__file__).with_name("one_g02_direct_control_stream_kernel.c")
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", str(src), "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    base = cdll.one_g02_plan_then_stream
    base.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                     ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                     ctypes.POINTER(Stats)]
    base.restype = ctypes.c_int
    direct = cdll.one_g02_direct_stream
    direct.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                       ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Stats)]
    direct.restype = ctypes.c_int
    return base, direct, td


def _u32le(v: int) -> bytes:
    return int(v).to_bytes(4, "little")


def _oracle(src: bytes, dst: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(dst)
    while i < n:
        ref = i > 0 and dst[i] == src[i-1]
        begin = i
        i += 1
        while i < n and ((i > 0 and dst[i] == src[i-1]) == ref):
            i += 1
        length = i - begin
        start = begin - 1 if ref else begin
        out.append(0 if ref else 1)
        out += _u32le(start)
        out += _u32le(length)
        if not ref:
            out += dst[begin:i]
    return bytes(out)


def run():
    base, direct, td = _build()
    rows = []
    exact_all = True
    timing_all = True
    ratios = []
    try:
        for n in SIZES:
            generated = _relation_cases(n)
            for case in CASES:
                src, dst, expected, shift = generated[case]
                assert expected and shift == 1
                a = (ctypes.c_uint8*n).from_buffer_copy(src)
                b = (ctypes.c_uint8*n).from_buffer_copy(dst)
                plan = (Segment*n)()
                out_cap = 10*n + 32
                ob = (ctypes.c_uint8*out_cap)()
                od = (ctypes.c_uint8*out_cap)()
                sb = Stats(); sd = Stats()
                rb = base(a, b, n, plan, n, ob, out_cap, ctypes.byref(sb))
                rd = direct(a, b, n, od, out_cap, ctypes.byref(sd))
                if rb != 0 or rd != 0:
                    raise AssertionError(f"native stream failure baseline={rb} direct={rd}")
                oracle = _oracle(src, dst)
                bb = bytes(ob[:int(sb.emitted_bytes)])
                db = bytes(od[:int(sd.emitted_bytes)])
                exact = bb == db == oracle
                accounting = (
                    int(sb.compared_target_bytes) == n == int(sd.compared_target_bytes)
                    and int(sb.segments) == int(sd.segments)
                    and int(sb.emitted_bytes) == int(sd.emitted_bytes) == len(oracle)
                    and int(sd.transient_plan_bytes) == 0
                    and int(sb.transient_plan_bytes) == int(sb.segments) * ctypes.sizeof(Segment)
                )
                before_src, before_dst = bytes(a), bytes(b)
                bsamp, dsamp = [], []
                for r in range(ROUNDS):
                    order = ((base, bsamp), (direct, dsamp))
                    if r & 1:
                        order = tuple(reversed(order))
                    for fn, samples in order:
                        t0 = time.perf_counter_ns()
                        if fn is base:
                            rc = fn(a, b, n, plan, n, ob, out_cap, ctypes.byref(sb))
                        else:
                            rc = fn(a, b, n, od, out_cap, ctypes.byref(sd))
                        samples.append(time.perf_counter_ns() - t0)
                        if rc != 0:
                            raise AssertionError("timed native stream failure")
                if bytes(a) != before_src or bytes(b) != before_dst:
                    raise AssertionError("input mutation")
                bm = float(statistics.median(bsamp)); dm = float(statistics.median(dsamp)); ratio = dm / bm
                row_timing = ratio <= MAX_ANY_RATIO and not (
                    case == "fragmented_every96" and n >= 16*1024 and ratio > MAX_FRAGMENTED_LARGE_RATIO
                )
                exact_all &= exact and accounting
                timing_all &= row_timing
                ratios.append(ratio)
                rows.append({
                    "relation_bytes": n,
                    "case": case,
                    "segments": int(sb.segments),
                    "emitted_bytes": int(sb.emitted_bytes),
                    "baseline_transient_plan_bytes": int(sb.transient_plan_bytes),
                    "candidate_transient_plan_bytes": int(sd.transient_plan_bytes),
                    "baseline_compared_target_bytes": int(sb.compared_target_bytes),
                    "candidate_compared_target_bytes": int(sd.compared_target_bytes),
                    "exact_control_stream": exact,
                    "accounting_exact": accounting,
                    "baseline_median_ns": bm,
                    "candidate_median_ns": dm,
                    "candidate_over_baseline_elapsed": ratio,
                    "timing_pass": row_timing,
                })
        median_ratio = float(statistics.median(ratios))
        passed = exact_all and timing_all and median_ratio <= MAX_MEDIAN_RATIO
        return {
            "schema": "cmpct-one-g02-direct-generic-control-stream-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "median_candidate_over_baseline_elapsed": median_ratio,
            "decision": "advance_direct_generic_control_streaming" if passed else "hold_direct_generic_control_streaming",
            "claim_boundary": "native writer-side generic Ref/Surprise control emission only; relation admission, production wire, auth, discovery and comparator authority excluded",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_direct_generic_control_streaming" else 1)
