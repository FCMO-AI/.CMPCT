#!/usr/bin/env python3
"""J24I33: exact-source Builder directory sentinel versus native r24 admission.

Science-only: authentic nested tree, causal nil/invalid variants and flat control.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import msgpack

from cmpct.builder import Builder
from cmpct.codec import HDR, FTR, MAGIC, VERSION, FMAGIC, K_DIR, K_FILE, sha, zc, zd
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

PAYLOAD = hashlib.sha256(b"J24I33 native directory sentinel control").digest() * 19 + b"\x00end"

def require(ok: bool, what: str) -> None:
    if not ok:
        raise AssertionError(what)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def split(archive: bytes):
    magic, version, flags, cs, us, physical_len, index_sha = HDR.unpack_from(archive)
    require((magic, version, flags) == (MAGIC, VERSION, 0), "not unmodified revision-24")
    raw_index = zd(archive[HDR.size:HDR.size + cs], us)
    require(len(raw_index) == us and sha(raw_index) == index_sha, "invalid source index")
    index = msgpack.unpackb(raw_index, raw=False)
    begin = HDR.size + cs
    end = begin + physical_len
    physical = archive[begin:end]
    require(len(physical) == physical_len, "physical truncation")
    return index, physical

def resign(archive: bytes, new_sentinel) -> bytes:
    index, physical = split(archive)
    rows = [r for r in index["files"] if r[1] == K_DIR]
    require(len(rows) == 2 and all(r[5] is None and r[6] is None for r in rows),
            "not two authentic absent-digest directory rows")
    for r in rows:
        r[5] = new_sentinel
    index_wire = msgpack.packb(index, use_bin_type=True)
    compressed = zc(index_wire, 12)
    checksum = sha(index_wire)
    header = HDR.pack(MAGIC, VERSION, 0, len(compressed), len(index_wire), len(physical), checksum)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(index_wire), 0, checksum)
    rebuilt = header + compressed + physical + compressed + footer
    _, after = split(rebuilt)
    require(after == physical, "diagnostic variant modified physical payload")
    return rebuilt

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    opts = ap.parse_args()
    target = opts.output.resolve()
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24i33-") as td:
        base = Path(td)
        nested = base / "nested-tree"
        (nested / "empty").mkdir(parents=True)
        (nested / "nested").mkdir()
        (nested / "nested" / "payload.bin").write_bytes(PAYLOAD)
        flat = base / "flat-tree"
        flat.mkdir()
        (flat / "payload.bin").write_bytes(PAYLOAD)
        nested_out = base / "nested.cmpct"
        flat_out = base / "flat.cmpct"
        Builder(nested, workers=1, reproducible=True).build(nested_out)
        Builder(flat, workers=1, reproducible=True).build(flat_out)
        original = nested_out.read_bytes()
        flat_wire = flat_out.read_bytes()

    source_index, source_physical = split(original)
    source_rows = source_index["files"]
    require([(r[0], r[1]) for r in source_rows] ==
            [("empty", K_DIR), ("nested", K_DIR), ("nested/payload.bin", K_FILE)],
            "unexpected original directory tree")
    require(all(r[5] is None and r[6] is None for r in source_rows[:2]),
            "Builder unexpectedly serialized intermediate directory b''")
    require(len(source_index["blobs"]) == 1, "not one physical member")
    require(source_rows[2][5] is None, "unexpected changed direct hash policy")

    cases = {
        "real-nested": original,
        "inserted-empty": resign(original, b""),
        "invalid-one-byte": resign(original, b"X"),
        "flat": flat_wire,
    }
    records = []
    for name, wire in cases.items():
        path = target / (name + ".cmpct")
        path.write_bytes(wire)
        expected_ok = name != "invalid-one-byte"
        try:
            preflight_archive(path)
            with CMPCT(path) as archive:
                member = "payload.bin" if name == "flat" else "nested/payload.bin"
                require(archive.read(member) == PAYLOAD, name + ": wrong logical payload")
                verified = archive.verify()
            python_ok, error = True, None
        except Exception as exc:
            python_ok, verified = False, None
            error = type(exc).__name__ + ": " + str(exc)
        require(python_ok == expected_ok, name + ": wrong Python result " + str(error))
        if python_ok:
            require(verified == 1, name + ": expected one verified regular file")
        index, physical = split(wire)
        if name != "flat":
            require(physical == source_physical, name + ": changed physical bytes")
        records.append({
            "case": name,
            "archive_sha256": digest(wire),
            "physical_sha256": digest(physical),
            "directory_hash_hex": [r[5].hex() if isinstance(r[5], bytes) else None
                                   for r in index["files"] if r[1] == K_DIR],
            "python_accepted": python_ok,
            "python_verified_regular": verified,
            "python_error": error,
            "entry_kinds": [r[1] for r in index["files"]],
        })
    receipt = {
        "schema": "cmpct-j24i33-authentic-directory-admission-v1",
        "science_only": True,
        "source_physical_sha256": digest(source_physical),
        "source_payload_sha256": digest(PAYLOAD),
        "cases": records,
    }
    (target / "python-observations.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
