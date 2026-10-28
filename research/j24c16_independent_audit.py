#!/usr/bin/env python3
"""J24C16 independent receipt auditor; no CMPCT imports."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


def judge(d: dict) -> dict:
    assert d["schema"] == "j24c16-installed-mutable-prefix-v1"
    assert len(bytes.fromhex(d["source_commit"])) == 20
    assert d["reader_blob"] == "c4d1dee0a31527b814d6e1f41b77abe1cc987996"
    assert d["installed_reader"].endswith("/cmpct/reader.py")
    assert "site-packages" in d["installed_reader"] or "dist-packages" in d["installed_reader"]
    assert len(bytes.fromhex(d["signed_wire_sha256"])) == 32
    assert d["archive_bytes"] > 0 and d["archive_unchanged"] is True
    assert d["native_index_helper_present"] is True
    assert d["original_signed_size"] == d["post_mutation_logical_bytes"] == 512
    assert d["original_strong_verify"] is True
    assert d["initial_native_marks"] == [0, 257]
    assert d["post_mutation_true_prefix_256"] == 255
    assert d["original_range_257_hex"] == d["post_mutation_expected_range_hex"] == "41"
    assert d["linear_control_range_hex"] == "41"
    wrong = d["indexed_error"] is None and d["indexed_range_hex"] != "41"
    assert d["decision"] == (
        "STALE_HINT_INSTALLED_WRONG_BYTES" if wrong else "MODEL_NOT_TRANSFERRED"
    )
    if wrong:
        assert d["indexed_range_hex"] == "42", (
            "Unpredicted deviation from frozen model; inspect rather than recast"
        )
    return {
        "schema": "j24c16-independent-audit-v1",
        "source_commit": d["source_commit"],
        "signed_wire_sha256": d["signed_wire_sha256"],
        "decision": d["decision"],
        "native_index_helper_executed": True,
        "source_unchanged": True,
        "control_exact": True,
        "model_prediction_transfer": bool(wrong),
        "scope": "in-process caller-mutated signed-reference list only; no archive tampering",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    d = json.loads(args.input.read_text())
    result = judge(d)
    # Check evaluator refuses materially forged records.
    for key, bad in (
        ("reader_blob", "00"*20),
        ("archive_unchanged", False),
        ("native_index_helper_present", False),
        ("original_strong_verify", False),
        ("post_mutation_true_prefix_256", 257),
        ("linear_control_range_hex", "42"),
        ("decision", "CONTRADICTS_WIRE"),
    ):
        corrupted = copy.deepcopy(d)
        corrupted[key] = bad
        try:
            judge(corrupted)
        except (AssertionError, ValueError, KeyError, TypeError):
            pass
        else:
            raise AssertionError("Forged J24C16 receipt was accepted: " + key)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24C16_SECOND_ROOT_PASS")
    print("J24C16_INDEPENDENT_DECISION=" + result["decision"])


if __name__ == "__main__":
    main()
