from __future__ import annotations

"""Research-only causal controls for the v0.30 ML extraction bottleneck."""
import argparse, json, shutil, statistics, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final as CANONICAL
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
ROUNDS = 7

def _selected_transforms(build_stats: dict) -> list[str]:
    auditions = build_stats.get("r25", {}).get("g04", {}).get("auditions", [])
    return [str(row.get("selected")) for row in auditions if row.get("selected") not in (None, "none")]

def _import_rss_kib(module: str) -> int:
    code = "import importlib,json,resource;importlib.import_module(%r);print(json.dumps({'rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}))" % module
    proc = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
    return int(json.loads(proc.stdout.strip().splitlines()[-1])["rss_kib"])

def _timed_extracts(archive: Path, source_tree: str, root: Path, label: str) -> list[float]:
    warm = root / f"{label}-warm"
    PRODUCT.extract(archive, warm)
    if PRODUCT.treehash(warm) != source_tree:
        raise RuntimeError(f"{label} warm extraction identity failure")
    samples = []
    for index in range(ROUNDS):
        dst = root / f"{label}-{index}"
        started = time.perf_counter(); PRODUCT.extract(archive, dst); elapsed = time.perf_counter() - started
        if PRODUCT.treehash(dst) != source_tree:
            raise RuntimeError(f"{label} timed extraction identity failure")
        samples.append(elapsed)
    return samples

def run(work: Path) -> dict:
    import_rss = {"v029_release": _import_rss_kib("experiments.entropygraph_v029_release"), "v030_release_product": _import_rss_kib("experiments.entropygraph_v030_release_product")}
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    source = PERF._build_corpora(work / "corpus")[TARGET]; source_tree = PRODUCT.treehash(source)
    baseline_archive = work / "shipping.cmpct"
    started = time.perf_counter(); baseline_build = PRODUCT.build(source, baseline_archive); baseline_build_s = time.perf_counter() - started
    baseline_verify = PRODUCT.strong_verify(baseline_archive)
    if not baseline_verify.get("ok") or baseline_verify.get("tree_sha256") != source_tree: raise RuntimeError("baseline shipping archive failed exact verification")
    baseline_transforms = _selected_transforms(baseline_build)
    if "delimiter" not in baseline_transforms: raise RuntimeError("exact-head ML shipping route no longer selects DGO1; counterfactual is stale")

    # The shipping ML route may replace canonical-final's local thread overlay with the preserved release base's
    # ProcessPoolExecutor. Spawned children import a fresh product module, so a parent-process audition monkeypatch
    # cannot cross that boundary. This research-only control therefore disables exactly that scheduler eligibility
    # seam while patching the private canonical G04 semantic owner. Scheduling is deliberately changed only to make
    # the semantic counterfactual observable; candidate build wall remains context-only and earns no product credit.
    owner = CANONICAL.SHARED.G
    original = owner._audition_record
    base_impl = PRODUCT._BASE_IMPL
    original_process_pool_eligible = base_impl._g04_process_pool_eligible
    audition_timings = []
    wrapper_invocations = 0
    def no_delimiter_audition(record_id, record, users):
        nonlocal wrapper_invocations
        wrapper_invocations += 1
        audition_started = time.perf_counter()
        raw, transform, stats = original(record_id, record, users)
        audition_elapsed = time.perf_counter() - audition_started
        is_delimiter = transform == "delimiter" or (
            isinstance(transform, (list, tuple)) and bool(transform) and transform[0] == "delimiter"
        )
        audition_timings.append({
            "record_id": int(record_id),
            "raw_bytes": int(stats.get("raw_bytes", 0)),
            "selected_before_counterfactual": str(stats.get("selected", "none")),
            "selected_after_counterfactual": "none" if is_delimiter else str(stats.get("selected", "none")),
            "payload_saving_bytes": int(stats.get("payload_saving_bytes", 0)),
            "audition_wall_s_context_only": audition_elapsed,
            "counterfactual_rejected_delimiter": bool(is_delimiter),
        })
        if not is_delimiter:
            return raw, transform, stats
        return record, None, {**stats, "selected": "none", "counterfactual_rejected": "delimiter"}

    candidate_archive = work / "no-delimiter.cmpct"
    try:
        owner._audition_record = no_delimiter_audition
        base_impl._g04_process_pool_eligible = lambda graph_path, graph_records: False
        started = time.perf_counter(); candidate_build = PRODUCT.build(source, candidate_archive); candidate_build_s = time.perf_counter() - started
    finally:
        base_impl._g04_process_pool_eligible = original_process_pool_eligible
        owner._audition_record = original
    candidate_verify = PRODUCT.strong_verify(candidate_archive)
    if not candidate_verify.get("ok") or candidate_verify.get("tree_sha256") != source_tree: raise RuntimeError("no-delimiter candidate failed exact verification")
    candidate_transforms = _selected_transforms(candidate_build)
    audition_timings.sort(key=lambda row: row["record_id"])
    counterfactual_effective = wrapper_invocations > 0 and any(row["counterfactual_rejected_delimiter"] for row in audition_timings) and "delimiter" not in candidate_transforms

    # Persist enough falsification state in the returned receipt that a future ownership miss is diagnosable from
    # the artifact. The workflow validates counterfactual_effective after this JSON is written by main().
    if not counterfactual_effective:
        return {
            "schema":"cmpct-v030-g04-delimiter-cost-counterfactual-v1","controls_version":11,"release_credit":False,"target":"/".join(TARGET),"source_tree_sha256":source_tree,"rounds":ROUNDS,
            "fresh_process_import_rss_kib_context_only":import_rss,
            "baseline":{"archive_bytes":baseline_archive.stat().st_size,"build_wall_s_context_only":baseline_build_s,"selected_transforms":baseline_transforms},
            "no_delimiter":{"archive_bytes":candidate_archive.stat().st_size,"build_wall_s_context_only":candidate_build_s,"selected_transforms":candidate_transforms,"wrapper_invocations":wrapper_invocations,"audition_timing_context_only":audition_timings,"strong_verify":candidate_verify},
            "counterfactual_effective":False,
            "claim_boundary":"Research control invalid: diagnostic state is persisted before workflow falsification. No size, extraction, build-wall, or release claim may be credited."
        }

    baseline_samples = _timed_extracts(baseline_archive, source_tree, work, "baseline")
    shipping_overlay = CANONICAL.SHARED.G.O
    original_inverse = shipping_overlay.delimiter_inverse
    try:
        shipping_overlay.delimiter_inverse = CANONICAL._banded_delimiter_inverse
        banded_samples = _timed_extracts(baseline_archive, source_tree, work, "banded-same-bytes")
    finally:
        shipping_overlay.delimiter_inverse = original_inverse
    candidate_samples = _timed_extracts(candidate_archive, source_tree, work, "candidate")
    baseline_bytes = baseline_archive.stat().st_size; candidate_bytes = candidate_archive.stat().st_size
    baseline_median = float(statistics.median(baseline_samples)); banded_median = float(statistics.median(banded_samples)); candidate_median = float(statistics.median(candidate_samples))
    return {
        "schema":"cmpct-v030-g04-delimiter-cost-counterfactual-v1","controls_version":11,"release_credit":False,"target":"/".join(TARGET),"source_tree_sha256":source_tree,"rounds":ROUNDS,
        "fresh_process_import_rss_kib_context_only":import_rss,"fresh_process_import_rss_ratio_context_only":import_rss["v030_release_product"]/import_rss["v029_release"],
        "baseline":{"archive_bytes":baseline_bytes,"build_wall_s_context_only":baseline_build_s,"selected_transforms":baseline_transforms,"extract_s":baseline_samples,"median_extract_s":baseline_median},
        "banded_same_archive_bytes":{"archive_bytes":baseline_bytes,"inverse":"guarded-banded-v2","extract_s":banded_samples,"median_extract_s":banded_median,"median_extract_ratio_vs_shipping":banded_median/baseline_median,"median_extract_speedup_vs_shipping":baseline_median/banded_median},
        "no_delimiter":{"archive_bytes":candidate_bytes,"build_wall_s_context_only":candidate_build_s,"selected_transforms":candidate_transforms,"wrapper_invocations":wrapper_invocations,"audition_timing_context_only":audition_timings,"extract_s":candidate_samples,"median_extract_s":candidate_median},
        "no_delimiter_delta":{"archive_bytes":candidate_bytes-baseline_bytes,"archive_pct":(candidate_bytes/baseline_bytes-1.0)*100.0,"build_wall_s_context_only":candidate_build_s-baseline_build_s,"build_ratio_context_only":candidate_build_s/baseline_build_s,"median_extract_s":candidate_median-baseline_median,"median_extract_ratio":candidate_median/baseline_median,"median_extract_speedup":baseline_median/candidate_median},
        "counterfactual_effective":True,
        "claim_boundary":"Research controls only: same-source shipping, same-byte reviewed inverse swap, and no-DGO1 rebuild. The no-DGO1 rebuild forces only the preserved release-base G04 process-pool eligibility seam off so the parent private audition wrapper is observable, then rejects the actual structured DGO1 descriptor; both hooks are restored in finally. Per-record audition wall times and candidate build wall are diagnostic context only. No release threshold, evaluator, grammar, or comparator is changed."
    }

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if not result.get("counterfactual_effective"):
        raise RuntimeError("no-DGO1 counterfactual did not reach and reject the shipping delimiter owner; inspect persisted receipt")
    print(json.dumps({"import_rss":result["fresh_process_import_rss_kib_context_only"],"baseline":result["baseline"],"banded_same_archive_bytes":result["banded_same_archive_bytes"],"no_delimiter":result["no_delimiter"],"no_delimiter_delta":result["no_delimiter_delta"],"counterfactual_effective":True,"release_credit":False},indent=2))
if __name__ == "__main__": main()
