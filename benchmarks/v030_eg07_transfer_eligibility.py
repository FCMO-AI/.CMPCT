from __future__ import annotations

"""Map the product-valid transfer domain of EG07 without consulting EG08."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT

MODULE = "experiments.entropygraph_v030_federated_embedded_fs_candidate_v7"


def probe(source: Path, archive: Path) -> dict:
    code = r'''
import importlib,json,resource,sys,time,traceback
from pathlib import Path
m=importlib.import_module(sys.argv[1]); source=Path(sys.argv[2]); out=Path(sys.argv[3])
try:
    c0=time.process_time(); w0=time.perf_counter(); result=m.build(source,out); cpu=time.process_time()-c0; wall=time.perf_counter()-w0
    verify=m.strong_verify(out, expected_tree=m._treehash(source)); locality=m.locality_report(out)
    print(json.dumps({'ok':bool(verify.get('ok')) and bool(locality.get('within_release_bounds')),'archive_bytes':out.stat().st_size,'cpu_s':cpu,'wall_s':wall,'peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'verify':verify,'locality':locality,'result':result},default=str,sort_keys=True))
except Exception as exc:
    print(json.dumps({'ok':False,'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()},sort_keys=True))
'''
    env=dict(os.environ); env["PYTHONNOUSERSITE"]="1"
    p=subprocess.run([sys.executable,"-c",code,MODULE,str(source),str(archive)],capture_output=True,text=True,env=env)
    if p.returncode != 0:
        return {"ok":False,"error_type":"SUBPROCESS_FAILURE","error":f"rc={p.returncode}","stdout":p.stdout,"stderr":p.stderr}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok":False,"error_type":"UNPARSEABLE_RECEIPT","stdout":p.stdout,"stderr":p.stderr}


def main() -> None:
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg07-transfer-eligibility.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg07-eligibility-") as td:
        work=Path(td); neutral=work/"neutral"; hostile=work/"hostile"
        nm=CURRENT.build(neutral); hm=HOSTILE.build(hostile); rows=[]
        surfaces=[("neutral",neutral,x["name"],x) for x in nm["corpora"]]+[("hostile",hostile,x["name"],x) for x in hm["workloads"]]
        for family,root,name,item in surfaces:
            w=work/f"probe-{family}-{name}"; w.mkdir(); r=probe(root/name,w/"eg07.cmpct")
            locality=r.get("locality") or {}
            rows.append({
                "family":family,"name":name,"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
                "classification":"ELIGIBLE" if r.get("ok") else "INELIGIBLE_BASELINE",
                "archive_bytes":r.get("archive_bytes"),"cpu_s":r.get("cpu_s"),"wall_s":r.get("wall_s"),"peak_rss_kib":r.get("peak_rss_kib"),
                "max_amp":locality.get("max_member_read_amplification"),"max_decode_unit_bytes":locality.get("max_decode_unit_bytes"),"member_count":locality.get("member_count"),
                "error_type":r.get("error_type"),"error":r.get("error"),"traceback":r.get("traceback"),
            })
        eligible=[r for r in rows if r["classification"]=="ELIGIBLE"]
        out={"schema":"v030-eg07-transfer-eligibility-v1","module":MODULE,"surface_count":len(rows),"eligible_count":len(eligible),"ineligible_count":len(rows)-len(eligible),"eligible_surfaces":[f"{r['family']}:{r['name']}" for r in eligible],"rows":rows}
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
