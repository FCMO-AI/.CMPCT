from __future__ import annotations

"""Research-only profiler for the remaining C25EG08 Office graph-build wall.

Exact single-expansion evidence leaves the Office candidate at 5,951,527 bytes with creation still slower than ZIP.
The coarse ``graph_s`` bucket is now large enough that further blind verifier/publication cleanup is low leverage, but
that bucket contains several very different operations.  This oracle profiles the exact existing RAM-backed EG07
semantic-stage builder without changing its bytes or policy and records function-level cumulative/self CPU time.

Profiler overhead receives no performance credit.  Unprofiled repetitions provide the ordinary wall-time reference;
one isolated cProfile pass exists only to rank hot functions.  The raw finalized EG07 bytes must be deterministic
across all passes.  This is diagnostic evidence only and cannot authorize selector/native/Android/release promotion.
"""

import argparse
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DV5

ROUNDS = 7
TOP = 40


def _stat_rows(profiler: cProfile.Profile) -> list[dict]:
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, lineno, funcname), (cc, nc, tt, ct, _callers) in stats.stats.items():
        rows.append(
            {
                "file": filename,
                "line": int(lineno),
                "function": funcname,
                "primitive_calls": int(cc),
                "total_calls": int(nc),
                "self_cpu_s": float(tt),
                "cumulative_cpu_s": float(ct),
            }
        )
    rows.sort(key=lambda row: (-row["cumulative_cpu_s"], -row["self_cpu_s"], row["file"], row["line"]))
    return rows[:TOP]


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root / "frozen")

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-hotpath-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        # Bind the normalized corpus while the temporary stage still exists.  Computing this after leaving
        # TemporaryDirectory turns an evidence field into a harness crash because the directory has been removed.
        normalized_tree_sha256 = V1.EG07._treehash(stage)
        times = []
        digests = set()
        sizes = set()
        for index in range(ROUNDS):
            started = time.perf_counter()
            raw, inner = DV5._tmpfs_capture_raw_final_eg07(stage, root / f"baseline-{index}")
            elapsed = time.perf_counter() - started
            times.append(float(elapsed))
            # The function-reported interval should cover essentially the same semantic-stage work. Preserve both.
            if inner <= 0 or inner > elapsed + 0.050:
                raise RuntimeError("EG07 graph timing boundary drifted unexpectedly")
            digests.add(hashlib.sha256(raw).hexdigest())
            sizes.add(len(raw))

        profiler = cProfile.Profile()
        started = time.perf_counter()
        profiler.enable()
        profiled_raw, profiled_inner = DV5._tmpfs_capture_raw_final_eg07(stage, root / "profiled")
        profiler.disable()
        profiled_wall = time.perf_counter() - started
        profiled_sha = hashlib.sha256(profiled_raw).hexdigest()
        if len(digests) != 1 or len(sizes) != 1 or profiled_sha not in digests or len(profiled_raw) not in sizes:
            raise RuntimeError("profiling changed or exposed nondeterministic finalized EG07 bytes")

    rows = _stat_rows(profiler)
    if not rows:
        raise RuntimeError("cProfile produced no function statistics")
    median_wall = statistics.median(times)
    return {
        "schema": "cmpct-v030-eg08-graph-hotpath-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "profiled_timing_receives_speed_credit": False,
            "profiled_region": "DV5._tmpfs_capture_raw_final_eg07 exact existing semantic-stage path",
            "benchmark_identity_not_policy_input": True,
        },
        "office": {
            "accepted_v029_bytes": int(accepted_v029),
            "normalized_tree_sha256": normalized_tree_sha256,
        },
        "unprofiled": {
            "rounds": ROUNDS,
            "raw_wall_s": times,
            "median_wall_s": float(median_wall),
            "finalized_eg07_bytes": next(iter(sizes)),
            "finalized_eg07_sha256": next(iter(digests)),
        },
        "profiled": {
            "wall_s": float(profiled_wall),
            "inner_reported_s": float(profiled_inner),
            "finalized_eg07_sha256": profiled_sha,
            "top_by_cumulative_cpu": rows,
        },
        "gate": {
            "experiment_valid": len(digests) == 1 and len(sizes) == 1 and profiled_sha in digests and bool(rows),
            "passed": len(digests) == 1 and len(sizes) == 1 and profiled_sha in digests and bool(rows),
        },
        "claim_boundary": (
            "Diagnostic hot-path attribution only. cProfile overhead is explicitly excluded from speed claims. Any "
            "optimization suggested by this receipt must preserve exact candidate bytes and then pass ordinary "
            "complete-create, all-15, native/Android, recovery/locality and strict release authority."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-graph-hotpath-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-graph-hotpath.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"unprofiled": result["unprofiled"], "top": result["profiled"]["top_by_cumulative_cpu"][:12], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("EG08 graph hot-path oracle invalid")


if __name__ == "__main__":
    main()
