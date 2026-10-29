#!/usr/bin/env python3
"""Independent J24G50 signed-wire auditor. Does not import CMPCT or its tests.

Audits both actual physical records and the journal ancestry, including a
one-byte mutation that remains outside both authenticated index payloads.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def digest(blob: bytes) -> bytes:
    return hashlib.sha256(blob).digest()


def _physical(data: bytes, offset: int, expect: bytes):
    m, codec, flags, res, usize, csize, mlen, crc32, content_sha = BHDR.unpack_from(data, offset)
    assert m == b"CMA4" and flags == 0 and res == 0
    start = offset + BHDR.size + mlen
    encoded = data[start:start+csize]
    assert len(encoded) == csize
    if codec == 0:
        raw = encoded
    elif codec == 1:
        raw = zstd.ZstdDecompressor().decompress(encoded, max_output_size=max(1, usize))
    else:
        raise AssertionError(f"unexpected research fixture codec {codec}")
    assert len(raw) == usize and raw == expect
    assert digest(raw) == content_sha
    assert (zlib.crc32(raw) & 0xffffffff) == crc32
    return {"codec": codec, "usize": usize, "csize": csize, "encoded_offset": start, "encoded": encoded}


def inspect(valid: bytes, bad: bytes, receipt: dict):
    assert hashlib.sha256(valid).hexdigest() == receipt["valid_sha256"]
    assert hashlib.sha256(bad).hexdigest() == receipt["invalid_sha256"]
    assert len(valid) == len(bad)
    positions = [i for i, (a,b) in enumerate(zip(valid,bad)) if a != b]
    assert positions == [receipt["physical_corrupt_offset"]], positions
    assert receipt["modified_bytes"] == 1

    magic, rev, flags, cs, us, ds, index_sha = HDR.unpack_from(valid)
    assert (magic, rev, flags) == (b"CMPCT24\0", 24, 0)
    primary_enc = valid[HDR.size:HDR.size+cs]
    primary = zstd.ZstdDecompressor().decompress(primary_enc, max_output_size=us+1)
    assert len(primary) == us and digest(primary) == index_sha
    idx = msgpack.unpackb(primary, raw=False)
    assert [r[0] for r in idx["files"]] == ["empty.bin"]
    assert idx["fsmeta"]["xattrs"] == [[0, [["com.fcmo.cmpct.j24g50" if sys.platform=="darwin" else "user.cmpct_j24g50", b"cmpct-integrated-identity\x00\xff"]]]]
    assert len(idx["blobs"]) == 1
    blob = idx["blobs"][0]
    root = HDR.size + cs
    physical = _physical(valid, root+blob[0], b"")
    assert physical["codec"] == 1
    assert physical["encoded_offset"] == positions[0]
    assert physical["encoded"].startswith(bytes.fromhex("28b52ffd"))
    with_bad = bad[positions[0]:positions[0]+len(physical["encoded"])]
    try:
        zstd.ZstdDecompressor().decompress(with_bad, max_output_size=1)
    except zstd.ZstdError:
        pass
    else:
        raise AssertionError("corrupt zero-output Zstd frame decoded independently")

    fmagic, kind, fcodec, fflags, fres, fcs, fus, prev, fsha = FTR.unpack_from(valid, len(valid)-FTR.size)
    assert (fmagic, kind, fflags, fres) == (b"CMPTF24\0", 1, 0, 0)
    e = valid[len(valid)-FTR.size-fcs:len(valid)-FTR.size]
    generation = e if fcodec == 0 else zstd.ZstdDecompressor().decompress(e, max_output_size=fus+1)
    assert len(generation) == fus and digest(generation) == fsha
    delta = msgpack.unpackb(generation, raw=False)
    assert len(delta["ops"]) == 1 and delta["ops"][0][0] == "put"
    new = delta["ops"][0][1]
    assert new[0] == "a-new.bin" and new[6][0] == 0
    assert len(delta["blobs"]) == 1
    new_blob = delta["blobs"][0]
    assert new[6][1] == len(idx["blobs"])
    second = _physical(valid, root+new_blob[0], b"independent-new-content"*7)
    assert new_blob[1] == second["usize"] and new_blob[2] == second["csize"]
    # Independent name-keyed row interpretation: the original path retains the
    # original xattr while the inserted path has none.
    new_rows = sorted([idx["files"][0], new], key=lambda r:r[0])
    assert [r[0] for r in new_rows] == ["a-new.bin", "empty.bin"]
    assert new_rows[1][0] == idx["files"][0][0]
    return {
        "decision": "COMPOSED_WIRE_VALID_AND_ONE_BYTE_CORRUPTION_REFUSED",
        "valid_sha256": digest(valid).hex(),
        "invalid_sha256": digest(bad).hex(),
        "journal_footer_previous": prev,
        "base_signed_index_sha256": index_sha.hex(),
        "journal_signed_sha256": fsha.hex(),
        "old_metadata_ordinal": 0,
        "new_metadata_ordinal": 1,
        "decoded_empty_frame": True,
        "new_blob_codec": second["codec"],
        "physical_corrupt_offset": positions[0],
    }


def main() -> int:
    folder = Path(sys.argv[1])
    receipt = json.loads((folder/"receipt.json").read_text())
    report = inspect((folder/"valid-with-journal.cmpct").read_bytes(),
                     (folder/"corrupt-with-journal.cmpct").read_bytes(), receipt)
    (folder/"independent-audit.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
