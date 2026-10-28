#!/usr/bin/env python3
"""J24G24: authentic installed CMPCT direct-Deflate ZIP export physical-integrity court.

Candidate-only: a source-exact historical fast-path control is used on the
same valid archive, while physical CRC corruption must be rejected by export.
Preregistration: docs/v031-research/2026-10-28-j24g24-deflate-export-verified-copy-prereg.md
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import shutil
import struct
import tempfile
import time
import types
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import BHDR, CODEC_DEFLATE, S_BLOB, K_FILE, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete


MEMBER = "a_payload.bin"
VIRTUAL = "z_nested.zip"
CRC_FIELD_OFFSET = struct.calcsize("<4sBBHQQI")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def released_fast_deflate_stream(self, row):
    # Source-exact released method main@80c358f8, deliberately used ONLY on the
    # uncorrupted same-input control. This is not the repair or a fixture oracle.
    storage=row[6]
    if row[1] not in (K_FILE,K_SYMLINK) or not storage or storage[0]!=S_BLOB:return None
    idx=storage[1];off,us,cs,codec,ml=self.blobs[idx]
    if codec!=CODEC_DEFLATE:return None
    pos=self.record_base+off;m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos)
    p=pos+BHDR.size+rml
    return self.mm[p:p+rcs],rcrc,rus


def record_failure(fn):
    start = time.perf_counter_ns()
    try:
        fn()
    except Exception as exc:
        return {"result": "REJECT", "exception": type(exc).__name__,
                "message": str(exc), "wall_ns": time.perf_counter_ns() - start}
    return {"result": "ACCEPT", "wall_ns": time.perf_counter_ns() - start}


def zip_check(path: Path, want: bytes) -> dict:
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if names != [MEMBER]:
                return {"result": "WRONG_NAMES", "names": names}
            info = z.getinfo(MEMBER)
            try:
                data = z.read(MEMBER)
                status = "PASS" if data == want else "WRONG_BYTES"
                return {"result": status, "size": len(data), "sha256": digest(data),
                        "record_crc32": info.CRC}
            except Exception as exc:
                return {"result": "REJECT", "exception": type(exc).__name__,
                        "message": str(exc), "record_crc32": info.CRC}
    except Exception as exc:
        return {"result": "REJECT", "exception": type(exc).__name__,
                "message": str(exc)}


def verify_archive(path: Path, want: bytes, zip_path: Path) -> dict:
    with CMPCT(path) as archive:
        assert sorted(archive.by) == [MEMBER]
        row = archive.by[MEMBER]
        assert row[6][0] == S_BLOB
        idx = row[6][1]
        assert archive.blobs[idx][3] == CODEC_DEFLATE, "not a real direct Deflate owner"
        payload_pos = archive.record_base + archive.blobs[idx][0]
        header = BHDR.unpack_from(archive.mm, payload_pos)
        assert header[1] == CODEC_DEFLATE
        checks = {
            "read": record_failure(lambda: (
                (_ for _ in ()).throw(AssertionError("wrong logical bytes"))
                if archive.read(MEMBER) != want else None)),
            "verify": record_failure(archive.verify),
            "export_zip": record_failure(lambda: archive.export_zip(zip_path)),
            "physical_crc32": header[7],
            "physical_sha256": bytes(header[8]).hex(),
            "blob_record_offset": payload_pos,
            "compressed_size": header[5],
            "logical_size": header[4],
        }
    if zip_path.exists():
        checks["output_zip_size"] = zip_path.stat().st_size
        checks["output_zip_sha256"] = digest(zip_path.read_bytes())
        checks["zip_consumer"] = zip_check(zip_path, want)
    else:
        checks["zip_consumer"] = {"result": "NOT_EMITTED"}
    return checks


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g24-") as tmp:
        root = Path(tmp)
        tree = root / "source"
        tree.mkdir()
        # Reproducible non-fixture-specific high-entropy bytes ensure Deflate
        # stream size exceeds the current reuse floor without special casing.
        raw = b"".join(hashlib.sha256(i.to_bytes(8, "little")).digest()
                       for i in range(4096))
        (tree / MEMBER).write_bytes(raw)
        with zipfile.ZipFile(tree / VIRTUAL, "w",
                             compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as nested:
            nested.writestr(MEMBER, raw)
        archive_path = root / "first_party.cmpct"
        Builder(tree, workers=1, reproducible=True).build(archive_path)
        with CMPCT(archive_path) as archive:
            assert MEMBER in archive.by and VIRTUAL in archive.by
            row = archive.by[MEMBER]
            assert row[6][0] == S_BLOB
            idx = row[6][1]
            assert archive.blobs[idx][3] == CODEC_DEFLATE, (
                "Builder did not choose the first-party exact Deflate reuse path")
            assert archive.read(MEMBER) == raw
        # Public Writer append_delete removes the ZIP recipe's logical name,
        # leaving one direct Deflate regular file and its authenticated provenance.
        append_delete(archive_path, VIRTUAL)
        valid = archive_path.read_bytes()
        valid_export = root / "valid.zip"
        reference = verify_archive(archive_path, raw, valid_export)
        assert reference["read"]["result"] == "ACCEPT"
        assert reference["verify"]["result"] == "ACCEPT"
        assert reference["export_zip"]["result"] == "ACCEPT"
        assert reference["zip_consumer"]["result"] == "PASS"
        assert reference["physical_crc32"] == (binascii.crc32(raw) & 0xffffffff)

        # Physical frame CRC32 (header only) is deliberately damaged; the
        # index and footer are not changed, and remain SHA-authenticated.
        off = reference["blob_record_offset"] + CRC_FIELD_OFFSET
        tampered = bytearray(valid)
        tampered[off] ^= 1
        changed_positions = [p for p, (a, b) in enumerate(zip(valid, tampered))
                             if a != b]
        assert changed_positions == [off], changed_positions
        damaged_path = root / "crc_bit_flipped.cmpct"
        damaged_path.write_bytes(tampered)
        damaged_export = root / "damaged.zip"
        damaged = verify_archive(damaged_path, raw, damaged_export)
        assert damaged["physical_crc32"] == (reference["physical_crc32"] ^ 1)
        assert damaged["read"]["result"] == "REJECT"
        assert damaged["verify"]["result"] == "REJECT"

        # The prospective hypothesis: physical integrity is skipped only by
        # the direct-Deflate export shortcut, not by the released ordinary read.
        # A positive outcome here is a product NEGATIVE requiring a new fix.
        assert damaged["export_zip"]["result"] == "REJECT", damaged
        # J24G24 narrows publication to exception-aware refusal; the current
        # export writer opens output before validating, and atomic replacement
        # of an existing destination is still separate productization debt.
        assert damaged["zip_consumer"]["result"] != "PASS", damaged

        # The historical and candidate ZIPs are compared byte-for-byte on
        # the SAME physical source and SAME host. POSIX-vs-Win32 Builder mode
        # metadata can differ, so one Linux ZIP hash is not a Windows oracle.
        published_export = root / "historical_valid.zip"
        with CMPCT(archive_path) as old_reader:
            old_reader._direct_deflate_stream = types.MethodType(
                released_fast_deflate_stream, old_reader)
            old_reader.export_zip(published_export)
        good_zip = valid_export.read_bytes()
        assert good_zip == published_export.read_bytes(), (
            "candidate changed valid ZIP bytes vs source-exact historical fast endpoint")
        bad_zip = damaged_export.read_bytes() if damaged_export.exists() else b""
        zip_diff = []
        report = {
            "court": "J24G24",
            "source_release": "v0.30.0-r24",
            "question": "Does direct-Deflate export reject source physical CRC corruption?",
            "scientific_decision": "CANDIDATE_REJECTS_CORRUPT_DEFLATE_EXPORT",
            "source_archive_sha256": digest(valid),
            "mutated_archive_sha256": digest(bytes(tampered)),
            "mutation_absolute_byte_offset": off,
            "modified_source_byte_count": len(changed_positions),
            "candidate_failed_export_bytes": len(bad_zip),
            "raw_member_sha256": digest(raw),
            "raw_member_bytes": len(raw),
            "candidate_valid_zip_sha256": digest(good_zip),
            "historical_valid_zip_sha256": digest(published_export.read_bytes()),
            "same_host_historical_candidate_byte_identity": True,
            "baseline": reference,
            "crc_mutation": damaged,
            "product_fix": True,
            "release_credit": 0,
        }
        print(json.dumps(report, sort_keys=True, indent=2))
        if os.environ.get("J24G24_ARTIFACT_DIR"):
            dest = Path(os.environ["J24G24_ARTIFACT_DIR"])
            dest.mkdir(parents=True, exist_ok=True)
            for p in (archive_path, damaged_path, valid_export, damaged_export, published_export):
                shutil.copyfile(p, dest / p.name)
            (dest / "report.json").write_text(
                json.dumps(report, sort_keys=True, indent=2) + "\n")
        return report


if __name__ == "__main__":
    run()
