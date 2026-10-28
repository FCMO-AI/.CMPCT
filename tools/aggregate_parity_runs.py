#!/usr/bin/env python3
from __future__ import annotations

"""Aggregate repeated CMPCT parity runs without hiding deterministic disagreements.

Release CI uses an ABBA order (base, candidate, candidate, base). Each invocation already reports a
within-run median; this tool takes the median of those run summaries. Archive bytes and logical corpus
sizes are not statistical values, so they must agree exactly across all replicates.
"""

import argparse
import copy
import json
from pathlib import Path
import statistics
from typing import Any

TIMING_FIELDS = ("create_s_median", "extract_s_median")
LAYERS = ("library", "cli")
FORMATS = ("cmpct", "zip")


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "cmpct-zip-parity-v1" or not isinstance(data.get("corpora"), dict):
        raise ValueError(f"{path}: not a cmpct-zip-parity-v1 record")
    return data


def exact(values: list[Any], label: str) -> Any:
    first = values[0]
    if any(value != first for value in values[1:]):
        raise ValueError(f"non-deterministic replicate value for {label}: {values!r}")
    return first


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("at least one record is required")
    names = list(records[0]["corpora"])
    exact([set(r["corpora"]) for r in records], "corpus set")
    out = copy.deepcopy(records[0])
    out["aggregate_runs"] = len(records)
    out["aggregate_statistic"] = "median of per-run medians"
    out["source_repetitions_per_run"] = [r.get("repetitions") for r in records]

    for name in names:
        rows = [r["corpora"][name] for r in records]
        out_row = out["corpora"][name]
        out_row["logical_bytes"] = exact([row["logical_bytes"] for row in rows], f"{name}/logical_bytes")
        for layer in LAYERS:
            for fmt in FORMATS:
                cells = [row[layer][fmt] for row in rows]
                target = out_row[layer][fmt]
                target["bytes"] = exact([cell["bytes"] for cell in cells], f"{name}/{layer}/{fmt}/bytes")
                for field in TIMING_FIELDS:
                    target[field] = statistics.median(float(cell[field]) for cell in cells)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("records", type=Path, nargs="+")
    args = ap.parse_args()
    data = aggregate([load(path) for path in args.records])
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"aggregated {len(args.records)} parity runs -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
