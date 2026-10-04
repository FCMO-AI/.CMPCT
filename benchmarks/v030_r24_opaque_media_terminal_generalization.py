from __future__ import annotations

"""Adversarial/generalization proof for the r24 opaque-media terminal predicate.

This deliberately includes media-magic impostors with very compressible payloads, threshold neighbors,
and independent high-entropy media-like trees. A frozen-suite success is not sufficient for selector promotion:
any eligible unseen case that fails the strict r24-vs-ZIP-vs-Zstd size+creation contract rejects the predicate.
Research evidence only; this file cannot alter product selection.
"""

import argparse
import json
from pathlib import Path
import random
import shutil
import tempfile
import time

from benchmarks import v030_external_competitors as B
from benchmarks import v030_r24_opaque_media_terminal_oracle as MEDIA
from experiments import entropygraph_v030_release_product as PRODUCT

CHUNK = 512 * 1024


def _bytes(seed: int, size: int) -> bytes:
    return random.Random(seed).randbytes(size)


def _write_case(root: Path, *, count: int, kind: str, compressible: bool = False, opaque_count: int | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    opaque_count = count if opaque_count is None else opaque_count
    for i in range(count):
        if i >= opaque_count:
            data = (b"ordinary-text-row,%08d\n" % i) * (CHUNK // 24)
            data = data[:CHUNK]
        elif compressible:
            data = b"\xff\xd8\xff" + bytes(CHUNK - 3)
        else:
            body = _bytes(10_000 + i, CHUNK - 16)
            if kind == "jpeg":
                data = b"\xff\xd8\xff" + b"JFIF" + bytes(9) + body
            elif kind == "png":
                data = b"\x89PNG\r\n\x1a\n" + bytes(8) + body
            elif kind == "flac":
                data = b"fLaC" + bytes(12) + body
            elif kind == "mp3":
                data = b"ID3" + bytes(13) + body
            elif kind == "mp4":
                data = (16).to_bytes(4, "big") + b"ftypisom" + bytes(4) + body
            elif kind == "zip":
                data = b"PK\x03\x04" + bytes(12) + body
            else:
                raise ValueError(kind)
        (root / f"member-{i:03d}.dat").write_bytes(data)


def _measure(label: str, source: Path, work: Path) -> dict:
    shape = MEDIA._shape(source)
    eligible = MEDIA._eligible(shape)
    row = {"label": label, **shape, "eligible": eligible}
    if not eligible:
        return row
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-media-gen-", dir=work) as td:
        scratch = Path(td)
        stage = B._normalized_stage(source, scratch)
        product_tree = PRODUCT.treehash(stage)
        zip_result = B._zip(stage, scratch / "baseline.zip", scratch / "zip-out")
        zstd_result = B._tar_zstd(stage, scratch / "baseline.tar.zst", scratch / "zstd-out", scratch)
        if not zstd_result.get("available"):
            raise RuntimeError("solid Zstd-19 comparator unavailable")
        archive = scratch / "terminal-r24.cmpct"
        started = time.perf_counter()
        PRODUCT._locality_bounded_r24_build(stage, archive)
        verified = PRODUCT.strong_verify(archive)
        create_s = time.perf_counter() - started
        if not verified.get("ok") or verified.get("tree_sha256") != product_tree:
            raise RuntimeError(f"{label}: r24 verification/tree mismatch")
        archive_bytes = archive.stat().st_size
        gate = {
            "smaller_than_zip": archive_bytes < int(zip_result["archive_bytes"]),
            "smaller_than_zstd19": archive_bytes < int(zstd_result["archive_bytes"]),
            "faster_than_zip": create_s < float(zip_result["create_s"]),
            "faster_than_zstd19": create_s < float(zstd_result["create_s"]),
        }
        gate["passed"] = all(gate.values())
        row.update({
            "archive_bytes": archive_bytes,
            "complete_create_s": create_s,
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "gate": gate,
        })
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    specs = [
        ("entropy-jpeg", 16, "jpeg", False, None),
        ("entropy-png", 16, "png", False, None),
        ("entropy-mp4", 16, "mp4", False, None),
        ("compressible-media-impostor", 16, "jpeg", True, None),
        ("mixed-75pct-opaque", 16, "flac", False, 12),
        ("file-count-below-threshold", 7, "mp3", False, None),
        ("zip-container-exclusion", 16, "zip", False, None),
    ]
    rows = []
    for label, count, kind, compressible, opaque_count in specs:
        source = work_root / "cases" / label
        _write_case(source, count=count, kind=kind, compressible=compressible, opaque_count=opaque_count)
        row = _measure(label, source, work_root)
        rows.append(row)
        print(json.dumps({"label": label, "eligible": row["eligible"], "gate": row.get("gate")}, separators=(",", ":")), flush=True)
    eligible = [r for r in rows if r["eligible"]]
    counterexamples = [r["label"] for r in eligible if not r["gate"]["passed"]]
    expected_rejections = {
        "file-count-below-threshold": not next(r for r in rows if r["label"] == "file-count-below-threshold")["eligible"],
        "zip-container-exclusion": not next(r for r in rows if r["label"] == "zip-container-exclusion")["eligible"],
    }
    return {
        "schema": "cmpct-v030-r24-opaque-media-terminal-generalization-v1",
        "claim_boundary": "unseen adversarial selector research only; no shipping/release credit",
        "admission_constants": {
            "min_regular_files": MEDIA.MIN_REGULAR_FILES,
            "max_regular_files": MEDIA.MAX_REGULAR_FILES,
            "min_logical_bytes": MEDIA.MIN_LOGICAL_BYTES,
            "min_opaque_share": MEDIA.MIN_OPAQUE_BYTE_SHARE,
        },
        "rows": rows,
        "summary": {
            "cases": len(rows),
            "eligible_cases": len(eligible),
            "counterexamples": counterexamples,
            "all_eligible_pass": bool(eligible) and not counterexamples,
            "expected_rejections": expected_rejections,
            "promotion_signal": bool(eligible) and not counterexamples and all(expected_rejections.values()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-opaque-media-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-opaque-media-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
