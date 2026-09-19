from __future__ import annotations

"""Exact-byte phase oracle for the remaining ZIP-factor recovery build budget.

The recovery memory-FFI frontier is already only ~0.2 ms behind ZIP on the frozen
Deflate-family workload.  This oracle does not change the builder.  It instruments the
existing fused V3 semantic path in place so the next optimization is aimed at a measured
owner rather than guessed at micro-costs.

Only two existing calls are wrapped: FUSED._scan and V3._pack_group.  Their results flow
unchanged into the existing build_bytes implementation.  The residual bucket therefore
contains template serialization, SHA/control construction, Zstd compression, payload
assembly and Python bookkeeping.  Exact output bytes are ratcheted against an unwrapped
reference every round.  Research-only; no release credit.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as BUILD
from experiments import entropygraph_v030_zipfactor_fused as FUSED

ROUNDS = 21
LEVEL = 3
GROUP_SIZE = 7


def _median(xs: list[float]) -> float:
    return float(statistics.median(xs))


@contextmanager
def _phase_timers(bucket: dict[str, float]):
    scan = FUSED._scan
    pack = V3._pack_group

    def timed_scan(root: Path):
        t0 = time.perf_counter_ns()
        result = scan(root)
        bucket["scan_ns"] += time.perf_counter_ns() - t0
        return result

    def timed_pack(group):
        t0 = time.perf_counter_ns()
        result = pack(group)
        bucket["pack_group_ns"] += time.perf_counter_ns() - t0
        return result

    FUSED._scan = timed_scan
    V3._pack_group = timed_pack
    try:
        yield
    finally:
        V3._pack_group = pack
        FUSED._scan = scan


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-build-phase-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        reference, ref_stats = BUILD.build_bytes(stage, level=LEVEL, group_size=GROUP_SIZE)
        reference_sha = hashlib.sha256(reference).hexdigest()

        total_s: list[float] = []
        scan_s: list[float] = []
        pack_s: list[float] = []
        residual_s: list[float] = []
        for _ in range(ROUNDS):
            bucket = {"scan_ns": 0.0, "pack_group_ns": 0.0}
            t0 = time.perf_counter_ns()
            with _phase_timers(bucket):
                raw, stats = BUILD.build_bytes(stage, level=LEVEL, group_size=GROUP_SIZE)
            elapsed_ns = time.perf_counter_ns() - t0
            if raw != reference or stats != ref_stats:
                raise RuntimeError("phase instrumentation changed exact ZIP-factor build result")
            scan_ns = int(bucket["scan_ns"])
            pack_ns = int(bucket["pack_group_ns"])
            residual_ns = elapsed_ns - scan_ns - pack_ns
            if residual_ns < 0:
                raise RuntimeError("invalid phase accounting")
            total_s.append(elapsed_ns / 1e9)
            scan_s.append(scan_ns / 1e9)
            pack_s.append(pack_ns / 1e9)
            residual_s.append(residual_ns / 1e9)

        med_total = _median(total_s)
        med_scan = _median(scan_s)
        med_pack = _median(pack_s)
        med_residual = _median(residual_s)
        return {
            "schema": "cmpct-v030-zipfactor-build-phase-oracle-v1",
            "contract": {
                "rounds": ROUNDS,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "builder_changed": False,
                "archive_bytes_changed": False,
                "exact_output_identity_each_round": True,
                "timers_use_perf_counter_ns": True,
                "selector_change": False,
                "release_credit": False,
            },
            "candidate": {
                "archive_bytes": len(reference),
                "archive_sha256": reference_sha,
                "stats": ref_stats,
            },
            "medians_s": {
                "total_build_bytes": med_total,
                "scan": med_scan,
                "pack_groups": med_pack,
                "residual_finalize_compress_control": med_residual,
            },
            "median_share": {
                "scan": med_scan / med_total,
                "pack_groups": med_pack / med_total,
                "residual_finalize_compress_control": med_residual / med_total,
            },
            "samples_s": {
                "total_build_bytes": total_s,
                "scan": scan_s,
                "pack_groups": pack_s,
                "residual_finalize_compress_control": residual_s,
            },
            "experiment_valid": (
                len(total_s) == len(scan_s) == len(pack_s) == len(residual_s) == ROUNDS
                and len(reference) == 14033
                and reference_sha == "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"
            ),
            "promotion_signal": False,
            "release_credit": False,
        }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor build phase oracle invalid")


if __name__ == "__main__":
    main()
