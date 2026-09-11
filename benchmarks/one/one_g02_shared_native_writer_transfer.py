"""ONE-G0.2 shared native writer transfer falsifier.

Frozen by ONE_G02_SHARED_NATIVE_WRITER_TRANSFER_PREREG_2026-09-06.md.
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

import benchmarks.one.one_g02_root_hash_writer_plan_direct_wire as v1
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    CONTROLS, PRODUCTIVE, ROUNDS, SIZES, Segment, SegmentStats,
    _build_native, _native_plan, _oracle_plan, _plan_signature, _relation_cases,
)
from benchmarks.one.one_g02_root_hash_writer_plan_direct_wire_v2 import _candidate_once_v2
from experiments.one.wire import WireStats, decode_program
from experiments.one.vm import evaluate

MATURE_MIN = 16 * 1024
PRODUCTIVE_MEDIAN_MAX = 0.80
PRODUCTIVE_GOOD_MAX = 0.90
MIN_PRODUCTIVE_GOOD = 15
PRODUCTIVE_ROW_MAX = 1.03
CONTROL_MEDIAN_MAX = 1.03
CONTROL_ROW_MAX = 1.08


def _build_writer_native():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-native-writer-")
    lib = Path(td.name) / "libnativewriter.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "native" / "one_g02_shared_native_writer.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    fn = c.one_g02_native_writer
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
        ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_size_t),
    ]
    fn.restype = ctypes.c_int
    free_fn = c.one_g02_native_writer_free
    free_fn.argtypes = [ctypes.c_void_p]
    free_fn.restype = None
    return fn, free_fn, td


def _digest_array(hex_digest: str):
    raw = bytes.fromhex(hex_digest)
    return (ctypes.c_uint8 * 32).from_buffer_copy(raw)


def _candidate_once_native(writer_fn, free_fn, admission_fn, segment_fn,
                           source, target, src_arr, dst_arr, seg_buf):
    # Keep root hashing charged exactly as in V2. bytes.fromhex is additionally
    # charged here because the native ABI consumes the already-defined raw digest.
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    pd = _digest_array(previous_digest)
    cd = _digest_array(current_digest)

    result, gate_reads, gate_used, enabled = v1._admit(admission_fn, src_arr, dst_arr, len(source))
    stats = SegmentStats()
    if enabled:
        rc = segment_fn(src_arr, dst_arr, len(source), seg_buf, len(source), ctypes.byref(stats))
        if rc != 0:
            raise RuntimeError(f"native one-pass segmenter failed: {rc}")
        segment_count = int(stats.segments)
    else:
        stats.compared_target_bytes = 0
        stats.segments = 0
        segment_count = 0

    out = ctypes.POINTER(ctypes.c_uint8)()
    out_len = ctypes.c_size_t()
    surprise_bytes = ctypes.c_size_t()
    allocated = ctypes.c_size_t()
    depth = ctypes.c_size_t()
    nodes = ctypes.c_size_t()
    rc = writer_fn(
        src_arr, len(source), dst_arr, len(target), seg_buf, segment_count,
        pd, cd, int(enabled), ctypes.byref(out), ctypes.byref(out_len),
        ctypes.byref(surprise_bytes), ctypes.byref(allocated),
        ctypes.byref(depth), ctypes.byref(nodes),
    )
    if rc != 0:
        raise RuntimeError(f"shared native ONE0 writer failed: {rc}")
    try:
        wire = ctypes.string_at(out, out_len.value)
    finally:
        free_fn(out)
    wire_stats = WireStats(
        total_bytes=int(out_len.value),
        surprise_bytes=int(surprise_bytes.value),
        control_integrity_bytes=int(out_len.value - surprise_bytes.value),
    )
    return (
        wire, wire_stats, result, gate_reads, gate_used, enabled,
        int(stats.compared_target_bytes), segment_count,
        int(depth.value), int(nodes.value), int(allocated.value),
    )


def _time_pair(ctx_baseline, ctx_candidate):
    baseline_samples = []
    candidate_samples = []
    baseline_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for r in range(ROUNDS):
            order = (False, True) if r % 2 == 0 else (True, False)
            for candidate in order:
                t0 = __import__("time").perf_counter_ns()
                value = (_candidate_once_native(*ctx_candidate) if candidate
                         else _candidate_once_v2(*ctx_baseline))
                elapsed = __import__("time").perf_counter_ns() - t0
                if candidate:
                    candidate_samples.append(elapsed)
                    candidate_value = value
                else:
                    baseline_samples.append(elapsed)
                    baseline_value = value
    finally:
        if was_enabled:
            gc.enable()
    return (
        float(statistics.median(baseline_samples)), baseline_value,
        float(statistics.median(candidate_samples)), candidate_value,
    )


def _malformed_native_probes(writer_fn, free_fn) -> bool:
    source = b"abcdefgh"
    target = b"bcdefghi"
    src = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    dst = (ctypes.c_uint8 * len(target)).from_buffer_copy(target)
    pd = _digest_array(sha256(source).hexdigest())
    cd = _digest_array(sha256(target).hexdigest())
    buf = (Segment * 16)()

    probes = [
        ([(0, 0, 0)], 1),       # zero length
        ([(0, 7, 2)], 1),       # source ref out of range
        ([(1, 7, 2)], 1),       # Surprise out of range
        ([(7, 0, 8)], 1),       # unknown kind
        ([(0, 0, 4)], 1),       # incomplete coverage
        ([(0, 0, 8), (1, 0, 1)], 2),  # over coverage
    ]
    for spec, count in probes:
        for i, (kind, start, length) in enumerate(spec):
            buf[i].kind, buf[i].start, buf[i].length = kind, start, length
        out = ctypes.POINTER(ctypes.c_uint8)()
        olen = ctypes.c_size_t(); surprise = ctypes.c_size_t(); alloc = ctypes.c_size_t()
        depth = ctypes.c_size_t(); nodes = ctypes.c_size_t()
        rc = writer_fn(src, len(source), dst, len(target), buf, count, pd, cd, 1,
                       ctypes.byref(out), ctypes.byref(olen), ctypes.byref(surprise),
                       ctypes.byref(alloc), ctypes.byref(depth), ctypes.byref(nodes))
        if rc == 0:
            free_fn(out)
            return False
    # enabled relation with segment_count > target length
    out = ctypes.POINTER(ctypes.c_uint8)()
    olen = ctypes.c_size_t(); surprise = ctypes.c_size_t(); alloc = ctypes.c_size_t()
    depth = ctypes.c_size_t(); nodes = ctypes.c_size_t()
    rc = writer_fn(src, len(source), dst, len(target), buf, len(target) + 1, pd, cd, 1,
                   ctypes.byref(out), ctypes.byref(olen), ctypes.byref(surprise),
                   ctypes.byref(alloc), ctypes.byref(depth), ctypes.byref(nodes))
    if rc == 0:
        free_fn(out)
        return False
    return True


def run():
    admission_fn, segment_fn, segment_td = _build_native()
    writer_fn, free_fn, writer_td = _build_writer_native()
    rows = []
    semantic_failures = 0
    oracle_failures = 0
    mature_productive = []
    mature_controls = []
    malformed_ok = _malformed_native_probes(writer_fn, free_fn)
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, _expected_enable, _expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                bctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
                cctx = (writer_fn, free_fn, admission_fn, segment_fn,
                        source, target, src_arr, dst_arr, seg_buf)

                baseline = _candidate_once_v2(*bctx)
                candidate = _candidate_once_native(*cctx)
                (bwire, bstats, bresult, breads, bused, benabled,
                 bplan, btraffic, bsegments, bdepth, bnodes) = baseline
                (cwire, cstats, cresult, creads, cused, cenabled,
                 ctraffic, csegments, cdepth, cnodes, calloc) = candidate

                audit_stats = SegmentStats()
                if benabled:
                    audit_plan = _native_plan(segment_fn, src_arr, dst_arr, size, seg_buf, audit_stats)
                    this_oracle = _plan_signature(audit_plan) == _plan_signature(_oracle_plan(source, target))
                else:
                    audit_plan = ()
                    this_oracle = True
                outputs, vm_stats = evaluate(decode_program(cwire))
                exact = outputs == {"previous": source, "current": target}
                this_semantic = (
                    bwire == cwire and bstats == cstats and benabled == cenabled
                    and int(bresult.best_shift) == int(cresult.best_shift)
                    and int(bresult.exact_proofs) == int(cresult.exact_proofs)
                    and breads == creads and bused == cused
                    and btraffic == ctraffic and bsegments == csegments
                    and bdepth == cdepth and bnodes == cnodes and exact
                )
                if not this_semantic:
                    semantic_failures += 1
                    raise AssertionError(f"shared native writer semantic mismatch: {case}/{size}")
                if not this_oracle:
                    oracle_failures += 1
                    raise AssertionError(f"shared native writer plan oracle mismatch: {case}/{size}")

                baseline_ns, bt, candidate_ns, ct = _time_pair(bctx, cctx)
                if bt is None or ct is None or bt[0] != ct[0] or bt[1] != ct[1]:
                    raise AssertionError("timed shared native writer changed canonical wire/stats")
                ratio = candidate_ns / baseline_ns
                productive = case in PRODUCTIVE
                if size >= MATURE_MIN:
                    (mature_productive if productive else mature_controls).append(ratio)
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": productive,
                    "relation_enabled": cenabled,
                    "segments": csegments,
                    "hierarchy_depth": cdepth,
                    "node_count": cnodes,
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "native_output_capacity_bytes": calloc,
                    "baseline_v2_median_ns": baseline_ns,
                    "candidate_native_median_ns": candidate_ns,
                    "candidate_over_baseline": ratio,
                    "canonical_wire_exact": bwire == cwire,
                    "native_plan_oracle_exact": this_oracle,
                    "exact_reconstruction": exact,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                })

        pmed = float(statistics.median(mature_productive))
        pgood = sum(r <= PRODUCTIVE_GOOD_MAX for r in mature_productive)
        pworst = max(mature_productive)
        cmed = float(statistics.median(mature_controls))
        cworst = max(mature_controls)
        semantic_ok = semantic_failures == 0 and oracle_failures == 0 and malformed_ok
        perf_ok = (
            pmed <= PRODUCTIVE_MEDIAN_MAX and pgood >= MIN_PRODUCTIVE_GOOD
            and pworst <= PRODUCTIVE_ROW_MAX and cmed <= CONTROL_MEDIAN_MAX
            and cworst <= CONTROL_ROW_MAX
        )
        decision = "advance_shared_native_writer_transfer" if semantic_ok and perf_ok else "reject_shared_native_writer_transfer"
        result = {
            "schema": "cmpct-one-g02-shared-native-writer-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD", "local"),
            "claim_boundary": "frozen adjacent-version shared-native writer transfer only; arbitrary/fused discovery, filesystem/product, authenticated placement, RSS/native peak and comparator authority excluded",
            "frozen_rounds": ROUNDS,
            "semantic_failures": semantic_failures,
            "oracle_failures": oracle_failures,
            "malformed_native_buffer_probes_pass": malformed_ok,
            "mature_productive_median_ratio": pmed,
            "mature_productive_rows_at_or_below_0_90": pgood,
            "mature_productive_worst_ratio": pworst,
            "mature_control_median_ratio": cmed,
            "mature_control_worst_ratio": cworst,
            "decision": decision,
            "rows": rows,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        if not semantic_ok or not perf_ok:
            raise SystemExit(1)
    finally:
        segment_td.cleanup()
        writer_td.cleanup()


if __name__ == "__main__":
    run()
