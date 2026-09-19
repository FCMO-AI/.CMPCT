from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from benchmarks.v030_ml_hierarchy_empty_screen_fast_reject import install_fast_reject
from experiments import entropygraph_v030_release_product as PRODUCT
ROOT=Path(__file__).resolve().parents[1]; ORDERS=(("control","fast"),("fast","control"))

def worker(arm,source,archive):
    C=PRODUCT._BASE_IMPL.C; counts={"fast_rejects":0,"fallback_original":0}
    if arm=="fast":
        # Canonical-final intentionally isolates dependency graphs.  Bind the public SHARED.G
        # handle to the exact module object captured by the build function before installing
        # the research hook; this is evidence plumbing only, not product behavior.
        C.SHARED.G=C.SHARED.build.__globals__["G"]
        counts=install_fast_reject()
    start_cpu=time.process_time(); start=time.perf_counter(); stats=C.SHARED.build(source,archive); wall=time.perf_counter()-start; cpu=time.process_time()-start_cpu
    verified=C.SHARED.strong_verify(archive)
    if not verified.get('ok'): raise RuntimeError(f'G04 verify failed: {verified}')
    return {'arm':arm,'wall_s':wall,'cpu_s':cpu,'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'tree_sha256':verified.get('tree_sha256'),'selected':stats.get('selected'),**counts}
def fresh(arm,source,archive):
    env=os.environ.copy(); env['PYTHONPATH']=str(ROOT)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',arm,'--source',str(source),'--archive',str(archive)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in cp.stdout.splitlines() if x.strip()][-1])
def run(root):
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); source=PERF._build_corpora(root/'corpora')[("neutral_hostile_v1","09_ml_artifacts")]; pairs=[]
    for rep,order in enumerate(ORDERS):
        rows={a:fresh(a,source,root/f'r{rep}-{a}.cmpct') for a in order}; c,f=rows['control'],rows['fast']
        if c['archive_sha256']!=f['archive_sha256'] or c['tree_sha256']!=f['tree_sha256']: raise RuntimeError('archive/tree identity drift')
        if f['fast_rejects']<1: raise RuntimeError('fast arm rejected no impossible hierarchical auditions')
        pairs.append({'rep':rep,'order':list(order),'rows':rows,'wall_improvement_pct':(c['wall_s']-f['wall_s'])/c['wall_s']*100,'cpu_improvement_pct':(c['cpu_s']-f['cpu_s'])/c['cpu_s']*100})
    vals=sorted(p['wall_improvement_pct'] for p in pairs); med=sum(vals)/len(vals)
    return {'schema':'cmpct-v030-ml-hierarchy-empty-screen-fast-reject-direct-v1','release_credit':False,'source_sha':os.environ.get('EVIDENCE_HEAD'),'pairs':pairs,'median_wall_improvement_pct':med,'required_whole_product_relative_improvement_pct':10.983601521924591,'claim_boundary':'direct canonical SHARED/G04 owner A/B; product transfer still unpaid','decision':'advance-product-transfer' if med>10.983601521924591 else 'insufficient-alone'}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--worker',choices=('control','fast')); ap.add_argument('--source',type=Path); ap.add_argument('--archive',type=Path); ap.add_argument('--root',type=Path,default=Path('benchmark-artifacts/v030-ml-hierarchy-empty-direct')); args=ap.parse_args()
    if args.worker: print(json.dumps(worker(args.worker,args.source,args.archive),separators=(',',':')))
    else:
        result=run(args.root); out=Path('benchmark-artifacts/v030-ml-hierarchy-empty-direct.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
