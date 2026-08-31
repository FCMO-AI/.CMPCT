from __future__ import annotations

"""Research-only reader/verification productization gate for r25 implicit-v4 filesystem control.

The size oracle proves that replacing the duplicated filesystem-v1 graph member with the already-bounded
implicit-v4 control can materially shrink the complete r25 candidate.  This gate advances the next prerequisite:
build the projected archive, recover regular identities from the authenticated selected content graph, expand the
archive-resident implicit control back to exact filesystem-v1 semantics, then re-read every regular user member
through the canonical r25 member reader with the unchanged <=8x locality law.

Nothing here changes shipping grammar, selector or release authority.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import v030_r25_manifest_derived_identity_oracle as SIZE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS


def _read_archive_control(archive: Path) -> tuple[bytes, dict]:
    raw, stats = CANON._read_profile_member(archive, FS.FILESYSTEM_MANIFEST)
    if float(stats["decoded_context_amplification"]) > 8.0:
        raise RuntimeError("implicit-v4 control member exceeds canonical locality ceiling")
    return raw, stats


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    source = SIZE._source(work_root)
    current_raw, regular_sources, _capture = SIZE._capture(source)
    implicit_raw = IFS4.encode_v1(
        current_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    implicit_stage = work_root / "implicit-stage"
    SIZE._stage(regular_sources, implicit_raw, implicit_stage)
    archive = work_root / "implicit-reader-productization.cmpct"
    built = SIZE._build(implicit_stage, archive)

    archive_control, control_stats = _read_archive_control(archive)
    if archive_control != implicit_raw:
        raise RuntimeError("archive-resident implicit-v4 control differs from staged control bytes")

    graph_identities = CANON._profile_content_identities(archive)
    manifest_identity = graph_identities.pop(FS.FILESYSTEM_MANIFEST, None)
    expected_manifest_identity = (len(implicit_raw), hashlib.sha256(implicit_raw).digest())
    if manifest_identity != expected_manifest_identity:
        raise RuntimeError("implicit-v4 control graph identity mismatch")

    expanded = IFS4.decode_to_v1(
        archive_control,
        regular_identities=graph_identities,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    original = FS.decode_manifest(
        current_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    if expanded["manifest"] != original["manifest"]:
        raise RuntimeError("archive-resident implicit-v4 expansion differs from exact filesystem-v1 semantics")
    if expanded["regular"] != original["regular"]:
        raise RuntimeError("archive-resident implicit-v4 regular identities differ from source semantics")
    if expanded["hardlinks"] != original["hardlinks"]:
        raise RuntimeError("archive-resident implicit-v4 hardlink semantics differ from source semantics")

    max_amp = float(control_stats["decoded_context_amplification"])
    checked = 0
    for rel, (size, digest) in expanded["regular"].items():
        raw, stats = CANON._read_profile_member(archive, rel)
        if len(raw) != int(size) or hashlib.sha256(raw).digest() != bytes(digest):
            raise RuntimeError(f"implicit-v4 projected archive member integrity mismatch: {rel}")
        amp = float(stats["decoded_context_amplification"])
        if amp > 8.0:
            raise RuntimeError(f"implicit-v4 projected archive member exceeds locality ceiling: {rel}")
        max_amp = max(max_amp, amp)
        checked += 1

    source_tree = CANON._semantic_tree_sha(original)
    expanded_tree = CANON._semantic_tree_sha(expanded)
    if expanded_tree != source_tree:
        raise RuntimeError("implicit-v4 projected archive changes canonical user-tree identity")

    return {
        "schema": "cmpct-v030-r25-manifest-implicit-reader-productization-v1",
        "target": SIZE.TARGET,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "selected": built.get("selected"),
        "regular_members_verified": checked,
        "control_member_exact": archive_control == implicit_raw,
        "graph_control_identity_exact": manifest_identity == expected_manifest_identity,
        "filesystem_v1_semantics_exact": expanded["manifest"] == original["manifest"],
        "regular_identities_exact": expanded["regular"] == original["regular"],
        "hardlink_semantics_exact": expanded["hardlinks"] == original["hardlinks"],
        "user_tree_sha256": expanded_tree,
        "source_tree_sha256": source_tree,
        "user_tree_exact": expanded_tree == source_tree,
        "max_member_read_amplification": max_amp,
        "within_release_locality_bounds": max_amp <= 8.0,
        "release_credit": False,
        "selector_change": False,
        "canonical_grammar_change": False,
        "next_boundary": "canonical writer/reader integration plus recovery/native/Android/all-15 exact authority",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r25-manifest-implicit-reader-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r25-manifest-implicit-reader.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
