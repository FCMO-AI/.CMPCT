#!/usr/bin/env python3
"""J24B01: Builder-independent signed-index direct RAW range-boundary court.

Research-only: creates two revision-24 archives with identical, valid physical
RAW blob bytes, changing only authenticated index logical file size.
"""
from __future__ import annotations
import binascii
import hashlib
import json
import tempfile
from pathlib import Path
import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_FILE, MAGIC,
    S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


PAYLOAD = (b"CMPCT-direct-physical-owner-0123456789|" * 4)[:128]
assert len(PAYLOAD) == 128


def construct(declared_size: int) -> tuple[bytes, bytes, bytes]:
    """Return physical v24 bytes, encoded tail index and original physical frame."""
    index = {
        "v": VERSION,
        "files": [["direct.bin", K_FILE, 0o644, 0, declared_size, None, [S_BLOB, 0]]],
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    wire_index = msgpack.packb(index, use_bin_type=True)
    packed_index = zc(wire_index, 3)
    physical = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xffffffff, sha(PAYLOAD),
    ) + PAYLOAD
    first = HDR.pack(
        MAGIC, VERSION, 0, len(packed_index), len(wire_index),
        len(physical), sha(wire_index),
    )
    last = FTR.pack(
        FMAGIC, 0, 1, 0, 0, len(packed_index), len(wire_index),
        0, sha(wire_index),
    )
    return first + packed_index + physical + packed_index + last, packed_index, physical


def result_of(f):
    try:
        value = f()
    except Exception as exc:
        return {"status": "REJECT", "error_type": type(exc).__name__, "message": str(exc)[:160]}
    if isinstance(value, bytes):
        return {"status": "ACCEPT", "length": len(value), "hex": value.hex(),
                "sha256": hashlib.sha256(value).hexdigest()}
    return {"status": "ACCEPT", "value": value if isinstance(value, (str, int)) else "summary"}


def run() -> dict:
    report = {"experiment": "J24B01", "revision": VERSION, "payload_length": len(PAYLOAD),
              "payload_sha256": hashlib.sha256(PAYLOAD).hexdigest(), "cases": {}}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b01-") as td:
        for label, size in (("valid", 128), ("oversized", 136)):
            image, tail, physical = construct(size)
            archive = Path(td) / (label + ".cmpct")
            archive.write_bytes(image)
            # The physical frame and all its CRC/SHA fields remain identical
            # across controls; only both authenticated index copies change.
            case = {"archive_hex": image.hex(),
                    "archive_sha256": hashlib.sha256(image).hexdigest(),
                    "physical_sha256": hashlib.sha256(physical).hexdigest(),
                    "tail_index_sha256": hashlib.sha256(tail).hexdigest(),
                    "tail_prefix_hex": tail[:8].hex(),
                    "declared_logical_size": size,
                    "physical_owner_length": len(PAYLOAD),
                    "preflight": result_of(lambda: preflight_archive(archive))}
            with CMPCT(archive) as ar:
                case["read"] = result_of(lambda: ar.read("direct.bin"))
                case["verify"] = result_of(lambda: ar.verify())
                case["in_frame_range"] = result_of(lambda: ar.read_range("direct.bin", 20, 8))
                case["after_owner_range"] = result_of(
                    lambda: ar.read_range("direct.bin", 128, 8))
            report["cases"][label] = case

    valid, bad = report["cases"]["valid"], report["cases"]["oversized"]
    assert valid["physical_sha256"] == bad["physical_sha256"]
    assert valid["preflight"]["status"] == "ACCEPT"
    assert valid["read"]["status"] == "ACCEPT"
    assert valid["verify"]["status"] == "ACCEPT"
    assert valid["in_frame_range"]["hex"] == PAYLOAD[20:28].hex()
    assert valid["after_owner_range"]["status"] == "REJECT"
    assert bad["preflight"]["status"] == "REJECT"
    assert bad["read"]["status"] == "REJECT"
    assert bad["in_frame_range"]["hex"] == PAYLOAD[20:28].hex()
    # A selected byte range inside the forged logical size must never traverse
    # the end of its physical owner. Predicted *incorrect* released outcome:
    assert bad["after_owner_range"]["status"] == "ACCEPT"
    assert bad["after_owner_range"]["hex"] == bad["tail_prefix_hex"]
    assert bad["after_owner_range"]["length"] == 8
    report["decision"] = "DIRECT_RAW_RANGE_SPILLS_INTO_AUTHENTICATED_TAIL"
    report["status"] = "PASS"
    return report


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
