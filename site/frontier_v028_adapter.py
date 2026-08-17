from __future__ import annotations

"""Normalize durable EntropyGraph II evidence into the website's frontier payload.

Footnote: this adapter exists because v0.28 measures a portfolio against its inherited frontier and a
structural competitor sweep, while the older site schema assumed ZIP/Zstd was always the primary
research comparator. The adapter derives every displayed byte/percentage from the committed JSON and
never renames one competitor as another merely to satisfy an old UI assumption.
"""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "benchmarks" / "history"
SCHEMA = "cmpct-public-entropygraph-v028-benchmark-v1"


def _pct_smaller(candidate: int, other: int) -> float | None:
    if other <= 0:
        return None
    return (other - candidate) / other * 100.0


def _latest_record() -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[tuple[int, int, int], str, Path, dict[str, Any]]] = []
    for path in HISTORY.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("schema") != SCHEMA:
            continue
        try:
            version = tuple(int(x) for x in str(data.get("project_version", "0.0.0")).split("."))
        except ValueError:
            version = (0, 0, 0)
        matches.append(((version + (0, 0, 0))[:3], str(data.get("date") or ""), path, data))
    if not matches:
        return None
    _, _, path, data = max(matches, key=lambda row: (row[0], row[1], row[2].name))
    return path, data


def _structural_totals(record: dict[str, Any]) -> dict[str, int]:
    """Add the two disjoint public aggregate trees without changing competitor semantics."""
    aliases = {
        "zip_deflate9": "ZIP / Deflate",
        "tar_zstd19_solid": "tar / Zstd solid",
        "seven_zip_lzma2": "7z / LZMA2",
        "zpaq_m5": "ZPAQ m5",
        "borg": "Borg",
    }
    totals = {label: 0 for label in aliases.values()}
    seen = {label: 0 for label in aliases.values()}
    structural = record.get("structural_competitors") or {}
    for suite in structural.get("rows") or []:
        for key, label in aliases.items():
            cell = (suite.get("competitors") or {}).get(key) or {}
            if cell.get("available") and isinstance(cell.get("bytes"), int):
                totals[label] += int(cell["bytes"])
                seen[label] += 1
    # Footnote: only expose a combined number when the competitor was available on both disjoint
    # aggregate trees. Partial sums would make a smaller-looking but semantically incomplete bar.
    return {label: value for label, value in totals.items() if seen[label] == 2}


def normalize(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    totals = record.get("totals") or {}
    candidate = int(totals.get("candidate_bytes") or 0)
    inherited = int(totals.get("inherited_v025_bytes") or 0)
    rows = list(record.get("rows") or [])
    logical = sum(int(row.get("logical_bytes") or 0) for row in rows)
    files = sum(int(row.get("files") or 0) for row in rows)

    competitors: list[dict[str, Any]] = [
        {
            "name": "CMPCT EntropyGraph II portfolio",
            "short": "CMPCT v0.28",
            "bytes": candidate,
            "lead_pct": 0.0,
            "role": "candidate",
        },
        {
            "name": "Inherited EntropyGraph v0.25 frontier",
            "short": "EntropyGraph v0.25",
            "bytes": inherited,
            "lead_pct": _pct_smaller(candidate, inherited),
            "role": "baseline",
        },
    ]
    for label, size in _structural_totals(record).items():
        competitors.append(
            {
                "name": label,
                "short": label,
                "bytes": size,
                "lead_pct": _pct_smaller(candidate, size),
                "role": "diagnostic" if "solid" in label.lower() else "competitor",
            }
        )

    workloads = []
    for row in rows:
        current = int(row.get("candidate_bytes") or 0)
        base = int(row.get("inherited_v025_bytes") or 0)
        workloads.append(
            {
                **row,
                "cmpct_vs_primary_pct": _pct_smaller(current, base),
                "improved": current < base,
                "fallback": row.get("selected") != "resemblance",
            }
        )

    primary_lead = _pct_smaller(candidate, inherited)
    return {
        "file": path.name,
        "date": record.get("date"),
        "kind": "research-frontier",
        "schema": SCHEMA,
        "render_contract": "entropygraph-v028",
        "project_version": record.get("project_version"),
        "canonical_format_revision": record.get("canonical_format_revision"),
        "candidate": record.get("candidate") or {},
        "contract": record.get("benchmark_contract") or {},
        "logical_bytes": logical,
        "files": files,
        "workload_count": len(workloads),
        "archive_bytes": candidate,
        "ratio": candidate / logical if logical else None,
        "saved_pct": _pct_smaller(candidate, logical),
        "primary_comparator": {
            "short": "EntropyGraph v0.25",
            "name": "inherited EntropyGraph v0.25 frontier",
            "bytes": inherited,
            "lead_pct": primary_lead,
        },
        "wins_primary": int(totals.get("workloads_improved") or 0),
        "regressions_primary": int(totals.get("workloads_regressed") or 0),
        "resemblance_selected": int(totals.get("resemblance_selected") or 0),
        "delta_nodes": int(totals.get("delta_nodes") or 0),
        "preflate_wins": int(totals.get("preflate_wins") or 0),
        "competitors": competitors,
        "workloads": workloads,
        "known_losses": record.get("known_limits") or [],
        "structural_competitor_contract": (record.get("structural_competitors") or {}).get("method") or {},
    }


def patch_project_data(output: Path) -> bool:
    found = _latest_record()
    path = output / "project-data.json"
    if found is None or not path.exists():
        return False
    record_path, record = found
    frontier = normalize(record_path, record)
    payload = json.loads(path.read_text(encoding="utf-8"))
    history = [row for row in list(payload.get("frontier_history") or []) if row.get("project_version") != frontier.get("project_version")]
    history.insert(0, frontier)
    payload["frontier"] = frontier
    payload["frontier_history"] = history
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return True
