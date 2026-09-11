"""ONE-G0.2 dense-size diagnostic for packed observer mid-size regression debt."""
from __future__ import annotations

import ctypes
from hashlib import sha256
import json
import os

from benchmarks.one.one_g02_compact_observer_handoff_writer import (
    FAMILIES,
    REPETITIONS,
    Segment,
    _build_native,
    _case,
    _same_writer_result,
)
from benchmarks.one.one_g02_packed_observer_rehabilitation import _time_pair, _writer_once
from experiments.one.native_observe import observe_native
from experiments.one.native_observe_view import observe_native_packed
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES_DIAGNOSTIC = (128 << 10, 192 << 10, 256 << 10, 384 << 10, 512 << 10, 768 << 10, 1 << 20)
RED_MAX = 1.05


def _row_state(row: dict) -> str:
    wall_red = row["packed_over_eager_wall"] > RED_MAX
    cpu_red = row["packed_over_eager_cpu"] > RED_MAX
    if wall_red and cpu_red:
        return "RED"
    if not wall_red and not cpu_red:
        return "CLEAR"
    return "AMBIGUOUS"


def _classify(rows: list[dict], family: str) -> str:
    by_size = {row["bytes"]: row for row in rows if row["family"] == family}
    r192 = _row_state(by_size[192 << 10])
    r256 = _row_state(by_size[256 << 10])
    r384 = _row_state(by_size[384 << 10])
    if r256 == "CLEAR":
        return "NO_256K_RED_ON_REPEAT"
    if r256 != "RED":
        return "AMBIGUOUS"
    if r192 == "RED" or r384 == "RED":
        return "STABLE_ADJACENT_REGRESSION"
    if r192 == "CLEAR" and r384 == "CLEAR":
        return "ISOLATED_256K_RED"
    return "AMBIGUOUS"


def run() -> dict:
    admission_fn, segment_fn, td = _build_native()
    rows: list[dict] = []
    semantic_ok = True
    try:
        for size in SIZES_DIAGNOSTIC:
            for family in FAMILIES:
                source, target = _case(family, size)
                packed_authority = observe_native_packed(target)
                observer_exact = packed_authority.materialize() == observe_native(target)
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                eager = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, False)
                packed = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, True)
                writer_exact = _same_writer_result(eager, packed)
                decoded = decode_program(packed["wire"])
                outputs, _ = evaluate(decoded)
                roots_exact = (
                    packed["program"].roots["previous"].sha256 == sha256(source).hexdigest()
                    and packed["program"].roots["current"].sha256 == sha256(target).hexdigest()
                )
                reconstruction_exact = outputs == {"previous": source, "current": target}
                this_semantic = observer_exact and writer_exact and roots_exact and reconstruction_exact
                semantic_ok &= this_semantic
                if not this_semantic:
                    raise AssertionError(f"size-debt semantic mismatch: {size=} {family=}")

                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
                ew, ec, ev, pw, pc, pv = _time_pair(ctx)
                timed_exact = _same_writer_result(ev, pv)
                if not timed_exact:
                    raise AssertionError(f"size-debt timed mismatch: {size=} {family=}")
                row = {
                    "bytes": size,
                    "family": family,
                    "observer_exact": observer_exact,
                    "writer_exact": writer_exact,
                    "timed_writer_exact": timed_exact,
                    "root_hashes_exact": roots_exact,
                    "exact_reconstruction": reconstruction_exact,
                    "observer_run_count": pv["observer_counts"][0],
                    "observer_reuse_count": pv["observer_counts"][1],
                    "observer_native_scratch_capacity_bytes": pv["observer_output_capacity_bytes"],
                    "observer_native_output_used_bytes": pv["observer_output_used_bytes"],
                    "observer_packed_retained_bytes": pv["observer_retained_output_bytes"],
                    "eager_writer_wall_median_ns": ew,
                    "eager_writer_cpu_median_ns": ec,
                    "packed_writer_wall_median_ns": pw,
                    "packed_writer_cpu_median_ns": pc,
                    "packed_over_eager_wall": pw / ew,
                    "packed_over_eager_cpu": pc / ec,
                }
                row["state"] = _row_state(row)
                rows.append(row)
        classifications = {family: _classify(rows, family) for family in FAMILIES}
        return {
            "schema": "cmpct-one-g02-packed-observer-size-debt-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "sizes": list(SIZES_DIAGNOSTIC),
            "families": list(FAMILIES),
            "red_max": RED_MAX,
            "semantic_gates_pass": semantic_ok,
            "classifications": classifications,
            "claim_boundary": (
                "dense-size diagnostic only; no size selector or production threshold; same packed/eager writer "
                "boundary and semantics as rehabilitation result; no stored-format, reader, RSS, v0.29/v0.30 authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["semantic_gates_pass"] else 1)
