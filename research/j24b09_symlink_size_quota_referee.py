#!/usr/bin/env python3
"""Detached J24B09 evidence court: no CMPCT imports or experiment imports.

Uses independent stdlib wire parsing + external zstandard/msgpack. Validates
the complete source archive, both signed indexes, every physical blob, exact
single-field mutation, and the extracted-byte claims made by the experiment.
"""
from __future__ import annotations

import argparse
import binascii
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
MAIN_SHA = "80c358f8824ec1b20d349c92ed94c898090969b0"
PARENT = "adcf38cb5be022567c1faf6538aefeef2f6b72de"
READER_BLOB = "20f6e257a07a61a4c1aebe23ae23e4109d6c41c8"
TARGET = b"payload.bin"
PAYLOAD_BYTES = 8192


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def decompress(comp: bytes, codec: int, size: int) -> bytes:
    if codec == 0:
        raw = comp
    elif codec == 1:
        raw = zstd.ZstdDecompressor().decompress(comp, max_output_size=size)
    elif codec == 4:
        raw = zlib.decompress(comp, -15)
    else:
        raise ValueError(f"unexpected physical codec {codec}")
    require(len(raw) == size, "physical payload length mismatch")
    return raw


def parse(raw: bytes) -> dict:
    require(len(raw) >= HDR.size + FTR.size, "truncated archive")
    magic, revision, flags, cs, us, ds, index_digest = HDR.unpack_from(raw)
    require(magic == b"CMPCT24\0" and revision == 24 and flags == 0,
            "invalid revision/flags")
    base = HDR.size + cs
    require(base + ds + cs + FTR.size == len(raw),
            "single-generation physical framing mismatch")
    encoded = raw[HDR.size:base]
    index_raw = zstd.ZstdDecompressor().decompress(encoded, max_output_size=us)
    require(len(index_raw) == us and hashlib.sha256(index_raw).digest() == index_digest,
            "primary index SHA/length mismatch")
    foot = FTR.unpack_from(raw, len(raw) - FTR.size)
    fm, kind, codec, ff, res, tail_cs, tail_us, prev, tail_sha = foot
    require((fm, kind, codec, ff, res, tail_cs, tail_us, prev, tail_sha)
            == (b"CMPTF24\0", 0, 1, 0, 0, cs, us, 0, index_digest),
            "tail footer metadata mismatch")
    require(encoded == raw[base + ds:base + ds + cs],
            "duplicate compressed index differs")
    index = msgpack.unpackb(index_raw, raw=False)
    require(isinstance(index, dict), "index not mapping")
    physical = raw[base:base + ds]
    blobs = []
    for n, row in enumerate(index["blobs"]):
        require(len(row) == 5, f"blob table width at {n}")
        off, uncompressed, compressed, codec, meta_len = row
        require(type(off) is int and 0 <= off <= ds - BHDR.size,
                "invalid blob offset")
        bm, bc, flags, reserved, bu, bs, bm_len, crc, digest = BHDR.unpack_from(physical, off)
        require((bm, bc, bu, bs, bm_len) ==
                (b"CMA4", codec, uncompressed, compressed, meta_len),
                "blob/header mismatch")
        start = off + BHDR.size + meta_len
        require(start + bs <= len(physical), "blob crosses physical span")
        payload = decompress(physical[start:start + bs], bc, bu)
        require((binascii.crc32(payload) & 0xffffffff) == crc,
                "decoded payload CRC32 mismatch")
        require(hashlib.sha256(payload).digest() == digest,
                "decoded payload SHA256 mismatch")
        blobs.append(payload)
    rows = {x[0]: x for x in index["files"]}
    require(len(rows) == 2 and {"offset-link", "payload.bin"} == set(rows),
            "unexpected logical tree")
    link, file = rows["offset-link"], rows["payload.bin"]
    require(link[1] == 2 and file[1] == 0, "unexpected logical kinds")
    require(link[6][0] == 0 and file[6][0] == 0, "unexpected logical storage")
    require(blobs[link[6][1]] == TARGET, "actual link target byte mismatch")
    require(len(blobs[file[6][1]]) == PAYLOAD_BYTES, "payload length mismatch")
    return {"index": index, "rows": rows, "physical": physical,
            "payload": blobs[file[6][1]], "target": blobs[link[6][1]],
            "source_sha256": sha(raw)}


def accepted(result: dict, payload_sha: str) -> bool:
    return (result.get("exception") is None and result.get("published") is True
            and result.get("file_bytes") == PAYLOAD_BYTES
            and result.get("file_sha256") == payload_sha
            and result.get("link_target") == TARGET.decode()
            and result.get("destination_exists") is True)


def rejected(result: dict) -> bool:
    return (result.get("exception") is not None and result.get("published") is False
            and result.get("destination_exists") is False
            and result.get("link_target") is None)


def audit(folder: Path, receipt: dict) -> str:
    require(receipt["schema"] == "j24b09-signed-symlink-v1", "schema mismatch")
    require(receipt["product_promotion"] is False, "false product claim")
    require(receipt["source"]["parent"] == PARENT, "wrong base")
    require(receipt["source"]["reader_blob"] == READER_BLOB, "wrong Reader blob")
    source_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    require(receipt["source"]["head"] == source_head, "wrong research HEAD")
    pinned = subprocess.check_output(["git", "show", f"{PARENT}:src/cmpct/reader.py"])
    pinned_blob = subprocess.check_output(
        ["git", "hash-object", "--stdin"], input=pinned
    ).decode().strip()
    require(pinned_blob == READER_BLOB, "pinned Reader changed")
    require(receipt["source"]["installed_reader_sha256"] == sha(pinned),
            "installed Reader witness does not match original")
    raw_source = (folder / "source-payload.bin").read_bytes()
    require(len(raw_source) == PAYLOAD_BYTES and
            sha(raw_source) == receipt["source_payload_sha256"], "bad source payload")
    decoded = {}
    for label in ("baseline", "zero", "one"):
        raw = (folder / (label + ".cmpct")).read_bytes()
        require(sha(raw) == receipt["archives"][label]["sha256"], "archive SHA altered")
        require(len(raw) == receipt["archives"][label]["bytes"], "archive bytes altered")
        decoded[label] = parse(raw)
        require(decoded[label]["payload"] == raw_source, "archive payload differs from source")
    base = decoded["baseline"]
    require(base["rows"]["offset-link"][4] == len(TARGET), "original link length")
    require(base["rows"]["payload.bin"][4] == PAYLOAD_BYTES, "original file length")
    ref_index = copy.deepcopy(base["index"])
    ref_physical = base["physical"]
    for label, size in (("zero", 0), ("one", 1)):
        record = decoded[label]
        require(record["physical"] == ref_physical, "physical records mutated")
        test_index = copy.deepcopy(record["index"])
        test_link = [r for r in test_index["files"] if r[0] == "offset-link"]
        require(len(test_link) == 1 and type(test_link[0][4]) is int and
                test_link[0][4] == size, "mutant declared length mismatch")
        test_link[0][4] = len(TARGET)
        require(test_index == ref_index, "additional logical index field changed")
    require(receipt["true_symlink_bytes"] == len(TARGET) and
            receipt["declared_symlink_lengths"] ==
            {"baseline": len(TARGET), "zero": 0, "one": 1},
            "receipt claims wrong on-disk lengths")
    require(receipt["symlink_target"] == TARGET.decode(), "receipt link target altered")
    cases = receipt["results"]
    expected = {
        "honest_low": PAYLOAD_BYTES,
        "honest_full": PAYLOAD_BYTES + len(TARGET),
        "zero_cap_8192": PAYLOAD_BYTES,
        "one_cap_8193": PAYLOAD_BYTES + 1,
        "zero_too_low": PAYLOAD_BYTES - 1,
        "zero_unlimited": None,
    }
    require(set(cases) == set(expected), "missing or added case")
    for name, cap in expected.items():
        case = cases[name]
        require(case["cap"] == cap, "reported budget altered")
        require(case["verified"] == 2 and
                case["read_link"] == TARGET.decode() and
                case["read_file_sha256"] == sha(raw_source),
                "Reader exactness receipt mismatch")
    require(rejected(cases["honest_low"]) and
            accepted(cases["honest_full"], sha(raw_source)) and
            rejected(cases["zero_too_low"]) and
            accepted(cases["zero_unlimited"], sha(raw_source)),
            "legitimate source/limit control mismatch")
    found = accepted(cases["zero_cap_8192"], sha(raw_source)) and \
            accepted(cases["one_cap_8193"], sha(raw_source))
    refused = rejected(cases["zero_cap_8192"]) and \
              rejected(cases["one_cap_8193"])
    require(found or refused, "mutant results are partial/contradictory")
    outcome = ("CONFIRMED_NONNEGATIVE_SYMLINK_QUOTA_UNDERCOUNT" if found
               else "FALSIFIED_BY_VALIDATION")
    require(receipt["scientific_decision"] == outcome, "false decision")
    return outcome


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", type=Path, required=True)
    args = ap.parse_args()
    r = json.loads((args.artifact_dir / "receipt.json").read_text())
    verdict = audit(args.artifact_dir, r)
    tests = [
        lambda x: x["source"].__setitem__("reader_blob", "0"*40),
        lambda x: x["archives"]["zero"].__setitem__("sha256", "f"*64),
        lambda x: x["declared_symlink_lengths"].__setitem__("zero", 11),
        lambda x: x["results"]["zero_cap_8192"].__setitem__("exception", "IOError: forged"),
        lambda x: x.__setitem__("symlink_target", "different"),
        lambda x: x["results"]["honest_low"].__setitem__("destination_exists", True),
        lambda x: x.__setitem__("scientific_decision", "FALSIFIED_BY_VALIDATION"
                               if verdict.startswith("CONFIRMED") else
                               "CONFIRMED_NONNEGATIVE_SYMLINK_QUOTA_UNDERCOUNT"),
    ]
    for i, attack in enumerate(tests):
        tampered = copy.deepcopy(r)
        attack(tampered)
        try:
            audit(args.artifact_dir, tampered)
        except (ValueError, KeyError, AssertionError):
            continue
        raise AssertionError(f"forged evidence {i} accepted")
    print(json.dumps({"verdict": verdict, "independent_physical_decodes": 3,
                      "forged_receipts_rejected": len(tests),
                      "source_sha256": sha((args.artifact_dir/"source-payload.bin").read_bytes())},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
