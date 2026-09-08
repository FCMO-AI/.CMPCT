"""ONE-G0.2 terminal Law root-sink rehabilitation falsifier.

Frozen by ONE_G02_TERMINAL_LAW_ROOT_SINK_PREREG_2026-09-08.md. The stored
Program/wire is unchanged; only reader execution is compared.
"""
from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import json
import os
import statistics
import subprocess
import sys
import time

from benchmarks.one.one_g02_compact_observer_handoff_writer import FAMILIES, _case
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from experiments.one.fused_terminal_reader import evaluate_terminal_roots_fused
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe_small_vector import observe_native_small_vector
from experiments.one.run_fill_law import MIN_FILL_RUN, program_from_observed_runs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (64 << 10, 256 << 10, 1 << 20)
REPETITIONS = 21
RUN_RICH = ("structured", "long_runs")
CONTROLS = ("compressed_like", "random", "near_repeats")
LONG_RUNS_1M_WIRE_MAX = 0.55
STRUCTURED_1M_WIRE_MAX = 0.90
FUSED_TRAFFIC_MAX = 1.05
FUSED_TEMP_MAX = 1.05
FUSED_TIME_MAX = 1.05


def _programs(source: bytes, target: bytes):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    observation = observe_native_small_vector(target).materialize()
    previous_root = Root(Ref(0), len(source), previous_digest)
    control, _ = _literal_program(source, target, previous_root, current_digest)
    candidate, stats = program_from_observed_runs(
        source,
        target,
        observation.runs,
        current_digest=current_digest,
        previous_digest=previous_digest,
    )
    control.validate_shape()
    candidate.validate_shape()
    control_wire, control_ws = _encode_program_growable_prevalidated(control)
    candidate_wire, candidate_ws = _encode_program_growable_prevalidated(candidate)
    return (
        decode_program(control_wire),
        decode_program(candidate_wire),
        control_ws,
        candidate_ws,
        stats,
    )


def _time_pair(control, candidate) -> tuple[float, float, float, float]:
    control_walls: list[int] = []
    control_cpus: list[int] = []
    candidate_walls: list[int] = []
    candidate_cpus: list[int] = []
    control_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        # Equal warmup before paired samples.
        evaluate_terminal_roots_fused(control)
        evaluate_terminal_roots_fused(candidate)
        for rep in range(REPETITIONS):
            order = (False, True) if rep % 2 == 0 else (True, False)
            for is_candidate in order:
                if is_candidate:
                    candidate_value = None
                    program = candidate
                else:
                    control_value = None
                    program = control
                c0 = time.process_time_ns()
                w0 = time.perf_counter_ns()
                value = evaluate_terminal_roots_fused(program)
                w1 = time.perf_counter_ns()
                c1 = time.process_time_ns()
                if is_candidate:
                    candidate_value = value
                    candidate_walls.append(w1 - w0)
                    candidate_cpus.append(c1 - c0)
                else:
                    control_value = value
                    control_walls.append(w1 - w0)
                    control_cpus.append(c1 - c0)
    finally:
        if was_enabled:
            gc.enable()
    if control_value is None or candidate_value is None:
        raise AssertionError("fused reader paired timing produced no value")
    return (
        float(statistics.median(control_walls)),
        float(statistics.median(control_cpus)),
        float(statistics.median(candidate_walls)),
        float(statistics.median(candidate_cpus)),
    )


def _child(size: int, family: str) -> dict:
    source, target = _case(family, size)
    control, candidate, control_ws, candidate_ws, compiler_stats = _programs(source, target)

    control_reference, control_reference_stats = evaluate(control)
    candidate_reference, candidate_reference_stats = evaluate(candidate)
    control_fused, control_fused_stats = evaluate_terminal_roots_fused(control)
    candidate_fused, candidate_fused_stats = evaluate_terminal_roots_fused(candidate)
    expected = {"previous": source, "current": target}
    semantic_ok = control_reference == candidate_reference == control_fused == candidate_fused == expected
    roots_ok = (
        control.roots["previous"].sha256 == candidate.roots["previous"].sha256 == sha256(source).hexdigest()
        and control.roots["current"].sha256 == candidate.roots["current"].sha256 == sha256(target).hexdigest()
    )
    if not semantic_ok or not roots_ok:
        raise AssertionError(f"terminal root-sink semantic mismatch: {size=} {family=}")

    scalars = {
        "semantic_ok": semantic_ok and roots_ok,
        "qualifying_fill_runs": compiler_stats.qualifying_runs,
        "fill_bytes": compiler_stats.fill_bytes,
        "control_wire_bytes": control_ws.total_bytes,
        "candidate_wire_bytes": candidate_ws.total_bytes,
        "control_reference_work_bytes": control_reference_stats.work_bytes,
        "candidate_reference_work_bytes": candidate_reference_stats.work_bytes,
        "control_fused_traffic_bytes": control_fused_stats.modeled_memory_traffic_bytes,
        "candidate_fused_traffic_bytes": candidate_fused_stats.modeled_memory_traffic_bytes,
        "control_fused_peak_temporary_bytes": control_fused_stats.peak_temporary_bytes,
        "candidate_fused_peak_temporary_bytes": candidate_fused_stats.peak_temporary_bytes,
        "control_stored_surprise_read_bytes": control_fused_stats.stored_surprise_read_bytes,
        "candidate_stored_surprise_read_bytes": candidate_fused_stats.stored_surprise_read_bytes,
    }
    del control_reference, candidate_reference, control_fused, candidate_fused
    gc.collect()

    control_wall, control_cpu, candidate_wall, candidate_cpu = _time_pair(control, candidate)
    return {
        "bytes": size,
        "family": family,
        **scalars,
        "candidate_over_control_wire": scalars["candidate_wire_bytes"] / scalars["control_wire_bytes"],
        "candidate_over_control_reference_work": scalars["candidate_reference_work_bytes"] / scalars["control_reference_work_bytes"],
        "candidate_over_control_fused_traffic": scalars["candidate_fused_traffic_bytes"] / scalars["control_fused_traffic_bytes"],
        "candidate_over_control_fused_peak_temporary": scalars["candidate_fused_peak_temporary_bytes"] / scalars["control_fused_peak_temporary_bytes"],
        "control_fused_wall_median_ns": control_wall,
        "candidate_fused_wall_median_ns": candidate_wall,
        "candidate_over_control_fused_wall": candidate_wall / control_wall,
        "control_fused_cpu_median_ns": control_cpu,
        "candidate_fused_cpu_median_ns": candidate_cpu,
        "candidate_over_control_fused_cpu": candidate_cpu / control_cpu,
    }


def _invoke(size: int, family: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_g02_terminal_law_root_sink", "--child", str(size), family],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("terminal root-sink child produced no JSON")
    return json.loads(lines[-1])


def adjudicate(rows: list[dict]) -> str:
    expected = {(size, family) for size in SIZES for family in FAMILIES}
    actual = {(int(row["bytes"]), str(row["family"])) for row in rows}
    if len(rows) != len(expected) or actual != expected:
        return "INVALIDATE_TERMINAL_LAW_ROOT_SINK"
    if not all(bool(row["semantic_ok"]) for row in rows):
        return "INVALIDATE_TERMINAL_LAW_ROOT_SINK"
    if any(row["candidate_wire_bytes"] > row["control_wire_bytes"] for row in rows):
        return "HOLD_TERMINAL_LAW_ROOT_SINK"
    if any(row["candidate_over_control_fused_traffic"] > FUSED_TRAFFIC_MAX for row in rows):
        return "HOLD_TERMINAL_LAW_ROOT_SINK"
    if any(row["candidate_over_control_fused_peak_temporary"] > FUSED_TEMP_MAX for row in rows):
        return "HOLD_TERMINAL_LAW_ROOT_SINK"

    long_1m = next(row for row in rows if row["bytes"] == (1 << 20) and row["family"] == "long_runs")
    structured_1m = next(row for row in rows if row["bytes"] == (1 << 20) and row["family"] == "structured")
    if long_1m["candidate_over_control_wire"] > LONG_RUNS_1M_WIRE_MAX:
        return "HOLD_TERMINAL_LAW_ROOT_SINK"
    if structured_1m["candidate_over_control_wire"] > STRUCTURED_1M_WIRE_MAX:
        return "HOLD_TERMINAL_LAW_ROOT_SINK"
    for row in rows:
        if row["candidate_over_control_fused_wall"] > FUSED_TIME_MAX or row["candidate_over_control_fused_cpu"] > FUSED_TIME_MAX:
            return "HOLD_TERMINAL_LAW_ROOT_SINK"
    return "ADVANCE_TERMINAL_LAW_ROOT_SINK"


def run() -> dict:
    rows = [_invoke(size, family) for size in SIZES for family in FAMILIES]
    decision = adjudicate(rows)
    return {
        "schema": "cmpct-one-g02-terminal-law-root-sink-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "families": list(FAMILIES),
        "repetitions_per_fresh_row": REPETITIONS,
        "min_fill_run": MIN_FILL_RUN,
        "long_runs_1m_wire_max": LONG_RUNS_1M_WIRE_MAX,
        "structured_1m_wire_max": STRUCTURED_1M_WIRE_MAX,
        "fused_traffic_max": FUSED_TRAFFIC_MAX,
        "fused_temp_max": FUSED_TEMP_MAX,
        "fused_time_max": FUSED_TIME_MAX,
        "decision": decision,
        "claim_boundary": (
            "full-root terminal surprise/fill concat execution fusion only; same stored Program/wire and root SHA-256; "
            "no selective-range claim, authenticated placement, recovery, filesystem, portability, comparator, or Genesis authority"
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", nargs=2, metavar=("SIZE", "FAMILY"))
    args = parser.parse_args()
    if args.child:
        size_s, family = args.child
        size = int(size_s)
        if size not in SIZES or family not in FAMILIES:
            return 2
        print(json.dumps(_child(size, family), sort_keys=True))
        return 0
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_TERMINAL_LAW_ROOT_SINK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
