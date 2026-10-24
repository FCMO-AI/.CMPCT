"""Adversarial end-to-end policy validation against the actual release comparator CLI."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parents[1] / "tools/check_performance_regression.py"


def _run(tmp_path, *args, create=0.107, archive_bytes=1000):
    base_metric = {"bytes": 1000, "create_s_median": 0.100, "extract_s_median": 0.070}
    cand_metric = {"bytes": archive_bytes, "create_s_median": create, "extract_s_median": 0.070}
    base = {"schema": "cmpct-zip-parity-v1", "corpora": {"hostile_policy": {
        "library": {"cmpct": base_metric}, "cli": {"cmpct": base_metric}}}}
    candidate = {"schema": "cmpct-zip-parity-v1", "corpora": {"hostile_policy": {
        "library": {"cmpct": cand_metric}, "cli": {"cmpct": cand_metric}}}}
    pa, pb = tmp_path / "base.json", tmp_path / "candidate.json"
    pa.write_text(json.dumps(base), encoding="utf-8")
    pb.write_text(json.dumps(candidate), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER), "--base", str(pa),
                           "--candidate", str(pb), *args],
                          capture_output=True, text=True, check=False)


@pytest.mark.parametrize("flag", [
    "--timing-relative", "--timing-absolute-ms",
    "--max-time-regression", "--max-size-regression",
])
@pytest.mark.parametrize("invalid", ["nan", "NaN", "inf", "-inf"])
def test_nonfinite_policy_arg_rejected(tmp_path, flag, invalid):
    result = _run(tmp_path, flag, invalid)
    assert result.returncode == 2
    assert "must be finite" in result.stderr
    assert "Result: **PASS**" not in result.stdout


def test_original_plus_seven_percent_and_seven_ms_remains_red(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "Result: **FAIL**" in result.stdout


@pytest.mark.parametrize("args", [
    ("--timing-relative", "0.05"),
    ("--timing-absolute-ms", "3"),
    ("--max-time-regression", "0.04"),
    ("--max-size-regression", "0.01"),
])
def test_valid_policy_inputs_preserve_a_real_red(tmp_path, args):
    result = _run(tmp_path, *args)
    assert result.returncode == 1
    assert "Result: **FAIL**" in result.stdout


def test_equal_timing_is_still_green(tmp_path):
    result = _run(tmp_path, create=0.100)
    assert result.returncode == 0
    assert "Result: **PASS**" in result.stdout


@pytest.mark.parametrize("args", [
    ("--timing-relative", "0.051"),
    ("--timing-absolute-ms", "3.01"),
    ("--max-time-regression", "0.051"),
    ("--max-size-regression", "-0.01"),
])
def test_finite_policy_that_loosens_or_violates_bounds_is_rejected(tmp_path, args):
    assert _run(tmp_path, *args).returncode == 2


def test_legacy_size_alias_does_not_waive_one_byte(tmp_path):
    result = _run(tmp_path, "--max-size-regression", "0.01",
                  create=0.100, archive_bytes=1001)
    assert result.returncode == 1
    assert "archive size" in result.stdout
