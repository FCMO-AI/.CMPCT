"""ONE-G0.2 paired post-counter residual attribution.

Referee freeze
==============
The existing post-counter cost ladder times all Gear, buffer/prefix, dense-suffix
and exact-selector repetitions in separate batches.  Exact-head reruns have
swapped the apparent largest residual between suffix construction and selection,
so a next Builder chosen from that ranking risks optimizing timer drift.

This instrument changes no algorithm.  For each large case and each adjacent
ladder pair it runs 9 warm-started A-B-B-A rounds and records the within-round
incremental ns/input-byte.  The next causal Builder may target a layer as the
`paired_dominant_owner` only when that layer has the largest cross-case median
increment AND every large case has positive median incremental cost.  Otherwise
the result is `no_stable_dominant_owner` and deeper attribution is required.

Ablation arms remain non-semantic diagnostics; the exact arm is independently
checked against the Python anchor oracle.  This creates no format, reader,
stored-byte or product-speed authority.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _python_anchor_trace
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_counter_cost_ladder import _CostResult, _bind, _call
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_residual import _bind_gear, _call_gear
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

ROUNDS = 9


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-counter-cost-paired-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_counter_cost_ladder.c"),
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _sample(fn) -> float:
    start = time.perf_counter_ns()
    fn()
    return float(time.perf_counter_ns() - start)


def _abba(a, b, nbytes: int) -> list[dict[str, float]]:
    a(); b()
    rows = []
    for _ in range(ROUNDS):
        a1 = _sample(a)
        b1 = _sample(b)
        b2 = _sample(b)
        a2 = _sample(a)
        am = (a1 + a2) * 0.5
        bm = (b1 + b2) * 0.5
        rows.append({
            "a_ns": am,
            "b_ns": bm,
            "ratio": bm / am,
            "incremental_ns_per_byte": (bm - am) / nbytes,
        })
    return rows


def run() -> dict[str, object]:
    lib, td = _build()
    try:
        gearfn = _bind_gear(lib)
        buffn = _bind(lib, "one_g02_counter_buffer_prefix_cost_kernel")
        suffn = _bind(lib, "one_g02_counter_dense_suffix_cost_kernel")
        exactfn = _bind_counter(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        layers = (
            ("buffer_prefix", gearfn, _call_gear, buffn, _call),
            ("dense_suffix", buffn, _call, suffn, _call),
            ("exact_selection", suffn, _call, exactfn, _call_counter),
        )
        rows: list[dict[str, object]] = []
        per_layer: dict[str, list[float]] = {name: [] for name, *_ in layers}

        for case_name, data in _cases().items():
            if case_name not in LARGE_CASES:
                continue
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            exact = _call_counter(exactfn, gear, arr, len(data))
            if int(exact.final_state) != expected_state or int(exact.positions_considered) != expected_considered or int(exact.emitted) != len(expected_trace):
                raise AssertionError(f"exact selector semantic mismatch: {case_name}")

            for layer, afn, acall, bfn, bcall in layers:
                a = lambda fn=afn, call=acall: call(fn, gear, arr, len(data))
                b = lambda fn=bfn, call=bcall: call(fn, gear, arr, len(data))
                rounds = _abba(a, b, len(data))
                deltas = [r["incremental_ns_per_byte"] for r in rounds]
                ratios = [r["ratio"] for r in rounds]
                median_delta = float(statistics.median(deltas))
                per_layer[layer].append(median_delta)
                rows.append({
                    "case": case_name,
                    "layer": layer,
                    "input_bytes": len(data),
                    "rounds": ROUNDS,
                    "median_incremental_ns_per_byte": median_delta,
                    "median_ratio": float(statistics.median(ratios)),
                    "min_incremental_ns_per_byte": min(deltas),
                    "max_incremental_ns_per_byte": max(deltas),
                    "round_samples": rounds,
                })

        medians = {layer: float(statistics.median(values)) for layer, values in per_layer.items()}
        candidate = max(medians, key=medians.get)
        stable = medians[candidate] > 0.0 and all(v > 0.0 for v in per_layer[candidate])
        decision = candidate if stable else "no_stable_dominant_owner"
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"paired_dominant_owner={decision}\n")
        return {
            "schema": "cmpct-one-g02-counter-cost-paired-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "protocol": "9 warm-started adjacent-layer A-B-B-A rounds per large case",
            "cross_case_median_incremental_ns_per_byte": medians,
            "paired_dominant_owner": decision,
            "interpretation_rule": "diagnostic owner only when largest median layer is positive on every large case",
            "claim_boundary": "non-semantic residual attribution; no implementation promotion or product-speed authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
