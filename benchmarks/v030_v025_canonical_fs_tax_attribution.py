from __future__ import annotations

"""Diagnostic-only attribution of the r25 canonical-filesystem tax on v0.25.

The current reactivation question is no longer whether v0.25/federation contains
useful predictive structure: exact repaired office/analytics v0.25 artifacts land
on the accepted v0.29 byte floors.  The narrower question is how many bytes are
introduced (or removed) when the *same* v0.25 representation, with the same
level-1 cap, stores the canonical filesystem staging tree required for a real r25
product.

For each frozen target this diagnostic builds two independently verified artifacts:

  raw_level1      normalized user tree -> unchanged v0.25, Zstd requests capped at 1
  canonical_level1 normalized user tree -> authenticated r25 filesystem staging ->
                   unchanged v0.25, the same Zstd cap

It therefore isolates filesystem/profile tax from compression-level effects.  It
also reports exact physical pack/metadata attribution for both artifacts.  It
changes no product, selector, format, or comparator and earns no release credit.
"""

import argparse
from contextlib import contextmanager
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_physical_attribution as ATTR
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = ("02_office_workspace", "04_analytics_and_database")
LEVEL_CAP = 1
MAX_PATH_BYTES = 4096


@contextmanager
def _level1(archive: Path, root: Path):
    old = (V25.ROOT, V25.OUT, V25.zc)
    original_zc = V25.zc
    V25.ROOT = root
    V25.OUT = archive

    def capped(raw: bytes, level: int = 19) -> bytes:
        return original_zc(raw, min(int(level), LEVEL_CAP))

    V25.zc = capped
    try:
        yield
    finally:
        V25.ROOT, V25.OUT, V25.zc = old


def _build_verified(root: Path, archive: Path, expected_tree: str) -> dict:
    with _level1(archive, root):
        started = time.perf_counter()
        stats = dict(V25.build())
        build_wall_s = time.perf_counter() - started
        started = time.perf_counter()
        verified = dict(V25.strong_verify())
        verify_wall_s = time.perf_counter() - started
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"v0.25 level-1 verification mismatch: {verified!r}")
    physical = ATTR._physical_attribution(archive)
    if physical["authenticated_tree_sha256"] != expected_tree:
        raise RuntimeError("v0.25 attribution identity drift")
    return {
        "archive_bytes": archive.stat().st_size,
        "build_wall_s": build_wall_s,
        "strong_verify_wall_s": verify_wall_s,
        "build_stats": stats,
        "physical_attribution": physical,
    }


def _one(name: str, source: Path, work: Path, accepted_v029_bytes: int) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"cmpct-v025-fs-tax-{name}-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized-root")
        expected_user_tree = PRODUCT.treehash(stage)

        raw_archive = root / "raw-level1.cmpnx5"
        raw = _build_verified(stage, raw_archive, V25.treehash(stage))

        profile = root / "canonical-profile"
        started = time.perf_counter()
        fs = FS.prepare_profile_tree(
            stage,
            profile,
            max_path_bytes=MAX_PATH_BYTES,
            max_profile_files=PRODUCT.MAX_PROFILE_FILES,
            max_profile_logical_bytes=PRODUCT.MAX_PROFILE_LOGICAL_BYTES,
            max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
        )
        fs_stage_wall_s = time.perf_counter() - started
        profile_tree = V25.treehash(profile)
        canonical_archive = root / "canonical-level1.cmpnx5"
        canonical = _build_verified(profile, canonical_archive, profile_tree)

        extracted = root / "canonical-out"
        with _level1(canonical_archive, profile):
            V25.extract(extracted)
        manifest_path = extracted.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise RuntimeError("canonical level-1 extraction omitted filesystem manifest")
        decoded = FS.decode_manifest(
            manifest_path.read_bytes(),
            max_path_bytes=MAX_PATH_BYTES,
            max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
        )
        FS.restore_manifest_tree(extracted, decoded)
        restored_user_tree = PRODUCT.treehash(extracted)
        if restored_user_tree != expected_user_tree:
            raise RuntimeError("canonical level-1 restored user-tree mismatch")

        raw_bytes = int(raw["archive_bytes"])
        canonical_bytes = int(canonical["archive_bytes"])
        return {
            "workload": name,
            "accepted_v029_bytes": int(accepted_v029_bytes),
            "canonical_user_tree_sha256": expected_user_tree,
            "raw_level1": raw,
            "canonical_level1": canonical,
            "filesystem": {
                "stage_wall_s": fs_stage_wall_s,
                "manifest_bytes": int(fs["manifest_bytes"]),
                "manifest_entries": int(fs["entries"]),
                "regular_graph_members": int(fs["regular_graph_members"]),
            },
            "delta": {
                "canonical_minus_raw_level1_bytes": canonical_bytes - raw_bytes,
                "raw_level1_minus_v029_bytes": raw_bytes - int(accepted_v029_bytes),
                "canonical_level1_minus_v029_bytes": canonical_bytes - int(accepted_v029_bytes),
            },
            "identities_verified": True,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_v025_canonical_fs_tax_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_v025_canonical_fs_tax_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    accepted = GENERAL._accepted_v029_rows()

    rows = []
    for name in TARGETS:
        source = corpus / name
        accepted_bytes = int(accepted[("neutral_hostile_v1", name)]["accepted_v029_bytes"])
        row = _one(name, source, work_root, accepted_bytes)
        rows.append(row)
        print(
            json.dumps(
                {
                    "workload": name,
                    "raw_level1_bytes": row["raw_level1"]["archive_bytes"],
                    "canonical_level1_bytes": row["canonical_level1"]["archive_bytes"],
                    "accepted_v029_bytes": accepted_bytes,
                    **row["delta"],
                },
                separators=(",", ":"),
            ),
            flush=True,
        )

    measurement = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_identities_verified": all(row["identities_verified"] for row in rows),
        "all_physical_accounting_exact": all(
            row[variant]["physical_attribution"]["physical"]["accounting_exact"]
            for row in rows
            for variant in ("raw_level1", "canonical_level1")
        ),
    }
    measurement["valid"] = all(measurement.values())
    return {
        "schema": "cmpct-v030-v025-canonical-fs-tax-attribution-v1",
        "level_cap": LEVEL_CAP,
        "targets": list(TARGETS),
        "rows": rows,
        "measurement": measurement,
        "claim_boundary": (
            "diagnostic-only causal attribution; no selector, canonical-format, release, native, Android, or shipping "
            "credit. Byte deltas compare the same unchanged v0.25 representation at the same level-1 cap, before "
            "and after paying the authenticated canonical-filesystem staging tax."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-v025-canonical-fs-tax-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-v025-canonical-fs-tax.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"measurement": result["measurement"]}, indent=2), flush=True)
    if not result["measurement"]["valid"]:
        raise SystemExit("canonical-filesystem tax attribution failed measurement integrity")


if __name__ == "__main__":
    main()
