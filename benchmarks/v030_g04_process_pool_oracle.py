from __future__ import annotations

"""Exact-byte oracle for replacing the promoted G0-G4 audition thread pool with processes.

The promoted v0.30 product already schedules independent G0-G4 record auditions concurrently, but it uses a
``ThreadPoolExecutor``.  The audition path is dominated by Python transform search and therefore cannot obtain
true CPU parallelism under CPython's GIL.  This oracle changes *only* that scheduler in-process:

* the source graph, record order, owning ``_audition_record`` implementation and user-count inputs are unchanged;
* ``ProcessPoolExecutor.map`` preserves input order, so the exact records/transforms passed to ``_write_overlay``
  remain deterministic;
* complete product bytes must be byte-for-byte identical to the current promoted product on every measured run;
* both products are strongly verified after construction;
* timing uses a balanced baseline-first / process-first order to avoid a one-sided warm-cache advantage.

This is deliberately an oracle rather than an automatic release-path switch.  A scheduler replacement earns
promotion only if GitHub-runner evidence shows material wall-clock improvement without changing one archive byte.
No compression threshold, candidate-admission rule, locality ceiling, verification boundary or release gate is
changed here.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = ("02_office_workspace", "05_logs_and_telemetry")
ORDERS = (("baseline", "process"), ("process", "baseline"))
MIN_MEDIAN_IMPROVEMENT_PCT = 10.0
MIN_MEDIAN_SAVED_S = 2.0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _audition_worker(payload: tuple[int, bytes, int]):
    """Spawn-safe exact delegation to the canonical owning audition implementation."""
    record_id, record, users = payload
    # Import in the child rather than serializing module state.  The release product installs only scheduling and
    # profile-isolation bindings; the owning transform function and its byte grammar remain the canonical clone.
    from experiments import entropygraph_v030_release_product as child_product

    shared = child_product.C.SHARED
    return shared.G._audition_record(record_id, record, users)


def _process_overlay_retained_graph(graph_path: Path, overlay_path: Path) -> dict:
    """Exact promoted overlay construction with ordered spawned-process auditions."""
    shared = PRODUCT.C.SHARED
    source_format, _source, graph_meta, graph_records = shared.strict._read_source_records(graph_path)
    users = shared.O._record_member_lengths(graph_meta, len(graph_records))

    if graph_records:
        # Hosted release runners currently expose four logical CPUs.  Keep this bounded for developer machines and
        # avoid the unbounded process fan-out that would turn an optimization into a resource regression.
        worker_count = min(4, len(graph_records), max(1, os.cpu_count() or 1))
        ctx = mp.get_context("spawn")
        payloads = [(record_id, record, users[record_id]) for record_id, record in enumerate(graph_records)]
        with ProcessPoolExecutor(
            max_workers=worker_count,
            mp_context=ctx,
        ) as pool:
            outcomes = list(pool.map(_audition_worker, payloads, chunksize=1))
    else:
        worker_count = 0
        outcomes = []

    records = [row[0] for row in outcomes]
    transforms = [row[1] for row in outcomes]
    auditions = [row[2] for row in outcomes]
    annotated_meta = dict(graph_meta)
    annotated_meta["overlay_source_format"] = source_format
    write_stats = shared.G._write_overlay(annotated_meta, records, transforms, overlay_path)
    return {
        "source_format": source_format,
        "records": records,
        "transforms": transforms,
        "auditions": auditions,
        "write_stats": write_stats,
        "verified": None,
        "verification_state": "deferred-until-byte-win",
        "audition_workers": worker_count,
        "audition_scheduler": "bounded-ordered-spawn-process-pool-oracle-v1",
        "delimiter_transpose": "bulk-rectangular-prefix-v1",
    }


def _build_one(root: Path, out: Path, scheduler: str, baseline_overlay) -> dict:
    shared = PRODUCT.C.SHARED
    if scheduler == "baseline":
        shared._overlay_retained_graph = baseline_overlay
    elif scheduler == "process":
        shared._overlay_retained_graph = _process_overlay_retained_graph
    else:
        raise ValueError(scheduler)

    started = time.perf_counter()
    stats = dict(PRODUCT.build(root, out))
    elapsed = time.perf_counter() - started
    verified = PRODUCT.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"{scheduler} product failed strong verification: {verified!r}")
    return {
        "scheduler": scheduler,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "create_s": elapsed,
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "format_profile": stats.get("format_profile"),
        "tree_sha256": verified.get("tree_sha256"),
        "portfolio_create_s": stats.get("portfolio_create_s"),
        "r24_create_s": (stats.get("r24") or {}).get("create_s"),
        "r25_create_s": (stats.get("r25") or {}).get("create_s"),
        "g04_create_s": ((stats.get("r25") or {}).get("g04") or {}).get("portfolio_create_s"),
    }


def _build_neutral_corpus(root: Path) -> None:
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_g04_process_oracle_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_g04_process_oracle_repair")
    repair.install_generation_hooks(neutral)
    neutral.build(root)
    repair.normalize_root(root)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "neutral"
    _build_neutral_corpus(corpus)

    baseline_overlay = PRODUCT.C.SHARED._overlay_retained_graph
    rows: list[dict] = []
    try:
        for target in TARGETS:
            source = corpus / target
            if not source.is_dir():
                raise RuntimeError(f"missing frozen workload {target}")
            repetitions = []
            for rep, order in enumerate(ORDERS):
                results = {}
                for scheduler in order:
                    out = work_root / f"{target}-{rep}-{scheduler}.cmpct"
                    results[scheduler] = _build_one(source, out, scheduler, baseline_overlay)
                baseline = results["baseline"]
                process = results["process"]
                byte_identical = (
                    baseline["archive_bytes"] == process["archive_bytes"]
                    and baseline["archive_sha256"] == process["archive_sha256"]
                    and baseline["tree_sha256"] == process["tree_sha256"]
                )
                if not byte_identical:
                    raise RuntimeError(
                        f"process audition scheduler changed exact product bytes/tree for {target}: "
                        f"baseline={baseline!r} process={process!r}"
                    )
                saved = float(baseline["create_s"]) - float(process["create_s"])
                pct = saved / max(float(baseline["create_s"]), 1e-9) * 100.0
                repetitions.append({
                    "rep": rep,
                    "execution_order": list(order),
                    "baseline": baseline,
                    "process": process,
                    "byte_identical": True,
                    "wallclock_saved_s": saved,
                    "wallclock_improvement_pct": pct,
                })

            base_times = [float(row["baseline"]["create_s"]) for row in repetitions]
            proc_times = [float(row["process"]["create_s"]) for row in repetitions]
            baseline_median = statistics.median(base_times)
            process_median = statistics.median(proc_times)
            saved = baseline_median - process_median
            pct = saved / max(baseline_median, 1e-9) * 100.0
            rows.append({
                "workload": target,
                "baseline_median_s": baseline_median,
                "process_median_s": process_median,
                "median_saved_s": saved,
                "median_improvement_pct": pct,
                "all_byte_identical": all(row["byte_identical"] for row in repetitions),
                "material_improvement": saved >= MIN_MEDIAN_SAVED_S and pct >= MIN_MEDIAN_IMPROVEMENT_PCT,
                "repetitions": repetitions,
            })
    finally:
        PRODUCT.C.SHARED._overlay_retained_graph = baseline_overlay

    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_byte_identical": all(row["all_byte_identical"] for row in rows),
        "all_materially_faster": all(row["material_improvement"] for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-process-pool-oracle-v1",
        "engine": "experiments/entropygraph_v030_release_product.py",
        "hypothesis": "replace GIL-bound ordered G0-G4 audition threads with bounded spawned processes",
        "contract": {
            "scheduling_only": True,
            "exact_product_bytes_required": True,
            "strong_verify_required": True,
            "targets": list(TARGETS),
            "orders": [list(order) for order in ORDERS],
            "minimum_median_improvement_pct": MIN_MEDIAN_IMPROVEMENT_PCT,
            "minimum_median_saved_s": MIN_MEDIAN_SAVED_S,
            "no_release_threshold_changed": True,
        },
        "rows": rows,
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-process-oracle-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-process-oracle.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["rows"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("G0-G4 process-pool scheduler oracle did not earn promotion")


if __name__ == "__main__":
    main()
