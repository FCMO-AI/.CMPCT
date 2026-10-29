"""Independent hostile controls for J24M01g full-suite JUnit positive custody.

The auditor is run as a subprocess with standard-library XML fixtures; this
test never imports the CMPCT archive implementation or changes its evaluator.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


AUDITOR = Path(__file__).resolve().parents[1] / "tools" / "j24m01g_junit_custody.py"
CLASSNAME = "tests.test_j24v01_sparse_verify_streamed"
NAME = "test_real_256m_sparse_verification_does_not_materialize_holes"
ROW = f'<testcase classname="{CLASSNAME}" name="{NAME}" time="0.01">{{child}}</testcase>'


@pytest.mark.parametrize(
    ("variant", "payload", "expect_pass"),
    [
        ("genuine_pass", ROW.format(child=""), True),
        ("missing", '<testcase classname="tests.other" name="different"/>', False),
        ("wrong_class", ROW.replace(CLASSNAME, "tests.unrelated"), False),
        ("wrong_namespace", ROW.replace(CLASSNAME, "decoy.test_j24v01_sparse_verify_streamed"), False),
        ("skipped", ROW.format(child="<skipped/>"), False),
        ("failure", ROW.format(child="<failure message='x'/>"), False),
        ("error", ROW.format(child="<error message='x'/>"), False),
        ("duplicated", ROW.format(child="") * 2, False),
        ("malformed", "<testcase", False),
        ("status_notrun", ROW.replace('time="0.01"', 'status="notrun" time="0.01"').format(child=""), False),
    ],
)
def test_real_junit_target_custody_rejects_false_green(
    tmp_path: Path, variant: str, payload: str, expect_pass: bool
) -> None:
    report = tmp_path / f"{variant}.xml"
    report.write_text(f"<testsuites><testsuite>{payload}</testsuite></testsuites>")
    process = subprocess.run(
        [sys.executable, str(AUDITOR), str(report)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if expect_pass:
        assert process.returncode == 0, (variant, process.stderr)
        assert "J24M01G_TARGET_EXECUTED_PASS" in process.stdout
        assert "GENERAL_SUITE_STATUS: NOT ASSERTED" in process.stdout
    else:
        assert process.returncode != 0, (variant, process.stdout)
        assert "J24M01G_TARGET_NOT_PROVEN" in process.stderr
