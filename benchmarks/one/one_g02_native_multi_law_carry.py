"""ONE-G0.2 native multi-Law carrying-cost falsifier.

Mission Lock / preregistration
==============================
Hypothesis
----------
The promoted Python multi-Law nomination substrate can be carried inside one native
forward observation pass without turning the extra add8/xor signals into a compute tax
large enough to defeat opportunity gating.

Causal comparison
-----------------
Both native arms execute the SAME bounded run + aligned-64B-FNV reuse evidence pass.
The candidate adds only:
- modulo-256 first-difference histogram;
- lag-64 XOR histogram + 64-byte ring;
- final dominant-bin nomination tests.

Both arms pay the Python->ctypes source copy and one FFI call. Library compilation is
outside timing because a product native observer would ship built. Neither arm performs
downstream exact Law synthesis; this experiment measures carrying cost only.

Independent oracle
------------------
Candidate decisions/support are required to equal `observe_multi_law_gate()` on every
frozen row. The Python implementation is semantic authority here, not a speed baseline.

Frozen matrix
-------------
64 KiB / 256 KiB / 1 MiB x:
long_runs, exact_repeat, add8_ramp, xor_chain, mixed_structured, random,
compressed_like, false_pattern. 21 paired repetitions with rotating arm order.

Advance iff:
- exact 24-cell unique matrix;
- candidate semantic equality on all rows;
- baseline run/reuse equality with candidate on all rows;
- candidate source scan remains exactly 1.0x input;
- candidate/baseline median wall <= 1.25x across 24 rows;
- candidate/baseline median CPU <= 1.25x across 24 rows;
- no row exceeds 1.40x on either wall or CPU;
- at 1 MiB candidate throughput >= 150 MiB/s on both wall and CPU accounting.

A HOLD means the signal set must be sampled/deferred/reworked before downstream search
integration. Thresholds must not be relaxed after observing hosted results.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
import json
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_multi_law_gate import FAMILIES, SIZES, make_case
from experiments.one.multi_law_gate import observe_multi_law_gate

REPETITIONS = 21
MAX_MEDIAN_OVERHEAD = 1.25
MAX_ROW_OVERHEAD = 1.40
MIN_1MIB_THROUGHPUT_MIB_S = 150.0

_C_SOURCE = r'''
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define FNV_OFFSET UINT64_C(0xcbf29ce484222325)
#define FNV_PRIME  UINT64_C(0x100000001b3)
#define MAX_FP 256
#define HIST 256
#define LAG 64
#define CHUNK 64
#define MIN_RUN 8
#define SUPPORT_NUM 7
#define SUPPORT_DEN 8

typedef struct {
    uint64_t input_bytes;
    uint64_t source_scan_bytes;
    uint64_t run_support;
    uint64_t reuse_support;
    uint64_t add8_support;
    uint64_t xor_support;
    uint64_t retained_entries;
    uint8_t run;
    uint8_t reuse;
    uint8_t add8;
    uint8_t xor_nom;
} gate_out;

static int fp_seen_or_insert(uint64_t *fps, size_t *count, uint64_t fp) {
    for (size_t i = 0; i < *count; ++i) {
        if (fps[i] == fp) return 1;
    }
    if (*count < MAX_FP) fps[(*count)++] = fp;
    return 0;
}

int one_gate_baseline(const uint8_t *data, size_t n, gate_out *out) {
    if (!out || (n && !data)) return 2;
    memset(out, 0, sizeof(*out));
    out->input_bytes = n;
    out->source_scan_bytes = n;
    if (!n) return 0;

    uint64_t fps[MAX_FP];
    size_t fp_count = 0;
    uint64_t chunk_hash = FNV_OFFSET;
    uint64_t repeated = 0;
    uint8_t run_value = data[0];
    uint64_t run_len = 0;
    uint64_t run_support = 0;

    for (size_t p = 0; p < n; ++p) {
        const uint8_t v = data[p];
        if (run_len == 0) { run_value = v; run_len = 1; }
        else if (v == run_value) { ++run_len; }
        else {
            if (run_len >= MIN_RUN) run_support += run_len;
            run_value = v;
            run_len = 1;
        }

        chunk_hash ^= (uint64_t)v;
        chunk_hash *= FNV_PRIME;
        if (((p + 1) % CHUNK) == 0) {
            if (fp_seen_or_insert(fps, &fp_count, chunk_hash)) ++repeated;
            chunk_hash = FNV_OFFSET;
        }
    }
    if (run_len >= MIN_RUN) run_support += run_len;

    out->run_support = run_support;
    out->reuse_support = repeated * CHUNK;
    out->retained_entries = fp_count;
    out->run = run_support >= MIN_RUN;
    out->reuse = repeated > 0;
    return 0;
}

int one_gate_candidate(const uint8_t *data, size_t n, gate_out *out) {
    if (!out || (n && !data)) return 2;
    memset(out, 0, sizeof(*out));
    out->input_bytes = n;
    out->source_scan_bytes = n;
    if (!n) return 0;

    uint64_t fps[MAX_FP];
    size_t fp_count = 0;
    uint64_t chunk_hash = FNV_OFFSET;
    uint64_t repeated = 0;
    uint8_t run_value = data[0];
    uint64_t run_len = 0;
    uint64_t run_support = 0;
    uint64_t delta[HIST] = {0};
    uint64_t xhist[HIST] = {0};
    uint8_t ring[LAG] = {0};
    uint8_t previous = 0;
    uint64_t arithmetic_pairs = 0;
    uint64_t xor_pairs = 0;

    for (size_t p = 0; p < n; ++p) {
        const uint8_t v = data[p];
        if (run_len == 0) { run_value = v; run_len = 1; }
        else if (v == run_value) { ++run_len; }
        else {
            if (run_len >= MIN_RUN) run_support += run_len;
            run_value = v;
            run_len = 1;
        }

        if (p) {
            const uint8_t d = (uint8_t)(v - previous);
            ++delta[d];
            ++arithmetic_pairs;
        }
        previous = v;

        if (p >= LAG) {
            const uint8_t relation = (uint8_t)(v ^ ring[p % LAG]);
            ++xhist[relation];
            ++xor_pairs;
        }
        ring[p % LAG] = v;

        chunk_hash ^= (uint64_t)v;
        chunk_hash *= FNV_PRIME;
        if (((p + 1) % CHUNK) == 0) {
            if (fp_seen_or_insert(fps, &fp_count, chunk_hash)) ++repeated;
            chunk_hash = FNV_OFFSET;
        }
    }
    if (run_len >= MIN_RUN) run_support += run_len;

    uint64_t best_delta = 0, best_xor = 0;
    uint32_t delta_idx = 0, xor_idx = 0;
    for (uint32_t i = 0; i < HIST; ++i) {
        if (delta[i] > best_delta) { best_delta = delta[i]; delta_idx = i; }
        if (xhist[i] > best_xor) { best_xor = xhist[i]; xor_idx = i; }
    }

    const int add8 = arithmetic_pairs >= 256 && delta_idx != 0 &&
        best_delta * SUPPORT_DEN >= arithmetic_pairs * SUPPORT_NUM;
    const int xor_nom = xor_pairs >= 256 && xor_idx != 0 &&
        best_xor * SUPPORT_DEN >= xor_pairs * SUPPORT_NUM;

    out->run_support = run_support;
    out->reuse_support = repeated * CHUNK;
    out->add8_support = add8 ? best_delta + 1 : 0;
    out->xor_support = xor_nom ? best_xor : 0;
    out->retained_entries = fp_count;
    out->run = run_support >= MIN_RUN;
    out->reuse = repeated > 0;
    out->add8 = add8;
    out->xor_nom = xor_nom;
    return 0;
}
'''


class _GateOut(ctypes.Structure):
    _fields_ = [
        ("input_bytes", ctypes.c_uint64),
        ("source_scan_bytes", ctypes.c_uint64),
        ("run_support", ctypes.c_uint64),
        ("reuse_support", ctypes.c_uint64),
        ("add8_support", ctypes.c_uint64),
        ("xor_support", ctypes.c_uint64),
        ("retained_entries", ctypes.c_uint64),
        ("run", ctypes.c_uint8),
        ("reuse", ctypes.c_uint8),
        ("add8", ctypes.c_uint8),
        ("xor_nom", ctypes.c_uint8),
    ]


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-native-multi-law-"))
    source = build / "kernel.c"
    output = build / "libgate.so"
    source.write_text(_C_SOURCE)
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    for name in ("one_gate_baseline", "one_gate_candidate"):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(_GateOut)]
        fn.restype = ctypes.c_int
    return lib


def _call(name: str, data: bytes) -> _GateOut:
    n = len(data)
    buf = (ctypes.c_uint8 * n).from_buffer_copy(data) if n else None
    ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out = _GateOut()
    rc = getattr(_library(), name)(ptr, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"{name} failed: {rc}")
    return out


def _semantic_tuple(out: _GateOut) -> tuple[bool, bool, bool, bool, int, int, int, int]:
    return (
        bool(out.run), bool(out.reuse), bool(out.add8), bool(out.xor_nom),
        int(out.run_support), int(out.reuse_support), int(out.add8_support), int(out.xor_support),
    )


def _oracle_tuple(data: bytes) -> tuple[bool, bool, bool, bool, int, int, int, int]:
    d = observe_multi_law_gate(data).decision
    return (d.run, d.reuse, d.add8, d.xor, d.run_support_bytes, d.reuse_support_bytes,
            d.add8_support_bytes, d.xor_support_bytes)


def _measure_pair(data: bytes) -> tuple[_GateOut, _GateOut, float, float, float, float]:
    # Compile/warm first; neither compilation nor first-call loader work is result-bearing.
    baseline = _call("one_gate_baseline", data)
    candidate = _call("one_gate_candidate", data)
    bw, bc, cw, cc = [], [], [], []
    for rep in range(REPETITIONS):
        order = ("candidate", "baseline") if rep % 2 else ("baseline", "candidate")
        for arm in order:
            name = "one_gate_candidate" if arm == "candidate" else "one_gate_baseline"
            t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
            out = _call(name, data)
            wall = time.perf_counter_ns() - t0w
            cpu = time.process_time_ns() - t0c
            if arm == "candidate":
                candidate = out; cw.append(wall); cc.append(cpu)
            else:
                baseline = out; bw.append(wall); bc.append(cpu)
    return (
        baseline,
        candidate,
        statistics.median(bw) / 1e9,
        statistics.median(bc) / 1e9,
        statistics.median(cw) / 1e9,
        statistics.median(cc) / 1e9,
    )


def decide(rows: list[dict]) -> str:
    expected = len(SIZES) * len(FAMILIES)
    if len(rows) != expected or len({(r["size"], r["family"]) for r in rows}) != expected:
        return "INVALIDATE_NATIVE_MULTI_LAW_CARRY"
    if any(not r["semantic_equal"] or not r["baseline_common_equal"] for r in rows):
        return "INVALIDATE_NATIVE_MULTI_LAW_CARRY"
    if any(r["source_scan_ratio"] != 1.0 for r in rows):
        return "INVALIDATE_NATIVE_MULTI_LAW_CARRY"
    wall_ratios = [r["wall_ratio"] for r in rows]
    cpu_ratios = [r["cpu_ratio"] for r in rows]
    if max(wall_ratios) > MAX_ROW_OVERHEAD or max(cpu_ratios) > MAX_ROW_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_CARRY"
    if statistics.median(wall_ratios) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_CARRY"
    if statistics.median(cpu_ratios) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_CARRY"
    mib_rows = [r for r in rows if r["size"] == 1024 * 1024]
    if any(r["candidate_wall_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S for r in mib_rows):
        return "HOLD_NATIVE_MULTI_LAW_CARRY"
    if any(r["candidate_cpu_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S for r in mib_rows):
        return "HOLD_NATIVE_MULTI_LAW_CARRY"
    return "ADVANCE_NATIVE_MULTI_LAW_CARRY"


def main() -> int:
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            data = make_case(family, size)
            baseline, candidate, bw, bc, cw, cc = _measure_pair(data)
            oracle = _oracle_tuple(data)
            cand = _semantic_tuple(candidate)
            baseline_common_equal = (
                bool(baseline.run) == bool(candidate.run)
                and bool(baseline.reuse) == bool(candidate.reuse)
                and int(baseline.run_support) == int(candidate.run_support)
                and int(baseline.reuse_support) == int(candidate.reuse_support)
                and int(baseline.retained_entries) == int(candidate.retained_entries)
            )
            mib = size / (1024 * 1024)
            rows.append({
                "size": size,
                "family": family,
                "semantic_equal": cand == oracle,
                "baseline_common_equal": baseline_common_equal,
                "source_scan_ratio": candidate.source_scan_bytes / max(1, candidate.input_bytes),
                "baseline_wall_seconds": bw,
                "baseline_cpu_seconds": bc,
                "candidate_wall_seconds": cw,
                "candidate_cpu_seconds": cc,
                "wall_ratio": cw / bw,
                "cpu_ratio": cc / bc,
                "candidate_wall_mib_s": mib / cw,
                "candidate_cpu_mib_s": mib / cc,
                "candidate_decision": [name for name, flag in zip(("run", "reuse", "add8", "xor"), cand[:4]) if flag],
            })
    decision = decide(rows)
    payload = {
        "experiment": "ONE-G0.2 native multi-Law carrying cost",
        "decision": decision,
        "repetitions": REPETITIONS,
        "max_median_overhead": MAX_MEDIAN_OVERHEAD,
        "max_row_overhead": MAX_ROW_OVERHEAD,
        "min_1mib_throughput_mib_s": MIN_1MIB_THROUGHPUT_MIB_S,
        "median_wall_ratio": statistics.median(r["wall_ratio"] for r in rows),
        "median_cpu_ratio": statistics.median(r["cpu_ratio"] for r in rows),
        "worst_wall_ratio": max(r["wall_ratio"] for r in rows),
        "worst_cpu_ratio": max(r["cpu_ratio"] for r in rows),
        "rows": rows,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if decision == "ADVANCE_NATIVE_MULTI_LAW_CARRY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
