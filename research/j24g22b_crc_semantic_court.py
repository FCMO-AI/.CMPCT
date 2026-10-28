#!/usr/bin/env python3
"""J24G22b: source-exact independent CRC-only BHDR semantic falsifier (research only)."""
from __future__ import annotations

import binascii
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main(folder: Path):
    from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, S_BLOB
    from cmpct.reader import CMPCT

    clean = folder / "original.cmpct"
    original = clean.read_bytes()
    with CMPCT(clean) as reader:
        row = reader.by["direct.bin"]
        assert row[6][0] == S_BLOB
        idx = row[6][1]
        off, us, cs, codec, ml = reader.blobs[idx]
        assert codec == CODEC_RAW
        header_start = reader.record_base + off
        m, c, flags, reserved, rus, rcs, rml, original_crc, original_sha = BHDR.unpack_from(reader.mm, header_start)
        assert m == BMAGIC and c == CODEC_RAW and rus == us == row[4] and rcs == cs and rml == ml
        payload_start = header_start + BHDR.size + rml
        raw = bytes(reader.mm[payload_start:payload_start+rcs])
        assert (binascii.crc32(raw)&0xffffffff) == original_crc
        assert hashlib.sha256(raw).digest() == original_sha
        assert reader.read("direct.bin") == raw

    # CRC32 starts at BHDR offset 28: magic[4], codec[1], flags[1], reserved[2],
    # uncompressed[8], compressed[8], metadata_len[4].
    crc_offset = header_start + 28
    mutant = bytearray(original)
    mutant[crc_offset] ^= 1
    changed = folder / "crc-field-corrupt.cmpct"
    changed.write_bytes(mutant)
    assert bytes(mutant) != original
    assert original[:crc_offset] == mutant[:crc_offset]
    assert original[crc_offset+1:] == mutant[crc_offset+1:]

    with CMPCT(changed) as reader:
        assert reader.by["direct.bin"][4] == len(raw)
        assert reader.file_sha256("direct.bin") == hashlib.sha256(raw).digest()
        assert reader.read_range("direct.bin", 0, len(raw)) == raw
        try:
            reader.verify()
        except IOError as exc:
            verify_error = type(exc).__name__ + ": " + str(exc)
        else:
            raise AssertionError("real verified Reader accepted invalid CRC header")

    observations = {}
    for mode in ("eager", "spool", "premature"):
        cmd = [sys.executable, str(Path(__file__).with_name("j24g22_verified_stdout_court.py")),
               "--worker", str(changed), "direct.bin", mode]
        run = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=90)
        observations[mode] = json.loads(run.stdout)

    assert observations["eager"]["error"] is not None
    assert observations["eager"]["emitted_bytes"] == 0
    assert observations["spool"]["error"] is None
    assert observations["spool"]["emitted_bytes"] == len(raw)
    assert observations["spool"]["emitted_sha256"] == hashlib.sha256(raw).hexdigest()
    assert observations["premature"]["error"] is None
    assert observations["premature"]["emitted_bytes"] == len(raw)
    receipt = {
        "schema": "cmpct-j24g22b-crc-only-semantic-falsifier-v1",
        "source_reader_blob": "e716233403dabd0966863c45635e18fa5ac6afb8",
        "original_archive_sha256": hashlib.sha256(original).hexdigest(),
        "crc_mutant_archive_sha256": hashlib.sha256(mutant).hexdigest(),
        "modified_byte_offset": crc_offset,
        "original_crc32": original_crc,
        "mutated_crc32": original_crc ^ 1,
        "raw_payload_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_bytes": len(raw),
        "verify_error": verify_error,
        "comparators": observations,
        "decision": "FALSIFIED: SHA_ONLY_SPOOL_ACCEPTS_BHDR_CRC_INVALID_ARCHIVE_REJECTED_BY_ORIGINAL_READ",
        "scope": "research-only; no product or release change",
    }
    (folder / "crc_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "decision": receipt["decision"],
        "crc_offset": crc_offset,
        "payload_bytes": len(raw),
        "eager_output": observations["eager"]["emitted_bytes"],
        "spool_output": observations["spool"]["emitted_bytes"],
        "verify_error": verify_error,
        "crc_mutant_sha256": receipt["crc_mutant_archive_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: research/j24g22b_crc_semantic_court.py ARTIFACT_DIRECTORY")
    main(Path(sys.argv[1]))
