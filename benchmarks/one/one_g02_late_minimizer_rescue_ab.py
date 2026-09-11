"""ONE-G0.2 paired elapsed falsifier for the fixed starvation-gated minimizer rescue.

The opportunity experiment showed that cold activation after a 4,096-position sparse-anchor
gap preserves the only currently observed hard-rescue relation.  This experiment charges the
actual Python reference work rather than treating rescue-active fraction as speed evidence.

The gate and corpus are frozen from the preceding experiment.  No threshold is tuned here.
A/B order alternates each round to reduce temporal runner bias.  These are hosted causal
measurements, not native/product-speed authority.
"""
from __future__ import annotations

import gc
import json
import os
import random
import statistics
import time
import zlib

from benchmarks.one.one_g02_gear_replacement_ab import _cases
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_late_minimizer_rescue import _late_rescue_observe

ROUNDS = 9


def _measure(fn):
    gc.disable()
    try:
        t0 = time.perf_counter_ns()
        result = fn()
        return time.perf_counter_ns() - t0, result
    finally:
        gc.enable()


def _paired(data: bytes) -> dict[str, object]:
    full_samples: list[int] = []
    rescue_samples: list[int] = []
    full = rescue = None
    for round_index in range(ROUNDS):
        if round_index % 2 == 0:
            ns, full = _measure(lambda: _minimizer_observe(data)); full_samples.append(ns)
            ns, rescue = _measure(lambda: _late_rescue_observe(data)); rescue_samples.append(ns)
        else:
            ns, rescue = _measure(lambda: _late_rescue_observe(data)); rescue_samples.append(ns)
            ns, full = _measure(lambda: _minimizer_observe(data)); full_samples.append(ns)
    assert full is not None and rescue is not None
    full_median = int(statistics.median(full_samples))
    rescue_median = int(statistics.median(rescue_samples))
    return {
        "full_minimizer_median_ns": full_median,
        "late_rescue_median_ns": rescue_median,
        "late_rescue_elapsed_ratio_over_full": rescue_median / full_median,
        "full_minimizer_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
        "late_rescue_reuse_opportunity_bytes": rescue.reuse_opportunity_bytes,
        "rescue_active_positions": rescue.rescue_active_positions,
        "rescue_active_fraction": rescue.rescue_active_positions / len(data) if data else 0.0,
        "peak_rescue_queue_entries": rescue.peak_queue_entries,
        "late_verification_read_bytes": rescue.verification_read_bytes,
        "late_extension_read_bytes": rescue.extension_read_bytes,
        "full_samples_ns": full_samples,
        "late_samples_ns": rescue_samples,
    }


def run() -> dict[str, object]:
    base = _cases()
    starved = random.Random(4876).randbytes(8 * 1024)
    cases = {
        "random_1mib": base["random_1mib"],
        "zlib_random_payload": base["zlib_random_payload"],
        "repeat_basis_64k_1mib": base["repeat_basis_64k_1mib"],
        "shifted_version_pair_1byte_insert": base["shifted_version_pair_1byte_insert"],
        "starved_shifted_basis_8k_insert1": starved + b"X" + starved,
    }
    rows = []
    hard_loss = []
    for name, data in cases.items():
        row = {"case": name, "input_bytes": len(data), **_paired(data)}
        if name == "starved_shifted_basis_8k_insert1" and row["late_rescue_reuse_opportunity_bytes"] < row["full_minimizer_reuse_opportunity_bytes"]:
            hard_loss.append(name)
        rows.append(row)

    negative_rows = [r for r in rows if r["case"] in {"random_1mib", "zlib_random_payload"}]
    negative_median_ratio = statistics.median(r["late_rescue_elapsed_ratio_over_full"] for r in negative_rows)
    return {
        "schema": "cmpct-one-g02-late-minimizer-rescue-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rounds": ROUNDS,
        "frozen_gate_gap_positions": 4096,
        "hypothesis": "the fixed starvation gate converts the observed low negative-path activation into a material elapsed reduction while preserving the hard-rescue relation",
        "disproof": "hard-rescue opportunity loss or no material paired elapsed advantage on the random/compressed negative controls rejects performance promotion",
        "hard_rescue_loss_cases": hard_loss,
        "negative_control_median_elapsed_ratio": negative_median_ratio,
        "decision": (
            "advance_late_rescue_compute_rehabilitation"
            if not hard_loss and negative_median_ratio < 0.9
            else "reject_or_rehabilitate_late_rescue_compute_shape"
        ),
        "claim_boundary": "hosted Python causal A/B only; no native/product-speed, stored-byte, reader-format or release authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
