#!/usr/bin/env python3
"""Second-root J24B01 physical wire and result auditor (never imports CMPCT).

Checks exact r24 framing, physical SHA/CRC, indexed tail bytes and prospective
decision; deliberately altered receipts must fail closed.
"""
from __future__ import annotations
import argparse
import binascii
import copy
import hashlib
import json
import struct

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def require(cond, message):
    if not cond:
        raise AssertionError(message)


def audit(report):
    require(report["experiment"] == "J24B01" and report["revision"] == 24, "identity")
    require(report["payload_length"] == 128, "physical length")
    outputs = {}
    count = 0
    for name, declared in (("valid", 128), ("oversized", 136)):
        c = report["cases"][name]
        image = bytes.fromhex(c["archive_hex"])
        require(hashlib.sha256(image).hexdigest() == c["archive_sha256"], "archive digest")
        magic, version, flags, cs, us, ds, ih = HDR.unpack_from(image)
        require(magic == (b"CMPCT24" + bytes([0])) and version == 24, "header identity")
        require(cs > 0 and us > 0, "encoded index")
        rstart = HDR.size + cs
        bmagic, codec, bflags, reserved, bu, bc, bm, bcrc, bhash = BHDR.unpack_from(image, rstart)
        require(bmagic == b"CMA4" and codec == 0 and bu == bc == 128 and bm == 0, "physical frame geometry")
        data = image[rstart + BHDR.size:rstart + BHDR.size + bu]
        require(len(data) == 128, "raw bytes")
        require(binascii.crc32(data) & 0xffffffff == bcrc, "physical crc")
        require(hashlib.sha256(data).digest() == bhash, "physical sha")
        require(ds == BHDR.size + bu, "declared physical region")
        tail_start = rstart + ds
        tail = image[tail_start:tail_start + cs]
        require(tail == image[HDR.size:HDR.size + cs], "index redundancy")
        require(hashlib.sha256(tail).hexdigest() == c["tail_index_sha256"], "tail digest")
        require(tail[:8].hex() == c["tail_prefix_hex"], "tail prefix")
        fpos = tail_start + cs
        fm, kind, fc, ff, fr, fcs, fus, fp, fh = FTR.unpack_from(image, fpos)
        require((fm, kind, fc, fcs, fus, fp, fh) == (
                (b"CMPTF24" + bytes([0])), 0, 1, cs, us, 0, ih), "footer identity")
        require(fpos + FTR.size == len(image), "archive complete")
        require(c["physical_owner_length"] == len(data), "owner receipt")
        require(c["declared_logical_size"] == declared, "logical receipt")
        require(c["physical_sha256"] == hashlib.sha256(image[rstart:tail_start]).hexdigest(),
                "frame receipt")
        require(c["in_frame_range"]["status"] == "ACCEPT", "in-range availability")
        require(c["in_frame_range"]["hex"] == data[20:28].hex(), "in-range exactness")
        require(c["after_owner_range"]["status"] == ("REJECT" if name == "valid" else "ACCEPT"),
                "boundary decision")
        if name == "oversized":
            require(c["after_owner_range"]["hex"] == tail[:8].hex(), "spill provenance")
            require(c["after_owner_range"]["length"] == 8, "spill length")
            require(c["preflight"]["status"] == "REJECT" and c["read"]["status"] == "REJECT",
                    "independent strict controls")
        else:
            require(c["preflight"]["status"] == "ACCEPT" and c["read"]["status"] == "ACCEPT"
                    and c["verify"]["status"] == "ACCEPT", "positive controls")
        outputs[name] = data
        count += 22
    require(outputs["valid"] == outputs["oversized"], "identical physical bytes")
    require(report["decision"] == "DIRECT_RAW_RANGE_SPILLS_INTO_AUTHENTICATED_TAIL"
            and report["status"] == "PASS", "unmodified prospective decision")
    count += 2
    return count


def run(filename, adversarial):
    with open(filename, encoding="utf8") as f:
        report = json.load(f)
    checks = audit(report)
    refused = 0
    if adversarial:
        for path, new in (
            (("cases", "valid", "archive_sha256"), "0" * 64),
            (("cases", "oversized", "tail_prefix_hex"), "deadbeef"),
            (("cases", "oversized", "after_owner_range", "hex"), "00" * 8),
            (("cases", "oversized", "declared_logical_size"), 128),
            (("cases", "valid", "physical_sha256"), "f" * 64),
            (("cases", "valid", "in_frame_range", "hex"), "bb" * 8),
        ):
            forged = copy.deepcopy(report)
            node = forged
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = new
            try:
                audit(forged)
            except AssertionError:
                refused += 1
            else:
                raise AssertionError("forged receipt accepted: " + str(path))
        require(refused == 6, "hostile audit coverage")
    return {"status": "PASS", "independent_checks": checks,
            "forged_receipts_rejected": refused}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt")
    ap.add_argument("--adversarial", action="store_true")
    args = ap.parse_args()
    print(json.dumps(run(args.receipt, args.adversarial), sort_keys=True))
