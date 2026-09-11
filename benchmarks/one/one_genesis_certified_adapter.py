from __future__ import annotations

"""Certification firewall for the real CMPCT1 Genesis adapter path.

This script belongs to the harness checkout, not to any contender checkout. The executor
runs it with cwd set to the sealed contender checkout. For CMPCT1 it requires the durable
candidate-boundary authority to name exactly the same frozen commit that the executor
selected before delegating to the raw adapter. This prevents a certification commit from
silently becoming the scientific contender merely because the harness branch advanced.

No workload generation, measurement, comparison, scoring, or winner selection occurs in
this layer.
"""

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.one.one_genesis_contender_raw_adapter import run as run_raw_adapter

BOUNDARY = ROOT / "benchmarks" / "one" / "genesis_one_candidate_boundary_v1.json"
CERTIFIED_STATUS = "CERTIFIED_FOR_GENESIS"


def _load_boundary() -> dict:
    try:
        payload = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Genesis ONE candidate-boundary authority is unreadable") from exc
    if payload.get("schema") != "cmpct-one-genesis-one-candidate-boundary-v1":
        raise RuntimeError("Genesis ONE candidate-boundary authority has wrong schema")
    return payload


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


def run() -> dict:
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("certified adapter requires explicit real-gate executor authorization")
    contender = os.environ.get("CMPCT_GENESIS_CONTENDER", "")
    if contender == "cmpct1":
        _assert_cmpct1_certification()
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
