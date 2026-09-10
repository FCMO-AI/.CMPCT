from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from benchmarks.one.one_genesis_fresh_process_meter import measure_command


def test_fresh_process_meter_charges_cpu_and_rss_and_reads_worker_receipt(tmp_path: Path):
    receipt = tmp_path / "receipt.json"
    command = [
        sys.executable,
        "benchmarks/one/one_genesis_fresh_process_meter.py",
        "--self-test-worker",
        "memory",
        "--receipt",
        str(receipt),
    ]
    result = measure_command(command, receipt_path=receipt)
    assert result["returncode"] == 0
    assert result["wall_s"] > 0
    assert result["cpu_total_s"] > 0
    assert result["peak_rss_bytes"] >= 16 * 1024 * 1024
    assert result["resource_scope"] == "direct-child-process"
    assert result["descendant_resource_scope"].startswith("unavailable")
    assert result["worker_receipt"]["mode"] == "memory"


def test_missing_worker_receipt_is_explicit_unavailable(tmp_path: Path):
    missing = tmp_path / "missing.json"
    result = measure_command([sys.executable, "-c", "pass"], receipt_path=missing)
    assert result["worker_receipt"]["status"] == "unavailable"


def test_failing_child_fails_closed_with_measurement():
    with pytest.raises(RuntimeError, match="metered command failed") as exc:
        measure_command([sys.executable, "-c", "raise SystemExit(7)"])
    payload = json.loads(str(exc.value))
    assert payload["measurement"]["returncode"] == 7
    assert payload["measurement"]["cpu_total_s"] >= 0


def test_empty_command_is_rejected():
    with pytest.raises(ValueError, match="non-empty command"):
        measure_command([])
