from __future__ import annotations

"""Hostile locality falsifier for the user-visible NPZ inverse view in the mode-2 owner inversion.

The mode-2 inversion restores the external NPY to ordinary v0.30 ownership, but a user may also
selectively read the original NPZ. Exact raw-DEFLATE regeneration is sequential. This oracle feeds
the exact NPY through the existing zlib-level-6 mode-2 semantic in bounded chunks and records how
much source must be consumed before a 4 KiB compressed-member range can exist.

This is a reconstruction-work falsifier, not a physical-I/O measurement. It intentionally gives the
candidate ideal source I/O; if sequential reconstruction work alone exceeds the inherited <=8x
selective-work target, naïve inverse-view promotion is already blocked.
"""

import argparse, json, shutil, time, zlib
from pathlib import Path
from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_npz_mode2_owner_inversion as M2

SCHEMA='cmpct-v030-r4-mode2-npz-inverse-locality-v1'
REQUEST=4096
MAX_WORK_AMP=8.0
CHUNK=4096


def consumed_to_cover(raw:bytes, level:int, end:int)->tuple[int,int,float]:
    co=zlib.compressobj(level,zlib.DEFLATED,-15)
    produced=0; consumed=0; cpu0=time.process_time()
    for off in range(0,len(raw),CHUNK):
        part=raw[off:off+CHUNK]; consumed+=len(part); produced+=len(co.compress(part))
        if produced>=end: break
    if produced<end:
        produced+=len(co.flush())
    cpu=time.process_time()-cpu0
    return consumed,produced,cpu


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    NEUTRAL.corpus_analytics(work); source=work/'04_analytics_and_database'
    rel=DUAL._npz_relation(source)['accepted']; npz=source/rel['npz_path']; npy=source/rel['npy_path']
    fs=M2._feature_stream(npz,rel['member'])
    if fs['source']!=npy.read_bytes() or fs['level'] is None: raise RuntimeError('mode2 relation invalid')
    stream=fs['stream']; raw=fs['source']; length=min(REQUEST,len(stream))
    starts=sorted({0,max(0,len(stream)//2-length//2),max(0,len(stream)-length)})
    rows=[]
    for start in starts:
        consumed,produced,cpu=consumed_to_cover(raw,int(fs['level']),start+length)
        rows.append({'compressed_start':start,'request_bytes':length,'source_bytes_consumed':consumed,'compressed_bytes_produced_when_covered':produced,'source_reconstruction_work_amplification':consumed/max(1,length),'mode2_cpu_s':cpu})
    maxamp=max(r['source_reconstruction_work_amplification'] for r in rows)
    return {'schema':SCHEMA,'mode2_level':int(fs['level']),'source_npy_bytes':len(raw),'compressed_member_bytes':len(stream),'request_bytes':length,'chunk_bytes':CHUNK,'requests':rows,'max_source_reconstruction_work_amplification':maxamp,'locality_ceiling':MAX_WORK_AMP,'hypothesis':{'naive_inverse_view_meets_8x_reconstruction_work':maxamp<=MAX_WORK_AMP,'naive_inverse_view_requires_rehabilitation':maxamp>MAX_WORK_AMP},'contract':{'diagnostic_only':True,'release_credit':False,'exact_existing_mode2_semantic':True,'ideal_source_io_assumed':True,'reconstruction_work_only_not_physical_io':True,'no_threshold_sweep':True},'next_if_falsified':'preserve mode2 density seed but do not expose large inverse ZIP view without a bounded range representation; consider independent bounded stream slabs/range proofs or keeping exact stream only where access law requires it','next_if_supported':'instrument actual physical source/archive reads and native parity before promotion'}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-mode2-npz-locality-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-mode2-npz-locality.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps({'mode2_level':d['mode2_level'],'source_npy_bytes':d['source_npy_bytes'],'compressed_member_bytes':d['compressed_member_bytes'],'max_source_reconstruction_work_amplification':d['max_source_reconstruction_work_amplification'],'hypothesis':d['hypothesis'],'requests':d['requests']},indent=2))
if __name__=='__main__': main()
