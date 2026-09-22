from __future__ import annotations

"""Final-form falsifier for common-first Deflate search inside proven information-yield admission.

Research only. It changes no shipping code. The test composes the accepted R4 admission policy with a
semantics-equivalent exhaustive Deflate-level order, then charges complete archive bytes and end-to-end
Office create CPU/wall while preserving full-tree and range reconstruction proof.
"""

import argparse, json, os, shutil, statistics, time, zlib
from pathlib import Path

from benchmarks import v030_r4_content_zip_information_yield_gate as YIELD
from benchmarks import v030_release_generalization as GENERAL
from cmpct import codec

COMMON_FIRST=(6,9,1,3,5,7,8,4,2,0)
REPS=3


def _search(raw:bytes,target:bytes,order=COMMON_FIRST):
    for level in order:
        co=zlib.compressobj(level,zlib.DEFLATED,-15)
        if co.compress(raw)+co.flush()==target:return level
    return None


def _one(source:Path,work:Path,label:str,fast:bool):
    work.mkdir(parents=True,exist_ok=True)
    arc=work/f'{label}.cmpct'; out=work/f'{label}-out'; original=codec.deflate_level_for
    if fast:codec.deflate_level_for=_search
    try:
        cpu=time.process_time();wall=time.perf_counter();stats=YIELD.InformationYieldBuilder(source).build(arc)
        cpu=time.process_time()-cpu;wall=time.perf_counter()-wall;verify=YIELD._verify(arc,source,out)
    finally:codec.deflate_level_for=original
    return {'archive_bytes':arc.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall,'tree_sha256':verify['tree_sha256'],
            'vzip_file_count':verify['vzip_file_count'],'range_checks':len(verify['range_checks']),
            'admitted_hidden_zip_files':stats['information_yield_gate']['admitted_hidden_zip_files']}


def run(work:Path):
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_fastzip_n')
    repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_fastzip_r');repair.install_generation_hooks(neutral)
    root=work/'neutral';neutral.build(root);repair.normalize_root(root);office=root/'02_office_workspace';rows=[]
    plan=[('current-0',False),('fast-0',True),('fast-1',True),('current-1',False),('current-2',False),('fast-2',True)]
    for label,fast in plan:
        row=_one(office,work/'runs',label,fast);row.update({'label':label,'fast':fast});rows.append(row);print(json.dumps(row),flush=True)
    cur=[r for r in rows if not r['fast']];fast=[r for r in rows if r['fast']];cur_bytes={r['archive_bytes'] for r in cur};fast_bytes={r['archive_bytes'] for r in fast}
    if len(cur_bytes)!=1 or len(fast_bytes)!=1:raise RuntimeError('nondeterministic final archive size')
    if len({r['tree_sha256'] for r in rows})!=1:raise RuntimeError('tree identity changed')
    if len({r['admitted_hidden_zip_files'] for r in rows})!=1:raise RuntimeError('admission changed')
    summary={'current_archive_bytes':next(iter(cur_bytes)),'fast_archive_bytes':next(iter(fast_bytes)),'archive_delta_bytes':next(iter(fast_bytes))-next(iter(cur_bytes)),
             'current_cpu_median_s':statistics.median(r['create_cpu_s'] for r in cur),'fast_cpu_median_s':statistics.median(r['create_cpu_s'] for r in fast),
             'current_wall_median_s':statistics.median(r['create_wall_s'] for r in cur),'fast_wall_median_s':statistics.median(r['create_wall_s'] for r in fast)}
    summary['cpu_ratio']=summary['fast_cpu_median_s']/summary['current_cpu_median_s'];summary['wall_ratio']=summary['fast_wall_median_s']/summary['current_wall_median_s']
    original=codec.deflate_level_for;codec.deflate_level_for=_search
    try:hostiles=YIELD._hostiles(work/'hostiles-fast')
    finally:codec.deflate_level_for=original
    supported=(summary['archive_delta_bytes']<=0 and summary['cpu_ratio']<0.90 and summary['wall_ratio']<0.90 and all(v['passes'] for v in hostiles.values()))
    return {'schema':'cmpct-v030-content-zip-fast-search-integration-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'order':list(COMMON_FIRST),'repetitions_per_arm':REPS,
            'rows':rows,'summary':summary,'hostiles':hostiles,'hypothesis':{'supported_for_fused_scan_next_rung':supported},
            'contract':{'diagnostic_only':True,'shipping_code_changed':False,'admission_policy_changed':False,'all_levels_exhausted_before_failure':True,'full_tree_verified':True,'range_reads_verified':True},
            'decision':'If supported, fold common-first search into the one-pass research scan/cache integration; otherwise preserve this result and isolate final-byte or remaining create-cost ownership before changing product code.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/fast-search-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/fast-search.json'));a=p.parse_args()
    d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['summary'],indent=2))

if __name__=='__main__':main()
