"""ONE-G0.2 fixed-block segmentation + current-root SHA fusion falsifier."""
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
    _relation_cases,
)

ROUNDS = 101
MATURE_MIN = 16 * 1024
ALL_MEDIAN_MAX = 0.97
PRODUCTIVE_MEDIAN_MAX = 0.96
FRAGMENTED_MEDIAN_MAX = 0.98
ROW_MAX = 1.05


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-segment-hash-fusion-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_native_segment_plan_fusion_kernel.c"),
            str(here / "native" / "one_g02_plan_carried_current_root_hash.c"),
            str(here / "native" / "one_g02_segment_observation_root_hash_fusion.c"),
            "-lcrypto", "-o", str(lib),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(SegmentStats),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    baseline = c.one_g02_segment_then_hash_baseline
    candidate = c.one_g02_segment_and_hash_fixed_blocks
    baseline.argtypes = argtypes
    candidate.argtypes = argtypes
    baseline.restype = ctypes.c_int
    candidate.restype = ctypes.c_int
    return baseline, candidate, td


def _signature(buf, count: int):
    return tuple((int(buf[i].start), int(buf[i].length), int(buf[i].kind)) for i in range(count))


def _once(fn, src, dst, n: int, seg_buf, stats, digest):
    return fn(src, dst, n, seg_buf, n, ctypes.byref(stats), digest)


def _measure_pair(baseline, candidate, src, dst, n: int):
    bbuf = (Segment * n)()
    cbuf = (Segment * n)()
    bstats = SegmentStats()
    cstats = SegmentStats()
    bd = (ctypes.c_uint8 * 32)()
    cd = (ctypes.c_uint8 * 32)()

    # Untimed warmup.
    if _once(baseline, src, dst, n, bbuf, bstats, bd) != 0:
        raise AssertionError("baseline warmup failed")
    if _once(candidate, src, dst, n, cbuf, cstats, cd) != 0:
        raise AssertionError("candidate warmup failed")

    bs, cs = [], []
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for r in range(ROUNDS):
            order = (0, 1) if (r & 1) == 0 else (1, 0)
            for which in order:
                stats = SegmentStats()
                digest = (ctypes.c_uint8 * 32)()
                buf = bbuf if which == 0 else cbuf
                fn = baseline if which == 0 else candidate
                t0 = time.perf_counter_ns()
                rc = _once(fn, src, dst, n, buf, stats, digest)
                elapsed = time.perf_counter_ns() - t0
                if rc != 0:
                    raise AssertionError(f"timed native path failed: {rc}")
                (bs if which == 0 else cs).append(elapsed)
    finally:
        if enabled:
            gc.enable()
    return float(statistics.median(bs)), float(statistics.median(cs))


def run():
    baseline, candidate, td = _build()
    rows = []
    all_mature = []
    productive_mature = []
    fragmented_mature = []
    semantic_ok = True
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, _enabled, _shift = cases[case]
                src = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst = (ctypes.c_uint8 * size).from_buffer_copy(target)
                bbuf = (Segment * size)()
                cbuf = (Segment * size)()
                bs = SegmentStats()
                cs = SegmentStats()
                bd = (ctypes.c_uint8 * 32)()
                cd = (ctypes.c_uint8 * 32)()
                if _once(baseline, src, dst, size, bbuf, bs, bd) != 0:
                    raise AssertionError("baseline authority failed")
                if _once(candidate, src, dst, size, cbuf, cs, cd) != 0:
                    raise AssertionError("candidate authority failed")
                same_plan = (
                    int(bs.segments) == int(cs.segments)
                    and int(bs.compared_target_bytes) == int(cs.compared_target_bytes)
                    and _signature(bbuf, int(bs.segments)) == _signature(cbuf, int(cs.segments))
                )
                expected_digest = hashlib.sha256(target).digest()
                same_digest = bytes(bd) == bytes(cd) == expected_digest
                this_semantic = same_plan and same_digest
                semantic_ok &= this_semantic
                if not this_semantic:
                    raise AssertionError("fixed-block fusion changed Segment plan or root digest")

                bns, cns = _measure_pair(baseline, candidate, src, dst, size)
                ratio = cns / bns
                mature = size >= MATURE_MIN
                productive = case in PRODUCTIVE
                fragmented = case in ("fragmented_every96", "fragmented_every32")
                if mature:
                    all_mature.append(ratio)
                    if productive:
                        productive_mature.append(ratio)
                    if fragmented:
                        fragmented_mature.append(ratio)
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": productive,
                    "segments": int(bs.segments),
                    "plan_exact": same_plan,
                    "digest_exact": same_digest,
                    "baseline_segment_plus_sha_median_ns": bns,
                    "candidate_fixed_block_fused_median_ns": cns,
                    "candidate_over_baseline": ratio,
                })

        all_med = float(statistics.median(all_mature))
        prod_med = float(statistics.median(productive_mature))
        frag_med = float(statistics.median(fragmented_mature))
        worst = max(all_mature)
        perf_ok = (
            all_med <= ALL_MEDIAN_MAX
            and prod_med <= PRODUCTIVE_MEDIAN_MAX
            and frag_med <= FRAGMENTED_MEDIAN_MAX
            and worst <= ROW_MAX
        )
        if not semantic_ok:
            decision = "invalidate_segment_observation_root_hash_fusion"
        elif perf_ok:
            decision = "advance_segment_observation_root_hash_fusion"
        else:
            decision = "reject_segment_observation_root_hash_fusion"
        return {
            "schema": "cmpct-one-g02-segment-observation-root-hash-fusion-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "hash_block_bytes": 16 * 1024,
            "semantic_gates_pass": semantic_ok,
            "mature_all_median_ratio": all_med,
            "mature_productive_median_ratio": prod_med,
            "mature_fragmented_median_ratio": frag_med,
            "mature_worst_ratio": worst,
            "decision": decision,
            "claim_boundary": "native one-pass Segment construction plus current-root SHA observation only; no Program/writer/authenticated-placement/full-ingest/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_segment_observation_root_hash_fusion" else 1)
