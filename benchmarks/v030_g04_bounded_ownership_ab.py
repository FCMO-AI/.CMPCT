from __future__ import annotations
"""Fresh-process ML A/B for promoted-G04 bounded ownership. Research evidence only."""
import argparse,hashlib,json,os,resource,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def child(mode,source,out):
    from experiments import entropygraph_v030_release_product as RP
    if mode=='bounded':
        from experiments import v030_g04_bounded_ownership as B; B.install()
    before=resource.getrusage(resource.RUSAGE_SELF); t=time.perf_counter(); stats=RP.build(source,out); wall=time.perf_counter()-t
    after=resource.getrusage(resource.RUSAGE_SELF)
    print(json.dumps({'mode':mode,'wall_s':wall,'cpu_s':(after.ru_utime-before.ru_utime)+(after.ru_stime-before.ru_stime),
      'peak_rss_kib':int(after.ru_maxrss),'archive_bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'selected':stats.get('selected'),'format_revision':stats.get('format_revision')},separators=(',',':')))

def invoke(mode,source,out):
    env={**os.environ,'PYTHONPATH':str(ROOT)}
    p=subprocess.run([sys.executable,__file__,'--child',mode,'--source',str(source),'--archive',str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--child',choices=('base','bounded')); p.add_argument('--source',type=Path); p.add_argument('--archive',type=Path); p.add_argument('--work-root',type=Path); p.add_argument('--output',type=Path); a=p.parse_args()
    if a.child: child(a.child,a.source,a.archive); return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root,ignore_errors=True); a.work_root.mkdir(parents=True)
    source=PERF._build_corpora(a.work_root/'corpus')[('neutral_hostile_v1','09_ml_artifacts')]
    rows=[]
    for rep,order in enumerate((('base','bounded'),('bounded','base'))):
        pair={'rep':rep}
        for mode in order: pair[mode]=invoke(mode,source,a.work_root/f'ml-{rep}-{mode}.cmpct')
        pair['byte_identical']=pair['base']['archive_bytes']==pair['bounded']['archive_bytes'] and pair['base']['sha256']==pair['bounded']['sha256']
        pair['rss_ratio']=pair['bounded']['peak_rss_kib']/pair['base']['peak_rss_kib']; pair['wall_ratio']=pair['bounded']['wall_s']/pair['base']['wall_s']; rows.append(pair)
    result={'schema':'cmpct-v030-g04-bounded-ownership-ab-v1','release_credit':False,'rows':rows,
      'all_byte_identical':all(x['byte_identical'] for x in rows),'claim_boundary':'ML frozen workload fresh-process whole promoted build; exact bytes + parent ru_maxrss + wall/CPU. Verification behavior is unchanged; release authority remains separate.'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
