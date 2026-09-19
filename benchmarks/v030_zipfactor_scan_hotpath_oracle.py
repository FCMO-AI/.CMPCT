from __future__ import annotations

"""Research-only function-level profiler for ZIP-factor's dominant source-scan phase.

The exact 21-round build-phase receipt attributes about 80% of the 14,033-byte candidate builder to FUSED._scan.
That bucket still mixes directory traversal, stat/xattr metadata capture, path policy, source reads, SHA-256, ZIP
parsing/signature checks and manifest serialization. This oracle profiles only the existing _scan implementation,
without changing bytes or policy, so the next sub-millisecond optimization targets a measured owner.

Profiler time has zero performance/release credit. Ordinary unprofiled repetitions establish the wall reference;
the profiled result must emit byte-identical manifest/items and the final builder must still reproduce the exact
14,033-byte archive/SHA ratchet.
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

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as BUILD

ROUNDS = 31
TOP = 50
EXPECTED_BYTES = 14033
EXPECTED_SHA = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"


def _fingerprint(result) -> str:
    manifest, items, stats = result
    h = hashlib.sha256(manifest)
    for rel, parsed in items:
        h.update(rel.encode("utf-8")); h.update(repr(parsed).encode("utf-8"))
    h.update(json.dumps(stats, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def _rows(profiler: cProfile.Profile) -> list[dict]:
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, lineno, function), (cc, nc, tt, ct, _callers) in stats.stats.items():
        rows.append({
            "file": filename, "line": int(lineno), "function": function,
            "primitive_calls": int(cc), "total_calls": int(nc),
            "self_cpu_s": float(tt), "cumulative_cpu_s": float(ct),
        })
    rows.sort(key=lambda r: (-r["cumulative_cpu_s"], -r["self_cpu_s"], r["file"], r["line"]))
    return rows[:TOP]


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    corpus = work_root / "corpus"; CORPUS.build(corpus); source = corpus / "04_deflate_family"
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-scan-hotpath-", dir=work_root) as td_raw:
        stage = EXT._normalized_stage(source, Path(td_raw))
        baseline = FUSED._scan(stage); fp = _fingerprint(baseline)
        times = []
        for _ in range(ROUNDS):
            t0 = time.perf_counter_ns(); result = FUSED._scan(stage); elapsed = time.perf_counter_ns() - t0
            if _fingerprint(result) != fp: raise RuntimeError("ZIP-factor scan became nondeterministic")
            times.append(elapsed / 1e9)
        profiler = cProfile.Profile(); profiler.enable(); profiled = FUSED._scan(stage); profiler.disable()
        if _fingerprint(profiled) != fp: raise RuntimeError("profiling changed ZIP-factor scan result")
        archive, _stats = BUILD.build_bytes(stage, level=3, group_size=7)
    archive_sha = hashlib.sha256(archive).hexdigest()
    rows = _rows(profiler)
    valid = len(times) == ROUNDS and bool(rows) and len(archive) == EXPECTED_BYTES and archive_sha == EXPECTED_SHA
    return {
        "schema": "cmpct-v030-zipfactor-scan-hotpath-oracle-v1",
        "contract": {"release_credit": False, "production_change": False, "profiled_timing_receives_speed_credit": False, "rounds": ROUNDS},
        "candidate": {"archive_bytes": len(archive), "archive_sha256": archive_sha},
        "unprofiled": {"median_scan_s": float(statistics.median(times)), "raw_scan_s": times, "scan_fingerprint": fp},
        "profiled": {"top_by_cumulative_cpu": rows},
        "gate": {"experiment_valid": valid, "passed": valid},
        "claim_boundary": "Diagnostic attribution only. Any optimization must preserve exact archive bytes and pass complete four-way/recovery/native/Android/final authority.",
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-scan-hotpath-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-scan-hotpath.json")); a=p.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"unprofiled": result["unprofiled"], "top": result["profiled"]["top_by_cumulative_cpu"][:15], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]: raise SystemExit("ZIP-factor scan hot-path oracle invalid")


if __name__ == "__main__": main()
