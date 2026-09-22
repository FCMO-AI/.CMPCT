from __future__ import annotations
"""Final-form falsifier for bounded-regret level-6-first Deflate search inside proven information-yield admission."""
import argparse,hashlib,json,os,shutil,statistics,time,zlib
from pathlib import Path
from benchmarks import v030_r4_content_zip_information_yield_gate as YIELD
from benchmarks import v030_release_generalization as GENERAL
from cmpct import codec
# #196's 180 Office streams all reproduce at level 6. Put only that proven owner first, then preserve
# canonical 0..9 order for every remaining level. Relative to canonical search, non-6 targets pay at most
# one extra attempt (levels 0..5) and levels 7..9 pay none; this avoids the large level-0/2 regressions
# exposed by adversarial synthetic replay of the earlier heuristic common-first permutation.
LEVEL6_FIRST=(6,0,1,2,3,4,5,7,8,9);REPS=3

def _search(raw:bytes,target:bytes,order=LEVEL6_FIRST):
    for level in order:
        co=zlib.compressobj(level,zlib.DEFLATED,-15)
        if co.compress(raw)+co.flush()==target:return level
    return None

def _one(source:Path,work:Path,label:str,fast:bool):
    work.mkdir(parents=True,exist_ok=True);arc=work/f'{label}.cmpct';out=work/f'{label}-out';original=codec.deflate_level_for
    if fast:codec.deflate_level_for=_search
    try:
        cpu=time.process_time();wall=time.perf_counter();stats=YIELD.InformationYieldBuilder(source).build(arc);cpu=time.process_time()-cpu;wall=time.perf_counter()-wall;verify=YIELD._verify(arc,source,out)
    finally:codec.deflate_level_for=original
    return {'archive_bytes':arc.stat().st_size,'archive_sha256':hashlib.sha256(arc.read_bytes()).hexdigest(),'create_cpu_s':cpu,'create_wall_s':wall,'tree_sha256':verify['tree_sha256'],'vzip_file_count':verify['vzip_file_count'],'range_checks':len(verify['range_checks']),'admitted_hidden_zip_files':stats['information_yield_gate']['admitted_hidden_zip_files']}

def run(work:Path):
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_fastzip_n');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_fastzip_r');repair.install_generation_hooks(neutral)
    root=work/'neutral';neutral.build(root);repair.normalize_root(root);office=root/'02_office_workspace';rows=[]
    for label,fast in [('current-0',False),('fast-0',True),('fast-1',True),('current-1',False),('current-2',False),('fast-2',True)]:
        row=_one(office,work/'runs',label,fast);row.update({'label':label,'fast':fast});rows.append(row);print(json.dumps(row),flush=True)
    cur=[r for r in rows if not r['fast']];fast=[r for r in rows if r['fast']];cur_bytes={r['archive_bytes'] for r in cur};fast_bytes={r['archive_bytes'] for r in fast};cur_sha={r['archive_sha256'] for r in cur};fast_sha={r['archive_sha256'] for r in fast}
    if len(cur_bytes)!=1 or len(fast_bytes)!=1 or len(cur_sha)!=1 or len(fast_sha)!=1:raise RuntimeError('nondeterministic final archive identity')
    if len({r['tree_sha256'] for r in rows})!=1:raise RuntimeError('tree identity changed')
    if len({r['admitted_hidden_zip_files'] for r in rows})!=1:raise RuntimeError('admission changed')
    floor=int(GENERAL._accepted_v029_rows()[('neutral_hostile_v1','02_office_workspace')]['accepted_v029_bytes'])
    summary={'accepted_v029_bytes':floor,'current_archive_bytes':next(iter(cur_bytes)),'fast_archive_bytes':next(iter(fast_bytes)),'current_archive_sha256':next(iter(cur_sha)),'fast_archive_sha256':next(iter(fast_sha)),'archive_delta_bytes':next(iter(fast_bytes))-next(iter(cur_bytes)),'fast_gap_vs_v029_bytes':next(iter(fast_bytes))-floor,'current_cpu_median_s':statistics.median(r['create_cpu_s'] for r in cur),'fast_cpu_median_s':statistics.median(r['create_cpu_s'] for r in fast),'current_wall_median_s':statistics.median(r['create_wall_s'] for r in cur),'fast_wall_median_s':statistics.median(r['create_wall_s'] for r in fast)}
    summary['cpu_ratio']=summary['fast_cpu_median_s']/summary['current_cpu_median_s'];summary['wall_ratio']=summary['fast_wall_median_s']/summary['current_wall_median_s']
    original=codec.deflate_level_for;codec.deflate_level_for=_search
    try:hostiles=YIELD._hostiles(work/'hostiles-fast')
    finally:codec.deflate_level_for=original
    supported=summary['archive_delta_bytes']<=0 and summary['cpu_ratio']<0.90 and summary['wall_ratio']<0.90 and all(v['passes'] for v in hostiles.values())
    return {'schema':'cmpct-v030-content-zip-fast-search-integration-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'order':list(LEVEL6_FIRST),'search_policy':'proven-owner-first-then-stable-canonical-order','worst_case_extra_attempts_for_non6_target':1,'repetitions_per_arm':REPS,'rows':rows,'summary':summary,'hostiles':hostiles,'hypothesis':{'supported_for_fused_scan_next_rung':supported},'contract':{'diagnostic_only':True,'shipping_code_changed':False,'admission_policy_changed':False,'all_levels_exhausted_before_failure':True,'full_tree_verified':True,'range_reads_verified':True,'archive_identity_deterministic_per_arm':True},'decision':'If supported, carry the bounded-regret level-6-first policy into the one-pass research scan/cache integration; otherwise preserve this result and isolate final-byte or remaining create-cost ownership before changing product code.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/fast-search-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/fast-search.json'));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['summary'],indent=2))
if __name__=='__main__':main()
