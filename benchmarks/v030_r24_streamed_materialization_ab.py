from __future__ import annotations
"""Fresh-process r24 materialization A/B on all frozen runtime workloads. Research evidence only."""
import argparse,hashlib,json,os,resource,shutil,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def child(mode:str,source:Path,out:Path)->None:
    if mode=='base':
        from cmpct.builder import Builder as BuilderType
    else:
        from experiments.v030_r24_streamed_materialization import StreamedBuilder as BuilderType
    before=resource.getrusage(resource.RUSAGE_SELF); started=time.perf_counter()
    stats=BuilderType(source).build(out)
    wall=time.perf_counter()-started; after=resource.getrusage(resource.RUSAGE_SELF)
    cpu=(after.ru_utime-before.ru_utime)+(after.ru_stime-before.ru_stime)
    print(json.dumps({'mode':mode,'wall_s':wall,'cpu_s':cpu,'peak_rss_kib':int(after.ru_maxrss),
      'prebuild_peak_rss_kib':int(before.ru_maxrss),'incremental_peak_kib':max(0,int(after.ru_maxrss-before.ru_maxrss)),
      'oublock_delta':int(after.ru_oublock-before.ru_oublock),'inblock_delta':int(after.ru_inblock-before.ru_inblock),
      'archive_bytes':out.stat().st_size,'archive_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'data_bytes':stats['data_bytes'],'unique_blobs':stats['unique_blobs']},separators=(',',':')))

def invoke(mode:str,source:Path,out:Path)->dict:
    env={**os.environ,'PYTHONPATH':str(ROOT)}
    p=subprocess.run([sys.executable,__file__,'--child',mode,'--source',str(source),'--archive',str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def main()->None:
    p=argparse.ArgumentParser(); p.add_argument('--child',choices=('base','streamed')); p.add_argument('--source',type=Path); p.add_argument('--archive',type=Path); p.add_argument('--work-root',type=Path); p.add_argument('--output',type=Path); p.add_argument('--repetitions',type=int,default=2); a=p.parse_args()
    if a.child: child(a.child,a.source,a.archive); return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root,ignore_errors=True); a.work_root.mkdir(parents=True)
    corp=PERF._build_corpora(a.work_root/'corpus'); workloads=[]
    for family,name in PERF.TARGETS:
        source=corp[(family,name)]; rows=[]
        for rep in range(a.repetitions):
            order=('base','streamed') if rep%2==0 else ('streamed','base'); pair={'rep':rep}
            for mode in order: pair[mode]=invoke(mode,source,a.work_root/f'{name}-{rep}-{mode}.cmpct')
            pair['byte_identical']=pair['base']['archive_sha256']==pair['streamed']['archive_sha256'] and pair['base']['archive_bytes']==pair['streamed']['archive_bytes']
            pair['rss_ratio']=pair['streamed']['peak_rss_kib']/pair['base']['peak_rss_kib']; pair['wall_ratio']=pair['streamed']['wall_s']/pair['base']['wall_s']; pair['cpu_ratio']=pair['streamed']['cpu_s']/pair['base']['cpu_s']; rows.append(pair)
        workloads.append({'family':family,'name':name,'rows':rows,'median_rss_ratio':statistics.median(x['rss_ratio'] for x in rows),'median_wall_ratio':statistics.median(x['wall_ratio'] for x in rows),'median_cpu_ratio':statistics.median(x['cpu_ratio'] for x in rows),'all_byte_identical':all(x['byte_identical'] for x in rows)})
    result={'schema':'cmpct-v030-r24-streamed-materialization-ab-v2','release_credit':False,'workloads':workloads,
      'all_byte_identical':all(x['all_byte_identical'] for x in workloads),'claim_boundary':'Fresh-process r24 component A/B on the three frozen runtime workloads; temp block I/O is charged; whole-product frozen release authority remains separate.'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
