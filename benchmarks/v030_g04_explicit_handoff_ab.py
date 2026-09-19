from __future__ import annotations

"""Paired A/B for G04 explicit attempt-5 ownership; research evidence, never release credit."""
import argparse, hashlib, json, resource, shutil, statistics, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_geometry_overlay_g04_explicit_handoff as EXPLICIT

ORDERS=(("control","explicit"),("explicit","control"),("explicit","control"),("control","explicit"))

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def usage():
    a=resource.getrusage(resource.RUSAGE_SELF); c=resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"cpu_s":a.ru_utime+a.ru_stime+c.ru_utime+c.ru_stime,"maxrss_kib":max(a.ru_maxrss,c.ru_maxrss)}

def measured(fn, source: Path, out: Path) -> dict:
    u0=usage(); t0=time.perf_counter(); stats=dict(fn(source,out)); wall=time.perf_counter()-t0; u1=usage()
    return {"wall_s":wall,"cpu_s":u1["cpu_s"]-u0["cpu_s"],"maxrss_kib_observed":u1["maxrss_kib"],"archive_bytes":out.stat().st_size,
            "archive_sha256":sha(out),"selected":stats["selected"],"tree_sha256":stats["tree_sha256"],"stats":stats}

def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    source=PERF._build_corpora(work/"corpus")[("neutral_hostile_v1","09_ml_artifacts")]
    pairs=[]
    for i,order in enumerate(ORDERS):
        arms={}
        for slot,arm in enumerate(order):
            root=work/"runs"/f"pair-{i}-{slot}-{arm}"; root.mkdir(parents=True,exist_ok=True); out=root/"out.cmpct"
            arms[arm]=measured(G04.build if arm=="control" else EXPLICIT.build,source,out)
        c,e=arms["control"],arms["explicit"]; ret=e["stats"].get("attempt5_retention",{})
        if c["archive_sha256"]!=e["archive_sha256"] or c["tree_sha256"]!=e["tree_sha256"]: raise RuntimeError("final identity mismatch")
        if e["stats"].get("global_monkeypatches") != 0 or e["stats"].get("ownership") != "explicit-artifact-handoff": raise RuntimeError("explicit ownership contract missing")
        if ret.get("payload_write_bytes") != 0 or ret.get("mode") != "same-filesystem-hardlink": raise RuntimeError("retention exported payload-write cost")
        pairs.append({"pair":i,"order":list(order),"control":c,"explicit":e,"wall_saving_fraction":1-e["wall_s"]/c["wall_s"],"cpu_saving_fraction":1-e["cpu_s"]/c["cpu_s"]})
    w=[p["wall_saving_fraction"] for p in pairs]; cpu=[p["cpu_saving_fraction"] for p in pairs]
    return {"schema":"cmpct-v030-g04-explicit-handoff-ab-v1","release_credit":False,"pairs":pairs,"median_wall_saving_fraction":statistics.median(w),
            "median_cpu_saving_fraction":statistics.median(cpu),"claim_boundary":"Explicit-ownership research evidence only. maxrss is process-tree high-water observation, not paired incremental RSS; fresh-process authority remains required."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    r=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+"\n"); print(json.dumps(r,indent=2))
if __name__=="__main__": main()
