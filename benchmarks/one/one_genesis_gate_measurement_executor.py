from __future__ import annotations

"""Sealed raw-measurement executor for the CMPCT1 Genesis gate.

This module deliberately stops *before* comparison/adjudication.  Its job is to bind one
candidate and the two frozen comparators to the exact 15-workload authority, execute each
contender through an explicit adapter contract, and persist each contender's raw output
before producing a joined raw-measurement bundle.

Before 2026-09-11 America/Mexico_City only ``--fixture`` is legal.  Fixture mode never
invokes contender code and is permanently marked synthetic/non-evidence.  Real execution
requires both the calendar gate and the explicit ``--execute-real-gate`` switch.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from zoneinfo import ZoneInfo

from benchmarks.one.one_genesis_gate_executor_preflight import (
    V029_SHA,
    V030_SHA,
    build_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_MANIFEST = ROOT / "benchmarks" / "one" / "genesis_gate_workload_identity_v1.json"
TZ = ZoneInfo("America/Mexico_City")
CONTENDERS = ("cmpct1", "v0.29", "v0.30")
REQUIRED_MEASUREMENT_KEYS = (
    "stored_bytes",
    "creation",
    "whole_read",
    "selective_access",
    "semantics",
    "reader_burden",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _looks_like_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(TZ)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def _gate_open(now: datetime) -> bool:
    return now.date().isoformat() >= "2026-09-11"


def _identity_rows() -> list[dict[str, Any]]:
    payload = _load(IDENTITY_MANIFEST)
    rows = payload.get("workloads")
    if payload.get("schema") != "cmpct-one-genesis-gate-workload-identity-v1" or not isinstance(rows, list):
        raise RuntimeError("invalid frozen workload identity manifest")
    if len(rows) != 15:
        raise RuntimeError(f"expected 15 frozen workload identities, got {len(rows)}")
    keys = [(row.get("suite"), row.get("name")) for row in rows]
    if len(set(keys)) != 15:
        raise RuntimeError("frozen workload identity manifest contains duplicate rows")
    return rows


def _fixture_measurement(identity: dict[str, Any], contender: str) -> dict[str, Any]:
    """Deterministic plumbing-only values; never admissible as scientific evidence."""
    logical = int(identity["logical_bytes"])
    offset = {"cmpct1": 11, "v0.29": 17, "v0.30": 23}[contender]
    stored = logical + offset
    return {
        "stored_bytes": stored,
        "creation": {"measured": True, "cpu_s": 0.001, "wall_s": 0.001, "peak_rss_bytes": 1},
        "whole_read": {"measured": True, "cpu_s": 0.001, "wall_s": 0.001},
        "selective_access": {
            "measured": True,
            "requested_bytes": min(4096, logical),
            "touched_bytes": min(4096, logical),
            "decoded_bytes": min(4096, logical),
            "authentication_bytes": 1,
            "reconstruction_work": min(4096, logical),
            "temporary_bytes": 1,
        },
        "semantics": {"exact": True, "integrity": True, "recovery": True, "portable": True},
        "reader_burden": {"reader_discovery": False, "hidden_codec": False},
    }


def _fixture_output(contender: str, source_sha: str) -> dict[str, Any]:
    return {
        "schema": "cmpct-one-genesis-contender-raw-v1",
        "contender": contender,
        "source_sha": source_sha,
        "synthetic": True,
        "production_eligible": False,
        "rows": [
            {**identity, "measurement": _fixture_measurement(identity, contender)}
            for identity in _identity_rows()
        ],
    }


def _adapter_output(
    contender: str,
    source_sha: str,
    adapter: dict[str, Any],
    work_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    command = adapter.get("command")
    checkout = Path(str(adapter.get("checkout", ""))).resolve()
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
        raise RuntimeError(f"{contender}: adapter command must be a non-empty argv list")
    if not checkout.is_dir():
        raise RuntimeError(f"{contender}: adapter checkout does not exist: {checkout}")

    observed = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if observed != source_sha:
        raise RuntimeError(f"{contender}: checkout HEAD {observed} != sealed source {source_sha}")

    env = os.environ.copy()
    env.update(
        {
            "CMPCT_GENESIS_CONTENDER": contender,
            "CMPCT_GENESIS_SOURCE_SHA": source_sha,
            "CMPCT_GENESIS_WORK_ROOT": str(work_root.resolve()),
            "CMPCT_GENESIS_OUTPUT": str(output_path.resolve()),
        }
    )
    subprocess.run(command, cwd=checkout, env=env, check=True)
    if not output_path.is_file():
        raise RuntimeError(f"{contender}: adapter did not persist CMPCT_GENESIS_OUTPUT")
    return _load(output_path)


def _validate_raw(payload: dict[str, Any], contender: str, expected_sha: str, *, synthetic: bool) -> None:
    errors: list[str] = []
    if payload.get("schema") != "cmpct-one-genesis-contender-raw-v1":
        errors.append("wrong schema")
    if payload.get("contender") != contender:
        errors.append("wrong contender id")
    if payload.get("source_sha") != expected_sha:
        errors.append("wrong source sha")
    if payload.get("synthetic") is not synthetic:
        errors.append("synthetic marker mismatch")
    if synthetic and payload.get("production_eligible") is not False:
        errors.append("fixture output must be production_eligible=false")
    if not synthetic and payload.get("production_eligible") is not True:
        errors.append("real adapter output must be production_eligible=true")

    expected = {(row["suite"], row["name"]): row for row in _identity_rows()}
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 15:
        errors.append("raw output must contain exactly 15 rows")
        rows = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.get("suite"), row.get("name"))
        if key in seen:
            errors.append(f"duplicate row {key}")
            continue
        seen.add(key)
        frozen = expected.get(key)
        if frozen is None:
            errors.append(f"unexpected workload {key}")
            continue
        for field in ("files", "logical_bytes", "tree_sha256"):
            if row.get(field) != frozen.get(field):
                errors.append(f"{key}: {field} differs from frozen identity")
        measurement = row.get("measurement")
        if not isinstance(measurement, dict):
            errors.append(f"{key}: missing measurement object")
            continue
        missing = [field for field in REQUIRED_MEASUREMENT_KEYS if field not in measurement]
        if missing:
            errors.append(f"{key}: missing measurement fields {missing}")
    if set(expected) != seen:
        errors.append("raw output does not cover exactly the frozen workload set")
    if errors:
        raise RuntimeError(f"{contender} raw output invalid: " + "; ".join(errors))


def execute(
    *,
    candidate_sha: str,
    raw_dir: Path,
    now_value: str | None,
    fixture: bool,
    execute_real_gate: bool,
    adapters_path: Path | None,
    work_root: Path | None,
) -> dict[str, Any]:
    if not _looks_like_sha(candidate_sha):
        raise RuntimeError("candidate SHA must be a 40-hex commit")
    now = _now(now_value)
    opened = _gate_open(now)

    # Reuse the already-falsified authority/candidate binding rather than reimplementing it.
    preflight = build_receipt(candidate_sha=candidate_sha, now_value=now.isoformat(), allow_dirty_tracked_tree=False)
    if preflight.get("verdict") != "EXECUTOR_PREFLIGHT_READY":
        raise RuntimeError("Genesis executor preflight is not READY")

    if fixture:
        if execute_real_gate or adapters_path is not None or work_root is not None:
            raise RuntimeError("fixture mode cannot accept real-execution inputs")
    else:
        if not opened:
            raise RuntimeError("real Genesis contender execution is calendar-locked until 2026-09-11 America/Mexico_City")
        if not execute_real_gate:
            raise RuntimeError("real Genesis execution requires explicit --execute-real-gate")
        if adapters_path is None or work_root is None:
            raise RuntimeError("real Genesis execution requires --adapters and --work-root")

    sources = {"cmpct1": candidate_sha, "v0.29": V029_SHA, "v0.30": V030_SHA}
    raw_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, dict[str, Any]] = {}
    adapter_manifest: dict[str, Any] = {}
    if not fixture:
        adapter_manifest = _load(adapters_path)  # type: ignore[arg-type]
        if adapter_manifest.get("schema") != "cmpct-one-genesis-adapters-v1":
            raise RuntimeError("invalid Genesis adapter manifest schema")
        if set(adapter_manifest.get("adapters", {})) != set(CONTENDERS):
            raise RuntimeError("adapter manifest must define exactly cmpct1, v0.29, v0.30")

    # Sequential persistence is intentional: a later failure cannot erase earlier raw evidence.
    for contender in CONTENDERS:
        raw_path = raw_dir / f"{contender.replace('.', '')}-raw.json"
        if fixture:
            payload = _fixture_output(contender, sources[contender])
            _write(raw_path, payload)
        else:
            payload = _adapter_output(
                contender,
                sources[contender],
                adapter_manifest["adapters"][contender],
                work_root,  # type: ignore[arg-type]
                raw_path,
            )
        _validate_raw(payload, contender, sources[contender], synthetic=fixture)
        outputs[contender] = payload

    frozen = _identity_rows()
    joined_rows = []
    by_contender = {
        contender: {(row["suite"], row["name"]): row for row in outputs[contender]["rows"]}
        for contender in CONTENDERS
    }
    for identity in frozen:
        key = (identity["suite"], identity["name"])
        joined_rows.append(
            {
                **identity,
                "measurements": {
                    contender: by_contender[contender][key]["measurement"] for contender in CONTENDERS
                },
            }
        )

    return {
        "schema": "cmpct-one-genesis-raw-measurements-v1",
        "claim_boundary": "raw contender measurements only; no comparisons, scoring, or winner selection",
        "experimental_version": "ONE-G0.2",
        "cmpct1_candidate_sha": candidate_sha,
        "frozen_comparators": {"v0.29": V029_SHA, "v0.30": V030_SHA},
        "gate_open": opened,
        "synthetic": fixture,
        "production_eligible": not fixture,
        "raw_files": [str((raw_dir / f"{name.replace('.', '')}-raw.json").resolve()) for name in CONTENDERS],
        "workloads": joined_rows,
        "execution_state": {
            "contender_measurement_executed": not fixture,
            "fixture_plumbing_executed": fixture,
            "comparisons_executed": False,
            "scoring_executed": False,
            "winner_selected": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--now")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--execute-real-gate", action="store_true")
    parser.add_argument("--adapters", type=Path)
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args()

    result = execute(
        candidate_sha=args.candidate_sha,
        raw_dir=args.raw_dir,
        now_value=args.now,
        fixture=args.fixture,
        execute_real_gate=args.execute_real_gate,
        adapters_path=args.adapters,
        work_root=args.work_root,
    )
    _write(args.output, result)
    print(json.dumps({
        "schema": result["schema"],
        "candidate": result["cmpct1_candidate_sha"],
        "gate_open": result["gate_open"],
        "synthetic": result["synthetic"],
        "workloads": len(result["workloads"]),
        "scoring_executed": result["execution_state"]["scoring_executed"],
    }, indent=2))


if __name__ == "__main__":
    main()
