"""J24E01: reject ambiguous JSON benchmark evidence, not only malformed numbers.

Raw JSON text is essential: creating fixtures via Python dicts would silently
eliminate duplicate keys before the actual release comparator sees them.
Preregistration: docs/v031-research/2026-10-27-j24e01-parity-json-duplicate-prereg.md
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_performance_regression.py"
BASE_ROW = ('{"logical_bytes":1000,'
            '"library":{"cmpct":{"bytes":1000,"create_s_median":0.100,"extract_s_median":0.070}},'
            '"cli":{"cmpct":{"bytes":1000,"create_s_median":0.100,"extract_s_median":0.070}}}')
RED_ROW = BASE_ROW.replace('"create_s_median":0.100', '"create_s_median":0.107')
DOC_PREFIX = '{"schema":"cmpct-zip-parity-v1","corpora":'
BASE = DOC_PREFIX + '{"demo":' + BASE_ROW + '}}'
RED = DOC_PREFIX + '{"demo":' + RED_ROW + '}}'
DUPLICATE_TIMING = RED.replace(
    '"create_s_median":0.107',
    '"create_s_median":0.107,"create_s_median":0.100',
)
DUPLICATE_CORPORA = (DOC_PREFIX + '{"demo":' + RED_ROW + '},'
                     '"corpora":{"demo":' + BASE_ROW + '}}')
DUPLICATE_SCHEMA = RED.replace(
    '"schema":"cmpct-zip-parity-v1"',
    '"schema":"invalid","schema":"cmpct-zip-parity-v1"',
)
DUPLICATE_ARCHIVE_BYTES = BASE.replace(
    '"bytes":1000', '"bytes":1100,"bytes":1000'
)
DUPLICATE_LOGICAL_LENGTH = BASE.replace(
    '"logical_bytes":1000', '"logical_bytes":1001,"logical_bytes":1000'
)


def run_checker(tmp_path: Path, candidate: str, base: str = BASE):
    b = tmp_path / "base.json"
    c = tmp_path / "candidate.json"
    b.write_text(base, encoding="utf-8")
    c.write_text(candidate, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECKER), "--base", str(b), "--candidate", str(c)],
        capture_output=True, text=True, check=False,
    )


@pytest.mark.parametrize("ambiguous", [
    DUPLICATE_TIMING,
    DUPLICATE_CORPORA,
    DUPLICATE_SCHEMA,
    DUPLICATE_ARCHIVE_BYTES,
    DUPLICATE_LOGICAL_LENGTH,
])
def test_any_duplicate_mapping_key_fails_closed(tmp_path: Path, ambiguous: str):
    # All three encoded objects are syntactically valid JSON. A last-wins
    # decoder would silently erase the original provenance and report PASS.
    result = run_checker(tmp_path, ambiguous)
    assert result.returncode != 0, result.stdout
    assert "duplicate JSON object key" in result.stderr, (result.stdout, result.stderr)
    assert "Result: **PASS**" not in result.stdout


@pytest.mark.parametrize("ambiguous", [
    DUPLICATE_TIMING,
    DUPLICATE_ARCHIVE_BYTES,
    DUPLICATE_LOGICAL_LENGTH,
])
def test_duplicate_in_base_report_also_fails_closed(tmp_path: Path, ambiguous: str):
    result = run_checker(tmp_path, BASE, base=ambiguous)
    assert result.returncode != 0, result.stdout
    assert "duplicate JSON object key" in result.stderr
    assert "Result: **PASS**" not in result.stdout


def test_unique_key_aa_preserves_valid_pass(tmp_path: Path):
    result = run_checker(tmp_path, BASE)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Result: **PASS**" in result.stdout


def test_unique_key_seven_percent_seven_ms_remains_a_release_fail(tmp_path: Path):
    result = run_checker(tmp_path, RED)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "Result: **FAIL**" in result.stdout
    assert "create_s_median" in result.stdout
