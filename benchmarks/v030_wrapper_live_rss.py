from __future__ import annotations
"""Live parent-RSS attribution across the canonical r24/r25 wrapper. Diagnostic only."""
import argparse, hashlib, json, os, shutil, subprocess, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PAGE_KIB=os.sysconf("SC_PAGE_SIZE")//1024

def rss(): return int(Path('/proc/self/statm').read_text().split()[1])*PAGE_KIB

def child(source:Path,out:Path):
    from experiments import entropygraph_v030_release_product as RP
    marks=[]; samples=[]; lock=threading.Lock(); stop=threading.Event(); t0=time.perf_counter()
    def mark(phase,event,**extra):
        row={'t_s':time.perf_counter()-t0,'phase':phase,'event':event,'rss_kib':rss(),**extra}
        with lock: marks.append(row)
    def sampler():
        while not stop.is_set():
            with lock: samples.append({'t_s':time.perf_counter()-t0,'rss_kib':rss()})
            stop.wait(.01)
    op,or24,or25,opre=RP.C._prepare_profile_tree,RP.C._r24_build,RP.C._r25_build,RP._locality_bounded_r24_build
    orpverify,ocverify=RP.strong_verify,RP.C.strong_verify
    def wrap(name,fn):
        def inner(*a,**kw):
            mark(name,'start')
            try: result=fn(*a,**kw)
            except BaseException as exc: mark(name,'error',error=type(exc).__name__); raise
            mark(name,'done',selected=result.get('selected') if isinstance(result,dict) else None)
            return result
        return inner
    # Current authority has distinct ownership windows: r24 prebuild overlaps profile capture, then canonical
    # tournament may overlap r24-future consumption with r25. Medium-binary terminal admission bypasses the
    # tournament entirely, so also mark release/canonical strong verification: a post-r24 peak there is a
    # verification-lifetime problem, not evidence for r24/r25 overlap.
    RP._locality_bounded_r24_build=wrap('r24-prebuild',opre)
    RP.C._prepare_profile_tree=wrap('profile-tree',op); RP.C._r24_build=wrap('r24-future',or24); RP.C._r25_build=wrap('r25',or25)
    RP.C.strong_verify=wrap('canonical-strong-verify',ocverify)
    RP.strong_verify=wrap('release-strong-verify',orpverify)
    th=threading.Thread(target=sampler,daemon=True); mark('wrapper','start'); th.start(); started=time.perf_counter()
    try: stats=RP.build(source,out)
    finally: stop.set(); th.join(timeout=2)
    wall=time.perf_counter()-started; mark('wrapper','done',selected=stats.get('selected'))
    with lock: peak=max((x['rss_kib'] for x in samples),default=rss()); cm=list(marks); cs=list(samples)
    # Restore the original release verifier for the post-measurement semantic check so the timeline covers build
    # only and the final check cannot be mistaken for product-build RSS.
    RP.strong_verify=orpverify; RP.C.strong_verify=ocverify
    verified=RP.strong_verify(out)
    print(json.dumps({'schema':'cmpct-v030-wrapper-live-rss-v3','release_credit':False,'source':source.name,'wall_s':wall,'peak_live_rss_kib':peak,'final_live_rss_kib':rss(),'archive_bytes':out.stat().st_size,'archive_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'selected':stats.get('selected'),'format_revision':stats.get('format_revision'),'terminal_r24':stats.get('terminal_r24'),'verify_ok':bool(verified.get('ok')),'marks':cm,'samples':cs,'claim_boundary':'10ms /proc/self/statm current-parent RSS across unchanged shipping build, distinguishing r24-prebuild/profile, r24-future/r25 and publication-verification windows; child RSS remains separately charged by whole-tree companion.'},separators=(',',':')))

def invoke(source,out):
    env={**os.environ,'PYTHONPATH':str(ROOT)}; p=subprocess.run([sys.executable,__file__,'--child','--source',str(source),'--archive',str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--child',action='store_true'); p.add_argument('--source',type=Path); p.add_argument('--archive',type=Path); p.add_argument('--work-root',type=Path); p.add_argument('--output',type=Path); a=p.parse_args()
    if a.child: child(a.source,a.archive); return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root,ignore_errors=True); a.work_root.mkdir(parents=True); corp=PERF._build_corpora(a.work_root/'corpus'); rows={}
    for suite,name in (('neutral_hostile_v1','05_logs_and_telemetry'),('neutral_hostile_v1','09_ml_artifacts')): rows[name]=invoke(corp[(suite,name)],a.work_root/f'{name}.cmpct')
    result={'schema':'cmpct-v030-wrapper-live-rss-suite-v3','release_credit':False,'rows':rows}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
