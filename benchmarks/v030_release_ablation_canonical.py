from __future__ import annotations

"""Exact v0.30 evidence split into historical causality and canonical product parity.

Two questions must remain separate because they have different byte semantics:

* ``historical_causality`` reproduces the repaired 15-workload v0.29 research frontier exactly. v0.29,
  Geometry-only, PrefixGraph-only and the complete-artifact combined tournament all consume the same original
  historical content tree. This is the only section allowed to enforce the frozen 137,501,815-byte v0.29
  aggregate and the inherited >=687,783-byte revision floor.
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


def _historical_artifact(path: Path, expected_tree: str, *, selected: str, details: dict | None = None) -> dict:
    verified = RC.strong_verify(path)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"historical ablation artifact failed strict verification: {selected}: {verified!r}")
    return {
        "substrate_id": HISTORICAL_SUBSTRATE,
        "selected": selected,
        "archive_bytes": path.stat().st_size,
        "archive_sha256": _sha256_file(path),
        "tree_sha256": expected_tree,
        "tree_verified": True,
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
        prefixgraph_only = dict(prefixgraph_raw)
        prefixgraph_only["selected"] = "prefixgraph"
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
            "combined_gain_beyond_best_single_bytes": expected_combined - combined["archive_bytes"],
        },
    }


def _load_product_module():
    from experiments import entropygraph_v030_canonical as canonical

    required = ("build", "strong_verify", "list_members", "read_member", "build_ablation", "treehash")
    missing = [name for name in required if not callable(getattr(canonical, name, None))]
    if missing:
        raise ProductSurfaceUnavailable(
            "final canonical product surface has not been imported; missing: " + ", ".join(missing)
        )
    return canonical


def _r24_product_build(source: Path, out: Path) -> dict:
    stats = dict(Builder(source).build(out))
    with CMPCT(out) as reader:
        verified_files = reader.verify()
    return {
        "substrate_id": PRODUCT_SUBSTRATE,
        "selected": "canonical-r24",
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256_file(out),
        "verified_files": int(verified_files),
        "format_revision": 24,
        "format_profile": "canonical-r24",
        "build": stats,
    }


def _product_row(suite: str, source: Path, archive_root: Path, canonical) -> dict:
    row_root = archive_root / "product" / suite / source.name
    row_root.mkdir(parents=True, exist_ok=True)
    r24_path = row_root / "r24.cmpct"
    candidate_path = row_root / "v030-product.cmpct"

    r24 = _r24_product_build(source, r24_path)
    candidate_stats = dict(canonical.build(source, candidate_path))
    candidate_verify = dict(canonical.strong_verify(candidate_path))
    expected_user_tree = canonical.treehash(source)
    if not candidate_verify.get("ok"):
        raise RuntimeError(f"canonical product verification failed: {suite}/{source.name}: {candidate_verify!r}")
    if candidate_verify.get("tree_sha256") != expected_user_tree:
        raise RuntimeError(
            f"canonical product user-tree identity mismatch: {suite}/{source.name}: "
            f"{candidate_verify.get('tree_sha256')} != {expected_user_tree}"
        )

    candidate = {
        "substrate_id": PRODUCT_SUBSTRATE,
        "selected": str(candidate_stats.get("selected")),
        "archive_bytes": candidate_path.stat().st_size,
        "archive_sha256": _sha256_file(candidate_path),
        "tree_sha256": expected_user_tree,
        "tree_verified": True,
        "format_revision": candidate_stats.get("format_revision"),
        "format_profile": candidate_stats.get("format_profile"),
        "filesystem_manifest_sha256": candidate_stats.get("filesystem_manifest_sha256"),
        "build": candidate_stats,
        "verify": candidate_verify,
    }
    _require_same_substrate(r24, candidate)
    return {
        "suite": suite,
        "name": source.name,
        "substrate_id": PRODUCT_SUBSTRATE,
        "r24": r24,
        "v030": candidate,
        "saving_vs_r24_bytes": r24["archive_bytes"] - candidate["archive_bytes"],
        "regressed_vs_r24": candidate["archive_bytes"] > r24["archive_bytes"],
    }


def _historical_totals(rows: list[dict]) -> tuple[dict, dict]:
    totals = {}
    for variant in VARIANTS:
        archive_bytes = sum(int(row["variants"][variant]["archive_bytes"]) for row in rows)
        totals[variant] = {
            "archive_bytes": archive_bytes,
            "saving_vs_v029_bytes": GENERAL.EXPECTED_V029_TOTAL - archive_bytes,
            "improved_rows": sum(
                row["variants"][variant]["archive_bytes"] < row["variants"]["v029"]["archive_bytes"]
                for row in rows
            ),
            "regressed_rows": sum(
                row["variants"][variant]["archive_bytes"] > row["variants"]["v029"]["archive_bytes"]
                for row in rows
            ),
        }
    combined = totals["combined"]
    gate = {
        "exact_workload_count": len(rows) == 15,
        "exact_v029_aggregate": totals["v029"]["archive_bytes"] == GENERAL.EXPECTED_V029_TOTAL,
        "one_historical_substrate": all(row["substrate_id"] == HISTORICAL_SUBSTRATE for row in rows),
        "all_variant_trees_verified": all(
            row["variants"][variant]["tree_verified"] for row in rows for variant in VARIANTS
        ),
        "all_selected_artifacts_sha256_addressed": all(
            len(row["variants"][variant]["archive_sha256"]) == 64 for row in rows for variant in VARIANTS
        ),
        "geometry_only_monotone": totals["geometry_only"]["regressed_rows"] == 0,
        "prefixgraph_only_monotone": totals["prefixgraph_only"]["regressed_rows"] == 0,
        "combined_no_size_regressions": combined["regressed_rows"] == 0,
        "combined_minimum_improved_rows": combined["improved_rows"] >= GENERAL.MIN_IMPROVED_ROWS,
        "combined_revision_sized_saving": combined["saving_vs_v029_bytes"] >= GENERAL.MIN_RELEASE_SAVING_BYTES,
        "combined_is_exact_equivalent_artifact_tournament": all(
            row["variants"]["combined"]["archive_bytes"]
            == min(
                row["variants"]["geometry_only"]["archive_bytes"],
                row["variants"]["prefixgraph_only"]["archive_bytes"],
            )
            for row in rows
        ),
        "no_additive_savings_credit": all(
            row["causal_deltas"]["combined_gain_beyond_best_single_bytes"] == 0 for row in rows
        ),
    }
    gate["passed"] = all(gate.values())
    return totals, gate


def _product_totals(rows: list[dict]) -> tuple[dict, dict]:
    r24_bytes = sum(int(row["r24"]["archive_bytes"]) for row in rows)
    v030_bytes = sum(int(row["v030"]["archive_bytes"]) for row in rows)
    totals = {
        "workloads": len(rows),
        "r24_product_bytes": r24_bytes,
        "v030_product_bytes": v030_bytes,
        "saving_vs_r24_bytes": r24_bytes - v030_bytes,
        "improved_rows": sum(row["v030"]["archive_bytes"] < row["r24"]["archive_bytes"] for row in rows),
        "regressed_rows": sum(bool(row["regressed_vs_r24"]) for row in rows),
    }
    gate = {
        "exact_workload_count": len(rows) == 15,
        "one_product_substrate": all(row["substrate_id"] == PRODUCT_SUBSTRATE for row in rows),
        "all_candidate_trees_verified": all(row["v030"]["tree_verified"] for row in rows),
        "all_product_artifacts_sha256_addressed": all(
            len(row[side]["archive_sha256"]) == 64 for row in rows for side in ("r24", "v030")
        ),
        "zero_product_byte_regressions": totals["regressed_rows"] == 0,
        "aggregate_product_no_regression": v030_bytes <= r24_bytes,
    }
    gate["passed"] = all(gate.values())
    return totals, gate


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpora = list(_build_corpora(work_root))
    if len(corpora) != 15:
        raise RuntimeError(f"v0.30 evidence expected 15 workloads, got {len(corpora)}")

    historical_rows = [
        _historical_row(suite, source, expected, work_root / "archives")
        for suite, source, expected in corpora
    ]
    historical_totals, historical_gate = _historical_totals(historical_rows)

    canonical = _load_product_module()
    product_rows = [
        _product_row(suite, source, work_root / "archives", canonical)
        for suite, source, _expected in corpora
    ]
    product_totals, product_gate = _product_totals(product_rows)

    gate = {
        "historical_causality_passed": historical_gate["passed"],
        "canonical_product_parity_passed": product_gate["passed"],
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-canonical-ablation-v2",
        "contract": {
            "historical_substrate": HISTORICAL_SUBSTRATE,
            "product_substrate": PRODUCT_SUBSTRATE,
            "historical_variants": list(VARIANTS),
            "expected_v029_historical_aggregate_bytes": GENERAL.EXPECTED_V029_TOTAL,
            "minimum_historical_release_saving_bytes": GENERAL.MIN_RELEASE_SAVING_BYTES,
            "minimum_historical_improved_rows": GENERAL.MIN_IMPROVED_ROWS,
            "historical_regression_tolerance_bytes": 0,
            "maximum_member_read_amplification": GENERAL.MAX_MEMBER_READ_AMP,
            "product_regression_tolerance_bytes": 0,
            "comparison_rule": "complete artifacts may be compared only when substrate_id is identical",
            "baseline_rule": (
                "137,501,815 B belongs only to the historical repaired content-tree substrate; canonical r24 "
                "product bytes are independently rebuilt and never substituted for that identity"
            ),
        },
        "historical_causality": {
            "rows": historical_rows,
            "totals": historical_totals,
            "gate": historical_gate,
        },
        "canonical_product_parity": {
            "rows": product_rows,
            "totals": product_totals,
            "gate": product_gate,
        },
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-ablation-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-ablation.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "historical_totals": result["historical_causality"]["totals"],
                "product_totals": result["canonical_product_parity"]["totals"],
                "gate": result["gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 historical-causality/product-parity gate failed")


if __name__ == "__main__":
    main()
