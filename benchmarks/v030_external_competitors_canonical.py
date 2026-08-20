from __future__ import annotations

"""Release-product binding for the exact-tree v0.30 external competitor frontier.

The public competitor corpus is regular-file-only and its frozen source fingerprint predates the richer r25
filesystem-manifest identity. CMPCT build/verify/extract therefore uses the promoted product API, while the
cross-format extracted-tree comparator intentionally remains the historical regular-file content fingerprint
used to freeze all 15 inputs.

v0.30 has a strict per-workload dominance contract for the two ubiquitous compression baselines: canonical
CMPCT must be strictly smaller than both deterministic ZIP/Deflate-9 and solid tar+Zstd-19 on every one of the
15 frozen workloads. Aggregate wins, suite-level wins and exact ties cannot compensate for a losing row.

Footnote: comparing ZIP/7z/tar/ZPAQ with the r25 metadata hash would be false equivalence because those formats do
not all preserve the same metadata semantics. The size frontier is credited only after exact regular-file content
round-trip, while CMPCT's richer filesystem fidelity is separately covered by canonical product parity tests.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_release as HISTORICAL_TREE

B.CMPCT = CANON
B._tree = lambda root: HISTORICAL_TREE.treehash(root)


def _strict_row_dominance(result: dict) -> dict:
    """Require CMPCT to beat ZIP and Zstd by at least one byte on every frozen workload."""
    rows = result["rows"]
    details = []
    all_zip = True
    all_zstd = True
    for row in rows:
        formats = row["formats"]
        cmpct = formats["cmpct_v030"]
        zip_row = formats["zip_deflate9"]
        zstd_row = formats["tar_zstd19_solid"]
        if not cmpct.get("available") or not zip_row.get("available") or not zstd_row.get("available"):
            zip_win = False
            zstd_win = False
        else:
            cmpct_bytes = int(cmpct["archive_bytes"])
            zip_bytes = int(zip_row["archive_bytes"])
            zstd_bytes = int(zstd_row["archive_bytes"])
            zip_win = cmpct_bytes < zip_bytes
            zstd_win = cmpct_bytes < zstd_bytes
        all_zip = all_zip and zip_win
        all_zstd = all_zstd and zstd_win
        details.append({
            "label": row["label"],
            "cmpct_bytes": cmpct.get("archive_bytes"),
            "zip_deflate9_bytes": zip_row.get("archive_bytes"),
            "tar_zstd19_solid_bytes": zstd_row.get("archive_bytes"),
            "strictly_beats_zip": zip_win,
            "strictly_beats_zstd19": zstd_win,
        })
    return {
        "all_workloads_strictly_beat_zip": all_zip,
        "all_workloads_strictly_beat_zstd19": all_zstd,
        "strict_no_ties": all_zip and all_zstd,
        "rows": details,
    }


def run(work_root: Path) -> dict:
    result = dict(B.run(work_root))
    strict = _strict_row_dominance(result)
    gate = dict(result["gate"])
    gate["all_workloads_strictly_beat_zip"] = strict["all_workloads_strictly_beat_zip"]
    gate["all_workloads_strictly_beat_zstd19"] = strict["all_workloads_strictly_beat_zstd19"]
    gate["strict_no_ties_vs_zip_or_zstd19"] = strict["strict_no_ties"]
    gate["passed"] = bool(gate.get("passed")) and all(
        gate[key]
        for key in (
            "all_workloads_strictly_beat_zip",
            "all_workloads_strictly_beat_zstd19",
            "strict_no_ties_vs_zip_or_zstd19",
        )
    )
    result["gate"] = gate
    result["strict_per_workload_dominance"] = strict
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["source_tree_identity"] = "historical-regular-file-content-v0.29-frozen"
    result["product_fidelity_evidence"] = "canonical product parity / native portability lanes"
    result["strict_competitor_contract"] = (
        "For every frozen workload: CMPCT archive_bytes < ZIP/Deflate-9 archive_bytes AND "
        "CMPCT archive_bytes < solid tar+Zstd-19 archive_bytes. Equality is failure."
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
