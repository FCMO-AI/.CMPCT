#!/usr/bin/env python3
"""Independent J24G57 revision-24 wire referee: never imports cmpct.

Uses separately installed MessagePack and Zstandard to re-derive footer and
operation admission. The pytest physical court owns behavior on installed CMPCT.
This referee owns input authenticity and reproducible negative controls.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
SHA = hashlib.sha256
DCTX = zstandard.ZstdDecompressor()


def require(test, message):
    if not test:
        raise AssertionError(message)


def unpack_payload(physical: bytes, offset: int, csize: int, usize: int, codec: int):
    require(0 <= offset and 0 <= csize and offset + csize <= len(physical), "payload bounds")
    require(usize <= 2**24 and csize <= 2**24, "small test envelope")
    encoded = physical[offset:offset+csize]
    if codec == 0:
        result = encoded
    else:
        require(codec == 1, "invalid codec")
        result = DCTX.decompress(encoded, max_output_size=usize)
    require(len(result) == usize, "decoded length")
    return result


def generation(physical: bytes, offset: int):
    require(offset >= 0 and offset + FTR.size <= len(physical), "footer bounds")
    magic, kind, codec, flags, reserved, cs, us, prev, digest = FTR.unpack_from(physical, offset)
    require(magic == b"CMPTF24\x00", "footer magic")
    payload = unpack_payload(physical, offset-cs, cs, us, codec)
    authentic = SHA(payload).digest() == digest
    result = {
        "kind": kind,
        "codec": codec,
        "flags": flags,
        "reserved": reserved,
        "prev": prev,
        "payload_sha_consistent": authentic,
        "payload": msgpack.unpackb(payload, raw=False) if authentic else None,
    }
    return result


def grammar_ok(ops):
    if not isinstance(ops, list):
        return False
    for op in ops:
        if not isinstance(op, list) or not op:
            return False
        tag = op[0]
        if tag == "put":
            if len(op) != 2 or not isinstance(op[1], list) or not op[1] or not isinstance(op[1][0], str):
                return False
        elif tag == "del":
            if len(op) != 2 or not isinstance(op[1], str):
                return False
        elif tag == "ren":
            if len(op) != 3 or not all(isinstance(x, str) for x in op[1:]):
                return False
        else:
            return False
    return True


def verify(root: Path):
    names = [
        "known_delete", "unknown_only", "unknown_then_delete",
        "delete_then_unknown", "malformed_del", "malformed_ren",
        "invalid_flags", "invalid_reserved", "bad_sha",
    ]
    results = []
    tamper_rejections = 0
    for name in names:
        report = json.loads((root / f"{name}.json").read_text())
        data = (root / report["archive"]).read_bytes()
        require(SHA(data).hexdigest() == report["sha256"], f"{name}: archive sha")
        magic, version, flags, cs, us, span, digest = HDR.unpack_from(data)
        require((magic, version, flags) == (b"CMPCT24\x00", 24, 0), f"{name}: primary header")
        primary = unpack_payload(data, HDR.size, cs, us, 1)
        require(SHA(primary).digest() == digest, f"{name}: primary sha")
        root_index = msgpack.unpackb(primary, raw=False)
        require(sorted(row[0] for row in root_index["files"]) == ["a.bin", "z.bin"], f"{name}: primary paths")

        prior, latest = report["prior"], report["latest"]
        old = generation(data, prior)
        new = generation(data, latest)
        require(old["payload_sha_consistent"] and old["kind"] == 0, f"{name}: old checkpoint")
        require(sorted(x[0] for x in old["payload"]["files"]) == ["a.bin", "z.bin"], f"{name}: old state")
        require(new["kind"] == 1 and new["prev"] == prior, f"{name}: next generation linkage")
        if name == "known_delete":
            require(new["payload_sha_consistent"], "valid delete hash")
            require(new["flags"] == 0 and new["reserved"] == 0, "valid delete fields")
            require(new["payload"]["ops"] == [["del", "a.bin"]], "known delete ops")
            require(grammar_ok(new["payload"]["ops"]), "known grammar")
            require(report["decision"] == "accept_latest", "valid behavior")
        elif name.startswith("invalid_"):
            require(new["payload_sha_consistent"], "invalid-header payload must still be authentic")
            require((new["flags"], new["reserved"]) in ((1, 0), (0, 1)), "exact invalid header")
            require(report["decision"] == "recover_previous", "header behavior")
        elif name == "bad_sha":
            require(not new["payload_sha_consistent"], "bad SHA must be detected")
            require((new["flags"], new["reserved"]) == (0, 0), "SHA-only mutation")
            require(report["decision"] == "recover_previous", "digest behavior")
        else:
            require(new["payload_sha_consistent"], "unknown-op payload must be authentic")
            require((new["flags"], new["reserved"]) == (0, 0), "unknown-op footer shape")
            require(not grammar_ok(new["payload"]["ops"]), "invalid opcode grammar")
            require(report["decision"] == "reject_committed_instruction", "unknown-op behavior")

        # Tamper each physical specimen's current commit digest to ensure the
        # external referee independently detects corruption without CMPCT code.
        mutated = bytearray(data)
        # Use a different digest byte from the already-mutated bad_sha
        # specimen: toggling the same byte again would repair its checksum.
        mutated[latest + FTR.size - 2] ^= 1
        require(not generation(bytes(mutated), latest)["payload_sha_consistent"],
                f"{name}: tampered SHA not rejected")
        tamper_rejections += 1
        results.append({
            "name": name,
            "sha256": report["sha256"],
            "prior": prior,
            "latest": latest,
            "old_valid": old["payload_sha_consistent"],
            "new_payload_sha_consistent": new["payload_sha_consistent"],
            "flags": new["flags"],
            "reserved": new["reserved"],
            "decision": report["decision"],
        })

    receipt = {
        "status": "PASS",
        "subject": "revision24 signed-journal known/unknown-op and invalid footer",
        "source": "independent zstandard/msgpack physical referee (no cmpct imports)",
        "archive_count": len(results),
        "independent_digest_tamper_rejections": tamper_rejections,
        "cases": results,
    }
    (root / "independent_referee.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps({
        "status": receipt["status"],
        "archives": len(results),
        "tamper_rejections": tamper_rejections,
        "decisions": [c["name"] + ":" + c["decision"] for c in results],
    }, sort_keys=True))


if __name__ == "__main__":
    require(len(sys.argv) == 2, "usage: independent_referee.py evidence/physical")
    verify(Path(sys.argv[1]))
