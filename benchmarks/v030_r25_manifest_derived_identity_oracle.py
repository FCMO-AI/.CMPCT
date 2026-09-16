from __future__ import annotations

"""Research-only developer-workload A/B for the already-proven implicit-v4 filesystem control grammar.

Canonical r25 currently stores the full filesystem-v1 manifest as a graph member, duplicating every regular
file's path/content identity even though the selected content graph already authenticates those facts. The
federated EG04/EG05 research family already has a bounded grammar (`implicit-v4`) that removes those duplicate
regular identities, delta-codes metadata, and expands back to exact filesystem-v1 semantics when joined with the
authenticated content graph.

This oracle applies that existing grammar to the repaired developer workload *without* changing shipping bytes.
It compares complete release-candidate artifacts whose only staged-tree difference is current filesystem-v1 bytes
versus implicit-v4 bytes. A positive result can justify canonical productization work; it grants no release,
selector, native, Android or recovery credit by itself.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_candidate as RC

TARGET = "01_developer_repository"
MIN_USEFUL_ARCHIVE_SAVING = 16 * 1024


def _source(root: Path) -> Path:
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_manifest_identity_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_manifest_identity_repair")
    repair.install_generation_hooks(neutral)
    corpus = root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    return corpus / TARGET


def _capture(root: Path) -> tuple[bytes, list[tuple[Path, str]], dict]:
    return FS.capture_filesystem_manifest(
        root,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=CANON.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CANON.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )


def _stage(regular_sources: list[tuple[Path, str]], control_raw: bytes, target: Path) -> None:
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    for source, rel in regular_sources:
        FS._link_or_copy(source, target.joinpath(*PurePosixPath(rel).parts))
    manifest_path = target.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(control_raw)


def _build(stage: Path, out: Path) -> dict:
    with CANON._revision25_profile_context():
        result = dict(RC.build(stage, out))
        verified = RC.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError("research staged candidate failed graph-level strong verification")
    return {
        "archive_bytes": out.stat().st_size,
        "physical_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "selected": result.get("selected"),
        "graph_tree_sha256": verified.get("tree_sha256"),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = _source(work_root)
    current_raw, regular_sources, capture = _capture(source)
    implicit_raw = IFS4.encode_v1(
        current_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    semantic_exact = IFS4.semantics_equal(
        current_raw,
        implicit_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    if not semantic_exact:
        raise RuntimeError("implicit-v4 failed exact filesystem-v1 semantic expansion")

    current_decoded = FS.decode_manifest(
        current_raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    regular_count = len(current_decoded["regular"])

    current_stage = work_root / "current-stage"
    implicit_stage = work_root / "implicit-stage"
    _stage(regular_sources, current_raw, current_stage)
    _stage(regular_sources, implicit_raw, implicit_stage)

    current = _build(current_stage, work_root / "current.cmpct")
    implicit = _build(implicit_stage, work_root / "implicit.cmpct")
    archive_saving = int(current["archive_bytes"]) - int(implicit["archive_bytes"])

    return {
        "schema": "cmpct-v030-r25-manifest-derived-identity-oracle-v2",
        "target": f"neutral_hostile_v1/{TARGET}",
        "capture": capture,
        "implicit_v4": {
            "regular_identity_count": regular_count,
            "duplicated_sha256_bytes_avoided": regular_count * 32,
            "current_manifest_bytes": len(current_raw),
            "implicit_control_bytes": len(implicit_raw),
            "control_saving_bytes": len(current_raw) - len(implicit_raw),
            "expands_to_exact_filesystem_v1_semantics": semantic_exact,
            "existing_research_grammar": True,
        },
        "current_candidate": current,
        "implicit_v4_projection": implicit,
        "archive_saving_bytes": archive_saving,
        "minimum_useful_archive_saving_bytes": MIN_USEFUL_ARCHIVE_SAVING,
        "promotion_signal": archive_saving >= MIN_USEFUL_ARCHIVE_SAVING,
        "release_credit": False,
        "selector_change": False,
        "canonical_grammar_change": False,
        "claim_boundary": (
            "Research-only canonicalization-gap projection using the existing bounded implicit-v4 grammar. A "
            "positive signal only justifies integrating that control grammar into canonical r25 with exact reader, "
            "recovery, native, Android, locality, no-regression and all-15 authority."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r25-manifest-derived-identity-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r25-manifest-derived-identity.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "implicit_v4": result["implicit_v4"],
                "current_candidate_bytes": result["current_candidate"]["archive_bytes"],
                "implicit_candidate_bytes": result["implicit_v4_projection"]["archive_bytes"],
                "archive_saving_bytes": result["archive_saving_bytes"],
                "promotion_signal": result["promotion_signal"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
