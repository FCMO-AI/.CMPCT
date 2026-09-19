from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT=Path(__file__).resolve().parents[1]
ORDER=(("control","fast"),("fast","control"))

def worker(arm: str, archive: Path, dst: Path) -> dict:
    fast_calls=slow_calls=0
    if arm=="fast":
        from experiments import entropygraph_v030_verified_restore as VR
        O=VR.C.SHARED.G.O
        original=O._get_varint
        def bounded_fast(data: bytes, pos: int):
            nonlocal fast_calls, slow_calls
            if pos < len(data) and data[pos] < 0x80:
                fast_calls += 1
                return data[pos], pos + 1
            slow_calls += 1
            return original(data, pos)
        O._get_varint=bounded_fast
    started=time.perf_counter(); PRODUCT.extract(archive,dst); wall=time.perf_counter()-started
    return {"arm":arm,"wall_s":wall,"tree_sha256":PRODUCT.treehash(dst),"one_byte_fast_calls":fast_calls,"fallback_calls":slow_calls}

def fresh(arm, archive, dst):
    env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",arm,"--archive",str(archive),"--dst",str(dst)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in cp.stdout.splitlines() if x.strip()][-1])

def run(root: Path):
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True)
    src=PERF._build_corpora(root/"corpora")[("neutral_hostile_v1","09_ml_artifacts")]
    archive=root/"ml.cmpct"; PRODUCT.build(src,archive); expected=PRODUCT.treehash(src)
    pairs=[]
    for rep,order in enumerate(ORDER):
        rows={}
        for arm in order: rows[arm]=fresh(arm,archive,root/f"r{rep}-{arm}")
        if rows["control"]["tree_sha256"]!=expected or rows["fast"]["tree_sha256"]!=expected: raise RuntimeError("semantic drift")
        pct=(rows["control"]["wall_s"]-rows["fast"]["wall_s"])/rows["control"]["wall_s"]*100
        pairs.append({"rep":rep,"order":list(order),"control":rows["control"],"fast":rows["fast"],"wall_improvement_pct":pct})
    return {"schema":"cmpct-v030-ml-varint-fastpath-oracle-v1","release_credit":False,"pairs":pairs,"claim_boundary":"research oracle only; exact existing decoder remains fallback for every multi-byte/truncated case"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--worker",choices=("control","fast")); ap.add_argument("--archive",type=Path); ap.add_argument("--dst",type=Path); ap.add_argument("--root",type=Path,default=Path("benchmark-artifacts/v030-ml-varint-fastpath")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-ml-varint-fastpath.json")); a=ap.parse_args()
    if a.worker: print(json.dumps(worker(a.worker,a.archive,a.dst),separators=(",",":"))); return
    d=run(a.root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps(d,indent=2))
if __name__=="__main__": main()
