from __future__ import annotations

"""Exact productization gate for generic r25 filesystem-control writer admission.

This advances the proven implicit-v4 size/reader result one prerequisite: both staging and authenticated-reader
validation now go through the same content-agnostic seam intended for canonical integration. The gate compares
complete r25 artifacts and reconstructs exact filesystem-v1 semantics from archive-authenticated content
identities. It changes no shipping selector and grants no release credit by itself.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from benchmarks import v030_r25_manifest_derived_identity_oracle as SIZE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_r25_manifest_admission as ADMIT

ROOT = Path(__file__).resolve().parents[1]
MIN_COMPLETE_ARTIFACT_SAVING = 16 * 1024


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = SIZE._source(work_root)
    current_raw, regular_sources, _capture = SIZE._capture(source)

    current_stage = work_root / "current-stage"
    admitted_stage = work_root / "admitted-stage"
    SIZE._stage(regular_sources, current_raw, current_stage)
    prepared = ADMIT.prepare_profile_tree(
        source,
        admitted_stage,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=CANON.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CANON.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    if prepared["source_manifest_raw"] != current_raw:
        raise RuntimeError("generic writer seam recaptured different filesystem-v1 source semantics")
    if prepared["selected_manifest_encoding"] != "implicit-v4":
        raise RuntimeError("proven developer workload did not admit the generic implicit-v4 writer control")
    admitted_raw = prepared["selected_manifest_raw"]

    current_archive = work_root / "current.cmpct"
    admitted_archive = work_root / "admitted.cmpct"
    current = SIZE._build(current_stage, current_archive)
    candidate = SIZE._build(admitted_stage, admitted_archive)
    archive_saving = int(current["archive_bytes"]) - int(candidate["archive_bytes"])

    archive_control, control_stats = CANON._read_profile_member(admitted_archive, FS.FILESYSTEM_MANIFEST)
    if archive_control != admitted_raw:
        raise RuntimeError("published graph member differs from generically admitted writer bytes")
    content_identities = CANON._profile_content_identities(admitted_archive)
    manifest_identity = content_identities.get(FS.FILESYSTEM_MANIFEST)
    expected_manifest_identity = (len(admitted_raw), hashlib.sha256(admitted_raw).digest())

    decoded, encoding = ADMIT.decode_from_content_identities(
        archive_control,
        content_identities=content_identities,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    original = FS.decode_manifest(
        current_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    exact = decoded["manifest"] == original["manifest"]
    if not exact:
        raise RuntimeError("generic writer admission changed filesystem-v1 semantics")
    tree_exact = CANON._semantic_tree_sha(decoded) == CANON._semantic_tree_sha(original)
    if not tree_exact:
        raise RuntimeError("generic writer admission changed user-tree identity")

    useful = archive_saving >= MIN_COMPLETE_ARTIFACT_SAVING
    if not useful:
        raise RuntimeError("generic writer seam failed the preregistered complete-artifact materiality floor")

    return {
        "schema": "cmpct-v030-r25-manifest-writer-admission-productization-v2",
        "source_commit": _source_commit(),
        "target": SIZE.TARGET,
        "admission": {
            "encoding": prepared["selected_manifest_encoding"],
            "filesystem_v1_bytes": len(prepared["source_manifest_raw"]),
            "selected_bytes": len(admitted_raw),
            "control_saving_bytes": prepared["manifest_control_saving_bytes"],
            "strictly_smaller_control": len(admitted_raw) < len(prepared["source_manifest_raw"]),
        },
        "current_candidate": current,
        "admitted_candidate": candidate,
        "archive_saving_bytes": archive_saving,
        "minimum_complete_artifact_saving_bytes": MIN_COMPLETE_ARTIFACT_SAVING,
        "archive_saving_useful": useful,
        "archive_control_exact": archive_control == admitted_raw,
        "graph_control_identity_exact": manifest_identity == expected_manifest_identity,
        "decoded_encoding": encoding,
        "filesystem_v1_semantics_exact": exact,
        "user_tree_exact": tree_exact,
        "max_control_read_amplification": float(control_stats["decoded_context_amplification"]),
        "within_release_locality_bounds": float(control_stats["decoded_context_amplification"]) <= 8.0,
        "shared_writer_reader_semantic_owner": True,
        "release_credit": False,
        "canonical_writer_change": False,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D5",
            "radicality": "R2",
            "active_saturation": ["S6"],
            "research_priority_score": 91,
            "strongest_self_critique": (
                "The shared seam proves exact staging/reader ownership on the known positive structure, but canonical "
                "integration must still prove fallback, recovery, native and Android parity without exporting runtime debt."
            ),
            "terminal_decision": "PROMOTE_NEXT_PREREQUISITE",
            "next_decisive_test": (
                "wire the shared seam into canonical r25 writer/validated-manifest paths and run exact fallback, "
                "recovery, locality, native, Android and all-15 no-regression authority"
            ),
        },
        "next_boundary": "canonical writer/reader integration, then recovery/native/Android/all-15 exact authority",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-manifest-writer-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-manifest-writer.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
