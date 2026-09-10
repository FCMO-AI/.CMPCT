from __future__ import annotations

"""Production-only 15-row raw adapter for the sealed Genesis executor.

The adapter never generates workloads and never compares contenders. The top-level
executor owns physical input generation/verification; this layer maps the frozen row
identities to those already-existing directories, chooses the contender-neutral selective
request, and delegates measurement to the five-sample workload orchestrator.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

# The executor deliberately launches this current-candidate orchestration script with cwd
# set to each contender checkout. Historical checkouts do not contain these ONE Genesis
# helpers, so bind imports to the script's own candidate source rather than ambient cwd.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.one.one_genesis_contender_workload_measurement import measure_workload
from benchmarks.one.one_genesis_selective_access_plan import select_primary_request

IDENTITY_MANIFEST = ROOT / "benchmarks" / "one" / "genesis_gate_workload_identity_v1.json"
CONTENDERS = ("cmpct1", "v0.29", "v0.30")


def _load_identities() -> list[dict[str, Any]]:
    payload = json.loads(IDENTITY_MANIFEST.read_text(encoding="utf-8"))
    rows = payload.get("workloads")
    if payload.get("schema") != "cmpct-one-genesis-gate-workload-identity-v1" or not isinstance(rows, list):
        raise RuntimeError("invalid frozen Genesis workload identity authority")
    keys = [(row.get("suite"), row.get("name")) for row in rows]
    if len(rows) != 15 or len(set(keys)) != 15:
        raise RuntimeError("Genesis raw adapter requires exactly 15 unique frozen workload identities")
    if sum(row.get("suite") == "neutral_hostile_v1" for row in rows) != 10:
        raise RuntimeError("Genesis raw adapter requires exactly 10 neutral-hostile rows")
    if sum(row.get("suite") == "resemblance_hostile_v1" for row in rows) != 5:
        raise RuntimeError("Genesis raw adapter requires exactly 5 resemblance-hostile rows")
    return rows


def _workload_path(work_root: Path, identity: dict[str, Any]) -> Path:
    suite = identity.get("suite")
    if suite == "neutral_hostile_v1":
        parent = work_root / "neutral"
    elif suite == "resemblance_hostile_v1":
        parent = work_root / "resemblance"
    else:
        raise RuntimeError(f"unknown frozen suite {suite!r}")
    path = parent / str(identity.get("name"))
    if not path.is_dir():
        raise RuntimeError(f"executor-owned workload directory missing: {path}")
    return path


def _git_head(checkout: Path) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()


def _production_context() -> tuple[str, str, Path, Path, Path]:
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("raw contender adapter requires explicit real-gate executor authorization")
    contender = os.environ.get("CMPCT_GENESIS_CONTENDER", "")
    source_sha = os.environ.get("CMPCT_GENESIS_SOURCE_SHA", "")
    work_root_raw = os.environ.get("CMPCT_GENESIS_WORK_ROOT", "")
    output_raw = os.environ.get("CMPCT_GENESIS_OUTPUT", "")
    if contender not in CONTENDERS:
        raise RuntimeError("raw contender adapter received unknown contender")
    if len(source_sha) != 40 or any(char not in "0123456789abcdef" for char in source_sha):
        raise RuntimeError("raw contender adapter requires a 40-hex sealed source SHA")
    if not work_root_raw or not output_raw:
        raise RuntimeError("raw contender adapter requires executor-owned work root and output path")
    checkout = Path.cwd().resolve()
    if _git_head(checkout) != source_sha:
        raise RuntimeError("raw contender adapter checkout HEAD differs from sealed source")
    work_root = Path(work_root_raw).resolve()
    output = Path(output_raw).resolve()
    if not work_root.is_dir():
        raise RuntimeError("executor-owned work root does not exist")
    return contender, source_sha, checkout, work_root, output


def _assemble_rows(
    *,
    contender: str,
    checkout: Path,
    work_root: Path,
    identities: list[dict[str, Any]],
    measure: Callable[..., dict[str, Any]] = measure_workload,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for identity in identities:
        workload = _workload_path(work_root, identity)
        request = select_primary_request(workload)
        result = measure(
            contender=contender,
            checkout=checkout,
            root=workload,
            member=request.relative_path if request.status == "selected" else None,
            transfer_fixture=False,
        )
        if result.get("schema") != "cmpct-one-genesis-workload-measurement-v1":
            raise RuntimeError(f"{identity['suite']}/{identity['name']}: workload measurement has wrong schema")
        if result.get("contender") != contender or result.get("production_eligible") is not True:
            raise RuntimeError(f"{identity['suite']}/{identity['name']}: workload measurement is not production-bound")
        measurement = result.get("measurement")
        if not isinstance(measurement, dict):
            raise RuntimeError(f"{identity['suite']}/{identity['name']}: missing measurement payload")
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
    return rows


def run() -> dict[str, Any]:
    contender, source_sha, checkout, work_root, output = _production_context()
    identities = _load_identities()
    rows = _assemble_rows(
        contender=contender,
        checkout=checkout,
        work_root=work_root,
        identities=identities,
    )
    payload = {
        "schema": "cmpct-one-genesis-contender-raw-v1",
        "claim_boundary": "raw measurements only; no comparison, scoring, aggregate rank, or winner selection",
        "contender": contender,
        "source_sha": source_sha,
        "synthetic": False,
        "production_eligible": True,
        "rows": rows,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


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
