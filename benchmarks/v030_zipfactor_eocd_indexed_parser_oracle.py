from __future__ import annotations

"""Exact A/B for the product-side EOCD-indexed ZIP-factor parser.

The exact scan profiler shows ZIP parsing dominates the remaining source-scan cost. The first byte-neutral parser
A/B (precompiled Structs + startswith guards) preserved exact semantics but saved only ~16 us median, far below
its 100 us materiality bar. This follow-up measures the product-side EOCD-first implementation: locate and validate
EOCD, walk the declared central directory once, and validate each owning local header directly from the central
local-offset. The returned structure must remain equality-identical to the mature parser.

The measurement itself has zero release credit. It is valid only if the parsed object, fused-scan fingerprint, and
exact 14,033-byte candidate/SHA remain unchanged across alternating timing rounds. Parser selection is injected
through the fused scanner's explicit differential-test seam; no process-global parser mutation is permitted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as BUILD
from experiments import entropygraph_v030_zipfactor_eocd_parser as PRODUCT_PARSER
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_profile as BASE

ROUNDS = 61
MIN_MEDIAN_SAVING_S = 0.00010
EXPECTED_BYTES = 14033
EXPECTED_SHA = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"
_candidate_parse_zip = PRODUCT_PARSER.parse_zip


def _fingerprint(result) -> str:
    manifest, items, stats = result
    h = hashlib.sha256(manifest)
    for rel, parsed in items:
        h.update(rel.encode("utf-8"))
        h.update(repr(parsed).encode("utf-8"))
    h.update(json.dumps(stats, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-eocd-parser-", dir=work_root) as td_raw:
        stage = EXT._normalized_stage(source, Path(td_raw))
        baseline_parse = BASE._parse_zip
        baseline_result = FUSED._scan(stage, parse_zip=baseline_parse)
        baseline_fp = _fingerprint(baseline_result)
        candidate_result = FUSED._scan(stage, parse_zip=_candidate_parse_zip)
        candidate_fp = _fingerprint(candidate_result)
        if candidate_result != baseline_result or candidate_fp != baseline_fp:
            raise RuntimeError("EOCD-indexed ZIP parser changed fused scan semantics")

        baseline_times: list[float] = []
        candidate_times: list[float] = []
        raw_rows = []
        for rep in range(ROUNDS):
            order = ("baseline", "candidate") if rep % 2 == 0 else ("candidate", "baseline")
            row = {}
            for kind in order:
                parser = baseline_parse if kind == "baseline" else _candidate_parse_zip
                t0 = time.perf_counter_ns()
                result = FUSED._scan(stage, parse_zip=parser)
                elapsed = (time.perf_counter_ns() - t0) / 1e9
                if _fingerprint(result) != baseline_fp:
                    raise RuntimeError(f"{kind} scan fingerprint drifted on repetition {rep}")
                row[kind] = elapsed
            baseline_times.append(row["baseline"])
            candidate_times.append(row["candidate"])
            raw_rows.append(row)
        archive, _stats = BUILD.build_bytes(stage, level=3, group_size=7)

    archive_sha = hashlib.sha256(archive).hexdigest()
    base_med = statistics.median(baseline_times)
    cand_med = statistics.median(candidate_times)
    saving = base_med - cand_med
    exact = len(archive) == EXPECTED_BYTES and archive_sha == EXPECTED_SHA
    faster = saving >= MIN_MEDIAN_SAVING_S and cand_med < base_med
    valid = exact and candidate_fp == baseline_fp and len(baseline_times) == ROUNDS and len(candidate_times) == ROUNDS
    return {
        "schema": "cmpct-v030-zipfactor-eocd-indexed-parser-oracle-v3",
        "contract": {
            "release_credit": False,
            "production_parser_module": "experiments.entropygraph_v030_zipfactor_eocd_parser",
            "production_selection_change": False,
            "process_global_mutation": False,
            "required_archive_bytes": EXPECTED_BYTES,
            "required_archive_sha256": EXPECTED_SHA,
            "minimum_median_saving_s": MIN_MEDIAN_SAVING_S,
            "candidate_change": "product-side EOCD-first central index + direct local-offset validation; identical parsed object",
        },
        "candidate": {
            "archive_bytes": len(archive),
            "archive_sha256": archive_sha,
            "scan_fingerprint": candidate_fp,
        },
        "timing": {
            "rounds": ROUNDS,
            "baseline_median_scan_s": float(base_med),
            "candidate_median_scan_s": float(cand_med),
            "median_saving_s": float(saving),
            "candidate_over_baseline_ratio": float(cand_med / base_med if base_med else 1.0),
            "raw": raw_rows,
        },
        "gate": {"experiment_valid": valid, "materially_faster": faster, "passed": valid},
        "claim_boundary": (
            "Product-side parser implementation under exact research A/B. The fused builder now uses the candidate "
            "by default, but complete ZIP/Zstd/recovery/native/Android/final-authority evidence remains mandatory."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-parser-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-parser.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "timing": result["timing"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor EOCD-indexed parser oracle invalid")


if __name__ == "__main__":
    main()
