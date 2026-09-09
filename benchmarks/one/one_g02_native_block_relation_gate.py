"""ONE-G0.2 non-redundant native block-relation opportunity gate.

Mission Lock / Referee
======================
Problem discovered by the preceding carrying-cost falsifiers
-------------------------------------------------------------
The promoted global add8-ramp and fixed-lag XOR cues are not only expensive to carry;
the frozen synthetic positives are structurally redundant with exact reuse on long
inputs. A modulo-256 constant-delta byte ramp has period <=256 bytes. A fixed-mask
lag-64 XOR recurrence repeats after two generations (128 bytes). The existing aligned
64-byte reuse observer therefore sees both families quickly.

This experiment asks a different question: can ONE discover *non-redundant* add8/XOR
parent-child structure cheaply, without a second full byte scan and without accepting a
sample match as semantic truth?

Candidate mechanism
-------------------
The full native run + aligned-64B-FNV reuse pass remains unchanged. At each 64-byte
chunk boundary, the candidate compares the current chunk with the immediately previous
chunk at eight fixed positions (1/8 of bytes). If all samples agree on one non-zero
mod-256 delta and/or XOR mask, that pair alone receives an exact 64-byte relation proof.
Only exact-verified pairs contribute support. A sample hit is nomination, never Law.

Frozen matrix
-------------
64 KiB / 256 KiB / 1 MiB x eight families:
- unique_pair_add8: independent random parent chunks, each followed once by parent+d;
- unique_pair_xor: independent random parent chunks, each followed once by parent^mask;
- exact_repeat: reuse positive, relation negative;
- long_runs: run/reuse positive, relation negative (zero relations suppressed);
- random: hostile negative;
- compressed_like: hostile negative;
- near_repeat: adjacent near copies with one unsampled mutation, relation negative;
- sample_trap: all eight sampled positions mimic add8, unsampled bytes break it; exact
  proof must reject every nominated pair.

The relation-positive generators are independently checked for zero exact duplicate
64-byte chunks. If reuse appears there, the experiment invalidates rather than letting
reuse make the relation cue look useful.

Frozen promotion law
--------------------
Advance iff:
- exactly 24 unique rows;
- baseline/candidate run+reuse state is identical on every row;
- unique_pair_add8: add8 true, xor false, reuse false on all rows;
- unique_pair_xor: xor true, add8 false, reuse false on all rows;
- all six other families have no final add8/xor decision;
- sample_trap produces sampled candidates but zero exact-verified relation pairs;
- every final relation support byte was exact-verified;
- source scan is exactly 1.0x input (candidate proofs are separately counted random
  reads, not disguised as another source scan);
- median candidate/baseline wall and CPU <=1.30x;
- median 1 MiB wall and CPU <=1.30x;
- no 1 MiB row exceeds 1.40x on wall or CPU;
- all 1 MiB candidate rows sustain >=200 MiB/s wall and CPU.

A HOLD means this pairwise sampled-proof geometry is not cheap/selective enough. Do not
rescue it by changing sample positions/counts after seeing hosted results.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
import json
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time
import zlib

import benchmarks.one.one_g02_native_multi_law_carry as parent

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
FAMILIES = (
    "unique_pair_add8",
    "unique_pair_xor",
    "exact_repeat",
    "long_runs",
    "random",
    "compressed_like",
    "near_repeat",
    "sample_trap",
)
REPETITIONS = 21
MAX_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_ROW_OVERHEAD = 1.40
MIN_1MIB_THROUGHPUT_MIB_S = 200.0
BLOCK = 64
SAMPLE_OFFSETS = (0, 9, 18, 27, 36, 45, 54, 63)

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

int one_block_relation_candidate(const uint8_t *data, size_t n, gate_out *out) {
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

            if ((p + 1) >= 2 * CHUNK) {
                const uint8_t *a = data + (p + 1) - 2 * CHUNK;
                const uint8_t *b = data + (p + 1) - CHUNK;
                uint8_t d = 0, m = 0;
                if (sample_add8(a, b, &d)) {
                    ++out->sampled_add8_candidates;
                    out->exact_relation_bytes_read += 2 * CHUNK;
                    if (verify_add8(a, b, d)) {
                        ++out->verified_add8_pairs;
                        out->add8_support += CHUNK;
                    }
                }
                if (sample_xor(a, b, &m)) {
                    ++out->sampled_xor_candidates;
                    out->exact_relation_bytes_read += 2 * CHUNK;
                    if (verify_xor(a, b, m)) {
                        ++out->verified_xor_pairs;
                        out->xor_support += CHUNK;
                    }
                }
            }
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
        ("exact_relation_bytes_read", ctypes.c_uint64),
        ("run", ctypes.c_uint8),
        ("reuse", ctypes.c_uint8),
        ("add8", ctypes.c_uint8),
        ("xor_nom", ctypes.c_uint8),
    ]


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-block-relation-"))
    source = build / "kernel.c"
    output = build / "libblockrelation.so"
    source.write_text(_C_SOURCE)
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    fn = lib.one_block_relation_candidate
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(_GateOut)]
    fn.restype = ctypes.c_int
    return lib


def _candidate(data: bytes) -> _GateOut:
    n = len(data)
    buf = (ctypes.c_uint8 * n).from_buffer_copy(data) if n else None
    ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out = _GateOut()
    rc = _library().one_block_relation_candidate(ptr, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"candidate failed: {rc}")
    return out


def _baseline(data: bytes) -> parent._GateOut:
    return parent._call("one_gate_baseline", data)


def _repeat_to_size(seed: bytes, size: int) -> bytes:
    return (seed * ((size + len(seed) - 1) // len(seed)))[:size]


def _unique_base(rng: random.Random) -> bytes:
    return bytes(rng.randrange(256) for _ in range(BLOCK))


def make_case(family: str, size: int) -> bytes:
    rng = random.Random(0xB10C0000 ^ size ^ sum(map(ord, family)))
    chunks: list[bytes] = []
    needed = (size + BLOCK - 1) // BLOCK

    if family == "unique_pair_add8":
        pair = 0
        while len(chunks) < needed:
            base = _unique_base(rng)
            d = (17 + 2 * pair) & 0xFF
            if d == 0:
                d = 19
            chunks.extend((base, bytes((v + d) & 0xFF for v in base)))
            pair += 1
    elif family == "unique_pair_xor":
        pair = 0
        while len(chunks) < needed:
            base = _unique_base(rng)
            mask = (0xA5 + 2 * pair) & 0xFF
            if mask == 0:
                mask = 0xA7
            chunks.extend((base, bytes(v ^ mask for v in base)))
            pair += 1
    elif family == "exact_repeat":
        seed = _unique_base(rng)
        chunks = [seed] * needed
    elif family == "long_runs":
        data = bytearray()
        value = 0
        while len(data) < size:
            data.extend(bytes((value,)) * min(4096, size - len(data)))
            value = (value + 37) & 0xFF
        return bytes(data)
    elif family == "random":
        return bytes(rng.randrange(256) for _ in range(size))
    elif family == "compressed_like":
        source = bytes(rng.randrange(16) + 65 for _ in range(size * 2))
        return _repeat_to_size(zlib.compress(source, 9), size)
    elif family == "near_repeat":
        pair = 0
        while len(chunks) < needed:
            base = _unique_base(rng)
            child = bytearray(base)
            # Offset 5 is deliberately outside the cheap sample positions.
            child[5] ^= (1 + 2 * pair) & 0xFF or 1
            chunks.extend((base, bytes(child)))
            pair += 1
    elif family == "sample_trap":
        pair = 0
        while len(chunks) < needed:
            base = _unique_base(rng)
            child = bytearray(rng.randrange(256) for _ in range(BLOCK))
            d = (23 + 2 * pair) & 0xFF
            if d == 0:
                d = 25
            for off in SAMPLE_OFFSETS:
                child[off] = (base[off] + d) & 0xFF
            chunks.extend((base, bytes(child)))
            pair += 1
    else:
        raise ValueError(family)
    return b"".join(chunks)[:size]


def _has_duplicate_aligned_chunk(data: bytes) -> bool:
    seen: set[bytes] = set()
    for p in range(0, len(data) - BLOCK + 1, BLOCK):
        chunk = data[p:p + BLOCK]
        if chunk in seen:
            return True
        seen.add(chunk)
    return False


def _measure(data: bytes):
    # Compile/warm before result-bearing clocks.
    baseline = _baseline(data)
    candidate = _candidate(data)
    bw: list[int] = []
    bc: list[int] = []
    cw: list[int] = []
    cc: list[int] = []
    for rep in range(REPETITIONS):
        order = ("candidate", "baseline") if rep & 1 else ("baseline", "candidate")
        for arm in order:
            t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
            out = _candidate(data) if arm == "candidate" else _baseline(data)
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
    return (
        baseline,
        candidate,
        statistics.median(bw) / 1e9,
        statistics.median(bc) / 1e9,
        statistics.median(cw) / 1e9,
        statistics.median(cc) / 1e9,
    )


def decide(rows: list[dict]) -> str:
    if len(rows) != 24 or len({(r["size"], r["family"]) for r in rows}) != 24:
        return "INVALIDATE_NATIVE_BLOCK_RELATION_GATE"
    if any(not r["baseline_common_equal"] or r["source_scan_ratio"] != 1.0 for r in rows):
        return "INVALIDATE_NATIVE_BLOCK_RELATION_GATE"
    positives_add = [r for r in rows if r["family"] == "unique_pair_add8"]
    positives_xor = [r for r in rows if r["family"] == "unique_pair_xor"]
    if any(r["has_duplicate_chunk"] or r["reuse"] or not r["add8"] or r["xor"] for r in positives_add):
        return "INVALIDATE_NATIVE_BLOCK_RELATION_GATE"
    if any(r["has_duplicate_chunk"] or r["reuse"] or not r["xor"] or r["add8"] for r in positives_xor):
        return "INVALIDATE_NATIVE_BLOCK_RELATION_GATE"
    controls = [r for r in rows if r["family"] not in {"unique_pair_add8", "unique_pair_xor"}]
    if any(r["add8"] or r["xor"] for r in controls):
        return "INVALIDATE_NATIVE_BLOCK_RELATION_GATE"
    traps = [r for r in rows if r["family"] == "sample_trap"]
    if any(r["sampled_relation_candidates"] == 0 or r["verified_relation_pairs"] != 0 for r in traps):
        return "INVALIDATE_NATIVE_BLOCK_RELATION_GATE"
    if statistics.median(r["wall_ratio"] for r in rows) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_BLOCK_RELATION_GATE"
    if statistics.median(r["cpu_ratio"] for r in rows) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_BLOCK_RELATION_GATE"
    mib = [r for r in rows if r["size"] == 1024 * 1024]
    if statistics.median(r["wall_ratio"] for r in mib) > MAX_1MIB_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_BLOCK_RELATION_GATE"
    if statistics.median(r["cpu_ratio"] for r in mib) > MAX_1MIB_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_BLOCK_RELATION_GATE"
    if max(r["wall_ratio"] for r in mib) > MAX_1MIB_ROW_OVERHEAD or max(r["cpu_ratio"] for r in mib) > MAX_1MIB_ROW_OVERHEAD:
        return "HOLD_NATIVE_BLOCK_RELATION_GATE"
    if any(r["candidate_wall_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S or r["candidate_cpu_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S for r in mib):
        return "HOLD_NATIVE_BLOCK_RELATION_GATE"
    return "ADVANCE_NATIVE_BLOCK_RELATION_GATE"


def main() -> int:
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            data = make_case(family, size)
            has_dup = _has_duplicate_aligned_chunk(data)
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
                "exact_relation_bytes_read": int(c.exact_relation_bytes_read),
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
    mib = [r for r in rows if r["size"] == 1024 * 1024]
    print(json.dumps({
        "experiment": "ONE-G0.2 native nonredundant block relation gate",
        "decision": decision,
        "repetitions": REPETITIONS,
        "sample_offsets": SAMPLE_OFFSETS,
        "median_wall_ratio": statistics.median(r["wall_ratio"] for r in rows),
        "median_cpu_ratio": statistics.median(r["cpu_ratio"] for r in rows),
        "median_1mib_wall_ratio": statistics.median(r["wall_ratio"] for r in mib),
        "median_1mib_cpu_ratio": statistics.median(r["cpu_ratio"] for r in mib),
        "worst_1mib_wall_ratio": max(r["wall_ratio"] for r in mib),
        "worst_1mib_cpu_ratio": max(r["cpu_ratio"] for r in mib),
        "rows": rows,
    }, sort_keys=True))
    return 0 if decision == "ADVANCE_NATIVE_BLOCK_RELATION_GATE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
