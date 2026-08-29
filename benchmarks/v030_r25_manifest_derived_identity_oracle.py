from __future__ import annotations

"""Research-only A/B for removing duplicated regular-file identities from the r25 filesystem manifest.

Canonical r25 currently authenticates every regular file twice: once in the selected content graph and again as
``[size, sha256]`` inside the filesystem-semantics manifest. The duplication is especially expensive on
high-file-count workloads because SHA-256 values are deliberately incompressible. This oracle does *not* change
the shipping grammar. It creates a projection in which regular-file manifest rows retain metadata but replace
the duplicated content identity with ``None``; the user-file identities are then derived from the content graph.

The projected manifest is deliberately marked as a research v2 identity and is never handed to canonical product
readers. We measure complete release-candidate bytes only to decide whether a real cross-platform grammar change
is worth productizing. Release/native/Android/recovery credit is always false here.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil

import msgpack

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_candidate as RC

TARGET = "01_developer_repository"
RESEARCH_PROFILE = "cmpct-r25-filesystem-manifest-v2-derived-regular-identities-research"
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


def _derived_manifest(current_raw: bytes) -> tuple[bytes, dict]:
    manifest = msgpack.unpackb(current_raw, raw=False)
    regular_rows = 0
    duplicated_digest_bytes = 0
    for row in manifest["entries"]:
        if row[1] != "f":
            continue
        extra = row[7]
        if (
            not isinstance(extra, list)
            or len(extra) != 2
            or not isinstance(extra[0], int)
            or not isinstance(extra[1], bytes)
            or len(extra[1]) != 32
        ):
            raise RuntimeError("current r25 manifest regular identity drift")
        regular_rows += 1
        duplicated_digest_bytes += len(extra[1])
        row[7] = None
    manifest["v"] = 2
    manifest["profile"] = RESEARCH_PROFILE
    raw = msgpack.packb(manifest, use_bin_type=True)
    return raw, {
        "regular_rows": regular_rows,
        "duplicated_sha256_bytes": duplicated_digest_bytes,
        "current_manifest_bytes": len(current_raw),
        "derived_manifest_bytes": len(raw),
        "manifest_saving_bytes": len(current_raw) - len(raw),
    }


def _stage(regular_sources: list[tuple[Path, str]], manifest_raw: bytes, target: Path) -> None:
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    for source, rel in regular_sources:
        FS._link_or_copy(source, target.joinpath(*PurePosixPath(rel).parts))
    manifest_path = target.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_raw)


def _hash_file(path: Path) -> tuple[int, bytes]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.digest()


def _identity_join_proof(current_raw: bytes, regular_sources: list[tuple[Path, str]]) -> dict:
    manifest = msgpack.unpackb(current_raw, raw=False)
    declared = {row[0]: (int(row[7][0]), bytes(row[7][1])) for row in manifest["entries"] if row[1] == "f"}
    observed = {rel: _hash_file(source) for source, rel in regular_sources}
    if declared != observed:
        raise RuntimeError("current manifest and graph-owned source identities disagree")
    return {
        "regular_identity_count": len(observed),
        "source_identities_match_current_manifest": True,
        "derivation_rule": "join manifest regular path to authenticated content-graph (size, sha256)",
    }


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
    derived_raw, manifest_stats = _derived_manifest(current_raw)
    join = _identity_join_proof(current_raw, regular_sources)

    current_stage = work_root / "current-stage"
    derived_stage = work_root / "derived-stage"
    _stage(regular_sources, current_raw, current_stage)
    _stage(regular_sources, derived_raw, derived_stage)

    current = _build(current_stage, work_root / "current.cmpct")
    derived = _build(derived_stage, work_root / "derived.cmpct")
    archive_saving = int(current["archive_bytes"]) - int(derived["archive_bytes"])

    return {
        "schema": "cmpct-v030-r25-manifest-derived-identity-oracle-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "capture": capture,
        "manifest": manifest_stats,
        "identity_join_proof": join,
        "current_candidate": current,
        "derived_identity_projection": derived,
        "archive_saving_bytes": archive_saving,
        "minimum_useful_archive_saving_bytes": MIN_USEFUL_ARCHIVE_SAVING,
        "promotion_signal": archive_saving >= MIN_USEFUL_ARCHIVE_SAVING,
        "release_credit": False,
        "selector_change": False,
        "canonical_grammar_change": False,
        "claim_boundary": (
            "Research-only byte projection. A positive signal only justifies designing a bounded filesystem-manifest "
            "grammar whose regular content identities are joined from the already-authenticated graph. Python/native/"
            "Android readers, recovery, locality, no-regression and exact all-15 authority remain mandatory."
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
                "manifest": result["manifest"],
                "current_candidate_bytes": result["current_candidate"]["archive_bytes"],
                "derived_candidate_bytes": result["derived_identity_projection"]["archive_bytes"],
                "archive_saving_bytes": result["archive_saving_bytes"],
                "promotion_signal": result["promotion_signal"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
