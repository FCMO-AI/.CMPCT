#!/usr/bin/env python3
"""J24B10 prospective signed-S_SPARSE quota falsifier, science only.

The output file is intentionally created only inside a runner-owned temporary
experiment directory. Never point this instrument at an existing user tree.
"""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import msgpack
from cmpct.codec import (
    MAGIC, VERSION, HDR, BMAGIC, BHDR, FMAGIC, FTR,
    K_FILE, S_SPARSE, CODEC_RAW, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

L = 16_384
B = 8_192
GOOD_OFF = 4_096
GOOD_LEN = B
BAD_OFF = L - 1
BAD_LEN = 1
REL = "sparse.bin"


def deterministic_blob() -> bytes:
    return b"".join(hashlib.sha256(f"J24B10:{i}".encode()).digest() for i in range(B // 32))


def create_wire(index: dict, physical: bytes) -> bytes:
    index_raw = msgpack.packb(index, use_bin_type=True)
    enc = zc(index_raw, 12)
    digest = sha(index_raw)
    return (HDR.pack(MAGIC, VERSION, 0, len(enc), len(index_raw), len(physical), digest)
            + enc + physical + enc
            + FTR.pack(FMAGIC, 0, 1, 0, 0, len(enc), len(index_raw), 0, digest))


def expect_refusal(call, fragment: str, case: str) -> str:
    try:
        call()
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        if fragment.lower() not in msg.lower():
            raise AssertionError(f"{case}: unexpected refusal {msg}") from exc
        return msg
    raise AssertionError(f"{case}: unexpectedly accepted")


def execute(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    payload = deterministic_blob()
    original = b"\0" * GOOD_OFF + payload + b"\0" * (L - GOOD_OFF - B)
    assert len(original) == L and len(payload) == B
    physical = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, B, B, 0,
                         __import__('binascii').crc32(payload) & 0xffffffff, sha(payload)) + payload
    positive_index = {
        "v": VERSION,
        "files": [[REL, K_FILE, 0o644, 0, L, sha(original),
                   [S_SPARSE, [[GOOD_OFF, GOOD_LEN, [0]]]]]],
        "blobs": [[0, B, B, CODEC_RAW, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {},
    }
    altered_index = msgpack.unpackb(msgpack.packb(positive_index, use_bin_type=True), raw=False)
    altered_index["files"][0][6][1][0][:2] = [BAD_OFF, BAD_LEN]
    good_path = root / "source-original.cmpct"
    bad_path = root / "source-mutant.cmpct"
    good_path.write_bytes(create_wire(positive_index, physical))
    bad_path.write_bytes(create_wire(altered_index, physical))

    # Independent strict validator is a strong control. Its rejection does NOT
    # mean the ordinary CMPCT reader/extractor calls this guard.
    preflight_archive(good_path)
    strict_rejection = expect_refusal(
        lambda: preflight_archive(bad_path), "extent", "signed invalid sparse extent preflight")

    good_rejected = root / "original-too-low"
    good_accepted = root / "original-accepted"
    bad_rejected = root / "mutant-too-low"
    bad_accepted = root / "mutant-accepted"
    with CMPCT(good_path) as reader:
        assert reader.read(REL) == original
        assert reader.verify() == 1
        original_refusal = expect_refusal(
            lambda: reader.extractall(good_rejected, metadata=False, max_bytes=L-1),
            "above limit", "original undercap")
        reader.extractall(good_accepted, metadata=False, max_bytes=L)
    actual_good = (good_accepted / REL).read_bytes()
    assert actual_good == original, (len(actual_good), len(original))

    with CMPCT(bad_path) as reader:
        malformed_read = expect_refusal(
            lambda: reader.read(REL), "file integrity failure", "malformed signed sparse full read")
        malformed_verify = expect_refusal(
            lambda: reader.verify(), "file integrity failure", "malformed signed sparse verify")
        bad_refusal = expect_refusal(
            lambda: reader.extractall(bad_rejected, metadata=False, max_bytes=L-1),
            "above limit", "mutant undercap")
        # This is the falsification target; no read() before extraction is used
        # as an admission policy. The expected flaw is in this exact API path.
        reader.extractall(bad_accepted, metadata=False, max_bytes=L)
    actual_bad = (bad_accepted / REL).read_bytes()
    expected_bad = b"\0" * BAD_OFF + payload
    assert actual_bad == expected_bad
    assert len(actual_bad) == BAD_OFF + B == 24_575
    assert len(actual_bad) - L == B - 1 == 8_191

    installed = Path(inspect.getfile(CMPCT)).resolve()
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    result = {
        "schema": "cmpct-j24b10-court-v1",
        "decision": "CONFIRMED_SPARSE_SIGNED_EXTENT_QUOTA_OVERRUN",
        "source_head": source_sha,
        "installed_reader_path": str(installed),
        "installed_reader_sha256": hashlib.sha256(installed.read_bytes()).hexdigest(),
        "platform": __import__('platform').platform(),
        "python": __import__('sys').version,
        "original_archive_sha256": hashlib.sha256(good_path.read_bytes()).hexdigest(),
        "mutant_archive_sha256": hashlib.sha256(bad_path.read_bytes()).hexdigest(),
        "physical_sha256": hashlib.sha256(physical).hexdigest(),
        "original_logical_sha256": hashlib.sha256(original).hexdigest(),
        "original_extracted_sha256": hashlib.sha256(actual_good).hexdigest(),
        "mutant_extracted_sha256": hashlib.sha256(actual_bad).hexdigest(),
        "declared_logical_size": L,
        "physical_payload_size": B,
        "original_extent": [GOOD_OFF, GOOD_LEN, [0]],
        "mutant_extent": [BAD_OFF, BAD_LEN, [0]],
        "limit_enforced": L,
        "original_extracted_bytes": len(actual_good),
        "mutant_extracted_bytes": len(actual_bad),
        "excess_logical_bytes": len(actual_bad) - L,
        "strict_mutant_refusal": strict_rejection,
        "original_undercap_refusal": original_refusal,
        "mutant_undercap_refusal": bad_refusal,
        "mutant_full_read_refusal": malformed_read,
        "mutant_verify_refusal": malformed_verify,
    }
    (root / "court-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    assert not out.exists(), "refuse to overwrite an existing destination/evidence tree"
    result = execute(out)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
