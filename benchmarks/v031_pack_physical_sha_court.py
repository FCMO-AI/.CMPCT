#!/usr/bin/env python3
"""Independent revision-24 physical PACK integrity court (not Builder-produced).

A CRC-repaired change to stored PACK bytes leaves their original SHA-256 in
the physical blob header. The whole PACK is the only digest owner for packed
logical slices: revision 24 deliberately omits per-slice SHA fields.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import tempfile
from pathlib import Path

import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_FILE, MAGIC,
    S_BLOB, S_PACK, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


def archive_bytes(original: bytes, materialized: bytes, *, packed: bool) -> bytes:
    assert len(original) == len(materialized) and len(original) % 2 == 0
    half = len(original) // 2
    rows = (
        [
            ["alpha.md", K_FILE, 0o644, 0, half, None, [S_PACK, 0, 0, half]],
            ["beta.md", K_FILE, 0o644, 0, half, None, [S_PACK, 0, half, half]],
        ]
        if packed
        else [["direct.md", K_FILE, 0o644, 0, len(original), None, [S_BLOB, 0]]]
    )
    # The index is independently constructed, rather than emitted by Builder.
    index = {
        "v": VERSION,
        "files": rows,
        "blobs": [[0, len(original), len(materialized), CODEC_RAW, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": ["micro-solid-packs"] if packed else [],
    }
    raw_index = msgpack.packb(index, use_bin_type=True)
    encoded_index = zc(raw_index, 3)
    physical_record = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(original), len(materialized), 0,
        binascii.crc32(materialized) & 0xffffffff,
        sha(original),  # Deliberately NOT recomputed after changing materialized bytes.
    ) + materialized
    head = HDR.pack(MAGIC, VERSION, 0, len(encoded_index), len(raw_index),
                    len(physical_record), sha(raw_index))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded_index),
                      len(raw_index), 0, sha(raw_index))
    return head + encoded_index + physical_record + encoded_index + footer


def accepts_verify(path: Path) -> bool:
    with CMPCT(path) as ar:
        try:
            ar.verify()
        except (IOError, OSError, ValueError):
            return False
    return True


def run(expect_packed_tamper: str) -> dict:
    left = (b"the quick brown fox " * 4)[:64]
    right = (b"PACK member two: exact " * 4)[:64]
    original = left + right
    altered = original[:-1] + bytes([original[-1] ^ 1])
    assert len(original) == len(altered) == 128
    result = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-pack-sha-court-") as td:
        root = Path(td)
        for label, packed, payload in (
            ("pack_control", True, original),
            ("pack_crc_repaired", True, altered),
            ("direct_crc_repaired", False, altered),
        ):
            target = root / (label + ".cmpct")
            image = archive_bytes(original, payload, packed=packed)
            target.write_bytes(image)
            summary = preflight_archive(target)
            assert summary["blobs"] == 1
            with CMPCT(target) as reader:
                name = "beta.md" if packed else "direct.md"
                got = reader.read(name)
                expected = payload[64:] if packed else payload
                assert got == expected, f"physical decoding mismatch in {label}"
                if packed:
                    assert reader.read("alpha.md") == left
                result[label] = {
                    "stored_bytes": len(image),
                    "archive_sha256": hashlib.sha256(image).hexdigest(),
                    "preflight": "PASS",
                    "normal_read_sha256": hashlib.sha256(got).hexdigest(),
                    "whole_pack_sha256_changed": hashlib.sha256(payload).digest() != sha(original),
                }
            result[label]["verify"] = "ACCEPT" if accepts_verify(target) else "REJECT"

    assert result["pack_control"]["verify"] == "ACCEPT"
    assert result["direct_crc_repaired"]["verify"] == "REJECT"
    wanted = "ACCEPT" if expect_packed_tamper == "accept" else "REJECT"
    assert result["pack_crc_repaired"]["verify"] == wanted, (
        f"PACK verification expected {wanted}: {result}"
    )
    result["scientific_decision"] = (
        "BASELINE_PACK_SHA_BYPASS" if wanted == "ACCEPT"
        else "PACK_PHYSICAL_SHA_VERIFIED"
    )
    result["status"] = "PASS"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-pack", choices=("accept", "reject"), required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.expected_pack), indent=2, sort_keys=True))
