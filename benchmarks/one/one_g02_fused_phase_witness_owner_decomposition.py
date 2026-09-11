"""ONE-G0.2 native owner decomposition for the rejected fused phase witness."""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_fused_phase_witness_native_cost import (
    LARGE_REPS,
    REPETITIONS,
    Stats,
    _buf,
    _c_source as _parent_c_source,
    _cases,
    _native_cert,
    _reference,
)

GATE_NAMES = {
    "random_1mib",
    "compressed_like_1mib",
    "repeated_1mib",
    "shifted_version_1mib",
    "zeros_1mib",
}


def _c_source() -> str:
    base = _parent_c_source()
    marker = "uint64_t run_baseline"
    if marker not in base:
        raise RuntimeError("parent native source shape changed")
    extra = r'''
static inline uint64_t word_once(const uint8_t*d,size_t n,uint64_t *anchors) {
  uint64_t pre=0,word=0;size_t run=0;uint8_t rv=0;
  for(size_t i=0;i<n;i++){
    uint8_t v=d[i];if(!run||v!=rv){rv=v;run=1;}else run++;
    pre=(pre<<1)+G[v];if(i+1>=64u&&!(pre&MASK))(*anchors)++;
    if(i<8u) word|=((uint64_t)v)<<(8u*i); else word=(word>>8)|((uint64_t)v<<56);
  }
  return pre+word+run;
}
static inline uint64_t hash_once(const uint8_t*d,size_t n,uint64_t *anchors,uint64_t *samples) {
  uint64_t pre=0,word=0,hacc=0;size_t run=0;uint8_t rv=0;
  for(size_t i=0;i<n;i++){
    uint8_t v=d[i];if(!run||v!=rv){rv=v;run=1;}else run++;
    pre=(pre<<1)+G[v];if(i+1>=64u&&!(pre&MASK))(*anchors)++;
    if(i<8u) word|=((uint64_t)v)<<(8u*i); else word=(word>>8)|((uint64_t)v<<56);
    if(i>=7u){uint32_t pos=(uint32_t)(i-7u);int q=pidx(pos&31u);if(q>=0){hacc^=mix64(word^UINT64_C(0x9E3779B97F4A7C15))+(uint64_t)pos;(*samples)++;}}
  }
  return pre+word+run+hacc;
}
uint64_t run_word(const uint8_t*d,size_t n,unsigned reps,stats_t*out){
  uint64_t x=0,a=0;for(unsigned r=0;r<reps;r++)x^=word_once(d,n,&a)+(uint64_t)r;ESC^=x;
  if(out){out->checksum=x;out->anchors=a;out->samples=out->admissions=out->replacements=0;}return x;
}
uint64_t run_hash(const uint8_t*d,size_t n,unsigned reps,stats_t*out){
  uint64_t x=0,a=0,s=0;for(unsigned r=0;r<reps;r++)x^=hash_once(d,n,&a,&s)+(uint64_t)r;ESC^=x;
  if(out){out->checksum=x;out->anchors=a;out->samples=s;out->admissions=out->replacements=0;}return x;
}
'''
    return base.replace(marker, extra + "\n" + marker, 1)


def _build(td: str):
    src = Path(td) / "native.c"
    so = Path(td) / "native.so"
    src.write_text(_c_source())
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", str(src), "-o", str(so)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lib = ctypes.CDLL(str(so))
    p8 = ctypes.POINTER(ctypes.c_uint8)
    for name in ("run_baseline", "run_word", "run_hash", "run_fused"):
        fn = getattr(lib, name)
        fn.argtypes = [p8, ctypes.c_size_t, ctypes.c_uint, ctypes.POINTER(Stats)]
        fn.restype = ctypes.c_uint64
    lib.phase_exact.argtypes = [
        p8,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.phase_exact.restype = ctypes.c_int
    return lib


def _sample(fn, b, n: int, reps: int):
    vals = []
    last = Stats()
    for _ in range(REPETITIONS):
        st = Stats()
        t0 = time.perf_counter_ns()
        fn(b, n, reps, ctypes.byref(st))
        vals.append(time.perf_counter_ns() - t0)
        last = st
    return int(statistics.median(vals)), last


def run():
    rows = []
    mismatches = []
    with tempfile.TemporaryDirectory(prefix="one_fused_phase_owner_") as td:
        lib = _build(td)
        cases = _cases()
        for name, data in cases.items():
            if _native_cert(lib, data) != _reference(data):
                mismatches.append(name)
        for name, data in cases.items():
            b = _buf(data)
            n = len(data)
            reps = LARGE_REPS if n >= 1024 * 1024 - 1024 else (1024 if n >= 4096 else 65536)
            bt, bs = _sample(lib.run_baseline, b, n, reps)
            wt, ws = _sample(lib.run_word, b, n, reps)
            ht, hs = _sample(lib.run_hash, b, n, reps)
            ft, fs = _sample(lib.run_fused, b, n, reps)
            logical = n * reps
            increments = {
                "raw_window_ns_per_input_byte": (wt - bt) / logical,
                "phase_hash_ns_per_input_byte": (ht - wt) / logical,
                "bottom_k_ns_per_input_byte": (ft - ht) / logical,
            }
            owner = max(increments, key=increments.get)
            rows.append(
                {
                    "case": name,
                    "input_bytes": n,
                    "internal_repetitions": reps,
                    "baseline_median_ns": bt,
                    "word_median_ns": wt,
                    "hash_median_ns": ht,
                    "full_median_ns": ft,
                    "word_over_baseline": wt / bt,
                    "hash_over_baseline": ht / bt,
                    "full_over_baseline": ft / bt,
                    **increments,
                    "largest_increment": owner,
                    "anchors_baseline": int(bs.anchors),
                    "anchors_full": int(fs.anchors),
                    "phase_samples_hash": int(hs.samples),
                    "phase_samples_full": int(fs.samples),
                    "witness_admissions_full": int(fs.admissions),
                    "heap_replacements_full": int(fs.replacements),
                    "native_witness_equal_reference": name not in mismatches,
                }
            )
    large = [r for r in rows if r["case"] in GATE_NAMES]
    counts = {k: 0 for k in ("raw_window_ns_per_input_byte", "phase_hash_ns_per_input_byte", "bottom_k_ns_per_input_byte")}
    for row in large:
        counts[row["largest_increment"]] += 1
    stable = [k for k, v in counts.items() if v >= 4]
    if mismatches:
        decision = "invalid_witness_mismatch"
    elif stable:
        decision = "stable_owner:" + stable[0]
    else:
        decision = "co_dominant_cost_cluster"
    return {
        "schema": "cmpct-one-g02-fused-phase-witness-owner-decomposition-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "parent_rejected_source_sha": "df083da415fb8aa426c3f6a1ed84cd6d25f5e32d",
        "native_witness_mismatches": mismatches,
        "large_owner_counts": counts,
        "decision": decision,
        "claim_boundary": "cost-owner attribution only; rejected unconditional fused path remains retired",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(2 if result["decision"] == "invalid_witness_mismatch" else 0)
