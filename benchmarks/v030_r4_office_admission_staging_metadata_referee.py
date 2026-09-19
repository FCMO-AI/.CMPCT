from __future__ import annotations

"""Falsify runtime staging-metadata leakage in the Office admission candidate.

The source-mtime-only referee proved that equal source metadata is insufficient:
copytree followed by unlink still changes staging-directory mtimes before the
canonical Builder snapshots filesystem metadata. This referee changes no product
semantics. It restores each surviving staging directory's metadata from the exact
source directory *after* admission pruning and immediately before PRODUCT.build.

Hypothesis
----------
The remaining 2-byte fresh-build drift is caused by runtime directory metadata
introduced by the research harness while deleting admitted/derived paths.

Disproof
--------
Two independently generated, content-identical Office roots are first normalized to
identical filesystem mtimes. If restoring surviving staging-directory metadata from
the corresponding source directories still fails to produce byte-identical complete
candidate components, staging-directory mtime leakage is not a sufficient cause.

This is diagnostic only. It does not authorize dropping mtimes, changing filesystem
fidelity, changing admission thresholds/codecs, or granting locality/release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_admission_mtime_causality_referee as MTIME
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_admission_transfer as ADMIT
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-admission-staging-metadata-referee-v1"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_source(work: Path, label: str) -> Path:
    neutral = V029._load(
        V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        f"r4_admitstage_neutral_{label}",
    )
    repair = V029._load(V029.REPAIR_PATH, f"r4_admitstage_repair_{label}")
    repair.install_generation_hooks(neutral)
    corpus = work / f"neutral-{label}"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    MTIME._fix_mtimes(source)
    return source


def _restore_surviving_directory_metadata(source: Path, staging: Path) -> int:
    restored = 0
    # Deepest-first is unnecessary for copystat itself, but makes the operation
    # insensitive to any future traversal helper that touches a parent directory.
    dirs = [source] + sorted(
        (p for p in source.rglob("*") if p.is_dir() and not p.is_symlink()),
        key=lambda p: len(p.relative_to(source).parts),
        reverse=True,
    )
    for src in dirs:
        rel = src.relative_to(source)
        dst = staging / rel
        if dst.exists() and dst.is_dir() and not dst.is_symlink():
            shutil.copystat(src, dst, follow_symlinks=False)
            restored += 1
    return restored


def _build_with_staging_restore(source: Path, out: Path, work: Path) -> dict:
    original_build = ADMIT.PRODUCT.build
    observed: dict[str, int | str] = {}

    def wrapped_build(staging: Path, archive: Path, *args, **kwargs):
        observed["staging_tree_before_restore"] = PRODUCT.treehash(staging)
        observed["restored_directories"] = _restore_surviving_directory_metadata(source, staging)
        observed["staging_tree_after_restore"] = PRODUCT.treehash(staging)
        return original_build(staging, archive, *args, **kwargs)

    ADMIT.PRODUCT.build = wrapped_build
    try:
        cand = ADMIT._build_candidate(source, out, work)
    finally:
        ADMIT.PRODUCT.build = original_build

    verify = SFV4.extract_candidate(out, work.parent / f"extract-{out.name}")
    expected = PRODUCT.treehash(source)
    if verify["tree_sha256"] != expected:
        raise RuntimeError("staging-restored candidate tree mismatch")
    if cand["derived_file_count"] != 8:
        raise RuntimeError("staging-restored candidate lost an exact derived view")

    files = sorted(p for p in out.iterdir() if p.is_file())
    return {
        "tree_sha256": expected,
        "stored_bytes": sum(p.stat().st_size for p in files),
        "component_bytes": {p.name: p.stat().st_size for p in files},
        "component_sha256": {p.name: _sha256(p) for p in files},
        "restored_directories": int(observed["restored_directories"]),
        "staging_content_tree_before_restore": observed["staging_tree_before_restore"],
        "staging_content_tree_after_restore": observed["staging_tree_after_restore"],
        "admitted_containers": cand["admitted_containers"],
        "rejected_containers": cand["rejected_containers"],
        "stream_roots": cand["stream_roots"],
        "derived_file_count": cand["derived_file_count"],
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    source_a = _build_source(work, "a")
    source_b = _build_source(work, "b")

    source_meta_a = MTIME._metadata_rows(source_a)
    source_meta_b = MTIME._metadata_rows(source_b)
    source_metadata_equal = MTIME._metadata_digest(source_meta_a) == MTIME._metadata_digest(source_meta_b)
    source_content_equal = PRODUCT.treehash(source_a) == PRODUCT.treehash(source_b)

    a = _build_with_staging_restore(source_a, work / "candidate-a", work / "work-a")
    b = _build_with_staging_restore(source_b, work / "candidate-b", work / "work-b")

    same_sizes = a["component_bytes"] == b["component_bytes"]
    same_hashes = a["component_sha256"] == b["component_sha256"]
    same_total = a["stored_bytes"] == b["stored_bytes"]
    staging_restore_sufficient = (
        source_content_equal
        and source_metadata_equal
        and same_sizes
        and same_hashes
        and same_total
        and a["staging_content_tree_before_restore"] == a["staging_content_tree_after_restore"]
        and b["staging_content_tree_before_restore"] == b["staging_content_tree_after_restore"]
    )

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": {
            "content_equal": source_content_equal,
            "metadata_equal": source_metadata_equal,
            "tree_sha256_a": PRODUCT.treehash(source_a),
            "tree_sha256_b": PRODUCT.treehash(source_b),
        },
        "candidate_a": a,
        "candidate_b": b,
        "hypothesis": {
            "fresh_candidate_total_equal": same_total,
            "fresh_candidate_component_sizes_equal": same_sizes,
            "fresh_candidate_byte_identical": same_hashes,
            "staging_restore_sufficient": staging_restore_sufficient,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "product_builder_changed": False,
            "filesystem_fidelity_weakened": False,
            "admission_thresholds_or_codecs_changed": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-admission-staging-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-admission-staging.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "candidate_bytes": {"a": d["candidate_a"]["stored_bytes"], "b": d["candidate_b"]["stored_bytes"]},
        "restored_directories": {"a": d["candidate_a"]["restored_directories"], "b": d["candidate_b"]["restored_directories"]},
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))
    if not d["hypothesis"]["staging_restore_sufficient"]:
        raise SystemExit("staging-directory metadata hypothesis falsified")


if __name__ == "__main__":
    main()
