#!/usr/bin/env python3
"""Hostile, independent r24 oracle: source changes *after* Deflate ZIP-export preflight.

Research only. Source and target are anonymous temporary files. The production
Reader is unmodified; the test hook delegates to its original verifier first.
The experiment intentionally expects a correctness negative, not a product pass.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import struct
import tempfile
import zipfile
import zlib
from pathlib import Path

import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_DEFLATE, FMAGIC, FTR, HDR, K_FILE,
    LFH, MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def make_archive(path: Path, names: tuple[str, ...]) -> dict:
    """Assemble authentic revision-24 direct-Deflate, independent of Builder."""
    raw = b"source-byte-identity-must-survive-export-boundaries!\n" * 25
    compressor = zlib.compressobj(0, zlib.DEFLATED, -15)
    compressed = compressor.compress(raw) + compressor.flush()
    assert len(raw) < 65535
    assert len(compressed) == len(raw) + 5
    assert compressed[0] == 1  # final RFC1951 stored block; byte 5 begins data
    assert zlib.decompress(compressed, -15) == raw
    crc = binascii.crc32(raw) & 0xffffffff
    blob = BHDR.pack(
        BMAGIC, CODEC_DEFLATE, 0, 0, len(raw), len(compressed), 0,
        crc, sha(raw),
    ) + compressed
    files = [
        [name, K_FILE, 0o644, 0, len(raw), None, [S_BLOB, 0]]
        for name in sorted(names)
    ]
    index = {
        "v": VERSION, "files": files,
        "blobs": [[0, len(raw), len(compressed), CODEC_DEFLATE, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    unpacked = msgpack.packb(index, use_bin_type=True)
    packed = zc(unpacked, 12)
    physical_start = HDR.size + len(packed) + BHDR.size
    path.write_bytes(
        HDR.pack(MAGIC, VERSION, 0, len(packed), len(unpacked), len(blob), sha(unpacked))
        + packed + blob + packed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed), len(unpacked), 0, sha(unpacked))
    )
    return {
        "raw": raw, "stream": compressed, "physical_start": physical_start,
        "mutate_offset": physical_start + 5 + 19, "crc": crc,
        "source_initial_sha": digest(path.read_bytes()),
    }


def mutate_source(source: Path, info: dict) -> dict:
    """In-place write through a second OS handle; no truncation, index, or SHA edit."""
    absolute = info["mutate_offset"]
    prior = source.read_bytes()[absolute]
    changed = prior ^ 0x01
    with open(source, "r+b", buffering=0) as writable:
        writable.seek(absolute)
        assert writable.write(bytes([changed])) == 1
        os.fsync(writable.fileno())
    stored = source.read_bytes()
    physical = stored[info["physical_start"]:info["physical_start"] + len(info["stream"])]
    logical = zlib.decompress(physical, -15)
    assert logical != info["raw"] and len(logical) == len(info["raw"])
    assert binascii.crc32(logical) & 0xffffffff != info["crc"]
    assert len(physical) == len(info["stream"])
    return {
        "source_mutated_sha": digest(stored),
        "original_byte": prior, "altered_byte": changed,
        "physical_stream_sha": digest(physical),
        "logical_mutated_sha": digest(logical),
    }


def independent_zip_verdict(target: Path, names: tuple[str, ...]) -> dict:
    """Separate parser, raw stream comparisons and decoded member verification."""
    result = {"exists": target.exists()}
    if not target.exists():
        return result
    artifact = target.read_bytes()
    result["zip_sha256"] = digest(artifact)
    result["zip_bytes"] = len(artifact)
    with zipfile.ZipFile(target) as z:
        result["central_names"] = z.namelist()
        result["members"] = {}
        for name in names:
            item = z.getinfo(name)
            local = LFH.unpack_from(artifact, item.header_offset)
            start = item.header_offset + LFH.size + local[-2] + local[-1]
            stored = artifact[start:start + item.compress_size]
            try:
                decoded = z.read(name)
                outcome = {"read": "accepted", "logical_sha256": digest(decoded)}
            except Exception as exc:
                outcome = {"read": "rejected", "exception": type(exc).__name__}
            outcome.update({
                "raw_deflate_sha256": digest(stored),
                "independent_inflate_sha256": digest(zlib.decompress(stored, -15)),
                "crc32_header": item.CRC,
                "compressed_bytes": item.compress_size,
            })
            result["members"][name] = outcome
    return result


def run_one(root: Path, variant: str, names: tuple[str, ...]) -> dict:
    directory = root / variant
    directory.mkdir()
    source, target = directory / "archive.cmpct", directory / "out.zip"
    info = make_archive(source, names)
    result = {
        "case": variant, "names": names,
        "initial_source_sha256": info["source_initial_sha"],
        "original_deflate_sha256": digest(info["stream"]),
        "original_logical_sha256": digest(info["raw"]),
        "original_logical_crc32": info["crc"],
        "original_archive_bytes": source.stat().st_size,
    }
    result["mutation"] = None
    if variant == "static_prior":
        target.write_bytes(b"valuable prior output")
        result["mutation"] = mutate_source(source, info)
    with CMPCT(source) as reader:
        result["reader_initial_mmap_sha256"] = digest(reader.mm[:])
        if variant.startswith("after_preflight"):
            original = reader._verify_direct_deflate_blob

            def mutate_after_verified(index):
                original(index)  # must accept original physical data FIRST
                result["mutation"] = mutate_source(source, info)
                assert reader.mm[info["mutate_offset"]] == result["mutation"]["altered_byte"]
                result["mmap_change_visible"] = True

            reader._verify_direct_deflate_blob = mutate_after_verified
        try:
            returned = reader.export_zip(target)
            result["export"] = "returned_successfully"
            result["return_is_target"] = Path(returned) == target
        except Exception as exc:
            result["export"] = "rejected"
            result["exception"] = type(exc).__name__
    if variant == "static_prior":
        result["existing_target_preserved"] = target.read_bytes() == b"valuable prior output"
    else:
        result["zip"] = independent_zip_verdict(target, names)
    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="deflate-mutation-evidence/result.json")
    args = p.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-deflate-mmap-oracle-") as temp:
        root = Path(temp)
        cases = [
            run_one(root, "pristine", ("member.bin",)),
            run_one(root, "static_prior", ("member.bin",)),
            run_one(root, "after_preflight_single", ("member.bin",)),
            run_one(root, "after_preflight_shared", ("a.bin", "b.bin", "c.bin")),
        ]
    result = {
        "scientific_question": "Does post-verification in-place source mutation affect later copied Deflate ZIP bytes?",
        "source_head": os.environ.get("GITHUB_SHA", "local-unbound"),
        "comparison_owner": "PR #284; independent hostile research only",
        "cases": cases,
    }
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    a, b, c, d = cases
    assert a["export"] == "returned_successfully"
    assert a["zip"]["members"]["member.bin"]["read"] == "accepted"
    assert a["zip"]["members"]["member.bin"]["raw_deflate_sha256"] == a["original_deflate_sha256"]
    assert b["export"] == "rejected" and b["existing_target_preserved"]
    for case in (c, d):
        assert case["export"] == "returned_successfully" and case["mmap_change_visible"]
        assert case["zip"]["central_names"] == list(case["names"])
        for entry in case["zip"]["members"].values():
            assert entry["raw_deflate_sha256"] == case["mutation"]["physical_stream_sha"]
            assert entry["read"] == "rejected" and entry["exception"] == "BadZipFile"
            assert entry["independent_inflate_sha256"] == case["mutation"]["logical_mutated_sha"]
    print(json.dumps({
        "outcome": "STATIC_PROTECTION_PASS; POST_PREFLIGHT_MUTATION_COPY_BYPASS_REPRODUCED",
        "source_head": result["source_head"],
        "cases": [
            {"case": c["case"], "export": c["export"],
             "member_verdicts": {
                 n: o["read"] for n, o in c.get("zip", {}).get("members", {}).items()
             }}
            for c in cases
        ],
        "evidence_path": str(output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
