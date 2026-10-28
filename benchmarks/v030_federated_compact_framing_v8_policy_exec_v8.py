from __future__ import annotations

"""C25EG08 exact-byte executor with one compact->EG07 expansion for verify+locality.

v7 proved the Office representation and policy are already on the correct side of every
size/locality boundary, but verified creation still loses to ZIP.  The timed v7 path
expands the same C25EG08 archive to an equivalent EG07 temporary archive twice: once in
``strong_verify`` and once again in ``locality_report``.  Both consumers require exactly
the same authenticated compact parse and exact EG07 byte expansion.

This experiment removes only that duplicate physical conversion.  It expands once inside
the timed boundary, then runs the unchanged EG07 strong verifier and unchanged EG07
locality report against that one exact expanded archive.  Archive bytes, selected levels,
strong verification, locality limits, recovery semantics, comparator timing and source
proof accounting are unchanged.  The source-tree proof oracle remains outside timing as
in v7.  This lane is research/productization evidence only and never grants release credit.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DV5
from benchmarks import v030_federated_compact_framing_v8_policy_exec_v6 as V6
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07


_ORIGINAL_CANDIDATE_ONCE = V6._candidate_once


def _candidate_once_single_expansion(
    stage: Path,
    root: Path,
    rules: list[dict],
    reference: bytes,
    vector: tuple[int, ...],
) -> dict:
    # External proof oracle over the normalized source tree.  As in v7, this is not
    # archive self-verification and is computed before the measured create boundary.
    expected_tree = EG07._treehash(stage)

    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    raw_eg07, graph_s = DV5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    output = root / "policy-v8.c25eg08"
    emitted = V6._emit_pruned(raw_eg07, output, rules)

    # v7 called EG08.strong_verify(output) and then EG08.locality_report(output).
    # Each helper reparsed the compact archive, regenerated an identical EG07 archive,
    # and wrote/read that temporary representation.  Build it once and preserve the
    # exact inherited verification/locality implementations on the resulting bytes.
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-v8-verify-locality-") as td:
        expanded = Path(td) / "expanded.cmpct"
        parsed = EG08._expand_to_eg07(output, expanded)
        verified = EG07.strong_verify(expanded, expected_tree=expected_tree)
        locality = EG07.locality_report(expanded)

    elapsed = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError("single-expansion EG08 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("single-expansion EG08 policy exceeded frozen locality/decode limits")

    raw = output.read_bytes()
    if raw != reference:
        raise RuntimeError("single-expansion verification changed EG08 archive bytes")
    selected = tuple(int(level) for level in emitted["selected_levels"])
    if selected != vector:
        raise RuntimeError("single-expansion verification changed selected compression levels")

    return {
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "verified_create_s": float(elapsed),
        "graph_s": float(graph_s),
        "parallel_compression_s": float(emitted["compression_s"]),
        "publication_s": float(emitted["publication_s"]),
        "workers": int(emitted["workers"]),
        "required_features": list(emitted["required_features"]),
        "level1_ratio_compressions_required": bool(emitted["level1_ratio_compressions_required"]),
        "selected_high_effort_packs": int(emitted["selected_high_effort_packs"]),
        "selected_levels": list(selected),
        "exact_bytes_vs_serial_reference": True,
        "locality": locality,
        "compact_expansion_passes": 1,
        "compact_pack_count": len(parsed["packs"]),
        "proof_source_tree_precomputed_outside_timing": True,
        "archive_strong_verification_still_timed": True,
        "archive_locality_check_still_timed": True,
    }


@contextmanager
def _single_expansion_boundary():
    original = V6._candidate_once
    V6._candidate_once = _candidate_once_single_expansion
    try:
        yield
    finally:
        V6._candidate_once = original


def run(work_root: Path) -> dict:
    with _single_expansion_boundary():
        result = dict(V6.run(work_root))

    result["schema"] = "cmpct-v030-eg08-policy-exec-v8"
    change = dict(result["execution_change"])
    change.update(
        {
            "type": "single-compact-expansion-verify-locality",
            "compact_expansion_passes_per_measured_round": 1,
            "duplicate_compact_to_eg07_expansion_removed": True,
            "proof_source_tree_precomputed_outside_timed_boundary": True,
            "archive_strong_verification_still_timed": True,
            "archive_locality_check_still_timed": True,
            "comparator_timing_changed": False,
            "archive_bytes_changed": False,
            "selected_levels_changed": False,
            "verification_semantics_changed": False,
            "locality_semantics_changed": False,
        }
    )
    result["execution_change"] = change

    strict = dict(result["strict"])
    experiment_valid = all(
        (
            strict["beats_accepted_v029_size"],
            strict["beats_zip_size"],
            strict["beats_zstd19_size"],
            strict["within_release_locality_bounds"],
            strict["content_identity_not_policy_input"],
            strict["exact_serial_archive_identity"],
            strict["same_selected_level_vector"],
        )
    )
    result["experiment_valid"] = bool(experiment_valid)
    result["promotion_signal"] = bool(strict["passed"])
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only exact-byte execution optimization. The exact C25EG08 archive is converted to its exact "
        "EG07 equivalent once per timed round and that same expanded artifact is consumed by the unchanged EG07 "
        "strong verifier and unchanged EG07 locality report. Source proof hashing remains outside timing exactly "
        "as in v7. Archive bytes, selected levels, integrity, recovery/locality semantics and ZIP/Zstd comparators "
        "are unchanged. Native/Android, all-15 and strict release authorities remain mandatory."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v8-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v8.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "execution_change": result["execution_change"],
                "measured_candidate": result["measured_candidate"],
                "comparators": result["comparators"],
                "strict": result["strict"],
                "experiment_valid": result["experiment_valid"],
                "promotion_signal": result["promotion_signal"],
                "release_credit": result["release_credit"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["experiment_valid"]:
        raise SystemExit("single-expansion C25EG08 experiment is invalid")


if __name__ == "__main__":
    main()
