from __future__ import annotations

"""Normalize durable Mosaic v0.29 evidence into the website's frontier payload.

Footnote: v0.29 has three research benchmark questions that must stay separate:
(1) release delta — does accepted attempt #5 beat the exact v0.28 portable frontier?
(2) structural position — how does current v0.29 compare with external tools on one matched hostile
    whole-suite tree?
(3) category frontier — on each exact individual workload tree, where does v0.29 beat or lose to a
    serious solid Zstandard size baseline, with ZIP/Deflate retained as familiar secondary context?
Canonical executable ZIP size/create/extract parity is a fourth site surface owned by build_site.py.
Different aggregation contracts may be numerically close, but they are never interchangeable.
"""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "benchmarks" / "history"
SCHEMA = "cmpct-public-mosaic-v029-benchmark-v1"
CATEGORY_SCHEMA = "cmpct-public-mosaic-v029-category-v1"


def _pct_smaller(candidate: int, other: int) -> float | None:
    if other <= 0:
        return None
    return (other - candidate) / other * 100.0


def _version_key(value: str | None) -> tuple[int, int, int]:
    try:
        bits = [int(x) for x in str(value or "0.0.0").split(".")]
    except ValueError:
        return (0, 0, 0)
    return tuple((bits + [0, 0, 0])[:3])  # type: ignore[return-value]


def _latest_record() -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[tuple[int, int, int], str, Path, dict[str, Any]]] = []
    for path in HISTORY.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("schema") != SCHEMA:
            continue
        matches.append((_version_key(data.get("project_version")), str(data.get("date") or ""), path, data))
    if not matches:
        return None
    _, _, path, data = max(matches, key=lambda row: (row[0], row[1], row[2].name))
    return path, data


def _latest_category_record(project_version: str | None) -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[str, Path, dict[str, Any]]] = []
    for path in HISTORY.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("schema") != CATEGORY_SCHEMA:
            continue
        if str(data.get("project_version") or "") != str(project_version or ""):
            continue
        matches.append((str(data.get("date") or ""), path, data))
    if not matches:
        return None
    _, path, data = max(matches, key=lambda row: (row[0], row[1].name))
    return path, data


def _matched_competitors(record: dict[str, Any]) -> tuple[int, int, int, list[dict[str, Any]]]:
    """Build one honest same-tree comparison ladder from the committed structural snapshot.

    Footnote: competitor rows are accepted only when they carry explicit bytes from the same structural
    aggregate named by the v0.29 record. The adapter does not borrow a missing ZIP, Borg, or other number
    from an older release merely to make the homepage look fuller.
    """
    structural = record.get("structural_aggregate") or {}
    candidate = int(structural.get("candidate_bytes") or 0)
    logical = int(structural.get("logical_bytes") or 0)
    files = int(structural.get("files") or 0)
    rows: list[dict[str, Any]] = []
    if candidate:
        rows.append(
            {
                "name": str((record.get("candidate") or {}).get("name") or "CMPCT Mosaic attempt #5"),
                "short": "CMPCT v0.29",
                "bytes": candidate,
                "lead_pct": 0.0,
                "role": "candidate",
            }
        )
    for raw in list(structural.get("competitors") or []):
        # Footnote: the source record is standalone-readable and may include its candidate in the same
        # array. The normalized site inserts exactly one candidate above, so skip that duplicate row.
        if raw.get("role") == "candidate":
            continue
        size = raw.get("bytes")
        if not isinstance(size, int) or size <= 0 or not candidate:
            continue
        rows.append(
            {
                "name": str(raw.get("name") or raw.get("short") or "archive comparator"),
                "short": str(raw.get("short") or raw.get("name") or "archive comparator"),
                "bytes": size,
                "lead_pct": _pct_smaller(candidate, size),
                "role": str(raw.get("role") or "competitor"),
            }
        )
    return candidate, logical, files, rows


def _category_snapshot(project_version: str | None, portable_rows: list[dict[str, Any]]) -> dict[str, Any]:
    found = _latest_category_record(project_version)
    if found is None:
        return {}
    path, record = found
    contract = record.get("benchmark_contract") or record.get("contract") or {}
    source_rows = list(record.get("rows") or [])
    by_key = {
        (str(row.get("suite") or ""), str(row.get("name") or "")): row
        for row in source_rows
    }
    expected = {
        (str(row.get("suite") or ""), str(row.get("name") or ""))
        for row in portable_rows
    }

    # Footnote: category boasting is all-or-nothing. The proof we need is that CMPCT and the external
    # baselines shared one exact live tree *inside each category run*, not that a later benchmark run
    # reproduces an old office/media container bit-for-bit. Producer metadata can legitimately vary
    # across separate runs. Complete workload-key coverage plus row-local tree hashes and the explicit
    # same-lifetime contract are therefore the correct provenance boundary.
    if contract.get("same_lifetime_measurement") is not True:
        return {}
    if contract.get("all_workloads_required") is not True:
        return {}
    if len(by_key) != len(source_rows) or set(by_key) != expected:
        return {}

    rows: list[dict[str, Any]] = []
    for inherited in portable_rows:
        key = (str(inherited.get("suite") or ""), str(inherited.get("name") or ""))
        raw = by_key[key]
        candidate = int(raw.get("cmpct_bytes") or 0)
        zstd = int(raw.get("tar_zstd19_solid_bytes") or 0)
        zip_bytes = int(raw.get("zip_deflate9_bytes") or 0)
        tree = str(raw.get("tree_sha256") or "")
        if candidate <= 0 or zstd <= 0 or zip_bytes <= 0 or len(tree) != 64:
            return {}
        rows.append(
            {
                "suite": key[0],
                "name": key[1],
                "baseline_identity": raw.get("baseline_identity") or inherited.get("baseline_identity"),
                "files": int(raw.get("files") or inherited.get("files") or 0),
                "logical_bytes": int(raw.get("logical_bytes") or inherited.get("logical_bytes") or 0),
                "tree_sha256": tree,
                "cmpct_bytes": candidate,
                "zstd_bytes": zstd,
                "zip_deflate_bytes": zip_bytes,
                "cmpct_vs_zstd_pct": _pct_smaller(candidate, zstd),
                "cmpct_vs_zip_deflate_pct": _pct_smaller(candidate, zip_bytes),
            }
        )

    candidate_total = sum(row["cmpct_bytes"] for row in rows)
    zstd_total = sum(row["zstd_bytes"] for row in rows)
    zip_total = sum(row["zip_deflate_bytes"] for row in rows)
    return {
        "file": path.name,
        "date": record.get("date"),
        "baseline_short": "tar / Zstd solid",
        "baseline_name": "solid tar + Zstandard-19",
        "secondary_short": "ZIP / Deflate",
        "candidate_bytes": candidate_total,
        "zstd_bytes": zstd_total,
        "zip_deflate_bytes": zip_total,
        "lead_vs_zstd_pct": _pct_smaller(candidate_total, zstd_total),
        "lead_vs_zip_deflate_pct": _pct_smaller(candidate_total, zip_total),
        "workloads": len(rows),
        "wins_vs_zstd": sum(row["cmpct_bytes"] < row["zstd_bytes"] for row in rows),
        "losses_vs_zstd": sum(row["cmpct_bytes"] > row["zstd_bytes"] for row in rows),
        "ties_vs_zstd": sum(row["cmpct_bytes"] == row["zstd_bytes"] for row in rows),
        "rows": rows,
        "contract": contract,
        "source": record.get("source") or {},
    }


def normalize(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    portable = record.get("portable_frontier") or {}
    source_rows = list(portable.get("rows") or [])
    baseline = int(portable.get("v028_bytes") or 0)
    release_candidate = int(portable.get("candidate_bytes") or 0)
    release_lead = _pct_smaller(release_candidate, baseline)
    matched_candidate, matched_logical, matched_files, competitors = _matched_competitors(record)
    category = _category_snapshot(record.get("project_version"), source_rows)
    category_by_key = {
        (str(row.get("suite") or ""), str(row.get("name") or "")): row
        for row in list(category.get("rows") or [])
    }

    workloads: list[dict[str, Any]] = []
    for row in source_rows:
        current = int(row.get("candidate_bytes") or 0)
        base = int(row.get("v028_bytes") or 0)
        key = (str(row.get("suite") or ""), str(row.get("name") or ""))
        external = category_by_key.get(key) or {}
        workloads.append(
            {
                **row,
                "cmpct_vs_primary_pct": _pct_smaller(current, base),
                "improved": current < base,
                "fallback": row.get("selected") != "mosaic",
                "category_zstd_bytes": external.get("zstd_bytes"),
                "category_zip_deflate_bytes": external.get("zip_deflate_bytes"),
                "cmpct_vs_zstd_pct": external.get("cmpct_vs_zstd_pct"),
                "cmpct_vs_zip_deflate_pct": external.get("cmpct_vs_zip_deflate_pct"),
            }
        )

    # ZIP is the familiar adoption headline requested for the public first impression. Zstd remains the
    # serious compression baseline and may legitimately show a negative CMPCT result. Never relabel a
    # negative Zstd delta as a lead merely to preserve the rhetoric.
    headline_short = "ZIP / Deflate"
    if not any(row.get("short") == headline_short for row in competitors):
        headline_short = str((record.get("structural_aggregate") or {}).get("headline_comparator_short") or "")
    if not any(row.get("short") == headline_short for row in competitors):
        headline_short = next(
            (str(row.get("short")) for row in competitors if row.get("role") == "competitor"),
            "",
        )

    return {
        "file": path.name,
        "date": record.get("date"),
        "kind": "research-frontier",
        "schema": SCHEMA,
        "render_contract": "mosaic-v029",
        "project_version": record.get("project_version"),
        "canonical_format_revision": record.get("canonical_format_revision"),
        "candidate": record.get("candidate") or {},
        "contract": record.get("benchmark_contract") or {},
        # Footnote: top-level fields power only the matched structural arena. The category frontier and
        # portable direct-base release delta each keep their own independently auditable byte totals.
        "logical_bytes": matched_logical,
        "files": matched_files,
        "workload_count": len(workloads),
        "archive_bytes": matched_candidate,
        "ratio": matched_candidate / matched_logical if matched_logical else None,
        "saved_pct": _pct_smaller(matched_candidate, matched_logical),
        "competitors": competitors,
        "overall_comparison": {
            "candidate_bytes": matched_candidate,
            "logical_bytes": matched_logical,
            "files": matched_files,
            "suite_count": 1 if matched_candidate else 0,
            "headline_comparator_short": headline_short,
            "serious_comparator_short": "tar / Zstd solid",
            "competitors": competitors,
            "method": (record.get("structural_aggregate") or {}).get("method") or {},
        },
        "category_comparison": category,
        "release_delta": {
            "candidate_bytes": release_candidate,
            "baseline_bytes": baseline,
            "baseline_short": "CMPCT v0.28",
            "lead_pct": release_lead,
            "workloads": len(workloads),
            "workloads_improved": int(portable.get("workloads_improved") or 0),
            "workloads_regressed": int(portable.get("workloads_regressed") or 0),
            "research_selected": int(portable.get("research_selected") or 0),
            "saving_bytes": baseline - release_candidate,
        },
        "primary_comparator": {
            "short": "CMPCT v0.28",
            "name": "exact embedded v0.28 portfolio",
            "bytes": baseline,
            "lead_pct": release_lead,
        },
        "wins_primary": int(portable.get("workloads_improved") or 0),
        "regressions_primary": int(portable.get("workloads_regressed") or 0),
        "research_selected": int(portable.get("research_selected") or 0),
        "residual_pack_records": int(portable.get("residual_pack_records") or 0),
        "residual_packed_delta_nodes": int(portable.get("residual_packed_delta_nodes") or 0),
        "workloads": workloads,
        "scheduler": record.get("scheduler") or {},
        "mechanism_gate": record.get("mechanism_gate") or {},
        "known_losses": record.get("known_limits") or [],
        "structural_competitor_contract": (record.get("structural_aggregate") or {}).get("method") or {},
    }


def patch_project_data(output: Path) -> bool:
    found = _latest_record()
    path = output / "project-data.json"
    if found is None or not path.exists():
        return False
    record_path, record = found
    frontier = normalize(record_path, record)
    payload = json.loads(path.read_text(encoding="utf-8"))
    history = [
        row
        for row in list(payload.get("frontier_history") or [])
        if row.get("project_version") != frontier.get("project_version")
    ]
    history.insert(0, frontier)
    payload["frontier"] = frontier
    payload["frontier_history"] = history
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return True
