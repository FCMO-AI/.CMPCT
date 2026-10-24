"""R272: compatibility alias must never weaken an independently tighter timing request.

Preregistered on PR #306 before this file and implementation existed.
Run the authentic public comparator CLI against valid, equal-input fixture
records; no benchmark or policy thresholds are modified by this court.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

COMPARATOR = Path(__file__).resolve().parents[1] / "tools/check_performance_regression.py"


def _compare(tmp_path: Path, *flags: str, candidate_create: float = 0.104):
    base_metric = {"bytes": 1000, "create_s_median": 0.100, "extract_s_median": 0.070}
    cand_metric = {"bytes": 1000, "create_s_median": candidate_create, "extract_s_median": 0.070}
    base = {"schema": "cmpct-zip-parity-v1", "corpora": {
        "same_input": {"logical_bytes": 1000, "library": {"cmpct": base_metric},
                       "cli": {"cmpct": base_metric}}}}
    candidate = {"schema": "cmpct-zip-parity-v1", "corpora": {
        "same_input": {"logical_bytes": 1000, "library": {"cmpct": cand_metric},
                       "cli": {"cmpct": cand_metric}}}}
    base_path, candidate_path = tmp_path / "base.json", tmp_path / "candidate.json"
    base_path.write_text(json.dumps(base), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return subprocess.run([
        sys.executable, str(COMPARATOR), "--base", str(base_path),
        "--candidate", str(candidate_path), *flags
    ], capture_output=True, text=True, check=False)


@pytest.mark.parametrize("flags", [
    ("--timing-relative=0.03", "--max-time-regression=0.05"),
    ("--max-time-regression=0.05", "--timing-relative=0.03"),
    ("--timing-relative=0.01", "--max-time-regression=0.04"),
    ("--timing-relative=0.05", "--max-time-regression=0.03"),
])
def test_both_flags_apply_tighter_relative_constraint_regardless_of_order(tmp_path, flags):
    # +4% and +4ms is a confirmed regression whenever either
    # individually requested relative bound is <4%; old source passed
    # the first two cases by overriding 3% with the looser legacy 5%.
    result = _compare(tmp_path, *flags)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "Result: **FAIL**" in result.stdout
    assert "create_s_median" in result.stdout


@pytest.mark.parametrize("flags", [
    (),
    ("--timing-relative=0.05",),
    ("--max-time-regression=0.05",),
    ("--timing-relative=0.05", "--max-time-regression=0.05"),
])
def test_normative_five_percent_envelope_stays_unmodified(tmp_path, flags):
    result = _compare(tmp_path, *flags)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Result: **PASS**" in result.stdout


def test_legacy_stricter_alias_without_explicit_flag_still_blocks(tmp_path):
    result = _compare(tmp_path, "--max-time-regression=0.03")
    assert result.returncode == 1
    assert "Result: **FAIL**" in result.stdout


def test_zero_byte_tolerance_remains_independent(tmp_path):
    # Existing tests verify one-byte growth. With equal archive sizes,
    # an exact equal-timing control also remains eligible under both flags.
    result = _compare(tmp_path, "--timing-relative=0.01",
                      "--max-time-regression=0.03", candidate_create=0.100)
    assert result.returncode == 0, (result.stdout, result.stderr)
