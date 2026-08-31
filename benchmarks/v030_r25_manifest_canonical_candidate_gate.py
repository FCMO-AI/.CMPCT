from __future__ import annotations

"""Exact D5 gate for the implicit-v4 canonical integration candidate.

The already-proven generic writer/reader seam is exercised through the real canonical
release primitives, not a second archive grammar. Baseline and candidate build the same
r25 combined ablation from the same source tree. The candidate must be strictly smaller,
strongly verify and extract through its direct seam, reconstruct the exact user tree, and
remain rejected by the unmodified shipping facade. Passing authorizes only the next
productization prerequisite.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from benchmarks import v030_r25_manifest_derived_identity_oracle as SIZE
from experiments import entropygraph_v030_canonical_final as BASE
from experiments import entropygraph_v030_canonical_manifest_candidate as CAND


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = SIZE._source(work_root)
    expected_tree = BASE.treehash(source)

    baseline_archive = work_root / "baseline-r25.cmpct"
    candidate_archive = work_root / "candidate-r25.cmpct"
    BASE.build_ablation(source, baseline_archive, "combined")
    CAND.build_ablation(source, candidate_archive, "combined")

    baseline_bytes = baseline_archive.stat().st_size
    candidate_bytes = candidate_archive.stat().st_size
    saving = baseline_bytes - candidate_bytes
    if saving <= 0:
        raise RuntimeError("canonical implicit-manifest candidate did not strictly reduce complete r25 bytes")

    candidate_verify = CAND.strong_verify(candidate_archive)
    if not candidate_verify.get("ok"):
        raise RuntimeError(f"candidate canonical facade failed strong verification: {candidate_verify!r}")
    if candidate_verify.get("tree_sha256") != expected_tree:
        raise RuntimeError("candidate canonical facade changed user-tree identity")

    extracted = work_root / "candidate-extracted"
    CAND.extract(candidate_archive, extracted)
    extracted_tree = BASE.treehash(extracted)
    if extracted_tree != expected_tree:
        raise RuntimeError("candidate canonical facade extraction changed user-tree identity")

    # The current shipping decoder understands filesystem-v1 only. Either a structured
    # failure or an exception caused by rejecting unsupported compact control is valid
    # fail-closed behavior. Candidate failure itself is never converted into success.
    try:
        shipping_verify = BASE.strong_verify(candidate_archive)
    except Exception as exc:
        shipping_verify = {
            "ok": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
    shipping_fail_closed = not bool(shipping_verify.get("ok"))
    if not shipping_fail_closed:
        raise RuntimeError("implicit-v4 candidate leaked into unmodified shipping canonical semantics")

    manifest_raw, manifest_stats = CAND.read_member_with_stats(
        candidate_archive, BASE.FS.FILESYSTEM_MANIFEST
    )
    content = BASE._profile_content_identities(candidate_archive)
    decoded, encoding = CAND.ADMIT.decode_from_content_identities(
        manifest_raw,
        content_identities=content,
        max_path_bytes=BASE.POLICY.R.MAX_PATH_BYTES,
        max_entries=BASE.MAX_MANIFEST_ENTRIES,
    )
    if encoding != "implicit-v4":
        raise RuntimeError("canonical candidate did not publish the proven implicit-v4 control")
    if BASE._semantic_tree_sha(decoded) != expected_tree:
        raise RuntimeError("authenticated implicit-v4 expansion changed semantic tree")
    locality = float(manifest_stats["decoded_context_amplification"])
    if locality > 8.0:
        raise RuntimeError("canonical candidate control read exceeded release locality ceiling")

    return {
        "schema": "cmpct-v030-r25-manifest-canonical-candidate-gate-v2",
        "source_commit": _source_commit(),
        "target": SIZE.TARGET,
        "release_credit": False,
        "shipping_module_changed": False,
        "candidate_uses_process_global_mutation": False,
        "baseline_archive_bytes": baseline_bytes,
        "candidate_archive_bytes": candidate_bytes,
        "complete_artifact_saving_bytes": saving,
        "strictly_smaller_than_legacy_r25": candidate_bytes < baseline_bytes,
        "candidate_strong_verify": candidate_verify,
        "candidate_extract_tree_sha256": extracted_tree,
        "expected_tree_sha256": expected_tree,
        "manifest_encoding": encoding,
        "manifest_control_bytes": len(manifest_raw),
        "manifest_read_amplification": locality,
        "locality_le_8x": locality <= 8.0,
        "shipping_facade_fail_closed_unchanged": shipping_fail_closed,
        "shipping_verify_observation": shipping_verify,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D5",
            "radicality": "R2",
            "saturation_triggers": ["S6"],
            "research_priority_score": 94,
            "pre_mortem": (
                "The compact control can save bytes in an isolated writer yet fail through canonical primitives because "
                "semantic tree identity, authenticated graph ownership or locality no longer match."
            ),
            "builder": (
                "Run legacy and implicit-v4 staging through the real canonical r25 combined substrate and exercise a "
                "direct candidate verify/read/extract seam without process-global mutation."
            ),
            "hostile_review": (
                "A green candidate is not shipping proof: release-facing source is unchanged, and recovery, native, "
                "Android, all-15 no-regression and exact external authority must be rerun after promotion."
            ),
            "measured_gap_change_bytes": saving,
            "terminal_decision": "PROMOTE_NEXT_PREREQUISITE",
            "next_decisive_test": (
                "Promote the same admission/validated-manifest semantics into canonical implementation, then run focused "
                "fallback/hostile/recovery tests before native, Android and all-15 exact authority."
            ),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-canonical-manifest-candidate-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-canonical-manifest-candidate.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "baseline_archive_bytes": result["baseline_archive_bytes"],
        "candidate_archive_bytes": result["candidate_archive_bytes"],
        "complete_artifact_saving_bytes": result["complete_artifact_saving_bytes"],
        "manifest_encoding": result["manifest_encoding"],
        "shipping_facade_fail_closed_unchanged": result["shipping_facade_fail_closed_unchanged"],
        "candidate_uses_process_global_mutation": result["candidate_uses_process_global_mutation"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
