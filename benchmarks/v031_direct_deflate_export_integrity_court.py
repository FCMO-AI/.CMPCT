#!/usr/bin/env python3
"""Exact-source science: native direct-Deflate ZIP export versus independently checked ZIP."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

from cmpct.reader import CMPCT
from cmpct.codec import BHDR, BMAGIC, CODEC_DEFLATE

FIXTURE = Path(__file__).resolve().parents[1] / "tests/conformance/v24-direct-codecs.json"
CRC_FIELD_OFFSET = struct.calcsize("<4sBBHQQI")


def outcome(source: bytes, member: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-deflate-export-court-") as temp:
        path = Path(temp) / "source.cmpct"
        target = Path(temp) / "export.zip"
        path.write_bytes(source)
        out: dict = {"source_sha256": hashlib.sha256(source).hexdigest()}
        with CMPCT(path) as archive:
            try:
                content = archive.read(member)
                out["cmpct_read"] = "ACCEPT"
                out["cmpct_read_sha256"] = hashlib.sha256(content).hexdigest()
            except Exception as exc:
                out["cmpct_read"] = "REJECT"
                out["cmpct_read_exception"] = type(exc).__name__
            try:
                archive.export_zip(target)
                out["export"] = "ACCEPT"
            except Exception as exc:
                out["export"] = "REJECT"
                out["export_exception"] = type(exc).__name__
        if target.exists():
            out["zip_bytes"] = target.stat().st_size
            out["zip_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            try:
                with zipfile.ZipFile(target) as z:
                    decompressed = z.read(member)
                out["independent_zip"] = "ACCEPT"
                out["independent_zip_sha256"] = hashlib.sha256(decompressed).hexdigest()
            except Exception as exc:
                out["independent_zip"] = "REJECT"
                out["independent_zip_exception"] = type(exc).__name__
        else:
            out["independent_zip"] = "ABSENT"
        return out


def run() -> dict:
    fixture = json.loads(FIXTURE.read_text())
    row = next(v for v in fixture["vectors"] if v["codec"] == CODEC_DEFLATE)
    source = base64.b64decode(row["archive_base64"], validate=True)
    assert hashlib.sha256(source).hexdigest() == row["archive_sha256"], "fixed vector custody"
    assert len(source) == row["archive_bytes"], "fixed vector length"
    pos = source.index(BMAGIC)
    magic, codec, flags, reserved, usize, csize, msize, expected_crc, expected_sha = BHDR.unpack_from(source, pos)
    assert magic == BMAGIC and codec == CODEC_DEFLATE
    payload = pos + BHDR.size + msize
    assert csize > 4 and payload + csize <= len(source)
    baseline = outcome(source, row["name"])
    assert baseline["cmpct_read"] == baseline["independent_zip"] == baseline["export"] == "ACCEPT"
    assert baseline["cmpct_read_sha256"] == baseline["independent_zip_sha256"] == row["logical_sha256"]

    # The physical checksum changes, but the same independently authenticated index/footer remains.
    crc_mutation = bytearray(source)
    struct.pack_into("<I", crc_mutation, pos + CRC_FIELD_OFFSET, expected_crc ^ 1)
    crc = outcome(bytes(crc_mutation), row["name"])
    # The retained RFC-1951 payload changes at exactly one position.
    payload_mutation = bytearray(source)
    payload_mutation[payload + csize // 2] ^= 1
    altered = outcome(bytes(payload_mutation), row["name"])

    cases = {"clean": baseline, "corrupt_header_crc": crc, "corrupt_deflate_payload": altered}
    bypass_cases = [name for name in ("corrupt_header_crc", "corrupt_deflate_payload")
                    if cases[name]["cmpct_read"] == "REJECT"
                    and cases[name]["export"] == "ACCEPT"
                    and cases[name]["independent_zip"] == "REJECT"]
    result = {
        "schema": "cmpct-v031-deflate-export-corruption-court-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_reader_blob": subprocess.check_output(["git", "hash-object", "src/cmpct/reader.py"], text=True).strip(),
        "fixed_vector": row["name"],
        "fixed_vector_archive_sha256": row["archive_sha256"],
        "logical_member_sha256": row["logical_sha256"],
        "record_crc_field_offset": pos + CRC_FIELD_OFFSET,
        "record_payload_offset": payload,
        "record_compressed_bytes": csize,
        "cases": cases,
        "bypass_cases": bypass_cases,
        "decision": ("BOTH_CORRUPTIONS_EXPORTED_UNVERIFIED" if len(bypass_cases) == 2
                     else "NARROWED_ONE_BYPASS" if bypass_cases else "PREDICTION_FALSIFIED"),
        "claim_scope": "research: fixed independent r24 direct Deflate; not a release benchmark or proposed fix",
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return result


if __name__ == "__main__":
    run()
