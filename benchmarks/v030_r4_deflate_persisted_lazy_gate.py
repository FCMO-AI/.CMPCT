from __future__ import annotations
import argparse, json, os, time, traceback
from pathlib import Path
from benchmarks import v030_r4_deflate_persisted_lazy_reader as C
SCHEMA="cmpct-v030-r4-deflate-persisted-lazy-gate-v1"
def run(work: Path):
    t=time.perf_counter()
    try:
        c=C.run(work)
        return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"experiment_completed":True,"candidate_exception":None,"candidate":c,"scientific_pass":bool(c["hypothesis"]["persisted_lazy_reader_preserves_exact_bounded_locality"]),"elapsed_wall_s":time.perf_counter()-t,"contract":{"diagnostic_only":True,"release_credit":False,"candidate_frozen":True}}
    except Exception as e:
        return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"experiment_completed":True,"candidate_exception":{"type":type(e).__name__,"message":str(e),"traceback_tail":traceback.format_exc().splitlines()[-24:]},"candidate":None,"scientific_pass":False,"elapsed_wall_s":time.perf_counter()-t,"contract":{"diagnostic_only":True,"release_credit":False,"candidate_frozen":True}}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-persist-lazy-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-persist-lazy-gate.json")); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps(d,indent=2))
if __name__=="__main__": main()
