from __future__ import annotations

"""Exact diagnostic for the two dominant canonical v0.29 no-regression losses.

This instrument does not grant release credit and does not alter admission. It decomposes the complete-product
byte gap for Office and Analytics into accepted-v0.29, genuine canonical-r24, exact staged r25 control, direct
r25 candidate, and promoted release-product outcomes. It also prices one deliberately non-product counterfactual
with the filesystem-control member removed after otherwise identical staging. That gifted-control floor is only a
causal attribution instrument: it cannot reconstruct canonical filesystem semantics and therefore can never be
selected, promoted, or interpreted as release evidence.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
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

    # Causal byte-attribution oracle. Stage the same regular graph members through the exact canonical seam, then
    # gift away only the authenticated filesystem-control member before building the graph. The resulting archive
    # is intentionally non-canonical because it cannot reconstruct mode/time/link/xattr semantics. Its only job is
    # to answer whether the remaining v0.29 byte miss is physically owned by filesystem control or by some deeper
    # content-graph/staging effect. Representation bytes are *not* being hidden from a product claim: there is no
    # product claim for this counterfactual at all.
    control_free_staged = work / "r25-control-free-staged"
    control_free_prepared = C._prepare_profile_tree(source, control_free_staged)
    control_path = control_free_staged.joinpath(*PurePosixPath(C.FS.FILESYSTEM_MANIFEST).parts)
    if control_path.read_bytes() != control_free_prepared["selected_manifest_raw"]:
        raise RuntimeError("counterfactual control member differs from canonical selected control")
    control_path.unlink()
    control_free = work / "r25-control-free-counterfactual.cmpct"
    control_free_stats = dict(C._r25_build(control_free_staged, control_free))
    control_free_bytes = control_free.stat().st_size
    effective_control_cost = r25_bytes - control_free_bytes
    strict_control_budget = accepted_bytes - control_free_bytes - 1

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
        "control_free_counterfactual_bytes": control_free_bytes,
        "control_free_minus_v029_bytes": control_free_bytes - accepted_bytes,
        "control_free_selected": control_free_stats.get("selected"),
        "control_free_g04_bytes": control_free_stats.get("g04_bytes"),
        "control_free_prefixgraph_bytes": control_free_stats.get("prefixgraph_bytes"),
        "effective_control_member_cost_bytes": effective_control_cost,
        "effective_control_minus_raw_selected_bytes": effective_control_cost - int(prepared["selected_manifest_bytes"]),
        "strict_control_budget_bytes": strict_control_budget,
        "control_cost_over_strict_budget_bytes": effective_control_cost - strict_control_budget,
        "control_free_claim_boundary": (
            "causal attribution only: filesystem control is gifted away, exact filesystem reconstruction is lost, "
            "and these bytes are never product/release evidence"
        ),
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
        "control_free_create_s": float(control_free_stats.get("create_s", 0.0)),
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
