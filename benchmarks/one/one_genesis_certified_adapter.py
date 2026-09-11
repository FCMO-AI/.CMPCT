from __future__ import annotations

"""Certification firewall for the real CMPCT1 Genesis adapter path.

This script belongs to the harness checkout, not to any contender checkout. The executor
runs it with cwd set to the sealed contender checkout. For CMPCT1 it requires the durable
candidate-boundary authority to name exactly the same frozen commit that the executor
selected before delegating to the raw adapter. It also routes the CMPCT1 phase worker
through a launcher that imports the product runtime from the sealed contender checkout,
not from the newer harness checkout.

No workload generation, measurement, comparison, scoring, or winner selection occurs in
this layer.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.one import one_genesis_contender_workload_measurement as workload_measurement
from benchmarks.one.one_genesis_contender_raw_adapter import run as run_raw_adapter

BOUNDARY = ROOT / "benchmarks" / "one" / "genesis_one_candidate_boundary_v1.json"
FROZEN_WORKER_LAUNCHER = ROOT / "benchmarks" / "one" / "one_genesis_cmpct1_frozen_worker_launcher.py"
CERTIFIED_STATUS = "CERTIFIED_FOR_GENESIS"
FORBIDDEN_IGNORED_RUNTIME_SUFFIXES = frozenset((".so", ".dylib", ".dll", ".pyd"))


def _load_boundary() -> dict:
    try:
        payload = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Genesis ONE candidate-boundary authority is unreadable") from exc
    if payload.get("schema") != "cmpct-one-genesis-one-candidate-boundary-v1":
        raise RuntimeError("Genesis ONE candidate-boundary authority has wrong schema")
    return payload


def _assert_initial_contender_checkout_sealed() -> None:
    """Require every contender to start from its committed checkout bytes.

    HEAD identity is necessary but not sufficient: Git can remain at the frozen commit while
    tracked files are edited/deleted or untracked modules are added.  The gate therefore
    rejects ordinary worktree drift for ONE *and* both frozen comparators before any product
    code is invoked.  Ignored caches are allowed, except native libraries that could replace
    or augment committed Python code during import/load.
    """
    checkout = Path.cwd().resolve()
    status = subprocess.run(
        ["git", "-C", str(checkout), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
        capture_output=True,
        check=True,
    )
    if status.stdout.strip():
        raise RuntimeError("Genesis contender checkout has working-tree drift from sealed Git state")

    ignored = subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    dangerous = [
        line
        for line in ignored.stdout.splitlines()
        if Path(line).suffix.lower() in FORBIDDEN_IGNORED_RUNTIME_SUFFIXES
    ]
    if dangerous:
        raise RuntimeError(
            "Genesis contender checkout contains ignored native runtime artifacts: "
            + ", ".join(sorted(dangerous)[:8])
        )


def _assert_cmpct1_certification() -> dict:
    payload = _load_boundary()
    if payload.get("status") != CERTIFIED_STATUS or payload.get("production_eligible") is not True:
        raise RuntimeError("Genesis ONE candidate boundary is not certified for production gate execution")
    certified = payload.get("certified_candidate")
    if not isinstance(certified, dict):
        raise RuntimeError("Genesis ONE candidate certification is missing certified_candidate")
    source = os.environ.get("CMPCT_GENESIS_SOURCE_SHA", "")
    if certified.get("candidate_sha") != source:
        raise RuntimeError("Genesis ONE certified candidate SHA differs from executor-sealed source")
    return certified


def _route_cmpct1_worker_to_frozen_checkout() -> None:
    if not FROZEN_WORKER_LAUNCHER.is_file():
        raise RuntimeError("CMPCT1 frozen worker launcher is missing from certified harness")
    workload_measurement.CMPCT1_WORKER = FROZEN_WORKER_LAUNCHER


def run() -> dict:
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("certified adapter requires explicit real-gate executor authorization")
    _assert_initial_contender_checkout_sealed()
    contender = os.environ.get("CMPCT_GENESIS_CONTENDER", "")
    if contender == "cmpct1":
        _assert_cmpct1_certification()
        _route_cmpct1_worker_to_frozen_checkout()
    return run_raw_adapter()


def main() -> None:
    payload = run()
    print(json.dumps({
        "schema": payload["schema"],
        "contender": payload["contender"],
        "rows": len(payload["rows"]),
        "scoring_executed": payload["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
