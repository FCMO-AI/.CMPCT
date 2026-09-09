"""ONE-G0.2 native block-cadence relation-sketch carrying-cost falsifier.

The candidate reuses the already-required aligned 64-byte fingerprint cadence. It does
not maintain per-byte add8/XOR histograms or a lag ring. At each completed block it uses
8 content-derived lanes to form a local add8 sketch and, when a previous block exists,
a lag-64 XOR sketch. A relation is nominated only when the same non-zero value wins in
>=7/8 of eligible blocks. Exact Law proof remains downstream and is not performed here.
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
from benchmarks.one.one_g02_multi_law_gate import FAMILIES as BASE_FAMILIES, SIZES, make_case, oracle_expected

REPETITIONS = 21
LANES = 8
LOCAL_NUM = 6
LOCAL_DEN = 8
GLOBAL_NUM = 7
GLOBAL_DEN = 8
MAX_MEDIAN_OVERHEAD = 1.20
MAX_ROW_OVERHEAD = 1.35
MIN_1MIB_THROUGHPUT_MIB_S = 250.0
FAMILIES = tuple(BASE_FAMILIES)

_BLOCK_C = r'''
static uint64_t mix64(uint64_t x) {
    x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}

int one_gate_block(const uint8_t *data, size_t n, gate_out *out) {
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
    uint64_t run_len = 0, run_support = 0;
    uint64_t add_blocks[HIST] = {0};
    uint64_t xor_blocks[HIST] = {0};
    uint64_t add_eligible = 0, xor_eligible = 0;
    size_t block_start = 0;
    uint64_t previous_hash = 0;
    int have_previous = 0;

    for (size_t p = 0; p < n; ++p) {
        const uint8_t v = data[p];
        if (run_len == 0) { run_value = v; run_len = 1; }
        else if (v == run_value) { ++run_len; }
        else {
            if (run_len >= MIN_RUN) run_support += run_len;
            run_value = v; run_len = 1;
        }

        chunk_hash ^= (uint64_t)v;
        chunk_hash *= FNV_PRIME;
        if (((p + 1) % CHUNK) == 0) {
            if (fp_seen_or_insert(fps, &fp_count, chunk_hash)) ++repeated;

            uint16_t add_hist[HIST] = {0};
            uint16_t xor_hist[HIST] = {0};
            uint64_t lane_state = mix64(chunk_hash ^ (previous_hash + UINT64_C(0x9e3779b97f4a7c15)));
            for (unsigned k = 0; k < 8; ++k) {
                lane_state = mix64(lane_state + UINT64_C(0x9e3779b97f4a7c15) + k);
                const size_t lane = 1u + (size_t)(lane_state % 63u);
                const uint8_t d = (uint8_t)(data[block_start + lane] - data[block_start + lane - 1]);
                ++add_hist[d];
                if (have_previous) {
                    const uint8_t x = (uint8_t)(data[block_start + lane] ^ data[block_start - CHUNK + lane]);
                    ++xor_hist[x];
                }
            }

            uint32_t add_idx = 0, xor_idx = 0;
            uint16_t add_best = 0, xor_best = 0;
            for (uint32_t i = 1; i < HIST; ++i) {
                if (add_hist[i] > add_best) { add_best = add_hist[i]; add_idx = i; }
                if (xor_hist[i] > xor_best) { xor_best = xor_hist[i]; xor_idx = i; }
            }
            ++add_eligible;
            if ((uint32_t)add_best * 8u >= 6u * 8u) ++add_blocks[add_idx];
            if (have_previous) {
                ++xor_eligible;
                if ((uint32_t)xor_best * 8u >= 6u * 8u) ++xor_blocks[xor_idx];
            }

            previous_hash = chunk_hash;
            have_previous = 1;
            chunk_hash = FNV_OFFSET;
            block_start = p + 1;
        }
    }
    if (run_len >= MIN_RUN) run_support += run_len;

    uint64_t best_add = 0, best_xor = 0;
    uint32_t add_idx = 0, xor_idx = 0;
    for (uint32_t i = 1; i < HIST; ++i) {
        if (add_blocks[i] > best_add) { best_add = add_blocks[i]; add_idx = i; }
        if (xor_blocks[i] > best_xor) { best_xor = xor_blocks[i]; xor_idx = i; }
    }
    const int add8 = add_eligible >= 8 && add_idx != 0 && best_add * 8 >= add_eligible * 7;
    const int xor_nom = xor_eligible >= 8 && xor_idx != 0 && best_xor * 8 >= xor_eligible * 7;

    out->run_support = run_support;
    out->reuse_support = repeated * CHUNK;
    out->add8_support = add8 ? best_add * CHUNK : 0;
    out->xor_support = xor_nom ? best_xor * CHUNK : 0;
    out->retained_entries = fp_count;
    out->run = run_support >= MIN_RUN;
    out->reuse = repeated > 0;
    out->add8 = add8;
    out->xor_nom = xor_nom;
    return 0;
}
'''

_C_SOURCE = full._C_SOURCE + _BLOCK_C

@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-block-relation-sketch-"))
    source = build / "kernel.c"; output = build / "libgate.so"
    source.write_text(_C_SOURCE)
    subprocess.run(["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lib = ctypes.CDLL(str(output))
    for name in ("one_gate_baseline", "one_gate_block"):
        fn = getattr(lib, name); fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(full._GateOut)]; fn.restype = ctypes.c_int
    return lib

def _call(name: str, data: bytes) -> full._GateOut:
    n=len(data); buf=(ctypes.c_uint8*n).from_buffer_copy(data) if n else None
    ptr=ctypes.cast(buf,ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out=full._GateOut(); rc=getattr(_library(),name)(ptr,n,ctypes.byref(out))
    if rc: raise RuntimeError(f"{name} failed: {rc}")
    return out

def _decision(out: full._GateOut) -> set[str]:
    return {name for name,flag in (("run",out.run),("reuse",out.reuse),("add8",out.add8),("xor",out.xor_nom)) if flag}

def _measure(data: bytes):
    names=("one_gate_baseline","one_gate_block"); latest={n:_call(n,data) for n in names}; walls={n:[] for n in names}; cpus={n:[] for n in names}
    for rep in range(REPETITIONS):
        order=names if rep%2==0 else names[::-1]
        for name in order:
            w0,c0=time.perf_counter_ns(),time.process_time_ns(); latest[name]=_call(name,data); walls[name].append(time.perf_counter_ns()-w0); cpus[name].append(time.process_time_ns()-c0)
    med=lambda xs: statistics.median(xs)/1e9
    return latest,{n:med(walls[n]) for n in names},{n:med(cpus[n]) for n in names}

def decide(rows: list[dict]) -> str:
    expected=len(SIZES)*len(FAMILIES)
    if len(rows)!=expected or len({(r["size"],r["family"]) for r in rows})!=expected: return "INVALIDATE_BLOCK_RELATION_SKETCH"
    if any(not r["semantic_ok"] or not r["baseline_common_equal"] or r["source_scan_ratio"]!=1.0 for r in rows): return "INVALIDATE_BLOCK_RELATION_SKETCH"
    wr=[r["wall_ratio"] for r in rows]; cr=[r["cpu_ratio"] for r in rows]
    if statistics.median(wr)>MAX_MEDIAN_OVERHEAD or statistics.median(cr)>MAX_MEDIAN_OVERHEAD or max(wr)>MAX_ROW_OVERHEAD or max(cr)>MAX_ROW_OVERHEAD: return "HOLD_BLOCK_RELATION_SKETCH"
    mib=[r for r in rows if r["size"]==1024*1024]
    if any(r["candidate_wall_mib_s"]<MIN_1MIB_THROUGHPUT_MIB_S or r["candidate_cpu_mib_s"]<MIN_1MIB_THROUGHPUT_MIB_S for r in mib): return "HOLD_BLOCK_RELATION_SKETCH"
    return "ADVANCE_BLOCK_RELATION_SKETCH"

def main() -> int:
    rows=[]
    for size in SIZES:
        for family in FAMILIES:
            data=make_case(family,size); latest,walls,cpus=_measure(data); b,c=latest["one_gate_baseline"],latest["one_gate_block"]
            actual=_decision(c); expected=oracle_expected(family)
            common=(bool(b.run)==bool(c.run) and bool(b.reuse)==bool(c.reuse) and int(b.run_support)==int(c.run_support) and int(b.reuse_support)==int(c.reuse_support) and int(b.retained_entries)==int(c.retained_entries))
            bw,cw=walls["one_gate_baseline"],walls["one_gate_block"]; bc,cc=cpus["one_gate_baseline"],cpus["one_gate_block"]; mib=size/(1024*1024)
            rows.append({"size":size,"family":family,"expected":sorted(expected),"actual":sorted(actual),"semantic_ok":actual==expected,"baseline_common_equal":common,"source_scan_ratio":c.source_scan_bytes/max(1,c.input_bytes),"wall_ratio":cw/bw,"cpu_ratio":cc/bc,"candidate_wall_mib_s":mib/cw,"candidate_cpu_mib_s":mib/cc,"add8_support":int(c.add8_support),"xor_support":int(c.xor_support)})
    decision=decide(rows); print(json.dumps({"experiment":"ONE-G0.2 block-cadence relation sketch","decision":decision,"repetitions":REPETITIONS,"lanes":LANES,"local_support":"6/8","global_support":"7/8","rows":rows},sort_keys=True)); return 0 if decision=="ADVANCE_BLOCK_RELATION_SKETCH" else 1

if __name__=="__main__": raise SystemExit(main())
