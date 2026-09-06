"""ONE-G0.2 exact parallel root-hash pair falsifier.

Frozen by ONE_G02_PARALLEL_ROOT_HASH_PAIR_PREREG_2026-09-06.md.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
MATURE_MIN = 16*1024
ROUNDS = 63
MATURE_MEDIAN_MAX = 0.75
MATURE_ROW_MAX = 0.90
ALL_ROW_MAX = 1.10
LARGE_MEDIAN_MAX = 0.65
MAX_COLD_NS = 1_000_000
MAX_WORKER_STACK = 64*1024


def _build_native():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-parallel-hash-")
    lib = Path(td.name) / "libhashpair.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "native" / "one_g02_parallel_root_hash_pair.c"),
            "-lcrypto", "-lpthread", "-o", str(lib),
        ],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    fn = c.one_g02_hash_pair
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
    ]
    fn.restype = ctypes.c_int
    stack_fn = c.one_g02_hash_pair_worker_stack_bytes
    stack_fn.argtypes = []
    stack_fn.restype = ctypes.c_size_t
    shutdown = c.one_g02_hash_pair_shutdown
    shutdown.argtypes = []
    shutdown.restype = ctypes.c_int
    return fn, stack_fn, shutdown, td


def _baseline(source: bytes, target: bytes):
    # Exact current shared-native writer preparation, including the existing
    # hexdigest -> raw conversion rather than a friendlier synthetic baseline.
    return (
        bytes.fromhex(sha256(source).hexdigest()),
        bytes.fromhex(sha256(target).hexdigest()),
    )


def _candidate(fn, src_arr, dst_arr, n: int, prev_out, curr_out):
    rc = fn(src_arr, n, dst_arr, n, prev_out, curr_out)
    if rc != 0:
        raise RuntimeError(f"parallel root hash pair failed: {rc}")
    return bytes(prev_out), bytes(curr_out)


def _pair_time(baseline_call, candidate_call):
    bs, cs = [], []
    bv = cv = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for i in range(ROUNDS):
            order = (False, True) if i % 2 == 0 else (True, False)
            for cand in order:
                t0 = time.perf_counter_ns()
                value = candidate_call() if cand else baseline_call()
                dt = time.perf_counter_ns() - t0
                if cand:
                    cs.append(dt); cv = value
                else:
                    bs.append(dt); bv = value
    finally:
        if was_enabled:
            gc.enable()
    return float(statistics.median(bs)), bv, float(statistics.median(cs)), cv


def _content_rows(size: int):
    rel = _relation_cases(size)
    shift_source, shift_target, *_ = rel["shift_plus1"]
    random_source, random_target, *_ = rel["independent_random"]
    repeated_source = bytes([0xA5]) * size
    repeated_target = bytes([0x5A]) * size
    pattern = bytes(range(251))
    periodic_source = (pattern * ((size + len(pattern)-1)//len(pattern)))[:size]
    periodic_target = periodic_source[1:] + periodic_source[:1]
    return (
        ("shift_plus1", shift_source, shift_target),
        ("independent_random", random_source, random_target),
        ("repeated_bytes", repeated_source, repeated_target),
        ("periodic_rotated", periodic_source, periodic_target),
    )


def run():
    fn, stack_fn, shutdown, td = _build_native()
    rows = []
    semantic_failures = 0
    try:
        worker_stack = int(stack_fn())

        # Fixed cold probe: 16 KiB shift_plus1. This is the first hash-pair call
        # in the process and therefore charges pthread_once + worker creation.
        cold_source, cold_target, *_ = _relation_cases(16*1024)["shift_plus1"]
        cold_src = (ctypes.c_uint8 * len(cold_source)).from_buffer_copy(cold_source)
        cold_dst = (ctypes.c_uint8 * len(cold_target)).from_buffer_copy(cold_target)
        cold_prev = (ctypes.c_uint8 * 32)(); cold_curr = (ctypes.c_uint8 * 32)()
        t0 = time.perf_counter_ns(); cold_baseline = _baseline(cold_source, cold_target); cold_baseline_ns = time.perf_counter_ns()-t0
        t0 = time.perf_counter_ns(); cold_candidate = _candidate(fn, cold_src, cold_dst, len(cold_source), cold_prev, cold_curr); cold_candidate_ns = time.perf_counter_ns()-t0
        if cold_candidate != cold_baseline:
            raise AssertionError("cold parallel hash pair changed canonical SHA-256")

        # Explicit warmup after the cold observation.
        _candidate(fn, cold_src, cold_dst, len(cold_source), cold_prev, cold_curr)

        for size in SIZES:
            for case, source, target in _content_rows(size):
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                prev_out = (ctypes.c_uint8 * 32)(); curr_out = (ctypes.c_uint8 * 32)()
                expected = _baseline(source, target)
                actual = _candidate(fn, src_arr, dst_arr, size, prev_out, curr_out)
                deterministic = actual == _candidate(fn, src_arr, dst_arr, size, prev_out, curr_out)
                exact = actual == expected and deterministic
                if not exact:
                    semantic_failures += 1
                    raise AssertionError(f"parallel root hash mismatch: {case}/{size}")

                bns, bv, cns, cv = _pair_time(
                    lambda s=source,t=target: _baseline(s,t),
                    lambda f=fn,sa=src_arr,da=dst_arr,n=size,po=prev_out,co=curr_out:
                        _candidate(f,sa,da,n,po,co),
                )
                if bv != cv or bv != expected:
                    semantic_failures += 1
                    raise AssertionError("timed root hash pair changed digest identity")
                ratio = cns / bns
                rows.append({
                    "bytes_per_root": size,
                    "total_input_bytes": 2*size,
                    "case": case,
                    "baseline_median_ns": bns,
                    "candidate_median_ns": cns,
                    "candidate_over_baseline": ratio,
                    "baseline_ns_per_input_byte": bns/(2*size),
                    "candidate_ns_per_input_byte": cns/(2*size),
                    "exact_previous_sha256": True,
                    "exact_current_sha256": True,
                })

        mature = [x["candidate_over_baseline"] for x in rows if x["bytes_per_root"] >= MATURE_MIN]
        large = [x["candidate_over_baseline"] for x in rows if x["bytes_per_root"] >= 128*1024]
        all_ratios = [x["candidate_over_baseline"] for x in rows]
        mature_med = float(statistics.median(mature))
        mature_worst = max(mature)
        large_med = float(statistics.median(large))
        all_worst = max(all_ratios)
        cold_ratio = cold_candidate_ns/cold_baseline_ns
        resource_ok = cold_candidate_ns <= MAX_COLD_NS and worker_stack <= MAX_WORKER_STACK
        perf_ok = (
            mature_med <= MATURE_MEDIAN_MAX
            and mature_worst <= MATURE_ROW_MAX
            and all_worst <= ALL_ROW_MAX
            and large_med <= LARGE_MEDIAN_MAX
        )
        semantic_ok = semantic_failures == 0
        if semantic_ok and perf_ok and resource_ok:
            decision = "advance_parallel_root_hash_pair_to_full_writer"
        elif semantic_ok and perf_ok:
            decision = "hold_parallel_root_hash_pair_for_shared_executor"
        else:
            decision = "reject_parallel_root_hash_pair"
        return {
            "schema": "cmpct-one-g02-parallel-root-hash-pair-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "worker_threads": 1,
            "worker_stack_bytes": worker_stack,
            "cold_baseline_ns": cold_baseline_ns,
            "cold_candidate_ns": cold_candidate_ns,
            "cold_candidate_over_baseline": cold_ratio,
            "semantic_failures": semantic_failures,
            "mature_median_ratio": mature_med,
            "mature_worst_ratio": mature_worst,
            "large_128_256k_median_ratio": large_med,
            "all_rows_worst_ratio": all_worst,
            "resource_guard_pass": resource_ok,
            "decision": decision,
            "claim_boundary": "exact encoder-side root-hash pair preparation only; no writer/reader/product/comparator authority",
            "rows": rows,
        }
    finally:
        shutdown()
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "reject_parallel_root_hash_pair" else 1)
