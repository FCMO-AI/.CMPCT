"""ONE-G0.2 generic range-cone Builder against the frozen selective-access loss.

Referee freeze
==============
The current public wire+VM path showed 32x/112x materialization/work amplification at
64 KiB and 128x/448x at 256 KiB for a 4 KiB request.  This Builder isolates whether that
loss is inherent to the generic Law graph or caused by whole-program/whole-root execution.

The Builder may use only a generic range evaluator over the existing six ONE operations.
It receives the already-decoded Program: wire indexing and integrity are *not gifted as
solved*; they are explicitly reported as remaining debt.  The full reference evaluator is
an independent oracle for exact requested bytes.

Frozen advance gate on every one of the 64 rows:
- selected bytes exactly equal the authenticated full-reference oracle slice;
- cone materialization <= 2.1x requested bytes;
- cone work <= 2.1x requested bytes;
- the range path must report authenticated=false.
If green, retire reconstruction-cone amplification as the causal owner and attack wire
indexing + hard selective authentication next.  No complete selective-read claim is allowed.
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
from experiments.one.range_vm import reconstruct_range_unverified
from experiments.one.vm import evaluate

REQUEST_BYTES = 4096
MAX_AMP = 2.1


def run():
    master = random.Random(MASTER_SEED)
    rows = []
    failures = []
    by_size = {size: [] for size in BASE_SIZES}
    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            for mutations in MUTATION_COUNTS:
                edited = _edited(base, random.Random(seed ^ (mutations << 32) ^ 0xA11CE5EED), mutations)
                _, program, _ = _programs(base, edited)
                oracle_outputs, _ = evaluate(program)
                start = (size - REQUEST_BYTES) // 2
                got, stats = reconstruct_range_unverified(program, "edited", start, REQUEST_BYTES)
                expected = oracle_outputs["edited"][start:start + REQUEST_BYTES]
                mat_amp = stats.materialized_bytes / REQUEST_BYTES
                work_amp = stats.work_bytes / REQUEST_BYTES
                reasons = []
                if got != expected:
                    reasons.append("oracle_mismatch")
                if mat_amp > MAX_AMP:
                    reasons.append("materialized_amp_gt_2.1x")
                if work_amp > MAX_AMP:
                    reasons.append("work_amp_gt_2.1x")
                if stats.authenticated:
                    reasons.append("unexpected_authentication_claim")
                row = {
                    "base_bytes": size,
                    "base_index": base_index,
                    "mutation_count": mutations,
                    "request_start": start,
                    "requested_bytes": REQUEST_BYTES,
                    "cone_materialized_bytes": stats.materialized_bytes,
                    "cone_materialized_amplification": mat_amp,
                    "cone_work_bytes": stats.work_bytes,
                    "cone_work_amplification": work_amp,
                    "nodes_touched": stats.nodes_touched,
                    "max_depth": stats.max_depth,
                    "authenticated": stats.authenticated,
                    "failures": reasons,
                }
                rows.append(row)
                by_size[size].append(row)
                if reasons:
                    failures.append(row)
    summaries = {}
    for size, group in by_size.items():
        summaries[str(size)] = {
            "rows": len(group),
            "median_materialized_amplification": median(r["cone_materialized_amplification"] for r in group),
            "max_materialized_amplification": max(r["cone_materialized_amplification"] for r in group),
            "median_work_amplification": median(r["cone_work_amplification"] for r in group),
            "max_work_amplification": max(r["cone_work_amplification"] for r in group),
            "median_nodes_touched": median(r["nodes_touched"] for r in group),
            "max_nodes_touched": max(r["nodes_touched"] for r in group),
        }
    return {
        "schema": "cmpct-one-g02-translation-ir-range-cone-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rows": len(rows),
        "request_bytes": REQUEST_BYTES,
        "gate_failures": failures,
        "summaries": summaries,
        "decision": "reconstruction_cone_owner_retired_wire_integrity_debt_remains" if not failures else "generic_range_cone_builder_rejected",
        "remaining_debt": ["wire_indexed_selective_access", "hard_selective_authentication"],
        "claim_boundary": "decoded-Program reconstruction-cone evidence only; range output is deliberately unauthenticated and full wire access is not modeled as solved",
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
