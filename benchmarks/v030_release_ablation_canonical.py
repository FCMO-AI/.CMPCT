from __future__ import annotations

"""Exact four-configuration ablation for the canonical CMPCT v0.30 candidate.

The release checklist requires a causal comparison of four *complete artifacts* on the same repaired
15-workload frontier:

1. accepted v0.29;
2. Geometry enabled, PrefixGraph disabled;
3. PrefixGraph enabled, Geometry disabled;
4. both v0.30 feature toggles enabled through the canonical release tournament.

No row is credited from detached payload estimates and no independent savings are added.  Every selected
artifact is strong-verified to the exact frozen source tree and SHA-256-addressed before its bytes enter the
ledger.  The current "combined" architecture is deliberately a complete-artifact tournament: it may select
either Geometry or PrefixGraph, but it does not claim that one archive simultaneously contains both mechanisms.
That distinction is recorded explicitly so a future compositional grammar cannot inherit this evidence by name.

Footnote: the PrefixGraph-only ablation retains the same accepted-v0.29 fallback semantics as a release feature.
Measuring raw PrefixGraph without its fallback would answer a different question (the research grammar's cost),
and could make a safe feature look regressive merely by disabling the immutable release floor.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v029_release as V029
from experiments import entropygraph_v030_canonical as CANON
from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_candidate as RC

VARIANTS = ("v029", "geometry_only", "prefixgraph_only", "combined")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _select_prefixgraph_candidate(v029_bytes: int, prefixgraph_bytes: int | None, admitted: bool) -> str:
    """Return the exact PrefixGraph-only tournament winner without approximate or additive scoring."""
    if admitted and prefixgraph_bytes is not None and prefixgraph_bytes < v029_bytes:
        return "prefixgraph"
    return "v029-fallback"


def _artifact(path: Path, expected_tree: str, *, selected: str, details: dict | None = None) -> dict:
    CANON.install_revision25_profiles()
    verified = CANON.strong_verify(path)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"ablation artifact failed canonical strong verification: {selected}: {verified!r}")
    revision, profile = CANON._revision_for_archive(path)
    return {
        "selected": selected,
        "archive_bytes": path.stat().st_size,
        "archive_sha256": _sha256_file(path),
        "format_revision": revision,
        "format_profile": profile,
        "tree_sha256": verified["tree_sha256"],
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


def _measure_row(suite: str, source: Path, expected: dict, archive_root: Path) -> dict:
    expected_tree = expected["tree_sha256"]
    live_tree = CANON.treehash(source)
    if live_tree != expected_tree:
        raise RuntimeError(f"ablation source-tree drift: {suite}/{source.name}: {live_tree} != {expected_tree}")

    row_root = archive_root / suite / source.name
    row_root.mkdir(parents=True, exist_ok=True)
    v029_path = row_root / "v029.cmpct"
    geometry_path = row_root / "geometry-only.cmpct"
    prefixgraph_path = row_root / "prefixgraph-raw.cmpct"
    combined_path = row_root / "combined.cmpct"

    v029_stats = V029.build(source, v029_path)
    expected_v029_bytes = int(expected["accepted_v029_bytes"])
    if v029_path.stat().st_size != expected_v029_bytes:
        raise RuntimeError(
            f"ablation accepted-v0.29 byte drift: {suite}/{source.name}: "
            f"{v029_path.stat().st_size} != {expected_v029_bytes}"
        )
    v029 = _artifact(v029_path, expected_tree, selected="v029", details={"build": v029_stats})

    CANON.install_revision25_profiles()
    geometry_stats = G04.build(source, geometry_path)
    geometry = _artifact(
        geometry_path,
        expected_tree,
        selected="geometry" if geometry_stats.get("selected") == "geometry-overlay-g04" else "v029-fallback",
        details={
            "builder_selected": geometry_stats.get("selected"),
            "saving_vs_v029_bytes": int(geometry_stats.get("saving_vs_v029_bytes", 0)),
            "max_selected_member_read_amplification": float(
                geometry_stats.get("max_selected_member_read_amplification", 0.0)
            ),
        },
    )
    if geometry["archive_bytes"] > v029["archive_bytes"]:
        raise RuntimeError("Geometry-only ablation violated immutable v0.29 size floor")

    pg_contract_eligible, pg_reject_reason = RC._prefixgraph_eligibility(source, expected_tree)
    pg_stats = None
    pg_locality = None
    pg_admitted = False
    prefixgraph_raw = None
    if pg_contract_eligible:
        CANON.install_revision25_profiles()
        pg_stats = PG.build(source, prefixgraph_path)
        prefixgraph_raw = _artifact(
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
        # Footnote: this is an evidence alias to the already-hashed exact v0.29 artifact, not an invented byte
        # count.  Keeping the same digest makes the fallback identity auditable without writing a duplicate file.
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

    CANON.install_revision25_profiles()
    combined_stats = CANON.build(source, combined_path)
    combined = _artifact(
        combined_path,
        expected_tree,
        selected=str(combined_stats.get("selected")),
        details={
            "builder_selected": combined_stats.get("selected"),
            "max_selected_member_read_amplification": float(
                combined_stats.get("max_selected_member_read_amplification", 0.0)
            ),
            "prefixgraph_admitted": bool(combined_stats.get("prefixgraph_admitted", False)),
        },
    )

    expected_combined = min(geometry["archive_bytes"], prefixgraph_only["archive_bytes"])
    if combined["archive_bytes"] != expected_combined:
        raise RuntimeError(
            f"combined tournament is not the exact minimum enabled complete artifact: "
            f"{suite}/{source.name}: combined={combined['archive_bytes']} expected={expected_combined}"
        )
    if combined["archive_bytes"] > v029["archive_bytes"]:
        raise RuntimeError("combined ablation violated immutable v0.29 size floor")

    variants = {
        "v029": v029,
        "geometry_only": geometry,
        "prefixgraph_only": prefixgraph_only,
        "combined": combined,
    }
    return {
        "suite": suite,
        "name": source.name,
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


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows = [
        _measure_row(suite, source, expected, work_root / "archives")
        for suite, source, expected in _build_corpora(work_root)
    ]
    if len(rows) != 15:
        raise RuntimeError(f"v0.30 canonical ablation expected 15 workloads, got {len(rows)}")

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
        "combined_is_exact_complete_artifact_tournament": all(
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
    return {
        "schema": "cmpct-v030-canonical-ablation-v1",
        "engine": "experiments/entropygraph_v030_canonical.py",
        "release_facade": "cmpct-v030-r25-v1",
        "contract": {
            "variants": list(VARIANTS),
            "expected_v029_aggregate_bytes": GENERAL.EXPECTED_V029_TOTAL,
            "minimum_release_saving_bytes": GENERAL.MIN_RELEASE_SAVING_BYTES,
            "minimum_improved_rows": GENERAL.MIN_IMPROVED_ROWS,
            "regression_tolerance_bytes": 0,
            "maximum_member_read_amplification": GENERAL.MAX_MEMBER_READ_AMP,
            "combined_semantics": (
                "both feature toggles enabled in one complete-artifact tournament; current architecture selects "
                "the exact smaller admitted Geometry-only or PrefixGraph-only artifact and never sums savings"
            ),
            "prefixgraph_only_semantics": (
                "PrefixGraph candidate plus exact accepted-v0.29 fallback; raw PrefixGraph bytes are retained as "
                "diagnostic evidence even when the release-safe feature toggle falls back"
            ),
        },
        "rows": rows,
        "totals": totals,
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
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 four-configuration ablation gate failed")


if __name__ == "__main__":
    main()
