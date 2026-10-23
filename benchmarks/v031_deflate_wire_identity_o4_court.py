#!/usr/bin/env python3
"""O4 bounded mechanism oracle: bind Deflate verifier input bytes to copied bytes.

Not a CMPCT ZIP exporter; a detached raw-stream custody experiment. It reads a
real builder-independent r24 archive and authenticates the same input chunks it
hashes. All target writes are private-temp -> verified atomic rename.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import tempfile
import zlib
from pathlib import Path

from cmpct.codec import BHDR, BMAGIC, CODEC_DEFLATE
from cmpct.reader import CMPCT
from v031_deflate_mmap_mutation_o2_court import digest, make_archive


def verify_once_with_wire_sha(reader: CMPCT, idx: int) -> dict:
    off, expected_us, cs, codec, mlen = reader.blobs[idx]
    if codec != CODEC_DEFLATE:
        raise IOError("not direct raw Deflate")
    pos = reader.record_base + off
    magic, record_codec, _flags, _reserved, usize, compressed_size, metadata_size, expected_crc, expected_sha = BHDR.unpack_from(reader.mm, pos)
    if magic != BMAGIC or record_codec != CODEC_DEFLATE or (usize, compressed_size, metadata_size) != (expected_us, cs, mlen):
        raise IOError("record framing mismatch")
    start = pos + BHDR.size + mlen
    end = start + cs
    if end > len(reader.mm):
        raise IOError("physical range outside archive")
    inflater = zlib.decompressobj(-15)
    wire_sha = hashlib.sha256()
    logical_sha = hashlib.sha256()
    crc = 0
    total = 0
    cursor = start
    max_input_chunk = 0
    while cursor < end:
        incoming = reader.mm[cursor:min(cursor + 65536, end)]
        cursor += len(incoming)
        max_input_chunk = max(max_input_chunk, len(incoming))
        wire_sha.update(incoming)  # EXACT SAME IMMUTABLE bytes fed to inflater
        while True:
            previous = len(incoming)
            block = inflater.decompress(incoming, 65536)
            incoming = inflater.unconsumed_tail
            total += len(block)
            if total > usize:
                raise IOError("uncompressed bytes exceed commitment")
            logical_sha.update(block)
            crc = binascii.crc32(block, crc)
            if inflater.eof:
                if incoming or inflater.unused_data or cursor != end:
                    raise IOError("trailing compressed bytes")
                break
            if incoming:
                if not block and len(incoming) >= previous:
                    raise IOError("decoder stalled")
                continue
            if len(block) == 65536:
                incoming = b""
                continue
            break
    if not inflater.eof or total != usize or crc & 0xffffffff != expected_crc or logical_sha.digest() != expected_sha:
        raise IOError("logical SHA/CRC/size does not match physical blob header")
    return {
        "wire_sha256": wire_sha.hexdigest(),
        "logical_sha256": logical_sha.hexdigest(),
        "logical_crc32": crc & 0xffffffff,
        "logical_bytes_inflated": total,
        "compressed_bytes_hashed": cs,
        "max_input_chunk": max_input_chunk,
        "start": start, "end": end,
    }


def flip_payload(path: Path, facts: dict, raw_byte_delta: int) -> dict:
    address = facts["physical_start"] + 5 + raw_byte_delta
    with open(path, "r+b", buffering=0) as writer:
        writer.seek(address)
        previous = writer.read(1)
        assert len(previous) == 1
        writer.seek(address)
        writer.write(bytes([previous[0] ^ 1]))
        os.fsync(writer.fileno())
    source = path.read_bytes()
    compressed = source[facts["physical_start"]:facts["physical_start"] + len(facts["stream"])]
    decoded = zlib.decompress(compressed, -15)
    assert len(decoded) == len(facts["raw"])
    return {
        "offset": address,
        "prior_byte": previous[0],
        "current_byte": previous[0] ^ 1,
        "source_sha256": digest(source),
        "copied_source_stream_sha256": digest(compressed),
        "logical_content_sha256": digest(decoded),
    }


def publish_if_wire_equal(reader: CMPCT, target: Path, identity: dict, details: dict, *,
                          mutate_on_chunk=None) -> None:
    """The *written* immutable Python bytes are the wire-SHA input."""
    with tempfile.NamedTemporaryFile(
        dir=target.parent, prefix=".cmpct-wire-stage-", suffix=".deflate", delete=False
    ) as temporary:
        stage = Path(temporary.name)
    copied_sha = hashlib.sha256()
    copied = 0
    largest = 0
    try:
        with open(stage, "wb") as output:
            for cursor in range(identity["start"], identity["end"], 256):
                block = reader.mm[cursor:min(cursor + 256, identity["end"])]
                largest = max(largest, len(block))
                assert output.write(block) == len(block)
                copied_sha.update(block)  # SAME immutable bytes object as f.write()
                copied += len(block)
                if mutate_on_chunk is not None and copied >= 256:
                    mutate_on_chunk()
                    mutate_on_chunk = None
        details["copied_wire_sha256"] = copied_sha.hexdigest()
        details["copied_bytes"] = copied
        details["max_copy_chunk"] = largest
        details["staged_stream_sha256"] = digest(stage.read_bytes())  # diagnostics only
        assert details["copied_wire_sha256"] == details["staged_stream_sha256"]
        details["staged_logical_sha256"] = digest(zlib.decompress(stage.read_bytes(), -15))
        if copied != identity["compressed_bytes_hashed"] or copied_sha.hexdigest() != identity["wire_sha256"]:
            raise IOError("copied compressed bytes differ from previously validated immutable input chunks")
        os.replace(stage, target)
        details["published"] = True
    finally:
        if stage.exists():
            stage.unlink()
        details["temp_deleted"] = not stage.exists()


def scenario(root: Path, variant: str) -> dict:
    folder = root / variant
    folder.mkdir()
    source, target = folder / "source.cmpct", folder / "user.deflate"
    facts = make_archive(source, ("member.bin",))
    previous = b"unchanged pre-existing user output"
    target.write_bytes(previous)
    result = {"case": variant, "published": False, "initial_source_sha256": facts["source_initial_sha"]}
    if variant == "static_corrupt":
        result["mutation"] = flip_payload(source, facts, 19)
    with CMPCT(source) as reader:
        try:
            identity = verify_once_with_wire_sha(reader, 0)
            result["preflight_wire_sha256"] = identity["wire_sha256"]
            result["preflight_inflated_bytes"] = identity["logical_bytes_inflated"]
            result["preflight_max_input_chunk"] = identity["max_input_chunk"]
            callback = None
            if variant == "after_verify":
                result["mutation"] = flip_payload(source, facts, 19)
                assert reader.mm[result["mutation"]["offset"]] == result["mutation"]["current_byte"]
            elif variant == "source_restored":
                result["mutation"] = flip_payload(source, facts, 19)
            elif variant == "during_copy":
                def mutate_next_chunk():
                    result["mutation"] = flip_payload(source, facts, 400)
                    assert reader.mm[result["mutation"]["offset"]] == result["mutation"]["current_byte"]
                callback = mutate_next_chunk
            publish_if_wire_equal(reader, target, identity, result, mutate_on_chunk=callback)
            if variant == "source_restored":
                raise AssertionError("source restoration should only occur after failed copy and before digest comparison")
            result["status"] = "published_verified"
        except IOError as exc:
            if variant == "source_restored":
                result["source_restoration"] = flip_payload(source, facts, 19)
            result["status"] = "rejected"
            result["exception"] = type(exc).__name__
    result["final_source_sha256"] = digest(source.read_bytes())
    result["final_target_sha256"] = digest(target.read_bytes())
    result["original_target_preserved"] = target.read_bytes() == previous
    result["stage_leaks"] = [
        entry.name for entry in folder.iterdir() if entry.name.startswith(".cmpct-wire-stage-")
    ]
    if result["published"]:
        result["raw_deflate_decodes_original"] = zlib.decompress(target.read_bytes(), -15) == facts["raw"]
    return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="deflate-mutation-evidence/o4-result.json")
    args = p.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-wire-binding-o4-") as td:
        root = Path(td)
        cases = [
            scenario(root, "pristine"),
            scenario(root, "static_corrupt"),
            scenario(root, "after_verify"),
            scenario(root, "during_copy"),
            scenario(root, "source_restored"),
        ]
    receipt = {
        "question": "Can a verifier-fed SHA256 compressed wire commitment bind subsequent bounded copies even when mmap changes?",
        "source_head": os.environ.get("GITHUB_SHA", "local-unbound"),
        "owner": "PR #284 (no product edits)", "evidence_tier": "detached byte-custody oracle",
        "cases": cases,
    }
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    clean = cases[0]
    assert clean["status"] == "published_verified" and clean["published"]
    assert clean["raw_deflate_decodes_original"] and not clean["original_target_preserved"]
    assert clean["preflight_wire_sha256"] == clean["copied_wire_sha256"]
    for case in cases[1:]:
        assert case["status"] == "rejected" and not case["published"]
        assert case["original_target_preserved"] and not case["stage_leaks"]
    for case in cases[2:]:
        assert case["preflight_wire_sha256"] != case["copied_wire_sha256"]
        assert case["copied_wire_sha256"] == case["staged_stream_sha256"]
        assert case["max_copy_chunk"] <= 256
    assert cases[4]["initial_source_sha256"] == cases[4]["final_source_sha256"], "restore control must finish with identical source bytes"
    print(json.dumps({
        "outcome": "VERIFIER_FED_WIRE_IDENTITY_REJECTS_POSTCHECK_AND_MIDCOPY_SOURCE_MUTATION",
        "source_head": receipt["source_head"],
        "cases": [
            {"case": x["case"], "status": x["status"], "published": x["published"],
             "existing_target_preserved": x["original_target_preserved"]}
            for x in cases
        ], "evidence_path": str(output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
