#!/usr/bin/env python3
"""Independent J24G25 r24 physical/ZIP referee. Does NOT import cmpct or Reader.

Requires msgpack and independently maintained zstandard. Referee checks archive
wire, duplicated authenticated indexes, physical Deflate header and payload,
logical SHA/CRC, raw trailing bytes, and standard ZIP consumption. It is not
a full independent implementation of arbitrary CMPCT archives.
"""
from __future__ import annotations

import binascii
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
LFH = struct.Struct("<IHHHHHIIIHH")
EXPECTED = {
    "clean": (0, False),
    "one_trailing_byte": (1, False),
    "two_trailing_bytes": (2, False),
    "trailing_complete_deflate_stream": (None, False),
    "corrupted_crc": (0, True),
}
READER_BLOB = "b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb"


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


CHECKS = 0


def check(condition, why: str):
    global CHECKS
    if not condition:
        raise AssertionError(why)
    CHECKS += 1


def audit_archive(wire: bytes, case: str, expected_member_sha: str) -> tuple[bytes, bytes, int, int]:
    check(len(wire) > HDR.size + BHDR.size + FTR.size, "truncated archive")
    m, ver, flags, ic, iu, ds, h = HDR.unpack_from(wire)
    check(m == b"CMPCT24\0" and ver == 24 and flags == 0, "r24 header")
    check(0 < ic < 1024 * 1024 and 0 < iu < 1024 * 1024, "bounded index")
    check(ds >= BHDR.size, "data span")
    packed = wire[HDR.size:HDR.size+ic]
    start = HDR.size + ic
    stop = start + ds
    check(stop + ic + FTR.size == len(wire), "physical header/data/tail geometry")
    check(packed == wire[stop:stop+ic], "duplicate physical index")
    f = FTR.unpack_from(wire, len(wire)-FTR.size)
    check(f[0] == b"CMPTF24\0" and (f[5], f[6], f[8]) == (ic, iu, h),
          "footer index fingerprint/length")
    clear = zstandard.ZstdDecompressor().decompress(packed, max_output_size=iu)
    check(len(clear) == iu and sha(clear) == h, "zstd index SHA")
    index = msgpack.unpackb(clear, raw=False, strict_map_key=False)
    check(index["v"] == 24, "index version")
    check(len(index["blobs"]) == len(index["files"]) == 1, "single-owner court")
    row = index["files"][0]
    check(row[0] == "member.bin" and row[1] == 0 and row[6] == [0, 0],
          "exact file/owner identity")
    blob = index["blobs"][0]
    check(blob[0] == 0 and blob[1] == row[4] and blob[3] == 4 and blob[4] == 0,
          "signed physical owner geometry")
    b = BHDR.unpack_from(wire, start)
    magic, codec, flags, res, usize, csize, metasz, crc, digest = b
    check(magic == b"CMA4" and codec == 4 and not flags and not res, "Deflate record")
    check(usize == blob[1] and csize == blob[2] and metasz == blob[4], "header/index parity")
    check(BHDR.size + metasz + csize == ds, "only physical record")
    comp = wire[start+BHDR.size+metasz:stop]
    inflater = zlib.decompressobj(-15)
    raw = inflater.decompress(comp) + inflater.flush()
    check(inflater.eof and len(raw) == usize, "Deflate logical decode")
    unused = inflater.unused_data
    check(sha(raw) == digest and sha(raw).hex() == expected_member_sha,
          "physical logical SHA")
    badcrc = EXPECTED[case][1]
    actual_crc = binascii.crc32(raw) & 0xffffffff
    check((actual_crc ^ crc) == (1 if badcrc else 0), "CRC single-bit hostile/clean")
    tail_len = EXPECTED[case][0]
    if tail_len is not None:
        check(len(unused) == tail_len, "trailer byte count")
    else:
        check(len(unused) > 3, "second raw-Deflate stream suffix")
    return raw, comp, len(unused), crc


def audit(root: Path) -> dict:
    report = json.loads((root / "report.json").read_text())
    check(report["schema"] == "cmpct-j24g25-physical-deflate-read-export-parity-v1",
          "report schema")
    check(report["installed_reader_blob"] == READER_BLOB, "exact candidate Reader")
    cases = report["cases"]
    check({x["case"] for x in cases} == set(EXPECTED) and len(cases) == 5,
          "exact case roster")
    summary = []
    for item in cases:
        case = item["case"]
        wire = (root / (case + ".cmpct")).read_bytes()
        independent = (root / (case + ".independent.zip")).read_bytes()
        emitted = (root / (case + ".export.zip")).read_bytes()
        check(sha(wire).hex() == item["r24_sha256"]
              and len(wire) == item["r24_bytes"], "archive receipt")
        raw, comp, trailer_len, crc = audit_archive(wire, case, report["member_sha256"])
        check(trailer_len == item["trailing_bytes"], "footer and report trailer")
        check(len(comp) == item["deflate_size"] and len(raw) == report["member_bytes"],
              "record logical size")
        check(sha(independent).hex() == item["independent_zip_sha256"],
              "independent ZIP receipt")
        with zipfile.ZipFile(io.BytesIO(independent)) as z:
            check(z.namelist() == ["member.bin"] and z.testzip() is None, "stdlib ZIP names/CRC")
            check(z.read("member.bin") == raw, "independent ZIP bytes")
            check(z.getinfo("member.bin").compress_size == len(comp), "ZIP compressed bytes")
        hdr = LFH.unpack_from(independent)
        start = LFH.size + hdr[9] + hdr[10]
        check(hdr[7] == len(comp) and hdr[8] == len(raw), "ZIP local geometry")
        check(independent[start:start+len(comp)] == comp, "source Deflate bitstream copied")
        check(item["read"]["status"] == ("REJECT" if case == "corrupted_crc" else "ACCEPT"),
              "Reader read control")
        check(item["verify"]["status"] == ("REJECT" if case == "corrupted_crc" else "ACCEPT"),
              "Reader verify control")
        check(item["export"]["status"] ==
              ("ACCEPT" if case == "clean" else "REJECT"), "candidate export decision")
        check(item["existing_destination_preserved"] == (case != "clean"), "output destination custody")
        check(sha(emitted).hex() == item["export_sha256"] and len(emitted) == item["export_size"],
              "emitted receipt")
        if case == "clean":
            with zipfile.ZipFile(io.BytesIO(emitted)) as z:
                check(z.read("member.bin") == raw and z.testzip() is None,
                      "candidate valid exported ZIP")
        else:
            check(emitted.startswith(b"existing-output-must-survive-rejection:"),
                  "no overwritten preexisting output")
        summary.append({"case": case, "physical_archive_sha256": sha(wire).hex(),
                        "trailing_bytes": trailer_len, "read": item["read"]["status"],
                        "verify": item["verify"]["status"], "export": item["export"]["status"]})
    check(report.get("decision") == "PR284_REJECTS_RELEASED_VALID_TRAILING_DEFLATE",
          "research decision")
    result = {"schema": "cmpct-j24g25-independent-physical-referee-v1",
              "checks": CHECKS, "status": "PASS",
              "scope": "detached physical r24, standard ZIP and reported Reader outcomes; not a second Reader",
              "cases": summary}
    (root / "referee_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), indent=2, sort_keys=True))
