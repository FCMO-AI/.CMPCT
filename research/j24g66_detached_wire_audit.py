#!/usr/bin/env python3
"""Detached J24G66 revision-24 footer/index/xattr interpreter.

No import from cmpct or J24G64 oracles. Uses only Python stdlib, MessagePack
and Zstandard. This is an independent second root for *metadata identity*,
not a full independent decoder for the compressed file members.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import sys

import msgpack
import zstandard as zstd

HEADER = struct.Struct("<8sHHQQQ32s")
FOOTER = struct.Struct("<8sBBBBQQQ32s")
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_META = 16 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unpack(payload: bytes):
    return msgpack.unpackb(payload, raw=False, strict_map_key=False)


def physical_index(archive: bytes):
    assert 0 < len(archive) <= MAX_ARCHIVE, "archive exceeds detached bound"
    magic, version, flags, compressed, logical, data_bytes, sha = HEADER.unpack_from(archive)
    assert magic == b"CMPCT24\x00" and version == 24 and flags == 0
    assert 0 < compressed < MAX_META and 0 < logical < MAX_META
    index_start = HEADER.size
    assert index_start + compressed <= len(archive)
    initial_raw = zstd.ZstdDecompressor().decompress(
        archive[index_start:index_start + compressed], max_output_size=logical)
    assert len(initial_raw) == logical and hashlib.sha256(initial_raw).digest() == sha
    primary = unpack(initial_raw)
    assert isinstance(primary, dict) and isinstance(primary["files"], list)
    assert isinstance(primary["blobs"], list)
    # Archive has no trailing bytes in this court. A generic salvage implementation
    # would need a bounded search for commit footers instead.
    pos = len(archive) - FOOTER.size
    seen = set()
    reverse_deltas = []
    footers = []
    while pos >= HEADER.size + compressed and pos not in seen and len(footers) <= 64:
        seen.add(pos)
        m, kind, codec, f, reserved, cs, us, previous, want = FOOTER.unpack_from(archive, pos)
        assert (m, kind, codec, f, reserved) in (
            (b"CMPTF24\x00", 0, 0, 0, 0),
            (b"CMPTF24\x00", 0, 1, 0, 0),
            (b"CMPTF24\x00", 1, 0, 0, 0),
            (b"CMPTF24\x00", 1, 1, 0, 0),
        ), ("invalid footer framing", pos)
        assert 0 < cs <= pos and 0 < us < MAX_META and (previous == 0 or previous < pos)
        coded = archive[pos - cs:pos]
        raw = coded if codec == 0 else zstd.ZstdDecompressor().decompress(
            coded, max_output_size=us)
        assert len(raw) == us and hashlib.sha256(raw).digest() == want
        doc = unpack(raw)
        footers.append({"position": pos, "kind": kind, "digest": digest(raw),
                        "previous": previous, "compressed": cs, "logical": us})
        if kind == 0:
            assert isinstance(doc, dict)
            assert msgpack.packb(doc, use_bin_type=True) == msgpack.packb(
                primary, use_bin_type=True), "initial index != authenticated original tail"
            assert previous == 0, "unexpected previous footer before first checkpoint"
            break
        assert isinstance(doc, dict) and isinstance(doc.get("ops"), list)
        assert len(doc["ops"]) == 1
        assert isinstance(doc.get("blobs"), list)
        reverse_deltas.append(doc)
        pos = previous
    assert len(footers) == 64 and len(reverse_deltas) == 63, "wrong physical generation depth"
    return primary, list(reversed(reverse_deltas)), footers


def replay_without_cmpct(primary, deltas):
    index = copy.deepcopy(primary)
    # The detached algorithm assigns metadata directly to immutable logical
    # identities, never to shifting ordinal positions.
    original_rows = index["files"]
    live = {row[0]: copy.deepcopy(row) for row in original_rows}
    assert len(live) == len(original_rows)
    metadata = index.get("fsmeta", {})
    attrs_by_path = {}
    owner_by_path = {}
    for item in metadata.get("xattrs", []):
        assert len(item) == 2 and type(item[0]) is int
        old = original_rows[item[0]][0]
        assert old not in attrs_by_path
        attrs_by_path[old] = copy.deepcopy(item[1])
    for item in metadata.get("owner_overrides", []):
        assert len(item) == 3 and type(item[0]) is int
        old = original_rows[item[0]][0]
        assert old not in owner_by_path
        owner_by_path[old] = list(item[1:])
    initial_count = len(attrs_by_path)
    opcode_count = {"ren": 0, "del": 0, "put": 0}
    for step, delta in enumerate(deltas):
        index["blobs"].extend(delta["blobs"])
        op = delta["ops"][0]
        tag = op[0]
        assert tag in opcode_count, (step, tag)
        opcode_count[tag] += 1
        if tag == "ren":
            assert len(op) == 3
            old, new = op[1:]
            assert old in live and new not in live
            moved = live.pop(old)
            moved[0] = new
            live[new] = moved
            if old in attrs_by_path:
                attrs_by_path[new] = attrs_by_path.pop(old)
            if old in owner_by_path:
                owner_by_path[new] = owner_by_path.pop(old)
        elif tag == "del":
            assert len(op) == 2
            old = op[1]
            assert old in live
            del live[old]
            attrs_by_path.pop(old, None)
            owner_by_path.pop(old, None)
        else:
            assert len(op) == 2 and isinstance(op[1], list)
            row = copy.deepcopy(op[1])
            assert len(row) >= 7
            # Existing pathname inherits xattrs; new identity gets no overrides.
            live[row[0]] = row
    assert opcode_count == {"ren": 21, "del": 21, "put": 21}
    names = sorted(live)
    index["files"] = [live[name] for name in names]
    if "xattrs" in metadata:
        metadata["xattrs"] = [
            [ordinal, attrs_by_path[name]]
            for ordinal, name in enumerate(names) if name in attrs_by_path
        ]
    if "owner_overrides" in metadata:
        metadata["owner_overrides"] = [
            [ordinal, *owner_by_path[name]]
            for ordinal, name in enumerate(names) if name in owner_by_path
        ]
    assert len(index["files"]) == len(live)
    return index, {
        "initial_signed_xattr_paths": initial_count,
        "final_signed_xattr_paths": len(attrs_by_path),
        "physical_opcode_counts": opcode_count,
        "final_signed_path_names": sorted(attrs_by_path),
        "final_signed_owner_paths": sorted(owner_by_path),
    }


def audit(path: Path, receipt_path: Path) -> dict:
    archive = path.read_bytes()
    receipt = json.loads(receipt_path.read_text())
    assert receipt["schema"] == "cmpct-j24g66-signed-fsmeta-physical-v1"
    assert receipt["decision"] == "PHYSICAL_SIGNED_XATTR_IDENTITY_PASS"
    assert digest(archive) == receipt["archive_sha256"]
    assert len(archive) == receipt["physical_archive_bytes"]
    primary, deltas, footers = physical_index(archive)
    result, metadata = replay_without_cmpct(primary, deltas)
    packed = msgpack.packb(result, use_bin_type=True)
    assert digest(packed) == receipt["final_index_msgpack_sha256"], (
        "independent signed metadata replay != CMPCT/J24G64 final index",
        digest(packed), receipt["final_index_msgpack_sha256"])
    assert len(result["files"]) == receipt["final_members"]
    assert metadata["initial_signed_xattr_paths"] == receipt["initial_xattr_records"]
    assert metadata["final_signed_xattr_paths"] == receipt["final_xattr_records"]
    assert metadata["final_signed_path_names"] == receipt["final_tagged_paths"]
    assert len(footers) == receipt["footer_count"] == 64
    assert len(deltas) == receipt["depth"] == 63
    return {
        "schema": "cmpct-j24g66-detached-replay-v1",
        "decision": "INDEPENDENT_PHYSICAL_SIGNED_METADATA_REPLAY_MATCH",
        "sha256": receipt["archive_sha256"],
        "index_sha256": digest(packed),
        "physical_archive_bytes": len(archive),
        "footer_count": len(footers),
        "source_no_cmpct_import": True,
        "metadata": metadata,
        "scope": "detached SHA-authenticated footer + index metadata replay only; no independent full codec/member decoder",
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: detached_wire_audit.py archive.cmpct receipt.json review.json")
    source, receipt, out = map(Path, sys.argv[1:])
    report = audit(source, receipt)
    # Independent negative: changing a copy of one physical signed footer
    # must invalidate its digest; never mutate the accepted original.
    raw = bytearray(source.read_bytes())
    raw[-1] ^= 0x01
    try:
        physical_index(bytes(raw))
    except (AssertionError, ValueError, zstd.ZstdError):
        report["modified_footer_rejected"] = True
    else:
        raise AssertionError("SHA mutation of physical footer accepted")
    # A forged receipt with a wrong index digest must not match the physical data.
    bogus = json.loads(receipt.read_text())
    bogus["final_index_msgpack_sha256"] = "0" * 64
    mutated = out.with_suffix(".forged-input.json")
    mutated.write_text(json.dumps(bogus))
    try:
        audit(source, mutated)
    except (AssertionError, ValueError, zstd.ZstdError):
        report["forged_index_receipt_rejected"] = True
    else:
        raise AssertionError("forged signed metadata receipt accepted")
    mutated.unlink()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("J24G66_DETACHED_DECISION", report["decision"])
    print("J24G66_DETACHED_INDEX_SHA", report["index_sha256"])


if __name__ == "__main__":
    main()
