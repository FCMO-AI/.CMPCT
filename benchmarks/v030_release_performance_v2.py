from __future__ import annotations

"""Final-authority binding for the frozen v0.30 paired runtime promotion gate.

The frozen gate is unchanged. After it completes, this adapter runs one explicitly non-credit v0.30 pack per
frozen target with r24/manifest overlap disabled. Exact bytes and user-tree identity must match the ordinary
shipping run. The counterfactual exists only to test whether independent-builder overlap owns the measured pack
RSS debt; it cannot make a red release gate green.
"""
import argparse
import json
from pathlib import Path
from benchmarks import v030_release_performance as B
from experiments import entropygraph_v030_release_product as PRODUCT
from tools import check_v030_release_lock as RELEASE_LOCK

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_v2.py"

def _candidate_fingerprint() -> str:
    manifest = RELEASE_LOCK.load_manifest(); fingerprint, _ = RELEASE_LOCK.fingerprint(manifest); return fingerprint

def _expected_tree_for_runtime_v2(engine: str, source: Path, historical_expected: str) -> str:
    if engine == "v030": return PRODUCT.treehash(source)
    return historical_expected
B._expected_tree_for_engine = _expected_tree_for_runtime_v2

_BASE_RUN_WORKER = B._run_worker
_PACK_DIAGNOSTICS: list[dict] = []
def _run_worker_with_diagnostics(*args: str) -> dict:
    result = _BASE_RUN_WORKER(*args)
    if "--op" in args and args[args.index("--op") + 1] == "pack" and result.get("build_stats") is not None:
        def _arg(name: str) -> str | None: return args[args.index(name) + 1] if name in args else None
        _PACK_DIAGNOSTICS.append({"engine":_arg("--engine"),"source":_arg("--source"),"archive":_arg("--archive"),"build_stats":result["build_stats"]})
    return result
B._run_worker = _run_worker_with_diagnostics

def _sequential_r24_rss_oracle(work_root: Path, release_rows: list[dict]) -> list[dict]:
    roots = B._build_corpora(work_root)
    by_target={(row["suite"],row["name"]):row for row in release_rows}; rows=[]
    for suite,name in B.TARGETS:
        source=roots[(suite,name)]; ordinary=by_target[(suite,name)]
        archive=work_root/"diagnostic-sequential-r24"/f"{suite}-{name}.cmpct"; archive.parent.mkdir(parents=True,exist_ok=True)
        measured=_BASE_RUN_WORKER("--engine","v030","--op","pack","--source",str(source),"--archive",str(archive),"--diagnostic-sequential-r24")
        expected_tree=PRODUCT.treehash(source)
        if measured["tree_sha256"] != expected_tree: raise RuntimeError(f"sequential-r24 oracle tree mismatch for {suite}/{name}")
        if int(measured["archive_bytes"]) != int(ordinary["v030_bytes"]): raise RuntimeError(f"sequential-r24 oracle byte mismatch for {suite}/{name}")
        ordinary_peak=max(int(rep["v030"]["pack_peak_rss_kib"]) for rep in ordinary["repetitions"])
        rows.append({"suite":suite,"name":name,"archive_bytes":int(measured["archive_bytes"]),"tree_sha256":expected_tree,"pack_wall_s":float(measured["wall_s"]),"pack_peak_rss_kib":int(measured["peak_rss_kib"]),"ordinary_max_pack_peak_rss_kib":ordinary_peak,"rss_ratio_vs_ordinary_max":float(measured["peak_rss_kib"])/max(1,ordinary_peak),"release_credit":False})
    return rows

def run(work_root: Path) -> dict:
    candidate_fingerprint=_candidate_fingerprint(); _PACK_DIAGNOSTICS.clear(); result=dict(B.run(work_root))
    result["engine"]="experiments/entropygraph_v030_release_product.py"; result["release_facade"]="cmpct-v030-release-product-v1"; result["worker"]="benchmarks/v030_perf_worker_v2.py"; result["identity_binding"]="v029-historical-content-tree + v030-canonical-user-tree"; result["candidate_fingerprint"]=candidate_fingerprint
    result["diagnostics"]={"release_credit":False,"timing_boundary_changed":False,"source":"worker-emitted post-pack build_stats","pack_build_stats":list(_PACK_DIAGNOSTICS)}
    result["diagnostics"]["sequential_r24_overlap_oracle"]={"release_credit":False,"hypothesis":"overlapping r24 construction with manifest/r25 preparation materially owns pack RSS debt","invariant":"same complete archive bytes and canonical user-tree identity as ordinary shipping build","rows":_sequential_r24_rss_oracle(work_root,result["rows"])}
    return result

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-release-performance-v2-work")); parser.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-release-performance-v2.json")); args=parser.parse_args(); result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"candidate_fingerprint":result["candidate_fingerprint"],"totals":result["totals"],"gate":result["gate"],"sequential_r24_overlap_oracle":result["diagnostics"]["sequential_r24_overlap_oracle"]},indent=2),flush=True)
    if not result["gate"]["passed"]: raise SystemExit("v0.30 release-product runtime promotion gate failed")
if __name__=="__main__": main()
