"""ONE-G0.2 native carrying-cost A/B for prefix-Gear-difference phase witnesses."""
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
    Stats,
    _buf,
    _c_source as _parent_c_source,
    _cases,
    _native_cert as _raw_native_cert,
    _reference as _raw_reference,
)
from benchmarks.one.one_g02_gear_difference_phase_certificate_validation import _source_certificate as _gear_reference_source

PAIRED_ROUNDS = 9
MODELED_INCREMENTAL_STATE_BYTES = 280
GATE_NAMES = {
    "random_1mib",
    "compressed_like_1mib",
    "repeated_1mib",
    "shifted_version_1mib",
    "zeros_1mib",
}


def _c_source() -> str:
    src = _parent_c_source()
    marker = "uint64_t run_baseline"
    extra = r'''
static inline int save_q(unsigned phase) {
  return phase==31?0:phase==0?1:phase==1?2:phase==29?3:phase==30?4:-1;
}
static inline int end_q(unsigned phase) {
  return phase==7?0:phase==8?1:phase==9?2:phase==5?3:phase==6?4:-1;
}
static inline uint64_t gear_diff_once(const uint8_t*d,size_t n,uint64_t *anchors,uint64_t *samples,uint64_t *adm,uint64_t *rep) {
  uint64_t pre=0,hs[P][K]={{0}},snap[P]={0};uint32_t ps[P][K]={{0}};unsigned cnt[P]={0};size_t run=0;uint8_t rv=0;
  for(size_t i=0;i<n;i++) {
    uint8_t v=d[i];if(!run||v!=rv){rv=v;run=1;}else run++;
    pre=(pre<<1)+G[v];if(i+1>=64u&&!(pre&MASK))(*anchors)++;
    unsigned phase=(unsigned)(i&31u);
    int eq=end_q(phase);
    if(eq>=0 && i>=7u) {
      uint32_t pos=(uint32_t)(i-7u);
      uint64_t local=pre-(snap[eq]<<8);
      uint64_t h=mix64(local^UINT64_C(0x9E3779B97F4A7C15));
      offer(h,pos,hs[eq],ps[eq],&cnt[eq],adm,rep);(*samples)++;
    }
    int sq=save_q(phase);if(sq>=0)snap[sq]=pre;
  }
  uint64_t z=pre+run;for(unsigned q=0;q<P;q++)for(unsigned j=0;j<cnt[q];j++)z^=hs[q][j]+((uint64_t)ps[q][j]<<((q+j)&31u));return z;
}
uint64_t run_gear_diff(const uint8_t*d,size_t n,unsigned reps,stats_t*out){
  uint64_t x=0,a=0,s=0,m=0,rp=0;for(unsigned r=0;r<reps;r++)x^=gear_diff_once(d,n,&a,&s,&m,&rp)+(uint64_t)r;ESC^=x;
  if(out){out->checksum=x;out->anchors=a;out->samples=s;out->admissions=m;out->replacements=rp;}return x;
}
int gear_phase_exact(const uint8_t*d,size_t n,uint64_t out_h[P*K],uint32_t out_p[P*K],uint8_t out_phase[P*K]) {
  uint64_t pre=0,hs[P][K]={{0}},snap[P]={0};uint32_t ps[P][K]={{0}};unsigned cnt[P]={0};uint64_t a=0,r=0;
  for(size_t i=0;i<n;i++) {
    pre=(pre<<1)+G[d[i]];unsigned phase=(unsigned)(i&31u);int eq=end_q(phase);
    if(eq>=0 && i>=7u){uint32_t pos=(uint32_t)(i-7u);uint64_t local=pre-(snap[eq]<<8);offer(mix64(local^UINT64_C(0x9E3779B97F4A7C15)),pos,hs[eq],ps[eq],&cnt[eq],&a,&r);}
    int sq=save_q(phase);if(sq>=0)snap[sq]=pre;
  }
  unsigned o=0;static const uint8_t pv[P]={0,1,2,30,31};for(unsigned q=0;q<P;q++)for(unsigned j=0;j<cnt[q];j++){out_h[o]=hs[q][j];out_p[o]=ps[q][j];out_phase[o]=pv[q];o++;}return (int)o;
}
'''
    return src.replace(marker, extra + "\n" + marker, 1)


def _build(td: str):
    c_path = Path(td) / "native.c"
    so_path = Path(td) / "native.so"
    c_path.write_text(_c_source())
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", str(c_path), "-o", str(so_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lib = ctypes.CDLL(str(so_path))
    p8 = ctypes.POINTER(ctypes.c_uint8)
    for name in ("run_baseline", "run_fused", "run_gear_diff"):
        fn = getattr(lib, name)
        fn.argtypes = [p8, ctypes.c_size_t, ctypes.c_uint, ctypes.POINTER(Stats)]
        fn.restype = ctypes.c_uint64
    for name in ("phase_exact", "gear_phase_exact"):
        fn = getattr(lib, name)
        fn.argtypes = [p8, ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint8)]
        fn.restype = ctypes.c_int
    return lib


def _native_gear_cert(lib, data: bytes):
    b = _buf(data); hs = (ctypes.c_uint64 * 20)(); ps = (ctypes.c_uint32 * 20)(); ph = (ctypes.c_uint8 * 20)()
    n = lib.gear_phase_exact(b, len(data), hs, ps, ph)
    return sorted((int(hs[i]), int(ps[i]), int(ph[i])) for i in range(n))


def _gear_reference(data: bytes):
    return sorted(_gear_reference_source(data)[0])


def _timed(fn, b, n: int, reps: int):
    st = Stats(); t0 = time.perf_counter_ns(); fn(b, n, reps, ctypes.byref(st)); return time.perf_counter_ns() - t0, st


def _paired(lib, b, n: int, reps: int):
    base=[]; raw=[]; gear=[]; last=(Stats(),Stats(),Stats())
    orders=((lib.run_baseline,base,0),(lib.run_fused,raw,1),(lib.run_gear_diff,gear,2))
    for r in range(PAIRED_ROUNDS):
        seq=orders if r%2==0 else tuple(reversed(orders)); sts=[None,None,None]
        for fn,bucket,idx in seq:
            t,st=_timed(fn,b,n,reps); bucket.append(t); sts[idx]=st
        last=tuple(sts)
    return int(statistics.median(base)),int(statistics.median(raw)),int(statistics.median(gear)),last


def run():
    rows=[]; raw_mismatch=[]; gear_mismatch=[]
    with tempfile.TemporaryDirectory(prefix="one_gear_diff_native_") as td:
        lib=_build(td); cases=_cases()
        for name,data in cases.items():
            if _raw_native_cert(lib,data)!=_raw_reference(data): raw_mismatch.append(name)
            if _native_gear_cert(lib,data)!=_gear_reference(data): gear_mismatch.append(name)
        for name,data in cases.items():
            b=_buf(data); n=len(data); reps=LARGE_REPS if n>=1024*1024-1024 else (1024 if n>=4096 else 65536)
            bt,rt,gt,sts=_paired(lib,b,n,reps)
            bs,rs,gs=sts
            rows.append({
                "case":name,"input_bytes":n,"internal_repetitions":reps,"paired_rounds":PAIRED_ROUNDS,
                "baseline_median_ns":bt,"raw_mixed_median_ns":rt,"gear_difference_mixed_median_ns":gt,
                "raw_over_baseline":rt/bt,"gear_over_baseline":gt/bt,"gear_over_raw":gt/rt,
                "anchors_equal":int(bs.anchors)==int(rs.anchors)==int(gs.anchors),
                "raw_witness_equal_reference":name not in raw_mismatch,"gear_witness_equal_reference":name not in gear_mismatch,
                "raw_samples":int(rs.samples),"gear_samples":int(gs.samples),"raw_admissions":int(rs.admissions),"gear_admissions":int(gs.admissions)
            })
    by={r["case"]:r for r in rows}; large=[r for r in rows if r["case"] in GATE_NAMES]; all1=[r for r in rows if r["input_bytes"]>=1024*1024-1024]
    med_gr=statistics.median(r["gear_over_raw"] for r in large); med_gb=statistics.median(r["gear_over_baseline"] for r in large)
    exact=not raw_mismatch and not gear_mismatch and all(r["anchors_equal"] for r in rows)
    gate=(exact and med_gr<=0.85 and all(r["gear_over_raw"]<=1.03 for r in all1) and by["tiny_4k"]["gear_over_raw"]<=1.05 and by["tiny_64b"]["gear_over_raw"]<=1.10 and MODELED_INCREMENTAL_STATE_BYTES<=280)
    return {
        "schema":"cmpct-one-g02-gear-difference-native-cost-v1","experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "modeled_incremental_state_bytes":MODELED_INCREMENTAL_STATE_BYTES,"raw_witness_mismatches":raw_mismatch,"gear_witness_mismatches":gear_mismatch,
        "large_gate_median_gear_over_raw":med_gr,"large_gate_median_gear_over_baseline":med_gb,
        "decision":"advance_gear_difference_native_rehabilitation" if gate else "retire_gear_difference_direct_compute_repair",
        "original_1p12_gate_recovered":exact and med_gb<=1.12,
        "claim_boundary":"native writer carrying-cost stage only; no density/reader/format/comparator claim","rows":rows
    }


if __name__=="__main__":
    result=run();print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if result["decision"]=="advance_gear_difference_native_rehabilitation" else 2)
