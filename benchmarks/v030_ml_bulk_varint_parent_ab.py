from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ORDERS = (("control", "product"), ("product", "control")) * 2
WORKER = r'''
import json,sys,time
from pathlib import Path
from experiments import entropygraph_v030_release_product as P
archive=Path(sys.argv[1]); dst=Path(sys.argv[2])
t0c=time.process_time(); t0=time.perf_counter(); P.extract(archive,dst)
print(json.dumps({"wall_s":time.perf_counter()-t0,"cpu_s":time.process_time()-t0c,"tree_sha256":P.treehash(dst)},separators=(",",":")))
'''


def fresh(source_root: Path, archive: Path, dst: Path) -> dict:
    env = os.environ.copy(); env["PYTHONPATH"] = str(source_root)
    cp = subprocess.run([sys.executable, "-c", WORKER, str(archive), str(dst)], cwd=source_root, env=env, check=True, capture_output=True, text=True)
    return json.loads([line for line in cp.stdout.splitlines() if line.strip()][-1])


def run(root: Path, control_root: Path) -> dict:
    sys.path.insert(0, str(ROOT))
    from benchmarks import v030_release_performance as PERF
    from experiments import entropygraph_v030_release_product as PRODUCT
    shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
    src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = root / "ml.cmpct"; PRODUCT.build(src, archive); expected = PRODUCT.treehash(src)
    pairs=[]
    roots={"control":control_root.resolve(),"product":ROOT.resolve()}
    for rep,order in enumerate(ORDERS):
        rows={arm:fresh(roots[arm],archive.resolve(),(root/f"r{rep}-{arm}").resolve()) for arm in order}
        if any(row["tree_sha256"] != expected for row in rows.values()): raise RuntimeError("parent/product tree drift")
        c,p=rows["control"],rows["product"]
        pairs.append({"rep":rep,"order":list(order),"rows":rows,"wall_improvement_pct":(c["wall_s"]-p["wall_s"])/c["wall_s"]*100,"cpu_improvement_pct":(c["cpu_s"]-p["cpu_s"])/c["cpu_s"]*100})
    wall=sorted(x["wall_improvement_pct"] for x in pairs); cpu=sorted(x["cpu_improvement_pct"] for x in pairs)
    mw=(wall[1]+wall[2])/2; mc=(cpu[1]+cpu[2])/2
    return {"schema":"cmpct-v030-ml-bulk-varint-parent-ab-v1","release_credit":False,"candidate_sha":os.environ.get("EVIDENCE_HEAD"),"control_sha":os.environ.get("CONTROL_HEAD"),"pairs":pairs,"median_wall_improvement_pct":mw,"median_cpu_improvement_pct":mc,"required_relative_improvement_for_median_1_10":8.038808244732154,"decision":"advance" if mw>8.038808244732154 else "kill-or-reframe","claim_boundary":"candidate release product versus exact authoritative parent checkout; same archive/tree semantics; release authority unpaid"}

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path("benchmark-artifacts/v030-ml-bulk-varint-parent")); ap.add_argument("--control-root",type=Path,required=True); args=ap.parse_args()
    result=run(args.root,args.control_root); out=Path("benchmark-artifacts/v030-ml-bulk-varint-parent.json"); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
