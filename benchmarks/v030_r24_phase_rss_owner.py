from __future__ import annotations
"""Fresh-process phase-attributed r24 Builder RSS falsifier.

Diagnostic only: this localizes the already-measured r24 memory owner before we
change materialization. It deliberately does not award release credit.
"""
import argparse,json,os,resource,shutil,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASES=("scan","_build_micro_packs","_prepare_deflate_reuse","_train_dictionary")

def _rss()->int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def child(source:Path,out:Path)->None:
    from cmpct.builder import Builder
    b=Builder(source)
    marks=[{"phase":"prebuild","rss_kib":_rss()}]
    for name in PHASES:
        original=getattr(b,name)
        def wrapped(*args,_name=name,_original=original,**kwargs):
            before=_rss(); started=time.perf_counter()
            result=_original(*args,**kwargs)
            marks.append({"phase":_name,"before_rss_kib":before,"rss_kib":_rss(),"wall_s":time.perf_counter()-started})
            return result
        setattr(b,name,wrapped)
    started=time.perf_counter(); stats=b.build(out); wall=time.perf_counter()-started
    final=_rss(); pre=marks[0]["rss_kib"]
    print(json.dumps({"schema":"cmpct-v030-r24-phase-rss-owner-v1","release_credit":False,
        "source":"01_shifted_versions","prebuild_rss_kib":pre,"final_rss_kib":final,
        "incremental_peak_kib":max(0,final-pre),"wall_s":wall,"archive_bytes":out.stat().st_size,
        "archive_sha256":__import__("hashlib").sha256(out.read_bytes()).hexdigest(),"marks":marks,
        "stats":{k:stats.get(k) for k in ("bytes","data_bytes","unique_blobs","encode_workers")},
        "claim_boundary":"ru_maxrss high-water after each pre-materialization Builder phase; final delta contains candidate encoding plus record/index/final archive materialization."},separators=(",",":")))

def invoke(source:Path,out:Path)->dict:
    env={**os.environ,"PYTHONPATH":str(ROOT)}
    p=subprocess.run([sys.executable,__file__,"--child","--source",str(source),"--archive",str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([line for line in p.stdout.splitlines() if line.strip()][-1])

def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("--child",action="store_true"); p.add_argument("--source",type=Path); p.add_argument("--archive",type=Path); p.add_argument("--work-root",type=Path); p.add_argument("--output",type=Path); a=p.parse_args()
    if a.child: child(a.source,a.archive); return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root,ignore_errors=True); a.work_root.mkdir(parents=True)
    corp=PERF._build_corpora(a.work_root/"corpus")
    source=corp[("resemblance_hostile_v1","01_shifted_versions")]
    result=invoke(source,a.work_root/"shifted-r24.cmpct")
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
