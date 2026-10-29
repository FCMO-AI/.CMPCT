#!/usr/bin/env python3
"""Fail-closed J24M01g custody check for a genuine executed sparse resource test.

This audits pytest's JUnit result identity. It does not import CMPCT, adjudicate
other suite failures, lower the 128-MiB ceiling, or redefine a product PASS.
"""
from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET

TEST_CLASS = "tests.test_j24v01_sparse_verify_streamed"
TEST_NAME = "test_real_256m_sparse_verification_does_not_materialize_holes"
BAD_CHILDREN = {"failure", "error", "skipped"}


def verify_target_pass(xml_path: Path) -> str:
    """Require exactly one unequivocally successful target testcase in real XML."""
    root = ET.parse(xml_path).getroot()
    if root.tag not in {"testsuites", "testsuite"}:
        raise ValueError(f"unexpected JUnit document root: {root.tag!r}")
    # A same-basename decoy in another module is not evidence the genuine test ran.
    matches = [
        c for c in root.iter("testcase")
        if c.get("name") == TEST_NAME
        and c.get("classname", "") == TEST_CLASS
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one {TEST_CLASS}::{TEST_NAME}, found {len(matches)}"
        )
    failed = [c.tag for c in matches[0] if c.tag in BAD_CHILDREN]
    if failed:
        raise ValueError(f"target was not an executed PASS: {failed}")
    if matches[0].get("status", "").lower() in {"skipped", "failed", "error", "notrun"}:
        raise ValueError(f"target status is not PASS: {matches[0].get('status')!r}")
    return f"{matches[0].get('classname')}::{TEST_NAME}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: j24m01g_junit_custody.py FULL-SUITE.XML", file=sys.stderr)
        return 2
    try:
        result = verify_target_pass(Path(argv[1]))
    except (ET.ParseError, OSError, ValueError) as exc:
        print(f"J24M01G_TARGET_NOT_PROVEN: {exc}", file=sys.stderr)
        return 1
    print(f"J24M01G_TARGET_EXECUTED_PASS: {result}")
    print("J24M01G_GENERAL_SUITE_STATUS: NOT ASSERTED; inspect real pytest exit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
