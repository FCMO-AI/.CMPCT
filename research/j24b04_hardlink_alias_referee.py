#!/usr/bin/env python3
"""Second-root J24B04 wire and outcome auditor (no cmpct import).

Re-decodes complete bytes, independent framing/CRC/SHA, signed primary/tail
indexes and verifies what the Reader reported. It is not a second Reader.
"""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
SHA = lambda data: hashlib.sha256(data).digest()
PAYLOAD = (b"exact-hardlink-owner-ABCD" * 8)[:128]


def audit_case(row):
    raw = base64.b64decode(row["archive_base64"], validate=True)
    assert SHA(raw).hex() == row["archive_sha256"]
    magic, rev, flags, ic, iu, span, ih = HDR.unpack_from(raw, 0)
    assert magic == b"CMPCT24\0" and rev == 24 and flags == 0
    primary = raw[HDR.size:HDR.size+ic]
    plain = zstd.ZstdDecompressor().decompress(primary, max_output_size=iu)
    assert len(plain) == iu and SHA(plain) == ih
    idx = msgpack.unpackb(plain, raw=False, strict_map_key=False)
    assert idx["v"] == 24 and len(idx["files"]) == 2
    owner, alias = idx["files"]
    assert owner[0] == "a-owner.bin" and owner[1] == 0
    assert owner[4] == 128 and owner[6] == [0, 0]
    assert alias[0] == "z-alias.bin" and alias[1] == 3
    assert alias[4] == row["declared"] and alias[6] == [owner[0]]
    assert len(idx["blobs"]) == 1
    blob = idx["blobs"][0]
    assert blob[0] == 0 and blob[1] == 128 and blob[3] == row["codec"]
    pos = HDR.size + ic
    m, codec, flags, reserved, us, cs, ml, crc, digest = BHDR.unpack_from(raw, pos)
    assert m == b"CMA4" and codec == row["codec"] and flags == reserved == ml == 0
    assert us == 128 and blob == [0, us, cs, codec, ml]
    comp = raw[pos+BHDR.size:pos+BHDR.size+cs]
    assert len(comp) == cs
    data = comp if codec == 0 else zstd.ZstdDecompressor().decompress(
        comp, max_output_size=us)
    assert data == PAYLOAD
    assert SHA(data) == digest and (binascii.crc32(data)&0xffffffff) == crc
    assert span == BHDR.size + cs
    tail_start = pos + span
    assert raw[tail_start:tail_start+ic] == primary
    foot = FTR.unpack_from(raw, tail_start+ic)
    assert foot == (b"CMPTF24\0", 0, 1, 0, 0, ic, iu, 0, ih)
    assert len(raw) == tail_start+ic+FTR.size

    for label in ("preflight", "owner_read", "alias_read", "verify",
                  "alias_zero", "alias_first", "alias_owner_eof"):
        assert row[label]["status"] == "ACCEPT", (label, row)
    assert row["owner_read"]["size"] == row["alias_read"]["size"] == len(data)
    assert row["owner_read"]["sha256"] == row["alias_read"]["sha256"] == SHA(data).hex()
    assert row["owner_read"]["hex"] == row["alias_read"]["hex"] == data[:8].hex()
    assert row["verify"]["value"] == 2
    assert row["alias_zero"]["size"] == 0
    assert row["alias_first"]["size"] == 1
    assert row["alias_owner_eof"]["size"] == 0
    assert row["owner_beyond_end"]["status"] == "REJECT"
    if row["declared"] < 128:
        assert row["alias_beyond_declared"]["status"] == "ACCEPT"
        assert row["alias_beyond_declared"]["size"] == 1
    else:
        assert row["alias_beyond_declared"]["status"] == "REJECT"
    return idx, hashlib.sha256(comp).hexdigest()


def audit(receipt):
    assert receipt["experiment"] == "J24B04"
    assert receipt["revision"] == 24
    assert receipt["source_kind"] == "released-reader"
    assert receipt["result"] == "PREDICTION_SURVIVED"
    assert receipt["missing_target_preflight"] == "REJECT"
    rows = receipt["cases"]
    assert receipt["case_count"] == len(rows) == 8
    identity = set()
    by_codec = {0: {}, 1: {}}
    for row in rows:
        key = (row["codec"], row["declared"])
        assert key not in identity and row["codec"] in (0,1)
        assert row["declared"] in (0,120,128,136)
        identity.add(key)
        idx, physical_digest = audit_case(row)
        by_codec[row["codec"]][row["declared"]] = (idx, physical_digest)
    assert len(by_codec[0]) == len(by_codec[1]) == 4
    for codec, entries in by_codec.items():
        assert len({value[1] for value in entries.values()}) == 1
        base = copy.deepcopy(entries[128][0])
        for declared, (idx, _) in entries.items():
            assert idx["files"][1][4] == declared
            idx["files"][1][4] = 128
            assert idx == base
    return 8


def mutate(receipt, n):
    bad = copy.deepcopy(receipt)
    row = bad["cases"][0]
    if n == 0: row["declared"] = 127
    if n == 1: row["archive_sha256"] = "0" * 64
    if n == 2: row["alias_read"]["size"] = 0
    if n == 3: row["alias_read"]["sha256"] = "0" * 64
    if n == 4: row["alias_beyond_declared"]["status"] = "ACCEPT"
    if n == 5: row["preflight"]["status"] = "REJECT"
    if n == 6: row["archive_base64"] = row["archive_base64"][:-8] + "AAAAAAAA"
    if n == 7: bad["missing_target_preflight"] = "ACCEPT"
    return bad


def main():
    receipt = json.loads(Path(sys.argv[1]).read_text())
    checked = audit(receipt)
    rejected = 0
    for n in range(8):
        try:
            audit(mutate(receipt, n))
        except (AssertionError, ValueError, TypeError, KeyError, struct.error, zstd.ZstdError, binascii.Error):
            rejected += 1
    assert rejected == 8
    result = {"experiment": "J24B04", "decision": "HARDLINK_ALIAS_DECLARED_SIZE_INCONSISTENCY_REPRODUCED",
              "genuine_wire_cases": checked, "invalid_alias_cases": 6,
              "independent_receipt_audit": "PASS", "adversarial_receipts_rejected": rejected,
              "limits": "Reader implementation independently executed; auditor is not a second Reader."}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
