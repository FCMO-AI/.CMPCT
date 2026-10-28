#!/usr/bin/env python3
"""J24B07 independent wire and filesystem referee (no CMPCT imports).

The scientific court may return SUCCESS because a safety defect was reproduced.
This referee verifies the claimed *counterexample*, not a successful product fix.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
MAGIC = b"CMPCT24\0"
FMAGIC = b"CMPTF24\0"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def must(pred: bool, label: str) -> None:
    if not pred:
        raise AssertionError(label)


def parse(path: Path) -> dict:
    raw = path.read_bytes()
    magic, version, flags, cs, us, ds, claimed = HDR.unpack_from(raw)
    must(magic == MAGIC and version == 24, "header/format")
    must(0 < cs < len(raw) and 0 < us < 16_000_000, "index bounds")
    p = HDR.size
    encoded = raw[p:p + cs]
    physical = raw[p + cs:p + cs + ds]
    must(len(physical) == ds, "physical length")
    footer_start = p + cs + ds + cs
    must(footer_start + FTR.size == len(raw), "exact footer position")
    must(raw[p + cs + ds:footer_start] == encoded, "tail index identity")
    fm, kind, codec, ff, reserved, tcs, tus, prev, fsha = FTR.unpack_from(
        raw, footer_start
    )
    must(fm == FMAGIC and kind == 0 and codec == 1, "footer grammar")
    must(tcs == cs and tus == us and prev == 0, "footer lengths/ancestry")
    must(fsha == claimed, "footer vs header SHA")
    index_raw = zstandard.ZstdDecompressor().decompress(
        encoded, max_output_size=us
    )
    must(len(index_raw) == us, "decoded index length")
    must(hashlib.sha256(index_raw).digest() == claimed, "index SHA")
    index = msgpack.unpackb(index_raw, raw=False)
    must(type(index) is dict and type(index.get("files")) is list, "index shape")
    return {
        "raw_sha": h(raw), "index_sha": h(index_raw),
        "index": index, "physical": physical, "physical_sha": h(physical),
        "physical_bytes": ds,
    }


def row(index: dict, name: str) -> list:
    rows = [r for r in index["files"] if r[0] == name]
    must(len(rows) == 1, "unique expected member")
    return rows[0]


def audit(out: Path, rec: dict) -> None:
    must(rec["schema"] == "j24b07-research-v1", "schema")
    must(rec["true_logical_total"] == 16384, "expected logical total")
    must(rec["original_cap_8192_rejected"] is True, "control refusal")
    must(rec["original_cap_16384_accepted"] is True, "control success")
    must(rec["source_reader_sha256"] ==
         h(Path("src/cmpct/reader.py").read_bytes()), "source lock")
    source = out / "source/payload.bin"
    must(source.exists() and source.stat().st_size == 8192, "source exists")
    payload = source.read_bytes()
    must(rec["payload_sha256"] == h(payload), "payload SHA")
    original = parse(out / "original.cmpct")
    must(rec["control_archive_sha256"] == original["raw_sha"], "control image SHA")
    must(not (out / "control-rejected").exists(), "control output absent")
    must((out / "control-accepted/payload.bin").read_bytes() == payload,
         "control owner bytes")
    must((out / "control-accepted/zz-alias.bin").read_bytes() == payload,
         "control alias bytes")
    original_alias = row(original["index"], "zz-alias.bin")
    original_owner = row(original["index"], "payload.bin")
    must(original_alias[4] == 8192 and original_owner[4] == 8192,
         "original two full logical sizes")
    must(len(rec["cases"]) == 2, "two hostile cases")
    must(sorted(x["declared"] for x in rec["cases"]) == [0, 1],
         "nonnegative cases")
    for case in rec["cases"]:
        declared = case["declared"]
        must(type(declared) is int and declared in (0, 1), "declared type")
        mutant = parse(out / f"alias-{declared}.cmpct")
        must(case["mutant_archive_sha256"] == mutant["raw_sha"], "mutant image SHA")
        must(case["mutant_index_sha256"] == mutant["index_sha"], "mutant index SHA")
        must(case["original_index_sha256"] == original["index_sha"],
             "original index SHA")
        must(mutant["physical"] == original["physical"], "physical bytes intact")
        must(case["physical_sha256"] == mutant["physical_sha"],
             "physical SHA")
        must(case["physical_bytes"] == mutant["physical_bytes"],
             "physical length")
        m_alias = row(mutant["index"], "zz-alias.bin")
        must(m_alias[1] == 3 and m_alias[4] == declared,
             "hardlink nonnegative malformed size")
        must(m_alias[6] == ["payload.bin"], "hardlink target")
        must(row(mutant["index"], "payload.bin") == original_owner,
             "physical owner metadata unchanged")
        normalized = copy.deepcopy(mutant["index"])
        normalized_alias = row(normalized, "zz-alias.bin")
        normalized_alias[1] = original_alias[1]
        normalized_alias[4] = original_alias[4]
        normalized_alias[6] = original_alias[6]
        must(normalized == original["index"],
             "only alias type/storage exception and size may differ")
        must(case["original_alias_kind"] == original_alias[1],
             "original kind provenance")
        if os.name != "nt":
            must(original_alias[1] == 3, "POSIX genuine hardlink")
        else:
            must(original_alias[1] in (0, 3), "Windows hardlink variant")
        cap = 8192 + declared
        must(case["accepted_cap"] == cap and case["quota_undercount"] ==
             8192 - declared, "charged vs actual logical bytes")
        must(case["verify_count"] == 2, "Reader verification count")
        must(case["logical_extracted_bytes"] == 16384, "logical bytes")
        must(case["logical_extracted_bytes"] > cap, "positive quota bypass")
        must(case["one_byte_alias_range_hex"] == payload[:1].hex(),
             "aliased range beyond claimed end")
        must("above limit" in case["tight_limit_error"],
             "tight negative budget")
        must(not (out / f"tight-rejected-{declared}").exists(),
             "tight refusal before filesystem effects")
        own = out / f"accepted-{declared}/payload.bin"
        alias = out / f"accepted-{declared}/zz-alias.bin"
        must(own.read_bytes() == payload and alias.read_bytes() == payload,
             "two intact 8192-byte paths")
        must(os.path.samefile(own, alias) and case["samefile"] is True,
             "true hardlink not duplicate disk allocation")
        must(case["payload_sha256"] == h(payload) and
             case["alias_sha256"] == h(payload), "extracted content hashes")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    receipt = json.loads((args.out / "receipt.json").read_text(encoding="utf-8"))
    audit(args.out, receipt)
    altered = 0
    for field, bad in [
        ("payload_sha256", "0" * 64),
        ("source_reader_sha256", "0" * 64),
        ("control_archive_sha256", "0" * 64),
        ("true_logical_total", 8192),
    ]:
        tampered = copy.deepcopy(receipt)
        tampered[field] = bad
        try:
            audit(args.out, tampered)
        except AssertionError:
            altered += 1
        else:
            raise AssertionError(f"forged {field} receipt accepted")
    for field, bad in [
        ("physical_sha256", "0" * 64),
        ("mutant_index_sha256", "0" * 64),
        ("logical_extracted_bytes", 8192),
        ("accepted_cap", 16384),
    ]:
        tampered = copy.deepcopy(receipt)
        tampered["cases"][0][field] = bad
        try:
            audit(args.out, tampered)
        except AssertionError:
            altered += 1
        else:
            raise AssertionError(f"forged case {field} accepted")
    print(json.dumps({
        "independent_referee": "PASS",
        "signed_images_and_physical_owner": "PASS",
        "logical_quota_bypass_cases": 2,
        "forged_receipts_rejected": altered,
        "product_promotion": "NONE",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
