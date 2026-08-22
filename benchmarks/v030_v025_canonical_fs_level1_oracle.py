from __future__ import annotations

"""Canonical-filesystem budget proof for the fast EntropyGraph-v0.25 mechanism.

The exact level frontier proved that CMPNX5 at a level-1 Zstd cap is already a strict size+verified-create winner
against ZIP/Deflate-9 and solid Zstd-19 on the frozen office and analytics workloads. CMPNX5 itself is not a
canonical format, so that result cannot receive release credit. This oracle asks the next productization question:
if the same representation is forced to pay the canonical r25 filesystem-manifest cost, does the four-way margin
survive?

For each target and each repeated round this lane:
- normalizes the frozen source tree exactly as the external-comparator matrix does;
- builds the canonical r25 filesystem staging tree with authenticated directory/mode/mtime/link semantics;
- stores that staging tree through the unchanged CMPNX5 representation with all internal Zstd requests capped at 1;
- charges filesystem staging + archive construction + mandatory CMPNX5 strong verification to creation time;
- extracts CMPNX5, decodes/restores the authenticated filesystem manifest, and compares the resulting canonical
  user-tree hash with the original source tree;
- freshly measures ZIP/Deflate-9 and solid tar+Zstd-19 on the same normalized source and rotated runner order.

This is still a productization *budget* proof, not a format promotion. CMPNX5 framing remains research-only and the
reader-visible representation has not yet been re-expressed as canonical r25. A green result means the canonical
filesystem tax is affordable and justifies building a bounded r25 profile with native/Android/recovery/locality
parity; it cannot satisfy any release receipt by itself.
"""

import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = ("02_office_workspace", "04_analytics_and_database")
LEVEL_CAP = 1
ROUNDS = 3
MAX_PATH_BYTES = 4096


def _canonical_v25(stage: Path, root: Path) -> dict:
    profile = root / "profile"
    archive = root / "candidate.cmpnx5"
    fs_started = time.perf_counter()
    fs_stats = FS.prepare_profile_tree(
        stage,
        profile,
        max_path_bytes=MAX_PATH_BYTES,
        max_profile_files=PRODUCT.MAX_PROFILE_FILES,
        max_profile_logical_bytes=PRODUCT.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    filesystem_stage_s = time.perf_counter() - fs_started

    V25.ROOT = profile
    V25.OUT = archive
    original_zc = V25.zc

    def capped_zc(raw: bytes, level: int = 19) -> bytes:
        return original_zc(raw, min(int(level), LEVEL_CAP))

    V25.zc = capped_zc
    try:
        started = time.perf_counter()
        build_stats = dict(V25.build())
        build_s = time.perf_counter() - started
    finally:
        V25.zc = original_zc

    started = time.perf_counter()
    verified = dict(V25.strong_verify())
    strong_verify_s = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError(f"canonical-filesystem CMPNX5 strong verification failed: {verified!r}")

    extracted_profile = root / "profile-out"
    V25.extract(extracted_profile)
    manifest_path = extracted_profile.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("canonical-filesystem CMPNX5 extraction omitted authenticated filesystem manifest")
    decoded = FS.decode_manifest(
        manifest_path.read_bytes(),
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    FS.restore_manifest_tree(extracted_profile, decoded)

    expected_user_tree = PRODUCT.treehash(stage)
    restored_user_tree = PRODUCT.treehash(extracted_profile)
    if restored_user_tree != expected_user_tree:
        raise RuntimeError(
            f"canonical-filesystem CMPNX5 restored user tree mismatch: {restored_user_tree} != {expected_user_tree}"
        )

    complete_create_s = filesystem_stage_s + build_s + strong_verify_s
    return {
        "archive_bytes": archive.stat().st_size,
        "filesystem_stage_s": filesystem_stage_s,
        "build_s": build_s,
        "strong_verify_s": strong_verify_s,
        "complete_verified_create_s": complete_create_s,
        "filesystem_manifest_bytes": int(fs_stats["manifest_bytes"]),
        "filesystem_manifest_entries": int(fs_stats["entries"]),
        "filesystem_manifest_sha256": str(fs_stats["manifest_sha256"]),
        "build_stats": build_stats,
        "verified": verified,
        "canonical_user_tree_sha256": restored_user_tree,
    }


def _one(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-v025-canonical-fs-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized-root")
        expected_external_tree = EXT._tree(stage)
        expected_user_tree = PRODUCT.treehash(stage)
        names = ["candidate", "zip", "zstd19"]
        samples = {name: [] for name in names}
        sizes = {name: set() for name in names}
        candidate_parts = []
        base_order = list(names)

        for round_index in range(ROUNDS):
            shift = round_index % len(base_order)
            order = base_order[shift:] + base_order[:shift]
            round_root = root / f"round-{round_index}"
            round_root.mkdir()
            for engine in order:
                engine_root = round_root / engine
                engine_root.mkdir()
                if engine == "candidate":
                    result = _canonical_v25(stage, engine_root)
                    samples[engine].append(float(result["complete_verified_create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))
                    candidate_parts.append({
                        "filesystem_stage_s": float(result["filesystem_stage_s"]),
                        "build_s": float(result["build_s"]),
                        "strong_verify_s": float(result["strong_verify_s"]),
                        "filesystem_manifest_bytes": int(result["filesystem_manifest_bytes"]),
                        "filesystem_manifest_entries": int(result["filesystem_manifest_entries"]),
                        "canonical_user_tree_sha256": result["canonical_user_tree_sha256"],
                    })
                    if result["canonical_user_tree_sha256"] != expected_user_tree:
                        raise RuntimeError("candidate canonical user-tree identity drift")
                elif engine == "zip":
                    result = EXT._zip(stage, engine_root / "archive.zip", engine_root / "out")
                    EXT._verify_extracted(engine_root / "out", expected_external_tree, "zip_deflate9")
                    samples[engine].append(float(result["create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))
                else:
                    result = EXT._tar_zstd(
                        stage,
                        engine_root / "archive.tar.zst",
                        engine_root / "out",
                        engine_root,
                    )
                    if not result.get("available"):
                        raise RuntimeError(f"solid Zstd-19 unavailable: {result!r}")
                    EXT._verify_extracted(engine_root / "out", expected_external_tree, "tar_zstd19_solid")
                    samples[engine].append(float(result["create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))

        if any(len(values) != 1 for values in sizes.values()):
            raise RuntimeError(f"nondeterministic archive size in {label}: {sizes!r}")
        medians = {name: statistics.median(values) for name, values in samples.items()}
        byte_values = {name: next(iter(values)) for name, values in sizes.items()}
        strict = {
            "smaller_than_zip": byte_values["candidate"] < byte_values["zip"],
            "smaller_than_zstd19": byte_values["candidate"] < byte_values["zstd19"],
            "verified_create_faster_than_zip": medians["candidate"] < medians["zip"],
            "verified_create_faster_than_zstd19": medians["candidate"] < medians["zstd19"],
        }
        strict["four_way"] = all(strict.values())
        return {
            "label": label,
            "external_tree_sha256": expected_external_tree,
            "canonical_user_tree_sha256": expected_user_tree,
            "level_cap": LEVEL_CAP,
            "candidate": {
                "archive_bytes": byte_values["candidate"],
                "median_complete_verified_create_s": medians["candidate"],
                "raw_complete_verified_create_s": samples["candidate"],
                "parts": candidate_parts,
            },
            "comparators": {
                "zip": {
                    "archive_bytes": byte_values["zip"],
                    "median_create_s": medians["zip"],
                    "raw_create_s": samples["zip"],
                },
                "zstd19": {
                    "archive_bytes": byte_values["zstd19"],
                    "median_create_s": medians["zstd19"],
                    "raw_create_s": samples["zstd19"],
                },
            },
            "strict": strict,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_v025_canonical_fs_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_v025_canonical_fs_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    rows = []
    for name in TARGETS:
        source = corpus / name
        if not source.is_dir():
            raise RuntimeError(f"missing frozen workload {name}")
        row = _one(f"neutral_hostile_v1/{name}", source, work_root)
        rows.append(row)
        print(json.dumps({"label": row["label"], "strict": row["strict"]}, separators=(",", ":")), flush=True)

    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_rounds_complete": all(
            len(row["candidate"]["raw_complete_verified_create_s"]) == ROUNDS
            and len(row["comparators"]["zip"]["raw_create_s"]) == ROUNDS
            and len(row["comparators"]["zstd19"]["raw_create_s"]) == ROUNDS
            for row in rows
        ),
        "all_sizes_deterministic": True,
        "all_canonical_user_trees_verified": all(bool(row["canonical_user_tree_sha256"]) for row in rows),
        "all_rows_preserve_four_way_after_filesystem_tax": all(row["strict"]["four_way"] for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-v025-canonical-fs-level1-v1",
        "targets": list(TARGETS),
        "level_cap": LEVEL_CAP,
        "rounds": ROUNDS,
        "rows": rows,
        "gate": gate,
        "claim_boundary": (
            "canonical filesystem tax / productization-budget proof only; CMPNX5 framing remains research-only. "
            "A green result authorizes engineering a bounded canonical r25 profile, not release or selector credit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-v025-canonical-fs-level1-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-v025-canonical-fs-level1.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.25 level-1 canonical-filesystem productization budget failed")


if __name__ == "__main__":
    main()
