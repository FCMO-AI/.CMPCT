from __future__ import annotations

"""Research/productization proof for wiring implicit-v4 into canonical r25.

The accompanying patch changes only canonical manifest staging/validation. This oracle prices explicit-v1 and
patched implicit-v4 through the same *canonical-r25-only* G04/PrefixGraph builder already used by the accepted
candidate gate. That avoids conflating the product selector's legitimate r24/v0.29 fallback with the narrower
question being tested here: does the exact canonical-r25 grammar become strictly smaller when the manifest seam is
wired in? Complete archive bytes, not only control-member bytes, must clear the existing >=16 KiB useful-saving
floor. Passing advances only the next D5 prerequisite; it is not release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess

from benchmarks import v030_r25_manifest_derived_identity_oracle as SIZE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_canonical_manifest_candidate as CAND
from experiments import entropygraph_v030_product_fs as FS

ROOT = Path(__file__).resolve().parents[1]
MIN_CONTROL_SAVING = 64 * 1024


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _explicit_stage(source: Path, stage: Path) -> dict:
    return FS.prepare_profile_tree(
        source,
        stage,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=CANON.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CANON.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = SIZE._source(work_root)
    original_raw, _regular_sources, _capture = SIZE._capture(source)
    original = FS.decode_manifest(
        original_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    source_tree = CANON._semantic_tree_sha(original)

    # Exact complete r25 baseline on the same representation substrate used by the accepted candidate gate.
    baseline_stage = work_root / "canonical-stage-explicit"
    baseline_prepared = _explicit_stage(source, baseline_stage)
    if baseline_prepared["manifest_raw"] != original_raw:
        raise RuntimeError("explicit canonical baseline changed source filesystem-v1 semantics")
    baseline_archive = work_root / "canonical-r25-manifest-explicit.cmpct"
    baseline_stats = CAND._build_canonical_r25_only(baseline_stage, baseline_archive)
    baseline_revision, baseline_profile = CANON._profile_for_archive(baseline_archive)
    if baseline_revision != CANON.REVISION:
        raise RuntimeError("explicit canonical-r25-only baseline did not emit canonical r25")
    baseline_validated = CANON._validated_manifest(baseline_archive)
    if CANON._semantic_tree_sha(baseline_validated) != source_tree:
        raise RuntimeError("explicit canonical baseline changed user-tree identity")
    baseline_verify = CANON.strong_verify(baseline_archive)
    if not baseline_verify.get("ok") or baseline_verify.get("tree_sha256") != source_tree:
        raise RuntimeError(f"explicit canonical baseline failed strong verification: {baseline_verify!r}")

    # Patched candidate: same r25-only builder, with only the canonical staging/reader seam changed.
    stage = work_root / "canonical-stage-implicit"
    prepared = CANON._prepare_profile_tree(source, stage)
    if prepared.get("selected_manifest_encoding") != "implicit-v4":
        raise RuntimeError("patched canonical staging did not select implicit-v4 on the proven positive structure")
    selected = bytes(prepared["selected_manifest_raw"])
    if prepared["manifest_raw"] != original_raw:
        raise RuntimeError("patched canonical staging changed source filesystem-v1 semantics")
    if len(original_raw) - len(selected) < MIN_CONTROL_SAVING:
        raise RuntimeError("canonical integration lost the preregistered control saving")
    manifest_path = stage.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    if manifest_path.read_bytes() != selected:
        raise RuntimeError("canonical staged graph member is not the admitted control")

    archive = work_root / "canonical-r25-manifest-implicit.cmpct"
    candidate_stats = CAND._build_canonical_r25_only(stage, archive)
    revision, profile = CANON._profile_for_archive(archive)
    if revision != CANON.REVISION:
        raise RuntimeError(f"r25-only candidate did not emit canonical r25: {revision!r}/{profile!r}")
    if candidate_stats.get("candidate_set") != baseline_stats.get("candidate_set"):
        raise RuntimeError("manifest integration changed the canonical r25 candidate set")
    if profile != baseline_profile:
        raise RuntimeError(
            f"manifest integration changed selected canonical representation family: {baseline_profile!r} -> {profile!r}"
        )

    baseline_bytes = baseline_archive.stat().st_size
    candidate_bytes = archive.stat().st_size
    complete_saving = baseline_bytes - candidate_bytes
    if complete_saving <= 0:
        raise RuntimeError("patched canonical implicit-v4 integration did not strictly reduce complete r25 bytes")
    if complete_saving < SIZE.MIN_USEFUL_ARCHIVE_SAVING:
        raise RuntimeError("patched canonical integration missed the existing useful complete-artifact saving floor")
    baseline_sha256 = _sha256(baseline_archive)
    candidate_sha256 = _sha256(archive)
    if baseline_sha256 == candidate_sha256:
        raise RuntimeError("patched canonical integration unexpectedly matched explicit baseline physical bytes")

    archive_raw, control_stats = CANON._read_profile_member(archive, FS.FILESYSTEM_MANIFEST)
    if archive_raw != selected:
        raise RuntimeError("canonical r25 archive changed admitted manifest-control bytes")
    validated = CANON._validated_manifest(archive)
    if validated["manifest"] != original["manifest"]:
        raise RuntimeError("patched canonical reader did not recover exact filesystem-v1 semantics")
    validated_tree = CANON._semantic_tree_sha(validated)
    if validated_tree != source_tree:
        raise RuntimeError("patched canonical reader changed user-tree identity")

    verified = CANON.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"patched canonical strong verification failed: {verified!r}")
    if verified.get("tree_sha256") != source_tree:
        raise RuntimeError("patched canonical strong verifier reports the wrong user-tree identity")

    content = CANON._profile_content_identities(archive)
    control_identity = content.get(FS.FILESYSTEM_MANIFEST)
    expected_control_identity = (len(selected), hashlib.sha256(selected).digest())
    if control_identity != expected_control_identity:
        raise RuntimeError("patched canonical graph does not authenticate selected manifest control exactly")

    return {
        "schema": "cmpct-v030-r25-manifest-canonical-integration-oracle-v3",
        "source_commit": _source_commit(),
        "target": SIZE.TARGET,
        "format_revision": revision,
        "format_profile": profile,
        "baseline_format_revision": baseline_revision,
        "baseline_format_profile": baseline_profile,
        "canonical_candidate_set": candidate_stats.get("candidate_set"),
        "baseline_selected": baseline_stats.get("selected"),
        "candidate_selected": candidate_stats.get("selected"),
        "filesystem_v1_bytes": len(original_raw),
        "selected_manifest_bytes": len(selected),
        "control_saving_bytes": len(original_raw) - len(selected),
        "selected_manifest_encoding": prepared["selected_manifest_encoding"],
        "baseline_archive_bytes": baseline_bytes,
        "baseline_archive_sha256": baseline_sha256,
        "candidate_archive_bytes": candidate_bytes,
        "candidate_archive_sha256": candidate_sha256,
        "complete_artifact_saving_bytes": complete_saving,
        "minimum_useful_archive_saving_bytes": SIZE.MIN_USEFUL_ARCHIVE_SAVING,
        "complete_artifact_promotion_signal": complete_saving >= SIZE.MIN_USEFUL_ARCHIVE_SAVING,
        "baseline_strong_verify_ok": bool(baseline_verify.get("ok")),
        "baseline_strong_verify_tree_exact": baseline_verify.get("tree_sha256") == source_tree,
        "graph_control_identity_exact": control_identity == expected_control_identity,
        "filesystem_v1_semantics_exact": validated["manifest"] == original["manifest"],
        "source_tree_sha256": source_tree,
        "validated_tree_sha256": validated_tree,
        "strong_verify_ok": bool(verified.get("ok")),
        "strong_verify_tree_exact": verified.get("tree_sha256") == source_tree,
        "control_read_amplification": float(control_stats["decoded_context_amplification"]),
        "within_locality_8x": float(control_stats["decoded_context_amplification"]) <= 8.0,
        "release_credit": False,
        "canonical_source_patch_candidate_only": True,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D5",
            "radicality": "R2",
            "active_saturation": ["S6"],
            "research_priority_score": 96,
            "measured_gap_change_bytes": complete_saving,
            "strongest_self_critique": (
                "This isolates the complete canonical-r25 representation A/B and patched writer/reader seam, but the "
                "shipping product selector and recovery/native/Android/all-15 authority still must consume the landed grammar."
            ),
            "terminal_decision": "PROMOTE_NEXT_PREREQUISITE",
            "next_decisive_test": (
                "land the exact seam, then prove shipping product-floor selection plus recovery/malformed-control parity "
                "before native/Android and all-15 exact authority"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
