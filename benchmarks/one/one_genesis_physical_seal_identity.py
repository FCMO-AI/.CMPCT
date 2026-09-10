from __future__ import annotations

"""Portable scientific identity for the CMPCT1 Genesis physical-input seal.

The physical-input executor records an absolute ``work_root`` for diagnostics.  That path
is useful operational metadata but is not part of the scientific identity of the exam.
This module derives a canonical identity from the immutable workload facts only, so two
runners that materialize the exact same 15 trees at different filesystem paths obtain the
same digest.

This module performs no contender execution, comparison, scoring, or winner selection.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SEAL_SCHEMA = "cmpct-one-genesis-physical-input-seal-v1"
IDENTITY_SCHEMA = "cmpct-one-genesis-physical-input-identity-v1"
ROW_FIELDS = ("suite", "name", "files", "logical_bytes", "tree_sha256")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def canonical_identity(seal: dict[str, Any]) -> dict[str, Any]:
    if seal.get("schema") != SEAL_SCHEMA:
        raise RuntimeError(f"unexpected physical seal schema: {seal.get('schema')!r}")
    if seal.get("all_15_identities_exact") is not True:
        raise RuntimeError("physical seal is not an exact 15-workload identity seal")

    raw_rows = seal.get("rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != 15:
        raise RuntimeError("physical seal must contain exactly 15 workload rows")

    rows: list[dict[str, Any]] = []
    keys: set[tuple[str, str]] = set()
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise RuntimeError("physical seal workload row must be an object")
        missing = [field for field in ROW_FIELDS if field not in raw]
        if missing:
            raise RuntimeError(f"physical seal workload row missing fields: {missing}")
        suite = raw["suite"]
        name = raw["name"]
        if not isinstance(suite, str) or not suite or not isinstance(name, str) or not name:
            raise RuntimeError("physical seal suite/name must be non-empty strings")
        key = (suite, name)
        if key in keys:
            raise RuntimeError(f"duplicate physical seal workload: {suite}/{name}")
        keys.add(key)
        files = raw["files"]
        logical = raw["logical_bytes"]
        tree = raw["tree_sha256"]
        if not isinstance(files, int) or isinstance(files, bool) or files < 0:
            raise RuntimeError(f"{suite}/{name}: files must be a non-negative integer")
        if not isinstance(logical, int) or isinstance(logical, bool) or logical < 0:
            raise RuntimeError(f"{suite}/{name}: logical_bytes must be a non-negative integer")
        if not _is_sha256(tree):
            raise RuntimeError(f"{suite}/{name}: tree_sha256 must be 64 lowercase hex characters")
        rows.append({field: raw[field] for field in ROW_FIELDS})

    rows.sort(key=lambda row: (row["suite"], row["name"]))
    suite_counts: dict[str, int] = {}
    for row in rows:
        suite_counts[row["suite"]] = suite_counts.get(row["suite"], 0) + 1
    if suite_counts != {"neutral_hostile_v1": 10, "resemblance_hostile_v1": 5}:
        raise RuntimeError(f"unexpected frozen suite distribution: {suite_counts!r}")

    return {
        "schema": IDENTITY_SCHEMA,
        "claim_boundary": "portable exact physical-input identity only; excludes runner-local paths and all contender results",
        "all_15_identities_exact": True,
        "rows": rows,
    }


def identity_digest(identity: dict[str, Any]) -> str:
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def receipt(seal: dict[str, Any]) -> dict[str, Any]:
    identity = canonical_identity(seal)
    return {
        "schema": "cmpct-one-genesis-physical-input-identity-receipt-v1",
        "scientific_identity_sha256": identity_digest(identity),
        "scientific_identity": identity,
        "diagnostic_work_root": seal.get("work_root"),
        "work_root_in_scientific_digest": False,
        "contender_measurement_executed": False,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = receipt(_load(args.seal))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"scientific_identity_sha256": result["scientific_identity_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
