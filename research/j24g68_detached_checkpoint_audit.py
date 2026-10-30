#!/usr/bin/env python3
"""Detached physical signed r24 checkpoint64 interpreter, no CMPCT product import.

Reuses J24G66's independent primary+63-delta wire parser and independently
models the 64th one-op logical identity transformation. It authenticates the
real public-Writer checkpoint footer, not a manually fabricated index.
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

from j24g66_detached_wire_audit import physical_index, replay_without_cmpct

FTR = struct.Struct("<8sBBBBQQQ32s")
OLD = "r0000.dat"
NEW = "z-checkpoint-owner.dat"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def checkpoint(data: bytes, expected_prev: int) -> dict:
    assert FTR.size <= len(data)
    pos = len(data) - FTR.size
    magic, kind, codec, flags, reserved, cs, us, previous, expected_sha = FTR.unpack_from(data, pos)
    assert (magic, kind, codec, flags, reserved) in (
        (b"CMPTF24\x00", 0, 0, 0, 0),
        (b"CMPTF24\x00", 0, 1, 0, 0),
    ), "invalid physical checkpoint footer"
    assert previous == expected_prev and previous < pos, "checkpoint previous pointer"
    assert 0 < cs <= pos and 0 < us < (16 * 1024 * 1024)
    encoded = data[pos - cs:pos]
    raw = (encoded if codec == 0 else zstd.ZstdDecompressor().decompress(
        encoded, max_output_size=us))
    assert len(raw) == us and hashlib.sha256(raw).digest() == expected_sha, (
        "physical checkpoint SHA failure")
    doc = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    assert isinstance(doc, dict) and isinstance(doc.get("files"), list)
    return {"index": doc, "position": pos, "previous": previous,
            "digest": digest(raw), "stored_bytes": cs}


def independent_rename(prior: dict) -> dict:
    """Path-keyed reassociation; no imported CMPCT ordinal-rekey code."""
    index = copy.deepcopy(prior)
    old_rows = index["files"]
    live = {row[0]: copy.deepcopy(row) for row in old_rows}
    assert len(live) == len(old_rows)
    assert OLD in live and NEW not in live
    meta = index.get("fsmeta", {})
    by_name = {}
    for field in ("xattrs", "owner_overrides"):
        records = meta.get(field, [])
        keyed = {}
        for rec in records:
            pos = rec[0]
            assert type(pos) is int and 0 <= pos < len(old_rows)
            name = old_rows[pos][0]
            assert name not in keyed
            keyed[name] = copy.deepcopy(rec[1:])
        by_name[field] = keyed
    row = live.pop(OLD)
    row[0] = NEW
    live[NEW] = row
    for keyed in by_name.values():
        if OLD in keyed:
            keyed[NEW] = keyed.pop(OLD)
    names = sorted(live)
    index["files"] = [live[name] for name in names]
    for field, keyed in by_name.items():
        if field in meta:
            meta[field] = [
                [i, *keyed[name]] for i, name in enumerate(names) if name in keyed
            ]
    assert OLD not in live and NEW in live
    return index


def audit(before: Path, after: Path, receipt_path: Path) -> dict:
    receipt_bytes = receipt_path.read_bytes()
    r = json.loads(receipt_bytes)
    assert r["schema"] == "cmpct-j24g68-checkpoint64-v1"
    assert r["decision"] == "J24G68_PHYSICAL_CHECKPOINT64_FIDELITY_PASS"
    base_raw, post_raw = before.read_bytes(), after.read_bytes()
    assert len(base_raw) == r["prior_archive_bytes"]
    assert len(post_raw) == r["checkpoint_archive_bytes"]
    assert digest(base_raw) == r["prior_archive_sha256"]
    assert digest(post_raw) == r["checkpoint_archive_sha256"]
    assert post_raw.startswith(base_raw), "signed physical prefix changed"
    assert len(post_raw) - len(base_raw) == r["checkpoint_appended_bytes"]
    primary, deltas, footers = physical_index(base_raw)
    assert len(deltas) == 63 and len(footers) == 64
    assert footers[0]["kind"] == 1
    expected_prev = footers[0]["position"]
    assert expected_prev == r["last_prior_footer_offset"]
    prior_index, prior_meta = replay_without_cmpct(primary, deltas)
    assert len(prior_index["files"]) == 118
    assert prior_meta["final_signed_xattr_paths"] == 5
    independently_expected = independent_rename(prior_index)
    physical = checkpoint(post_raw, expected_prev)
    actual = physical["index"]
    assert actual == independently_expected, "physical checkpoint vs detached replay"
    assert msgpack.packb(actual, use_bin_type=True) == msgpack.packb(
        independently_expected, use_bin_type=True), "checkpoint indexed wire bytes differ"
    assert digest(msgpack.packb(actual, use_bin_type=True)) == r["final_index_msgpack_sha256"]
    assert len(actual["files"]) == r["final_members"] == 118
    # A corrupted physical footer cannot be misclassified as valid checkpoint.
    mutated = bytearray(post_raw)
    mutated[-1] ^= 0x01
    rejected_footer = False
    try:
        checkpoint(bytes(mutated), expected_prev)
    except AssertionError:
        rejected_footer = True
    assert rejected_footer, "detached auditor accepted corrupted footer digest"
    # A transposed signed xattr ordinal must not be mistaken for the same identity.
    forged = copy.deepcopy(actual)
    records = forged.get("fsmeta", {}).get("xattrs", [])
    assert records
    occupied = {rec[0] for rec in records}
    victim = next(i for i in range(len(forged["files"])) if i not in occupied)
    records[0][0] = victim
    assert forged != independently_expected and msgpack.packb(
        forged, use_bin_type=True) != msgpack.packb(actual, use_bin_type=True)
    return {
        "schema": "cmpct-j24g68-detached-v1",
        "decision": "DETACHED_PHYSICAL_CHECKPOINT64_IDENTITY_PASS",
        "research_source_head": r["source"]["head"],
        "archive_sha256": digest(post_raw),
        "checkpoint_payload_sha256": physical["digest"],
        "checkpoint_previous_footer_offset": physical["previous"],
        "physical_prior_footer_count": len(footers),
        "physical_new_checkpoint_count": 1,
        "prior_signed_xattrs": prior_meta["final_signed_xattr_paths"],
        "final_index_sha256": digest(msgpack.packb(actual, use_bin_type=True)),
        "checkpoint_extra_bytes": len(post_raw) - len(base_raw),
        "wrong_footer_digest_rejected": rejected_footer,
        "wrong_xattr_ordinal_rejected": True,
        "product_code_imported": False,
        "limitation": "Detached metadata/index/footer proof; does not independently decode every codec payload or measure performance",
    }


def main() -> None:
    assert len(sys.argv) == 5, "before.cmpct after.cmpct result.json detached.json"
    result = audit(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    out = Path(sys.argv[4])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24G68_DETACHED", result["decision"])
    print("J24G68_HEAD", result["research_source_head"])


if __name__ == "__main__":
    main()
