from __future__ import annotations

"""Research-only ownership profile for canonical ML extraction through the real shipping front door."""
import argparse, cProfile, json, pstats, shutil, statistics, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
TARGET=("neutral_hostile_v1","09_ml_artifacts"); ROUNDS=7

def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    source=PERF._build_corpora(work/"corpus")[TARGET]; source_tree=PRODUCT.treehash(source); archive=work/"ml.cmpct"
    t=time.perf_counter(); built=PRODUCT.build(source,archive); build_s=time.perf_counter()-t
    auditions=built.get("r25",{}).get("g04",{}).get("auditions",[])
    if not any(row.get("selected") not in (None,"none") for row in auditions): raise RuntimeError("shipping ML target did not select nested G04 records")
    verified=PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256")!=source_tree: raise RuntimeError("shipping archive failed exact strong verification")
    warm=work/"warm"; PRODUCT.extract(archive,warm)
    if PRODUCT.treehash(warm)!=source_tree: raise RuntimeError("warm extraction identity failure")
    extracts=[]; hashes=[]; combined=[]
    for i in range(ROUNDS):
        dst=work/f"timed-{i}"; t=time.perf_counter(); PRODUCT.extract(archive,dst); e=time.perf_counter()-t
        t=time.perf_counter(); got=PRODUCT.treehash(dst); h=time.perf_counter()-t
        if got!=source_tree: raise RuntimeError("timed extraction identity failure")
        extracts.append(e); hashes.append(h); combined.append(e+h)
    dst=work/"profiled"; profile=cProfile.Profile(); t=time.perf_counter(); profile.enable(); PRODUCT.extract(archive,dst); profile.disable(); profiled=time.perf_counter()-t
    if PRODUCT.treehash(dst)!=source_tree: raise RuntimeError("profiled extraction identity failure")
    stats=pstats.Stats(profile); total=float(stats.total_tt); rows=[]
    for (filename,line,function),(cc,nc,tt,ct,_callers) in stats.stats.items(): rows.append({"filename":str(filename),"line":int(line),"function":str(function),"primitive_calls":int(cc),"total_calls":int(nc),"self_s":float(tt),"cumulative_s":float(ct),"self_fraction":float(tt/total) if total else 0.0})
    return {"schema":"cmpct-v030-g04-ml-shipping-extract-profile-v1","release_credit":False,"target":"/".join(TARGET),"diagnostic_route":"shipping-product-front-door-no-external-r25-context-v1","archive_bytes":archive.stat().st_size,"source_tree_sha256":source_tree,"build_elapsed_s_context_only":build_s,"unprofiled_rounds":ROUNDS,"unprofiled_extract_s":extracts,"unprofiled_treehash_s":hashes,"unprofiled_combined_s":combined,"unprofiled_extract_median_s":float(statistics.median(extracts)),"unprofiled_treehash_median_s":float(statistics.median(hashes)),"unprofiled_combined_median_s":float(statistics.median(combined)),"profiled_extract_wall_s_context_only":profiled,"profile_total_self_s":total,"shipping_build":built,"top_by_self":sorted(rows,key=lambda r:r["self_s"],reverse=True)[:60],"top_by_cumulative":sorted(rows,key=lambda r:r["cumulative_s"],reverse=True)[:60],"claim_boundary":"Function ownership plus extract/treehash phase diagnostic only; no timing here is release performance evidence."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args(); result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:result[k] for k in ("schema","archive_bytes","build_elapsed_s_context_only","unprofiled_extract_median_s","unprofiled_treehash_median_s","unprofiled_combined_median_s","profiled_extract_wall_s_context_only","release_credit")}|{"top_by_self":result["top_by_self"][:15]},indent=2))
if __name__=="__main__": main()
