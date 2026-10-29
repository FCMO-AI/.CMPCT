#!/usr/bin/env python3
"""Detached J24I34b physical referee: row SHA agrees with bytes, CMA4 disagrees.

Uses the independent J24I30 parser, which imports no CMPCT modules.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "j24i30"))
from audit_symlink_wire import parse  # noqa: E402

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", type=Path, required=True)
    args = ap.parse_args()
    directory = args.case_dir
    control = parse(directory / "original.cmpct")
    hostile = parse(directory / "dual-commit-corrupt.cmpct")
    original_gen = json.loads((directory / "dual-commit-conflict.json").read_text())
    assert control["physical_record_valid"] is True
    assert control["logical_row_sha"] is None
    assert hostile["physical_record_valid"] is False
    assert hostile["logical_row_matches_decoded"] is True
    assert hostile["physical_sha256"] != control["physical_sha256"]
    assert hostile["decoded_sha256"] == original_gen["new_payload_sha256"]
    assert control["decoded_sha256"] == original_gen["original_payload_sha256"]
    assert hostile["index_sha256"] != control["index_sha256"]
    assert hostile["whole_sha256"] == original_gen["archive_sha256"]
    result = {
        "schema": "cmpct-j24i34b-detached-two-commit-referee-v1",
        "science_only": True,
        "conclusion": "VALID hostile r24 index, INVALID CMA4 payload, row matches altered bytes",
        "original": control,
        "adversarial": hostile,
    }
    (directory / "dual-commit-detached-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
