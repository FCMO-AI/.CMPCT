"""ONE-G0.2 representation-neutral relation root-fusion falsifier.

Mission Lock / Referee
======================
The relation-granularity frontier found strong density (~0.504x literal wire at 4 KiB)
but the unchanged generic graph pays 2.333x reference work and 2.5x materialization.  This
experiment asks whether that penalty is execution geometry rather than a reason to invent a
relation codec.

Falsifiable hypothesis
----------------------
For the exact existing Surprise + Fill + add8/xor + root-Concat Programs, a bounded direct
root sink must preserve byte/root semantics, reduce modeled reader work to <=1.50x literal,
reduce materialization to <=1.10x literal, and make the decisive 1 MiB / 4 KiB relation rows
no worse than 1.50x literal wall+CPU while beating the already-promoted native prepared
executor by at least 2x.  No stored Program, node limit, Law operation, root commitment or
resource setting may change.

An ADVANCE is scoped to execution geometry.  It does not make relations canonical or claim
literal-parity; <=1.05x literal remains the stronger system-ready target.
"""
from __future__ import annotations

import json
import statistics
import time

from benchmarks.one.one_g02_relation_granularity_frontier import _candidate, _case, _literal
from experiments.one.generic_execution_plan import compile_execution_plan
from experiments.one.native_plan_bulk import execute_native_bulk_plan
from experiments.one.relation_root_fusion import evaluate_relation_roots_fused
from experiments.one.vm import evaluate

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
BLOCKS = (512, 1024, 2048, 4096)
OPS = ("add8", "xor")
REPETITIONS = 11
MAX_WORK_RATIO = 1.50
MAX_MATERIALIZED_RATIO = 1.10
MAX_DECISIVE_LITERAL_TIME_RATIO = 1.50
MAX_DECISIVE_NATIVE_TIME_RATIO = 0.50
SYSTEM_READY_TIME_RATIO = 1.05


def _timed(fn) -> tuple[int, int]:
    walls: list[int] = []
    cpus: list[int] = []
    fn()
    for _ in range(REPETITIONS):
        w0, c0 = time.perf_counter_ns(), time.process_time_ns()
        fn()
        walls.append(time.perf_counter_ns() - w0)
        cpus.append(time.process_time_ns() - c0)
    return int(statistics.median(walls)), int(statistics.median(cpus))


def decide(rows: list[dict]) -> str:
    expected = {(size, block, op) for size in SIZES for block in BLOCKS for op in OPS}
    observed = {(row["size"], row["block"], row["op"]) for row in rows}
    if len(rows) != len(expected) or observed != expected:
        return "INVALIDATE_RELATION_ROOT_FUSION"
    if any(not row["semantic_ok"] or not row["root_ok"] for row in rows):
        return "INVALIDATE_RELATION_ROOT_FUSION"
    if any(row["wire_changed"] for row in rows):
        return "INVALIDATE_RELATION_ROOT_FUSION"
    decisive = [row for row in rows if row["size"] == 1024 * 1024 and row["block"] == 4096]
    if len(decisive) != 2:
        return "INVALIDATE_RELATION_ROOT_FUSION"
    for row in decisive:
        if row["fused_work_ratio_vs_literal"] > MAX_WORK_RATIO:
            return "HOLD_RELATION_ROOT_FUSION"
        if row["fused_materialized_ratio_vs_literal"] > MAX_MATERIALIZED_RATIO:
            return "HOLD_RELATION_ROOT_FUSION"
        if row["fused_wall_ratio_vs_literal"] > MAX_DECISIVE_LITERAL_TIME_RATIO:
            return "HOLD_RELATION_ROOT_FUSION"
        if row["fused_cpu_ratio_vs_literal"] > MAX_DECISIVE_LITERAL_TIME_RATIO:
            return "HOLD_RELATION_ROOT_FUSION"
        if row["fused_wall_ratio_vs_native"] > MAX_DECISIVE_NATIVE_TIME_RATIO:
            return "HOLD_RELATION_ROOT_FUSION"
        if row["fused_cpu_ratio_vs_native"] > MAX_DECISIVE_NATIVE_TIME_RATIO:
            return "HOLD_RELATION_ROOT_FUSION"
    return "ADVANCE_RELATION_ROOT_FUSION"


def main() -> int:
    rows: list[dict] = []
    for size in SIZES:
        for block in BLOCKS:
            for op in OPS:
                data, pairs = _case(op, size, block)
                literal = _literal(data)
                candidate = _candidate(data, pairs, op, block)
                if candidate is None:
                    raise AssertionError((size, block, op, "unexpected node-budget rejection"))

                ref_out, ref_stats = evaluate(candidate)
                lit_out, lit_stats = evaluate(literal)
                fused_out, fused_stats = evaluate_relation_roots_fused(candidate)
                semantic_ok = ref_out == fused_out == lit_out == {"root": data}
                root_ok = candidate.roots["root"].sha256 == literal.roots["root"].sha256

                # Stored Program identity is protected by comparing the exact frontier
                # candidate object before and after execution; fusion receives no rewrite.
                before = repr(candidate)
                evaluate_relation_roots_fused(candidate)
                wire_changed = repr(candidate) != before

                plan = compile_execution_plan(candidate)
                lw, lc = _timed(lambda: evaluate(literal))
                nw, nc = _timed(lambda: execute_native_bulk_plan(plan))
                fw, fc = _timed(lambda: evaluate_relation_roots_fused(candidate))

                rows.append({
                    "size": size,
                    "block": block,
                    "op": op,
                    "nodes": len(candidate.nodes),
                    "semantic_ok": semantic_ok,
                    "root_ok": root_ok,
                    "wire_changed": wire_changed,
                    "reference_work_ratio_vs_literal": ref_stats.work_bytes / lit_stats.work_bytes,
                    "reference_materialized_ratio_vs_literal": ref_stats.materialized_bytes / lit_stats.materialized_bytes,
                    "fused_work_ratio_vs_literal": fused_stats.modeled_work_bytes / lit_stats.work_bytes,
                    "fused_materialized_ratio_vs_literal": fused_stats.materialized_bytes / lit_stats.materialized_bytes,
                    "fused_peak_temporary_bytes": fused_stats.peak_temporary_bytes,
                    "fused_relations": fused_stats.fused_relations,
                    "literal_wall_ns": lw,
                    "native_wall_ns": nw,
                    "fused_wall_ns": fw,
                    "fused_cpu_ns": fc,
                    "fused_wall_ratio_vs_literal": fw / lw,
                    "fused_cpu_ratio_vs_literal": fc / lc,
                    "fused_wall_ratio_vs_native": fw / nw,
                    "fused_cpu_ratio_vs_native": fc / nc,
                    "system_ready_wall": fw / lw <= SYSTEM_READY_TIME_RATIO,
                    "system_ready_cpu": fc / lc <= SYSTEM_READY_TIME_RATIO,
                })

    decision = decide(rows)
    decisive = [row for row in rows if row["size"] == 1024 * 1024 and row["block"] == 4096]
    payload = {
        "experiment": "ONE-G0.2 representation-neutral relation root fusion",
        "decision": decision,
        "repetitions": REPETITIONS,
        "max_work_ratio": MAX_WORK_RATIO,
        "max_materialized_ratio": MAX_MATERIALIZED_RATIO,
        "max_decisive_literal_time_ratio": MAX_DECISIVE_LITERAL_TIME_RATIO,
        "max_decisive_native_time_ratio": MAX_DECISIVE_NATIVE_TIME_RATIO,
        "system_ready_time_ratio": SYSTEM_READY_TIME_RATIO,
        "decisive_system_ready": all(row["system_ready_wall"] and row["system_ready_cpu"] for row in decisive),
        "rows": rows,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if decision == "ADVANCE_RELATION_ROOT_FUSION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
