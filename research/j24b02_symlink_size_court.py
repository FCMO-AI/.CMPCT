#!/usr/bin/env python3
"""J24B02 frozen symlink direct-S_BLOB size-disagreement test (no Builder)."""
from __future__ import annotations
import binascii
import hashlib
import json
import tempfile
from pathlib import Path
import msgpack
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_SYMLINK, MAGIC, S_BLOB, VERSION, sha, zc
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

PAYLOAD = (b"cmpct-symlink-target-A0123456789|" * 5)[:128]
assert len(PAYLOAD) == 128

def construct(declared_size):
    index = {
        "v": VERSION,
        "files": [["link", K_SYMLINK, 0o777, 0, declared_size, sha(PAYLOAD), [S_BLOB, 0]]],
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    wire = msgpack.packb(index, use_bin_type=True)
    packed = zc(wire, 3)
    physical = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xffffffff, sha(PAYLOAD)
    ) + PAYLOAD
    first = HDR.pack(MAGIC, VERSION, 0, len(packed), len(wire), len(physical), sha(wire))
    foot = FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed), len(wire), 0, sha(wire))
    return first + packed + physical + packed + foot, physical, packed

def observe(f):
    try:
        output = f()
    except Exception as exc:
        return {"status": "REJECT", "error_type": type(exc).__name__,
                "message": str(exc)[:160]}
    if isinstance(output, bytes):
        return {"status": "ACCEPT", "length": len(output), "hex": output.hex(),
                "sha256": hashlib.sha256(output).hexdigest()}
    return {"status": "ACCEPT", "value": output if isinstance(output, (int, str)) else "summary"}

def run():
    report = {"question": "J24B02", "revision": VERSION,
              "payload_sha256": hashlib.sha256(PAYLOAD).hexdigest(), "cases": {}}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b02-") as td:
        for label, declared in (("valid", 128), ("oversized", 136)):
            image, frame, tail = construct(declared)
            archive = Path(td) / f"{label}.cmpct"
            archive.write_bytes(image)
            c = {"archive_hex": image.hex(),
                 "archive_sha256": hashlib.sha256(image).hexdigest(),
                 "physical_frame_sha256": hashlib.sha256(frame).hexdigest(),
                 "tail_prefix_hex": tail[:8].hex(),
                 "declared": declared, "owner_size": 128,
                 "preflight": observe(lambda: preflight_archive(archive))}
            with CMPCT(archive) as r:
                c["read"] = observe(lambda: r.read("link"))
                c["verify"] = observe(lambda: r.verify())
                c["inside"] = observe(lambda: r.read_range("link", 20, 8))
                c["after_owner"] = observe(lambda: r.read_range("link", 128, 8))
            report["cases"][label] = c
    Path("benchmark-artifacts").mkdir(exist_ok=True)
    Path("benchmark-artifacts/j24b02-raw.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24B02_RAW=" + json.dumps(report, sort_keys=True), flush=True)
    control = report["cases"]["valid"]
    hostile = report["cases"]["oversized"]
    assert control["preflight"]["status"] == "ACCEPT"
    assert control["read"]["status"] == "ACCEPT" and control["read"]["hex"] == PAYLOAD.hex()
    assert control["verify"]["status"] == "ACCEPT"
    assert control["inside"]["hex"] == PAYLOAD[20:28].hex()
    assert control["after_owner"]["status"] == "REJECT"
    assert hostile["preflight"]["status"] == "ACCEPT"
    assert hostile["read"]["status"] == "ACCEPT" and hostile["read"]["hex"] == PAYLOAD.hex()
    assert hostile["verify"]["status"] == "ACCEPT"
    assert hostile["inside"]["hex"] == PAYLOAD[20:28].hex()
    assert hostile["after_owner"]["status"] == "ACCEPT"
    assert hostile["after_owner"]["length"] == 8
    assert hostile["after_owner"]["hex"] == hostile["tail_prefix_hex"]
    assert control["physical_frame_sha256"] == hostile["physical_frame_sha256"]
    report["status"] = "PASS"
    print(json.dumps({"status": "PASS", "decision": "K_SYMLINK_SIZE_NOT_ENFORCED",
                      "cases": {k: {"preflight": v["preflight"]["status"],
                                    "read": v["read"]["status"],
                                    "verify": v["verify"]["status"],
                                    "after_owner": v["after_owner"]["status"]}
                                for k, v in report["cases"].items()}}, sort_keys=True))

if __name__ == "__main__":
    run()
