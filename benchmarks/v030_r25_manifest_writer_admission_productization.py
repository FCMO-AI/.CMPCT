from __future__ import annotations

"""Exact productization gate for generic r25 filesystem-control writer admission.

This advances the proven implicit-v4 size/reader result one prerequisite: the control choice is made by the same
content-agnostic admission seam intended for canonical integration.  The gate compares complete r25 artifacts,
then reconstructs exact filesystem-v1 semantics from archive-authenticated content identities.  It changes no
shipping selector and grants no release credit by itself.
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

    admitted = ADMIT.admit(
        current_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    if admitted.encoding != "implicit-v4":
        raise RuntimeError("proven developer workload did not admit the generic implicit-v4 writer control")

    current_stage = work_root / "current-stage"
    admitted_stage = work_root / "admitted-stage"
    SIZE._stage(regular_sources, current_raw, current_stage)
    SIZE._stage(regular_sources, admitted.raw, admitted_stage)

    current_archive = work_root / "current.cmpct"
    admitted_archive = work_root / "admitted.cmpct"
    current = SIZE._build(current_stage, current_archive)
    candidate = SIZE._build(admitted_stage, admitted_archive)
    archive_saving = int(current["archive_bytes"]) - int(candidate["archive_bytes"])

    archive_control, control_stats = CANON._read_profile_member(admitted_archive, FS.FILESYSTEM_MANIFEST)
    if archive_control != admitted.raw:
        raise RuntimeError("published graph member differs from generically admitted writer bytes")
    identities = CANON._profile_content_identities(admitted_archive)
    manifest_identity = identities.pop(FS.FILESYSTEM_MANIFEST, None)
    expected_manifest_identity = (len(admitted.raw), hashlib.sha256(admitted.raw).digest())
    if manifest_identity != expected_manifest_identity:
        raise RuntimeError("admitted filesystem control is not bound by the selected content graph")

    decoded, encoding = ADMIT.decode(
        archive_control,
        regular_identities=identities,
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

    return {
        "schema": "cmpct-v030-r25-manifest-writer-admission-productization-v1",
        "source_commit": _source_commit(),
        "target": SIZE.TARGET,
        "admission": {
            "encoding": admitted.encoding,
            "filesystem_v1_bytes": admitted.filesystem_v1_bytes,
            "selected_bytes": admitted.selected_bytes,
            "control_saving_bytes": admitted.saving_bytes,
            "strictly_smaller_control": admitted.selected_bytes < admitted.filesystem_v1_bytes,
        },
        "current_candidate": current,
        "admitted_candidate": candidate,
        "archive_saving_bytes": archive_saving,
        "minimum_complete_artifact_saving_bytes": MIN_COMPLETE_ARTIFACT_SAVING,
        "archive_saving_useful": archive_saving >= MIN_COMPLETE_ARTIFACT_SAVING,
        "archive_control_exact": archive_control == admitted.raw,
        "graph_control_identity_exact": manifest_identity == expected_manifest_identity,
        "decoded_encoding": encoding,
        "filesystem_v1_semantics_exact": exact,
        "user_tree_exact": tree_exact,
        "max_control_read_amplification": float(control_stats["decoded_context_amplification"]),
        "within_release_locality_bounds": float(control_stats["decoded_context_amplification"]) <= 8.0,
        "release_credit": False,
        "canonical_writer_change": False,
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
