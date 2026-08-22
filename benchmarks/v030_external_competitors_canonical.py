from __future__ import annotations

"""Release-product binding for the exact-tree v0.30 external competitor frontier.

The public competitor corpus is regular-file-only and its frozen source fingerprint predates the richer r25
filesystem-manifest identity. CMPCT build/verify/extract therefore uses the promoted product API, while the
cross-format extracted-tree comparator intentionally remains the historical regular-file content fingerprint
used to freeze all 15 inputs.

v0.30 has a strict per-workload dominance contract for the two ubiquitous compression baselines: canonical
CMPCT must be strictly smaller and strictly faster to create than both deterministic ZIP/Deflate-9 and solid
tar+Zstd-19 on every one of the 15 frozen workloads. Aggregate wins, suite-level wins and exact ties cannot
compensate for a losing row on either dimension.

Footnote: comparing ZIP/7z/tar/ZPAQ with the r25 metadata hash would be false equivalence because those formats do
not all preserve the same metadata semantics. The size frontier is credited only after exact regular-file content
round-trip, while CMPCT's richer filesystem fidelity is separately covered by canonical product parity tests.
"""

import argparse
import json
from pathlib import Path
import time

from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_release as HISTORICAL_TREE

B.CMPCT = CANON
B._tree = lambda root: HISTORICAL_TREE.treehash(root)


def _candidate_profile(stats: dict) -> dict:
    """Retain internal time/byte ownership without changing the competitor measurement boundary.

    The release problem is now often a *canonicalization gap*: G0-G4 may possess a much smaller accepted-v0.29
    research floor but be unable to publish it as revision 25.  Preserve the exact competing byte counts so a red
    row tells us whether engineering should target r24, G0-G4 framing, PrefixGraph, or candidate scheduling.
    """
    r24 = stats.get("r24") if isinstance(stats.get("r24"), dict) else {}
    r25 = stats.get("r25") if isinstance(stats.get("r25"), dict) else {}
    g04 = r25.get("g04") if isinstance(r25.get("g04"), dict) else {}
    pg = r25.get("prefixgraph") if isinstance(r25.get("prefixgraph"), dict) else {}
    r24_bytes = stats.get("r24_product_bytes")
    r25_bytes = stats.get("r25_product_bytes")
    v029_bytes = g04.get("v029_bytes")
    overlay_bytes = g04.get("overlay_bytes")
    return {
        "product_portfolio_create_s": stats.get("portfolio_create_s"),
        "r24_product_bytes": r24_bytes,
        "r25_product_bytes": r25_bytes,
        "r24_create_s": r24.get("create_s"),
        "r24_verification_state": r24.get("verification_state"),
        "r24_prebuild_overlap": r24.get("r24_prebuild_overlap"),
        "r25_selected": r25.get("selected"),
        "r25_create_s": r25.get("create_s"),
        "r25_portfolio_create_s": r25.get("portfolio_create_s"),
        "r25_preselection_logical_verification": r25.get("preselection_logical_verification"),
        "g04_selected": g04.get("selected"),
        "g04_product_bytes": r25.get("g04_bytes"),
        "g04_v029_floor_bytes": v029_bytes,
        "g04_prefallback_graph_bytes": g04.get("pre_overlay_graph_bytes"),
        "g04_overlay_bytes": overlay_bytes,
        "g04_overlay_delta_vs_v029_bytes": (
            int(overlay_bytes) - int(v029_bytes)
            if isinstance(overlay_bytes, int) and isinstance(v029_bytes, int)
            else None
        ),
        "g04_overlay_delta_vs_r24_bytes": (
            int(overlay_bytes) - int(r24_bytes)
            if isinstance(overlay_bytes, int) and isinstance(r24_bytes, int)
            else None
        ),
        "g04_portfolio_create_s": g04.get("portfolio_create_s"),
        "g04_shared_candidate_build_s": g04.get("shared_candidate_build_s"),
        "g04_v028_child_s": g04.get("v028_child_s"),
        "g04_attempt5_child_s": g04.get("attempt5_child_s"),
        "g04_overlay_verification_state": g04.get("overlay_verification_state"),
        "prefixgraph_contract_eligible": r25.get("prefixgraph_contract_eligible"),
        "prefixgraph_admitted": r25.get("prefixgraph_admitted"),
        "prefixgraph_reject_reason": r25.get("prefixgraph_reject_reason"),
        "prefixgraph_bytes": r25.get("prefixgraph_bytes"),
        "prefixgraph_portfolio_create_s": pg.get("portfolio_create_s"),
    }


def _cmpct_with_stage_timings(stage: Path, archive: Path, extracted: Path) -> dict:
    """Mirror the frozen CMPCT competitor measurement and expose only nested diagnostics.

    The create timer starts immediately before and stops immediately after ``CANON.build`` exactly as the base
    harness does. Strong verification and extraction remain outside that timer. The extra fields merely preserve
    already-produced product stats so a red row identifies which internal stage owns latency and bytes.
    """
    started = time.perf_counter()
    stats = CANON.build(stage, archive)
    create_s = time.perf_counter() - started
    verified = CANON.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"CMPCT v0.30 competitor artifact failed strong verification: {verified!r}")
    started = time.perf_counter()
    CANON.extract(archive, extracted)
    extract_s = time.perf_counter() - started
    return {
        "available": True,
        "archive_bytes": archive.stat().st_size,
        "create_s": create_s,
        "extract_s": extract_s,
        "selected": stats.get("selected"),
        "max_member_read_amplification": stats.get("max_selected_member_read_amplification"),
        "candidate_profile": _candidate_profile(stats),
    }


# Diagnostic enrichment only: the exact same public product build/verify/extract calls and timer boundary remain
# authoritative. No comparator implementation, threshold, workload, ordering or archive bytes are changed.
B._cmpct = _cmpct_with_stage_timings


def _strict_row_dominance(result: dict) -> dict:
    """Require strict per-workload size and create-time wins over ZIP and solid Zstd-19."""
    rows = result["rows"]
    details = []
    all_zip_size = True
    all_zstd_size = True
    all_zip_create = True
    all_zstd_create = True
    for row in rows:
        formats = row["formats"]
        cmpct = formats["cmpct_v030"]
        zip_row = formats["zip_deflate9"]
        zstd_row = formats["tar_zstd19_solid"]
        available = cmpct.get("available") and zip_row.get("available") and zstd_row.get("available")
        if not available:
            zip_size_win = zstd_size_win = zip_create_win = zstd_create_win = False
        else:
            cmpct_bytes = int(cmpct["archive_bytes"])
            zip_bytes = int(zip_row["archive_bytes"])
            zstd_bytes = int(zstd_row["archive_bytes"])
            cmpct_create = float(cmpct["create_s"])
            zip_create = float(zip_row["create_s"])
            zstd_create = float(zstd_row["create_s"])
            zip_size_win = cmpct_bytes < zip_bytes
            zstd_size_win = cmpct_bytes < zstd_bytes
            zip_create_win = cmpct_create < zip_create
            zstd_create_win = cmpct_create < zstd_create
        all_zip_size = all_zip_size and zip_size_win
        all_zstd_size = all_zstd_size and zstd_size_win
        all_zip_create = all_zip_create and zip_create_win
        all_zstd_create = all_zstd_create and zstd_create_win
        details.append({
            "label": row["label"],
            "cmpct_bytes": cmpct.get("archive_bytes"),
            "zip_deflate9_bytes": zip_row.get("archive_bytes"),
            "tar_zstd19_solid_bytes": zstd_row.get("archive_bytes"),
            "cmpct_create_s": cmpct.get("create_s"),
            "zip_deflate9_create_s": zip_row.get("create_s"),
            "tar_zstd19_solid_create_s": zstd_row.get("create_s"),
            "strictly_beats_zip_size": zip_size_win,
            "strictly_beats_zstd19_size": zstd_size_win,
            "strictly_beats_zip_create": zip_create_win,
            "strictly_beats_zstd19_create": zstd_create_win,
        })
    strict_all = all_zip_size and all_zstd_size and all_zip_create and all_zstd_create
    return {
        "all_workloads_strictly_beat_zip_size": all_zip_size,
        "all_workloads_strictly_beat_zstd19_size": all_zstd_size,
        "all_workloads_strictly_beat_zip_create": all_zip_create,
        "all_workloads_strictly_beat_zstd19_create": all_zstd_create,
        "strict_no_ties_size_or_create": strict_all,
        "rows": details,
    }


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    strict = _strict_row_dominance(result)
    gate = dict(result["gate"])
    for key in (
        "all_workloads_strictly_beat_zip_size",
        "all_workloads_strictly_beat_zstd19_size",
        "all_workloads_strictly_beat_zip_create",
        "all_workloads_strictly_beat_zstd19_create",
        "strict_no_ties_size_or_create",
    ):
        gate[key] = strict[key]
    gate["passed"] = bool(gate.get("passed")) and all(gate[key] for key in (
        "all_workloads_strictly_beat_zip_size",
        "all_workloads_strictly_beat_zstd19_size",
        "all_workloads_strictly_beat_zip_create",
        "all_workloads_strictly_beat_zstd19_create",
        "strict_no_ties_size_or_create",
    ))
    result["gate"] = gate
    result["strict_per_workload_dominance"] = strict
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["source_tree_identity"] = "historical-regular-file-content-v0.29-frozen"
    result["product_fidelity_evidence"] = "canonical product parity / native portability lanes"
    result["timing_diagnostics"] = (
        "CMPCT rows retain product-internal candidate time/byte ownership; comparator create_s remains the unchanged "
        "full public CANON.build wall-clock and strict ZIP/Zstd gates use only that outer measurement."
    )
    result["strict_competitor_contract"] = (
        "For every frozen workload: CMPCT archive_bytes < ZIP/Deflate-9 archive_bytes AND CMPCT archive_bytes < "
        "solid tar+Zstd-19 archive_bytes AND CMPCT create_s < ZIP/Deflate-9 create_s AND CMPCT create_s < solid "
        "tar+Zstd-19 create_s. Equality on any comparison is failure."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-external-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-external.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"aggregates": result["aggregates"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 external competitor gate failed")


if __name__ == "__main__":
    main()
