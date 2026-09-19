from __future__ import annotations

"""Exact-byte oracle for the promoted G0-G4 process audition scheduler.

The release product now uses spawned processes for sufficiently large G0-G4 record tournaments because the
pre-promotion oracle showed that the Python-heavy transform search was materially GIL-bound. This harness remains
an independent regression oracle rather than becoming self-referential:

1. build the accepted v0.29/pre-overlay graph substrate once for each frozen workload;
2. run the previous ordered-thread scheduler and the promoted product scheduler on that same retained graph;
3. invoke both from a worker thread, matching canonical r25 nesting;
4. require exact overlay bytes, exact SHA-256 and exact logical-tree verification on every repetition;
5. use balanced execution order and preserve the original materiality hurdle.

No transform, compression level, record order, locality rule, verification rule, candidate selection rule or
release threshold changes. If the promoted path stops being byte-identical or materially faster, this gate goes
red and the scheduling optimization loses promotion evidence.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
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


def _thread_overlay_retained_graph(graph_path: Path, overlay_path: Path) -> dict:
    """Reconstruct the exact pre-promotion ordered-thread scheduler as the independent baseline."""
    shared = PRODUCT.C.SHARED
    source_format, _source, graph_meta, graph_records = shared.strict._read_source_records(graph_path)
    users = shared.O._record_member_lengths(graph_meta, len(graph_records))

    def audition(item):
        record_id, record = item
        return shared.G._audition_record(record_id, record, users[record_id])

    if graph_records:
        worker_count = min(PRODUCT.G04_AUDITION_MAX_WORKERS, len(graph_records))
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="cmpct-v030-g04-oracle-thread") as pool:
            outcomes = list(pool.map(audition, enumerate(graph_records)))
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
        "audition_scheduler": "bounded-ordered-thread-pool-v1",
        "delimiter_transpose": "bulk-rectangular-prefix-v1",
    }


def _promoted_overlay_retained_graph(graph_path: Path, overlay_path: Path) -> dict:
    stats = dict(PRODUCT._parallel_deferred_overlay(graph_path, overlay_path))
    if graph_path.stat().st_size >= PRODUCT.G04_PROCESS_MIN_GRAPH_BYTES:
        if stats.get("audition_scheduler") != "bounded-ordered-spawn-process-pool-v1":
            raise RuntimeError(f"frozen oracle target did not exercise promoted process scheduler: {stats!r}")
    return stats


def _run_nested(function, graph_path: Path, overlay_path: Path) -> tuple[dict, float]:
    """Execute one overlay from a worker thread to match canonical r25 nesting."""
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="cmpct-v030-g04-oracle-parent") as pool:
        stats = dict(pool.submit(function, graph_path, overlay_path).result())
    return stats, time.perf_counter() - started


def _measure_overlay(graph_path: Path, out: Path, scheduler: str, expected_tree: str) -> dict:
    function = _thread_overlay_retained_graph if scheduler == "baseline" else _promoted_overlay_retained_graph
    stats, elapsed = _run_nested(function, graph_path, out)
    verified = PRODUCT.C.SHARED.G.strong_verify(out)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{scheduler} overlay failed exact logical verification: {verified!r}")
    return {
        "scheduler": scheduler,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "overlay_s": elapsed,
        "tree_sha256": verified.get("tree_sha256"),
        "audition_workers": stats.get("audition_workers"),
        "audition_scheduler": stats.get("audition_scheduler"),
        "record_count": len(stats.get("records", [])),
        "transformed_records": sum(row.get("selected") != "none" for row in stats.get("auditions", [])),
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

    shared = PRODUCT.C.SHARED
    rows: list[dict] = []
    for target in TARGETS:
        source = corpus / target
        if not source.is_dir():
            raise RuntimeError(f"missing frozen workload {target}")
        expected_tree = shared.treehash(source)

        with tempfile.TemporaryDirectory(prefix=f"cmpct-v030-g04-oracle-{target}-", dir=work_root) as td:
            stage = Path(td)
            substrate_started = time.perf_counter()
            substrate = shared._build_shared_candidates(source, stage)
            substrate_s = time.perf_counter() - substrate_started
            graph_path = Path(substrate["graph_path"])
            if not graph_path.is_file():
                raise RuntimeError("shared substrate omitted pre-overlay graph")

            repetitions = []
            for rep, order in enumerate(ORDERS):
                results = {}
                for scheduler in order:
                    out = stage / f"overlay-{rep}-{scheduler}.cmpct"
                    results[scheduler] = _measure_overlay(graph_path, out, scheduler, expected_tree)
                baseline = results["baseline"]
                process = results["process"]
                byte_identical = (
                    baseline["archive_bytes"] == process["archive_bytes"]
                    and baseline["archive_sha256"] == process["archive_sha256"]
                    and baseline["tree_sha256"] == process["tree_sha256"]
                )
                if not byte_identical:
                    raise RuntimeError(
                        f"promoted process scheduler changed G0-G4 overlay bytes/tree for {target}: "
                        f"baseline={baseline!r} process={process!r}"
                    )
                saved = float(baseline["overlay_s"]) - float(process["overlay_s"])
                pct = saved / max(float(baseline["overlay_s"]), 1e-9) * 100.0
                repetitions.append({
                    "rep": rep,
                    "execution_order": list(order),
                    "baseline": baseline,
                    "process": process,
                    "byte_identical": True,
                    "wallclock_saved_s": saved,
                    "wallclock_improvement_pct": pct,
                })

            base_times = [float(row["baseline"]["overlay_s"]) for row in repetitions]
            proc_times = [float(row["process"]["overlay_s"]) for row in repetitions]
            baseline_median = statistics.median(base_times)
            process_median = statistics.median(proc_times)
            saved = baseline_median - process_median
            pct = saved / max(baseline_median, 1e-9) * 100.0
            rows.append({
                "workload": target,
                "substrate_build_s": substrate_s,
                "substrate_graph_bytes": graph_path.stat().st_size,
                "baseline_median_overlay_s": baseline_median,
                "process_median_overlay_s": process_median,
                "median_saved_s": saved,
                "median_improvement_pct": pct,
                "all_byte_identical": all(row["byte_identical"] for row in repetitions),
                "material_improvement": saved >= MIN_MEDIAN_SAVED_S and pct >= MIN_MEDIAN_IMPROVEMENT_PCT,
                "repetitions": repetitions,
            })

    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_byte_identical": all(row["all_byte_identical"] for row in rows),
        "all_materially_faster": all(row["material_improvement"] for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-process-pool-oracle-v2",
        "engine": "experiments/entropygraph_v030_release_product.py",
        "hypothesis": "promoted bounded process auditions beat the previous GIL-bound ordered thread scheduler",
        "measurement_boundary": "same retained pre-overlay graph; G0-G4 overlay stage only; nested worker-thread invocation",
        "contract": {
            "scheduling_only": True,
            "exact_overlay_bytes_required": True,
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
        raise SystemExit("G0-G4 process-pool scheduler oracle did not retain promotion evidence")


if __name__ == "__main__":
    main()
