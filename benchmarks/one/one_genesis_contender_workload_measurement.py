from __future__ import annotations

"""Five-sample raw measurement orchestrator for one executor-owned workload.

This module deliberately operates below the 15-workload Genesis executor. It never
selects/generates Genesis workloads, compares contenders, or scores a winner. Before the
gate it may be exercised only with ``--transfer-fixture`` on synthetic/transfer trees.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
from typing import Any


REPETITIONS = 5
CONTENDERS = ("cmpct1", "v0.29", "v0.30")
FROZEN = {
    "v0.29": "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d",
    "v0.30": "f4b158a55a08b9b18b50e4e4abe4b9251048c772",
}
SCHEMA = "cmpct-one-genesis-workload-measurement-v1"
HERE = Path(__file__).resolve().parent
CMPCT1_WORKER = HERE / "one_genesis_cmpct1_product_worker.py"
HISTORICAL_WORKER = HERE / "one_genesis_historical_product_worker.py"


def _git_head(checkout: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()


def _authorize(contender: str, checkout: Path, transfer_fixture: bool) -> dict[str, Any]:
    head = _git_head(checkout)
    if transfer_fixture:
        return {
            "transfer_fixture": True,
            "production_authorized": False,
            "observed_source_sha": head,
        }
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("production workload measurement requires executor authorization")
    source = os.environ.get("CMPCT_GENESIS_SOURCE_SHA", "")
    if source != head:
        raise RuntimeError("production source SHA is not bound to contender checkout HEAD")
    if contender in FROZEN and source != FROZEN[contender]:
        raise RuntimeError(f"{contender} source differs from frozen Genesis authority")
    return {
        "transfer_fixture": False,
        "production_authorized": True,
        "observed_source_sha": head,
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("worker output must be a JSON object")
    return payload


def _run_worker(
    *,
    contender: str,
    mode: str,
    checkout: Path,
    root: Path,
    archive: Path,
    output: Path,
    member: str | None,
    transfer_fixture: bool,
) -> dict[str, Any]:
    if contender == "cmpct1":
        command = [
            sys.executable,
            str(CMPCT1_WORKER),
            "--mode",
            mode,
            "--root",
            str(root),
            "--archive",
            str(archive),
            "--output",
            str(output),
        ]
    else:
        command = [
            sys.executable,
            str(HISTORICAL_WORKER),
            "--contender",
            "v029" if contender == "v0.29" else "v030",
            "--mode",
            mode,
            "--checkout",
            str(checkout),
            "--root",
            str(root),
            "--archive",
            str(archive),
            "--output",
            str(output),
        ]
    if member is not None:
        command += ["--member", member]
    if transfer_fixture:
        command.append("--transfer-fixture")

    env = os.environ.copy()
    # Never allow ambient production authorization to turn a transfer falsifier into
    # production evidence. In real mode authorization is inherited from the sealed executor.
    if transfer_fixture:
        env.pop("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", None)
        env.pop("CMPCT_GENESIS_SOURCE_SHA", None)
    subprocess.run(command, cwd=checkout, env=env, check=True)
    return _load_json(output)


def _median(samples: list[dict[str, Any]], key: str) -> float | int:
    values: list[float | int] = []
    for index, row in enumerate(samples):
        value = row.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise RuntimeError(f"sample {index} has invalid non-negative metric {key}")
        values.append(value)
    result = statistics.median(values)
    if all(isinstance(value, int) for value in values):
        return int(result)
    return float(result)


def _timing_family(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if len(samples) != REPETITIONS:
        raise RuntimeError(f"expected exactly {REPETITIONS} samples, got {len(samples)}")
    return {
        "measured": True,
        "repetitions": REPETITIONS,
        "statistic": "median",
        "process_boundary": "fresh-process",
        "cpu_s": _median(samples, "cpu_s"),
        "wall_s": _median(samples, "wall_s"),
        "peak_rss_bytes": _median(samples, "peak_rss_bytes"),
        "samples": samples,
    }


def _assert_phase(samples: list[dict[str, Any]], phase: str) -> None:
    if len(samples) != REPETITIONS:
        raise RuntimeError(f"expected exactly {REPETITIONS} {phase} samples")
    for index, row in enumerate(samples):
        if row.get("phase") != phase:
            raise RuntimeError(f"sample {index} has wrong phase {row.get('phase')!r}")


def _stable_build(samples: list[dict[str, Any]], contender: str) -> tuple[int, str]:
    _assert_phase(samples, "creation")
    sizes = {row.get("stored_bytes") for row in samples}
    if len(sizes) != 1 or not all(isinstance(value, int) and value >= 0 for value in sizes):
        raise RuntimeError("deterministic creation produced inconsistent stored bytes")
    digest_key = "wire_sha256" if contender == "cmpct1" else "archive_sha256"
    digests = {row.get(digest_key) for row in samples}
    if len(digests) != 1:
        raise RuntimeError("deterministic creation produced inconsistent persistent wire")
    digest = next(iter(digests))
    if not isinstance(digest, str) or len(digest) != 64:
        raise RuntimeError("creation sample missing persistent artifact digest")
    return int(next(iter(sizes))), digest


def _assert_whole_exact(samples: list[dict[str, Any]]) -> None:
    _assert_phase(samples, "whole_read")
    for index, row in enumerate(samples):
        if row.get("exact") is not True:
            raise RuntimeError(f"whole-read sample {index} is not exact")


def _assert_selective_exact(samples: list[dict[str, Any]], member: str) -> None:
    _assert_phase(samples, "selective_access")
    for index, row in enumerate(samples):
        if row.get("exact") is not True or row.get("member") != member:
            raise RuntimeError(f"selective sample {index} is not exact for requested member")


def _selective_family(samples: list[dict[str, Any]], member: str) -> dict[str, Any]:
    _assert_selective_exact(samples, member)
    requested = {row.get("requested_bytes") for row in samples}
    if len(requested) != 1 or not all(isinstance(value, int) and value >= 0 for value in requested):
        raise RuntimeError("selective requested bytes changed across repetitions")
    return {
        **_timing_family(samples),
        "member": member,
        "requested_bytes": int(next(iter(requested))),
        # Product-specific access counters are intentionally retained in verbatim samples.
        # A later frozen normalization layer may promote only counters whose semantics are proven.
        "touched_bytes": {"status": "unavailable"},
        "decoded_bytes": {"status": "unavailable"},
        "authentication_bytes": {"status": "unavailable"},
        "reconstruction_work": {"status": "unavailable"},
        "temporary_bytes": {"status": "unavailable"},
    }


def measure_workload(
    *,
    contender: str,
    checkout: Path,
    root: Path,
    member: str | None,
    transfer_fixture: bool,
) -> dict[str, Any]:
    if contender not in CONTENDERS:
        raise RuntimeError(f"unknown contender {contender!r}")
    checkout = checkout.resolve()
    root = root.resolve()
    if not checkout.is_dir() or not root.is_dir():
        raise RuntimeError("checkout and workload root must be directories")
    authorization = _authorize(contender, checkout, transfer_fixture)

    with tempfile.TemporaryDirectory(prefix="cmpct-genesis-workload-measurement-") as td:
        scratch = Path(td)
        build_samples: list[dict[str, Any]] = []
        archives: list[Path] = []
        for index in range(REPETITIONS):
            archive = scratch / f"build-{index}.cmpct"
            output = scratch / f"build-{index}.json"
            build_samples.append(
                _run_worker(
                    contender=contender,
                    mode="build",
                    checkout=checkout,
                    root=root,
                    archive=archive,
                    output=output,
                    member=None,
                    transfer_fixture=transfer_fixture,
                )
            )
            archives.append(archive)

        stored_bytes, artifact_sha = _stable_build(build_samples, contender)
        canonical_archive = archives[0]

        whole_samples = [
            _run_worker(
                contender=contender,
                mode="whole",
                checkout=checkout,
                root=root,
                archive=canonical_archive,
                output=scratch / f"whole-{index}.json",
                member=None,
                transfer_fixture=transfer_fixture,
            )
            for index in range(REPETITIONS)
        ]
        _assert_whole_exact(whole_samples)

        if contender == "v0.29":
            selective: Any = {
                "status": "unavailable",
                "reason": "no proven exact frozen v0.29 selective member surface",
            }
        elif member is None:
            selective = {
                "status": "unavailable",
                "reason": "no deterministic selective member supplied by authority layer",
            }
        else:
            selective_samples = [
                _run_worker(
                    contender=contender,
                    mode="selective",
                    checkout=checkout,
                    root=root,
                    archive=canonical_archive,
                    output=scratch / f"selective-{index}.json",
                    member=member,
                    transfer_fixture=transfer_fixture,
                )
                for index in range(REPETITIONS)
            ]
            selective = _selective_family(selective_samples, member)

    measurement = {
        "stored_bytes": stored_bytes,
        "creation": _timing_family(build_samples),
        "whole_read": _timing_family(whole_samples),
        "selective_access": selective,
        # Do not fabricate static capability claims merely to satisfy a schema. Exactness
        # and integrity evidence remains preserved in phase samples until a separate frozen
        # capability authority maps all four semantic fields.
        "semantics": {"status": "unavailable"},
        "reader_burden": {"status": "unavailable"},
    }
    return {
        "schema": SCHEMA,
        "contender": contender,
        "source_sha": authorization["observed_source_sha"],
        "synthetic": transfer_fixture,
        "production_eligible": not transfer_fixture,
        "artifact_sha256": artifact_sha,
        "repetitions": REPETITIONS,
        "statistic": "median",
        "measurement": measurement,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contender", choices=CONTENDERS, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--member")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transfer-fixture", action="store_true")
    args = parser.parse_args()
    result = measure_workload(
        contender=args.contender,
        checkout=args.checkout,
        root=args.root,
        member=args.member,
        transfer_fixture=args.transfer_fixture,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "contender": result["contender"],
        "synthetic": result["synthetic"],
        "stored_bytes": result["measurement"]["stored_bytes"],
        "scoring_executed": result["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
