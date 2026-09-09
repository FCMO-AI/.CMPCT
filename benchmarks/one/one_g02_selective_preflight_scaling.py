"""ONE-G0.2 fixed-cone selective preflight scaling falsifier.

This diagnostic asks whether authenticated/native selective planning remains CPU-proportional
to the requested cone when unrelated, valid ONE nodes are added to the same Program.
It changes no promotion threshold and no reader semantics. Its purpose is to localize a
possible whole-Program validation tax before attempting a validated-plan/certificate design.
"""
from __future__ import annotations

import gc
import json
import statistics
import time

from benchmarks.one.one_g02_native_law_terminal_reader import _case
from experiments.one.ir import Node, Program
from experiments.one.native_law_range_plan import compile_native_law_range_plan

ROOT_BYTES = 128 * 1024
REQUEST_START = 0
REQUEST_BYTES = 4096
DEAD_NODE_COUNTS = (0, 64, 256, 1024, 4096)
ROUNDS = 11


def _with_unrelated_nodes(base: Program, count: int) -> Program:
    # Valid unreachable nodes are intentional. ONE's current preflight validates every stored
    # node so archive validity does not depend on which root happens to be requested.
    nodes = list(base.nodes)
    for i in range(count):
        payload = bytes(((i * 17 + j) & 0xFF) for j in range(32))
        nodes.append(Node("surprise", surprise=payload, declared_length=len(payload)))
    return Program(tuple(nodes), base.roots, base.limits)


def _median_cpu_ns(fn) -> int:
    fn()
    samples = []
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(ROUNDS):
            c0 = time.process_time_ns()
            fn()
            samples.append(time.process_time_ns() - c0)
    finally:
        if was_enabled:
            gc.enable()
    return int(statistics.median(samples))


def run():
    rows = []
    for family in ("add8", "xor"):
        base = _case(ROOT_BYTES, family)
        baseline_ns = None
        for dead_nodes in DEAD_NODE_COUNTS:
            program = _with_unrelated_nodes(base, dead_nodes)
            cpu_ns = _median_cpu_ns(
                lambda p=program: compile_native_law_range_plan(
                    p, "current", REQUEST_START, REQUEST_BYTES
                )
            )
            if baseline_ns is None:
                baseline_ns = cpu_ns
            rows.append(
                {
                    "family": family,
                    "root_bytes": ROOT_BYTES,
                    "request_bytes": REQUEST_BYTES,
                    "unrelated_nodes": dead_nodes,
                    "program_nodes": len(program.nodes),
                    "compile_cpu_ns": cpu_ns,
                    "over_zero_unrelated": cpu_ns / max(baseline_ns, 1),
                }
            )

    summaries = {}
    for family in ("add8", "xor"):
        group = [r for r in rows if r["family"] == family]
        first, last = group[0], group[-1]
        summaries[family] = {
            "zero_unrelated_cpu_ns": first["compile_cpu_ns"],
            "max_unrelated_cpu_ns": last["compile_cpu_ns"],
            "max_over_zero_unrelated": last["over_zero_unrelated"],
        }

    # This is a cost-owner diagnostic, not an ADVANCE gate. A strong monotonic rise falsifies
    # the stronger interpretation that fixed-cone open CPU is independent of unrelated graph size.
    monotonic = {}
    for family in ("add8", "xor"):
        vals = [r["compile_cpu_ns"] for r in rows if r["family"] == family]
        monotonic[family] = all(b >= a for a, b in zip(vals, vals[1:]))

    return {
        "schema": "cmpct-one-g02-selective-preflight-scaling-v1",
        "experimental_version": "ONE-G0.2",
        "root_bytes": ROOT_BYTES,
        "request_bytes": REQUEST_BYTES,
        "rounds": ROUNDS,
        "dead_node_counts": DEAD_NODE_COUNTS,
        "summary": {
            "families": summaries,
            "monotonic_cpu_growth": monotonic,
            "interpretation": (
                "If compile CPU rises materially with unrelated nodes while request/cone bytes stay fixed, "
                "whole-Program preflight is a selective-open cost owner. Rehabilitation must preserve full "
                "validation, likely by reusing authenticated immutable validation metadata rather than skipping checks."
            ),
        },
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
