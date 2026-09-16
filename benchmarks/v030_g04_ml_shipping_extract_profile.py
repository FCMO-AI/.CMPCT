from __future__ import annotations

"""Research-only ownership profile for canonical ML extraction through the real shipping front door.

The diagnostic now carries an exact canonical-r24 control built from the same source tree.  This does not alter
release timing or earn release credit; it answers the narrower causal question exposed by authority-v2: whether
the ML extraction debt belongs to r25 representation/reader work rather than filesystem materialization or the
shared benchmark substrate.
"""
import argparse, cProfile, json, pstats, shutil, statistics, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
TARGET=("neutral_hostile_v1","09_ml_artifacts"); ROUNDS=7


def _measure_extract(archive: Path, source_tree: str, work: Path, prefix: str) -> dict:
    warm=work/f"{prefix}-warm"; PRODUCT.extract(archive,warm)
    if PRODUCT.treehash(warm)!=source_tree: raise RuntimeError(f"{prefix} warm extraction identity failure")
    extracts=[]; hashes=[]; combined=[]
    for i in range(ROUNDS):
        dst=work/f"{prefix}-timed-{i}"; t=time.perf_counter(); PRODUCT.extract(archive,dst); e=time.perf_counter()-t
        t=time.perf_counter(); got=PRODUCT.treehash(dst); h=time.perf_counter()-t
        if got!=source_tree: raise RuntimeError(f"{prefix} timed extraction identity failure")
        extracts.append(e); hashes.append(h); combined.append(e+h)
    return {
        "archive_bytes":archive.stat().st_size,
        "unprofiled_extract_s":extracts,
        "unprofiled_treehash_s":hashes,
        "unprofiled_combined_s":combined,
        "unprofiled_extract_median_s":float(statistics.median(extracts)),
        "unprofiled_treehash_median_s":float(statistics.median(hashes)),
        "unprofiled_combined_median_s":float(statistics.median(combined)),
    }


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    source=PERF._build_corpora(work/"corpus")[TARGET]; source_tree=PRODUCT.treehash(source); archive=work/"ml.cmpct"
    t=time.perf_counter(); built=PRODUCT.build(source,archive); build_s=time.perf_counter()-t
    auditions=built.get("r25",{}).get("g04",{}).get("auditions",[])
    if not any(row.get("selected") not in (None,"none") for row in auditions): raise RuntimeError("shipping ML target did not select nested G04 records")
    verified=PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256")!=source_tree: raise RuntimeError("shipping archive failed exact strong verification")

    r24=work/"ml-r24-control.cmpct"; r24_stats=dict(PRODUCT._locality_bounded_r24_build(source,r24))
    r24_verified=PRODUCT.strong_verify(r24)
    if not r24_verified.get("ok") or r24_verified.get("tree_sha256")!=source_tree: raise RuntimeError("r24 control failed exact strong verification")

    shipping=_measure_extract(archive,source_tree,work,"shipping")
    r24_control=_measure_extract(r24,source_tree,work,"r24")
    extraction_ratio=shipping["unprofiled_extract_median_s"]/max(r24_control["unprofiled_extract_median_s"],1e-9)

    dst=work/"profiled"; profile=cProfile.Profile(); t=time.perf_counter(); profile.enable(); PRODUCT.extract(archive,dst); profile.disable(); profiled=time.perf_counter()-t
    if PRODUCT.treehash(dst)!=source_tree: raise RuntimeError("profiled extraction identity failure")
    stats=pstats.Stats(profile); total=float(stats.total_tt); rows=[]
    for (filename,line,function),(cc,nc,tt,ct,_callers) in stats.stats.items(): rows.append({"filename":str(filename),"line":int(line),"function":str(function),"primitive_calls":int(cc),"total_calls":int(nc),"self_s":float(tt),"cumulative_s":float(ct),"self_fraction":float(tt/total) if total else 0.0})
    return {
        "schema":"cmpct-v030-g04-ml-shipping-extract-profile-v2",
        "release_credit":False,
        "target":"/".join(TARGET),
        "diagnostic_route":"shipping-product-front-door-vs-exact-r24-control-v2",
        "archive_bytes":archive.stat().st_size,
        "source_tree_sha256":source_tree,
        "build_elapsed_s_context_only":build_s,
        "unprofiled_rounds":ROUNDS,
        "unprofiled_extract_s":shipping["unprofiled_extract_s"],
        "unprofiled_treehash_s":shipping["unprofiled_treehash_s"],
        "unprofiled_combined_s":shipping["unprofiled_combined_s"],
        "unprofiled_extract_median_s":shipping["unprofiled_extract_median_s"],
        "unprofiled_treehash_median_s":shipping["unprofiled_treehash_median_s"],
        "unprofiled_combined_median_s":shipping["unprofiled_combined_median_s"],
        "r24_control":{**r24_control,"build_stats":r24_stats},
        "shipping_to_r24_extract_ratio":float(extraction_ratio),
        "profiled_extract_wall_s_context_only":profiled,
        "profile_total_self_s":total,
        "shipping_build":built,
        "top_by_self":sorted(rows,key=lambda r:r["self_s"],reverse=True)[:60],
        "top_by_cumulative":sorted(rows,key=lambda r:r["cumulative_s"],reverse=True)[:60],
        "claim_boundary":"Function ownership plus same-source shipping-vs-r24 extraction diagnostic only; no timing here is release performance evidence."
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args(); result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:result[k] for k in ("schema","archive_bytes","build_elapsed_s_context_only","unprofiled_extract_median_s","unprofiled_treehash_median_s","unprofiled_combined_median_s","shipping_to_r24_extract_ratio","profiled_extract_wall_s_context_only","release_credit")}|{"r24_extract_median_s":result["r24_control"]["unprofiled_extract_median_s"],"top_by_self":result["top_by_self"][:15]},indent=2))
if __name__=="__main__": main()
