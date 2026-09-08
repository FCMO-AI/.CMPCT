"""ONE-G0.2 observer-run -> generic fill-Law compiler falsifier.

Frozen by ONE_G02_OBSERVER_RUN_FILL_LAW_PREREG_2026-09-08.md.
Both arms pay the same native observation/materialization and root hashing. Only the
candidate consumes qualifying maximal-run evidence into existing fill/concat Law.
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
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe_small_vector import observe_native_small_vector
from experiments.one.observe import RunOpportunity
from experiments.one.run_fill_law import MIN_FILL_RUN, program_from_observed_runs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (64 << 10, 256 << 10, 1 << 20)
REPETITIONS = 15
RUN_RICH = ("structured", "long_runs")
CONTROLS = ("compressed_like", "random", "near_repeats")
LONG_RUNS_1M_WIRE_MAX = 0.55
STRUCTURED_1M_WIRE_MAX = 0.90
RUN_RICH_TIME_MAX = 1.10
CONTROL_TIME_MAX = 1.05
READER_WORK_MAX = 1.05
ALLOWED_CURRENT_OPS = {"surprise", "fill", "concat"}


def _python_maximal_runs(data: bytes, min_run: int = 8) -> tuple[RunOpportunity, ...]:
    runs: list[RunOpportunity] = []
    i = 0
    n = len(data)
    while i < n:
        start = i
        value = data[i]
        i += 1
        while i < n and data[i] == value:
            i += 1
        length = i - start
        if length >= min_run:
            runs.append(RunOpportunity(start, length, value))
    return tuple(runs)


def _writer_once(source: bytes, target: bytes, candidate: bool):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    observer = observe_native_small_vector(target)
    observation = observer.materialize()
    if candidate:
        program, compiler_stats = program_from_observed_runs(
            source,
            target,
            observation.runs,
            current_digest=current_digest,
            previous_digest=previous_digest,
        )
    else:
        previous_root = Root(Ref(0), len(source), previous_digest)
        program, _depth = _literal_program(source, target, previous_root, current_digest)
        compiler_stats = None
    program.validate_shape()
    wire, wire_stats = _encode_program_growable_prevalidated(program)
    return program, wire, wire_stats, compiler_stats, observation


def _time_pair(source: bytes, target: bytes) -> tuple[float, float, float, float]:
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
        for rep in range(REPETITIONS):
            order = (False, True) if rep % 2 == 0 else (True, False)
            for candidate in order:
                # Destroy the preceding same-arm result before either clock starts so
                # Python object/wire teardown cannot be billed to the opposite arm.
                if candidate:
                    candidate_value = None
                else:
                    control_value = None
                c0 = time.process_time_ns()
                w0 = time.perf_counter_ns()
                value = _writer_once(source, target, candidate)
                w1 = time.perf_counter_ns()
                c1 = time.process_time_ns()
                if candidate:
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
        raise AssertionError("paired writer timing produced no value")
    return (
        float(statistics.median(control_walls)),
        float(statistics.median(control_cpus)),
        float(statistics.median(candidate_walls)),
        float(statistics.median(candidate_cpus)),
    )


def _child(size: int, family: str) -> dict:
    source, target = _case(family, size)
    oracle_runs = _python_maximal_runs(target)
    control_program, control_wire, control_ws, _control_cs, control_observation = _writer_once(source, target, False)
    candidate_program, candidate_wire, candidate_ws, candidate_cs, candidate_observation = _writer_once(source, target, True)
    if candidate_cs is None:
        raise AssertionError("candidate compiler stats missing")

    native_qualifying = tuple(run for run in candidate_observation.runs if run.length >= MIN_FILL_RUN)
    oracle_qualifying = tuple(run for run in oracle_runs if run.length >= MIN_FILL_RUN)
    oracle_exact = native_qualifying == oracle_qualifying
    observer_same = control_observation.runs == candidate_observation.runs and control_observation.reuse == candidate_observation.reuse

    control_outputs, control_vm = evaluate(decode_program(control_wire))
    candidate_outputs, candidate_vm = evaluate(decode_program(candidate_wire))
    reconstruction_exact = control_outputs == candidate_outputs == {"previous": source, "current": target}
    expected_previous_digest = sha256(source).hexdigest()
    expected_current_digest = sha256(target).hexdigest()
    roots_exact = (
        control_program.roots["previous"].sha256 == candidate_program.roots["previous"].sha256 == expected_previous_digest
        and control_program.roots["current"].sha256 == candidate_program.roots["current"].sha256 == expected_current_digest
        and control_program.roots["previous"].length == candidate_program.roots["previous"].length == len(source)
        and control_program.roots["current"].length == candidate_program.roots["current"].length == len(target)
    )
    ops_exact = all(node.op in ALLOWED_CURRENT_OPS for node in candidate_program.nodes)
    caps_ok = (
        len(candidate_program.nodes) <= candidate_program.limits.max_nodes
        and max((len(node.refs) for node in candidate_program.nodes), default=0) <= candidate_program.limits.max_nodes
    )
    semantic_ok = oracle_exact and observer_same and reconstruction_exact and roots_exact and ops_exact and caps_ok
    if not semantic_ok:
        raise AssertionError(f"observer-run/fill semantic mismatch: {size=} {family=}")

    # Preserve scalar authority, then release the large semantic-probe objects before
    # timing so retained Programs/wires do not perturb the allocation experiment.
    result_scalars = {
        "native_observer_runs": len(candidate_observation.runs),
        "qualifying_fill_runs": candidate_cs.qualifying_runs,
        "fill_bytes": candidate_cs.fill_bytes,
        "current_surprise_bytes": candidate_cs.surprise_bytes_current,
        "bounded": candidate_cs.bounded,
        "program_nodes": len(candidate_program.nodes),
        "concat_refs": candidate_cs.concat_refs,
        "control_wire_bytes": control_ws.total_bytes,
        "candidate_wire_bytes": candidate_ws.total_bytes,
        "control_surprise_bytes": control_ws.surprise_bytes,
        "candidate_surprise_bytes": candidate_ws.surprise_bytes,
        "control_reader_work_bytes": control_vm.work_bytes,
        "candidate_reader_work_bytes": candidate_vm.work_bytes,
    }
    del control_program, control_wire, candidate_program, candidate_wire, control_observation, candidate_observation
    gc.collect()

    control_wall, control_cpu, candidate_wall, candidate_cpu = _time_pair(source, target)

    wire_ratio = result_scalars["candidate_wire_bytes"] / result_scalars["control_wire_bytes"]
    surprise_ratio = result_scalars["candidate_surprise_bytes"] / result_scalars["control_surprise_bytes"]
    reader_work_ratio = (
        result_scalars["candidate_reader_work_bytes"] / result_scalars["control_reader_work_bytes"]
        if result_scalars["control_reader_work_bytes"] else 1.0
    )
    wall_ratio = candidate_wall / control_wall
    cpu_ratio = candidate_cpu / control_cpu
    bytes_eliminated = result_scalars["control_wire_bytes"] - result_scalars["candidate_wire_bytes"]
    added_wall_ms = (candidate_wall - control_wall) / 1e6
    added_cpu_ms = (candidate_cpu - control_cpu) / 1e6

    return {
        "bytes": size,
        "family": family,
        "semantic_ok": semantic_ok,
        **result_scalars,
        "candidate_over_control_wire": wire_ratio,
        "candidate_over_control_surprise": surprise_ratio,
        "candidate_over_control_reader_work": reader_work_ratio,
        "control_wall_median_ns": control_wall,
        "candidate_wall_median_ns": candidate_wall,
        "candidate_over_control_wall": wall_ratio,
        "control_cpu_median_ns": control_cpu,
        "candidate_cpu_median_ns": candidate_cpu,
        "candidate_over_control_cpu": cpu_ratio,
        "wire_bytes_eliminated": bytes_eliminated,
        "added_wall_ms": added_wall_ms,
        "added_cpu_ms": added_cpu_ms,
        "wire_bytes_eliminated_per_added_wall_ms": None if added_wall_ms <= 0 else bytes_eliminated / added_wall_ms,
        "wire_bytes_eliminated_per_added_cpu_ms": None if added_cpu_ms <= 0 else bytes_eliminated / added_cpu_ms,
    }


def _invoke(size: int, family: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_g02_observer_run_fill_law", "--child", str(size), family],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("observer-run/fill child produced no JSON")
    return json.loads(lines[-1])


def adjudicate(rows: list[dict]) -> str:
    expected = {(size, family) for size in SIZES for family in FAMILIES}
    actual = {(int(row["bytes"]), str(row["family"])) for row in rows}
    if len(rows) != len(expected) or actual != expected:
        return "INVALIDATE_OBSERVER_RUN_FILL_LAW"
    if not all(bool(row["semantic_ok"]) and bool(row["bounded"]) for row in rows):
        return "INVALIDATE_OBSERVER_RUN_FILL_LAW"
    if any(row["candidate_wire_bytes"] > row["control_wire_bytes"] for row in rows):
        return "HOLD_OBSERVER_RUN_FILL_LAW"
    if any(row["candidate_surprise_bytes"] > row["control_surprise_bytes"] for row in rows):
        return "HOLD_OBSERVER_RUN_FILL_LAW"
    if any(row["candidate_over_control_reader_work"] > READER_WORK_MAX for row in rows):
        return "HOLD_OBSERVER_RUN_FILL_LAW"

    long_1m = next(row for row in rows if row["bytes"] == (1 << 20) and row["family"] == "long_runs")
    structured_1m = next(row for row in rows if row["bytes"] == (1 << 20) and row["family"] == "structured")
    if long_1m["candidate_over_control_wire"] > LONG_RUNS_1M_WIRE_MAX:
        return "HOLD_OBSERVER_RUN_FILL_LAW"
    if structured_1m["candidate_over_control_wire"] > STRUCTURED_1M_WIRE_MAX:
        return "HOLD_OBSERVER_RUN_FILL_LAW"

    for row in rows:
        time_max = RUN_RICH_TIME_MAX if row["family"] in RUN_RICH else CONTROL_TIME_MAX
        if row["candidate_over_control_wall"] > time_max or row["candidate_over_control_cpu"] > time_max:
            return "HOLD_OBSERVER_RUN_FILL_LAW"
    return "ADVANCE_OBSERVER_RUN_FILL_LAW"


def run() -> dict:
    rows = [_invoke(size, family) for size in SIZES for family in FAMILIES]
    decision = adjudicate(rows)
    return {
        "schema": "cmpct-one-g02-observer-run-fill-law-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "families": list(FAMILIES),
        "repetitions_per_fresh_row": REPETITIONS,
        "min_fill_run": MIN_FILL_RUN,
        "long_runs_1m_wire_max": LONG_RUNS_1M_WIRE_MAX,
        "structured_1m_wire_max": STRUCTURED_1M_WIRE_MAX,
        "run_rich_time_max": RUN_RICH_TIME_MAX,
        "control_time_max": CONTROL_TIME_MAX,
        "reader_work_max": READER_WORK_MAX,
        "decision": decision,
        "claim_boundary": (
            "rejected-temporal-root intra-object maximal-run compiler only; existing surprise/fill/concat grammar; "
            "same native observation and root hashing in both arms; no authenticated placement, recovery, filesystem, "
            "portability, v0.29/v0.30, or Genesis supersession authority"
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
    return 0 if result["decision"] == "ADVANCE_OBSERVER_RUN_FILL_LAW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
