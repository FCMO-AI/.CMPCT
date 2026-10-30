#!/usr/bin/env python3
"""J24G56 independent signed-wire referee; deliberately imports no CMPCT code.

Checks primary r24 index SHA, authentic latest footer SHA and exact signed
operation tags, and rejects deliberately altered physical samples. This
cannot establish Reader/preflight semantics alone; installed-package pytest
establishes that separately on the same archived samples.
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
FMAGIC = b"CMPTF24\x00"


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def decode(encoded: bytes, usize: int, codec: int) -> bytes:
    if codec == 0:
        return encoded
    assert codec == 1, f"unknown footer codec {codec}"
    return zstandard.ZstdDecompressor().decompress(encoded, max_output_size=usize)


def read_base(data: bytes) -> dict:
    if len(data) < HDR.size:
        raise ValueError("short header")
    magic, version, flags, cs, us, span, digest = HDR.unpack_from(data)
    if magic != b"CMPCT24\x00" or version != 24 or flags:
        raise ValueError("bad r24 header")
    if cs <= 0 or us <= 0 or HDR.size + cs + span > len(data):
        raise ValueError("invalid primary span")
    primary = zstandard.ZstdDecompressor().decompress(
        data[HDR.size : HDR.size + cs], max_output_size=us
    )
    if len(primary) != us or sha(primary) != digest:
        raise ValueError("primary index SHA mismatch")
    index = msgpack.unpackb(primary, raw=False)
    if not isinstance(index, dict) or "files" not in index:
        raise ValueError("primary index malformed")
    return index


def read_last(data: bytes) -> dict:
    if len(data) < FTR.size:
        raise ValueError("short footer")
    pos = len(data) - FTR.size
    magic, kind, codec, flags, reserved, cs, us, prev, digest = FTR.unpack_from(data, pos)
    if magic != FMAGIC or kind != 1 or flags or reserved:
        raise ValueError("bad latest footer")
    if cs <= 0 or us <= 0 or cs > pos or prev >= pos:
        raise ValueError("invalid generation geometry")
    raw = decode(data[pos - cs : pos], us, codec)
    if len(raw) != us or sha(raw) != digest:
        raise ValueError("journal generation SHA mismatch")
    delta = msgpack.unpackb(raw, raw=False)
    if not isinstance(delta, dict) or delta.get("blobs") != []:
        raise ValueError("unexpected journal representation")
    return {"footer_offset": pos, "prev": prev, "ops": delta.get("ops", [])}


def main() -> None:
    root = Path(sys.argv[1])
    expected = {
        "known_delete": [["del", "a.bin"]],
        "unknown_only": [["future_op", "z.bin"]],
        "unknown_then_delete": [["future_op", "z.bin"], ["del", "a.bin"]],
        "delete_then_unknown": [["del", "a.bin"], ["future_op", "z.bin"]],
    }
    results = []
    for label, ops in expected.items():
        data = (root / (label + ".cmpct")).read_bytes()
        receipt = json.loads((root / (label + ".json")).read_text())
        assert sha(data).hex() == receipt["sha256"], label
        base = read_base(data)
        assert sorted(row[0] for row in base["files"]) == ["a.bin", "z.bin"], label
        last = read_last(data)
        assert last["ops"] == ops, (label, last["ops"])
        assert last["footer_offset"] == receipt["reader"]["selected_footer"]
        assert last["prev"] < last["footer_offset"]
        assert receipt["preflight"] == (
            "accepts_new_footer" if label == "known_delete"
            else "rejects_supported_physical_footer_unsupported_operation"
        )
        results.append({"label": label, **last, "sha256": receipt["sha256"]})

        # Mutating a payload byte or the digest is not equivalent to an unknown
        # authenticated opcode; both must fail independently, including when
        # decompression throws.
        for location in ("payload", "digest"):
            altered = bytearray(data)
            offset = last["footer_offset"] - 1 if location == "payload" else len(data) - 1
            altered[offset] ^= 1
            try:
                read_last(altered)
            except Exception:
                pass
            else:
                raise AssertionError(f"{label}: {location} tamper accepted")

    corrupt = (root / "corrupt_footer.cmpct").read_bytes()
    read_base(corrupt)
    try:
        read_last(corrupt)
    except ValueError as exc:
        assert "SHA mismatch" in str(exc), str(exc)
    else:
        raise AssertionError("corrupted signed footer accepted")
    invalid_header = []
    for field, expected_flags, expected_reserved in (
        ("flags", 1, 0), ("reserved", 0, 1)
    ):
        label = "footer_nonzero_" + field
        data = (root / (label + ".cmpct")).read_bytes()
        receipt = json.loads((root / (label + ".json")).read_text())
        assert sha(data).hex() == receipt["sha256"]
        read_base(data)
        pos = len(data) - FTR.size
        magic, kind, codec, flags, reserved, cs, us, prev, digest = FTR.unpack_from(data, pos)
        assert magic == FMAGIC
        assert (kind, flags, reserved) == (1, expected_flags, expected_reserved)
        assert cs > 0 and us > 0 and cs <= pos and prev < pos
        raw = decode(data[pos - cs : pos], us, codec)
        assert len(raw) == us and sha(raw) == digest
        signed_delta = msgpack.unpackb(raw, raw=False)
        assert signed_delta["ops"] == [["del", "a.bin"]]
        assert receipt["reader"]["selected_footer"] == pos
        assert receipt["preflight"] == "recovers_prior_valid_footer"
        # Format admission is independent of the payload digest. The strict
        # independent footer referee must reject a reserved header bit.
        try:
            read_last(data)
        except ValueError as exc:
            assert "bad latest footer" in str(exc), str(exc)
        else:
            raise AssertionError(f"{label}: invalid footer admitted")
        invalid_header.append({
            "label": label,
            "footer_offset": pos,
            "previous_footer": prev,
            "content_sha256": digest.hex(),
            "flags": flags,
            "reserved": reserved,
            "sha256": receipt["sha256"],
        })
    out = {"question": "J24G56 authenticated unsupported-op replay mismatch",
           "archive_count": len(results) + 3, "authenticated_op_samples": results,
           "invalid_footer_header_samples": invalid_header,
           "tamper_controls_rejected": 2 * len(results) + 3,
           "claim": "wire-only; Reader/preflight outcome comes from installed tests"}
    (root / "independent_wire_referee.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
