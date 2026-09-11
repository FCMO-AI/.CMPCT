from __future__ import annotations

"""Resume/diagnose the frozen v0.30 Genesis contender without rerunning ONE/v0.29.

This is a raw-measurement harness only. It regenerates and seals the exact frozen 15
physical workloads, invokes the same five-sample measurement function used by the sealed
Genesis executor, and persists progress after every workload. It never compares contenders,
scores rows, or selects a winner. A failure receipt records the exact workload and traceback
so a comparator/harness failure cannot be misclassified as scientific evidence.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import traceback
from typing import Any

from benchmarks.one.one_genesis_contender_raw_adapter import (
    _load_identities,
    _workload_path,
)
from benchmarks.one.one_genesis_contender_workload_measurement import measure_workload
from benchmarks.one.one_genesis_gate_measurement_executor import _seal_physical_inputs
from benchmarks.one.one_genesis_selective_access_plan import select_primary_request

V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
SCHEMA = "cmpct-one-genesis-v030-resume-diagnostic-v1"


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _head(checkout: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()


def run(*, checkout: Path, work_root: Path, output: Path, progress: Path) -> dict[str, Any]:
    checkout = checkout.resolve()
    work_root = work_root.resolve()
    if _head(checkout) != V030_SHA:
        raise RuntimeError("v0.30 resume diagnostic checkout differs from frozen Genesis authority")
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("v0.30 resume diagnostic requires real-gate authorization")
    if os.environ.get("CMPCT_GENESIS_SOURCE_SHA") != V030_SHA:
        raise RuntimeError("v0.30 resume diagnostic source SHA is not frozen authority")

    seal = _seal_physical_inputs(work_root)
    identities = _load_identities()
    rows: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_boundary": "v0.30 raw-resume diagnosis only; no comparison, scoring, or winner selection",
        "source_sha": V030_SHA,
        "physical_input_seal": seal,
        "completed_rows": 0,
        "current": None,
        "failure": None,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }
    _write(progress, receipt)

    for identity in identities:
        key = f"{identity['suite']}/{identity['name']}"
        workload = _workload_path(work_root, identity)
        request = select_primary_request(workload)
        receipt["current"] = {
            "workload": key,
            "selective_request": request.to_dict(),
        }
        _write(progress, receipt)
        try:
            result = measure_workload(
                contender="v0.30",
                checkout=checkout,
                root=workload,
                member=request.relative_path if request.status == "selected" else None,
                transfer_fixture=False,
            )
        except BaseException as exc:
            receipt["failure"] = {
                "workload": key,
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
            _write(progress, receipt)
            raise

        measurement = result.get("measurement")
        if not isinstance(measurement, dict):
            raise RuntimeError(f"{key}: missing measurement payload")
        rows.append(
            {
                **identity,
                "selective_request": request.to_dict(),
                "measurement": measurement,
                "workload_measurement_artifact_sha256": result.get("artifact_sha256"),
                "workload_measurement_repetitions": result.get("repetitions"),
                "workload_measurement_statistic": result.get("statistic"),
            }
        )
        receipt["completed_rows"] = len(rows)
        receipt["current"] = {"workload": key, "status": "complete"}
        _write(progress, receipt)

    payload = {
        "schema": "cmpct-one-genesis-contender-raw-v1",
        "claim_boundary": "raw measurements only; no comparison, scoring, aggregate rank, or winner selection",
        "contender": "v0.30",
        "source_sha": V030_SHA,
        "synthetic": False,
        "production_eligible": True,
        "rows": rows,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }
    _write(output, payload)
    receipt["current"] = None
    receipt["complete"] = True
    _write(progress, receipt)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path, required=True)
    args = parser.parse_args()
    payload = run(
        checkout=args.checkout,
        work_root=args.work_root,
        output=args.output,
        progress=args.progress,
    )
    print(json.dumps({"schema": payload["schema"], "contender": "v0.30", "rows": len(payload["rows"])}, sort_keys=True))


if __name__ == "__main__":
    main()
