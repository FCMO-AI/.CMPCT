"""ONE-G0.2 bounded non-redundant block-relation opportunity gate.

This is the admissible descendant of `one_g02_native_block_relation_gate.py`.
Source `26ac8f582cbdfbfa4981091ed19130f1b4f5ec4b` is pre-result inadmissible: repository
reconciliation showed that the already-developed shift/resemblance lineage had proven a
branch-and-bound lesson the draft did not yet absorb. A hostile sample match could force
an exact proof for every candidate pair, creating ~1x wasted source-size proof traffic.

The representation question is unchanged. Unique random parent chunks followed once by
add8/XOR children must be discovered without exact reuse. Eight fixed probe offsets are
nomination only; exact 64-byte relation proof remains mandatory. Uniform/uniform pairs
are suppressed because Fill already explains them.

New causal constraint, frozen before hosted result:
- each relation channel gets at most 16 *failed* exact proofs per source;
- successful proofs do not consume the failure budget;
- once a channel reaches 16 failures, later sample matches for that channel are ignored;
- sample-trap exact proof traffic must be <=4% of input at every size;
- positive exact-proof reads must be <=2x their exact-verified support bytes.

This is mechanism transfer from the existing proof-led relation research, not a new
reader-visible opcode and not a hidden fallback codec.
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

import benchmarks.one.one_g02_native_block_relation_gate as base

SIZES = base.SIZES
FAMILIES = base.FAMILIES
REPETITIONS = 21
MAX_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_ROW_OVERHEAD = 1.40
MIN_1MIB_THROUGHPUT_MIB_S = 200.0
MAX_FAILED_PROOFS_PER_CHANNEL = 16
MAX_NEGATIVE_EXACT_READ_FRACTION = 0.04
MAX_POSITIVE_PROOF_READS_PER_SUPPORT = 2.0

_C_SOURCE = r'''
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define FNV_OFFSET UINT64_C(0xcbf29ce484222325)
#define FNV_PRIME  UINT64_C(0x100000001b3)
#define MAX_FP 256
#define CHUNK 64
#define MIN_RUN 8
#define MIN_RELATION_PAIRS 4
#define MAX_FAILED_PROOFS 16

typedef struct {
    uint64_t input_bytes;
    uint64_t source_scan_bytes;
    uint64_t run_support;
    uint64_t reuse_support;
    uint64_t add8_support;
    uint64_t xor_support;
    uint64_t retained_entries;
    uint64_t sampled_add8_candidates;
    uint64_t sampled_xor_candidates;
    uint64_t verified_add8_pairs;
    uint64_t verified_xor_pairs;
    uint64_t failed_add8_proofs;
    uint64_t failed_xor_proofs;
    uint64_t exact_relation_bytes_read;
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

static int sample_add8(const uint8_t *a, const uint8_t *b, uint8_t *delta) {
    static const uint8_t off[8] = {0,9,18,27,36,45,54,63};
    const uint8_t d = (uint8_t)(b[0] - a[0]);
    if (d == 0) return 0;
    for (size_t i = 1; i < 8; ++i)
        if ((uint8_t)(b[off[i]] - a[off[i]]) != d) return 0;
    *delta = d;
    return 1;
}

static int sample_xor(const uint8_t *a, const uint8_t *b, uint8_t *mask) {
    static const uint8_t off[8] = {0,9,18,27,36,45,54,63};
    const uint8_t m = (uint8_t)(b[0] ^ a[0]);
    if (m == 0) return 0;
    for (size_t i = 1; i < 8; ++i)
        if ((uint8_t)(b[off[i]] ^ a[off[i]]) != m) return 0;
    *mask = m;
    return 1;
}

static int verify_add8(const uint8_t *a, const uint8_t *b, uint8_t d) {
    for (size_t i = 0; i < CHUNK; ++i)
        if ((uint8_t)(b[i] - a[i]) != d) return 0;
    return 1;
}

static int verify_xor(const uint8_t *a, const uint8_t *b, uint8_t m) {
    for (size_t i = 0; i < CHUNK; ++i)
        if ((uint8_t)(b[i] ^ a[i]) != m) return 0;
    return 1;
}

int one_bounded_block_relation_candidate(const uint8_t *data, size_t n, gate_out *out) {
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
    int previous_chunk_uniform = 0;

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
            const int current_chunk_uniform = run_len >= CHUNK;

            if ((p + 1) >= 2 * CHUNK && !(previous_chunk_uniform && current_chunk_uniform)) {
                const uint8_t *a = data + (p + 1) - 2 * CHUNK;
                const uint8_t *b = data + (p + 1) - CHUNK;
                uint8_t d = 0, m = 0;

                if (out->failed_add8_proofs < MAX_FAILED_PROOFS && sample_add8(a, b, &d)) {
                    ++out->sampled_add8_candidates;
                    out->exact_relation_bytes_read += 2 * CHUNK;
                    if (verify_add8(a, b, d)) {
                        ++out->verified_add8_pairs;
                        out->add8_support += CHUNK;
                    } else {
                        ++out->failed_add8_proofs;
                    }
                }

                if (out->failed_xor_proofs < MAX_FAILED_PROOFS && sample_xor(a, b, &m)) {
                    ++out->sampled_xor_candidates;
                    out->exact_relation_bytes_read += 2 * CHUNK;
                    if (verify_xor(a, b, m)) {
                        ++out->verified_xor_pairs;
                        out->xor_support += CHUNK;
                    } else {
                        ++out->failed_xor_proofs;
                    }
                }
            }
            previous_chunk_uniform = current_chunk_uniform;
        }
    }
    if (run_len >= MIN_RUN) run_support += run_len;

    out->run_support = run_support;
    out->reuse_support = repeated * CHUNK;
    out->retained_entries = fp_count;
    out->run = run_support >= MIN_RUN;
    out->reuse = repeated > 0;
    out->add8 = out->verified_add8_pairs >= MIN_RELATION_PAIRS;
    out->xor_nom = out->verified_xor_pairs >= MIN_RELATION_PAIRS;
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
        ("sampled_add8_candidates", ctypes.c_uint64),
        ("sampled_xor_candidates", ctypes.c_uint64),
        ("verified_add8_pairs", ctypes.c_uint64),
        ("verified_xor_pairs", ctypes.c_uint64),
        ("failed_add8_proofs", ctypes.c_uint64),
        ("failed_xor_proofs", ctypes.c_uint64),
        ("exact_relation_bytes_read", ctypes.c_uint64),
        ("run", ctypes.c_uint8),
        ("reuse", ctypes.c_uint8),
        ("add8", ctypes.c_uint8),
        ("xor_nom", ctypes.c_uint8),
    ]


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-bounded-block-relation-"))
    source = build / "kernel.c"
    output = build / "libboundedblockrelation.so"
    source.write_text(_C_SOURCE)
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    fn = lib.one_bounded_block_relation_candidate
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(_GateOut)]
    fn.restype = ctypes.c_int
    return lib


def _candidate(data: bytes) -> _GateOut:
    n = len(data)
    buf = (ctypes.c_uint8 * n).from_buffer_copy(data) if n else None
    ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out = _GateOut()
    rc = _library().one_bounded_block_relation_candidate(ptr, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"candidate failed: {rc}")
    return out


def _measure(data: bytes):
    baseline = base._baseline(data)
    candidate = _candidate(data)
    bw: list[int] = []
    bc: list[int] = []
    cw: list[int] = []
    cc: list[int] = []
    for rep in range(REPETITIONS):
        order = ("candidate", "baseline") if rep & 1 else ("baseline", "candidate")
        for arm in order:
            t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
            out = _candidate(data) if arm == "candidate" else base._baseline(data)
            wall = time.perf_counter_ns() - t0w
            cpu = time.process_time_ns() - t0c
            if arm == "candidate":
                candidate = out
                cw.append(wall)
                cc.append(cpu)
            else:
                baseline = out
                bw.append(wall)
                bc.append(cpu)
    return baseline, candidate, statistics.median(bw)/1e9, statistics.median(bc)/1e9, statistics.median(cw)/1e9, statistics.median(cc)/1e9


def decide(rows: list[dict]) -> str:
    if len(rows) != 24 or len({(r["size"], r["family"]) for r in rows}) != 24:
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    if any(not r["baseline_common_equal"] or r["source_scan_ratio"] != 1.0 for r in rows):
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"

    add_rows = [r for r in rows if r["family"] == "unique_pair_add8"]
    xor_rows = [r for r in rows if r["family"] == "unique_pair_xor"]
    if any(r["has_duplicate_chunk"] or r["reuse"] or not r["add8"] or r["xor"] for r in add_rows):
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    if any(r["has_duplicate_chunk"] or r["reuse"] or not r["xor"] or r["add8"] for r in xor_rows):
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"

    controls = [r for r in rows if r["family"] not in {"unique_pair_add8", "unique_pair_xor"}]
    if any(r["add8"] or r["xor"] for r in controls):
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    traps = [r for r in rows if r["family"] == "sample_trap"]
    if any(r["sampled_relation_candidates"] == 0 or r["verified_relation_pairs"] != 0 for r in traps):
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    if any(r["failed_relation_proofs"] > 2 * MAX_FAILED_PROOFS_PER_CHANNEL for r in rows):
        return "INVALIDATE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    if any(r["exact_read_fraction"] > MAX_NEGATIVE_EXACT_READ_FRACTION for r in controls):
        return "HOLD_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    for r in add_rows + xor_rows:
        support = r["add8_support_bytes"] + r["xor_support_bytes"]
        if support <= 0 or r["exact_relation_bytes_read"] / support > MAX_POSITIVE_PROOF_READS_PER_SUPPORT:
            return "HOLD_NATIVE_BOUNDED_BLOCK_RELATION_GATE"

    if statistics.median(r["wall_ratio"] for r in rows) > MAX_MEDIAN_OVERHEAD or statistics.median(r["cpu_ratio"] for r in rows) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    mib = [r for r in rows if r["size"] == 1024 * 1024]
    if statistics.median(r["wall_ratio"] for r in mib) > MAX_1MIB_MEDIAN_OVERHEAD or statistics.median(r["cpu_ratio"] for r in mib) > MAX_1MIB_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    if max(r["wall_ratio"] for r in mib) > MAX_1MIB_ROW_OVERHEAD or max(r["cpu_ratio"] for r in mib) > MAX_1MIB_ROW_OVERHEAD:
        return "HOLD_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    if any(r["candidate_wall_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S or r["candidate_cpu_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S for r in mib):
        return "HOLD_NATIVE_BOUNDED_BLOCK_RELATION_GATE"
    return "ADVANCE_NATIVE_BOUNDED_BLOCK_RELATION_GATE"


def main() -> int:
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            data = base.make_case(family, size)
            has_dup = base._has_duplicate_aligned_chunk(data)
            b, c, bw, bc, cw, cc = _measure(data)
            common = (
                bool(b.run) == bool(c.run)
                and bool(b.reuse) == bool(c.reuse)
                and int(b.run_support) == int(c.run_support)
                and int(b.reuse_support) == int(c.reuse_support)
                and int(b.retained_entries) == int(c.retained_entries)
            )
            mib = size / (1024 * 1024)
            rows.append({
                "size": size,
                "family": family,
                "has_duplicate_chunk": has_dup,
                "baseline_common_equal": common,
                "source_scan_ratio": c.source_scan_bytes / max(1, c.input_bytes),
                "run": bool(c.run),
                "reuse": bool(c.reuse),
                "add8": bool(c.add8),
                "xor": bool(c.xor_nom),
                "add8_support_bytes": int(c.add8_support),
                "xor_support_bytes": int(c.xor_support),
                "sampled_relation_candidates": int(c.sampled_add8_candidates + c.sampled_xor_candidates),
                "verified_relation_pairs": int(c.verified_add8_pairs + c.verified_xor_pairs),
                "failed_relation_proofs": int(c.failed_add8_proofs + c.failed_xor_proofs),
                "exact_relation_bytes_read": int(c.exact_relation_bytes_read),
                "exact_read_fraction": c.exact_relation_bytes_read / max(1, len(data)),
                "baseline_wall_seconds": bw,
                "baseline_cpu_seconds": bc,
                "candidate_wall_seconds": cw,
                "candidate_cpu_seconds": cc,
                "wall_ratio": cw / bw,
                "cpu_ratio": cc / bc,
                "candidate_wall_mib_s": mib / cw,
                "candidate_cpu_mib_s": mib / cc,
            })

    decision = decide(rows)
    mib_rows = [r for r in rows if r["size"] == 1024 * 1024]
    print(json.dumps({
        "experiment": "ONE-G0.2 native bounded nonredundant block relation gate",
        "decision": decision,
        "repetitions": REPETITIONS,
        "max_failed_proofs_per_channel": MAX_FAILED_PROOFS_PER_CHANNEL,
        "max_negative_exact_read_fraction": MAX_NEGATIVE_EXACT_READ_FRACTION,
        "median_wall_ratio": statistics.median(r["wall_ratio"] for r in rows),
        "median_cpu_ratio": statistics.median(r["cpu_ratio"] for r in rows),
        "median_1mib_wall_ratio": statistics.median(r["wall_ratio"] for r in mib_rows),
        "median_1mib_cpu_ratio": statistics.median(r["cpu_ratio"] for r in mib_rows),
        "worst_1mib_wall_ratio": max(r["wall_ratio"] for r in mib_rows),
        "worst_1mib_cpu_ratio": max(r["cpu_ratio"] for r in mib_rows),
        "rows": rows,
    }, sort_keys=True))
    return 0 if decision == "ADVANCE_NATIVE_BOUNDED_BLOCK_RELATION_GATE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
