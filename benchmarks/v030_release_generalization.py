from __future__ import annotations

"""Authoritative compression/generalization gate for the integrated CMPCT v0.30 release candidate.

This harness reuses the exact repaired 15-workload source identities that accepted v0.29 used. For every
workload it builds the system release candidate (monotone G0-G4/v0.29 path plus locality-admitted PrefixGraph),
strong-verifies the selected complete artifact, and compares it to the exact accepted v0.29 bytes for that row.

Release-worthiness is intentionally stricter than a research oracle:
- 0 historical source-tree or accepted-v0.29 baseline drift rows;
- the selected product artifact independently strong-verifies to the candidate product's user-tree identity;
- 0 candidate byte regressions;
- at least 3 workloads strictly improved;
- at least 0.5% aggregate saving versus accepted v0.29, while retaining the inherited 687,783-byte absolute
  revision floor so a slightly smaller/repaired substrate cannot make a numeric revision easier to earn;
- every selected representation <=8x per-member decoded-context amplification.

The benchmark intentionally carries two tree identities. ``historical_tree_sha256`` is the frozen v0.28/v0.29
content-tree contract used by repair-v6 evidence (regular-file path + length + bytes). ``tree_sha256`` is the
current candidate product identity. Research candidates historically used the same content-only domain, while the
canonical r24/r25 product uses the richer user-tree semantic domain that also represents entry kind/link relations.
Those identities must never be compared as though they were interchangeable: the historical hash proves benchmark
substrate continuity; the product hash proves the selected archive represents the product's exact user-visible tree.

This is the compression/generalization tranche only. Passing it does not by itself authorize release:
controlled create/extract/selective-read/memory, recovery/fuzz, native/shared-reader parity, portability/export,
and external-competitor gates remain mandatory.

Footnote: accepted v0.29 changed only two rows versus v0.28 on this corpus. We reconstruct the exact row floor
from durable evidence: those two winners use their accepted v0.29 bytes and every other row retains its exact
v0.28 artifact byte count on the independently accepted repair-v6 source identity. The absolute revision hurdle
is an inherited policy input and is never recomputed downward after benchmark-substrate repair.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from experiments import entropygraph_v030_release_candidate as RC

EXPECTED_V029_TOTAL = 137_499_525
LEGACY_V028_REVISION_FLOOR_BASE = 137_550_416
INHERITED_ABSOLUTE_REVISION_FLOOR = 687_783
MIN_RELEASE_SAVING_BYTES = max(
    math.ceil(EXPECTED_V029_TOTAL * 0.005),
    math.ceil(LEGACY_V028_REVISION_FLOOR_BASE * 0.005),
    INHERITED_ABSOLUTE_REVISION_FLOOR,
)
MIN_IMPROVED_ROWS = 3
MAX_MEMBER_READ_AMP = 8.0

_V029_WINNERS = {
    ("resemblance_hostile_v1", "01_shifted_versions"): 1_723_056,
    ("resemblance_hostile_v1", "03_boundary_churn"): 79_876,
}


def _historical_treehash(root: Path) -> str:
    """Return the frozen benchmark content-tree identity used by v0.28/v0.29 and repair-v6.

    Do not delegate this to ``RC.treehash``. The canonical v0.30 adapter deliberately replaces ``RC`` with the
    release product, whose r24/r25 semantic tree includes entry-kind/link relations. Historical benchmark evidence
    instead authenticates regular-file relative path, length and bytes. Keeping the implementation here makes the
    evidence boundary explicit and prevents a future product-hash evolution from being misdiagnosed as corpus drift.
    """
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(rel).to_bytes(4, "little"))
        digest.update(rel)
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()


def _accepted_v029_rows() -> dict[tuple[str, str], dict]:
    preserved = V029._preserved_rows()
    rows: dict[tuple[str, str], dict] = {}
    for key, inherited in preserved.items():
        row = dict(inherited)
        row["accepted_v029_bytes"] = int(_V029_WINNERS.get(key, int(inherited["candidate_bytes"])))
        rows[key] = row
    total = sum(row["accepted_v029_bytes"] for row in rows.values())
    if len(rows) != 15 or total != EXPECTED_V029_TOTAL:
        raise RuntimeError(f"accepted v0.29 row reconstruction drift: rows={len(rows)} total={total}")
    return rows


def _embedded_v029_create_s(stats: dict) -> float | None:
    """Recover the already-paid accepted-v0.29 timing from the G0-G4 builder without rebuilding it."""
    g04 = stats.get("g04") or {}
    v029 = g04.get("v029") or {}
    for key in ("portfolio_create_s", "create_s", "build_wall_s"):
        value = v029.get(key)
        if isinstance(value, (int, float)) and float(value) > 0:
            return float(value)
    return None


def _measure_workload(suite: str, path: Path, archive_dir: Path, accepted: dict[tuple[str, str], dict]) -> dict:
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / f"{path.name}.cmpct"
    expected = accepted[(suite, path.name)]

    historical_tree = _historical_treehash(path)
    baseline_tree_match = historical_tree == expected["tree_sha256"]
    if not baseline_tree_match:
        raise RuntimeError(
            f"v0.30 historical source-tree drift: {suite}/{path.name}: "
            f"{historical_tree} != {expected['tree_sha256']}"
        )

    # Candidate/product identity is a separate domain from frozen benchmark provenance. In research mode this may
    # happen to equal ``historical_tree``; canonical r24/r25 intentionally uses the richer user-tree semantic hash.
    product_tree = RC.treehash(path)

    started = time.perf_counter()
    stats = RC.build(path, archive)
    wall = time.perf_counter() - started
    verified = RC.strong_verify(archive)
    product_tree_match = bool(verified.get("ok")) and verified.get("tree_sha256") == product_tree
    if not product_tree_match:
        raise RuntimeError(
            f"v0.30 selected artifact failed product-tree strong verification: {suite}/{path.name}: "
            f"verified={verified.get('tree_sha256')!r} expected={product_tree!r}"
        )

    expected_v029 = int(expected["accepted_v029_bytes"])
    measured_v029 = int(stats["v029_bytes"])
    baseline_match = measured_v029 == expected_v029
    if not baseline_match:
        raise RuntimeError(
            f"accepted v0.29 byte drift: {suite}/{path.name}: measured={measured_v029} expected={expected_v029}"
        )

    candidate = int(stats["archive_bytes"])
    amp = float(stats.get("max_selected_member_read_amplification", 0.0))
    if amp > MAX_MEMBER_READ_AMP:
        raise RuntimeError(f"selected v0.30 locality exceeds {MAX_MEMBER_READ_AMP}x: {suite}/{path.name}: {amp}")
    embedded_v029_create = _embedded_v029_create_s(stats)

    return {
        "suite": suite,
        "name": path.name,
        "baseline_identity": expected["baseline_identity"],
        "tree_sha256": product_tree,
        "historical_tree_sha256": historical_tree,
        "preserved_tree_sha256": expected["tree_sha256"],
        "baseline_tree_match": baseline_tree_match,
        "product_tree_match": product_tree_match,
        "accepted_v029_bytes": expected_v029,
        "measured_v029_bytes": measured_v029,
        "baseline_v029_bytes_match": baseline_match,
        "candidate_bytes": candidate,
        "saving_vs_v029_bytes": expected_v029 - candidate,
        "saving_vs_v029_pct": (expected_v029 - candidate) / max(1, expected_v029) * 100.0,
        "selected": stats["selected"],
        "g04_bytes": int(stats["g04_bytes"]),
        "g04_selected": stats["g04_selected"],
        "prefixgraph_contract_eligible": bool(stats["prefixgraph_contract_eligible"]),
        "prefixgraph_admitted": bool(stats["prefixgraph_admitted"]),
        "prefixgraph_reject_reason": stats["prefixgraph_reject_reason"],
        "prefixgraph_bytes": stats["prefixgraph_bytes"],
        "saving_vs_g04_bytes": int(stats["saving_vs_g04_bytes"]),
        "max_dependency_depth": int(stats["max_dependency_depth"]),
        "max_selected_member_read_amplification": amp,
        "selection_materialization": stats["selection_materialization"],
        "selection_extra_payload_write_bytes": int(stats["selection_extra_payload_write_bytes"]),
        "release_candidate_create_s": float(stats["portfolio_create_s"]),
        "embedded_v029_create_s": embedded_v029_create,
        "create_ratio_vs_embedded_v029": (
            float(stats["portfolio_create_s"]) / embedded_v029_create if embedded_v029_create else None
        ),
        "benchmark_wall_s": wall,
        "strong_verify": verified,
        "g04_hierarchical_records": int((stats.get("g04") or {}).get("hierarchical_total_records", 0)),
        "g04_hierarchical_incremental_saving_bytes": int(
            (stats.get("g04") or {}).get("hierarchical_incremental_saving_bytes", 0)
        ),
        "prefixgraph_locality": stats.get("prefixgraph_locality"),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = _accepted_v029_rows()

    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_release_neutral")
    hostile = V029._load(V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_release_hostile")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_v030_release_repair_v6")
    repair.install_generation_hooks(neutral)

    rows: list[dict] = []
    for label, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            row = _measure_workload(label, workload, work_root / "archives" / label, accepted)
            rows.append(row)
            print(
                json.dumps(
                    {
                        "suite": label,
                        "name": workload.name,
                        "v029": row["accepted_v029_bytes"],
                        "candidate": row["candidate_bytes"],
                        "saving": row["saving_vs_v029_bytes"],
                        "selected": row["selected"],
                        "g04_selected": row["g04_selected"],
                        "pg_admitted": row["prefixgraph_admitted"],
                        "pg_reject": row["prefixgraph_reject_reason"],
                        "max_amp": row["max_selected_member_read_amplification"],
                        "create_ratio": row["create_ratio_vs_embedded_v029"],
                    }
                ),
                flush=True,
            )

    if len(rows) != 15:
        raise RuntimeError(f"v0.30 generalization expected 15 workloads, got {len(rows)}")
    v029_total = sum(row["accepted_v029_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    saving = v029_total - candidate_total
    create_ratios = [
        row["create_ratio_vs_embedded_v029"]
        for row in rows
        if row["create_ratio_vs_embedded_v029"] is not None
    ]
    release_create = sum(row["release_candidate_create_s"] for row in rows)
    embedded_create = sum(row["embedded_v029_create_s"] or 0.0 for row in rows)
    totals = {
        "workloads": len(rows),
        "accepted_v029_bytes": v029_total,
        "candidate_bytes": candidate_total,
        "saving_vs_v029_bytes": saving,
        "saving_vs_v029_pct": saving / v029_total * 100.0,
        "workloads_improved": sum(row["candidate_bytes"] < row["accepted_v029_bytes"] for row in rows),
        "workloads_regressed": sum(row["candidate_bytes"] > row["accepted_v029_bytes"] for row in rows),
        "baseline_tree_drift_rows": sum(not row["baseline_tree_match"] for row in rows),
        "product_tree_drift_rows": sum(not row["product_tree_match"] for row in rows),
        "baseline_v029_byte_drift_rows": sum(not row["baseline_v029_bytes_match"] for row in rows),
        "v029_fallback_rows": sum(row["selected"] == "v029-fallback" for row in rows),
        "g04_overlay_rows": sum(row["selected"] == "g04-overlay" for row in rows),
        "prefixgraph_rows": sum(row["selected"] == "prefixgraph" for row in rows),
        "prefixgraph_contract_eligible_rows": sum(row["prefixgraph_contract_eligible"] for row in rows),
        "prefixgraph_admitted_rows": sum(row["prefixgraph_admitted"] for row in rows),
        "prefixgraph_locality_rejected_rows": sum(
            row["prefixgraph_reject_reason"] == "locality-ceiling" for row in rows
        ),
        "hierarchical_selected_records": sum(row["g04_hierarchical_records"] for row in rows),
        "hierarchical_incremental_saving_bytes": sum(
            row["g04_hierarchical_incremental_saving_bytes"] for row in rows
        ),
        "max_selected_member_read_amplification": max(
            (row["max_selected_member_read_amplification"] for row in rows), default=0.0
        ),
        "release_candidate_create_s": release_create,
        "embedded_v029_create_s": embedded_create,
        "creation_ratio_vs_embedded_v029": release_create / embedded_create if embedded_create > 0 else None,
        "median_workload_creation_ratio_vs_v029": statistics.median(create_ratios) if create_ratios else None,
    }
    if v029_total != EXPECTED_V029_TOTAL:
        raise RuntimeError(f"accepted v0.29 aggregate drift: {v029_total} != {EXPECTED_V029_TOTAL}")

    gate = {
        "exact_workload_count": len(rows) == 15,
        "exact_v029_aggregate": v029_total == EXPECTED_V029_TOTAL,
        "no_tree_drift": totals["baseline_tree_drift_rows"] == 0,
        "product_tree_verified": totals["product_tree_drift_rows"] == 0,
        "no_v029_byte_drift": totals["baseline_v029_byte_drift_rows"] == 0,
        "no_size_regressions": totals["workloads_regressed"] == 0,
        "minimum_improved_rows": totals["workloads_improved"] >= MIN_IMPROVED_ROWS,
        "revision_sized_aggregate_saving": saving >= MIN_RELEASE_SAVING_BYTES,
        "locality": totals["max_selected_member_read_amplification"] <= MAX_MEMBER_READ_AMP,
        "zero_copy_publication": all(
            row["selection_materialization"] == "same-filesystem-atomic-move"
            and row["selection_extra_payload_write_bytes"] == 0
            for row in rows
        ),
    }
    gate["passed"] = all(gate.values())

    return {
        "schema": "cmpct-v030-release-generalization-v1",
        "claim_boundary": (
            "integrated v0.30 compression/generalization gate on the exact repaired 15-workload v0.29 frontier; "
            "historical benchmark identity and canonical product identity are independently authenticated; "
            "not final release authority until timing/memory/native/recovery/portability/competitor gates pass"
        ),
        "engine": "experiments/entropygraph_v030_release_candidate.py",
        "contract": {
            "expected_v029_aggregate_bytes": EXPECTED_V029_TOTAL,
            "minimum_release_saving_bytes": MIN_RELEASE_SAVING_BYTES,
            "minimum_release_saving_pct": 0.5,
            "inherited_absolute_revision_floor_bytes": INHERITED_ABSOLUTE_REVISION_FLOOR,
            "minimum_improved_rows": MIN_IMPROVED_ROWS,
            "maximum_member_read_amplification": MAX_MEMBER_READ_AMP,
            "regression_tolerance_bytes": 0,
            "historical_tree_identity": "regular-file relative path + length + bytes; exact v0.28/v0.29 and repair-v6 evidence domain",
            "product_tree_identity": "candidate-owned user-tree semantic identity; canonical r24/r25 includes entry kind/link relations",
            "baseline": "accepted v0.29 exact row artifacts on 10 historical + 5 independently accepted repair-v6 identities",
            "non_additivity": "complete artifacts compete; independent Geometry/PrefixGraph savings are never summed",
        },
        "rows": rows,
        "totals": totals,
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 integrated compression/generalization gate failed")


if __name__ == "__main__":
    main()
