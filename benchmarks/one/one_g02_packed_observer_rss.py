"""ONE-G0.2 fresh-process peak-RSS gate for the packed observer handoff.

Frozen by ONE_G02_PACKED_OBSERVER_RSS_PREREG_2026-09-08.md.
"""
from __future__ import annotations

import argparse
import ctypes
from hashlib import sha256
import json
import os
import resource
import statistics
import subprocess
import sys

from benchmarks.one.one_g02_compact_observer_handoff_writer import (
    FAMILIES,
    Segment,
    _build_native,
    _case,
    _same_writer_result,
)
from benchmarks.one.one_g02_packed_observer_rehabilitation import _writer_once
from experiments.one.native_observe import observe_native
from experiments.one.native_observe_view import observe_native_packed
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZE = 1 << 20
REPETITIONS = 7
RSS_NO_REGRESSION_MAX = 1.05
STRUCTURED_REDUCTION_MAX = 0.95


def _rss_kib() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS reports bytes. Hosted authority is Ubuntu, but keep local
    # diagnostics comparable rather than silently changing units.
    if sys.platform == "darwin":
        value //= 1024
    return value


def _child(arm: str, family: str) -> dict:
    source, target = _case(family, SIZE)
    admission_fn, segment_fn, td = _build_native()
    try:
        src_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(source)
        dst_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(target)
        seg_buf = (Segment * SIZE)()
        before_kib = _rss_kib()
        value = _writer_once(
            admission_fn,
            segment_fn,
            source,
            target,
            src_arr,
            dst_arr,
            seg_buf,
            arm == "packed",
        )
        peak_kib = _rss_kib()
        decoded = decode_program(value["wire"])
        outputs, _ = evaluate(decoded)
        semantic_ok = (
            outputs == {"previous": source, "current": target}
            and value["program"].roots["previous"].sha256 == sha256(source).hexdigest()
            and value["program"].roots["current"].sha256 == sha256(target).hexdigest()
        )
        return {
            "arm": arm,
            "family": family,
            "peak_rss_kib": peak_kib,
            "pre_writer_peak_rss_kib": before_kib,
            "writer_incremental_peak_kib": max(0, peak_kib - before_kib),
            "semantic_ok": semantic_ok,
            "observer_run_count": value["observer_counts"][0],
            "observer_reuse_count": value["observer_counts"][1],
            "observer_output_capacity_bytes": value["observer_output_capacity_bytes"],
            "observer_output_used_bytes": value["observer_output_used_bytes"],
            "observer_retained_output_bytes": value["observer_retained_output_bytes"],
            "canonical_wire_bytes": value["wire_stats"].total_bytes,
            "surprise_bytes": value["wire_stats"].surprise_bytes,
        }
    finally:
        td.cleanup()


def _authority() -> bool:
    admission_fn, segment_fn, td = _build_native()
    ok = True
    try:
        for family in FAMILIES:
            source, target = _case(family, SIZE)
            packed = observe_native_packed(target)
            ok &= packed.materialize() == observe_native(target)
            src_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(source)
            dst_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(target)
            seg_buf = (Segment * SIZE)()
            eager = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, False)
            candidate = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, True)
            ok &= _same_writer_result(eager, candidate)
            decoded = decode_program(candidate["wire"])
            outputs, _ = evaluate(decoded)
            ok &= outputs == {"previous": source, "current": target}
        return bool(ok)
    finally:
        td.cleanup()


def _invoke_child(arm: str, family: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_g02_packed_observer_rss", "--child", arm, family],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("RSS child produced no result")
    return json.loads(lines[-1])


def run() -> dict:
    semantic_ok = _authority()
    rows = []
    child_semantic_ok = True
    for family in FAMILIES:
        samples = {"eager": [], "packed": []}
        increments = {"eager": [], "packed": []}
        last = {}
        for repetition in range(REPETITIONS):
            order = ("eager", "packed") if repetition % 2 == 0 else ("packed", "eager")
            for arm in order:
                result = _invoke_child(arm, family)
                child_semantic_ok &= bool(result["semantic_ok"])
                samples[arm].append(int(result["peak_rss_kib"]))
                increments[arm].append(int(result["writer_incremental_peak_kib"]))
                last[arm] = result
        eager_median = float(statistics.median(samples["eager"]))
        packed_median = float(statistics.median(samples["packed"]))
        eager_inc = float(statistics.median(increments["eager"]))
        packed_inc = float(statistics.median(increments["packed"]))
        rows.append({
            "family": family,
            "eager_peak_rss_kib_median": eager_median,
            "packed_peak_rss_kib_median": packed_median,
            "packed_over_eager_peak_rss": packed_median / eager_median,
            "eager_writer_incremental_peak_kib_median": eager_inc,
            "packed_writer_incremental_peak_kib_median": packed_inc,
            "observer_run_count": last["packed"]["observer_run_count"],
            "observer_reuse_count": last["packed"]["observer_reuse_count"],
            "observer_native_scratch_capacity_bytes": last["packed"]["observer_output_capacity_bytes"],
            "observer_native_output_used_bytes": last["packed"]["observer_output_used_bytes"],
            "observer_packed_retained_bytes": last["packed"]["observer_retained_output_bytes"],
            "canonical_wire_bytes": last["packed"]["canonical_wire_bytes"],
            "surprise_bytes": last["packed"]["surprise_bytes"],
        })

    semantic_ok = semantic_ok and child_semantic_ok
    no_regression = all(row["packed_over_eager_peak_rss"] <= RSS_NO_REGRESSION_MAX for row in rows)
    structured = next(row for row in rows if row["family"] == "structured")
    structured_reduction = structured["packed_over_eager_peak_rss"] <= STRUCTURED_REDUCTION_MAX
    if not semantic_ok:
        decision = "INVALIDATE_PACKED_OBSERVER_RSS_GATE"
    elif no_regression:
        decision = "ADVANCE_PACKED_OBSERVER_RSS_SAFE"
    else:
        decision = "HOLD_PACKED_OBSERVER_RSS"
    return {
        "schema": "cmpct-one-g02-packed-observer-rss-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "size": SIZE,
        "repetitions": REPETITIONS,
        "families": list(FAMILIES),
        "rss_unit": "KiB",
        "rss_no_regression_max": RSS_NO_REGRESSION_MAX,
        "structured_reduction_max": STRUCTURED_REDUCTION_MAX,
        "semantic_gates_pass": semantic_ok,
        "all_rows_rss_no_regression": no_regression,
        "structured_rss_reduction": structured_reduction,
        "decision": decision,
        "claim_boundary": (
            "fresh-process 1 MiB research-writer RSS only; absolute ru_maxrss includes interpreter/native-library/"
            "input/segment/common writer state; packed still pays the same worst-case observer scratch peak; no "
            "256 KiB speed rehabilitation, stored-format, reader, product-memory, durability, recovery, portability, "
            "or v0.29/v0.30 authority"
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", nargs=2, metavar=("ARM", "FAMILY"))
    args = parser.parse_args()
    if args.child:
        arm, family = args.child
        if arm not in {"eager", "packed"} or family not in FAMILIES:
            raise SystemExit(2)
        print(json.dumps(_child(arm, family), sort_keys=True))
        return 0
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_PACKED_OBSERVER_RSS_SAFE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
