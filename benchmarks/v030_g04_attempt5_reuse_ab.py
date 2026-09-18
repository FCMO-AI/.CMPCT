from __future__ import annotations

"""Research-only paired A/B for retaining G04's already-built attempt-5 intermediate."""
import argparse, hashlib, json, shutil, statistics, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_geometry_overlay_g04 as G04

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

def build_reuse(source: Path, out: Path, work: Path) -> dict:
    retained=work/"retained-attempt5.cmpct"; retained.parent.mkdir(parents=True,exist_ok=True)
    scheduler=G04.BASE.scheduler
    original_replace=scheduler._durable_replace; original_graph=G04.A5.build_graph; captured={}
    def capture_replace(chosen,destination):
        candidate=Path(chosen).parent/"attempt5.cmpct"
        if not candidate.is_file(): raise RuntimeError("attempt5 candidate unavailable at v0.29 publication boundary")
        started=time.perf_counter(); shutil.copyfile(candidate,retained); copy_s=time.perf_counter()-started
        captured.update({"sha256":sha(retained),"bytes":retained.stat().st_size,"retention_copy_s":copy_s})
        return original_replace(chosen,destination)
    def reuse_graph(root,graph):
        if not retained.is_file(): raise RuntimeError("retained attempt5 missing before G04 overlay")
        started=time.perf_counter(); shutil.copyfile(retained,graph); copy_s=time.perf_counter()-started
        return {"create_s":copy_s,"selected":True,"graph_bytes":graph.stat().st_size,"retained_intermediate":True,"physical_sha256":sha(graph)}
    scheduler._durable_replace=capture_replace; G04.A5.build_graph=reuse_graph
    try:
        started=time.perf_counter(); stats=dict(G04.build(source,out)); wall=time.perf_counter()-started
    finally:
        scheduler._durable_replace=original_replace; G04.A5.build_graph=original_graph
    return {"wall_s":wall,"archive_bytes":out.stat().st_size,"archive_sha256":sha(out),"selected":stats["selected"],"tree_sha256":stats["tree_sha256"],"retained_attempt5":captured,"stats":stats}

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
        if c["attempt5_second_build"]["sha256"]!=r["retained_attempt5"]["sha256"]: raise RuntimeError("retained attempt5 identity mismatch")
        saving=1-r["wall_s"]/c["wall_s"]
        pairs.append({"pair":i,"order":list(order),"control":c,"reuse":r,"wall_saving_fraction":saving,"wall_saving_s":c["wall_s"]-r["wall_s"]})
    vals=[p["wall_saving_fraction"] for p in pairs]
    return {"schema":"cmpct-v030-g04-attempt5-reuse-ab-v1","release_credit":False,"pairs":pairs,"median_wall_saving_fraction":statistics.median(vals),"min_wall_saving_fraction":min(vals),"max_wall_saving_fraction":max(vals),"claim_boundary":"Research-only exact-intermediate reuse evidence; no product/release credit."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
