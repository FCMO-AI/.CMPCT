from __future__ import annotations

"""Exact v0.30 evidence split into historical causality and canonical product parity.

Two questions must remain separate because they have different byte semantics:

* ``historical_causality`` reproduces the repaired 15-workload v0.29 research frontier exactly. v0.29,
  Geometry-only, PrefixGraph-only and the complete-artifact combined tournament all consume the same original
  historical content tree. This is the only section allowed to enforce the frozen accepted-v0.29 aggregate and
  the inherited >=687,783-byte revision floor.
* ``canonical_product_parity`` compares a genuine released r24 product archive with the final canonical v0.30
  product archive on the same original filesystem tree. Revision-25 filesystem-manifest bytes are paid here,
  and genuine r24 fallback is allowed. This section is an additional no-regression/product-worthiness gate; it
  never rewrites the historical v0.29 baseline.

A byte comparison is valid only between complete artifacts carrying the same ``substrate_id``. Cross-substrate
``min``/saving arithmetic is rejected before it can enter a ledger.

Footnote: productization is allowed to cost bytes. Evidence is not allowed to hide that cost by charging a
filesystem manifest to only one side or by retroactively pretending the accepted research archive was r24.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v029_release as V029
from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_candidate as RC

HISTORICAL_SUBSTRATE = "historical-repaired-content-tree-v1"
PRODUCT_SUBSTRATE = "canonical-filesystem-product-v1"
VARIANTS = ("v029", "geometry_only", "prefixgraph_only", "combined")


class ProductSurfaceUnavailable(RuntimeError):
    """Final T03 canonical product API has not yet been imported into the reconciled candidate."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_same_substrate(*artifacts: dict) -> str:
    ids = {artifact.get("substrate_id") for artifact in artifacts}
    if None in ids or len(ids) != 1:
        raise RuntimeError(f"incomparable complete-artifact substrates: {sorted(str(x) for x in ids)}")
    return str(next(iter(ids)))


def _select_prefixgraph_candidate(v029_bytes: int, prefixgraph_bytes: int | None, admitted: bool) -> str:
    if admitted and prefixgraph_bytes is not None and prefixgraph_bytes < v029_bytes:
        return "prefixgraph"
    return "v029-fallback"


def _historical_artifact(
    path: Path,
    expected_tree: str,
    *,
    selected: str,
    details: dict | None = None,
    verifier=None,
) -> dict:
    """Authenticate one historical complete artifact in the grammar that actually owns those bytes.

    Historical causality deliberately includes a *raw* PrefixGraph arm before release admission.  That raw arm
    may reconstruct the exact tree yet later be rejected because selective-read context exceeds the <=8x product
    law.  Sending it through ``RC.strong_verify`` collapses those two questions: the release reader correctly
    rejects the raw artifact for locality, which makes the causal ledger unable to record the rejected candidate
    at all.  Use the representation's own authenticated logical verifier here, then apply release locality and
    selection policy explicitly below.  Product/combined artifacts continue to use the release verifier.

    Footnote: this is not a bypass. A raw PrefixGraph artifact verified here is never marked ``admitted`` by this
    helper and cannot become ``prefixgraph_only`` unless the separate release-locality check passes. The released
    combined tournament still uses ``RC.build`` / ``RC.strong_verify`` unchanged.
    """
    verify = RC.strong_verify if verifier is None else verifier
    verified = verify(path)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"historical ablation artifact failed logical verification: {selected}: {verified!r}")
    return {
        "substrate_id": HISTORICAL_SUBSTRATE,
        "selected": selected,
        "archive_bytes": path.stat().st_size,
        "archive_sha256": _sha256_file(path),
        "tree_sha256": expected_tree,
        "tree_verified": True,
        "verification_domain": "representation-logical" if verifier is not None else "release-candidate",
        "details": details or {},
    }


def _build_corpora(work_root: Path):
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_ablation_neutral",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_ablation_hostile",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_ablation_repair")
    repair.install_generation_hooks(neutral)
    roots = (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    )
    for suite, builder, root in roots:
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            yield suite, workload, accepted[(suite, workload.name)]


def _historical_row(suite: str, source: Path, expected: dict, archive_root: Path) -> dict:
    expected_tree = expected["tree_sha256"]
    live_tree = RC.treehash(source)
    if live_tree != expected_tree:
        raise RuntimeError(f"historical ablation source-tree drift: {suite}/{source.name}: {live_tree} != {expected_tree}")

    row_root = archive_root / "historical" / suite / source.name
    row_root.mkdir(parents=True, exist_ok=True)
    v029_path = row_root / "v029.cmpct"
    geometry_path = row_root / "geometry-only.cmpct"
    prefixgraph_path = row_root / "prefixgraph-raw.cmpct"
    combined_path = row_root / "combined.cmpct"

    v029_stats = V029.build(source, v029_path)
    expected_v029_bytes = int(expected["accepted_v029_bytes"])
    if v029_path.stat().st_size != expected_v029_bytes:
        raise RuntimeError(
            f"accepted-v0.29 byte drift: {suite}/{source.name}: {v029_path.stat().st_size} != {expected_v029_bytes}"
        )
    v029 = _historical_artifact(v029_path, expected_tree, selected="v029", details={"build": v029_stats})

    geometry_stats = G04.build(source, geometry_path)
    geometry = _historical_artifact(
        geometry_path,
        expected_tree,
        selected="geometry" if geometry_stats.get("selected") == "geometry-overlay-g04" else "v029-fallback",
        details={
            "builder_selected": geometry_stats.get("selected"),
            "saving_vs_v029_bytes": int(geometry_stats.get("saving_vs_v029_bytes", 0)),
            "max_selected_member_read_amplification": geometry_stats.get("max_selected_member_read_amplification"),
        },
    )
    _require_same_substrate(v029, geometry)
    if geometry["archive_bytes"] > v029["archive_bytes"]:
        raise RuntimeError("Geometry-only historical ablation violated immutable v0.29 size floor")

    pg_contract_eligible, pg_reject_reason = RC._prefixgraph_eligibility(source, expected_tree)
    pg_stats = None
    pg_locality = None
    pg_admitted = False
    prefixgraph_raw = None
    if pg_contract_eligible:
        pg_stats = PG.build(source, prefixgraph_path)
        prefixgraph_raw = _historical_artifact(
            prefixgraph_path,
            expected_tree,
            selected="prefixgraph-raw",
            verifier=PG.strong_verify,
            details={
                "prefix_records": int(pg_stats.get("prefix_records", 0)),
                "max_dependency_depth": int(pg_stats.get("max_dependency_depth", 0)),
            },
        )
        pg_locality = RC._prefixgraph_locality(prefixgraph_path)
        pg_admitted = bool(pg_locality["passed"])
        if not pg_admitted:
            pg_reject_reason = "locality-ceiling"

    prefix_selected = _select_prefixgraph_candidate(
        v029["archive_bytes"],
        prefixgraph_raw["archive_bytes"] if prefixgraph_raw is not None else None,
        pg_admitted,
    )
    if prefix_selected == "prefixgraph":
        assert prefixgraph_raw is not None
        # A PrefixGraph arm may enter the release-equivalent historical tournament only after explicit locality
        # admission. Re-run the strict release verifier at that boundary so the causal ledger cannot launder a
        # representation-only proof into release eligibility.
        strict_pg = RC.strong_verify(prefixgraph_path)
        if not strict_pg.get("ok") or strict_pg.get("tree_sha256") != expected_tree:
            raise RuntimeError(f"admitted PrefixGraph failed strict release verification: {strict_pg!r}")
        prefixgraph_only = dict(prefixgraph_raw)
        prefixgraph_only["selected"] = "prefixgraph"
        prefixgraph_only["verification_domain"] = "release-candidate"
    else:
        # Footnote: this fallback aliases the exact already-hashed v0.29 complete artifact. It does not invent a
        # smaller byte count or silently replace the historical substrate with canonical r24.
        prefixgraph_only = dict(v029)
        prefixgraph_only["selected"] = "v029-fallback"
    prefixgraph_only["details"] = {
        "contract_eligible": pg_contract_eligible,
        "admitted": pg_admitted,
        "reject_reason": pg_reject_reason,
        "raw_prefixgraph_bytes": prefixgraph_raw["archive_bytes"] if prefixgraph_raw is not None else None,
        "raw_prefixgraph_sha256": prefixgraph_raw["archive_sha256"] if prefixgraph_raw is not None else None,
        "raw_prefixgraph_tree_verified": bool(prefixgraph_raw and prefixgraph_raw.get("tree_verified")),
        "locality": pg_locality,
    }

    combined_stats = RC.build(source, combined_path)
    combined = _historical_artifact(
        combined_path,
        expected_tree,
        selected=str(combined_stats.get("selected")),
        details={
            "builder_selected": combined_stats.get("selected"),
            "max_selected_member_read_amplification": combined_stats.get("max_selected_member_read_amplification"),
            "prefixgraph_admitted": bool(combined_stats.get("prefixgraph_admitted", False)),
        },
    )

    _require_same_substrate(v029, geometry, prefixgraph_only, combined)
    expected_combined = min(geometry["archive_bytes"], prefixgraph_only["archive_bytes"])
    if combined["archive_bytes"] != expected_combined:
        raise RuntimeError(
            f"historical combined tournament is not the exact minimum equivalent complete artifact: "
            f"{suite}/{source.name}: combined={combined['archive_bytes']} expected={expected_combined}"
        )

    variants = {
        "v029": v029,
        "geometry_only": geometry,
        "prefixgraph_only": prefixgraph_only,
        "combined": combined,
    }
    return {
        "suite": suite,
        "name": source.name,
        "substrate_id": HISTORICAL_SUBSTRATE,
        "baseline_identity": expected["baseline_identity"],
        "tree_sha256": expected_tree,
        "variants": variants,
        "causal_deltas": {
            "geometry_only_saving_vs_v029_bytes": v029["archive_bytes"] - geometry["archive_bytes"],
            "prefixgraph_only_saving_vs_v029_bytes": v029["archive_bytes"] - prefixgraph_only["archive_bytes"],
            "combined_saving_vs_v029_bytes": v029["archive_bytes"] - combined["archive_bytes"],
        },
    }


def _load_product_surface():
    try:
        from experiments import entropygraph_v030_release_product as PRODUCT
    except ImportError as exc:  # pragma: no cover - release integration guard
        raise ProductSurfaceUnavailable("canonical v0.30 product surface unavailable") from exc
    required = ("build", "strong_verify", "treehash")
    if any(not callable(getattr(PRODUCT, name, None)) for name in required):
        raise ProductSurfaceUnavailable("canonical v0.30 product surface incomplete")
    return PRODUCT


def _product_row(suite: str, source: Path, archive_root: Path, PRODUCT) -> dict:
    row_root = archive_root / "product" / suite / source.name
    row_root.mkdir(parents=True, exist_ok=True)
    r24_path = row_root / "r24.cmpct"
    v030_path = row_root / "v030.cmpct"

    Builder(source).build(r24_path)
    with CMPCT(r24_path) as reader:
        r24_files = reader.verify()
    r24 = {
        "substrate_id": PRODUCT_SUBSTRATE,
        "selected": "canonical-r24",
        "archive_bytes": r24_path.stat().st_size,
        "archive_sha256": _sha256_file(r24_path),
        "tree_sha256": PRODUCT.treehash(source),
        "tree_verified": bool(r24_files >= 0),
    }

    stats = PRODUCT.build(source, v030_path)
    verified = PRODUCT.strong_verify(v030_path)
    expected_tree = PRODUCT.treehash(source)
    if not verified.get("ok"):
        raise RuntimeError(f"canonical product failed strong verification: {suite}/{source.name}: {verified!r}")
    if stats.get("format_revision") == 25 and verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"canonical r25 product tree mismatch: {suite}/{source.name}")
    v030 = {
        "substrate_id": PRODUCT_SUBSTRATE,
        "selected": str(stats.get("selected")),
        "archive_bytes": v030_path.stat().st_size,
        "archive_sha256": _sha256_file(v030_path),
        "tree_sha256": expected_tree,
        "tree_verified": True,
        "format_revision": stats.get("format_revision"),
        "format_profile": stats.get("format_profile"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "r25_strictly_smaller_than_r24": stats.get("r25_strictly_smaller_than_r24"),
    }
    _require_same_substrate(r24, v030)
    if v030["archive_bytes"] > r24["archive_bytes"]:
        raise RuntimeError(f"canonical v0.30 product regressed genuine r24 bytes: {suite}/{source.name}")
    if v030["archive_bytes"] == r24["archive_bytes"] and stats.get("format_revision") != 24:
        raise RuntimeError(f"canonical exact tie did not conservatively retain r24: {suite}/{source.name}")
    return {
        "suite": suite,
        "name": source.name,
        "substrate_id": PRODUCT_SUBSTRATE,
        "tree_sha256": expected_tree,
        "r24": r24,
        "v030": v030,
        "saving_vs_r24_bytes": r24["archive_bytes"] - v030["archive_bytes"],
    }


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    historical_rows = [
        _historical_row(suite, source, expected, work_root / "archives")
        for suite, source, expected in _build_corpora(work_root / "corpus")
    ]
    PRODUCT = _load_product_surface()
    product_rows = [
        _product_row(suite, source, work_root / "archives", PRODUCT)
        for suite, source, _expected in _build_corpora(work_root / "product-corpus")
    ]

    accepted_v029 = sum(row["variants"]["v029"]["archive_bytes"] for row in historical_rows)
    combined = sum(row["variants"]["combined"]["archive_bytes"] for row in historical_rows)
    improved = sum(
        row["variants"]["combined"]["archive_bytes"] < row["variants"]["v029"]["archive_bytes"]
        for row in historical_rows
    )
    regressed = sum(
        row["variants"]["combined"]["archive_bytes"] > row["variants"]["v029"]["archive_bytes"]
        for row in historical_rows
    )
    max_amp = max(
        float(row["variants"]["combined"]["details"].get("max_selected_member_read_amplification") or 0.0)
        for row in historical_rows
    )
    product_regressions = [
        f"{row['suite']}/{row['name']}" for row in product_rows if row["v030"]["archive_bytes"] > row["r24"]["archive_bytes"]
    ]
    return {
        "schema": "cmpct-v030-release-ablation-canonical-v3",
        "historical_causality": {
            "substrate_id": HISTORICAL_SUBSTRATE,
            "accepted_v029_bytes": accepted_v029,
            "combined_bytes": combined,
            "saving_vs_v029_bytes": accepted_v029 - combined,
            "workloads_improved": improved,
            "workloads_regressed": regressed,
            "max_selected_member_read_amplification": max_amp,
            "rows": historical_rows,
        },
        "canonical_product_parity": {
            "substrate_id": PRODUCT_SUBSTRATE,
            "product_regressions": product_regressions,
            "rows": product_rows,
        },
        "claim_boundary": (
            "historical causality and canonical product parity are independent ledgers; no byte arithmetic crosses substrates"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
