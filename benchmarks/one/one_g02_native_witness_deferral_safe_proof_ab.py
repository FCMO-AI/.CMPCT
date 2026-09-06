"""ONE-G0.2 native witness-deferral + overlap-safe proof causal A/B.

Frozen by ONE_G02_NATIVE_WITNESS_DEFERRAL_SAFE_PROOF_PREREG_2026-09-06.md.
The native minimizer trace is generated once per row outside the timed boundary;
both arms then consume the identical trace and invoke the identical safe proof
when nominated. This is a native causal transfer, not fused-writer authority.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_relation_shared_observer_validation import MINIMIZER_SPAN, _cases

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
CASES = (
    "shift_plus1", "damage_quarter", "fragmented_every96",
    "hostile_fixed_bands", "fragmented_every32", "independent_random",
)
NEGATIVES = {"fragmented_every32", "independent_random"}
ROUNDS = 21
MAX_PRODUCTIVE_MEDIAN = 0.95
MAX_PRODUCTIVE_ROW = 1.03
MAX_NEGATIVE_SIZE_MEDIAN = 1.03
MAX_TRAFFIC_RATIO = 0.70
WINDOW = 64


class SelectorResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64), ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64), ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64), ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
    ]


class ConsumerResult(ctypes.Structure):
    _fields_ = [
        ("cross_auditions", ctypes.c_uint64), ("cross_witnesses", ctypes.c_uint64),
        ("nominations", ctypes.c_uint64), ("local_peak_entries", ctypes.c_uint64),
        ("global_peak_entries", ctypes.c_uint64), ("global_capacity_entries", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64), ("extension_read_bytes", ctypes.c_uint64),
        ("anchors_consumed", ctypes.c_uint64),
    ]


class SafeResult(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64), ("zero_shift_matches", ctypes.c_uint64),
        ("coverage_compared_bytes", ctypes.c_uint64), ("best_hits", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64), ("proof_attempts", ctypes.c_uint64),
        ("exact_proofs", ctypes.c_uint64), ("proof_compared_bytes", ctypes.c_uint64),
        ("strata_with_support", ctypes.c_uint64),
    ]


def _sig(x: SafeResult) -> tuple[int, ...]:
    return tuple(int(getattr(x, name)) for name, _ in SafeResult._fields_)


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-native-witness-deferral-")
    lib = Path(td.name) / "libab.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_minimizer_offset_only_kernel.c"),
        str(here / "one_g02_native_witness_deferral_consumer_kernel.c"),
        str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    selector = c.one_g02_minimizer_offset_only_kernel
    selector.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(SelectorResult), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t]
    selector.restype = ctypes.c_int
    consume = c.one_g02_native_witness_deferral_consume
    consume.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
        ctypes.c_int, ctypes.POINTER(ConsumerResult)]
    consume.restype = ctypes.c_int
    safe = c.one_g02_shift_relation_safe_dispatch
    safe.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t, ctypes.POINTER(SafeResult)]
    safe.restype = ctypes.c_int
    direct = c.one_g02_shift_branch_bound_relation_direct
    direct.argtypes = safe.argtypes
    direct.restype = ctypes.c_int
    return selector, consume, safe, direct, td


def _arm(consume, safe, data_buf, total_len, boundary, gear, trace, emitted, mode, src_ptr, dst_ptr, rel_len):
    cr = ConsumerResult()
    rc = consume(data_buf, total_len, boundary, gear, trace, emitted, mode, ctypes.byref(cr))
    if rc != 0:
        raise RuntimeError(f"consumer rc={rc}")
    sr = SafeResult()
    path = -1
    if cr.nominations:
        path = safe(src_ptr, dst_ptr, rel_len, ctypes.byref(sr))
        if path < 0:
            raise RuntimeError(f"safe proof rc={path}")
    law = bool(cr.nominations and sr.exact_proofs >= 4)
    traffic = int(cr.verification_read_bytes + cr.extension_read_bytes)
    if cr.nominations:
        traffic += int(sr.coverage_compared_bytes + sr.proof_compared_bytes)
    return cr, sr, path, law, traffic


def _overlap_checks(safe, direct):
    rows = []
    n = 4096
    raw = bytes(((i * 131 + 17) ^ (i >> 3)) & 255 for i in range(n + 1))
    arr = (ctypes.c_uint8 * len(raw)).from_buffer_copy(raw)
    addr = ctypes.addressof(arr)
    for name, so, do in (("same", 0, 0), ("forward_overlap", 0, 1), ("backward_overlap", 1, 0)):
        sp = ctypes.cast(addr + so, ctypes.POINTER(ctypes.c_uint8))
        dp = ctypes.cast(addr + do, ctypes.POINTER(ctypes.c_uint8))
        a, b = SafeResult(), SafeResult()
        path = safe(sp, dp, n, ctypes.byref(a))
        rc = direct(sp, dp, n, ctypes.byref(b))
        rows.append({"layout": name, "dispatch_path": path, "direct_rc": rc,
                     "result_exact": _sig(a) == _sig(b),
                     "pass": path == 0 and rc == 0 and _sig(a) == _sig(b)})
    return rows


def run():
    selector, consume, safe, direct, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                generated = _cases(size, seed)
                for name in CASES:
                    source, target = generated[name]
                    if len(source) != len(target):
                        raise RuntimeError("frozen relation arms require equal source/target length")
                    data = source + target
                    arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                    addr = ctypes.addressof(arr)
                    src = ctypes.cast(addr, ctypes.POINTER(ctypes.c_uint8))
                    dst = ctypes.cast(addr + len(source), ctypes.POINTER(ctypes.c_uint8))
                    trace = (ctypes.c_uint64 * (len(data) + 1))()
                    sel = SelectorResult()
                    rc = selector(arr, len(data), gear, WINDOW, MINIMIZER_SPAN,
                                  ctypes.byref(sel), trace, len(data) + 1)
                    if rc != 0:
                        raise RuntimeError(f"selector rc={rc}")
                    emitted = int(sel.emitted)

                    base_samples, cand_samples = [], []
                    for _ in range(ROUNDS):
                        t = time.perf_counter_ns(); _arm(consume, safe, arr, len(data), len(source), gear, trace, emitted, 0, src, dst, len(source)); base_samples.append(time.perf_counter_ns() - t)
                        t = time.perf_counter_ns(); _arm(consume, safe, arr, len(data), len(source), gear, trace, emitted, 1, src, dst, len(source)); cand_samples.append(time.perf_counter_ns() - t)
                        t = time.perf_counter_ns(); _arm(consume, safe, arr, len(data), len(source), gear, trace, emitted, 1, src, dst, len(source)); cand_samples.append(time.perf_counter_ns() - t)
                        t = time.perf_counter_ns(); _arm(consume, safe, arr, len(data), len(source), gear, trace, emitted, 0, src, dst, len(source)); base_samples.append(time.perf_counter_ns() - t)

                    bcr, bsr, bpath, blaw, btraffic = _arm(consume, safe, arr, len(data), len(source), gear, trace, emitted, 0, src, dst, len(source))
                    ccr, csr, cpath, claw, ctraffic = _arm(consume, safe, arr, len(data), len(source), gear, trace, emitted, 1, src, dst, len(source))
                    bn = float(statistics.median(base_samples)); cn = float(statistics.median(cand_samples)); ratio = cn / bn
                    semantic_exact = blaw == claw
                    rows.append({
                        "relation_bytes": size, "seed": seed, "case": name,
                        "baseline_ns": bn, "candidate_ns": cn, "candidate_over_baseline": ratio,
                        "baseline_nominated": bool(bcr.nominations), "candidate_nominated": bool(ccr.nominations),
                        "baseline_final_law": blaw, "candidate_final_law": claw, "semantic_exact": semantic_exact,
                        "baseline_dispatch_path": bpath, "candidate_dispatch_path": cpath,
                        "baseline_verification_bytes": int(bcr.verification_read_bytes),
                        "baseline_extension_bytes": int(bcr.extension_read_bytes),
                        "candidate_verification_bytes": int(ccr.verification_read_bytes),
                        "candidate_extension_bytes": int(ccr.extension_read_bytes),
                        "baseline_total_relation_traffic": btraffic, "candidate_total_relation_traffic": ctraffic,
                        "baseline_exact_proofs": int(bsr.exact_proofs), "candidate_exact_proofs": int(csr.exact_proofs),
                        "global_capacity_entries": int(ccr.global_capacity_entries),
                    })

        overlap = _overlap_checks(safe, direct)
        positives = [r for r in rows if r["baseline_nominated"] and r["baseline_final_law"] and r["case"] not in NEGATIVES]
        opportunity_losses = [r for r in positives if not r["candidate_final_law"]]
        false_laws = [r for r in rows if r["case"] in NEGATIVES and r["candidate_final_law"]]
        productive_ratios = [float(r["candidate_over_baseline"]) for r in positives]
        productive_median = float(statistics.median(productive_ratios)) if productive_ratios else float("inf")
        worst_productive = max(productive_ratios, default=float("inf"))
        negative_size_medians = {}
        grouped = defaultdict(list)
        for r in rows:
            if r["case"] in NEGATIVES:
                grouped[int(r["relation_bytes"])].append(float(r["candidate_over_baseline"]))
        for size, values in grouped.items():
            negative_size_medians[str(size)] = float(statistics.median(values))
        worst_negative_size_median = max(negative_size_medians.values(), default=1.0)
        btraffic = sum(int(r["baseline_total_relation_traffic"]) for r in rows)
        ctraffic = sum(int(r["candidate_total_relation_traffic"]) for r in rows)
        traffic_ratio = ctraffic / btraffic if btraffic else 1.0
        semantic_ok = (not opportunity_losses and not false_laws and
                       all(bool(r["semantic_exact"]) for r in rows) and
                       all(bool(x["pass"]) for x in overlap))
        perf_ok = (productive_median <= MAX_PRODUCTIVE_MEDIAN and
                   worst_productive <= MAX_PRODUCTIVE_ROW and
                   worst_negative_size_median <= MAX_NEGATIVE_SIZE_MEDIAN and
                   traffic_ratio <= MAX_TRAFFIC_RATIO)
        if not semantic_ok:
            decision = "reject_native_witness_deferral_safe_proof"
        elif perf_ok:
            decision = "advance_native_witness_deferral_safe_proof"
        else:
            decision = "hold_native_witness_deferral_safe_proof"
        return {
            "schema": "cmpct-one-g02-native-witness-deferral-safe-proof-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "productive_rows": len(positives),
            "productive_median_candidate_over_baseline": productive_median,
            "worst_productive_candidate_over_baseline": worst_productive,
            "negative_size_medians": negative_size_medians,
            "worst_negative_size_median": worst_negative_size_median,
            "aggregate_baseline_relation_traffic": btraffic,
            "aggregate_candidate_relation_traffic": ctraffic,
            "aggregate_candidate_over_baseline_relation_traffic": traffic_ratio,
            "opportunity_losses": [(r["relation_bytes"], r["seed"], r["case"]) for r in opportunity_losses],
            "false_laws": [(r["relation_bytes"], r["seed"], r["case"]) for r in false_laws],
            "overlap_checks": overlap,
            "decision": decision,
            "claim_boundary": "native causal transfer at selector-trace/event-consumer boundary; trace generation is outside timed A/B and this is not fused-writer/product authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "reject_native_witness_deferral_safe_proof" else 1)
