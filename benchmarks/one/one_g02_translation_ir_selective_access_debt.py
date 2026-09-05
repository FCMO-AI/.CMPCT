"""ONE-G0.2 selective-access falsifier for the generic translation Law+Surprise IR.

Referee freeze
==============
The automatic translation Law+Surprise result is dense and compiles into the existing
ONE IR, but density alone is insufficient. This experiment asks whether the *current*
experimental wire+reference evaluator can serve a 4 KiB range of the edited root without
materializing unrelated information.

This is deliberately a current-implementation falsifier, not a theoretical lower bound.
Each row builds the same edited-version program used by the generic-IR compile experiment,
serializes it, decodes it through the public experimental wire reader, evaluates the
program through the public reference VM, then slices one deterministic 4 KiB request from
the authenticated edited root. The reader currently has no range API, so all work required
by that public path is charged.

Frozen interpretation:
- PASS/advance only if median materialized amplification <= 8x AND median work
  amplification <= 16x on both source sizes.
- Otherwise preserve the density result but open explicit access debt; do not tune this
  benchmark. The next Builder must add indexed/range-aware execution and/or selective
  Crystallization while preserving the same generic reader ontology.

No product, format, v0.29/v0.30, native-speed or release authority is created here.
"""
from __future__ import annotations

import json
import os
import random
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, MUTATION_COUNTS, _edited,
)
from benchmarks.one.one_g02_translation_law_surprise_ir_compile import _programs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

REQUEST_BYTES = 4096


def run():
    master = random.Random(MASTER_SEED)
    rows = []
    by_size: dict[int, list[dict]] = {size: [] for size in BASE_SIZES}
    failures = []

    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            for mutations in MUTATION_COUNTS:
                edited = _edited(
                    base,
                    random.Random(seed ^ (mutations << 32) ^ 0xA11CE5EED),
                    mutations,
                )
                _, full, _ = _programs(base, edited)
                wire, _ = encode_program(full)
                decoded = decode_program(wire)
                outputs, stats = evaluate(decoded)
                request = min(REQUEST_BYTES, size)
                start = max(0, (size - request) // 2)
                selected = outputs["edited"][start : start + request]
                expected = edited[start : start + request]
                reasons = []
                if selected != expected:
                    reasons.append("selected_bytes")
                row = {
                    "base_bytes": size,
                    "base_index": base_index,
                    "mutation_count": mutations,
                    "request_start": start,
                    "requested_bytes": request,
                    "wire_bytes_touched_current_api": len(wire),
                    "wire_amplification": len(wire) / request,
                    "materialized_bytes_current_api": stats.materialized_bytes,
                    "materialized_amplification": stats.materialized_bytes / request,
                    "work_bytes_current_api": stats.work_bytes,
                    "work_amplification": stats.work_bytes / request,
                    "nodes_evaluated": stats.nodes_evaluated,
                    "failures": reasons,
                }
                rows.append(row)
                by_size[size].append(row)
                if reasons:
                    failures.append(row)

    summaries = {}
    gate_failures = list(failures)
    for size, group in by_size.items():
        summary = {
            "rows": len(group),
            "median_wire_amplification": median(r["wire_amplification"] for r in group),
            "median_materialized_amplification": median(r["materialized_amplification"] for r in group),
            "median_work_amplification": median(r["work_amplification"] for r in group),
            "max_materialized_amplification": max(r["materialized_amplification"] for r in group),
            "max_work_amplification": max(r["work_amplification"] for r in group),
        }
        summaries[str(size)] = summary
        if summary["median_materialized_amplification"] > 8.0:
            gate_failures.append({"base_bytes": size, "reason": "median_materialized_amplification_gt_8x"})
        if summary["median_work_amplification"] > 16.0:
            gate_failures.append({"base_bytes": size, "reason": "median_work_amplification_gt_16x"})

    return {
        "schema": "cmpct-one-g02-translation-ir-selective-access-debt-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "request_bytes": REQUEST_BYTES,
        "rows": len(rows),
        "summaries": summaries,
        "gate_failures": gate_failures,
        "decision": "current_ir_selective_access_acceptable" if not gate_failures else "preserve_density_open_selective_access_debt",
        "claim_boundary": "current experimental wire+reference VM access-cost evidence only; not a theoretical cone lower bound or product authority",
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
