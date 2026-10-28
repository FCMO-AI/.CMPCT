#!/usr/bin/env python3
"""J24B03-H: distinct, preregistered physical RAW header hostile-field court.

Ten deterministic mutations are run against the same frozen released Reader and
the guarded candidate. No Builder or mutable fixture identity participates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, K_FILE, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24b03_direct_blob_size_court import PAYLOAD, wire


def observation(fn):
    try:
        data = fn()
    except Exception as exc:
        return {"status": "REJECT", "type": type(exc).__name__}
    if isinstance(data, bytes):
        return {"status": "ACCEPT", "hex": data.hex(),
                "sha256": hashlib.sha256(data).hexdigest()}
    return {"status": "ACCEPT"}


def run(mode: str):
    items = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24b03-h-") as td:
        for kind in (K_FILE, K_SYMLINK):
            good, _, old_frame = wire(kind, CODEC_RAW, len(PAYLOAD))
            name = "direct.bin" if kind == K_FILE else "link"
            valid_path = Path(td) / f"valid-{kind}.cmpct"
            valid_path.write_bytes(good)
            assert observation(lambda: preflight_archive(valid_path))["status"] == "ACCEPT"
            with CMPCT(valid_path) as ar:
                assert ar.read_range(name, 7, 8) == PAYLOAD[7:15]

            head = list(BHDR.unpack_from(old_frame, 0))
            options = ("magic", "codec", "usize", "csize", "mlen")
            for fault in options:
                malformed = list(head)
                if fault == "magic":
                    malformed[0] = bytes([BMAGIC[0] ^ 1]) + BMAGIC[1:]
                elif fault == "codec":
                    malformed[1] = CODEC_ZSTD
                elif fault == "usize":
                    malformed[4] = len(PAYLOAD) + 1
                elif fault == "csize":
                    malformed[5] = len(PAYLOAD) - 1
                elif fault == "mlen":
                    malformed[6] = 1
                bhdr = BHDR.pack(*malformed)
                assert bhdr != old_frame[:BHDR.size]
                new_frame = bhdr + old_frame[BHDR.size:]
                image = good.replace(old_frame, new_frame, 1)
                assert image != good and len(image) == len(good)
                path = Path(td) / f"bad-{kind}-{fault}.cmpct"
                path.write_bytes(image)
                preflight = observation(lambda: preflight_archive(path))
                with CMPCT(path) as ar:
                    selection = observation(lambda: ar.read_range(name, 7, 8))
                assert preflight["status"] == "REJECT", (fault, kind, preflight)
                assert selection["status"] == (
                    "ACCEPT" if mode == "vulnerable" else "REJECT"), (fault, kind, selection)
                if mode == "vulnerable":
                    assert selection["hex"] == PAYLOAD[7:15].hex()
                items.append({"kind": kind, "fault": fault, "archive_sha256":
                              hashlib.sha256(image).hexdigest(), "preflight": preflight,
                              "range": selection})

    import cmpct.reader as reader
    result = {"experiment": "J24B03-H", "mode": mode,
              "reader": str(Path(reader.__file__).resolve()),
              "valid_controls": 2, "items": items}
    dst = os.environ.get("J24B03_H_RECEIPT")
    if dst:
        Path(dst).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"experiment": result["experiment"], "mode": mode,
                      "cases": len(items), "valid_controls": 2, "result": "PASS"}))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--expect", choices=("vulnerable", "repaired"), required=True)
    run(p.parse_args().expect)
