#!/usr/bin/env python3
"""J24P04 audit falsifier: corrupt receipts, require strict independent rejection.

Does not modify or invoke CMPCT Reader, kernel test, comparators or gates.
Pure negative controls for the JSON receipt checker.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main():
    src = Path(sys.argv[1])
    target = Path(__file__).with_name("j24p04_receipt_audit.py")
    original = json.loads(src.read_text(encoding="utf8"))
    cases = original["cases"]
    attacked = next(i for i, c in enumerate(cases) if c["hostile"])
    untouched = next(i for i, c in enumerate(cases) if not c["hostile"])

    cases_to_test = {}
    x = copy.deepcopy(original)
    x["cases"][attacked]["final_sha"] = x["cases"][attacked]["expected_logical_sha"]
    cases_to_test["spoof_attacked_final_digest"] = json.dumps(x)

    x = copy.deepcopy(original)
    x["cases"][attacked]["final_is_original_verified_inode"] = True
    cases_to_test["mislabel_foreign_inode"] = json.dumps(x)

    x = copy.deepcopy(original)
    x["cases"][attacked]["publication"]["actor"]["uid"] += 1
    cases_to_test["mislabel_actor_credential"] = json.dumps(x)

    x = copy.deepcopy(original)
    x["cases"][untouched]["publication"]["linked_sha"] = "0" * 64
    cases_to_test["spoof_link_digest"] = json.dumps(x)

    x = copy.deepcopy(original)
    x["cases"][1] = copy.deepcopy(x["cases"][0])
    cases_to_test["duplicate_scenario"] = json.dumps(x)

    text = src.read_text(encoding="utf8")
    marker = '"schema": "j24p04-postlink-namespace-v1"'
    assert text.count(marker) == 1
    cases_to_test["duplicate_json_key"] = text.replace(marker, marker + ', "schema": "j24p04-postlink-namespace-v1"', 1)

    altered, n = re.subn(r'("uid"\s*:\s*)[0-9]+', r'\g<1>NaN', text, count=1)
    assert n == 1
    cases_to_test["nonfinite_json_literal"] = altered

    reports = {}
    with tempfile.TemporaryDirectory(prefix="j24p04-mutants-") as td:
        for label, mutated in cases_to_test.items():
            path = Path(td) / f"{label}.json"
            path.write_text(mutated, encoding="utf8")
            proc = subprocess.run([sys.executable, str(target), str(path)],
                                  capture_output=True, text=True, timeout=15)
            if proc.returncode == 0:
                raise AssertionError(f"independent auditor INCORRECTLY ACCEPTED {label}")
            reports[label] = {"rejected": True, "returncode": proc.returncode,
                              "reason_last_line": (proc.stderr or proc.stdout).strip().splitlines()[-1][:240]}
            print("J24P04_AUDIT_MUTANT=" + json.dumps({"name": label, "rejected": True}), flush=True)
    assert len(reports) == 7
    result = {"status": "PASS", "mutants_rejected": len(reports), "mutants": reports}
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print("J24P04_AUDIT_MUTANT_DECISION=7_OF_7_REJECTED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
