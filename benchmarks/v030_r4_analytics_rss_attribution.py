from __future__ import annotations

"""Fresh-process RSS attribution for the Analytics v0.30 / R4 dual-owner paths.

The prior locality harness reported ~0.5 GiB RUSAGE_SELF after corpus generation, baseline creation,
dual-owner creation/extraction, duplicated-view construction and hundreds of probes in one process.
That number is not attributable to product state. This diagnostic holds the frozen Analytics input on
disk, then launches independent processes for runtime/import, ordinary v0.30 build, R4 dual build and
R4 dual extract. It reports each process' own peak RSS; no subtraction is presented as exact memory
ownership because ru_maxrss is a high-water mark.

Pre-registered interpretation: if the fresh build/extract peaks are materially below the monolithic
498456 KiB observation, the old number is harness/runtime aggregation debt, not a product-state budget.
If any fresh product operation remains near that peak, treat it as real operation-level resource debt
and profile allocations before optimizing representation. Diagnostic only; no release credit.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

SCHEMA = "cmpct-v030-r4-analytics-rss-attribution-v1"
MONOLITHIC_OBSERVED_KIB = 498_456


def _rss() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _worker(mode: str, source: Path, out: Path, candidate: Path) -> None:
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
    payload = {
        "mode": mode,
        "peak_rss_kib": _rss(),
        "wall_s": time.perf_counter() - t0,
        "cpu_s": time.process_time() - cpu0,
    }
    print(json.dumps(payload, sort_keys=True))


def _run_worker(script: Path, mode: str, source: Path, out: Path, candidate: Path) -> dict:
    if out.exists():
        if out.is_dir(): shutil.rmtree(out)
        else: out.unlink()
    cp = subprocess.run(
        [sys.executable, str(script), "--worker", mode, "--source", str(source), "--worker-out", str(out), "--candidate", str(candidate)],
        text=True, capture_output=True, check=True, env=os.environ.copy(),
    )
    lines = [x for x in cp.stdout.splitlines() if x.strip()]
    return json.loads(lines[-1])


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    # Corpus generation is deliberately outside every measured product worker.
    from benchmarks import mosaic_v029_generalization_bench as v029
    neutral = v029._load(v029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_rss_neutral")
    repair = v029._load(v029.REPAIR_PATH, "r4_rss_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    script = Path(__file__).resolve()
    candidate = work / "dual-candidate"

    results = {}
    for mode in ("runtime", "product_import", "dual_import", "v030_build", "dual_build", "dual_extract"):
        results[mode] = _run_worker(script, mode, source, work / f"worker-{mode}", candidate)

    max_fresh = max(v["peak_rss_kib"] for k, v in results.items() if k in {"v030_build", "dual_build", "dual_extract"})
    ratio = max_fresh / MONOLITHIC_OBSERVED_KIB
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "monolithic_prior_peak_rss_kib": MONOLITHIC_OBSERVED_KIB,
        "fresh_process": results,
        "max_fresh_product_operation_rss_kib": max_fresh,
        "max_fresh_to_monolithic_ratio": ratio,
        "interpretation": {
            "fresh_materially_below_monolithic": max_fresh <= 0.75 * MONOLITHIC_OBSERVED_KIB,
            "fresh_near_monolithic": max_fresh >= 0.90 * MONOLITHIC_OBSERVED_KIB,
            "note": "thresholds classify attribution strength only; they are not release memory budgets",
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_frozen_analytics_input": True,
            "corpus_generation_outside_measured_workers": True,
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
    p.add_argument("--worker", choices=("runtime","product_import","dual_import","v030_build","dual_build","dual_extract"))
    p.add_argument("--source", type=Path)
    p.add_argument("--worker-out", type=Path)
    p.add_argument("--candidate", type=Path)
    a = p.parse_args()
    if a.worker:
        _worker(a.worker, a.source, a.worker_out, a.candidate)
        return
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({k:d[k] for k in ("monolithic_prior_peak_rss_kib","fresh_process","max_fresh_product_operation_rss_kib","max_fresh_to_monolithic_ratio","interpretation")}, indent=2))

if __name__ == "__main__":
    main()
