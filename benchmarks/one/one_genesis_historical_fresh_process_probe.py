from __future__ import annotations

"""Synthetic transfer probe that meters frozen product operations in fresh processes.

This is pre-gate plumbing only. It uses the tiny independent transfer tree from the
historical adapter probe and never imports or generates the 15 Genesis workloads.
"""

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from benchmarks.one.one_genesis_fresh_process_meter import measure_command
from benchmarks.one.one_genesis_historical_adapter_probe import SURFACES, _tree_digest, _write_transfer_tree


def _meter_worker(argv: list[str], receipt: Path) -> dict[str, Any]:
    measurement = measure_command(argv, receipt_path=receipt)
    worker = measurement.get("worker_receipt")
    if not isinstance(worker, dict):
        raise RuntimeError("fresh historical worker did not publish a structured receipt")
    if worker.get("comparison_executed") is not False or worker.get("scoring_executed") is not False:
        raise RuntimeError("historical worker crossed the pre-gate claim boundary")
    return measurement


def probe(contender: str, checkout: Path, work_root: Path) -> dict[str, Any]:
    if contender not in SURFACES:
        raise RuntimeError(contender)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    source = work_root / "external-transfer-tree"
    archive = work_root / "archive.cmpct"
    extracted = work_root / "extracted"
    _write_transfer_tree(source)
    input_digest = _tree_digest(source)

    worker_module = "benchmarks.one.one_genesis_historical_operation_worker"

    build_receipt = work_root / "build-receipt.json"
    build = _meter_worker(
        [
            sys.executable,
            "-m",
            worker_module,
            "--contender",
            contender,
            "--checkout",
            str(checkout),
            "--operation",
            "build",
            "--source",
            str(source),
            "--archive",
            str(archive),
            "--receipt",
            str(build_receipt),
        ],
        build_receipt,
    )
    if build["worker_receipt"].get("input_tree_sha256") != input_digest:
        raise RuntimeError("fresh build worker observed the wrong external input")

    verify_receipt = work_root / "verify-receipt.json"
    verify = _meter_worker(
        [
            sys.executable,
            "-m",
            worker_module,
            "--contender",
            contender,
            "--checkout",
            str(checkout),
            "--operation",
            "verify",
            "--archive",
            str(archive),
            "--receipt",
            str(verify_receipt),
        ],
        verify_receipt,
    )

    extract_receipt = work_root / "extract-receipt.json"
    extract = _meter_worker(
        [
            sys.executable,
            "-m",
            worker_module,
            "--contender",
            contender,
            "--checkout",
            str(checkout),
            "--operation",
            "extract",
            "--archive",
            str(archive),
            "--output-tree",
            str(extracted),
            "--receipt",
            str(extract_receipt),
        ],
        extract_receipt,
    )
    if extract["worker_receipt"].get("output_tree_sha256") != input_digest:
        raise RuntimeError("fresh extract worker reconstruction differs from executor-owned input")
    if _tree_digest(source) != input_digest:
        raise RuntimeError("executor-owned input changed during fresh-process probe")

    return {
        "schema": "cmpct-one-genesis-historical-fresh-process-probe-v1",
        "claim_boundary": "synthetic transfer plumbing only; direct-child cold operation resources, no Genesis workload, comparison, scoring, or winner",
        "contender": contender,
        "source_sha": SURFACES[contender][0],
        "synthetic": True,
        "genesis_inputs_used": False,
        "input_tree_sha256": input_digest,
        "archive_bytes": archive.stat().st_size,
        "build": build,
        "verify": verify,
        "extract": extract,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contender", choices=sorted(SURFACES), required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.contender, args.checkout.resolve(), args.work_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "contender": result["contender"],
        "archive_bytes": result["archive_bytes"],
        "build_cpu_s": result["build"]["cpu_total_s"],
        "build_peak_rss_bytes": result["build"]["peak_rss_bytes"],
        "genesis_inputs_used": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
