from __future__ import annotations

"""Research-only timing decomposition for the exact C25EG08 v7 Office executor.

The accepted candidate already wins the frozen Office size contract but remains slower
than ZIP to create.  This oracle does not invent another encoder.  It instruments the
exact v7 candidate helper and measures the existing mandatory phases separately so the
next optimization can remove a whole owner rather than move benchmark accounting.

Archive bytes, selected levels, source-tree proof boundary, strong verification,
locality/recovery semantics, comparators and all promotion thresholds are inherited
unchanged from v7.  No timing component is moved outside the v7 measured boundary.
"""

import argparse
import json
from pathlib import Path
import statistics
import time
import traceback

from benchmarks import v030_federated_compact_framing_v8_policy_exec_v7 as V7
from benchmarks import v030_federated_compact_framing_v8_policy_exec_v6 as V6


_ORIGINAL = V7._ORIGINAL_CANDIDATE_ONCE


def _instrumented_candidate_once(stage: Path, root: Path, rules: list[dict], reference: bytes, vector: tuple[int, ...]) -> dict:
    timings = {"profile_prepare_s": 0.0, "strong_verify_s": 0.0, "locality_s": 0.0}
    counts = {"profile_prepare": 0, "strong_verify": 0, "locality": 0}

    prepare_owner = V6.DV5.EG07_EFFORT
    original_prepare = prepare_owner._prepare
    original_verify = V6.EG08.strong_verify
    original_locality = V6.EG08.locality_report

    def timed_prepare(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_prepare(*args, **kwargs)
        finally:
            timings["profile_prepare_s"] += time.perf_counter() - started
            counts["profile_prepare"] += 1

    def timed_verify(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_verify(*args, **kwargs)
        finally:
            timings["strong_verify_s"] += time.perf_counter() - started
            counts["strong_verify"] += 1

    def timed_locality(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_locality(*args, **kwargs)
        finally:
            timings["locality_s"] += time.perf_counter() - started
            counts["locality"] += 1

    prepare_owner._prepare = timed_prepare
    V6.EG08.strong_verify = timed_verify
    V6.EG08.locality_report = timed_locality
    try:
        measured = dict(_ORIGINAL(stage, root, rules, reference, vector))
    finally:
        prepare_owner._prepare = original_prepare
        V6.EG08.strong_verify = original_verify
        V6.EG08.locality_report = original_locality

    total = float(measured["verified_create_s"])
    known = (
        float(timings["profile_prepare_s"])
        + float(measured["graph_s"])
        + float(measured["parallel_compression_s"])
        + float(measured["publication_s"])
        + float(timings["strong_verify_s"])
        + float(timings["locality_s"])
    )
    measured["stage_breakdown"] = {
        **{key: float(value) for key, value in timings.items()},
        "graph_s": float(measured["graph_s"]),
        "parallel_compression_s": float(measured["parallel_compression_s"]),
        "publication_s": float(measured["publication_s"]),
        "residual_s": float(max(0.0, total - known)),
        "accounted_s": float(known),
        "accounted_fraction": float(min(1.0, known / total)) if total > 0 else 0.0,
        "calls": counts,
    }
    return measured


def run(work_root: Path) -> dict:
    samples: list[dict] = []
    original = V7._ORIGINAL_CANDIDATE_ONCE

    def capture(*args, **kwargs):
        row = _instrumented_candidate_once(*args, **kwargs)
        samples.append(dict(row["stage_breakdown"]))
        return row

    V7._ORIGINAL_CANDIDATE_ONCE = capture
    try:
        result = dict(V7.run(work_root))
    finally:
        V7._ORIGINAL_CANDIDATE_ONCE = original

    if len(samples) != int(V6.ROUNDS):
        raise RuntimeError(f"expected {V6.ROUNDS} measured candidate rounds, observed {len(samples)}")

    stage_keys = (
        "profile_prepare_s",
        "graph_s",
        "parallel_compression_s",
        "publication_s",
        "strong_verify_s",
        "locality_s",
        "residual_s",
    )
    medians = {key: float(statistics.median(float(row[key]) for row in samples)) for key in stage_keys}
    total = float(result["measured_candidate"]["median_verified_create_s"])
    zip_s = float(result["comparators"]["zip"]["median_create_s"])
    gap = max(0.0, total - zip_s)
    ranked = sorted(
        ((key, value) for key, value in medians.items()),
        key=lambda item: item[1],
        reverse=True,
    )

    result["schema"] = "cmpct-v030-eg08-stage-breakdown-v1"
    result["stage_breakdown"] = {
        "raw_rounds": samples,
        "median_s": medians,
        "candidate_verified_create_s": total,
        "zip_create_s": zip_s,
        "zip_create_gap_s": float(gap),
        "largest_owner": ranked[0][0],
        "largest_owner_s": float(ranked[0][1]),
        "owners_larger_than_zip_gap": [key for key, value in ranked if value > gap],
    }
    result["experiment_valid"] = bool(
        result.get("experiment_valid")
        and result["strict"]["beats_accepted_v029_size"]
        and result["strict"]["beats_zip_size"]
        and result["strict"]["beats_zstd19_size"]
        and result["strict"]["verified_create_beats_zstd19"]
        and result["strict"]["within_release_locality_bounds"]
        and result["strict"]["exact_serial_archive_identity"]
        and result["strict"]["same_selected_level_vector"]
        and all(row["calls"] == {"profile_prepare": 1, "strong_verify": 1, "locality": 1} for row in samples)
    )
    result["promotion_signal"] = False
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only causal timing decomposition of the byte-identical v7 C25EG08 Office candidate. "
        "No phase is removed or moved outside timing; no archive, selector, policy, comparator, locality, "
        "recovery, native/Android or release rule changes. The result only identifies the next optimization owner."
    )
    return result


def _failure_receipt(exc: BaseException) -> dict:
    """Preserve an invalid diagnostic as durable negative evidence without converting it into a pass."""
    return {
        "schema": "cmpct-v030-eg08-stage-breakdown-failure-v1",
        "experiment_valid": False,
        "promotion_signal": False,
        "release_credit": False,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "claim_boundary": (
            "Diagnostic failure receipt only. No benchmark threshold, archive byte, selector, locality/recovery, "
            "native/Android or release requirement is changed; the lane must remain red until the causal defect is fixed."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-stage-breakdown-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-stage-breakdown.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run(args.work_root)
    except BaseException as exc:
        failure = _failure_receipt(exc)
        args.output.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2), flush=True)
        raise
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "measured_candidate": result["measured_candidate"],
        "comparators": result["comparators"],
        "stage_breakdown": result["stage_breakdown"],
        "strict": result["strict"],
        "experiment_valid": result["experiment_valid"],
        "promotion_signal": result["promotion_signal"],
        "release_credit": result["release_credit"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("C25EG08 stage decomposition invalidated the inherited candidate contract")


if __name__ == "__main__":
    main()
