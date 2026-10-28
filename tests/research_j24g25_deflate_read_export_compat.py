#!/usr/bin/env python3
"""J24G25: prospectively frozen, installed-Reader r24 Deflate acceptance court.

This is an independent test child of PR #284, not a fix. The question is
whether the *same candidate Reader* accepts a physical Deflate stream via read()
but refuses export_zip() solely because RFC1951 trailing bytes are present.
Prereg: docs/v031-research/2026-10-28-j24g25-deflate-read-export-compat-prereg.md
"""
from __future__ import annotations

import binascii
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib

import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_DEFLATE, FMAGIC, FTR, HDR, K_FILE,
    MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT

MEMBER = "member.bin"
CANDIDATE_READER_GIT_BLOB = "b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb"


def hexhash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def deflate(data: bytes) -> bytes:
    obj = zlib.compressobj(9, zlib.DEFLATED, -15)
    return obj.compress(data) + obj.flush()


def create_r24(path: Path, raw: bytes, encoded: bytes, *, corrupt_crc=False):
    """Construct a genuine r24 file using the physical grammar, not Builder or Reader."""
    crc = (binascii.crc32(raw) & 0xffffffff) ^ int(corrupt_crc)
    record = BHDR.pack(
        BMAGIC, CODEC_DEFLATE, 0, 0, len(raw), len(encoded), 0, crc, sha(raw)
    ) + encoded
    index = {
        "v": VERSION,
        "files": [[MEMBER, K_FILE, 0o644, 0, len(raw), None, [S_BLOB, 0]]],
        "blobs": [[0, len(raw), len(encoded), CODEC_DEFLATE, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    clear = msgpack.packb(index, use_bin_type=True)
    packed = zc(clear, 12)
    wire = (
        HDR.pack(MAGIC, VERSION, 0, len(packed), len(clear), len(record), sha(clear))
        + packed + record + packed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed), len(clear), 0, sha(clear))
    )
    path.write_bytes(wire)
    return wire


def independent_zip(comp: bytes, raw: bytes) -> bytes:
    """Make a standalone ZIP from raw RFC1951 bytes; independent of CMPCT.export_zip."""
    name = MEMBER.encode("utf-8")
    crc = binascii.crc32(raw) & 0xffffffff
    lfh = struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0x800, 8, 0, 0,
                      crc, len(comp), len(raw), len(name), 0)
    body = lfh + name + comp
    central = struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0x800,
                          8, 0, 0, crc, len(comp), len(raw), len(name),
                          0, 0, 0, 0, 0, 0) + name
    tail = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, 1, 1,
                       len(central), len(body), 0)
    return body + central + tail


def try_operation(fn):
    try:
        result = fn()
    except Exception as exc:
        return {"status": "REJECT", "exception": type(exc).__name__,
                "message": str(exc)}
    return {"status": "ACCEPT", "return_type": type(result).__name__}


def run() -> dict:
    expected_reader = subprocess.check_output(
        ["git", "hash-object", "src/cmpct/reader.py"], text=True
    ).strip()
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    assert expected_reader == CANDIDATE_READER_GIT_BLOB, (
        "This court MUST use the original frozen PR284 Reader, not a newer author edit",
        expected_reader,
    )
    raw = hashlib.sha256(b"J24G25 exact payload").digest() * 1024
    deflated = deflate(raw)
    cases = [
        ("clean", b"", False),
        ("one_trailing_byte", b"\x00", False),
        ("two_trailing_bytes", b"\x00\x01", False),
        ("trailing_complete_deflate_stream", deflated, False),
        ("corrupted_crc", b"", True),
    ]
    destination = Path(os.environ.get("J24G25_ARTIFACT_DIR") or tempfile.mkdtemp(
        prefix="j24g25-artifact-"))
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    report = {
        "schema": "cmpct-j24g25-physical-deflate-read-export-parity-v1",
        "source_sha": source_sha,
        "installed_reader_blob": expected_reader,
        "parent_pr": 284,
        "parent_sha": "2e493d2d941f9c144c0c5050b41c88dc7c6e57dd",
        "member_sha256": hexhash(raw),
        "member_bytes": len(raw),
        "cases": results,
        "release_credit": 0,
    }
    try:
        for name, trailer, bad_crc in cases:
            comp = deflated + trailer
            source = destination / (name + ".cmpct")
            physical = create_r24(source, raw, comp, corrupt_crc=bad_crc)
            zip_bytes = independent_zip(comp, raw)
            # The independent RFC1951 decoder and standard ZIP consumer are the
            # simpler controls; they do not call the CMPCT Reader or ZIP writer.
            decoder = zlib.decompressobj(-15)
            assert decoder.decompress(comp) + decoder.flush() == raw
            assert decoder.eof
            assert decoder.unused_data == trailer
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                assert z.read(MEMBER) == raw
                assert z.testzip() is None
            control = destination / (name + ".independent.zip")
            control.write_bytes(zip_bytes)
            out = destination / (name + ".export.zip")
            sentinel = b"existing-output-must-survive-rejection:" + name.encode()
            out.write_bytes(sentinel)
            with CMPCT(source) as reader:
                actual_read = try_operation(lambda: (
                    None if reader.read(MEMBER) == raw
                    else (_ for _ in ()).throw(AssertionError("wrong member bytes"))))
                actual_verify = try_operation(reader.verify)
                actual_export = try_operation(lambda: reader.export_zip(out))
            final_bytes = out.read_bytes()
            observed = {
                "case": name,
                "r24_sha256": hexhash(physical),
                "r24_bytes": len(physical),
                "deflate_size": len(comp),
                "trailing_bytes": len(trailer),
                "physical_crc_corrupt": bad_crc,
                "independent_zip_sha256": hexhash(zip_bytes),
                "independent_zip_bytes": len(zip_bytes),
                "read": actual_read,
                "verify": actual_verify,
                "export": actual_export,
                "export_size": len(final_bytes),
                "export_sha256": hexhash(final_bytes),
                "existing_destination_preserved": final_bytes == sentinel,
            }
            if actual_export["status"] == "ACCEPT":
                with zipfile.ZipFile(io.BytesIO(final_bytes)) as z:
                    assert z.read(MEMBER) == raw
                    assert z.testzip() is None
            results.append(observed)
        (destination / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
        for case in results:
            is_crc = case["physical_crc_corrupt"]
            suffix = case["trailing_bytes"] != 0
            expected_read = "REJECT" if is_crc else "ACCEPT"
            assert case["read"]["status"] == expected_read, case
            assert case["verify"]["status"] == expected_read, case
            expected_export = "REJECT" if is_crc or suffix else "ACCEPT"
            assert case["export"]["status"] == expected_export, case
            if expected_export == "REJECT":
                assert case["existing_destination_preserved"], case
            else:
                assert not case["existing_destination_preserved"], case
        report["decision"] = "PR284_REJECTS_RELEASED_VALID_TRAILING_DEFLATE"
        (destination / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return report
    finally:
        (destination / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    run()
