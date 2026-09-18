from __future__ import annotations

"""Paired A/B for the product-shaped G04 retained-attempt5 ownership seam."""
import argparse, hashlib, json, shutil, statistics, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_geometry_overlay_g04_retained as RET

ORDERS=(("control","reuse"),("reuse","control"),("reuse","control"),("control","reuse"))

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def build_control(source: Path, out: Path) -> dict:
    original=G04.A5.build_graph; seen={}
    def measured(root, graph):
        started=time.perf_counter(); stats=dict(original(root,graph))
        seen.update({"sha256":sha(graph),"bytes":graph.stat().st_size,"wall_s":time.perf_counter()-started})
        return stats
    G04.A5.build_graph=measured
    try:
        started=time.perf_counter(); stats=dict(G04.build(source,out)); wall=time.perf_counter()-started
    finally: G04.A5.build_graph=original
    return {"wall_s":wall,"archive_bytes":out.stat().st_size,"archive_sha256":sha(out),"selected":stats["selected"],"tree_sha256":stats["tree_sha256"],"attempt5_second_build":seen,"stats":stats}

def build_reuse(source: Path, out: Path, _work: Path) -> dict:
    started=time.perf_counter(); stats=dict(RET.build(source,out)); wall=time.perf_counter()-started
    retention=dict(stats.get("attempt5_retention",{}))
    return {"wall_s":wall,"archive_bytes":out.stat().st_size,"archive_sha256":sha(out),"selected":stats["selected"],"tree_sha256":stats["tree_sha256"],"retained_attempt5":retention,"stats":stats}

def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    source=PERF._build_corpora(work/"corpus")[("neutral_hostile_v1","09_ml_artifacts")]
    pairs=[]
    for i,order in enumerate(ORDERS):
        arms={}
        for slot,arm in enumerate(order):
            root=work/"runs"/f"pair-{i}-{slot}-{arm}"; root.mkdir(parents=True,exist_ok=True); out=root/"out.cmpct"
            arms[arm]=build_control(source,out) if arm=="control" else build_reuse(source,out,root)
        c,r=arms["control"],arms["reuse"]
        if c["archive_sha256"]!=r["archive_sha256"] or c["tree_sha256"]!=r["tree_sha256"]: raise RuntimeError("final G04 identity mismatch")
        if c["attempt5_second_build"]["bytes"]!=r["retained_attempt5"]["bytes"]: raise RuntimeError("retained attempt5 size mismatch")
        if r["retained_attempt5"].get("payload_write_bytes") != 0: raise RuntimeError("retention unexpectedly rewrote payload bytes")
        saving=1-r["wall_s"]/c["wall_s"]
        pairs.append({"pair":i,"order":list(order),"control":c,"reuse":r,"wall_saving_fraction":saving,"wall_saving_s":c["wall_s"]-r["wall_s"]})
    vals=[p["wall_saving_fraction"] for p in pairs]
    return {"schema":"cmpct-v030-g04-attempt5-retained-productization-ab-v2","release_credit":False,"pairs":pairs,"median_wall_saving_fraction":statistics.median(vals),"min_wall_saving_fraction":min(vals),"max_wall_saving_fraction":max(vals),"claim_boundary":"Research productization evidence only; unchanged fresh-process release authority still required."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
