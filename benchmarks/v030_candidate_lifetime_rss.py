from __future__ import annotations
"""Research-only candidate/verification live-RSS attribution for frozen ML."""
import argparse,json,os,resource,shutil,threading,time
from pathlib import Path

def rss_kib():
    try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')//1024
    except Exception:return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    from benchmarks import v030_release_performance as PERF
    from experiments import entropygraph_v030_release_product as RP
    C=RP.C;shutil.rmtree(a.work_root,ignore_errors=True);a.work_root.mkdir(parents=True)
    source=PERF._build_corpora(a.work_root/'corpus')[("neutral_hostile_v1","09_ml_artifacts")];archive=a.work_root/'ml.cmpct'
    t0=time.perf_counter();events=[];stop=threading.Event();peak={'rss_kib':0,'t':0.0}
    def mark(kind,**kw):events.append({'t':time.perf_counter()-t0,'rss_kib':rss_kib(),'ru_maxrss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'kind':kind,**kw})
    originals={n:getattr(C,n) for n in ('_r24_build','_r25_build','strong_verify')}
    def wrap(name):
        fn=originals[name]
        def inner(*x,**kw):
            mark(name+'_start');out=fn(*x,**kw);mark(name+'_end',archive_bytes=(Path(x[1]).stat().st_size if len(x)>1 and Path(x[1]).exists() else None));return out
        return inner
    for n in originals:setattr(C,n,wrap(n))
    def sample():
        while not stop.is_set():
            v=rss_kib()
            if v>peak['rss_kib']:peak.update(rss_kib=v,t=time.perf_counter()-t0)
            time.sleep(.002)
    th=threading.Thread(target=sample,daemon=True);th.start();mark('build_start')
    try:stats=RP.build(source,archive);mark('build_end',selected=stats.get('selected'),revision=stats.get('format_revision'))
    finally:
        stop.set();th.join()
        for n,fn in originals.items():setattr(C,n,fn)
    result={'schema':'cmpct-v030-candidate-lifetime-rss-v1','release_credit':False,'selected':stats.get('selected'),'format_revision':stats.get('format_revision'),'archive_bytes':archive.stat().st_size,'peak':peak,'events':events,'claim_boundary':'Frozen ML promoted build; observational candidate/verify phase instrumentation only.'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
