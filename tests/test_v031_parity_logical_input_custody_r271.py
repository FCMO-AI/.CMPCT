"""Real CLI adversarial court: logical source bytes are a release parity invariant.

The size is a *necessary*, not sufficient, condition for comparing the same input.
The producer's immutable shared-tree custody remains the stronger content control.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parents[1] / "tools/check_performance_regression.py"
MISSING = object()


def _record(logical=1000, *, create=0.100):
    metric = {"bytes": 1000, "create_s_median": create, "extract_s_median": 0.070}
    row = {"library": {"cmpct": copy.deepcopy(metric)},
           "cli": {"cmpct": copy.deepcopy(metric)}}
    if logical is not MISSING:
        row["logical_bytes"] = logical
    return {"schema": "cmpct-zip-parity-v1",
            "corpora": {"structural_test": row}}


def _check(tmp_path, base, candidate):
    bp, cp = tmp_path / "base.json", tmp_path / "candidate.json"
    bp.write_text(json.dumps(base), encoding="utf-8")
    cp.write_text(json.dumps(candidate), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER), "--base", str(bp),
                           "--candidate", str(cp)],
                          capture_output=True, text=True, check=False)


def test_same_names_sizes_and_timings_with_different_input_lengths_is_red(tmp_path):
    # Old comparator returned PASS: it never read logical_bytes. Neither
    # archive size nor timing equality establishes equivalent input.
    r = _check(tmp_path, _record(1000), _record(1001))
    assert r.returncode == 1
    assert "Result: **FAIL**" in r.stdout
    assert "logical input bytes changed" in r.stdout


@pytest.mark.parametrize("side", ["base", "candidate"])
@pytest.mark.parametrize("invalid", [MISSING, None, True, False, -1, 1000.5, "1000", []])
def test_missing_or_invalid_input_length_fails_closed(tmp_path, side, invalid):
    b, c = _record(), _record()
    target = b if side == "base" else c
    if invalid is MISSING:
        target["corpora"]["structural_test"].pop("logical_bytes")
    else:
        target["corpora"]["structural_test"]["logical_bytes"] = invalid
    r = _check(tmp_path, b, c)
    assert r.returncode != 0
    assert "expected non-negative integral logical input bytes" in r.stderr
    assert "Result: **PASS**" not in r.stdout


@pytest.mark.parametrize("logical", [0, 1000, 2**53 + 1])
def test_equal_nonnegative_integral_input_lengths_preserve_green(tmp_path, logical):
    r = _check(tmp_path, _record(logical), _record(logical))
    assert r.returncode == 0
    assert "Result: **PASS**" in r.stdout


def test_real_seven_percent_seven_ms_timing_red_still_blocks(tmp_path):
    r = _check(tmp_path, _record(), _record(create=0.107))
    assert r.returncode == 1
    assert "create_s_median" in r.stdout


def test_one_archive_byte_still_blocks_even_with_equal_logical_input(tmp_path):
    b, c = _record(), _record()
    c["corpora"]["structural_test"]["library"]["cmpct"]["bytes"] += 1
    r = _check(tmp_path, b, c)
    assert r.returncode == 1
    assert "archive size" in r.stdout
