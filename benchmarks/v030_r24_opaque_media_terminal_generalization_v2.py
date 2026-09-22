from __future__ import annotations

"""Entropy-refined adversarial proof for terminal r24 on opaque encoded media.

The v1 magic/shape predicate correctly recognized real high-entropy media-like trees but also admitted a
compressible JPEG-magic impostor. This refinement adds only a cheap, deterministic sampled-byte entropy test.
It does not inspect names, extensions, paths, hashes, workload identity, or comparator outcomes. Predicate cost
is charged inside CMPCT complete creation time. Research evidence only; no selector/release credit by itself.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import tempfile
import time

from benchmarks import v030_external_competitors as B
from benchmarks import v030_r24_opaque_media_terminal_generalization as V1
from benchmarks import v030_r24_opaque_media_terminal_oracle as MEDIA
from experiments import entropygraph_v030_release_product as PRODUCT

SAMPLE_PER_FILE = 64 * 1024
MAX_SAMPLED_FILES = 16
MIN_SAMPLE_BYTES = 256 * 1024
MIN_ENTROPY_BITS_PER_BYTE = 7.50


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _sample_opaque_bytes(root: Path) -> bytes:
    samples = bytearray()
    sampled = 0
    # Sorting is solely for deterministic traversal; path text is never part of the admission decision.
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if not MEDIA._is_opaque_encoded_media(path, size):
            continue
        with path.open("rb") as handle:
            samples.extend(handle.read(SAMPLE_PER_FILE))
        sampled += 1
        if sampled >= MAX_SAMPLED_FILES:
            break
    return bytes(samples)


def _refined_shape(root: Path) -> dict:
    shape = MEDIA._shape(root)
    sample = _sample_opaque_bytes(root)
    shape.update(
        {
            "sample_bytes": len(sample),
            "sample_entropy_bits_per_byte": _entropy(sample),
        }
    )
    return shape


def _eligible(shape: dict) -> bool:
    return (
        MEDIA._eligible(shape)
        and int(shape["sample_bytes"]) >= MIN_SAMPLE_BYTES
        and float(shape["sample_entropy_bits_per_byte"]) >= MIN_ENTROPY_BITS_PER_BYTE
    )


def _measure(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-media-gen-v2-", dir=work) as td:
        scratch = Path(td)
        stage = B._normalized_stage(source, scratch)
        product_tree = PRODUCT.treehash(stage)
        zip_result = B._zip(stage, scratch / "baseline.zip", scratch / "zip-out")
        zstd_result = B._tar_zstd(stage, scratch / "baseline.tar.zst", scratch / "zstd-out", scratch)
        if not zstd_result.get("available"):
            raise RuntimeError("solid Zstd-19 comparator unavailable")

        started = time.perf_counter()
        shape = _refined_shape(stage)
        eligible = _eligible(shape)
        predicate_s = time.perf_counter() - started
        row = {"label": label, **shape, "eligible": eligible, "predicate_s": predicate_s}
        if not eligible:
            return row

        archive = scratch / "terminal-r24.cmpct"
        PRODUCT._locality_bounded_r24_build(stage, archive)
        verified = PRODUCT.strong_verify(archive)
        complete_create_s = time.perf_counter() - started
        if not verified.get("ok") or verified.get("tree_sha256") != product_tree:
            raise RuntimeError(f"{label}: r24 verification/tree mismatch")
        archive_bytes = archive.stat().st_size
        gate = {
            "smaller_than_zip": archive_bytes < int(zip_result["archive_bytes"]),
            "smaller_than_zstd19": archive_bytes < int(zstd_result["archive_bytes"]),
            "faster_than_zip": complete_create_s < float(zip_result["create_s"]),
            "faster_than_zstd19": complete_create_s < float(zstd_result["create_s"]),
        }
        gate["passed"] = all(gate.values())
        row.update(
            {
                "archive_bytes": archive_bytes,
                "complete_create_s": complete_create_s,
                "zip": zip_result,
                "tar_zstd19": zstd_result,
                "gate": gate,
            }
        )
        return row


def run(work_root: Path) -> dict:
    if work_root.exists():
        import shutil
        shutil.rmtree(work_root)
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
        V1._write_case(source, count=count, kind=kind, compressible=compressible, opaque_count=opaque_count)
        row = _measure(label, source, work_root)
        rows.append(row)
        print(json.dumps({"label": label, "eligible": row["eligible"], "entropy": row["sample_entropy_bits_per_byte"], "gate": row.get("gate")}, separators=(",", ":")), flush=True)

    eligible = [r for r in rows if r["eligible"]]
    counterexamples = [r["label"] for r in eligible if not r["gate"]["passed"]]
    rejected = {r["label"]: not r["eligible"] for r in rows}
    expected_rejections = {
        "compressible-media-impostor": rejected["compressible-media-impostor"],
        "file-count-below-threshold": rejected["file-count-below-threshold"],
        "zip-container-exclusion": rejected["zip-container-exclusion"],
    }
    expected_admissions = {
        label: next(r for r in rows if r["label"] == label)["eligible"]
        for label in ("entropy-jpeg", "entropy-png", "entropy-mp4", "mixed-75pct-opaque")
    }
    return {
        "schema": "cmpct-v030-r24-opaque-media-terminal-generalization-v2-entropy",
        "claim_boundary": "unseen adversarial selector research only; predicate time included; no shipping/release credit",
        "admission": {
            "base_shape_predicate": "v1 opaque-media shape/magic",
            "sample_per_file": SAMPLE_PER_FILE,
            "max_sampled_files": MAX_SAMPLED_FILES,
            "minimum_sample_bytes": MIN_SAMPLE_BYTES,
            "minimum_entropy_bits_per_byte": MIN_ENTROPY_BITS_PER_BYTE,
            "forbidden_inputs": ["workload-name", "path-text", "filename", "extension", "content-hash", "archive-hash", "comparator-result"],
        },
        "rows": rows,
        "summary": {
            "cases": len(rows),
            "eligible_cases": len(eligible),
            "counterexamples": counterexamples,
            "expected_rejections": expected_rejections,
            "expected_admissions": expected_admissions,
            "promotion_signal": bool(eligible) and not counterexamples and all(expected_rejections.values()) and all(expected_admissions.values()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-opaque-media-generalization-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-opaque-media-generalization-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
