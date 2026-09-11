from __future__ import annotations

"""Capture the exact child-process failure for the frozen v0.30 Genesis media row.

Diagnostic only: regenerates/seals the authoritative physical Genesis inputs and invokes
exactly one v0.30 historical-worker build for neutral_hostile_v1/03_media_library.
It does not compare contenders, score rows, select a winner, or modify the frozen product.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from benchmarks.one.one_genesis_contender_raw_adapter import _load_identities, _workload_path
from benchmarks.one.one_genesis_gate_measurement_executor import _seal_physical_inputs

V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
TARGET_SUITE = "neutral_hostile_v1"
TARGET_NAME = "03_media_library"
HERE = Path(__file__).resolve().parent
WORKER = HERE / "one_genesis_historical_product_worker.py"
SCHEMA = "cmpct-one-genesis-v030-media-build-stderr-diagnostic-v1"


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _head(checkout: Path) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()


def run(*, checkout: Path, work_root: Path, archive: Path, worker_output: Path, receipt: Path) -> dict[str, Any]:
    checkout = checkout.resolve()
    work_root = work_root.resolve()
    archive = archive.resolve()
    worker_output = worker_output.resolve()

    if _head(checkout) != V030_SHA:
        raise RuntimeError("v0.30 stderr diagnostic checkout differs from frozen Genesis authority")
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("v0.30 stderr diagnostic requires real-gate authorization")
    if os.environ.get("CMPCT_GENESIS_SOURCE_SHA") != V030_SHA:
        raise RuntimeError("v0.30 stderr diagnostic source SHA is not frozen authority")

    seal = _seal_physical_inputs(work_root)
    identities = _load_identities()
    identity = next(
        row for row in identities
        if row.get("suite") == TARGET_SUITE and row.get("name") == TARGET_NAME
    )
    workload = _workload_path(work_root, identity)

    archive.parent.mkdir(parents=True, exist_ok=True)
    worker_output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(WORKER),
        "--contender", "v030",
        "--mode", "build",
        "--checkout", str(checkout),
        "--root", str(workload),
        "--archive", str(archive),
        "--output", str(worker_output),
    ]
    env = os.environ.copy()
    completed = subprocess.run(
        command,
        cwd=checkout,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1800,
        check=False,
    )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_boundary": "single frozen-v0.30 media build failure diagnosis only; no comparison, scoring, or winner selection",
        "source_sha": V030_SHA,
        "target": {"suite": TARGET_SUITE, "name": TARGET_NAME, **identity},
        "physical_input_seal": seal,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "archive_exists": archive.is_file(),
        "archive_bytes": archive.stat().st_size if archive.is_file() else None,
        "worker_output_exists": worker_output.is_file(),
        "worker_output": worker_output.read_text(encoding="utf-8") if worker_output.is_file() else None,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }
    _write(receipt, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--worker-output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    payload = run(
        checkout=args.checkout,
        work_root=args.work_root,
        archive=args.archive,
        worker_output=args.worker_output,
        receipt=args.receipt,
    )
    print(json.dumps({
        "schema": payload["schema"],
        "returncode": payload["returncode"],
        "stderr": payload["stderr"],
    }, sort_keys=True))
    if payload["returncode"] == 0:
        raise SystemExit("diagnostic unexpectedly succeeded; frozen media build failure did not reproduce")


if __name__ == "__main__":
    main()
