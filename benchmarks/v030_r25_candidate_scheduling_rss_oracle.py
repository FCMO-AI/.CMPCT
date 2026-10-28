from __future__ import annotations

import argparse, json, os, shutil, statistics, subprocess, sys
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final as CANONICAL

ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/'benchmarks'/'v030_r25_candidate_scheduling_rss_worker.py'
ORDERS=(('concurrent','serialized'),('serialized','concurrent'))
TARGET=('resemblance_hostile_v1','01_shifted_versions')

def _head(): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def _run(mode,source,archive):
    env=os.environ.copy(); env['PYTHONPATH']=str(ROOT)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    c=subprocess.run([sys.executable,str(WORKER),'--mode',mode,'--source',str(source),'--archive',str(archive)],cwd=ROOT,env=env,capture_output=True,text=True)
    lines=[x for x in c.stdout.splitlines() if x.strip()]
    if c.returncode or not lines: return {'mode':mode,'worker_failed':True,'returncode':c.returncode,'stdout':c.stdout,'stderr':c.stderr}
    try: d=json.loads(lines[-1])
    except Exception as e: return {'mode':mode,'worker_failed':True,'returncode':0,'failure':f'json:{e}','stdout':c.stdout,'stderr':c.stderr}
    d['worker_failed']=False; return d

def run(root:Path):
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True)
    corp=PERF._build_corpora(root/'corpora'); source=corp[TARGET]; tree=str(CANONICAL.RC.treehash(source))
    reps=[]; failures=[]; valid=True
    for ri,order in enumerate(ORDERS):
        row={'round':ri,'execution_order':list(order)}
        for mode in order:
            arc=root/'archives'/f'r{ri}-{mode}.cmpct'; arc.parent.mkdir(parents=True,exist_ok=True)
            d=_run(mode,source,arc); row[mode]=d
            owners=d.get('semantic_owners') or {}
            ok=(not d.get('worker_failed') and d.get('tree_sha256')==tree and owners.get('identity_exact') is True and owners.get('pg')=='experiments._v030_canonical_prefixgraph' and owners.get('g04')=='experiments._v030_canonical_shared_portfolio' and d.get('selected')=='prefixgraph')
            if mode=='serialized': ok=ok and d.get('inline_executor_submissions')==2
            if not ok: valid=False; failures.append({'round':ri,**d})
        if not row['concurrent'].get('worker_failed') and not row['serialized'].get('worker_failed'):
            if row['concurrent']['archive_bytes']!=row['serialized']['archive_bytes'] or row['concurrent']['archive_sha256']!=row['serialized']['archive_sha256'] or row['concurrent']['tree_sha256']!=row['serialized']['tree_sha256'] or row['concurrent']['selected']!=row['serialized']['selected']:
                valid=False; failures.append({'round':ri,'failure':'paired-product-identity-mismatch'})
        reps.append(row)
    def med(mode,key): return statistics.median(float(r[mode][key]) for r in reps)
    cp,sp=med('concurrent','peak_rss_kib'),med('serialized','peak_rss_kib'); cw,sw=med('concurrent','wall_s'),med('serialized','wall_s')
    reduction=(cp-sp)/cp if cp else 0.0
    decision='supports-concurrency-lifetime-ownership' if reduction>=.20 else 'retires-concurrency-primary-explanation' if reduction<.10 else 'ambiguous'
    return {'schema':'cmpct-v030-r25-candidate-scheduling-rss-v1','source_commit':_head(),'preregistration':'docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_PREREG.md','target':list(TARGET),'tree_sha256':tree,'orders':[list(x) for x in ORDERS],'repetitions':reps,'concurrent_median_peak_rss_kib':int(cp),'serialized_median_peak_rss_kib':int(sp),'serialized_peak_rss_reduction':reduction,'concurrent_median_wall_s':cw,'serialized_median_wall_s':sw,'serialized_wall_ratio':sw/cw if cw else None,'decision':decision,'experiment_valid':valid,'worker_failures':failures,'release_credit':False,'contract':{'exact_product_identity_required':True,'fresh_process_per_measurement':True,'total_peak_rss_is_causal_metric':True,'baseline_subtracted_ru_maxrss_is_diagnostic_only':True,'production_source_changed':False,'selector_changed':False,'admission_changed':False,'grammar_changed':False,'integrity_changed':False,'locality_changed':False,'recovery_changed':False}}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r25-candidate-scheduling-rss-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r25-candidate-scheduling-rss.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps({k:d[k] for k in ('source_commit','experiment_valid','concurrent_median_peak_rss_kib','serialized_median_peak_rss_kib','serialized_peak_rss_reduction','concurrent_median_wall_s','serialized_median_wall_s','decision')},indent=2));
    if not d['experiment_valid']: raise SystemExit('candidate scheduling RSS evidence invalid')
if __name__=='__main__': main()
