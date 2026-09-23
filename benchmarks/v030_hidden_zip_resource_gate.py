from __future__ import annotations
"""Isolated resource/economics evidence for #205 actual-Builder hidden-ZIP productization.
Fresh child processes make peak RSS arm-local; each fresh Office tree runs A-B-B-A. Promotion classification
uses the current v0.30 lock: median create/extract <=1.10, peak RSS <=1.25, selective reads measured.
"""
import argparse,json,os,resource,shutil,statistics,subprocess,sys,time
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
REPS=3;MAX_MEDIAN_RUNTIME_RATIO=1.10;MAX_PEAK_RSS_RATIO=1.25;TIMING_RELATIVE=0.05;TIMING_ABSOLUTE_S=0.003;RANGE=4096

def _treehash(root:Path)->str:return PRODUCT.treehash(root)
def _confirmed_timing_regression(base:float,candidate:float)->bool:return candidate>base*(1+TIMING_RELATIVE) and candidate-base>TIMING_ABSOLUTE_S

def _hidden_targets(source:Path):
    out=[]
    for p in sorted(x for x in source.rglob('*') if x.is_file()):
        if p.suffix.lower() in {'.zip','.whl'}:continue
        try:
            with p.open('rb') as fh:head=fh.read(4)
        except OSError:continue
        if head==b'PK\x03\x04':out.append(p)
    return out

def _child(source:Path,arm:str,arc:Path,out:Path,result_path:Path)->None:
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct import v030_hidden_zip_builder as HIDDEN_SCAN
    from cmpct import builder_hidden_zip as BRIDGE
    authority=getattr(Builder,"_cmpct_v030_authority_scan",None)
    if authority is None:raise RuntimeError("#205 installer did not retain authority scan")
    scan=authority if arm=="base" else HIDDEN_SCAN._scan_with_hidden_zip;capture={};original_finalize=BRIDGE.finalize_deferred_hidden_files
    def observed_finalize(builder,deferred,*,min_verified_reuse=BRIDGE.MIN_VERIFIED_REUSE):
        phase={};orig_prove=BRIDGE.prove_candidate_zip_ownership;orig_stage=BRIDGE.stage_stable_hidden_cohort;orig_commit=BRIDGE._commit_hidden_winners
        def timed_prove(*args,**kwargs):
            t=time.perf_counter();result=orig_prove(*args,**kwargs);phase['ownership_proof_wall_s']=time.perf_counter()-t;return result
        def timed_stage(*args,**kwargs):
            t=time.perf_counter();result=orig_stage(*args,**kwargs);phase['winner_staging_wall_s']=time.perf_counter()-t;return result
        def timed_commit(*args,**kwargs):
            t=time.perf_counter();result=orig_commit(*args,**kwargs);phase['winner_commit_retention_wall_s']=time.perf_counter()-t;return result
        BRIDGE.prove_candidate_zip_ownership=timed_prove;BRIDGE.stage_stable_hidden_cohort=timed_stage;BRIDGE._commit_hidden_winners=timed_commit
        try:resolved=original_finalize(builder,deferred,min_verified_reuse=min_verified_reuse)
        finally:
            BRIDGE.prove_candidate_zip_ownership=orig_prove;BRIDGE.stage_stable_hidden_cohort=orig_stage;BRIDGE._commit_hidden_winners=orig_commit
        c=resolved.cohort
        capture.update({"proof_io_bytes":int(resolved.proof.io_bytes),"proof_logical_bytes":int(resolved.proof.logical_bytes),"proof_rejects":list(resolved.proof.rejects),"stage_source_bytes_read":int(c.source_bytes_read),"stage_temp_bytes_written":int(c.temporary_bytes_written),"stage_temp_bytes_read":int(c.temporary_bytes_read),"stage_retained_candidate_bytes":int(c.retained_candidate_bytes),"stage_realized":sorted(c.realized),"stage_excluded":sorted(c.excluded),**phase})
        return resolved
    if arm=="candidate":BRIDGE.finalize_deferred_hidden_files=observed_finalize
    old=Builder.scan
    try:
        Builder.scan=scan;cpu0=time.process_time();wall0=time.perf_counter();stats=dict(Builder(source).build(arc));create_cpu=time.process_time()-cpu0;create_wall=time.perf_counter()-wall0
    finally:Builder.scan=old;BRIDGE.finalize_deferred_hidden_files=original_finalize
    targets=_hidden_targets(source);selective=[];sel0=time.perf_counter()
    with CMPCT(arc) as reader:
        for p in targets:
            rel=p.relative_to(source).as_posix();raw=p.read_bytes();ln=min(RANGE,len(raw));start=max(0,len(raw)//2-ln//2);t0=time.perf_counter();got=reader.read_range(rel,start,ln);dt=time.perf_counter()-t0
            if got!=raw[start:start+ln]:raise RuntimeError(f"selective range mismatch {rel}")
            selective.append({"rel":rel,"start":start,"logical_bytes":ln,"wall_s":dt})
    selective_wall=time.perf_counter()-sel0
    want=_treehash(source);shutil.rmtree(out,ignore_errors=True);cpu0=time.process_time();wall0=time.perf_counter()
    with CMPCT(arc) as reader:reader.extractall(out,metadata=True)
    extract_cpu=time.process_time()-cpu0;extract_wall=time.perf_counter()-wall0;got=_treehash(out)
    if got!=want:raise RuntimeError(f"tree mismatch {got} != {want}")
    result={"arm":arm,"archive_bytes":arc.stat().st_size,"create_cpu_s":create_cpu,"create_wall_s":create_wall,"extract_cpu_s":extract_cpu,"extract_wall_s":extract_wall,"peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),"tree_sha256":got,"stats":stats,"hidden_accounting":capture,"selective_read":{"targets":selective,"target_count":len(selective),"logical_bytes":sum(x['logical_bytes'] for x in selective),"wall_s":selective_wall}}
    result_path.parent.mkdir(parents=True,exist_ok=True);result_path.write_text(json.dumps(result,indent=2)+"\n")

def _run_child(script,source,arm,root,tag):
    arc=root/f"{tag}.cmpct";out=root/f"{tag}-out";result=root/f"{tag}.json";env=dict(os.environ);env['PYTHONPATH']=os.getcwd();subprocess.run([sys.executable,os.fspath(script),'--child','--source',os.fspath(source),'--arm',arm,'--arc',os.fspath(arc),'--extract',os.fspath(out),'--child-output',os.fspath(result)],check=True,env=env);return json.loads(result.read_text())
def _median(rows,key):return float(statistics.median(float(row[key]) for row in rows))

def run(root:Path)->dict:
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);script=Path(__file__).resolve();reps=[]
    for rep in range(REPS):
        work=root/f'rep-{rep}';suite_root=work/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_hidden_resource_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_hidden_resource_r_{rep}');repair.install_generation_hooks(n);n.build(suite_root);repair.normalize_root(suite_root);source=suite_root/'02_office_workspace'
        if not source.is_dir():raise RuntimeError('Office workload missing')
        source_hash=_treehash(source);run_root=work/'runs';run_root.mkdir(parents=True);sequence=[]
        for idx,arm in enumerate(('base','candidate','candidate','base')):
            row=_run_child(script,source,arm,run_root,f'{idx}-{arm}')
            if row['tree_sha256']!=source_hash:raise RuntimeError('child source identity drift')
            sequence.append(row)
        base=[sequence[0],sequence[3]];candidate=[sequence[1],sequence[2]]
        reps.append({'rep':rep,'source_tree_sha256':source_hash,'sequence':sequence,'base_create_wall_median_s':_median(base,'create_wall_s'),'candidate_create_wall_median_s':_median(candidate,'create_wall_s'),'base_extract_wall_median_s':_median(base,'extract_wall_s'),'candidate_extract_wall_median_s':_median(candidate,'extract_wall_s'),'base_peak_rss_kib_median':_median(base,'peak_rss_kib'),'candidate_peak_rss_kib_median':_median(candidate,'peak_rss_kib'),'base_selective_wall_median_s':statistics.median(x['selective_read']['wall_s'] for x in base),'candidate_selective_wall_median_s':statistics.median(x['selective_read']['wall_s'] for x in candidate),'base_archive_bytes':base[0]['archive_bytes'],'candidate_archive_bytes':candidate[0]['archive_bytes'],'candidate_hidden_accounting':candidate[0]['hidden_accounting']})
    bc=statistics.median(r['base_create_wall_median_s'] for r in reps);cc=statistics.median(r['candidate_create_wall_median_s'] for r in reps);be=statistics.median(r['base_extract_wall_median_s'] for r in reps);ce=statistics.median(r['candidate_extract_wall_median_s'] for r in reps);br=statistics.median(r['base_peak_rss_kib_median'] for r in reps);cr=statistics.median(r['candidate_peak_rss_kib_median'] for r in reps);bs=statistics.median(r['base_selective_wall_median_s'] for r in reps);cs=statistics.median(r['candidate_selective_wall_median_s'] for r in reps)
    saving=[r['base_archive_bytes']-r['candidate_archive_bytes'] for r in reps];create_ratio=cc/bc;extract_ratio=ce/be;rss_ratio=cr/br;selective_ratio=cs/bs if bs else None
    lock_pass=create_ratio<=MAX_MEDIAN_RUNTIME_RATIO and extract_ratio<=MAX_MEDIAN_RUNTIME_RATIO and rss_ratio<=MAX_PEAK_RSS_RATIO
    phase_keys=('ownership_proof_wall_s','winner_staging_wall_s','winner_commit_retention_wall_s')
    phase_medians={key:statistics.median(float(r['candidate_hidden_accounting'].get(key,0.0)) for r in reps) for key in phase_keys}
    summary={'office_saving_bytes_by_rep':saving,'base_create_wall_median_s':bc,'candidate_create_wall_median_s':cc,'create_wall_ratio':create_ratio,'create_confirmed_general_timing_regression':_confirmed_timing_regression(bc,cc),'base_extract_wall_median_s':be,'candidate_extract_wall_median_s':ce,'extract_wall_ratio':extract_ratio,'extract_confirmed_general_timing_regression':_confirmed_timing_regression(be,ce),'base_peak_rss_kib_median':br,'candidate_peak_rss_kib_median':cr,'peak_rss_ratio':rss_ratio,'base_selective_wall_median_s':bs,'candidate_selective_wall_median_s':cs,'selective_wall_ratio':selective_ratio,'selective_read_measured':True,'hidden_phase_wall_medians_s':phase_medians,'v030_runtime_memory_lock_pass':lock_pass,'byte_floor_pass':min(saving)>=9_000_000,'promotion_ready':lock_pass and min(saving)>=9_000_000}
    return {'schema':'cmpct-v030-hidden-zip-resource-gate-v5','source_commit':os.environ.get('EVIDENCE_HEAD'),'repetitions':REPS,'order':'A-B-B-A fresh child processes per repetition','rows':reps,'summary':summary,'contract':{'actual_builder_candidate':True,'same_tree_per_ABBA':True,'isolated_process_per_arm':True,'exact_tree_verified':True,'v030_median_create_extract_ratio_max':MAX_MEDIAN_RUNTIME_RATIO,'v030_peak_rss_ratio_max':MAX_PEAK_RSS_RATIO,'general_timing_noise_rule':'slowdown exceeds both 5% and 3 ms','selective_read_measured':True,'phase_timing_is_diagnostic_only':True}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-resource-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-resource.json'));p.add_argument('--child',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--arm',choices=('base','candidate'));p.add_argument('--arc',type=Path);p.add_argument('--extract',type=Path);p.add_argument('--child-output',type=Path);a=p.parse_args()
    if a.child:_child(a.source,a.arm,a.arc,a.extract,a.child_output);return
    result=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
    if not result['summary']['byte_floor_pass'] or not result['summary']['v030_runtime_memory_lock_pass']:raise SystemExit(2)
if __name__=='__main__':main()
