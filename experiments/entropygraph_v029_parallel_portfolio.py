"""Byte-identical parallel scheduler oracle for the accepted v0.29 Mosaic portfolio.

The accepted attempt-5 portfolio currently pays a large wall-clock penalty because it builds the complete
v0.28 fallback and the complete Residual Program Packing candidate serially, even though neither build
depends on the other for multi-file trees. This oracle changes *scheduling only*: both inherited builders
run in separate spawned Python processes, then the exact same smaller-artifact selection rule is applied.

The experiment is intentionally conservative. A result is admissible only when the selected archive
SHA-256 exactly matches ``entropygraph_v029_residual_fast.build``. No encoder threshold, record order,
codec setting, metadata byte, format field, residual-pack rule, Mosaic rule, or fallback rule may change.

Timing uses balanced ABBA ordering across four paired repetitions. This matters because always running
sequential first can warm filesystem/page-cache state for the parallel run and manufacture an apparent
speedup. ABBA gives each implementation two first-position and two second-position measurements while
retaining the same frozen >=20% and >=5 s per-pair and median gates.

Footnote: an earlier scheduler prototype accidentally targeted the obsolete attempt-1 ``CMPNX9`` engine.
Its timing result was real for that old portfolio but was not evidence for the accepted attempt-5
``CMPNX11`` mechanism. This module therefore imports the accepted Residual Program Packing wrapper
explicitly and records that engine identity in every evidence row so stale-engine drift fails loudly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import queue as queue_module
import statistics
import sys
import tempfile
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments import entropygraph_v029_residual_fast as accepted

MIN_WALLCLOCK_IMPROVEMENT_PCT = 20.0
MIN_ABSOLUTE_IMPROVEMENT_S = 5.0
BALANCED_ORDER = ("sequential-first", "parallel-first", "parallel-first", "sequential-first")
ACCEPTED_ENGINE = "attempt5-residual-program-packing"
CHILD_RESULT_TIMEOUT_S = 30 * 60


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024, ), b""):
            h.update(block)
    return h.hexdigest()


def _durable_replace(source: Path, destination: Path) -> str:
    """Publish ``source`` without recopying payload bytes and harden the rename against crashes.

    ``os.replace`` makes publication atomic but atomicity alone is not a durability guarantee: after a
    power loss, dirty file data or the renamed directory entry may not have reached stable storage. Flush
    the completed candidate first, perform the same-filesystem rename, then fsync the destination directory
    where the platform supports directory descriptors. The directory sync is intentionally capability-
    detected because Windows does not expose POSIX directory fsync through this interface.
    """
    with source.open("rb") as candidate:
        os.fsync(candidate.fileno())
    os.replace(source, destination)

    if os.name != "posix":
        return "atomic-file-fsynced"

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        directory_fd = os.open(destination.parent, flags)
    except OSError:
        return "atomic-file-fsynced-directory-sync-unavailable"
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return "atomic-file-and-directory-fsynced"


def _worker(kind: str, root_s: str, out_s: str, queue) -> None:
    root = Path(root_s)
    out = Path(out_s)
    started = time.perf_counter()
    try:
        if kind == "v028":
            stats = accepted.V028.build(root, out)
        elif kind == "attempt5":
            # Footnote: ``build_graph`` is the accepted attempt-5 CMPNX11 candidate without the outer
            # v0.28 tournament. It is independent of the v0.28 build, which is precisely what makes
            # parallel scheduling legal without changing a single candidate byte.
            stats = accepted.build_graph(root, out)
        else:
            raise ValueError(kind)
        queue.put({"kind": kind, "ok": True, "elapsed_s": time.perf_counter() - started, "stats": stats})
    except BaseException as exc:  # child must return a durable error rather than silently disappear
        queue.put({"kind": kind, "ok": False, "elapsed_s": time.perf_counter() - started, "error": repr(exc)})


def _single_file_compatible_build(root: Path, out: Path) -> dict:
    """Preserve the accepted scheduler's single-file fast-reject policy exactly.

    The fast reject needs the completed v0.28 selection before it knows whether the research graph may be
    skipped. Starting the graph speculatively would re-introduce the exact 22.8x dead-end cost that the
    accepted optimization removed. Single-file trees therefore keep the accepted sequential policy;
    parallelism is a multi-file portfolio optimization only.
    """
    started = time.perf_counter()
    stats = accepted.build(root, out)
    elapsed = time.perf_counter() - started
    return {
        "selected": stats["selected"],
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "parallel_create_s": elapsed,
        "v028_child_s": float(stats.get("v028", {}).get("create_s", elapsed)),
        "attempt5_child_s": float(stats.get("mosaic", {}).get("create_s", 0.0)),
        "v028_bytes": int(stats["v028_bytes"]),
        "attempt5_graph_bytes": int(stats["mosaic_graph_bytes"]),
        "scheduler_mode": "single-file-accepted-policy",
        "accepted_engine": ACCEPTED_ENGINE,
        "fast_reject_reason": stats.get("fast_reject_reason"),
    }


def build_parallel(root: Path, out: Path) -> dict:
    if accepted._logical_file_count(root) <= 1:
        return _single_file_compatible_build(root, out)

    started = time.perf_counter()
    ctx = mp.get_context("spawn")
    # Keep candidates beside the requested output so winner publication can be a same-filesystem atomic
    # rename instead of an archive-sized payload copy. Candidate bytes and selection semantics are unchanged.
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-mosaic-parallel-", dir=out.parent) as td:
        td_path = Path(td)
        v028_path = td_path / "v028.cmpct"
        attempt5_path = td_path / "attempt5.cmpct"
        queue = ctx.Queue()
        processes = [
            ctx.Process(target=_worker, args=("v028", str(root), str(v028_path), queue)),
            ctx.Process(target=_worker, args=("attempt5", str(root), str(attempt5_path), queue)),
        ]
        for process in processes:
            process.start()

        results = []
        try:
            for _ in processes:
                results.append(queue.get(timeout=CHILD_RESULT_TIMEOUT_S))
        except queue_module.Empty as exc:
            for process in processes:
                if process.is_alive():
                    process.terminate()
            raise RuntimeError("parallel portfolio child failed to report before timeout") from exc
        finally:
            for process in processes:
                process.join(timeout=30)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)

        failures = [result for result in results if not result.get("ok")]
        if failures or any(process.exitcode != 0 for process in processes):
            raise RuntimeError(
                f"parallel portfolio child failure: results={results!r}, "
                f"exitcodes={[p.exitcode for p in processes]!r}"
            )

        # Snapshot both sizes before publication. ``os.replace`` intentionally removes the winner's old
        # temporary path, so post-publication metadata must never stat that path.
        v028_bytes = v028_path.stat().st_size
        attempt5_bytes = attempt5_path.stat().st_size
        if attempt5_bytes < v028_bytes:
            chosen = attempt5_path
            selected = "mosaic"
        else:
            chosen = v028_path
            selected = "v028-fallback"
        durability = _durable_replace(chosen, out)
        by_kind = {result["kind"]: result for result in results}
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "archive_sha256": _sha256(out),
            "parallel_create_s": time.perf_counter() - started,
            "v028_child_s": by_kind["v028"]["elapsed_s"],
            "attempt5_child_s": by_kind["attempt5"]["elapsed_s"],
            "v028_bytes": v028_bytes,
            "attempt5_graph_bytes": attempt5_bytes,
            "scheduler_mode": "parallel-independent-portfolio",
            "selection_materialization": "same-filesystem-atomic-move",
            "selection_extra_payload_write_bytes": 0,
            "selection_durability": durability,
            "accepted_engine": ACCEPTED_ENGINE,
            "fast_reject_reason": None,
        }


def _build_sequential(root: Path, out: Path) -> tuple[dict, float]:
    started = time.perf_counter()
    stats = accepted.build(root, out)
    return stats, time.perf_counter() - started


def _pair_passes(sequential_s: float, parallel_s: float) -> bool:
    saved = sequential_s - parallel_s
    pct = saved / max(sequential_s, 1e-9) * 100.0
    return saved >= MIN_ABSOLUTE_IMPROVEMENT_S and pct >= MIN_WALLCLOCK_IMPROVEMENT_PCT


def measure(root: Path, work_root: Path, repetitions: int = 4) -> dict:
    if repetitions != len(BALANCED_ORDER):
        raise ValueError(
            f"balanced timing requires exactly {len(BALANCED_ORDER)} repetitions; got {repetitions}"
        )

    work_root.mkdir(parents=True, exist_ok=True)
    sequential_times: list[float] = []
    parallel_times: list[float] = []
    exact_rows: list[dict] = []

    for rep, execution_order in enumerate(BALANCED_ORDER):
        seq = work_root / f"sequential-{rep}.cmpct"
        par = work_root / f"parallel-{rep}.cmpct"

        if execution_order == "sequential-first":
            seq_stats, seq_elapsed = _build_sequential(root, seq)
            par_stats = build_parallel(root, par)
        elif execution_order == "parallel-first":
            par_stats = build_parallel(root, par)
            seq_stats, seq_elapsed = _build_sequential(root, seq)
        else:  # pragma: no cover - BALANCED_ORDER is constant and validated above
            raise AssertionError(execution_order)

        seq_sha = _sha256(seq)
        exact = seq.read_bytes() == par.read_bytes()
        if not exact or seq_sha != par_stats["archive_sha256"]:
            raise RuntimeError("parallel scheduler changed accepted attempt-5 selected archive bytes")
        if par_stats["accepted_engine"] != ACCEPTED_ENGINE:
            raise RuntimeError("parallel scheduler drifted away from the accepted attempt-5 engine")

        sequential_times.append(seq_elapsed)
        parallel_times.append(par_stats["parallel_create_s"])
        saved = seq_elapsed - par_stats["parallel_create_s"]
        improvement_pct = saved / max(seq_elapsed, 1e-9) * 100.0
        exact_rows.append(
            {
                "rep": rep,
                "execution_order": execution_order,
                "accepted_engine": ACCEPTED_ENGINE,
                "scheduler_mode": par_stats["scheduler_mode"],
                "selected": seq_stats["selected"],
                "archive_bytes": seq.stat().st_size,
                "archive_sha256": seq_sha,
                "v028_bytes": int(seq_stats["v028_bytes"]),
                "attempt5_graph_bytes": int(seq_stats["mosaic_graph_bytes"]),
                "sequential_s": seq_elapsed,
                "parallel_s": par_stats["parallel_create_s"],
                "wallclock_saved_s": saved,
                "wallclock_improvement_pct": improvement_pct,
                "v028_child_s": par_stats["v028_child_s"],
                "attempt5_child_s": par_stats["attempt5_child_s"],
                "byte_identical": exact,
                "pair_gate_pass": _pair_passes(seq_elapsed, par_stats["parallel_create_s"]),
            }
        )

    seq_median = statistics.median(sequential_times)
    par_median = statistics.median(parallel_times)
    saving = seq_median - par_median
    improvement_pct = saving / max(seq_median, 1e-9) * 100.0
    median_gate = (
        saving >= MIN_ABSOLUTE_IMPROVEMENT_S
        and improvement_pct >= MIN_WALLCLOCK_IMPROVEMENT_PCT
    )

    return {
        "schema": "cmpct-v029-parallel-portfolio-oracle-v3",
        "accepted_engine": ACCEPTED_ENGINE,
        "policy": {
            "scheduling_only": True,
            "spawned_workers": 2,
            "parallel_scope": "multi-file-only",
            "single_file_policy": "preserve-accepted-fast-reject-sequentially",
            "exact_archive_identity_required": True,
            "minimum_wallclock_improvement_pct": MIN_WALLCLOCK_IMPROVEMENT_PCT,
            "minimum_absolute_improvement_s": MIN_ABSOLUTE_IMPROVEMENT_S,
            "repetitions": repetitions,
            "paired_order": list(BALANCED_ORDER),
            "every_pair_must_pass": True,
            "median_must_pass": True,
        },
        "rows": exact_rows,
        "sequential_median_s": seq_median,
        "parallel_median_s": par_median,
        "wallclock_saved_s": saving,
        "wallclock_improvement_pct": improvement_pct,
        "median_gate_pass": median_gate,
        "research_gate_pass": (
            median_gate
            and all(row["accepted_engine"] == ACCEPTED_ENGINE for row in exact_rows)
            and all(row["byte_identical"] for row in exact_rows)
            and all(row["pair_gate_pass"] for row in exact_rows)
        ),
    }


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=4)
    args = parser.parse_args()
    result = measure(args.root, args.work_root, args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
