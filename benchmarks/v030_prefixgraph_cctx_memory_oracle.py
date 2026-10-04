from __future__ import annotations

"""Attribute frozen-Shifted PrefixGraph RSS to live Zstd compression contexts.

Prior exact evidence eliminated retained complete candidates, top-level r24/r25 overlap,
allocator arenas, Zstd window/hash/chain tuning, and the direct payload floor as primary
owners of Shifted's ~3x product RSS regression. The remaining signature is close to
linear with the number of concurrent PrefixGraph anchor workers. This research-only
oracle asks the causal question directly: how much memory does python-zstandard report
for one raw-prefix ``ZSTD_CCtx`` after the exact level-19 anchor audition workload, and
how does that compare with fresh-process 1-worker and 4-worker PrefixGraph RSS?

No compressor parameter, candidate, archive byte, selector, reader, locality, recovery,
or production worker policy is changed. The context profiler runs anchors sequentially
and discards every trial output; shipping identity is independently ratcheted by the
existing fresh-process worker-count implementation. A signal only chooses the next
architecture target (native/context-lifetime redesign); it grants zero release credit.
"""

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_prefixgraph as BASE

ROOT = Path(__file__).resolve().parents[1]
SHIPPING_WORKER = ROOT / "benchmarks" / "v030_prefixgraph_worker_count_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 2
MIN_SINGLE_WORKER_CCTX_SHARE_FOR_SIGNAL = 0.50
MIN_WORKER_SCALING_FOR_SIGNAL = 3.0


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _profile_contexts(source: Path) -> dict:
    files = sorted(path for path in source.rglob("*") if path.is_file())
    rels = [path.relative_to(source).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if not raws:
        raise RuntimeError("PrefixGraph context profiler requires a non-empty source")
    if any(len(raw) > BASE.MAX_FILE_BYTES for raw in raws):
        raise RuntimeError("PrefixGraph context profiler source exceeds file ceiling")

    # Keep the same immutable direct floor live while measuring contexts so the process
    # shape matches the shipping anchor phase. It is deliberately not included in the
    # CCtx-owned byte count returned by python-zstandard.
    direct_payloads = [BASE._compress(raw) for raw in raws]
    anchors = BASE._anchor_indices(len(raws))
    process_baseline = _rss_kib()
    rows = []
    for anchor in anchors:
        compressor, dictionary = BASE._prefix_codec(raws[anchor])
        if not hasattr(compressor, "memory_size"):
            raise RuntimeError("python-zstandard ZstdCompressor.memory_size() is required for causal attribution")
        samples = [int(compressor.memory_size())]
        compressed_trials = 0
        for index, raw in enumerate(raws):
            if index == anchor or not raw or not raws[anchor]:
                continue
            trial = compressor.compress(raw)
            compressed_trials += 1
            samples.append(int(compressor.memory_size()))
            # Drop output immediately so candidate payload retention cannot impersonate
            # compressor working memory in this attribution experiment.
            del trial
        rows.append({
            "anchor": int(anchor),
            "anchor_raw_bytes": len(raws[anchor]),
            "compressed_trials": compressed_trials,
            "initial_cctx_bytes": samples[0],
            "peak_reported_cctx_bytes": max(samples),
            "final_reported_cctx_bytes": samples[-1],
        })
        del compressor, dictionary
        gc.collect()

    peak = _rss_kib()
    return {
        "files": len(files),
        "rels": rels,
        "logical_bytes": sum(map(len, raws)),
        "direct_payload_bytes": sum(map(len, direct_payloads)),
        "anchors": rows,
        "process_baseline_rss_kib": process_baseline,
        "process_peak_rss_kib": peak,
        "process_incremental_peak_rss_kib": peak - process_baseline,
    }


def _run_context_worker(source: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, __file__, "--worker-source", str(source)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("PrefixGraph CCtx worker emitted no JSON")
    return json.loads(lines[-1])


def _run_shipping(source: Path, archive: Path, workers: int) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [
            sys.executable,
            str(SHIPPING_WORKER),
            "--source", str(source),
            "--archive", str(archive),
            "--workers", str(workers),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"PrefixGraph shipping RSS worker emitted no JSON for {workers} workers")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]

    context_rounds = [_run_context_worker(source) for _ in range(ROUNDS)]
    shipping_rounds = []
    for round_index in range(ROUNDS):
        order = (1, 4) if round_index % 2 == 0 else (4, 1)
        measured = {}
        for workers in order:
            archive = work_root / "archives" / f"r{round_index}-w{workers}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            measured[str(workers)] = _run_shipping(source, archive, workers)
        shipping_rounds.append({"round": round_index, "order": list(order), "measurements": measured})

    identities = {
        (
            int(row["archive_bytes"]),
            str(row["archive_sha256"]),
            str(row["tree_sha256"]),
        )
        for round_row in shipping_rounds
        for row in round_row["measurements"].values()
    }
    exact_shipping_identity = len(identities) == 1

    anchor_counts = {len(row["anchors"]) for row in context_rounds}
    if len(anchor_counts) != 1 or not anchor_counts or next(iter(anchor_counts)) < 1:
        raise RuntimeError("PrefixGraph CCtx attribution changed anchor cardinality between rounds")
    per_round_max_cctx = [max(int(anchor["peak_reported_cctx_bytes"]) for anchor in row["anchors"]) for row in context_rounds]
    per_round_median_cctx = [
        float(statistics.median(int(anchor["peak_reported_cctx_bytes"]) for anchor in row["anchors"]))
        for row in context_rounds
    ]
    max_cctx_bytes = int(statistics.median(per_round_max_cctx))
    median_cctx_bytes = float(statistics.median(per_round_median_cctx))

    def median_shipping(workers: int, field: str) -> float:
        return float(statistics.median(
            float(round_row["measurements"][str(workers)][field])
            for round_row in shipping_rounds
        ))

    w1_rss_kib = median_shipping(1, "incremental_peak_rss_kib")
    w4_rss_kib = median_shipping(4, "incremental_peak_rss_kib")
    w1_wall_s = median_shipping(1, "wall_s")
    w4_wall_s = median_shipping(4, "wall_s")
    cctx_share_w1 = max_cctx_bytes / max(1.0, w1_rss_kib * 1024.0)
    worker_rss_scaling = w4_rss_kib / max(1.0, w1_rss_kib)
    four_cctx_to_w4 = (4.0 * max_cctx_bytes) / max(1.0, w4_rss_kib * 1024.0)
    causal_signal = (
        exact_shipping_identity
        and cctx_share_w1 >= MIN_SINGLE_WORKER_CCTX_SHARE_FOR_SIGNAL
        and worker_rss_scaling >= MIN_WORKER_SCALING_FOR_SIGNAL
    )

    return {
        "schema": "cmpct-v030-prefixgraph-cctx-memory-attribution-v1",
        "source_commit": _source_commit(),
        "target": list(TARGET),
        "rounds": ROUNDS,
        "context_rounds": context_rounds,
        "shipping_rounds": shipping_rounds,
        "summary": {
            "anchors": next(iter(anchor_counts)),
            "max_reported_single_cctx_bytes": max_cctx_bytes,
            "median_reported_single_cctx_bytes": median_cctx_bytes,
            "shipping_w1_incremental_peak_rss_kib": w1_rss_kib,
            "shipping_w4_incremental_peak_rss_kib": w4_rss_kib,
            "shipping_w1_wall_s": w1_wall_s,
            "shipping_w4_wall_s": w4_wall_s,
            "max_cctx_share_of_w1_incremental_rss": cctx_share_w1,
            "w4_to_w1_rss_scaling": worker_rss_scaling,
            "four_max_cctx_to_w4_incremental_rss": four_cctx_to_w4,
        },
        "contract": {
            "production_change": False,
            "compressor_parameters_changed": False,
            "candidate_set_changed": False,
            "anchor_nomination_changed": False,
            "serializer_changed": False,
            "tie_law_changed": False,
            "reader_changed": False,
            "recovery_changed": False,
            "locality_changed": False,
            "shipping_archive_identity_required": True,
            "minimum_single_worker_cctx_share_for_signal": MIN_SINGLE_WORKER_CCTX_SHARE_FOR_SIGNAL,
            "minimum_worker_rss_scaling_for_signal": MIN_WORKER_SCALING_FOR_SIGNAL,
            "release_credit": False,
        },
        "gate": {
            "exact_shipping_identity": exact_shipping_identity,
            "causal_signal": bool(causal_signal),
            "passed": bool(exact_shipping_identity),
        },
        "release_credit": False,
        "claim_boundary": (
            "Research-only memory attribution. A causal signal says the next Shifted RSS work should redesign "
            "live Zstd CCtx/context lifetime (potentially native) rather than revisit retained candidate bytes, "
            "allocator arenas, or top-level scheduling. It cannot change shipping policy or release authority."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-cctx-memory-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-cctx-memory.json"))
    parser.add_argument("--worker-source", type=Path)
    args = parser.parse_args()
    if args.worker_source is not None:
        print(json.dumps(_profile_contexts(args.worker_source), sort_keys=True), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("PrefixGraph CCtx attribution changed shipping archive identity")


if __name__ == "__main__":
    main()
