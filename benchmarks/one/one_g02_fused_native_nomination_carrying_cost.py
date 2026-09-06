"""ONE-G0.2 paired native carrying-cost gate for fused nomination.

Frozen by ONE_G02_FUSED_NATIVE_NOMINATION_CARRYING_COST_PREREG_2026-09-06.md.
All timed arms enter one C wrapper once per sample.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_relation_shared_observer_validation import MINIMIZER_SPAN, _cases

SIZES = (64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
WINDOW = 64
ROUNDS = 31
WARMUP = 5
CASES = (
    "shift_plus1",
    "damage_quarter",
    "fragmented_every96",
    "hostile_fixed_bands",
    "fragmented_every32",
    "independent_random",
)
NEGATIVES = {"fragmented_every32", "independent_random"}


class Summary(ctypes.Structure):
    _fields_ = [
        ("anchors", ctypes.c_uint64),
        ("cross_auditions", ctypes.c_uint64),
        ("cross_exact", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fused-nomination-cost-")
    lib = Path(td.name) / "libcost.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_native_nomination_event_consumer_kernel.c"),
            str(here / "one_g02_fused_native_nomination_kernel.c"),
            str(here / "one_g02_fused_native_nomination_timing_wrapper.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    selector = c.one_g02_timing_selector_only
    selector.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(Summary),
    ]
    selector.restype = ctypes.c_int
    two_stage = c.one_g02_timing_two_stage
    fused = c.one_g02_timing_fused
    for fn in (two_stage, fused):
        fn.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(Summary),
        ]
        fn.restype = ctypes.c_int
    return selector, two_stage, fused, td


def _call(fn, buf, length: int, boundary: int, gear, *, selector: bool = False) -> Summary:
    out = Summary()
    if selector:
        rc = fn(buf, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    else:
        rc = fn(buf, length, boundary, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"native timing wrapper failed: rc={rc}")
    return out


def _ns(fn) -> int:
    start = time.perf_counter_ns()
    fn()
    return time.perf_counter_ns() - start


def run() -> dict[str, object]:
    selector, two_stage, fused, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows = []
    semantic_mismatches = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                generated = _cases(size, seed)
                for name in CASES:
                    source, target = generated[name]
                    data = source + target
                    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                    boundary = len(source)

                    selector_out = _call(selector, buf, len(data), boundary, gear, selector=True)
                    two_out = _call(two_stage, buf, len(data), boundary, gear)
                    fused_out = _call(fused, buf, len(data), boundary, gear)
                    if (
                        two_out.anchors != fused_out.anchors
                        or two_out.cross_auditions != fused_out.cross_auditions
                        or two_out.cross_exact != fused_out.cross_exact
                        or two_out.final_state != fused_out.final_state
                        or selector_out.anchors != fused_out.anchors
                        or selector_out.final_state != fused_out.final_state
                    ):
                        semantic_mismatches.append((size, seed, name))

                    for _ in range(WARMUP):
                        _call(selector, buf, len(data), boundary, gear, selector=True)
                        _call(two_stage, buf, len(data), boundary, gear)
                        _call(fused, buf, len(data), boundary, gear)

                    selector_samples: list[int] = []
                    two_samples: list[int] = []
                    fused_samples: list[int] = []
                    for round_index in range(ROUNDS):
                        selector_samples.append(_ns(lambda: _call(selector, buf, len(data), boundary, gear, selector=True)))
                        if round_index % 2 == 0:
                            two_samples.append(_ns(lambda: _call(two_stage, buf, len(data), boundary, gear)))
                            fused_samples.append(_ns(lambda: _call(fused, buf, len(data), boundary, gear)))
                        else:
                            fused_samples.append(_ns(lambda: _call(fused, buf, len(data), boundary, gear)))
                            two_samples.append(_ns(lambda: _call(two_stage, buf, len(data), boundary, gear)))

                    selector_median = statistics.median(selector_samples)
                    two_median = statistics.median(two_samples)
                    fused_median = statistics.median(fused_samples)
                    rows.append({
                        "relation_bytes": size,
                        "seed": seed,
                        "case": name,
                        "cross_exact": int(fused_out.cross_exact),
                        "selector_median_ns": selector_median,
                        "two_stage_median_ns": two_median,
                        "fused_median_ns": fused_median,
                        "fused_over_two_stage": fused_median / two_median,
                        "fused_over_selector_only": fused_median / selector_median,
                        "selector_samples_ns": selector_samples,
                        "two_stage_samples_ns": two_samples,
                        "fused_samples_ns": fused_samples,
                    })

        ratios = [float(r["fused_over_two_stage"]) for r in rows]
        selector_ratios = [float(r["fused_over_selector_only"]) for r in rows]
        negative_ratios = [
            float(r["fused_over_two_stage"]) for r in rows if r["case"] in NEGATIVES
        ]
        cross_median = statistics.median(ratios)
        worst = max(ratios)
        worst_negative = max(negative_ratios)
        selector_premium_median = statistics.median(selector_ratios)

        if semantic_mismatches or cross_median >= 1.0 or worst_negative > 1.05:
            decision = "retire_fused_nomination_hot_path"
        elif cross_median <= 0.90 and worst <= 1.05 and worst_negative <= 1.0:
            decision = "advance_fused_nomination_state_rehabilitation"
        else:
            decision = "hold_fused_nomination_state_rehabilitation"

        return {
            "schema": "cmpct-one-g02-fused-native-nomination-carrying-cost-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "warmup": WARMUP,
            "semantic_mismatches": semantic_mismatches,
            "cross_large_median_fused_over_two_stage": cross_median,
            "worst_fused_over_two_stage": worst,
            "worst_negative_fused_over_two_stage": worst_negative,
            "median_fused_over_selector_only": selector_premium_median,
            "fixed_research_event_index_storage_bytes": 198144,
            "decision": decision,
            "rows": rows,
            "claim_boundary": (
                "hosted native carrying-cost evidence for fixed-index research shape; same semantics vs two-stage, "
                "but state debt blocks product promotion regardless of elapsed result"
            ),
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "retire_fused_nomination_hot_path" else 1)
