from __future__ import annotations
"""Research-only ownership profile for canonical ML extraction through the real shipping front door."""
import argparse,cProfile,hashlib,json,pstats,shutil,statistics,time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
TARGET=("neutral_hostile_v1","09_ml_artifacts"); ROUNDS=8

def _sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def _extract_once(archive:Path,source_tree:str,dst:Path)->tuple[float,float,float]:
    t=time.perf_counter(); PRODUCT.extract(archive,dst); e=time.perf_counter()-t; t=time.perf_counter(); got=PRODUCT.treehash(dst); h=time.perf_counter()-t
    if got!=source_tree: raise RuntimeError(f"timed extraction identity failure: {archive.name}")
    return e,h,e+h

def _measure_balanced(shipping_archive:Path,r24_archive:Path,source_tree:str,work:Path)->tuple[dict,dict,list[str]]:
    for prefix,archive in (("shipping",shipping_archive),("r24",r24_archive)):
        warm=work/f"{prefix}-warm"; PRODUCT.extract(archive,warm)
        if PRODUCT.treehash(warm)!=source_tree: raise RuntimeError(f"{prefix} warm extraction identity failure")
    samples={"shipping":[],"r24":[]}; order=[]
    for i in range(ROUNDS):
        pair=(("shipping",shipping_archive),("r24",r24_archive)) if i%2==0 else (("r24",r24_archive),("shipping",shipping_archive)); order.append("shipping-r24" if i%2==0 else "r24-shipping")
        for prefix,archive in pair: samples[prefix].append(_extract_once(archive,source_tree,work/f"{prefix}-timed-{i}"))
    def summarize(prefix:str,archive:Path)->dict:
        vals=samples[prefix]; extracts=[x[0] for x in vals]; hashes=[x[1] for x in vals]; combined=[x[2] for x in vals]
        return {"archive_bytes":archive.stat().st_size,"archive_sha256":_sha256(archive),"unprofiled_extract_s":extracts,"unprofiled_treehash_s":hashes,"unprofiled_combined_s":combined,"unprofiled_extract_median_s":float(statistics.median(extracts)),"unprofiled_treehash_median_s":float(statistics.median(hashes)),"unprofiled_combined_median_s":float(statistics.median(combined))}
    return summarize("shipping",shipping_archive),summarize("r24",r24_archive),order

def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True); source=PERF._build_corpora(work/"corpus")[TARGET]; source_tree=PRODUCT.treehash(source); archive=work/"ml.cmpct"; t=time.perf_counter(); built=PRODUCT.build(source,archive); build_s=time.perf_counter()-t
    if built.get("selected")!="g04-overlay" or built.get("r25",{}).get("selected")!="g04-overlay": raise RuntimeError(f"shipping ML target did not select G04 overlay: {built.get('selected')!r}/{built.get('r25',{}).get('selected')!r}")
    verified=PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256")!=source_tree: raise RuntimeError("shipping archive failed exact strong verification")
    r24=work/"ml-r24-control.cmpct"; r24_stats=dict(PRODUCT._locality_bounded_r24_build(source,r24)); r24_verified=PRODUCT.strong_verify(r24)
    if not r24_verified.get("ok") or r24_verified.get("tree_sha256")!=source_tree: raise RuntimeError("r24 control failed exact strong verification")
    shipping,r24_control,order=_measure_balanced(archive,r24,source_tree,work); shipping_m=shipping["unprofiled_extract_median_s"]; r24_m=r24_control["unprofiled_extract_median_s"]
    dst=work/"profiled"; profile=cProfile.Profile(); t=time.perf_counter(); profile.enable(); PRODUCT.extract(archive,dst); profile.disable(); profiled=time.perf_counter()-t
    if PRODUCT.treehash(dst)!=source_tree: raise RuntimeError("profiled extraction identity failure")
    stats=pstats.Stats(profile); total=float(stats.total_tt); rows=[]
    for (filename,line,function),(cc,nc,tt,ct,_callers) in stats.stats.items(): rows.append({"filename":str(filename),"line":int(line),"function":str(function),"primitive_calls":int(cc),"total_calls":int(nc),"self_s":float(tt),"cumulative_s":float(ct),"self_fraction":float(tt/total) if total else 0.0})
    return {"schema":"cmpct-v030-g04-ml-shipping-extract-profile-v2","release_credit":False,"target":"/".join(TARGET),"diagnostic_route":"shipping-product-front-door-vs-exact-r24-control-v2","order_policy":"balanced-ab-ba","round_order":order,"archive_bytes":archive.stat().st_size,"archive_sha256":shipping["archive_sha256"],"source_tree_sha256":source_tree,"build_elapsed_s_context_only":build_s,"unprofiled_rounds":ROUNDS,"unprofiled_extract_s":shipping["unprofiled_extract_s"],"unprofiled_treehash_s":shipping["unprofiled_treehash_s"],"unprofiled_combined_s":shipping["unprofiled_combined_s"],"unprofiled_extract_median_s":shipping_m,"unprofiled_treehash_median_s":shipping["unprofiled_treehash_median_s"],"unprofiled_combined_median_s":shipping["unprofiled_combined_median_s"],"r24_control":{**r24_control,"build_stats":r24_stats},"shipping_to_r24_extract_ratio":float(shipping_m/max(r24_m,1e-9)),"shipping_minus_r24_extract_s":float(shipping_m-r24_m),"shipping_minus_r24_archive_bytes":int(shipping["archive_bytes"]-r24_control["archive_bytes"]),"profiled_extract_wall_s_context_only":profiled,"profile_total_self_s":total,"shipping_build":built,"top_by_self":sorted(rows,key=lambda r:r["self_s"],reverse=True)[:60],"top_by_cumulative":sorted(rows,key=lambda r:r["cumulative_s"],reverse=True)[:60],"claim_boundary":"Function ownership plus balanced same-source shipping-vs-r24 extraction diagnostic only; no timing here is release performance evidence."}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args(); result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:result[k] for k in ("schema","archive_bytes","archive_sha256","order_policy","build_elapsed_s_context_only","unprofiled_extract_median_s","unprofiled_treehash_median_s","unprofiled_combined_median_s","shipping_to_r24_extract_ratio","shipping_minus_r24_extract_s","shipping_minus_r24_archive_bytes","profiled_extract_wall_s_context_only","release_credit")}|{"r24_archive_sha256":result["r24_control"]["archive_sha256"],"r24_extract_median_s":result["r24_control"]["unprofiled_extract_median_s"],"top_by_self":result["top_by_self"][:15]},indent=2))
if __name__=="__main__": main()
