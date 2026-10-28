#!/usr/bin/env python3
"""O218d: source-derived proof of the only changes to the O218 C predicate.

A bounded source-custody audit, not a substitute for compiled native semantic
testing. Prevents the abi3 research experiment silently drifting into a new
checker / permitting a broken or weaker control.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "research" / "o218_fastscan.c"
ABI3 = ROOT / "research" / "o218d_abi3_package" / "o218d_abi3_fastscan.c"
EXPECTED_ORIGINAL = "a54f15181d9dbe667b9e8c9d52e927b09c80152f"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()

def check() -> dict:
    old_bytes = ORIGINAL.read_bytes()
    assert git_blob(old_bytes) == EXPECTED_ORIGINAL, "historical scanner mutated"
    old = old_bytes.decode("utf-8")
    expected = (old.replace("#include <Python.h>",
                            "#define Py_LIMITED_API 0x030B0000\n#include <Python.h>")
                .replace("Research-only exact built-in list path",
                         "Research-only stable-ABI exact built-in list path")
                .replace("PyList_GET_SIZE(", "PyList_Size(")
                .replace("PyList_GET_ITEM(", "PyList_GetItem("))
    assert old.count("PyList_GET_SIZE(") == 3
    assert old.count("PyList_GET_ITEM(") == 2
    assert expected.encode("utf-8") == ABI3.read_bytes(), (
        "unapproved abi3 predicate source mutation")
    assert "Py_LIMITED_API=0x030B0000" in expected.replace(" ", "")
    assert "PyList_GET_SIZE(" not in expected
    assert "PyList_GET_ITEM(" not in expected
    assert "PyList_Size(" in expected and "PyList_GetItem(" in expected
    return {
        "decision": "ABI3_SOURCE_DERIVED_ONLY",
        "original_blob": git_blob(old_bytes),
        "abi3_blob": git_blob(ABI3.read_bytes()),
        "max_rewrite_scope": [
            "one Py_LIMITED_API 3.11 define",
            "three PyList_GET_SIZE->PyList_Size",
            "two PyList_GET_ITEM->PyList_GetItem",
            "one explanatory comment update",
        ],
    }

if __name__ == "__main__":
    import json
    print("O218D_SOURCE_CUSTODY=PASS", json.dumps(check(), sort_keys=True))
