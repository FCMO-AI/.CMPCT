from __future__ import annotations

"""Research-only composition of the strongest byte-neutral C25EG08 execution moves.

The lower-effort raw-size policy is the smallest known generic Office representation that
still clears accepted v0.29, ZIP and Zstd-19 in bytes. Two independent execution changes
preserve that exact representation:

* convert compact EG08 -> inherited EG07 only once for strong verify + locality;
* reuse one libzstd compression context per bounded final-pack worker.

This oracle composes those changes at the complete verified-create boundary rather than
adding isolated micro-benchmark savings. Search/profiling still only distills the fixed
content-agnostic raw-size policy and is not credited to candidate creation, exactly as in
the predecessor lower-effort oracle. Candidate timing still includes graph construction,
final pack compression, publication, strong verification and locality.

A strict result must be smaller than accepted v0.29, ZIP and solid Zstd-19 and faster to
create than ZIP and Zstd-19, with exact serial bytes/SHA, unchanged level vector and <=8x
locality. This remains research evidence only; no selector/native/Android/release credit.
"""

import argparse
from contextlib import contextmanager
import json
from pathlib import Path

from benchmarks import v030_federated_compact_framing_v8_low_effort_policy as LOW
from benchmarks import v030_federated_compact_framing_v8_policy_exec_v6 as V6
from benchmarks import v030_federated_compact_framing_v8_policy_exec_v8 as V8
from benchmarks import v030_eg08_reused_zstd_context_oracle as CCTX


@contextmanager
def _reused_final_pack_contexts():
    original = V6._emit_pruned

    def emit(raw_eg07: bytes, output: Path, rules: list[dict]):
        # The bounded ThreadPool is created and joined inside _emit_pruned; worker-local
        # CCtx handles therefore cannot survive this context. Search/graph compression
        # remains on the ordinary engine and receives no hidden speed credit.
        with CCTX._zc(True):
            return original(raw_eg07, output, rules)

    V6._emit_pruned = emit
    try:
        yield
    finally:
        V6._emit_pruned = original


def run(work_root: Path) -> dict:
    with V8._single_expansion_boundary(), _reused_final_pack_contexts():
        result = dict(LOW.run(work_root))

    strict = dict(result["strict"])
    measured = dict(result["measured_candidate"])
    experiment_valid = bool(
        strict["beats_accepted_v029_size"]
        and strict["beats_zip_size"]
        and strict["beats_zstd19_size"]
        and strict["within_release_locality_bounds"]
        and strict["content_identity_not_policy_input"]
        and strict["only_raw_size_policy_input"]
        and strict["exact_serial_archive_identity"]
        and strict["same_selected_level_vector"]
        and measured.get("compact_expansion_passes") == 1
    )
    result["schema"] = "cmpct-v030-eg08-low-effort-composed-oracle-v1"
    result["execution_composition"] = {
        "base_policy": "one-or-two nested raw-size thresholds only",
        "single_compact_expansion_verify_locality": True,
        "reused_zstd_context_per_final_pack_worker": True,
        "graph_semantics_changed": False,
        "archive_bytes_changed_vs_same_selected_policy": False,
        "selected_levels_changed": False,
        "comparator_timing_changed": False,
        "release_credit": False,
    }
    result["experiment_valid"] = experiment_valid
    result["promotion_signal"] = bool(experiment_valid and strict["passed"])
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only complete-boundary composition. A strict result authorizes only the next canonical "
        "productization prerequisite; selector, hostile/recovery, native, Android, all-15 and final authority "
        "must still be earned on the exact candidate fingerprint."
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-low-effort-composed-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-low-effort-composed.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_policy": result["selected_policy"],
        "measured_candidate": result["measured_candidate"],
        "comparators": result["comparators"],
        "strict": result["strict"],
        "experiment_valid": result["experiment_valid"],
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("composed C25EG08 experiment invalid")


if __name__ == "__main__":
    main()
