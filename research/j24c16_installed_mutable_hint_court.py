#!/usr/bin/env python3
"""J24C16 installed-Reader exact signed-source vs mutated in-memory hint falsifier.

Research ONLY: never treat a caller-mutated index object as authenticated input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_o215_fixed_chunk_admission import _make_archive
import cmpct.reader as reader_module
import cmpct._chunk_admission as native
from cmpct.reader import CMPCT


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    opt = p.parse_args()
    assert callable(native._scan_refs_index), "native positive-only proof is required"
    installed = Path(reader_module.__file__).resolve()
    assert "site-packages" in installed.parts or "dist-packages" in installed.parts, installed
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert len(source_sha) == 40
    source_blob = subprocess.check_output(
        ["git", "hash-object", "src/cmpct/reader.py"], text=True
    ).strip()
    assert source_blob == "c4d1dee0a31527b814d6e1f41b77abe1cc987996", source_blob
    owners = (b"A", b"BB", b"")
    original_refs = [1] + [0] * 255 + [2] + [0] * 255
    assert len(original_refs) == 512
    signed_payload = b"".join(owners[j] for j in original_refs)
    assert len(signed_payload) == 512
    wire = _make_archive(original_refs, signed_payload, blobs=owners)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c16-") as tmp:
        archive = Path(tmp) / "signed-valid.cmpct"
        archive.write_bytes(wire)
        signed_wire_sha = sha(wire)
        assert sha(archive.read_bytes()) == signed_wire_sha
        with CMPCT(archive) as reader:
            initial_proof = reader._chunk_range_marks.get("fixed.bin")
            assert initial_proof == (0, 257), initial_proof
            assert reader.verify() == 1
            assert reader.read("fixed.bin") == signed_payload
            assert reader.read_range("fixed.bin", 257, 1) == b"A"
            live_refs = reader.by["fixed.bin"][6][1]
            assert type(live_refs) is list and len(live_refs) == 512
            live_refs[0], live_refs[256] = live_refs[256], live_refs[0]
            # Even after deliberate caller mutation, the total logical size
            # stays 512. A stale offset is the only tested source of deviation.
            current_payload = b"".join(owners[j] for j in live_refs)
            assert len(current_payload) == reader.by["fixed.bin"][4] == 512
            expected = current_payload[257:258]
            assert expected == b"A"
            assert sum(len(owners[j]) for j in live_refs[:256]) == 255
            try:
                indexed = reader.read_range("fixed.bin", 257, 1)
                indexed_error = None
            except Exception as exc:
                indexed = None
                indexed_error = f"{type(exc).__name__}: {exc}"
            # Original unindexed Reader path is the stronger simple control:
            # same mutated list and same physical archive, only hint removed.
            marks = reader._chunk_range_marks.pop("fixed.bin")
            try:
                linear = reader.read_range("fixed.bin", 257, 1)
            finally:
                reader._chunk_range_marks["fixed.bin"] = marks
            assert linear == expected
            assert sha(archive.read_bytes()) == signed_wire_sha
            result = {
                "schema": "j24c16-installed-mutable-prefix-v1",
                "source_commit": source_sha,
                "reader_blob": source_blob,
                "installed_reader": str(installed),
                "signed_wire_sha256": signed_wire_sha,
                "archive_bytes": len(wire),
                "archive_unchanged": True,
                "native_index_helper_present": True,
                "original_signed_size": len(signed_payload),
                "original_strong_verify": True,
                "original_range_257_hex": signed_payload[257:258].hex(),
                "initial_native_marks": list(initial_proof),
                "post_mutation_logical_bytes": len(current_payload),
                "post_mutation_true_prefix_256": 255,
                "post_mutation_expected_range_hex": expected.hex(),
                "indexed_range_hex": indexed.hex() if indexed is not None else None,
                "indexed_error": indexed_error,
                "linear_control_range_hex": linear.hex(),
                "decision": (
                    "STALE_HINT_INSTALLED_WRONG_BYTES"
                    if indexed is not None and indexed != expected
                    else "MODEL_NOT_TRANSFERRED"
                ),
                "limits": [
                    "In-process caller mutation of public Python index objects only",
                    "Original archive is authenticated and unchanged on disk",
                    "Not an on-disk malformed input admission bypass",
                    "Ubuntu CPython3.11 installed optional ABI3 only",
                ],
            }
        opt.output.parent.mkdir(parents=True, exist_ok=True)
        opt.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("J24C16_DECISION=" + result["decision"])
        print("J24C16_ORIGINAL_ARCHIVE_SHA256=" + signed_wire_sha)
        print("J24C16_INSTALLED_READER=" + str(installed))
        print("J24C16_CONTROL expected=" + repr(expected) +
              " indexed=" + repr(indexed) + " linear=" + repr(linear))


if __name__ == "__main__":
    main()
