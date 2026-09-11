"""ONE-G0.2 exact-source fused nomination + mirrored-fp8 native A/B.

Frozen by ONE_G02_NATIVE_FUSED_NOMINATION_FP8_MIRRORED_PREREG_2026-09-06.md.
The candidate is mechanically derived from the authoritative fused consumer so
only the local 64-entry lookup representation differs.  Timing stays in C.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_relation_shared_observer_validation import MINIMIZER_SPAN, _cases

WINDOW = 64
SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
BASELINE_BLOB = "89f25972374c747654ddbf631372929b3f21b970"
FP_SOURCE_BLOB = "00af27f2025e4be4bad92a2e5705cb7f91680584"
PRODUCTIVE = {"shift_plus1", "damage_quarter", "fragmented_every96", "fragmented_every32", "local_hit_rich"}
CONTROLS = {"independent_random", "false_pattern"}


class FusedResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64), ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64), ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64), ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64), ("suffix_value_indirect_loads", ctypes.c_uint64),
        ("cross_auditions", ctypes.c_uint64), ("cross_exact", ctypes.c_uint64),
        ("local_peak_entries", ctypes.c_uint64), ("global_peak_entries", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64), ("extension_read_bytes", ctypes.c_uint64),
    ]


class LocalIndexResult(ctypes.Structure):
    _fields_ = [
        ("lookup_events", ctypes.c_uint64), ("hits", ctypes.c_uint64),
        ("full_key_checks", ctypes.c_uint64), ("fingerprint_bytes", ctypes.c_uint64),
        ("live_entries", ctypes.c_uint64), ("decision_checksum", ctypes.c_uint64),
        ("state_bytes", ctypes.c_uint64),
    ]


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _candidate_source(src: str) -> str:
    marker = "static size_t extend_left("
    helper = r'''
static uint8_t one_g02_fp8(uint64_t key) { return (uint8_t)(key >> 56); }

static int find_local_fp8(
    const one_g02_index_entry entries[ONE_G02_LOCAL_ENTRIES],
    const uint8_t fp[ONE_G02_LOCAL_ENTRIES * 2u],
    size_t count,
    size_t head,
    uint64_t key,
    size_t *start_out
) {
    if (count == 0) return 0;
    const uint8_t target = one_g02_fp8(key);
    const uint8_t *cur = fp + head;
    const uint8_t *end = cur + count;
    while (cur < end) {
        const uint8_t *p = (const uint8_t *)memchr(cur, (int)target, (size_t)(end - cur));
        if (p == NULL) return 0;
        const size_t slot = ((size_t)(p - fp)) & (ONE_G02_LOCAL_ENTRIES - 1u);
        if (!entries[slot].used) return -7;
        if (entries[slot].key == key) {
            *start_out = entries[slot].start;
            return 1;
        }
        cur = p + 1;
    }
    return 0;
}

'''
    if marker not in src:
        raise RuntimeError("fused source helper insertion marker moved")
    out = src.replace(marker, helper + marker, 1)
    decl = "    one_g02_index_entry local[ONE_G02_LOCAL_ENTRIES] = {{0}};\n"
    if out.count(decl) != 1:
        raise RuntimeError("local ring declaration boundary moved")
    out = out.replace(decl, decl + "    uint8_t local_fp[ONE_G02_LOCAL_ENTRIES * 2u] = {0};\n", 1)
    old_lookup = """            const int have_prior = find_entry(\n                local, ONE_G02_LOCAL_ENTRIES, local_count, local_head, state, &prior\n            );"""
    new_lookup = """            const int have_prior = find_local_fp8(\n                local, local_fp, local_count, local_head, state, &prior\n            );\n            if (have_prior < 0) goto bad_local_fp;"""
    if out.count(old_lookup) != 1:
        raise RuntimeError("local lookup boundary moved")
    out = out.replace(old_lookup, new_lookup, 1)
    old_insert = """                local[slot].key = state;\n                local[slot].start = start;\n                local[slot].used = 1;\n                if (local_count > out->local_peak_entries) out->local_peak_entries = local_count;"""
    new_insert = """                local[slot].key = state;\n                local[slot].start = start;\n                local[slot].used = 1;\n                local_fp[slot] = one_g02_fp8(state);\n                local_fp[slot + ONE_G02_LOCAL_ENTRIES] = local_fp[slot];\n                if (local_count > out->local_peak_entries) out->local_peak_entries = local_count;"""
    if out.count(old_insert) != 1:
        raise RuntimeError("local insertion boundary moved")
    out = out.replace(old_insert, new_insert, 1)
    old_state = "        sizeof(local) + global_capacity * sizeof(*global);"
    new_state = "        sizeof(local) + sizeof(local_fp) + global_capacity * sizeof(*global);"
    if out.count(old_state) != 1:
        raise RuntimeError("state accounting boundary moved")
    out = out.replace(old_state, new_state, 1)
    cleanup = """bad_state:\n    free(global);"""
    fp_cleanup = """bad_local_fp:\n    free(global);\n    free(block_values);\n    free(suffix_offsets);\n    return -7;\nbad_state:\n    free(global);"""
    if out.count(cleanup) != 1:
        raise RuntimeError("cleanup boundary moved")
    out = out.replace(cleanup, fp_cleanup, 1)
    if out.count("one_g02_fused_native_nomination(") != 1:
        raise RuntimeError("fused symbol boundary moved")
    out = out.replace("one_g02_fused_native_nomination(", "one_g02_fused_native_nomination_fp8(", 1)
    return out


WRAPPER = r'''
#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t emitted, final_state, positions_considered, reserved_state_bytes;
    uint64_t derived_state_reads, suffix_blocks_built, suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads, cross_auditions, cross_exact;
    uint64_t local_peak_entries, global_peak_entries, verification_read_bytes, extension_read_bytes;
} fused_result;

int one_g02_fused_native_nomination_baseline(const uint8_t*, size_t, size_t, const uint64_t[256], size_t, size_t, fused_result*, uint64_t*, size_t);
int one_g02_fused_native_nomination_fp8(const uint8_t*, size_t, size_t, const uint64_t[256], size_t, size_t, fused_result*, uint64_t*, size_t);

static uint64_t now_ns(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}

int one_g02_fused_fp8_measure(const uint8_t *data, size_t length, size_t boundary,
                              const uint64_t gear[256], size_t window, size_t span,
                              size_t batch, fused_result *b, fused_result *c,
                              uint64_t *bt, uint64_t *ct, size_t trace_capacity,
                              double *baseline_ns, double *candidate_ns) {
    if (!batch || !b || !c || !baseline_ns || !candidate_ns) return -100;
    int rc = one_g02_fused_native_nomination_baseline(data,length,boundary,gear,window,span,b,bt,trace_capacity);
    if (rc) return rc;
    rc = one_g02_fused_native_nomination_fp8(data,length,boundary,gear,window,span,c,ct,trace_capacity);
    if (rc) return rc;
    uint64_t t, b1, b2, c1, c2;
    t=now_ns(); for(size_t i=0;i<batch;i++){ rc=one_g02_fused_native_nomination_baseline(data,length,boundary,gear,window,span,b,bt,trace_capacity); if(rc)return rc; } b1=now_ns()-t;
    t=now_ns(); for(size_t i=0;i<batch;i++){ rc=one_g02_fused_native_nomination_fp8(data,length,boundary,gear,window,span,c,ct,trace_capacity); if(rc)return rc; } c1=now_ns()-t;
    t=now_ns(); for(size_t i=0;i<batch;i++){ rc=one_g02_fused_native_nomination_fp8(data,length,boundary,gear,window,span,c,ct,trace_capacity); if(rc)return rc; } c2=now_ns()-t;
    t=now_ns(); for(size_t i=0;i<batch;i++){ rc=one_g02_fused_native_nomination_baseline(data,length,boundary,gear,window,span,b,bt,trace_capacity); if(rc)return rc; } b2=now_ns()-t;
    *baseline_ns=((double)b1+(double)b2)/(2.0*(double)batch);
    *candidate_ns=((double)c1+(double)c2)/(2.0*(double)batch);
    return 0;
}
'''


def _build():
    here = Path(__file__).parent
    fused_path = here / "one_g02_fused_native_nomination_kernel.c"
    fp_path = here / "one_g02_local_index_fingerprint_view_kernel.c"
    fused_bytes = fused_path.read_bytes()
    fp_bytes = fp_path.read_bytes()
    if _git_blob_sha(fused_bytes) != BASELINE_BLOB:
        raise RuntimeError("authoritative fused source blob moved; re-review before benchmarking")
    if _git_blob_sha(fp_bytes) != FP_SOURCE_BLOB:
        raise RuntimeError("promoted fp8 source blob moved; re-review before benchmarking")
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fused-fp8-")
    root = Path(td.name)
    cand = root / "candidate.c"; cand.write_text(_candidate_source(fused_bytes.decode()), encoding="utf-8")
    wrap = root / "wrapper.c"; wrap.write_text(WRAPPER, encoding="utf-8")
    lib = root / "libab.so"
    cc = os.environ.get("CC", "cc")
    base_o = root / "base.o"; cand_o = root / "cand.o"; wrap_o = root / "wrap.o"; fp_o = root / "fp.o"
    common = [cc, "-O3", "-std=c11", "-fPIC", "-c"]
    subprocess.run(common + ["-Done_g02_fused_native_nomination=one_g02_fused_native_nomination_baseline", str(fused_path), "-o", str(base_o)], check=True)
    subprocess.run(common + [str(cand), "-o", str(cand_o)], check=True)
    subprocess.run(common + [str(wrap), "-o", str(wrap_o)], check=True)
    subprocess.run(common + [str(fp_path), "-o", str(fp_o)], check=True)
    subprocess.run([cc, "-shared", str(base_o), str(cand_o), str(wrap_o), str(fp_o), "-o", str(lib)], check=True)
    c = ctypes.CDLL(str(lib))
    measure = c.one_g02_fused_fp8_measure
    measure.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
                        ctypes.c_size_t, ctypes.POINTER(FusedResult), ctypes.POINTER(FusedResult),
                        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
    measure.restype = ctypes.c_int
    local_audit = c.one_g02_local_index_fp_audit
    local_audit.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(LocalIndexResult), ctypes.POINTER(LocalIndexResult)]
    local_audit.restype = ctypes.c_int
    return measure, local_audit, td


def _false_pattern(size: int, seed: int) -> tuple[bytes, bytes]:
    # Similar short prefixes, deliberately no 64-byte identity.
    a = bytearray(((i * 131 + seed * 17) & 255) for i in range(size))
    b = bytearray(a)
    for i in range(0, size, 61): b[i] ^= 0x5A
    return bytes(a), bytes(b)


def _local_hit_rich(size: int, seed: int) -> tuple[bytes, bytes]:
    blocks = []
    for j in range(max(4, size // 64)):
        k = (j % 16) ^ seed
        blocks.append(bytes(((k * 29 + i * 7) & 255) for i in range(64)))
    blob = b"".join(blocks)[:size]
    return blob, blob


def _same_except_state(b: FusedResult, c: FusedResult) -> bool:
    for name, _ in FusedResult._fields_:
        if name == "reserved_state_bytes": continue
        if int(getattr(b, name)) != int(getattr(c, name)): return False
    return int(c.reserved_state_bytes) - int(b.reserved_state_bytes) == 128


def _batch(size: int) -> int:
    return max(1, min(64, (256 * 1024) // size))


def run() -> dict[str, object]:
    measure, local_audit, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows, semantic_failures, local_audit_failures = [], [], []
    try:
        for size in SIZES:
            for seed in SEEDS:
                cases = dict(_cases(size, seed))
                cases["false_pattern"] = _false_pattern(size, seed)
                cases["local_hit_rich"] = _local_hit_rich(size, seed)
                for name, (source, target) in cases.items():
                    data = source + target
                    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                    lb, lc = LocalIndexResult(), LocalIndexResult()
                    if local_audit(buf, len(data), gear, ctypes.byref(lb), ctypes.byref(lc)) != 0:
                        local_audit_failures.append((size, seed, name))
                    samples = []
                    last = None
                    for _ in range(7):
                        b, c = FusedResult(), FusedResult()
                        cap = len(data) + 1
                        bt, ct = (ctypes.c_uint64 * cap)(), (ctypes.c_uint64 * cap)()
                        bn, cn = ctypes.c_double(), ctypes.c_double()
                        rc = measure(buf, len(data), len(source), gear, WINDOW, MINIMIZER_SPAN,
                                     _batch(size), ctypes.byref(b), ctypes.byref(c), bt, ct, cap,
                                     ctypes.byref(bn), ctypes.byref(cn))
                        if rc != 0: raise RuntimeError(f"native A/B failed rc={rc} {size=} {seed=} {name=}")
                        btrace = [int(bt[i]) for i in range(int(b.emitted))]
                        ctrace = [int(ct[i]) for i in range(int(c.emitted))]
                        if not _same_except_state(b, c) or btrace != ctrace:
                            semantic_failures.append((size, seed, name))
                        samples.append(float(cn.value) / float(bn.value))
                        last = (b, c, bn.value, cn.value)
                    b, c, bn, cn = last
                    rows.append({"relation_bytes": size, "seed": seed, "case": name,
                                 "ratio_median": statistics.median(samples),
                                 "ratio_samples": samples, "baseline_ns_last": bn, "candidate_ns_last": cn,
                                 "baseline_state_bytes": int(b.reserved_state_bytes),
                                 "candidate_state_bytes": int(c.reserved_state_bytes),
                                 "state_delta_bytes": int(c.reserved_state_bytes)-int(b.reserved_state_bytes),
                                 "local_lookup_events": int(lb.lookup_events), "local_hits": int(lb.hits),
                                 "baseline_full_key_checks": int(lb.full_key_checks),
                                 "candidate_full_key_checks": int(lc.full_key_checks),
                                 "local_decision_checksum_equal": int(lb.decision_checksum)==int(lc.decision_checksum),
                                 "cross_exact": int(c.cross_exact)})
        productive = [r for r in rows if r["case"] in PRODUCTIVE and r["relation_bytes"] >= 16*1024]
        controls = [r for r in rows if r["case"] in CONTROLS]
        prod_median = statistics.median(r["ratio_median"] for r in productive)
        prod_worst = max(r["ratio_median"] for r in productive)
        ctrl_median = statistics.median(r["ratio_median"] for r in controls)
        passed = (not semantic_failures and not local_audit_failures and
                  prod_median <= 0.95 and prod_worst <= 1.03 and ctrl_median <= 1.03 and
                  all(r["state_delta_bytes"] == 128 for r in rows))
        return {"schema":"cmpct-one-g02-native-fused-nomination-fp8-v1",
                "experimental_version":"ONE-G0.2",
                "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
                "baseline_blob":BASELINE_BLOB,"fp_source_blob":FP_SOURCE_BLOB,
                "semantic_failures":semantic_failures,"local_audit_failures":local_audit_failures,
                "productive_median_ratio":prod_median,"productive_worst_ratio":prod_worst,
                "control_median_ratio":ctrl_median,
                "decision":"advance_fused_fp8" if passed else "reject_fused_fp8_speed",
                "rows":rows}
    finally:
        td.cleanup()


if __name__ == "__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"]=="advance_fused_fp8" else 1)
