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

from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_release as HISTORICAL_TREE

B.CMPCT = CANON
B._tree = lambda root: HISTORICAL_TREE.treehash(root)


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
