from __future__ import annotations

"""All-15 structural terminal-r24 oracle for already-encoded media-heavy trees.

The exact external matrix shows a large self-inflicted creation loss on the media workload: canonical r24 is already
smaller and faster than both ZIP/Deflate-9 and solid Zstd-19, but the full product spends ~minute-scale time building
a smaller G0-G4 candidate. This oracle asks whether a cheap, benchmark-identity-free source predicate can safely
terminalize the already-winning r24 representation.

Admission uses only regular-file shape and magic-byte evidence that the majority of logical bytes are already in
opaque encoded media containers (JPEG, PNG, ISO-BMFF/MP4, FLAC, MP3). ZIP-family magic is deliberately excluded:
office documents are ZIP containers whose cross-file redundancy is exactly where solid/federated transforms can
still beat r24. Paths, filenames, extensions, workload labels, content hashes, archive hashes and frozen pack hashes
never participate in admission.

Research evidence only. A positive all-15 result must still survive an independent adversarial/generalization suite
before the predicate may be promoted into the shipping selector.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time

from benchmarks import v030_external_competitors as B
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT

MIN_REGULAR_FILES = 8
MAX_REGULAR_FILES = 128
MIN_LOGICAL_BYTES = 8 * 1024 * 1024
MIN_OPAQUE_BYTE_SHARE = 0.70


def _is_opaque_encoded_media(path: Path, size: int) -> bool:
    if size <= 0:
        return False
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError:
        return False
    if head.startswith(b"\xff\xd8\xff"):  # JPEG
        return True
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if head.startswith(b"fLaC"):
        return True
    if head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return True
    # ISO Base Media File Format: box length then 'ftyp'. This covers ordinary MP4/M4A-family encoded media.
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return True
    return False


def _shape(root: Path) -> dict:
    regular_files = 0
    logical_bytes = 0
    opaque_bytes = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            size = int(st.st_size)
            regular_files += 1
            logical_bytes += size
            if _is_opaque_encoded_media(path, size):
                opaque_bytes += size
    share = opaque_bytes / max(1, logical_bytes)
    return {
        "regular_files": regular_files,
        "logical_bytes": logical_bytes,
        "opaque_encoded_media_bytes": opaque_bytes,
        "opaque_encoded_media_share": share,
    }


def _eligible(shape: dict) -> bool:
    return (
        MIN_REGULAR_FILES <= int(shape["regular_files"]) <= MAX_REGULAR_FILES
        and int(shape["logical_bytes"]) >= MIN_LOGICAL_BYTES
        and float(shape["opaque_encoded_media_share"]) >= MIN_OPAQUE_BYTE_SHARE
    )


def _one(label: str, source: Path, accepted_v029_bytes: int, work: Path) -> dict:
    shape = _shape(source)
    eligible = _eligible(shape)
    row = {"label": label, **shape, "eligible": eligible}
    if not eligible:
        return row

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-opaque-media-terminal-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)
        historical_tree = B._tree(source)
        product_tree = PRODUCT.treehash(stage)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        if not zstd_result.get("available"):
            raise RuntimeError("solid Zstd-19 comparator unavailable")
        B._verify_extracted(root / "zip-out", historical_tree, "zip")
        B._verify_extracted(root / "zstd-out", historical_tree, "zstd")

        archive = root / "terminal-r24.cmpct"
        started = time.perf_counter()
        build_stats = PRODUCT._locality_bounded_r24_build(stage, archive)
        verified = PRODUCT.strong_verify(archive)
        complete_create_s = time.perf_counter() - started
        if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
            raise RuntimeError(f"opaque-media terminal r24 failed strong verification: {verified!r}")
        if verified.get("tree_sha256") != product_tree:
            raise RuntimeError(
                f"opaque-media terminal r24 product-tree mismatch: {verified.get('tree_sha256')!r} != {product_tree!r}"
            )

        archive_bytes = archive.stat().st_size
        gate = {
            "strictly_smaller_than_v029": archive_bytes < accepted_v029_bytes,
            "strictly_smaller_than_zip": archive_bytes < int(zip_result["archive_bytes"]),
            "strictly_smaller_than_zstd19": archive_bytes < int(zstd_result["archive_bytes"]),
            "strictly_faster_than_zip": complete_create_s < float(zip_result["create_s"]),
            "strictly_faster_than_zstd19": complete_create_s < float(zstd_result["create_s"]),
            "strong_verify_green": True,
            "product_tree_match": True,
        }
        gate["passed"] = all(gate.values())
        row.update(
            {
                "historical_tree_sha256": historical_tree,
                "product_tree_sha256": product_tree,
                "accepted_v029_bytes": accepted_v029_bytes,
                "archive_bytes": archive_bytes,
                "complete_create_s": complete_create_s,
                "zip": zip_result,
                "tar_zstd19": zstd_result,
                "build_stats": build_stats,
                "gate": gate,
            }
        )
        return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_opaque_media_terminal_neutral"
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_opaque_media_terminal_hostile"
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_opaque_media_terminal_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected = accepted[key]
            historical_tree = B._tree(workload)
            if historical_tree != expected["tree_sha256"]:
                raise RuntimeError(f"opaque-media historical source drift: {suite}/{workload.name}")
            row = _one(
                f"{suite}/{workload.name}", workload, int(expected["accepted_v029_bytes"]), work_root
            )
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            print(
                json.dumps(
                    {
                        "label": row["label"],
                        "eligible": row["eligible"],
                        "share": row["opaque_encoded_media_share"],
                        "files": row["regular_files"],
                        "gate": row.get("gate"),
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )

    eligible = [row for row in rows if row["eligible"]]
    counterexamples = [row["label"] for row in eligible if not row["gate"]["passed"]]
    return {
        "schema": "cmpct-v030-r24-opaque-media-terminal-v1",
        "claim_boundary": "all-15 structural admission research only; no selector/native/Android/release authority",
        "admission": {
            "regular_files": [MIN_REGULAR_FILES, MAX_REGULAR_FILES],
            "minimum_logical_bytes": MIN_LOGICAL_BYTES,
            "minimum_opaque_encoded_media_byte_share": MIN_OPAQUE_BYTE_SHARE,
            "recognized_magic": ["jpeg", "png", "iso-bmff-ftyp", "flac", "mp3"],
            "explicitly_excluded_from_opaque_magic": ["zip-family"],
            "forbidden_inputs": ["workload-name", "path", "filename", "extension", "content-hash", "archive-hash", "pack-hash"],
        },
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "eligible_workloads": len(eligible),
            "eligible_labels": [row["label"] for row in eligible],
            "counterexamples": counterexamples,
            "all_eligible_pass": bool(eligible) and not counterexamples,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-opaque-media-terminal-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-opaque-media-terminal.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)
    # A zero-admission or counterexample result is valid negative evidence. The workflow records it without granting
    # promotion credit; only malformed/incomplete evidence should fail the experiment lane itself.


if __name__ == "__main__":
    main()
