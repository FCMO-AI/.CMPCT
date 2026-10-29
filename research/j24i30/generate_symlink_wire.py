#!/usr/bin/env python3
"""J24I30: real r24 symlink wire, independently observed Python strong verifier.

This research instrument reuses J24I27's exact immutable-index converter. It does
not modify the original wire bytes or any product/format/conformance evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.codec import BHDR, HDR, K_SYMLINK
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "j24i27"))
from test_present_row_sha import source_parts, with_row_hash  # noqa: E402

def sha256(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dest = args.output.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="j24i30-source-") as td:
        source = Path(td) / "tree"
        source.mkdir()
        literal = "relative-symlink-target.txt"
        os.symlink(literal, source / "link")
        original_path = Path(td) / "authentic.cmpct"
        Builder(source, workers=1, reproducible=True).build(original_path)
        original = original_path.read_bytes()

    idx, physical, raw = source_parts(original)
    require(len(idx["files"]) == 1, "not exactly one source member")
    require(idx["files"][0][1] == K_SYMLINK, "not a real symlink row")
    require(raw == literal.encode(), "symlink raw target differs from stored literal")
    require(idx["files"][0][0] == "link", "unexpected path")
    correct = hashlib.sha256(raw).digest()
    wrong = hashlib.sha256(b"J24I30 contradictory optional symlink-row digest").digest()
    require(wrong != correct, "expected distinct digest")
    examples = {
        "original": original,
        "present-correct": with_row_hash(original, correct),
        "present-empty": with_row_hash(original, b""),
        "present-foreign": with_row_hash(original, wrong),
    }
    for key in ("present-correct", "present-empty", "present-foreign"):
        _ix, copied, recovered = source_parts(examples[key])
        require(copied == physical and recovered == raw, key + " rewrote physical record")

    # Separate attack: alter a single physical payload byte without touching
    # either authenticated index. The corruption is intentionally uncorrected.
    physical_wrong = bytearray(original)
    _m, _v, _flags, cs, _us, _span, _idxsha = HDR.unpack_from(original)
    off, _size, _csize, _codec, meta_len = idx["blobs"][0]
    payload_offset = HDR.size + cs + off + BHDR.size + meta_len
    require(original[payload_offset] == raw[0], "expected direct RAW symlink payload")
    physical_wrong[payload_offset] ^= 1
    examples["physical-wrong"] = bytes(physical_wrong)
    require(sum(a != b for a,b in zip(original, physical_wrong)) == 1, "not a one-byte mutation")

    records = []
    for name, archive in examples.items():
        file = dest / (name + ".cmpct")
        file.write_bytes(archive)
        expected_pass = name not in ("present-foreign", "physical-wrong")
        try:
            with CMPCT(file) as ar:
                verified = ar.verify()
            python_ok = True
            error = None
        except Exception as ex:
            python_ok = False
            verified = None
            error = type(ex).__name__ + ": " + str(ex)
        require(python_ok == expected_pass, f"Python unexpected {name}: {error}")
        if python_ok:
            require(verified == 1, f"Python {name} verified {verified} entries")
        records.append({
            "case": name,
            "archive_sha256": sha256(archive),
            "physical_unchanged": name != "physical-wrong",
            "source_r24_symlink": True,
            "python_strong_verify_accepted": python_ok,
            "python_verified_count": verified,
            "python_error": error,
            "expected_native_verified_regular_entries": 0,
        })
    receipt = {
        "schema": "cmpct-j24i30-native-symlink-verify-v1",
        "classification": "research-only; native acceptance of contradiction is a negative result",
        "source_archive_sha256": sha256(original),
        "source_physical_sha256": sha256(physical),
        "source_symlink_target_hex": raw.hex(),
        "case_records": records,
    }
    (dest / "python-observations.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
