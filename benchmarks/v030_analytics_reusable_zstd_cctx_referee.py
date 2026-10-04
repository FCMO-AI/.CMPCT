from __future__ import annotations

"""Research-only referee: can one reusable ZSTD_CCtx remove material L19 CPU overhead?

Frozen before measurement.  This changes execution only, not archive grammar, admission, level,
or payload semantics.  Advance at >=20% median zc CPU reduction with byte identity; retire at <=5%;
5-20% is ambiguous.  No release/product credit.
"""
import argparse, ctypes, json, statistics, time
from pathlib import Path
import shutil

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25

TARGET="04_analytics_and_database"; LEVEL=19; ROUNDS=5

class Reuser:
    def __init__(self):
        self.z=V25.z; sz=ctypes.c_size_t
        self.z.ZSTD_createCCtx.argtypes=[]; self.z.ZSTD_createCCtx.restype=ctypes.c_void_p
        self.z.ZSTD_freeCCtx.argtypes=[ctypes.c_void_p]; self.z.ZSTD_freeCCtx.restype=sz
        self.z.ZSTD_compressCCtx.argtypes=[ctypes.c_void_p,ctypes.c_void_p,sz,ctypes.c_void_p,sz,ctypes.c_int]
        self.z.ZSTD_compressCCtx.restype=sz
        self.ctx=self.z.ZSTD_createCCtx()
        if not self.ctx: raise RuntimeError("ZSTD_createCCtx failed")
    def close(self):
        if self.ctx: self.z.ZSTD_freeCCtx(self.ctx); self.ctx=None
    def zc(self,b:bytes,l:int=19)->bytes:
        if not b:return b''
        s=ctypes.create_string_buffer(b); cap=int(self.z.ZSTD_compressBound(len(b))); d=ctypes.create_string_buffer(cap)
        n=int(self.z.ZSTD_compressCCtx(self.ctx,d,cap,s,len(b),l)); return d.raw[:n]


def _build(stage:Path, root:Path, mode:str, verify_identity:bool=False)->dict:
    real=V25.zc; old=CANON.LEVEL_CAP; cpu=0.0; calls=0; mismatches=0
    r=Reuser() if mode=="reuse" else None
    def wrapped(b:bytes,l:int=19)->bytes:
        nonlocal cpu,calls,mismatches
        calls+=1; t=time.process_time()
        out=(r.zc(b,l) if r else real(b,l)); cpu+=time.process_time()-t
        if verify_identity and r:
            ref=real(b,l)
            if out!=ref:mismatches+=1
        return out
    V25.zc=wrapped; CANON.LEVEL_CAP=LEVEL
    try: res=dict(CANON._canonical_v25(stage,root))
    finally:
        V25.zc=real; CANON.LEVEL_CAP=old
        if r:r.close()
    res.update(zc_cpu_s=cpu,zc_calls=calls,zc_byte_mismatches=mismatches); return res


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cctx_neutral')
    repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cctx_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus)
    stage=EXT._normalized_stage(corpus/TARGET,work/'normalized')

    # One untimed full-call identity pass: every compressed payload must equal the one-shot implementation.
    ident=_build(stage,work/'identity','reuse',True)
    if ident['zc_byte_mismatches']!=0: raise RuntimeError(f"payload mismatch count={ident['zc_byte_mismatches']}")

    cpu={"oneshot":[],"reuse":[]}; total={"oneshot":[],"reuse":[]}; sizes={"oneshot":set(),"reuse":set()}
    for i in range(ROUNDS):
        order=("oneshot","reuse") if i%2==0 else ("reuse","oneshot")
        for mode in order:
            root=work/f"r{i}-{mode}";root.mkdir()
            t=time.perf_counter();res=_build(stage,root,mode);total[mode].append(time.perf_counter()-t)
            cpu[mode].append(float(res['zc_cpu_s']));sizes[mode].add(int(res['archive_bytes']))
    if any(len(v)!=1 for v in sizes.values()):raise RuntimeError(f"nondeterministic sizes {sizes}")
    b={k:next(iter(v)) for k,v in sizes.items()}; mc={k:statistics.median(v) for k,v in cpu.items()}; mt={k:statistics.median(v) for k,v in total.items()}
    byte_identity=(b['oneshot']==b['reuse']==int(ident['archive_bytes']))
    cpu_gain=(mc['oneshot']-mc['reuse'])/mc['oneshot'] if mc['oneshot'] else 0.0
    total_gain=(mt['oneshot']-mt['reuse'])/mt['oneshot'] if mt['oneshot'] else 0.0
    decision=('ADVANCE_REUSABLE_CCTX' if byte_identity and cpu_gain>=0.20 else 'RETIRE_REUSABLE_CCTX' if (not byte_identity or cpu_gain<=0.05) else 'AMBIGUOUS_REUSABLE_CCTX')
    return {
      'schema':'cmpct-v030-analytics-reusable-zstd-cctx-v1','target':f'neutral_hostile_v1/{TARGET}','release_credit':False,'rounds':ROUNDS,
      'frozen_gate':{'advance_zc_cpu_reduction_fraction':0.20,'retire_at_or_below_fraction':0.05,'exact_payload_identity_required':True},
      'identity_pass':{'archive_bytes':ident['archive_bytes'],'zc_calls':ident['zc_calls'],'zc_byte_mismatches':ident['zc_byte_mismatches']},
      'archive_bytes':b,'zc_cpu_s':cpu,'total_wall_s':total,'median_zc_cpu_s':mc,'median_total_wall_s':mt,
      'zc_cpu_reduction_fraction':cpu_gain,'total_wall_reduction_fraction':total_gain,'byte_identity':byte_identity,'decision':decision,
      'claim_boundary':'Research-only execution-architecture referee; no format, admission, threshold, product, or release credit.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-analytics-reusable-cctx-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-analytics-reusable-cctx.json'));a=p.parse_args()
    r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('archive_bytes','median_zc_cpu_s','median_total_wall_s','zc_cpu_reduction_fraction','decision')},indent=2),flush=True)
if __name__=='__main__':main()
