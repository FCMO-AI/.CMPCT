from __future__ import annotations

"""Fresh-process RSS attribution for Analytics v0.30 / R4 dual-owner operations.

The first attribution harness correctly separated product operations into subprocesses, but launched
those subprocesses from the same Python process that had generated the large neutral corpus. On Linux,
ru_maxrss is a process high-water mark and a fork/exec child can inherit a misleading pre-exec high-water
context. The resulting ~470 MiB even for an empty `runtime` worker therefore cannot identify product
ownership.

This v2 diagnostic deliberately separates *preparation* from *measurement*. CI first generates the frozen
Analytics corpus in one Python process which exits. Bash then launches every measured Python worker
independently, so each starts from the small runner shell rather than the corpus-building interpreter.
Each worker records starting resident RSS from /proc when available plus its own RUSAGE_SELF peak. A final
unmeasured aggregation process combines the worker receipts. No peak subtraction is claimed as exact
memory ownership; runtime/import/build/extract comparisons are attribution evidence only.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import time

SCHEMA = "cmpct-v030-r4-analytics-rss-attribution-v2"
MONOLITHIC_OBSERVED_KIB = 498_456
MODES = ("runtime", "product_import", "dual_import", "v030_build", "dual_build", "dual_extract")


def _peak_rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _current_rss_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return None


def _worker(mode: str, source: Path, out: Path, candidate: Path) -> dict:
    if out.exists():
        if out.is_dir():
            shutil.rmtree(out)
        else:
            out.unlink()
    start_current = _current_rss_kib()
    start_peak = _peak_rss_kib()
    t0 = time.perf_counter()
    cpu0 = time.process_time()
    if mode == "runtime":
        pass
    elif mode == "product_import":
        from experiments import entropygraph_v030_release_product as _product  # noqa:F401
    elif mode == "dual_import":
        from benchmarks import v030_r4_analytics_dual_owner_oracle as _dual  # noqa:F401
    elif mode == "v030_build":
        from experiments import entropygraph_v030_release_product as product
        product.build(source, out)
    elif mode == "dual_build":
        from benchmarks import v030_r4_analytics_dual_owner_oracle as dual
        dual._build_candidate(source, candidate, out)
    elif mode == "dual_extract":
        from benchmarks import v030_r4_analytics_dual_owner_oracle as dual
        dual._extract_candidate(candidate, out)
    else:
        raise ValueError(mode)
    return {
        "mode": mode,
        "start_current_rss_kib": start_current,
        "start_peak_rss_kib": start_peak,
        "end_current_rss_kib": _current_rss_kib(),
        "peak_rss_kib": _peak_rss_kib(),
        "wall_s": time.perf_counter() - t0,
        "cpu_s": time.process_time() - cpu0,
    }


def prepare(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    from benchmarks import mosaic_v029_generalization_bench as v029
    neutral = v029._load(v029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_rss_neutral_v2")
    repair = v029._load(v029.REPAIR_PATH, "r4_rss_repair_v2")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    if not source.is_dir():
        raise RuntimeError("frozen Analytics source missing after preparation")
    return {"source": str(source), "candidate": str(work / "dual-candidate")}


def aggregate(work: Path) -> dict:
    results = {}
    for mode in MODES:
        p = work / "rss-workers" / f"{mode}.json"
        if not p.exists():
            raise RuntimeError(f"missing worker receipt: {p}")
        d = json.loads(p.read_text())
        if d.get("mode") != mode:
            raise RuntimeError(f"worker receipt mode mismatch for {mode}")
        results[mode] = d
    product_modes = ("v030_build", "dual_build", "dual_extract")
    max_fresh = max(results[m]["peak_rss_kib"] for m in product_modes)
    runtime_peak = results["runtime"]["peak_rss_kib"]
    ratio = max_fresh / MONOLITHIC_OBSERVED_KIB
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "monolithic_prior_peak_rss_kib": MONOLITHIC_OBSERVED_KIB,
        "fresh_process": results,
        "runtime_peak_rss_kib": runtime_peak,
        "max_fresh_product_operation_rss_kib": max_fresh,
        "max_fresh_minus_runtime_peak_kib_diagnostic_only": max_fresh - runtime_peak,
        "max_fresh_to_monolithic_ratio": ratio,
        "interpretation": {
            "fresh_materially_below_monolithic": max_fresh <= 0.75 * MONOLITHIC_OBSERVED_KIB,
            "fresh_near_monolithic": max_fresh >= 0.90 * MONOLITHIC_OBSERVED_KIB,
            "runtime_itself_near_monolithic": runtime_peak >= 0.90 * MONOLITHIC_OBSERVED_KIB,
            "note": "differences between ru_maxrss peaks are diagnostic comparisons, never exact owned-memory accounting",
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_frozen_analytics_input": True,
            "corpus_generation_outside_measured_workers": True,
            "workers_launched_independently_from_runner_shell": True,
            "fresh_process_per_operation": True,
            "ru_maxrss_not_subtracted_as_exact_ownership": True,
            "product_format_changed": False,
            "selector_changed": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-rss-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-rss-attribution.json"))
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--aggregate", action="store_true")
    p.add_argument("--worker", choices=MODES)
    p.add_argument("--source", type=Path)
    p.add_argument("--worker-out", type=Path)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--worker-json", type=Path)
    a = p.parse_args()
    if a.prepare_only:
        print(json.dumps(prepare(a.work_root), sort_keys=True))
        return
    if a.worker:
        if not all((a.source, a.worker_out, a.candidate, a.worker_json)):
            raise SystemExit("--worker requires --source --worker-out --candidate --worker-json")
        d = _worker(a.worker, a.source, a.worker_out, a.candidate)
        a.worker_json.parent.mkdir(parents=True, exist_ok=True)
        a.worker_json.write_text(json.dumps(d, indent=2) + "\n")
        print(json.dumps(d, sort_keys=True))
        return
    if a.aggregate:
        d = aggregate(a.work_root)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(d, indent=2) + "\n")
        print(json.dumps({k:d[k] for k in ("fresh_process","runtime_peak_rss_kib","max_fresh_product_operation_rss_kib","max_fresh_minus_runtime_peak_kib_diagnostic_only","max_fresh_to_monolithic_ratio","interpretation")}, indent=2))
        return
    raise SystemExit("choose --prepare-only, --worker MODE, or --aggregate")


if __name__ == "__main__":
    main()
