#!/usr/bin/env python3
"""O3 science: stage actual emitted ZIP bytes, verify then atomically publish.

This does NOT patch CMPCT.export_zip; PR #284 owns production. Scope is direct
raw-Deflate archive members, with frozen logical commitments from open time.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

from cmpct.codec import BHDR, CODEC_DEFLATE, K_FILE, K_SYMLINK, S_BLOB
from cmpct.reader import CMPCT
from v031_deflate_mmap_mutation_o2_court import (
    digest, independent_zip_verdict, make_archive, mutate_source,
)


def freeze_expected_source(reader: CMPCT) -> dict:
    """Snapshot logically committed SHA/CRC/size before any source mutation."""
    commitments = {}
    for row in reader.files:
        name, kind, *_rest, storage = row
        if kind not in (K_FILE, K_SYMLINK) or not storage or storage[0] != S_BLOB:
            raise ValueError("O3 deliberately supports only direct Deflate")
        idx = storage[1]
        off, usize, csize, codec, mlen = reader.blobs[idx]
        if codec != CODEC_DEFLATE:
            raise ValueError("O3 deliberately supports only direct Deflate")
        header = BHDR.unpack_from(reader.mm, reader.record_base + off)
        _magic, _codec, _flags, _reserved, length, stream_size, meta_size, crc, physical_sha = header
        assert (length, stream_size, meta_size) == (usize, csize, mlen)
        commitments[name] = {
            "sha256": physical_sha.hex(), "crc32": crc,
            "length": length, "compressed_length": stream_size,
        }
    return commitments


def verify_staged_output(temp_zip: Path, commitments: dict) -> dict:
    """Verify *copied output bytes*, not earlier source mmap bytes."""
    observations = {}
    with zipfile.ZipFile(temp_zip) as reader:
        assert sorted(reader.namelist()) == sorted(commitments)
        for name, expected in commitments.items():
            item = reader.getinfo(name)
            if item.compress_type != zipfile.ZIP_DEFLATED:
                raise IOError("O3 expected exact physical Deflate retention")
            if item.file_size != expected["length"]:
                raise IOError("staged ZIP logical length mismatch")
            if item.CRC != expected["crc32"]:
                raise IOError("staged ZIP CRC field mismatch")
            strong = hashlib.sha256()
            crc = 0
            size = 0
            with reader.open(name) as member:
                while True:
                    block = member.read(65536)
                    if not block:
                        break
                    size += len(block)
                    if size > expected["length"]:
                        raise IOError("staged ZIP logical length overflow")
                    strong.update(block)
                    crc = binascii.crc32(block, crc)
            if size != expected["length"] or (crc & 0xffffffff) != expected["crc32"]:
                raise IOError("staged ZIP logical length/CRC failed")
            if strong.hexdigest() != expected["sha256"]:
                raise IOError("staged ZIP logical SHA-256 failed")
            observations[name] = {"read": "verified", "sha256": strong.hexdigest()}
    return observations


def stage_then_verify(reader: CMPCT, target: Path, commitments: dict, details: dict) -> None:
    """Research-only same-filesystem private staging; output verified before rename."""
    with tempfile.NamedTemporaryFile(
        dir=target.parent, prefix=".cmpct-zip-o3-", suffix=".zip", delete=False
    ) as temporary:
        stage = Path(temporary.name)
    details["staging_created"] = True
    try:
        reader.export_zip(stage)
        details["staging_zip_bytes"] = stage.stat().st_size
        details["precheck_zip"] = independent_zip_verdict(stage, tuple(commitments))
        details["staging_verification"] = verify_staged_output(stage, commitments)
        os.replace(stage, target)
        details["published"] = True
    finally:
        if stage.exists():
            stage.unlink()
        details["staging_cleaned"] = not stage.exists()


def scenario(root: Path, scenario_id: str, names: tuple[str, ...]) -> dict:
    folder = root / scenario_id
    folder.mkdir()
    source, target = folder / "source.cmpct", folder / "user-output.zip"
    facts = make_archive(source, names)
    previous = b"preserve-old-publication-exactly"
    target.write_bytes(previous)
    result = {
        "case": scenario_id, "names": names,
        "initial_source_sha256": facts["source_initial_sha"],
        "original_deflate_sha256": digest(facts["stream"]),
        "old_target_sha256": digest(previous),
        "mutation": None, "published": False,
    }
    if scenario_id == "static_corrupt":
        result["mutation"] = mutate_source(source, facts)
    with CMPCT(source) as reader:
        expectations = freeze_expected_source(reader)
        result["logical_commitments_sha256"] = {
            n: x["sha256"] for n, x in expectations.items()
        }
        if scenario_id.startswith("postcheck"):
            genuine_verifier = reader._verify_direct_deflate_blob

            def after_original_preflight(index):
                genuine_verifier(index)
                result["mutation"] = mutate_source(source, facts)
                assert reader.mm[facts["mutate_offset"]] == result["mutation"]["altered_byte"]
                result["mmap_change_visible"] = True

            reader._verify_direct_deflate_blob = after_original_preflight
        try:
            stage_then_verify(reader, target, expectations, result)
            result["status"] = "published_verified"
        except Exception as exc:
            result["status"] = "rejected_before_publication"
            result["failure_type"] = type(exc).__name__
        if scenario_id == "pristine":
            reference = folder / "reference.zip"
            reader.export_zip(reference)
            result["direct_zip_sha256"] = digest(reference.read_bytes())
    result["published_target_sha256"] = digest(target.read_bytes())
    result["old_target_preserved"] = target.read_bytes() == previous
    result["stage_files_remaining"] = [
        p.name for p in folder.iterdir() if p.name.startswith(".cmpct-zip-o3-")
    ]
    if result["published"]:
        result["zip"] = independent_zip_verdict(target, names)
    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="deflate-mutation-evidence/o3-result.json")
    args = p.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-deflate-stage-oracle-") as temp:
        root = Path(temp)
        cases = [
            scenario(root, "pristine", ("member.bin",)),
            scenario(root, "static_corrupt", ("member.bin",)),
            scenario(root, "postcheck_single", ("member.bin",)),
            scenario(root, "postcheck_aliases", ("a.bin", "b.bin", "c.bin")),
        ]
    evidence = {
        "scientific_question": "Can source mutation after preflight publish a bad ZIP when emitted bytes are independently verified before same-FS rename?",
        "source_head": os.environ.get("GITHUB_SHA", "local-unbound"),
        "owner": "PR #284 — production code unchanged",
        "cases": cases,
    }
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    a, b, c, d = cases
    assert a["published"] and a["status"] == "published_verified"
    assert not a["old_target_preserved"]
    assert a["published_target_sha256"] == a["direct_zip_sha256"]
    assert a["zip"]["members"]["member.bin"]["read"] == "accepted"
    for case in (b, c, d):
        assert not case["published"] and case["old_target_preserved"]
        assert case["status"] == "rejected_before_publication"
        assert case["stage_files_remaining"] == []
    for case in (c, d):
        assert case["mmap_change_visible"]
        assert all(m["read"] == "rejected" for m in case["precheck_zip"]["members"].values())
    print(json.dumps({
        "outcome": "OUTPUT_STAGE_VERIFICATION_PROTECTS_PUBLICATION_IN_TESTED_REGIME",
        "source_head": evidence["source_head"],
        "case_results": [
            {"case": r["case"], "status": r["status"],
             "old_target_preserved": r["old_target_preserved"],
             "stage_leaks": len(r["stage_files_remaining"])}
            for r in cases
        ], "evidence_path": str(output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
