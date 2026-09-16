from __future__ import annotations

"""Research-only exact-ML A/B for the shipping guarded G04 delimiter inverse.

The earlier unguarded banded candidate was ~50% slower and is durably retired. This follow-up tests the actual
shipping guarded implementation against its reviewed bulk-v1 semantic predecessor on the same canonical revision-25
ML archive. Archive bytes and release thresholds are unchanged; this is mechanism attribution only.
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


def _implementations():
    canonical = PRODUCT.C
    candidate = getattr(canonical, "_banded_delimiter_inverse", None)
    control = getattr(canonical, "_BULK_V1_DELIMITER_INVERSE", None)
    if candidate is None or control is None:
        raise RuntimeError("canonical guarded/bulk delimiter implementations unavailable")
    return control, candidate


def _property_check() -> int:
    """Differently shaped exactness controls before any timing claim."""
    O = G04.O
    control, candidate = _implementations()
    cases = [
        (b"", 0),
        (b"single-member", 0),
        (b"a,b,c,d", ord(",")),
        (b",leading,,empty,trailing,", ord(",")),
        (b"x" * 4096 + b"|" + b"y" * 3 + b"|" + b"z" * 1024, ord("|")),
        (b"\x00".join(bytes((index,)) * (index % 17) for index in range(1, 128)), 0),
    ]
    checked = 0
    for raw, delimiter in cases:
        encoded = O.delimiter_forward(raw, delimiter)
        baseline = control(encoded, len(raw))
        guarded = candidate(encoded, len(raw))
        if baseline != raw or guarded != raw or guarded != baseline:
            raise RuntimeError("delimiter inverse property-control mismatch")
        checked += 1
    return checked


def _assert_nested_g04_selected(built: dict) -> None:
    g04 = built.get("r25", {}).get("g04", {})
    auditions = g04.get("auditions", [])
    selected = [row for row in auditions if row.get("selected") not in (None, "none")]
    if not selected:
        raise RuntimeError("canonical ML r25 archive did not select any G04 overlay records")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    property_cases_checked = _property_check()
    source = PERF._build_corpora(work_root / "corpus")[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    built = PRODUCT.build(source, archive)
    _assert_nested_g04_selected(built)
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("canonical ML archive failed strong verification")

    control_impl, candidate_impl = _implementations()
    original = G04.O.delimiter_inverse
    control: list[float] = []
    candidate: list[float] = []
    try:
        for round_index in range(ROUNDS):
            order = ("control", "candidate") if round_index % 2 == 0 else ("candidate", "control")
            for arm in order:
                G04.O.delimiter_inverse = control_impl if arm == "control" else candidate_impl
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
        "property_cases_checked": property_cases_checked,
        "archive_bytes": archive.stat().st_size,
        "source_tree_sha256": source_tree,
        "shipping_build": built,
        "rounds": ROUNDS,
        "control_implementation": "reviewed-bulk-rectangular-prefix-v1",
        "candidate_implementation": getattr(PRODUCT.C, "DELIMITER_INVERSE_IMPLEMENTATION", "guarded-banded-v2"),
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
        "claim_boundary": "Exact-archive reader mechanism A/B only. The candidate is already present in the research release branch; release credit still requires fresh authority-v2 and full correctness/platform evidence.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("property_cases_checked", "control_implementation", "candidate_implementation", "control_median_s", "candidate_median_s", "candidate_ratio", "speedup_fraction", "promotion_signal", "release_credit")}, indent=2))


if __name__ == "__main__":
    main()
