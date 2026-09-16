from __future__ import annotations

"""Research-only exact-ML A/B for the shipping G04 delimiter inverse.

The release product owns a private canonical Geometry module graph. This oracle therefore patches that exact
shipping reader object, not the public historical Geometry module. Control is the reviewed bulk-v1 predecessor;
candidate is the currently installed release single-buffer inverse. Archive bytes and thresholds are unchanged.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
ROUNDS = 9
MIN_SPEEDUP = 0.15


def delimiter_inverse_banded(encoded: bytes, logical_size: int) -> bytes:
    """Stable regression seam for the formerly named banded candidate.

    The banded research implementation was superseded by the release-owned single-buffer inverse, but the hostile
    exactness tests intentionally remain as differently rooted fixtures.  Route them through the current promoted
    implementation instead of leaving a dead import that prevents the full regression suite from collecting.
    """
    return PRODUCT.C.SHARED.G.O.delimiter_inverse(encoded, logical_size)


def _implementations():
    canonical = PRODUCT.C
    control = getattr(canonical, "_BULK_V1_DELIMITER_INVERSE", None)
    candidate = canonical.SHARED.G.O.delimiter_inverse
    if control is None or candidate is None:
        raise RuntimeError("canonical delimiter implementations unavailable")
    return control, candidate


def _property_check() -> int:
    """Differently shaped exactness controls before any timing claim."""
    O = PRODUCT.C.SHARED.G.O
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
        shipping = candidate(encoded, len(raw))
        if baseline != raw or shipping != raw or shipping != baseline:
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
    canonical_o = PRODUCT.C.SHARED.G.O
    policy_o = getattr(PRODUCT.C.POLICY.R.G04, "O", None)
    original_canonical = canonical_o.delimiter_inverse
    original_policy = None if policy_o is None else policy_o.delimiter_inverse
    control: list[float] = []
    candidate: list[float] = []
    try:
        for round_index in range(ROUNDS):
            order = ("control", "candidate") if round_index % 2 == 0 else ("candidate", "control")
            for arm in order:
                implementation = control_impl if arm == "control" else candidate_impl
                canonical_o.delimiter_inverse = implementation
                if policy_o is not None:
                    policy_o.delimiter_inverse = implementation
                dst = work_root / f"{arm}-{round_index}"
                started = time.perf_counter()
                PRODUCT.extract(archive, dst)
                elapsed = time.perf_counter() - started
                if PRODUCT.treehash(dst) != source_tree:
                    raise RuntimeError(f"{arm} extraction identity failure")
                (control if arm == "control" else candidate).append(elapsed)
    finally:
        canonical_o.delimiter_inverse = original_canonical
        if policy_o is not None:
            policy_o.delimiter_inverse = original_policy

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
        "candidate_implementation": getattr(candidate_impl, "__name__", "shipping-delimiter-inverse"),
        "patched_reader_scope": "isolated-canonical-shared-and-policy-g04",
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
        "claim_boundary": "Exact-archive shipping-reader mechanism A/B only. Release credit still requires fresh authority-v2 and full correctness/platform evidence.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("property_cases_checked", "control_implementation", "candidate_implementation", "patched_reader_scope", "control_median_s", "candidate_median_s", "candidate_ratio", "speedup_fraction", "promotion_signal", "release_credit")}, indent=2))


if __name__ == "__main__":
    main()
