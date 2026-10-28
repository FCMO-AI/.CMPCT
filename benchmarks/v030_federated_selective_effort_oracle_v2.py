from __future__ import annotations

"""Timing-corrected front door for the C25EG01 per-pack selective-effort experiment.

The v1 profiler intentionally evaluates seven compression levels three times for every final pack.  That is useful
for byte/CPU attribution but its instrumented build wall-clock is not a legitimate level-1 candidate baseline.
This front door preserves the exact v1 pack frontier and DP model while replacing only that contaminated timing
with three ordinary level-1 C25EG01 build + mandatory-strong-verify measurements.

Keeping profiling cost separate is part of the evidence contract: the modeled ZIP CPU budget must compare the
candidate users would actually build, not the deliberately expensive measurement apparatus used to understand it.
"""

import argparse
import json
from pathlib import Path
import statistics

from benchmarks import v030_federated_selective_effort_oracle as V1

BASELINE_ROUNDS = 3
_PROFILE = V1._profile_final_packs


def _timing_correct_profile(source: Path, root: Path) -> dict:
    profiled = dict(_PROFILE(source, root))
    instrumentation = {
        "profiled_build_s": float(profiled["build_s"]),
        "profiled_strong_verify_s": float(profiled["strong_verify_s"]),
        "profiled_verified_create_s": float(profiled["verified_create_s"]),
    }

    samples = []
    sizes = set()
    localities = []
    for index in range(BASELINE_ROUNDS):
        lane = root / f"true-level1-baseline-{index}"
        lane.mkdir(parents=True)
        result = V1._policy_build(source, lane, {})
        samples.append(float(result["verified_create_s"]))
        sizes.add(int(result["archive_bytes"]))
        localities.append(result["locality"])
    if len(sizes) != 1:
        raise RuntimeError(f"true level-1 baseline size is nondeterministic: {sizes!r}")
    if not all(item.get("within_release_bounds") for item in localities):
        raise RuntimeError("true level-1 baseline violated frozen locality bounds")

    true_bytes = next(iter(sizes))
    if true_bytes != int(profiled["archive_bytes"]):
        raise RuntimeError(
            f"profiling changed level-1 archive bytes: profiled={profiled['archive_bytes']} true={true_bytes}"
        )
    profiled["instrumentation_timing"] = instrumentation
    profiled["archive_bytes"] = true_bytes
    profiled["build_s"] = None
    profiled["strong_verify_s"] = None
    profiled["verified_create_s"] = statistics.median(samples)
    profiled["true_level1_raw_verified_create_s"] = samples
    return profiled


def run(work_root: Path) -> dict:
    old = V1._profile_final_packs
    V1._profile_final_packs = _timing_correct_profile
    try:
        result = dict(V1.run(work_root))
    finally:
        V1._profile_final_packs = old
    result["schema"] = "cmpct-v030-federated-selective-effort-v2"
    result["baseline_rounds"] = BASELINE_ROUNDS
    result["claim_boundary"] = (
        "research-only per-pack effort model for C25EG01. Profiling wall-clock is excluded from the candidate "
        "baseline; ZIP budgeting uses three ordinary level-1 build+strong-verify runs. No candidate default, "
        "selector, v0.29 floor, competitor threshold, locality law, native/Android support or release gate changes."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("federated selective-effort v2 measurement invalid")


if __name__ == "__main__":
    main()
