from __future__ import annotations

"""Research-only exact-ML A/B for a faster G04 delimiter inverse.

The candidate changes no archive bytes and is injected only into the reader's owning Geometry module after a
canonical revision-25 shipping ML archive has been built and strongly verified. Control and candidate extract the
same archive to fresh destinations; every output must equal the same semantic source tree. Timing is mechanism
attribution only and receives no release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
ROUNDS = 9
MIN_SPEEDUP = 0.15


def delimiter_inverse_banded(encoded: bytes, logical_size: int) -> bytes:
    O = G04.O
    if not encoded.startswith(b"DGO1") or len(encoded) < 6 or logical_size < 0 or logical_size > O.MAX_OVERLAY_RECORD:
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")
    lengths: list[int] = []
    logical_members = 0
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length)
        logical_members += length
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    if count * max(lengths, default=0) > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    starts: list[int] = []
    cursor = 0
    for index, length in enumerate(lengths):
        starts.append(cursor)
        cursor += length + (1 if index + 1 < count else 0)
    if cursor != logical_size:
        raise RuntimeError("Geometry overlay delimiter output-size mismatch")
    out = bytearray(logical_size)
    for index in range(count - 1):
        out[starts[index] + lengths[index]] = delimiter

    body_offset = 0
    previous = 0
    for end in sorted(set(lengths)):
        width = end - previous
        if width <= 0:
            continue
        active = [index for index, length in enumerate(lengths) if length >= end]
        active_count = len(active)
        band_bytes = active_count * width
        band = body[body_offset:body_offset + band_bytes]
        if len(band) != band_bytes:
            raise RuntimeError("Geometry overlay delimiter band underflow")
        for rank, index in enumerate(active):
            out[starts[index] + previous:starts[index] + end] = band[rank::active_count]
        body_offset += band_bytes
        previous = end
    if body_offset != len(body):
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return bytes(out)


def _assert_nested_g04_selected(built: dict) -> None:
    # Canonical r25 is the outer archive grammar. G04 is a nested physical-record strategy, so checking the outer
    # archive magic against G04.MAG is category-wrong and previously caused an infrastructure false negative.
    g04 = built.get("r25", {}).get("g04", {})
    auditions = g04.get("auditions", [])
    selected = [row for row in auditions if row.get("selected") not in (None, "none")]
    if not selected:
        raise RuntimeError("canonical ML r25 archive did not select any G04 overlay records")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpus")[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    built = PRODUCT.build(source, archive)
    _assert_nested_g04_selected(built)
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("canonical ML archive failed strong verification")

    original = G04.O.delimiter_inverse
    control: list[float] = []
    candidate: list[float] = []
    try:
        for round_index in range(ROUNDS):
            order = ("control", "candidate") if round_index % 2 == 0 else ("candidate", "control")
            for arm in order:
                G04.O.delimiter_inverse = original if arm == "control" else delimiter_inverse_banded
                dst = work_root / f"{arm}-{round_index}"
                started = time.perf_counter()
                PRODUCT.extract(archive, dst)
                elapsed = time.perf_counter() - started
                if PRODUCT.treehash(dst) != source_tree:
                    raise RuntimeError(f"{arm} extraction identity failure")
                (control if arm == "control" else candidate).append(elapsed)
    finally:
        G04.O.delimiter_inverse = original

    control_median = float(statistics.median(control))
    candidate_median = float(statistics.median(candidate))
    ratio = candidate_median / max(control_median, 1e-12)
    return {
        "schema": "cmpct-v030-g04-delimiter-inverse-ab-v1",
        "target": "/".join(TARGET),
        "release_credit": False,
        "archive_bytes": archive.stat().st_size,
        "source_tree_sha256": source_tree,
        "shipping_build": built,
        "rounds": ROUNDS,
        "control_s": control,
        "candidate_s": candidate,
        "control_median_s": control_median,
        "candidate_median_s": candidate_median,
        "candidate_ratio": ratio,
        "speedup_fraction": 1.0 - ratio,
        "promotion_signal": bool(ratio <= 1.0 - MIN_SPEEDUP),
        "minimum_speedup_fraction": MIN_SPEEDUP,
        "product_source_changed": False,
        "archive_bytes_changed": False,
        "release_thresholds_changed": False,
        "claim_boundary": "Exact-archive reader mechanism A/B only. Promotion requires guarded production implementation plus fresh-process authority-v2 and full correctness/platform evidence.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("control_median_s", "candidate_median_s", "candidate_ratio", "speedup_fraction", "promotion_signal", "release_credit")}, indent=2))


if __name__ == "__main__":
    main()
