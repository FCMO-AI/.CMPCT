from __future__ import annotations

"""Research/productization proof for wiring implicit-v4 into canonical r25.

The accompanying patch changes only the canonical writer/validated-manifest seams: staging delegates to the
already-tested strict-smaller admission owner and reader validation delegates to the authenticated identity-aware
decoder. This oracle must run only after that patch is applied. It proves the patched canonical seam publishes
implicit-v4 on the known positive developer structure and that canonical validation expands it back to the exact
filesystem-v1 semantics and user-tree identity.

This is D5/S6 convergence. It grants no release credit and does not change external-selector thresholds.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess

from benchmarks import v030_r25_manifest_derived_identity_oracle as SIZE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS

ROOT = Path(__file__).resolve().parents[1]
MIN_CONTROL_SAVING = 64 * 1024


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


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

    stage = work_root / "canonical-stage"
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

    archive = work_root / "canonical-r25-manifest-candidate.cmpct"
    built = CANON._r25_build(stage, archive)
    revision, profile = CANON._profile_for_archive(archive)
    if revision != CANON.REVISION:
        raise RuntimeError(f"r25 candidate builder did not emit canonical r25 profile: {revision!r}/{profile!r}")

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
        "schema": "cmpct-v030-r25-manifest-canonical-integration-oracle-v1",
        "source_commit": _source_commit(),
        "target": SIZE.TARGET,
        "format_revision": revision,
        "format_profile": profile,
        "filesystem_v1_bytes": len(original_raw),
        "selected_manifest_bytes": len(selected),
        "control_saving_bytes": len(original_raw) - len(selected),
        "selected_manifest_encoding": prepared["selected_manifest_encoding"],
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
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
            "research_priority_score": 94,
            "strongest_self_critique": (
                "This proves the canonical Python writer/reader seam on a positive exact structure, but recovery, "
                "native, Android and all-15 no-regression authority still have to consume the same grammar before promotion."
            ),
            "terminal_decision": "PROMOTE_NEXT_PREREQUISITE",
            "next_decisive_test": "recovery and malformed-control parity, then native/Android and all-15 exact authority",
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
