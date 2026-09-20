from __future__ import annotations
"""Fresh-process ML verification-cache A/B. Research evidence only; no release credit."""
import argparse, json, os, resource, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def child(mode: str, source: Path, archive: Path) -> None:
    from experiments import entropygraph_v030_release_product as RP
    R = RP.C.POLICY.R
    if mode == "tight":
        # Research-only dynamic policy injection. _cache_put resolves these module globals at call time.
        R.MAX_RECORD_CACHE_BYTES = 16 * 1024 * 1024
        R.MAX_NODE_CACHE_BYTES = 8 * 1024 * 1024
    before = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()
    stats = RP.build(source, archive)
    wall = time.perf_counter() - t0
    after = resource.getrusage(resource.RUSAGE_SELF)
    verified = RP.C.strong_verify(archive)
    print(json.dumps({
        "mode": mode,
        "wall_s": wall,
        "cpu_s": (after.ru_utime-before.ru_utime)+(after.ru_stime-before.ru_stime),
        "peak_rss_kib": int(after.ru_maxrss),
        "archive_bytes": archive.stat().st_size,
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "tree_sha256": verified.get("tree_sha256"),
        "physical_record_reads": verified.get("physical_record_reads"),
        "record_cache_peak_bound_bytes": verified.get("record_cache_peak_bound_bytes"),
        "node_cache_peak_bound_bytes": verified.get("node_cache_peak_bound_bytes"),
    }, separators=(",", ":")))


def invoke(mode: str, source: Path, out: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    p = subprocess.run([sys.executable, __file__, "--child", mode, "--source", str(source), "--archive", str(out)], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    return json.loads([line for line in p.stdout.splitlines() if line.strip()][-1])


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--child", choices=("base","tight")); p.add_argument("--source", type=Path); p.add_argument("--archive", type=Path); p.add_argument("--work-root", type=Path); p.add_argument("--output", type=Path); a=p.parse_args()
    if a.child:
        child(a.child, a.source, a.archive); return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root, ignore_errors=True); a.work_root.mkdir(parents=True)
    source = PERF._build_corpora(a.work_root/"corpus")[("neutral_hostile_v1","09_ml_artifacts")]
    rows=[]
    for rep, order in enumerate((("base","tight"),("tight","base"))):
        pair={"rep":rep}
        for mode in order: pair[mode]=invoke(mode,source,a.work_root/f"ml-{rep}-{mode}.cmpct")
        pair["identity_equal"]=(pair["base"]["archive_bytes"]==pair["tight"]["archive_bytes"] and pair["base"]["selected"]==pair["tight"]["selected"] and pair["base"]["format_revision"]==pair["tight"]["format_revision"] and pair["base"]["tree_sha256"]==pair["tight"]["tree_sha256"])
        pair["rss_ratio"]=pair["tight"]["peak_rss_kib"]/pair["base"]["peak_rss_kib"]
        pair["wall_ratio"]=pair["tight"]["wall_s"]/pair["base"]["wall_s"]
        rows.append(pair)
    exact=all(r["identity_equal"] for r in rows)
    result={"schema":"cmpct-v030-verify-cache-ownership-ab-v1","release_credit":False,"rows":rows,"all_exact":exact,"claim_boundary":"Frozen ML whole promoted build; only release-reader record/node LRU caps change (64/32 MiB -> 16/8 MiB). Exact archive identity/selection/tree plus parent ru_maxrss, wall/CPU and physical reads charged."}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
    if not exact: raise SystemExit("verification cache cap changed product identity")

if __name__ == "__main__": main()
