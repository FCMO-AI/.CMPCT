"""Byte-identical parallel scheduler oracle for the v0.29 Mosaic portfolio.

The accepted research portfolio currently pays a large wall-clock penalty because it builds the complete
v0.28 fallback and the complete Mosaic candidate serially, even though neither build depends on the
other.  This oracle changes *scheduling only*: both inherited builders run in separate spawned Python
processes, then the exact same smaller-artifact selection rule is applied.

The experiment is intentionally conservative.  A result is admissible only when the selected archive
SHA-256 exactly matches the existing sequential portfolio output.  No encoder threshold, record order,
codec setting, metadata byte, format field, or fallback rule may change.  The purpose is to test whether
we can buy wall-clock creation speed without spending archive bytes, locality, integrity, or reader
complexity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from experiments import entropygraph_v029_mosaic as mosaic


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _worker(kind: str, root_s: str, out_s: str, queue) -> None:
    root = Path(root_s)
    out = Path(out_s)
    started = time.perf_counter()
    try:
        if kind == "v028":
            stats = mosaic.V028.build(root, out)
        elif kind == "mosaic":
            stats = mosaic._build_mosaic_graph(root, out)
        else:
            raise ValueError(kind)
        queue.put({"kind": kind, "ok": True, "elapsed_s": time.perf_counter() - started, "stats": stats})
    except BaseException as exc:  # child must return a durable error rather than silently disappear
        queue.put({"kind": kind, "ok": False, "elapsed_s": time.perf_counter() - started, "error": repr(exc)})


def build_parallel(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    ctx = mp.get_context("spawn")
    with tempfile.TemporaryDirectory(prefix="cmpct-mosaic-parallel-") as td:
        td_path = Path(td)
        v028_path = td_path / "v028.cmpct"
        mosaic_path = td_path / "mosaic.cmpct"
        queue = ctx.Queue()
        processes = [
            ctx.Process(target=_worker, args=("v028", str(root), str(v028_path), queue)),
            ctx.Process(target=_worker, args=("mosaic", str(root), str(mosaic_path), queue)),
        ]
        for process in processes:
            process.start()
        results = [queue.get() for _ in processes]
        for process in processes:
            process.join()
        failures = [result for result in results if not result.get("ok")]
        if failures or any(process.exitcode != 0 for process in processes):
            raise RuntimeError(f"parallel portfolio child failure: results={results!r}, exitcodes={[p.exitcode for p in processes]!r}")

        if mosaic_path.stat().st_size < v028_path.stat().st_size:
            chosen = mosaic_path
            selected = "mosaic"
        else:
            chosen = v028_path
            selected = "v028-fallback"
        shutil.copyfile(chosen, out)
        by_kind = {result["kind"]: result for result in results}
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "archive_sha256": _sha256(out),
            "parallel_create_s": time.perf_counter() - started,
            "v028_child_s": by_kind["v028"]["elapsed_s"],
            "mosaic_child_s": by_kind["mosaic"]["elapsed_s"],
            "v028_bytes": v028_path.stat().st_size,
            "mosaic_graph_bytes": mosaic_path.stat().st_size,
        }


def measure(root: Path, work_root: Path, repetitions: int = 2) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    sequential_times = []
    parallel_times = []
    exact_rows = []
    for rep in range(repetitions):
        seq = work_root / f"sequential-{rep}.cmpct"
        par = work_root / f"parallel-{rep}.cmpct"
        t0 = time.perf_counter()
        seq_stats = mosaic.build(root, seq)
        seq_elapsed = time.perf_counter() - t0
        par_stats = build_parallel(root, par)
        seq_sha = _sha256(seq)
        exact = seq.read_bytes() == par.read_bytes()
        if not exact or seq_sha != par_stats["archive_sha256"]:
            raise RuntimeError("parallel scheduler changed selected archive bytes")
        sequential_times.append(seq_elapsed)
        parallel_times.append(par_stats["parallel_create_s"])
        exact_rows.append({
            "rep": rep,
            "selected": seq_stats["selected"],
            "archive_bytes": seq.stat().st_size,
            "archive_sha256": seq_sha,
            "sequential_s": seq_elapsed,
            "parallel_s": par_stats["parallel_create_s"],
            "v028_child_s": par_stats["v028_child_s"],
            "mosaic_child_s": par_stats["mosaic_child_s"],
            "byte_identical": exact,
        })
    seq_median = statistics.median(sequential_times)
    par_median = statistics.median(parallel_times)
    saving = seq_median - par_median
    return {
        "schema": "cmpct-v029-parallel-portfolio-oracle-v1",
        "policy": {
            "scheduling_only": True,
            "spawned_workers": 2,
            "exact_archive_identity_required": True,
            "minimum_wallclock_improvement_pct": 20.0,
            "minimum_absolute_improvement_s": 5.0,
            "repetitions": repetitions,
        },
        "rows": exact_rows,
        "sequential_median_s": seq_median,
        "parallel_median_s": par_median,
        "wallclock_saved_s": saving,
        "wallclock_improvement_pct": saving / max(seq_median, 1e-9) * 100.0,
        "research_gate_pass": (
            saving >= 5.0
            and saving / max(seq_median, 1e-9) >= 0.20
            and all(row["byte_identical"] for row in exact_rows)
        ),
    }


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=2)
    args = parser.parse_args()
    result = measure(args.root, args.work_root, args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
