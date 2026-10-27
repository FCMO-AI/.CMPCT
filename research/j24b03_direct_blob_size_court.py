#!/usr/bin/env python3
"""J24B03 independent signed-wire court: exact direct-owner length custody.

No Builder involved. The same test corpus runs against pinned released Reader
(--expect vulnerable) and candidate Reader (--expect repaired), never altering
the original J24B01/J24B02 scientific tests or their preregistered expectations.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zlib

import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_DEFLATE, CODEC_RAW, CODEC_ZSTD,
    FMAGIC, FTR, HDR, K_FILE, K_SYMLINK, MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]
assert len(PAYLOAD) == 128


def wire(kind: int, codec: int, declared_size: int, physical: bytes = PAYLOAD):
    if codec == CODEC_RAW:
        compressed = physical
    elif codec == CODEC_ZSTD:
        compressed = zc(physical, 3)
    elif codec == CODEC_DEFLATE:
        co = zlib.compressobj(6, zlib.DEFLATED, -15)
        compressed = co.compress(physical) + co.flush()
    else:
        raise ValueError(codec)

    idx = {
        "v": VERSION,
        "files": [["direct.bin" if kind == K_FILE else "link", kind, 0o644, 0,
                   declared_size, None, [S_BLOB, 0]]],
        "blobs": [[0, len(physical), len(compressed), codec, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    plain = msgpack.packb(idx, use_bin_type=True)
    encoded = zc(plain, 3)
    frame = BHDR.pack(
        BMAGIC, codec, 0, 0, len(physical), len(compressed), 0,
        binascii.crc32(physical) & 0xFFFFFFFF, sha(physical),
    ) + compressed
    first = HDR.pack(MAGIC, VERSION, 0, len(encoded), len(plain), len(frame), sha(plain))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(plain), 0, sha(plain))
    return first + encoded + frame + encoded + footer, encoded, frame


def observe(operation):
    try:
        obj = operation()
    except Exception as exc:
        return {"status": "REJECT", "type": type(exc).__name__}
    if isinstance(obj, bytes):
        return {"status": "ACCEPT", "length": len(obj), "sha256": hashlib.sha256(obj).hexdigest(),
                "hex": obj.hex() if len(obj) <= 8 else None}
    return {"status": "ACCEPT"}


def run(mode: str):
    cases = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b03-") as td:
        for codec in (CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE):
            for kind in (K_FILE, K_SYMLINK):
                for declared in (128, 136, 120, 0):
                    physical = PAYLOAD
                    archive_bytes, tail, frame = wire(kind, codec, declared, physical)
                    path = Path(td) / f"test-{codec}-{kind}-{declared}.cmpct"
                    path.write_bytes(archive_bytes)
                    name = "direct.bin" if kind == K_FILE else "link"
                    row = {
                        "codec": codec, "kind": kind, "declared": declared, "physical": len(physical),
                        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
                        "frame_sha256": hashlib.sha256(frame).hexdigest(),
                        "tail_prefix": tail[:8].hex(),
                        "preflight": observe(lambda: preflight_archive(path)),
                    }
                    with CMPCT(path) as reader:
                        row["read"] = observe(lambda: reader.read(name))
                        row["verify"] = observe(lambda: reader.verify())
                        row["zero"] = observe(lambda: reader.read_range(name, 0, 0))
                        row["early"] = observe(lambda: reader.read_range(name, 7, 8))
                        row["eof"] = observe(lambda: reader.read_range(name, 128, 0))
                        row["spill"] = observe(lambda: reader.read_range(name, 128, 8))
                    good = declared == len(physical)
                    if good:
                        assert row["preflight"]["status"] == "ACCEPT", row
                        assert row["read"]["status"] == "ACCEPT", row
                        assert row["verify"]["status"] == "ACCEPT", row
                        assert row["read"]["sha256"] == hashlib.sha256(physical).hexdigest(), row
                        assert row["zero"]["status"] == "ACCEPT", row
                        assert row["early"]["status"] == "ACCEPT", row
                        assert row["eof"]["status"] == "ACCEPT", row
                        assert row["spill"]["status"] == "REJECT", row
                    elif mode == "repaired":
                        for action in ("preflight", "read", "verify", "zero", "early", "eof", "spill"):
                            # Out-of-size requests are always rejected, but even logically
                            # in-range requests must reject contradicting owner geometry.
                            assert row[action]["status"] == "REJECT", (action, row)
                    else:
                        assert row["preflight"]["status"] == "ACCEPT", row
                        assert row["zero"]["status"] == "ACCEPT", row
                        assert row["early"]["status"] == "ACCEPT" if declared >= 15 else row["early"]["status"] == "REJECT", row
                        if kind == K_SYMLINK:
                            assert row["read"]["status"] == "ACCEPT", row
                            assert row["verify"]["status"] == "ACCEPT", row
                        else:
                            assert row["read"]["status"] == "REJECT", row
                            assert row["verify"]["status"] == "REJECT", row
                        if codec == CODEC_RAW and declared == 136:
                            assert row["spill"]["status"] == "ACCEPT", row
                            assert row["spill"]["hex"] == row["tail_prefix"], row
                    cases.append(row)

        # Empty valid owner is an essential equality boundary.
        for kind in (K_FILE, K_SYMLINK):
            image, _, _ = wire(kind, CODEC_RAW, 0, b"")
            path = Path(td) / f"empty-{kind}.cmpct"
            path.write_bytes(image)
            name = "direct.bin" if kind == K_FILE else "link"
            assert observe(lambda: preflight_archive(path))["status"] == "ACCEPT"
            with CMPCT(path) as reader:
                assert reader.read(name) == b""
                assert reader.read_range(name, 0, 0) == b""
                reader.verify()

    receipt = {"experiment": "J24B03", "mode": mode, "format_revision": VERSION,
               "case_count": len(cases), "cases": cases,
               "empty_owners_verified": 2,
               "source_module": str(Path(__import__("cmpct.reader").reader.__file__).resolve())}
    target = os.environ.get("J24B03_RECEIPT")
    if target:
        Path(target).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"mode": mode, "cases": len(cases), "empty_controls": 2,
                      "result": "PASS", "source_module": receipt["source_module"]}))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=("repaired", "vulnerable"), required=True)
    run(parser.parse_args().expect)
