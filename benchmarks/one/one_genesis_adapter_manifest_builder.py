from __future__ import annotations

"""Build the runtime adapter manifest for the sealed Genesis executor.

This tool performs only source/path binding. It never generates workloads, authorizes a
real gate, executes contenders, computes comparisons, or selects a winner.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
RAW_ADAPTER_REL = Path("benchmarks/one/one_genesis_contender_raw_adapter.py")


def _sha(value: str, label: str) -> str:
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise RuntimeError(f"{label} must be a 40-hex commit SHA")
    return value


def _head(checkout: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()


def _bind_checkout(checkout: Path, expected: str, label: str) -> Path:
    checkout = checkout.resolve()
    if not checkout.is_dir():
        raise RuntimeError(f"{label} checkout is not a directory: {checkout}")
    observed = _head(checkout)
    if observed != expected:
        raise RuntimeError(f"{label} checkout HEAD {observed} != sealed source {expected}")
    return checkout


def _candidate_adapter(candidate_checkout: Path) -> Path:
    candidate_root = candidate_checkout.resolve()
    script = (candidate_root / RAW_ADAPTER_REL).resolve()
    try:
        script.relative_to(candidate_root)
    except ValueError as exc:
        raise RuntimeError("raw adapter resolves outside sealed candidate checkout") from exc
    if not script.is_file():
        raise RuntimeError(f"raw adapter script missing from sealed candidate checkout: {script}")
    return script


def build_manifest(
    *,
    candidate_sha: str,
    candidate_checkout: Path,
    v029_checkout: Path,
    v030_checkout: Path,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    candidate_sha = _sha(candidate_sha, "candidate SHA")
    _sha(V029_SHA, "frozen v0.29 SHA")
    _sha(V030_SHA, "frozen v0.30 SHA")
    if not isinstance(python_executable, str) or not python_executable:
        raise RuntimeError("python executable must be a non-empty argv element")

    candidate = _bind_checkout(candidate_checkout, candidate_sha, "CMPCT1")
    v029 = _bind_checkout(v029_checkout, V029_SHA, "v0.29")
    v030 = _bind_checkout(v030_checkout, V030_SHA, "v0.30")
    script = _candidate_adapter(candidate)
    command = [python_executable, str(script)]
    adapters = {
        "cmpct1": {"checkout": str(candidate), "command": list(command)},
        "v0.29": {"checkout": str(v029), "command": list(command)},
        "v0.30": {"checkout": str(v030), "command": list(command)},
    }
    if set(adapters) != {"cmpct1", "v0.29", "v0.30"}:
        raise RuntimeError("adapter manifest must contain exactly the three Genesis contenders")
    return {
        "schema": "cmpct-one-genesis-adapters-v1",
        "claim_boundary": "source/path binding only; no authorization, contender execution, workload generation, comparison, scoring, or winner selection",
        "candidate_sha": candidate_sha,
        "frozen_comparators": {"v0.29": V029_SHA, "v0.30": V030_SHA},
        "adapters": adapters,
        "execution_authorized": False,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--candidate-checkout", type=Path, required=True)
    parser.add_argument("--v029-checkout", type=Path, required=True)
    parser.add_argument("--v030-checkout", type=Path, required=True)
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_manifest(
        candidate_sha=args.candidate_sha,
        candidate_checkout=args.candidate_checkout,
        v029_checkout=args.v029_checkout,
        v030_checkout=args.v030_checkout,
        python_executable=args.python_executable,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": payload["schema"],
        "candidate_sha": payload["candidate_sha"],
        "adapters": sorted(payload["adapters"]),
        "execution_authorized": payload["execution_authorized"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
