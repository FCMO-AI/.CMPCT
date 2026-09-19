from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT=Path(__file__).resolve().parents[1]
ORDER=(("control","fold"),("fold","control"))


def _install_filehash_fold():
    from experiments import entropygraph_v030_verified_restore as VR
    R=VR.C.POLICY.R
    original=R._consume_g04_file

    def folded(session, rel, desc, tree, target_root):
        safe=R._safe_relpath(rel)
        expected_size=int(desc[2])
        rel_bytes=rel.encode("utf-8")
        tree.update(len(rel_bytes).to_bytes(4,"little")); tree.update(rel_bytes); tree.update(expected_size.to_bytes(8,"little"))
        written=0; output=None
        try:
            if target_root is not None:
                target=target_root.joinpath(*safe.parts); target.parent.mkdir(parents=True,exist_ok=True); output=target.open("wb")
            chunks=[session.record(int(desc[1]))] if desc[0]=="preflate" else (session.node(int(node_id)) for node_id in desc[1])
            for raw in chunks:
                written += len(raw)
                if written > expected_size: raise RuntimeError("G0-G4 streamed file exceeds declared size")
                tree.update(raw)
                if output is not None: output.write(raw)
        finally:
            if output is not None: output.close()
        if written != expected_size: raise RuntimeError("G0-G4 streamed file size mismatch")
        return written

    R._consume_g04_file=folded
    return original


def worker(arm: str, archive: Path, dst: Path) -> dict:
    if arm=="fold": _install_filehash_fold()
    started=time.perf_counter(); PRODUCT.extract(archive,dst); wall=time.perf_counter()-started
    return {"arm":arm,"wall_s":wall,"tree_sha256":PRODUCT.treehash(dst)}


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
        rows={arm:fresh(arm,archive,root/f"r{rep}-{arm}") for arm in order}
        if rows["control"]["tree_sha256"]!=expected or rows["fold"]["tree_sha256"]!=expected: raise RuntimeError("semantic drift")
        pct=(rows["control"]["wall_s"]-rows["fold"]["wall_s"])/rows["control"]["wall_s"]*100
        pairs.append({"rep":rep,"order":list(order),"control":rows["control"],"fold":rows["fold"],"wall_improvement_pct":pct})
    return {"schema":"cmpct-v030-ml-filehash-fold-oracle-v1","release_credit":False,"pairs":pairs,"preserved_checks":["physical payload SHA-256","record CRC32+SHA-256","logical-node SHA-256","final authenticated streamed-tree SHA-256"],"omitted_success_path_check":"per-file SHA-256 only","claim_boundary":"research headroom only; hostile equivalence and replay semantics unpaid"}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--worker",choices=("control","fold")); ap.add_argument("--archive",type=Path); ap.add_argument("--dst",type=Path); ap.add_argument("--root",type=Path,default=Path("benchmark-artifacts/v030-ml-filehash-fold")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-ml-filehash-fold.json")); a=ap.parse_args()
    if a.worker: print(json.dumps(worker(a.worker,a.archive,a.dst),separators=(",",":"))); return
    d=run(a.root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps(d,indent=2))
if __name__=="__main__": main()
