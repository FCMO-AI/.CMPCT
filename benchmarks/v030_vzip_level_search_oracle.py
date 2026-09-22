from __future__ import annotations

"""Charged oracle for exact Deflate-level search cost in hidden ZIP-family containers.

This does not change archive semantics.  It measures the current exhaustive 0..9 search against a
semantics-identical ordering that tries common creator levels first and still exhausts every level
before declaring a stream non-reproducible.  Equality is byte-for-byte raw Deflate equality.
"""

import json, os, time, zipfile, zlib
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029

LIKELY_ORDER=(6,9,1,3,5,7,8,4,2,0)
CURRENT_ORDER=tuple(range(10))


def _payload(ap:Path, zi:zipfile.ZipInfo)->bytes:
    from cmpct.codec import LFH
    with ap.open('rb') as f:
        f.seek(zi.header_offset); v=LFH.unpack(f.read(LFH.size)); nl,xl=v[-2],v[-1]
        f.seek(nl+xl,1); return f.read(zi.compress_size)


def _search(raw:bytes,target:bytes,order:tuple[int,...])->tuple[int|None,int,float]:
    t=time.process_time(); attempts=0
    for level in order:
        attempts+=1
        co=zlib.compressobj(level,zlib.DEFLATED,-15); got=co.compress(raw)+co.flush()
        if got==target:return level,attempts,time.process_time()-t
    return None,attempts,time.process_time()-t


def run(work:Path)->dict:
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_vzip_level_neutral')
    repair=V029._load(V029.REPAIR_PATH,'cmpct_v030_vzip_level_repair'); repair.install_generation_hooks(neutral)
    root=work/'neutral'; neutral.build(root); repair.normalize_root(root)
    rows=[]; rejected=[]
    for family in ('02_office_workspace','04_analytics_and_database'):
        src=root/family
        for ap in sorted(p for p in src.rglob('*') if p.is_file()):
            with ap.open('rb') as f:
                if f.read(4)!=b'PK\x03\x04':continue
            try:
                z=zipfile.ZipFile(ap)
            except zipfile.BadZipFile:
                rejected.append(ap.relative_to(src).as_posix());continue
            with z:
                for zi in z.infolist():
                    if zi.is_dir() or zi.compress_type!=zipfile.ZIP_DEFLATED:continue
                    raw=z.read(zi); target=_payload(ap,zi)
                    a=_search(raw,target,CURRENT_ORDER); b=_search(raw,target,LIKELY_ORDER)
                    if a[0]!=b[0]:raise RuntimeError('search order changed exact-level result')
                    rows.append({'family':family,'container':ap.relative_to(src).as_posix(),'member':zi.filename,'raw_bytes':len(raw),'deflate_bytes':len(target),'level':a[0],'current_attempts':a[1],'likely_attempts':b[1],'current_cpu_s':a[2],'likely_cpu_s':b[2]})
    cur=sum(r['current_cpu_s'] for r in rows); likely=sum(r['likely_cpu_s'] for r in rows)
    return {'schema':'cmpct-v030-vzip-level-search-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'rows':rows,'rejected_pk_like':rejected,'summary':{'members':len(rows),'reproducible':sum(r['level'] is not None for r in rows),'current_attempts':sum(r['current_attempts'] for r in rows),'likely_attempts':sum(r['likely_attempts'] for r in rows),'current_cpu_s':cur,'likely_cpu_s':likely,'cpu_saved_s':cur-likely,'speedup':cur/likely if likely else None},'contract':{'diagnostic_only':True,'archive_semantics_changed':False,'all_levels_exhausted_before_failure':True,'exact_stream_equality_required':True,'search_disagreement_fails_run':True},'decision':'If common-first ordering materially reduces CPU with identical level results, use it as the first semantics-preserving VZIP productization speed repair; otherwise retire search order and profile inflate/recipe ownership.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/vzip-level-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/vzip-level-search.json'));a=p.parse_args();a.work_root.mkdir(parents=True,exist_ok=True);d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['summary'],indent=2))
