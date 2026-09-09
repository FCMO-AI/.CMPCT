"""ONE-G0.2 root Law fusion falsifier.

Frozen by docs/one/prereg/ONE_G02_ROOT_LAW_FUSION_PREREG_2026-09-08.md.
"""
from __future__ import annotations

import json
import statistics
import time

from benchmarks.one.one_g02_relation_granularity_frontier import _candidate, _case, _has_duplicate_blocks, _literal
from experiments.one.fused_root_law_plan import compile_fused_root_law_plan, execute_fused_root_law_plan
from experiments.one.generic_execution_plan import compile_execution_plan
from experiments.one.native_plan_bulk import execute_native_bulk_plan
from experiments.one.wire import encode_program

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
BLOCKS = (512, 4096)
OPS = ("add8", "xor")
REPETITIONS = 21
MAX_WIRE_RATIO = 0.55
MAX_FUSED_VS_GENERIC = 0.50
MAX_FUSED_VS_LITERAL = 1.25
MAX_TRAFFIC_RATIO = 1.05


def _median_call(fn):
    walls: list[int] = []
    cpus: list[int] = []
    last = None
    for _ in range(REPETITIONS):
        w0, c0 = time.perf_counter_ns(), time.process_time_ns()
        last = fn()
        walls.append(time.perf_counter_ns() - w0)
        cpus.append(time.process_time_ns() - c0)
    return last, int(statistics.median(walls)), int(statistics.median(cpus))


def _median_compile(plan):
    walls: list[int] = []
    cpus: list[int] = []
    last = None
    for _ in range(7):
        w0, c0 = time.perf_counter_ns(), time.process_time_ns()
        last = compile_fused_root_law_plan(plan)
        walls.append(time.perf_counter_ns() - w0)
        cpus.append(time.process_time_ns() - c0)
    return last, int(statistics.median(walls)), int(statistics.median(cpus))


def decide(rows: list[dict]) -> str:
    expected = {(s, b, o) for s in SIZES for b in BLOCKS for o in OPS}
    observed = {(r["size"], r["block"], r["op"]) for r in rows}
    if len(rows) != len(expected) or observed != expected:
        return "INVALIDATE_ROOT_LAW_FUSION"
    if any(r["duplicate_blocks"] or not r["semantic_ok"] or not r["wire_unchanged"] for r in rows):
        return "INVALIDATE_ROOT_LAW_FUSION"
    if any(r["modeled_traffic_ratio_vs_literal"] > MAX_TRAFFIC_RATIO for r in rows):
        return "INVALIDATE_ROOT_LAW_FUSION"

    decisive = [r for r in rows if r["size"] == 1024 * 1024]
    if any(r["wire_ratio_vs_literal"] > MAX_WIRE_RATIO for r in decisive):
        return "HOLD_ROOT_LAW_FUSION"
    if any(r["fused_wall_ratio_vs_generic"] > MAX_FUSED_VS_GENERIC or r["fused_cpu_ratio_vs_generic"] > MAX_FUSED_VS_GENERIC for r in decisive):
        return "HOLD_ROOT_LAW_FUSION"
    if any(r["fused_wall_ratio_vs_literal"] > MAX_FUSED_VS_LITERAL or r["fused_cpu_ratio_vs_literal"] > MAX_FUSED_VS_LITERAL for r in decisive):
        return "HOLD_ROOT_LAW_FUSION"
    return "ADVANCE_ROOT_LAW_FUSION"


def main() -> int:
    rows: list[dict] = []
    # Warm native libraries before any reported timing.
    warm_data, warm_pairs = _case("add8", 64 * 1024, 4096)
    warm_program = _candidate(warm_data, warm_pairs, "add8", 4096)
    assert warm_program is not None
    warm_plan = compile_execution_plan(warm_program)
    warm_fused = compile_fused_root_law_plan(warm_plan)
    execute_native_bulk_plan(warm_plan)
    execute_fused_root_law_plan(warm_fused)

    for size in SIZES:
        for block in BLOCKS:
            for op in OPS:
                data, pairs = _case(op, size, block)
                duplicate = _has_duplicate_blocks(data, block)
                candidate = _candidate(data, pairs, op, block)
                if candidate is None:
                    raise AssertionError((size, block, op, "unexpected node rejection"))
                literal = _literal(data)
                candidate_wire_before, _ = encode_program(candidate)
                literal_wire, _ = encode_program(literal)
                candidate_plan = compile_execution_plan(candidate)
                literal_plan = compile_execution_plan(literal)
                fused, compile_wall, compile_cpu = _median_compile(candidate_plan)
                candidate_wire_after, _ = encode_program(candidate)

                generic_last, gw, gc = _median_call(lambda: execute_native_bulk_plan(candidate_plan))
                fused_last, fw, fc = _median_call(lambda: execute_fused_root_law_plan(fused))
                literal_last, lw, lc = _median_call(lambda: execute_native_bulk_plan(literal_plan))
                generic_outputs, _ = generic_last
                fused_outputs, fused_stats = fused_last
                literal_outputs, _ = literal_last
                semantic_ok = generic_outputs["root"] == fused_outputs["root"] == literal_outputs["root"] == data
                literal_traffic = 3 * len(data)
                rows.append({
                    "size": size,
                    "block": block,
                    "op": op,
                    "duplicate_blocks": duplicate,
                    "semantic_ok": semantic_ok,
                    "wire_unchanged": candidate_wire_before == candidate_wire_after,
                    "candidate_wire_bytes": len(candidate_wire_before),
                    "literal_wire_bytes": len(literal_wire),
                    "wire_ratio_vs_literal": len(candidate_wire_before) / len(literal_wire),
                    "command_count": fused_stats.command_count,
                    "fused_compile_wall_ns": compile_wall,
                    "fused_compile_cpu_ns": compile_cpu,
                    "generic_wall_ns": gw,
                    "generic_cpu_ns": gc,
                    "fused_wall_ns": fw,
                    "fused_cpu_ns": fc,
                    "literal_wall_ns": lw,
                    "literal_cpu_ns": lc,
                    "fused_wall_ratio_vs_generic": fw / gw,
                    "fused_cpu_ratio_vs_generic": fc / gc,
                    "fused_wall_ratio_vs_literal": fw / lw,
                    "fused_cpu_ratio_vs_literal": fc / lc,
                    "modeled_traffic_bytes": fused_stats.modeled_traffic_bytes,
                    "literal_modeled_traffic_bytes": literal_traffic,
                    "modeled_traffic_ratio_vs_literal": fused_stats.modeled_traffic_bytes / literal_traffic,
                })

    decision = decide(rows)
    payload = {
        "experiment": "ONE-G0.2 root Law fusion",
        "decision": decision,
        "repetitions": REPETITIONS,
        "max_wire_ratio": MAX_WIRE_RATIO,
        "max_fused_vs_generic": MAX_FUSED_VS_GENERIC,
        "max_fused_vs_literal": MAX_FUSED_VS_LITERAL,
        "max_traffic_ratio": MAX_TRAFFIC_RATIO,
        "rows": rows,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if decision == "ADVANCE_ROOT_LAW_FUSION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
