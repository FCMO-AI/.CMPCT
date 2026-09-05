"""ONE-G0.2 paired carrying-cost review for deferred minimizer materialization.

Semantic transfer is already established separately.  This experiment charges the always-on
bounded Gear-history writes and on-demand materialization against the full rolling minimizer.
It does not tune the 4,096-position gate or history horizon. Alternating paired order reduces
runner drift. Hosted Python timing is causal architecture evidence only.
"""
from __future__ import annotations

import gc
import json
import os
import random
import statistics
import time

from benchmarks.one.one_g02_gear_replacement_ab import _cases
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_deferred_minimizer_rescue import _deferred_rescue_observe

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
    deferred_samples: list[int] = []
    full = deferred = None
    for i in range(ROUNDS):
        if i % 2 == 0:
            ns, full = _measure(lambda: _minimizer_observe(data)); full_samples.append(ns)
            ns, deferred = _measure(lambda: _deferred_rescue_observe(data)); deferred_samples.append(ns)
        else:
            ns, deferred = _measure(lambda: _deferred_rescue_observe(data)); deferred_samples.append(ns)
            ns, full = _measure(lambda: _minimizer_observe(data)); full_samples.append(ns)
    assert full is not None and deferred is not None
    full_median = int(statistics.median(full_samples))
    deferred_median = int(statistics.median(deferred_samples))
    return {
        "full_median_ns": full_median,
        "deferred_median_ns": deferred_median,
        "deferred_elapsed_ratio_over_full": deferred_median / full_median,
        "full_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
        "deferred_reuse_opportunity_bytes": deferred.reuse_opportunity_bytes,
        "history_payload_bytes": deferred.history_payload_bytes,
        "materialization_input_entries": deferred.materialization_input_entries,
        "rescue_active_positions": deferred.rescue_active_positions,
        "verification_read_bytes": deferred.verification_read_bytes,
        "extension_read_bytes": deferred.extension_read_bytes,
        "full_samples_ns": full_samples,
        "deferred_samples_ns": deferred_samples,
    }


def run() -> dict[str, object]:
    base = _cases()
    transfer_basis = random.Random(10).randbytes(4096)
    cases = {
        "random_1mib": base["random_1mib"],
        "zlib_random_payload": base["zlib_random_payload"],
        "repeat_basis_64k_1mib": base["repeat_basis_64k_1mib"],
        "shifted_version_pair_1byte_insert": base["shifted_version_pair_1byte_insert"],
        "transfer_starved_seed10_insert1": transfer_basis + b"X" + transfer_basis,
    }
    rows = [{"case": name, "input_bytes": len(data), **_paired(data)} for name, data in cases.items()]
    negative = [r for r in rows if r["case"] in {"random_1mib", "zlib_random_payload"}]
    neg_ratio = statistics.median(r["deferred_elapsed_ratio_over_full"] for r in negative)
    hard = next(r for r in rows if r["case"] == "transfer_starved_seed10_insert1")
    hard_preserved = hard["deferred_reuse_opportunity_bytes"] >= hard["full_reuse_opportunity_bytes"]
    return {
        "schema": "cmpct-one-g02-deferred-rescue-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rounds": ROUNDS,
        "hypothesis": "deferred materialization preserves the hard transfer relation while retaining a material elapsed advantage over always-on minimizer maintenance on entropy-dense controls",
        "disproof": "hard opportunity loss or negative-control median elapsed ratio >= 0.9 rejects this Python execution shape for performance advancement",
        "negative_control_median_elapsed_ratio": neg_ratio,
        "hard_transfer_preserved": hard_preserved,
        "decision": "advance_deferred_compute_shape" if hard_preserved and neg_ratio < 0.9 else "reject_or_rehabilitate_deferred_compute_shape",
        "claim_boundary": "hosted Python paired causal evidence; complete Python object RSS is not modeled by history_payload_bytes; no native/product or release authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
