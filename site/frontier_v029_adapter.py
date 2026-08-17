from __future__ import annotations

"""Normalize durable Mosaic v0.29 evidence into the website's frontier payload.

Footnote: v0.29 deliberately keeps two benchmark questions separate, just as v0.28 does:
(1) release delta — does accepted attempt #5 beat the exact v0.28 portfolio on the portable inherited
frontier without a size regression? and (2) current cross-format position — how does the same accepted
engine compare with external archive tools on one matched hostile whole-suite tree? These aggregation
contracts are different on purpose and must never be added together or substituted for one another.
"""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "benchmarks" / "history"
SCHEMA = "cmpct-public-mosaic-v029-benchmark-v1"


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
        # Footnote: the public structural record may include its candidate in the same comparator array
        # for standalone readability. The normalized site already inserts exactly one authoritative
        # candidate row above, so carrying that source row through would create two candidates and make
        # a malformed comparison ladder look superficially valid until the Pages coherence gate runs.
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


def normalize(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    portable = record.get("portable_frontier") or {}
    rows = list(portable.get("rows") or [])
    baseline = int(portable.get("v028_bytes") or 0)
    release_candidate = int(portable.get("candidate_bytes") or 0)
    release_lead = _pct_smaller(release_candidate, baseline)
    matched_candidate, matched_logical, matched_files, competitors = _matched_competitors(record)

    workloads: list[dict[str, Any]] = []
    for row in rows:
        current = int(row.get("candidate_bytes") or 0)
        base = int(row.get("v028_bytes") or 0)
        workloads.append(
            {
                **row,
                "cmpct_vs_primary_pct": _pct_smaller(current, base),
                "improved": current < base,
                "fallback": row.get("selected") != "mosaic",
            }
        )

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
        # Footnote: these top-level fields power the cross-format arena and therefore use only the
        # matched structural aggregate. The portable 15-workload direct-base release delta stays below.
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
            "competitors": competitors,
            "method": (record.get("structural_aggregate") or {}).get("method") or {},
        },
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
