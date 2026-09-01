from __future__ import annotations

"""Exact diagnostic for the two dominant canonical v0.29 no-regression losses.

This instrument does not grant release credit and does not alter admission. It decomposes the complete-product
byte gap for Office and Analytics into accepted-v0.29, genuine canonical-r24, exact staged r25 control, direct
r25 candidate, and promoted release-product outcomes. The purpose is to identify which physical layer owns the
multi-megabyte regression before any codec or framing change is attempted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from benchmarks import neutral_hostile_corpus_v1 as N
from experiments import entropygraph_v030_canonical_final_impl as C
from experiments import entropygraph_v030_geometry_overlay_g04 as HIST_G04
from experiments import entropygraph_v030_release_product as PRODUCT


WORKLOADS = (
    ("02_office_workspace", N.corpus_office),
    ("04_analytics_and_database", N.corpus_analytics),
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _candidate_stats(source: Path, work: Path) -> dict:
    accepted = work / "accepted-v029.cmpct"
    HIST_G04.BASE.build(source, accepted)
    accepted_bytes = accepted.stat().st_size

    staged = work / "r25-staged"
    prepared = C._prepare_profile_tree(source, staged)

    r24 = work / "canonical-r24.cmpct"
    r24_stats = dict(C._r24_build(source, r24))

    r25 = work / "direct-r25-candidate.cmpct"
    r25_stats = dict(C._r25_build(staged, r25))
    r25_revision, r25_profile = C._profile_for_archive(r25)
    r25_bytes = r25.stat().st_size

    product = work / "promoted-product.cmpct"
    product_stats = dict(PRODUCT.build(source, product))
    product_revision, product_profile = PRODUCT._revision_for_archive(product)
    verified = dict(PRODUCT.strong_verify(product))
    if not verified.get("ok"):
        raise RuntimeError(f"promoted product failed strong verification: {verified!r}")

    nested = r25_stats
    return {
        "accepted_v029_bytes": accepted_bytes,
        "accepted_v029_sha256": _sha256(accepted),
        "genuine_r24_bytes": r24.stat().st_size,
        "genuine_r24_minus_v029_bytes": r24.stat().st_size - accepted_bytes,
        "genuine_r24_sha256": _sha256(r24),
        "filesystem_v1_manifest_bytes": int(prepared["manifest_bytes"]),
        "selected_manifest_encoding": prepared["selected_manifest_encoding"],
        "selected_manifest_bytes": int(prepared["selected_manifest_bytes"]),
        "manifest_control_saving_bytes": int(prepared["manifest_control_saving_bytes"]),
        "manifest_entries": int(prepared["entries"]),
        "regular_graph_members": int(prepared["regular_graph_members"]),
        "direct_r25_bytes": r25_bytes,
        "direct_r25_minus_v029_bytes": r25_bytes - accepted_bytes,
        "direct_r25_minus_r24_bytes": r25_bytes - r24.stat().st_size,
        "direct_r25_revision": r25_revision,
        "direct_r25_profile": r25_profile,
        "direct_r25_sha256": _sha256(r25),
        "direct_r25_reported_v029_floor_bytes": nested.get("v029_bytes"),
        "direct_r25_g04_bytes": nested.get("g04_bytes"),
        "direct_r25_prefixgraph_bytes": nested.get("prefixgraph_bytes"),
        "direct_r25_selected": nested.get("selected"),
        "direct_r25_g04_selected": nested.get("g04_selected"),
        "direct_r25_prefixgraph_admitted": nested.get("prefixgraph_admitted"),
        "direct_r25_prefixgraph_reject_reason": nested.get("prefixgraph_reject_reason"),
        "promoted_product_bytes": product.stat().st_size,
        "promoted_product_minus_v029_bytes": product.stat().st_size - accepted_bytes,
        "promoted_product_revision": product_revision,
        "promoted_product_profile": product_profile,
        "promoted_product_selected": product_stats.get("selected"),
        "promoted_product_r24_bytes": product_stats.get("r24_product_bytes"),
        "promoted_product_r25_bytes": product_stats.get("r25_product_bytes"),
        "promoted_product_v029_research_floor_bytes": product_stats.get("v029_research_floor_bytes"),
        "promoted_product_sha256": _sha256(product),
        "strong_verify": verified,
        "r24_create_s": float(r24_stats.get("create_s", 0.0)),
        "r25_create_s": float(r25_stats.get("create_s", 0.0)),
        "promoted_portfolio_create_s": float(product_stats.get("portfolio_create_s", 0.0)),
    }


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, builder in WORKLOADS:
        corpus_root = work_root / f"corpus-{name}"
        corpus_root.mkdir(parents=True, exist_ok=True)
        builder(corpus_root)
        source = corpus_root / name
        if not source.is_dir():
            raise RuntimeError(f"workload builder did not create expected source tree: {source}")
        with tempfile.TemporaryDirectory(prefix=f"gap-{name}-", dir=work_root) as td:
            measured = _candidate_stats(source, Path(td))
        row = {"workload": name, **measured}
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    return {
        "schema": "cmpct-v030-canonical-product-gap-v1",
        "claim_boundary": (
            "diagnostic-only exact byte decomposition; no release credit, no changed admission, and no hidden "
            "preprocessing/search/verification cost"
        ),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/canonical-product-gap-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/canonical-product-gap.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
