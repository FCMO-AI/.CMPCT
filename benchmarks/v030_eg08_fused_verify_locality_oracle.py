from __future__ import annotations

"""C25EG08 one-expansion strong-verify + locality execution oracle.

Exact-head Office evidence leaves C25EG08 about 114 ms behind ZIP after policy-feature pruning. The canonical EG08
reader currently expands the compact archive to an EG07 temporary archive once for ``strong_verify`` and then
repeats the complete EG08 parse/expansion/publication for ``locality_report``. Both consumers require the same exact
EG07 byte stream.

This research oracle removes that whole duplicate expansion/materialization category: one authenticated EG08 parse
produces one temporary EG07 archive, and both mature EG07 semantic owners consume that same immutable expansion.
The source-tree proof digest remains outside the timed boundary exactly as in v7. Archive strong verification and
locality are both still timed; no result is cached across benchmark rounds, no comparator changes, and archive bytes,
selected levels, recovery and locality limits remain identical.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_exec_v6 as V6
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

_ORIGINAL = V6._candidate_once


def _candidate_once_fused(stage: Path, root: Path, rules: list[dict], reference: bytes, vector: tuple[int, ...]) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    # External proof oracle; as in v7, this is not archive self-verification work.
    expected_tree = EG07._treehash(stage)

    started = time.perf_counter()
    raw_eg07, graph_s = V6.DV5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    output = root / "policy-v8.c25eg08"
    emitted = V6._emit_pruned(raw_eg07, output, rules)

    fused_started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-fused-vl-", dir=root) as td:
        expanded = Path(td) / "expanded.cmpct"
        parsed = EG08._expand_to_eg07(output, expanded)
        verified = EG07.strong_verify(expanded, expected_tree=expected_tree)
        locality = EG07.locality_report(expanded)
    fused_verify_locality_s = time.perf_counter() - fused_started
    elapsed = time.perf_counter() - started

    if not verified.get("ok"):
        raise RuntimeError("one-expansion EG08 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("one-expansion EG08 policy exceeded frozen locality/decode limits")
    raw = output.read_bytes()
    if raw != reference:
        raise RuntimeError("one-expansion verify/locality changed EG08 archive bytes")
    selected = tuple(int(level) for level in emitted["selected_levels"])
    if selected != vector:
        raise RuntimeError("one-expansion verify/locality changed selected compression levels")
    return {
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "verified_create_s": float(elapsed),
        "graph_s": float(graph_s),
        "parallel_compression_s": float(emitted["compression_s"]),
        "publication_s": float(emitted["publication_s"]),
        "fused_verify_locality_s": float(fused_verify_locality_s),
        "compact_pack_count": len(parsed["packs"]),
        "workers": int(emitted["workers"]),
        "required_features": list(emitted["required_features"]),
        "level1_ratio_compressions_required": bool(emitted["level1_ratio_compressions_required"]),
        "selected_high_effort_packs": int(emitted["selected_high_effort_packs"]),
        "selected_levels": list(selected),
        "exact_bytes_vs_serial_reference": True,
        "locality": locality,
    }


@contextmanager
def _fused_boundary():
    V6._candidate_once = _candidate_once_fused
    try:
        yield
    finally:
        V6._candidate_once = _ORIGINAL


def run(work_root: Path) -> dict:
    with _fused_boundary():
        result = dict(V6.run(work_root))
    result["schema"] = "cmpct-v030-eg08-fused-verify-locality-v1"
    change = dict(result["execution_change"])
    change.update({
        "type": "one-eg08-expansion-for-strong-verify-and-locality",
        "proof_source_tree_precomputed_outside_timed_boundary": True,
        "archive_strong_verification_still_timed": True,
        "locality_still_timed": True,
        "eg08_expansion_count_per_round": 1,
        "eg07_semantic_owners_unchanged": True,
        "comparator_timing_changed": False,
        "archive_bytes_changed": False,
        "selected_levels_changed": False,
    })
    result["execution_change"] = change
    strict = result["strict"]
    valid = all((
        strict["beats_accepted_v029_size"], strict["beats_zip_size"], strict["beats_zstd19_size"],
        strict["within_release_locality_bounds"], strict["content_identity_not_policy_input"],
        strict["exact_serial_archive_identity"], strict["same_selected_level_vector"],
    ))
    result["experiment_valid"] = bool(valid)
    result["promotion_signal"] = bool(strict["passed"])
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only execution fusion. One authenticated EG08 expansion is shared by the unchanged EG07 strong-"
        "verification and locality semantic owners inside every measured round. No archive bytes, policy selection, "
        "recovery/locality limits, comparator timing, native/Android dispatch or release authority changes."
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-fused-vl-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-fused-vl.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "execution_change": result["execution_change"],
        "measured_candidate": result["measured_candidate"],
        "comparators": result["comparators"],
        "strict": result["strict"],
        "experiment_valid": result["experiment_valid"],
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("one-expansion EG08 verify/locality experiment invalid")


if __name__ == "__main__":
    main()
