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
import math
from pathlib import Path
import statistics
from typing import Any

TIMING_FIELDS = ("create_s_median", "extract_s_median")
LAYERS = ("library", "cli")
FORMATS = ("cmpct", "zip")


def load(path: Path) -> dict[str, Any]:
    # The final release comparator may reject ambiguous JSON, but by that
    # point this ABBA reducer has already rewritten the raw run records.
    # Reject duplicate names and nonfinite numbers here, before medians and
    # deterministic-byte checks can launder contradictory source evidence.
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f"{path}: duplicate JSON object key {key!r}")
            obj[key] = value
        return obj

    def finite_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"{path}: nonfinite JSON floating-point value {token!r}")
        return value

    def reject_constant(token: str) -> None:
        raise ValueError(f"{path}: nonfinite JSON constant {token!r}")

    data = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_float=finite_float,
        parse_constant=reject_constant,
    )
    if data.get("schema") != "cmpct-zip-parity-v1" or not isinstance(data.get("corpora"), dict):
        raise ValueError(f"{path}: not a cmpct-zip-parity-v1 record")

    # The final CMPCT comparator checks its own normalized CMPCT metrics,
    # not the original ZIP controls, and float("nan") accepts a JSON *string*.
    # Validate both physical formats at the raw-run boundary so the reducer
    # cannot convert an invalid typed observation into apparently valid proof.
    corpora = data["corpora"]
    if not corpora:
        raise ValueError(f"{path}: expected at least one release-parity corpus")
    for name, row in corpora.items():
        if not isinstance(name, str) or not name or not isinstance(row, dict):
            raise ValueError(f"{path}: expected nonempty corpus name and mapping")
        logical = row.get("logical_bytes")
        if type(logical) is not int or logical < 0:
            raise ValueError(f"{path}: {name}/logical_bytes: expected nonnegative integer")
        for layer in LAYERS:
            containers = row.get(layer)
            if not isinstance(containers, dict):
                raise ValueError(f"{path}: {name}/{layer}: expected format mapping")
            for fmt in FORMATS:
                metric = containers.get(fmt)
                if not isinstance(metric, dict):
                    raise ValueError(f"{path}: {name}/{layer}/{fmt}: expected metric mapping")
                size = metric.get("bytes")
                if type(size) is not int or size <= 0:
                    raise ValueError(f"{path}: {name}/{layer}/{fmt}/bytes: expected positive integer")
                for field in TIMING_FIELDS:
                    value = metric.get(field)
                    if type(value) not in (int, float):
                        raise ValueError(f"{path}: {name}/{layer}/{fmt}/{field}: expected positive finite seconds")
                    try:
                        finite = math.isfinite(value)
                    except OverflowError:
                        finite = False
                    if not finite or value <= 0:
                        raise ValueError(f"{path}: {name}/{layer}/{fmt}/{field}: expected positive finite seconds")
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
    # All ABBA observations must describe the same experiment. Numeric-only
    # equality cannot repair a run that used a different timing/cache/integrity
    # regime; copying the first record would silently launder that conflict.
    semantic_fields = (
        "schema", "timing_statistic", "cache_semantics",
        "integrity_semantics", "filesystem_semantic_mismatch",
        "corpus_semantics",
    )
    def semantic_token(record: dict[str, Any], field: str) -> tuple[bool, str | None]:
        # Canonical JSON distinguishes bool from int, missing from explicit null,
        # and nested integrity declarations while ignoring irrelevant key order.
        return (field in record, json.dumps(
            record[field], sort_keys=True, separators=(",", ":"), allow_nan=False
        ) if field in record else None)

    for field in semantic_fields:
        exact([semantic_token(record, field) for record in records], f"ABBA/{field}")

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
