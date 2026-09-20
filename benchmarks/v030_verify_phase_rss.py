from __future__ import annotations
"""Research-only live-RSS attribution for the frozen ML promoted build."""
import argparse,json,os,resource,shutil,threading,time
from pathlib import Path


def rss_kib()->int:
    try:
        pages=int(Path('/proc/self/statm').read_text().split()[1]); return pages*os.sysconf('SC_PAGE_SIZE')//1024
    except Exception:return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    from benchmarks import v030_release_performance as PERF
    from experiments import entropygraph_v030_release_product as RP
    R=RP.C.POLICY.R
    shutil.rmtree(a.work_root,ignore_errors=True);a.work_root.mkdir(parents=True)
    source=PERF._build_corpora(a.work_root/'corpus')[("neutral_hostile_v1","09_ml_artifacts")]
    archive=a.work_root/'ml.cmpct'
    events=[]; lock=threading.Lock(); stop=threading.Event(); peak={'rss':0,'t':0.0,'sessions':0}; sessions={'n':0}; cache_peak={'record':0,'node':0}
    t0=time.perf_counter()
    def mark(kind,**kw):
        with lock: events.append({'t':time.perf_counter()-t0,'rss_kib':rss_kib(),'kind':kind,**kw})
    orig_init=R._G04Session.__init__;orig_close=R._G04Session.close;orig_put=R._cache_put
    def init(self,*x,**kw):
        orig_init(self,*x,**kw);sessions['n']+=1;mark('session_open',record_count=len(self.offsets))
    def close(self):
        mark('session_close',record_cache_bytes=self.record_cache_bytes[0],node_cache_bytes=self.node_cache_bytes[0],physical_reads=self.physical_record_reads);sessions['n']-=1;return orig_close(self)
    def put(cache,cache_bytes,key,value,limit):
        out=orig_put(cache,cache_bytes,key,value,limit);name='record' if limit==R.MAX_RECORD_CACHE_BYTES else 'node' if limit==R.MAX_NODE_CACHE_BYTES else 'other';cache_peak[name]=max(cache_peak.get(name,0),cache_bytes[0]);mark('cache_put',cache=name,cache_bytes=cache_bytes[0],value_bytes=len(value));return out
    R._G04Session.__init__=init;R._G04Session.close=close;R._cache_put=put
    def sample():
        while not stop.is_set():
            v=rss_kib()
            if v>peak['rss']:peak.update(rss=v,t=time.perf_counter()-t0,sessions=sessions['n'])
            time.sleep(.002)
    th=threading.Thread(target=sample,daemon=True);th.start();mark('build_start')
    try: stats=RP.build(source,archive);mark('build_end',selected=stats.get('selected'),revision=stats.get('format_revision'))
    finally: stop.set();th.join();R._G04Session.__init__=orig_init;R._G04Session.close=orig_close;R._cache_put=orig_put
    result={'schema':'cmpct-v030-verify-phase-rss-v1','release_credit':False,'archive_bytes':archive.stat().st_size,'selected':stats.get('selected'),'format_revision':stats.get('format_revision'),'peak':peak,'cache_peak_bytes':cache_peak,'events':events,'claim_boundary':'Frozen ML promoted build; observational instrumentation only; no product mutation.'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
