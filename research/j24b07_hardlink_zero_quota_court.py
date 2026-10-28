#!/usr/bin/env python3
"""J24B07: research-only, SHA-consistent nonnegative hardlink quota undercount.

This is an expected-vulnerability scientific court, NOT a product regression test
or permission to merge an unsafe Reader. Parent #690 owns the narrow negative-size fix.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import time

import msgpack

from cmpct.builder import Builder
from cmpct.codec import (
    FTR, FMAGIC, HDR, K_FILE, K_HARDLINK, MAGIC, VERSION, sha, zc, zd
)
from cmpct.reader import CMPCT


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expect_refusal(archive: CMPCT, destination: Path, cap: int) -> str:
    try:
        archive.extractall(destination, metadata=False, max_bytes=cap)
    except IOError as exc:
        assert not destination.exists(), "quota refusal created destination"
        return str(exc)
    raise AssertionError(f"extraction unexpectedly accepted cap={cap}")


def mutate_alias(source: Path, dest: Path, declared: int) -> dict:
    original = source.read_bytes()
    magic, version, flags, csize, usize, data_size, index_sha = HDR.unpack_from(original)
    assert magic == MAGIC and version == VERSION
    index_start = HDR.size
    index_end = index_start + csize
    body_end = index_end + data_size
    encoded = original[index_start:index_end]
    index_raw = zd(encoded, usize)
    assert sha(index_raw) == index_sha
    index = msgpack.unpackb(index_raw, raw=False)
    rows = [row for row in index["files"] if row[0] == "zz-alias.bin"]
    assert len(rows) == 1 and rows[0][4] == 8192
    row = rows[0]
    original_kind = row[1]
    # On Windows the released Builder may encode a real source hardlink as
    # a second K_FILE. Convert only this alias row, preserving the body.
    if original_kind != K_HARDLINK:
        assert os.name == "nt" and original_kind == K_FILE
        row[1] = K_HARDLINK
        row[6] = ["payload.bin"]
    assert row[1] == K_HARDLINK and row[6][0] == "payload.bin"
    assert type(declared) is int and declared >= 0
    row[4] = declared
    reencoded_raw = msgpack.packb(index, use_bin_type=True)
    reencoded = zc(reencoded_raw, 12)
    new_sha = sha(reencoded_raw)
    physical = original[index_end:body_end]
    image = (
        HDR.pack(MAGIC, VERSION, flags, len(reencoded), len(reencoded_raw),
                 data_size, new_sha)
        + reencoded + physical + reencoded
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(reencoded),
                   len(reencoded_raw), 0, new_sha)
    )
    dest.write_bytes(image)
    return {
        "declared": declared, "original_alias_kind": original_kind,
        "original_index_sha256": digest(index_raw),
        "mutant_index_sha256": digest(reencoded_raw),
        "physical_sha256": digest(physical), "physical_bytes": len(physical),
        "mutant_archive_sha256": digest(image),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    t0 = time.perf_counter()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    root = out / "source"
    root.mkdir()
    payload = b"".join(
        hashlib.sha256(f"J24B07-owner-{n}".encode()).digest()
        for n in range(8192 // 32)
    )
    assert len(payload) == 8192
    (root / "payload.bin").write_bytes(payload)
    os.link(root / "payload.bin", root / "zz-alias.bin")
    assert os.path.samefile(root / "payload.bin", root / "zz-alias.bin")
    original = out / "original.cmpct"
    Builder(root, workers=1, reproducible=True).build(original)

    with CMPCT(original) as archive:
        assert archive.verify() == 2
        reject = expect_refusal(archive, out / "control-rejected", 8192)
        assert "above limit" in reject
        archive.extractall(out / "control-accepted", max_bytes=16384, metadata=False)
    assert (out / "control-accepted/payload.bin").read_bytes() == payload
    assert (out / "control-accepted/zz-alias.bin").read_bytes() == payload

    receipt = {
        "schema": "j24b07-research-v1",
        "host": platform.platform(),
        "os_name": os.name,
        "python": platform.python_version(),
        "source_reader_sha256": digest(Path(inspect.getfile(CMPCT)).read_bytes()),
        "control_archive_sha256": digest(original.read_bytes()),
        "payload_sha256": digest(payload),
        "true_logical_total": 16384,
        "original_cap_8192_rejected": True,
        "original_cap_16384_accepted": True,
        "cases": [],
    }
    for declared in (0, 1):
        hostile = out / f"alias-{declared}.cmpct"
        data = mutate_alias(original, hostile, declared)
        cap = 8192 + declared
        with CMPCT(hostile) as archive:
            data["verify_count"] = archive.verify()
            assert data["verify_count"] == 2
            data["one_byte_alias_range_hex"] = archive.read_range(
                "zz-alias.bin", 0, 1
            ).hex()
            assert data["one_byte_alias_range_hex"] == payload[:1].hex()
            data["tight_limit_error"] = expect_refusal(
                archive, out / f"tight-rejected-{declared}", cap - 1
            )
            actual = out / f"accepted-{declared}"
            archive.extractall(actual, metadata=False, max_bytes=cap)
        own = actual / "payload.bin"
        alias = actual / "zz-alias.bin"
        assert own.read_bytes() == payload and alias.read_bytes() == payload
        assert os.path.samefile(own, alias), "expected one physical inode"
        data.update({
            "accepted_cap": cap,
            "logical_extracted_bytes": own.stat().st_size + alias.stat().st_size,
            "payload_sha256": digest(own.read_bytes()),
            "alias_sha256": digest(alias.read_bytes()),
            "samefile": True,
            "quota_undercount": 8192 - declared,
        })
        assert data["logical_extracted_bytes"] > cap
        receipt["cases"].append(data)
    receipt["elapsed_seconds"] = round(time.perf_counter() - t0, 6)
    (out / "receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "decision": "CONFIRMED_NONNEGATIVE_HARDLINK_LOGICAL_QUOTA_UNDERCOUNT",
        "cases": [
            {"declared": x["declared"], "cap": x["accepted_cap"],
             "logical_extracted": x["logical_extracted_bytes"],
             "undercount": x["quota_undercount"]}
            for x in receipt["cases"]
        ],
        "source_reader_sha256": receipt["source_reader_sha256"],
        "elapsed_seconds": receipt["elapsed_seconds"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
