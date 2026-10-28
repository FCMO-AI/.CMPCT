from __future__ import annotations

"""Referee the narrow Office structural-locality rejection with exact dependency closure.

Mission Lock / Referee
======================
The workload-independent streaming admission proof rejected all eight exact SFV4 derived streams at a
worst enclosing dependency span of 34,580 B (8.442x), only 1,812 B above the frozen 32,768 B decoded-
work limit. That certificate is deliberately sufficient, not necessary: it charges every byte in the
contiguous interval between the earliest transitive ancestor and the end of the 4 KiB request, including
holes that the sparse reader would not need to reconstruct.

Falsifiable hypothesis: each Office stream's *first* structural rejection is a conservative false
negative: the exact unique transitive decoded-byte closure of that same 4 KiB window is <=32,768 B.
This would authorize research on a tighter workload-independent certificate; it would not authorize
product admission, because later sliding windows remain unchecked after the current proof rejects.

Disproof: if any first-rejected window has exact unique closure >32,768 B, the current rejection is
mechanistically real for that stream and certificate tightening cannot rescue it under the frozen 8x
contract. Preserve that result and change representation/framing instead of moving the threshold.

The full parent graph exists only in this diagnostic referee. It is forbidden as product/admission
state. We also measure all 4 KiB-aligned windows plus the final suffix as an independent opportunity
probe, but those aligned probes do not substitute for a future every-window safety certificate.
"""

import argparse
from array import array
import json
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv3_derived_views as SFV3
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_deflate_structural_locality_admission as ADMIT
from benchmarks import v030_r4_deflate_sparse_dependency_oracle as EXACT

SCHEMA = "cmpct-v030-r4-office-exact-dependency-rejection-referee-v1"
REQUEST = 4096
LIMIT = 8 * REQUEST


def _exact_window(parents: array, start: int, end: int) -> dict:
    marks = array("I", [0]) * len(parents)
    return EXACT.closure_for_request(parents, marks, 1, start, end)


def _aligned_probe(parents: array) -> dict:
    starts = EXACT._request_starts(len(parents))
    marks = array("I", [0]) * len(parents)
    worst = None
    failures = 0
    total = 0
    t0 = time.perf_counter()
    for generation, start in enumerate(starts, 1):
        row = EXACT.closure_for_request(parents, marks, generation, start, min(start + REQUEST, len(parents)))
        total += row["unique_decoded_closure_bytes"]
        failures += row["unique_decoded_closure_bytes"] > LIMIT
        if worst is None or row["unique_decoded_closure_bytes"] > worst["unique_decoded_closure_bytes"]:
            worst = row
    if worst is None:
        raise RuntimeError("no aligned probes")
    return {
        "requests": len(starts),
        "failed_over_8x": failures,
        "worst": worst,
        "mean_unique_decoded_closure_bytes": total / len(starts),
        "wall_s": time.perf_counter() - t0,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_exact_rejection_referee_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_exact_rejection_referee_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"

    containers, _shared = SFV2.discover(source)
    all_streams = SFV4._all_member_streams(containers)
    derived = SFV3._derived_inventory(source, containers, all_streams)
    if not derived:
        raise RuntimeError("no exact Office derived streams")

    rows = []
    first_rejection_true_violations = 0
    aligned_streams_with_violation = 0
    for rel, rec in sorted(derived.items()):
        stream = all_streams[rec["stream_hash"]]
        raw = (source / rel).read_bytes()
        if zlib.decompress(stream, -15) != raw:
            raise RuntimeError("derived identity mismatch")

        proof = ADMIT.prove(stream)
        failure = proof["first_failure"]
        if proof["accepted"] or failure is None:
            raise RuntimeError("expected frozen Office stream to reproduce structural rejection")

        t0 = time.perf_counter()
        parsed = EXACT.parse_parents(stream)
        parse_wall = time.perf_counter() - t0
        parents = parsed["parents"]
        if len(parents) != len(raw):
            raise RuntimeError("exact parent parser length mismatch")

        exact_failure = _exact_window(parents, int(failure["window_start"]), int(failure["window_end"]))
        exact_failure_over = exact_failure["unique_decoded_closure_bytes"] > LIMIT
        first_rejection_true_violations += exact_failure_over

        aligned = _aligned_probe(parents)
        aligned_streams_with_violation += aligned["failed_over_8x"] > 0
        rows.append({
            "logical_bytes": len(raw),
            "compressed_bytes": len(stream),
            "structural_first_failure": failure,
            "structural_first_failure_amplification": failure["enclosing_dependency_span_bytes"] / REQUEST,
            "exact_first_failure": exact_failure,
            "exact_first_failure_over_8x": exact_failure_over,
            "first_rejection_is_conservative_false_negative": not exact_failure_over,
            "aligned_probe": aligned,
            "parser": {
                "blocks": parsed["blocks"],
                "tokens": parsed["tokens"],
                "literal_tokens": parsed["literal_tokens"],
                "copy_tokens": parsed["copy_tokens"],
                "parse_wall_s": parse_wall,
            },
        })

    all_first_rejections_false = first_rejection_true_violations == 0
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "request_bytes": REQUEST,
        "limit_bytes": LIMIT,
        "stream_count": len(rows),
        "first_rejection_true_violation_count": first_rejection_true_violations,
        "aligned_streams_with_exact_violation": aligned_streams_with_violation,
        "max_structural_first_failure_span_bytes": max(r["structural_first_failure"]["enclosing_dependency_span_bytes"] for r in rows),
        "max_exact_first_failure_closure_bytes": max(r["exact_first_failure"]["unique_decoded_closure_bytes"] for r in rows),
        "max_exact_first_failure_amplification": max(r["exact_first_failure"]["amplification"] for r in rows),
        "max_aligned_exact_closure_bytes": max(r["aligned_probe"]["worst"]["unique_decoded_closure_bytes"] for r in rows),
        "rows": rows,
        "hypothesis": {
            "all_first_structural_rejections_are_conservative_false_negatives": all_first_rejections_false,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "frozen_8x_limit": True,
            "threshold_sweep": False,
            "path_hash_workload_dispatch": False,
            "full_parent_graph_used_only_as_referee": True,
            "product_admission_authorized": False,
            "later_unaligned_windows_proven_safe": False,
            "aligned_probe_is_opportunity_evidence_only": True,
        },
        "next_if_supported": "design a tighter workload-independent streaming certificate for sparse/holed dependency closure, then hostile-review it against known >8x streams and every-window exact referee before any Office admission",
        "next_if_falsified": "preserve the negative and change Office representation/framing; do not relax the frozen 8x contract or add path-specific exceptions",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-exact-rejection-referee-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-exact-rejection-referee.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({k: d[k] for k in (
        "stream_count",
        "first_rejection_true_violation_count",
        "aligned_streams_with_exact_violation",
        "max_structural_first_failure_span_bytes",
        "max_exact_first_failure_closure_bytes",
        "max_exact_first_failure_amplification",
        "max_aligned_exact_closure_bytes",
        "hypothesis",
    )}, indent=2))


if __name__ == "__main__":
    main()
