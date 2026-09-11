"""ONE-G0.2 deterministic sampled multi-Law carrying-cost falsifier.

Tests whether add8/xor opportunity signals can be carried at one-quarter sampling density
without losing any relation that the promoted full observer would nominate at >=87.5%
support. The baseline and full candidate are imported from the frozen native carrying-cost
experiment; this file adds one sampled candidate to the same C translation unit.
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

import benchmarks.one.one_g02_native_multi_law_carry as full
from benchmarks.one.one_g02_multi_law_gate import FAMILIES as BASE_FAMILIES, SIZES, make_case
from experiments.one.multi_law_gate import observe_multi_law_gate

REPETITIONS = 21
SAMPLE_MASK = 3
SAMPLED_SUPPORT_NUM = 1
SAMPLED_SUPPORT_DEN = 2
MAX_MEDIAN_OVERHEAD = 1.20
MAX_ROW_OVERHEAD = 1.35
MAX_RELATION_MEDIAN_VS_FULL = 0.90
MIN_1MIB_THROUGHPUT_MIB_S = 250.0
PHASE_FAMILIES = ("add8_phase_poison", "xor_phase_poison")
FAMILIES = tuple(BASE_FAMILIES) + PHASE_FAMILIES
RELATION_FAMILIES = ("add8_ramp", "xor_chain") + PHASE_FAMILIES

_SAMPLED_C = r'''
int one_gate_sampled(const uint8_t *data, size_t n, gate_out *out) {
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
    uint64_t arithmetic_samples = 0;
    uint64_t xor_samples = 0;

    for (size_t p = 0; p < n; ++p) {
        const uint8_t v = data[p];
        if (run_len == 0) { run_value = v; run_len = 1; }
        else if (v == run_value) { ++run_len; }
        else {
            if (run_len >= MIN_RUN) run_support += run_len;
            run_value = v;
            run_len = 1;
        }

        if (p && ((p & 3u) == 0u)) {
            const uint8_t d = (uint8_t)(v - previous);
            ++delta[d];
            ++arithmetic_samples;
        }
        previous = v;

        if (p >= LAG && ((p & 3u) == 0u)) {
            const uint8_t relation = (uint8_t)(v ^ ring[p % LAG]);
            ++xhist[relation];
            ++xor_samples;
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

    uint64_t best_nonzero_delta = 0, best_nonzero_xor = 0;
    for (uint32_t i = 1; i < HIST; ++i) {
        if (delta[i] > best_nonzero_delta) best_nonzero_delta = delta[i];
        if (xhist[i] > best_nonzero_xor) best_nonzero_xor = xhist[i];
    }

    const int add8 = arithmetic_samples >= 64 &&
        best_nonzero_delta * 2 >= arithmetic_samples;
    const int xor_nom = xor_samples >= 64 &&
        best_nonzero_xor * 2 >= xor_samples;

    out->run_support = run_support;
    out->reuse_support = repeated * CHUNK;
    out->add8_support = add8 ? best_nonzero_delta : 0;
    out->xor_support = xor_nom ? best_nonzero_xor : 0;
    out->retained_entries = fp_count;
    out->run = run_support >= MIN_RUN;
    out->reuse = repeated > 0;
    out->add8 = add8;
    out->xor_nom = xor_nom;
    return 0;
}
'''

_C_SOURCE = full._C_SOURCE + _SAMPLED_C


def _phase_case(family: str, size: int) -> bytes:
    if family == "add8_phase_poison":
        out = bytearray(size)
        out[0] = 17
        for p in range(1, size):
            step = 9 if (p & 7) == 0 else 5
            out[p] = (out[p - 1] + step) & 0xFF
        return bytes(out)
    if family == "xor_phase_poison":
        lag, target, poison = 64, 0x5A, 0xA6
        out = bytearray(((17 + 29 * i) & 0xFF) for i in range(min(lag, size)))
        for p in range(lag, size):
            mask = poison if (p & 7) == 0 else target
            out.append(out[p - lag] ^ mask)
        return bytes(out)
    raise ValueError(family)


def make_sample_case(family: str, size: int) -> bytes:
    return _phase_case(family, size) if family in PHASE_FAMILIES else make_case(family, size)


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-native-multi-law-sampled-"))
    source = build / "kernel.c"
    output = build / "libgate.so"
    source.write_text(_C_SOURCE)
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    lib = ctypes.CDLL(str(output))
    for name in ("one_gate_baseline", "one_gate_candidate", "one_gate_sampled"):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(full._GateOut)]
        fn.restype = ctypes.c_int
    return lib


def _call(name: str, data: bytes) -> full._GateOut:
    n = len(data)
    buf = (ctypes.c_uint8 * n).from_buffer_copy(data) if n else None
    ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out = full._GateOut()
    rc = getattr(_library(), name)(ptr, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"{name} failed: {rc}")
    return out


def _decision_tuple(out: full._GateOut) -> tuple[bool, bool, bool, bool]:
    return bool(out.run), bool(out.reuse), bool(out.add8), bool(out.xor_nom)


def _oracle_decision(data: bytes) -> tuple[bool, bool, bool, bool]:
    d = observe_multi_law_gate(data).decision
    return d.run, d.reuse, d.add8, d.xor


def _measure_three(data: bytes):
    names = ("one_gate_baseline", "one_gate_candidate", "one_gate_sampled")
    latest = {name: _call(name, data) for name in names}
    walls = {name: [] for name in names}
    cpus = {name: [] for name in names}
    for rep in range(REPETITIONS):
        order = names[rep % 3:] + names[:rep % 3]
        for name in order:
            t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
            latest[name] = _call(name, data)
            walls[name].append(time.perf_counter_ns() - t0w)
            cpus[name].append(time.process_time_ns() - t0c)
    def med(values):
        return statistics.median(values) / 1e9
    return latest, {n: med(walls[n]) for n in names}, {n: med(cpus[n]) for n in names}


def decide(rows: list[dict]) -> str:
    expected = len(SIZES) * len(FAMILIES)
    if len(rows) != expected or len({(r["size"], r["family"]) for r in rows}) != expected:
        return "INVALIDATE_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    if any(not r["full_semantic_equal"] or not r["sampled_semantic_equal"] or not r["baseline_common_equal"] for r in rows):
        return "INVALIDATE_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    if any(r["source_scan_ratio"] != 1.0 for r in rows):
        return "INVALIDATE_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    sw = [r["sampled_wall_ratio"] for r in rows]
    sc = [r["sampled_cpu_ratio"] for r in rows]
    if statistics.median(sw) > MAX_MEDIAN_OVERHEAD or statistics.median(sc) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    if max(sw) > MAX_ROW_OVERHEAD or max(sc) > MAX_ROW_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    relation = [r for r in rows if r["family"] in RELATION_FAMILIES]
    if statistics.median(r["sampled_vs_full_wall"] for r in relation) > MAX_RELATION_MEDIAN_VS_FULL:
        return "HOLD_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    if statistics.median(r["sampled_vs_full_cpu"] for r in relation) > MAX_RELATION_MEDIAN_VS_FULL:
        return "HOLD_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    mib = [r for r in rows if r["size"] == 1024 * 1024]
    if any(r["sampled_wall_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S or r["sampled_cpu_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S for r in mib):
        return "HOLD_NATIVE_MULTI_LAW_SAMPLED_CARRY"
    return "ADVANCE_NATIVE_MULTI_LAW_SAMPLED_CARRY"


def main() -> int:
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            data = make_sample_case(family, size)
            latest, walls, cpus = _measure_three(data)
            baseline = latest["one_gate_baseline"]
            full_out = latest["one_gate_candidate"]
            sampled = latest["one_gate_sampled"]
            oracle = _oracle_decision(data)
            baseline_common_equal = (
                bool(baseline.run) == bool(full_out.run) == bool(sampled.run)
                and bool(baseline.reuse) == bool(full_out.reuse) == bool(sampled.reuse)
                and int(baseline.run_support) == int(full_out.run_support) == int(sampled.run_support)
                and int(baseline.reuse_support) == int(full_out.reuse_support) == int(sampled.reuse_support)
                and int(baseline.retained_entries) == int(full_out.retained_entries) == int(sampled.retained_entries)
            )
            bw, bc = walls["one_gate_baseline"], cpus["one_gate_baseline"]
            fw, fc = walls["one_gate_candidate"], cpus["one_gate_candidate"]
            sw, sc = walls["one_gate_sampled"], cpus["one_gate_sampled"]
            mib = size / (1024 * 1024)
            rows.append({
                "size": size,
                "family": family,
                "oracle": oracle,
                "full_semantic_equal": _decision_tuple(full_out) == oracle,
                "sampled_semantic_equal": _decision_tuple(sampled) == oracle,
                "baseline_common_equal": baseline_common_equal,
                "source_scan_ratio": sampled.source_scan_bytes / max(1, sampled.input_bytes),
                "baseline_wall_seconds": bw,
                "full_wall_seconds": fw,
                "sampled_wall_seconds": sw,
                "baseline_cpu_seconds": bc,
                "full_cpu_seconds": fc,
                "sampled_cpu_seconds": sc,
                "sampled_wall_ratio": sw / bw,
                "sampled_cpu_ratio": sc / bc,
                "full_wall_ratio": fw / bw,
                "full_cpu_ratio": fc / bc,
                "sampled_vs_full_wall": sw / fw,
                "sampled_vs_full_cpu": sc / fc,
                "sampled_wall_mib_s": mib / sw,
                "sampled_cpu_mib_s": mib / sc,
                "sampled_decision": [name for name, flag in zip(("run", "reuse", "add8", "xor"), _decision_tuple(sampled)) if flag],
            })
    decision = decide(rows)
    print(json.dumps({
        "experiment": "ONE-G0.2 native sampled multi-Law carrying cost",
        "decision": decision,
        "repetitions": REPETITIONS,
        "sample_fraction": 0.25,
        "sampled_support_threshold": 0.5,
        "max_median_overhead": MAX_MEDIAN_OVERHEAD,
        "max_row_overhead": MAX_ROW_OVERHEAD,
        "max_relation_median_vs_full": MAX_RELATION_MEDIAN_VS_FULL,
        "min_1mib_throughput_mib_s": MIN_1MIB_THROUGHPUT_MIB_S,
        "rows": rows,
    }, sort_keys=True))
    return 0 if decision == "ADVANCE_NATIVE_MULTI_LAW_SAMPLED_CARRY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
