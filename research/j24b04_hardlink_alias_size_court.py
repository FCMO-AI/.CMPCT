#!/usr/bin/env python3
"""J24B04 prospective signed-wire hardlink-alias size court.

This is deliberately research-only: Builder-independent revision-24 images are
read by the installed, unmodified CMPCT Reader. The structural claim is about
the alias's own declared size, not the referenced S_BLOB owner or SHA-256.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import tempfile

import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, FMAGIC, FTR, HDR,
    K_FILE, K_HARDLINK, MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

OWNER = "a-owner.bin"
ALIAS = "z-alias.bin"
PAYLOAD = (b"exact-hardlink-owner-ABCD" * 8)[:128]
assert len(PAYLOAD) == 128


def image(codec: int, alias_size: int, *, alias_target: str = OWNER) -> bytes:
    comp = PAYLOAD if codec == CODEC_RAW else zc(PAYLOAD, 3)
    index = {
        "v": VERSION,
        "files": [
            [OWNER, K_FILE, 0o644, 0, len(PAYLOAD), None, [S_BLOB, 0]],
            [ALIAS, K_HARDLINK, 0o644, 0, alias_size, None, [alias_target]],
        ],
        "blobs": [[0, len(PAYLOAD), len(comp), codec, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    plain = msgpack.packb(index, use_bin_type=True)
    enc = zc(plain, 3)
    frame = BHDR.pack(
        BMAGIC, codec, 0, 0, len(PAYLOAD), len(comp), 0,
        binascii.crc32(PAYLOAD) & 0xFFFFFFFF, sha(PAYLOAD),
    ) + comp
    header = HDR.pack(MAGIC, VERSION, 0, len(enc), len(plain), len(frame), sha(plain))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(enc), len(plain), 0, sha(plain))
    return header + enc + frame + enc + footer


def observe(fn):
    try:
        result = fn()
    except Exception as error:
        return {"status": "REJECT", "error_type": type(error).__name__}
    if isinstance(result, bytes):
        return {"status": "ACCEPT", "size": len(result),
                "sha256": hashlib.sha256(result).hexdigest(),
                "hex": result[:8].hex()}
    return {"status": "ACCEPT", "value": result if isinstance(result, int) else None}


def main():
    records = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b04-") as root:
        for codec in (CODEC_RAW, CODEC_ZSTD):
            for declared in (128, 136, 120, 0):
                raw = image(codec, declared)
                path = Path(root) / f"alias-{codec}-{declared}.cmpct"
                path.write_bytes(raw)
                row = {
                    "codec": codec, "declared": declared,
                    "owner_size": len(PAYLOAD),
                    "archive_sha256": hashlib.sha256(raw).hexdigest(),
                    "archive_base64": base64.b64encode(raw).decode("ascii"),
                    "preflight": observe(lambda: preflight_archive(path)),
                }
                with CMPCT(path) as reader:
                    row["owner_read"] = observe(lambda: reader.read(OWNER))
                    row["alias_read"] = observe(lambda: reader.read(ALIAS))
                    row["verify"] = observe(lambda: reader.verify())
                    row["alias_zero"] = observe(lambda: reader.read_range(ALIAS, 0, 0))
                    row["alias_first"] = observe(lambda: reader.read_range(ALIAS, 0, 1))
                    row["alias_owner_eof"] = observe(lambda: reader.read_range(ALIAS, 128, 0))
                    row["alias_beyond_declared"] = observe(
                        lambda: reader.read_range(ALIAS, declared, 1))
                    row["owner_beyond_end"] = observe(
                        lambda: reader.read_range(OWNER, 128, 1))
                assert row["preflight"]["status"] == "ACCEPT", row
                for key in ("owner_read", "alias_read", "verify", "alias_zero",
                            "alias_first", "alias_owner_eof"):
                    assert row[key]["status"] == "ACCEPT", (key, row)
                assert row["owner_read"]["size"] == row["alias_read"]["size"] == 128, row
                assert row["owner_read"]["sha256"] == row["alias_read"]["sha256"], row
                assert row["verify"]["value"] == 2, row
                assert row["owner_beyond_end"]["status"] == "REJECT", row
                if declared < 128:
                    assert row["alias_beyond_declared"]["status"] == "ACCEPT", row
                    assert row["alias_beyond_declared"]["size"] == 1, row
                if declared >= 128:
                    assert row["alias_beyond_declared"]["status"] == "REJECT", row
                records.append(row)

        # Stronger negative: activate genuine hardlink graph validation.
        missing = image(CODEC_RAW, 128, alias_target="missing-file")
        missing_path = Path(root) / "missing.cmpct"
        missing_path.write_bytes(missing)
        assert observe(lambda: preflight_archive(missing_path))["status"] == "REJECT"

    receipt = {
        "experiment": "J24B04", "source_kind": "released-reader",
        "revision": VERSION, "cases": records, "case_count": len(records),
        "missing_target_preflight": "REJECT",
        "result": "PREDICTION_SURVIVED",
    }
    out = os.environ.get("J24B04_RECEIPT")
    if out:
        Path(out).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"experiment": "J24B04", "result": receipt["result"],
                      "cases": len(records), "different_declared": 6,
                      "missing_target": "REJECT"}, sort_keys=True))


if __name__ == "__main__":
    main()
