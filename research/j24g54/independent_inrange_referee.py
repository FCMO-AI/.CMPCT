"""Independent physical referee of J24G54b in-range signed-journal misbinding.

This process uses no CMPCT import. The original J24G54a referee is unchanged.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

import msgpack
import zstandard as zstd

from independent_journal_referee import HDR, FTR, BHDR, decode_payload, footer, sha


def physical(before: bytes, after: bytes, tag: str) -> dict:
    assert after.startswith(before) and len(after) > len(before)
    magic, version, flags, csize, usize, span, digest = HDR.unpack_from(before)
    assert (magic, version, flags) == (b"CMPCT24\x00", 24, 0)
    assert 0 < csize and 0 < usize < 8_388_608
    raw = decode_payload(before[HDR.size:HDR.size + csize], 1, usize)
    assert sha(raw) == digest
    index = msgpack.unpackb(raw, raw=False)
    names = [r[0] for r in index["files"]]
    assert names == ["a-early.bin", "b-delete.bin", "c-owned.bin", "z-late.bin"]
    original = index["fsmeta"].get("xattrs", [])
    assert [x[0] for x in original] == ([2] if tag == "inrange_xattr" else [])
    bstart = HDR.size + csize
    bend = bstart + span
    for off, blob_usize, blob_csize, codec, metadata_size in index["blobs"]:
        at = bstart + off
        info = BHDR.unpack_from(before, at)
        assert info[0] == b"CMA4"
        assert (info[1], info[4], info[5], info[6]) == (
            codec, blob_usize, blob_csize, metadata_size)
        assert at + BHDR.size + metadata_size + blob_csize <= bend
    start_footer = len(before) - FTR.size
    root, previous, kind = footer(before, start_footer)
    assert kind == 0 and previous == 0 and root == index
    delta, parent, delta_kind = footer(after, len(after) - FTR.size)
    assert delta_kind == 1 and parent == start_footer
    assert delta["blobs"] == [] and delta["ops"] == [["del", "b-delete.bin"]]
    # A single deleted ordinal 1 makes owner's old 2 become 1. Old 2 still
    # fits the new length 3, so range-only preflight cannot detect misbinding.
    final_names = ["a-early.bin", "c-owned.bin", "z-late.bin"]
    assert (2 < len(final_names)) and (final_names[2] == "z-late.bin")
    return {
        "tag": tag, "sha256_before": sha(before).hex(),
        "sha256_after": sha(after).hex(),
        "body_sha256": sha(before[bstart:bend]).hex(),
        "initial_xattr_ordinals": [row[0] for row in original],
        "stale_ordinal_inside_final_range": bool(original),
        "actual_signed_journal": True,
        "actual_original_owner": "c-owned.bin" if original else None,
        "preflight_if_not_rekeyed": "z-late.bin" if original else None,
        "correct_remapped_owner": "c-owned.bin" if original else None,
    }


def main(root: Path):
    results = {}
    for tag in ("inrange_xattr", "inrange_control"):
        before = (root / f"{tag}-before.cmpct").read_bytes()
        after = (root / f"{tag}-after.cmpct").read_bytes()
        out = physical(before, after, tag)
        receipt = json.loads((root / f"{tag}-receipt.json").read_text())
        assert receipt["original_sha256"] == out["sha256_before"]
        assert receipt["after_sha256"] == out["sha256_after"]
        assert receipt["preflight_accepted"] is True and receipt["depth"] == 1
        assert receipt["reader_bound_paths"] == ([out["correct_remapped_owner"]] if out["correct_remapped_owner"] else [])
        assert receipt["preflight_bound_paths"] == ([out["preflight_if_not_rekeyed"]] if out["preflight_if_not_rekeyed"] else [])
        results[tag] = out
    raw_before = (root / "inrange_xattr-before.cmpct").read_bytes()
    raw_after = (root / "inrange_xattr-after.cmpct").read_bytes()
    mutations = {}
    for label, pos in (
        ("delta_sha", len(raw_after) - 1),
        ("checkpoint_sha", len(raw_before) - 1),
        ("index_sha", HDR.size + 2),
        ("physical_header", HDR.size + HDR.unpack_from(raw_before)[3]),
    ):
        altered = bytearray(raw_after)
        altered[pos] ^= 1
        altered_before = bytearray(raw_before)
        if pos < len(raw_before):
            altered_before[pos] ^= 1
        assert altered.startswith(altered_before)
        try:
            physical(bytes(altered_before), bytes(altered), "inrange_xattr")
        except (AssertionError, ValueError, KeyError, TypeError, msgpack.UnpackException, zstd.ZstdError):
            mutations[label] = True
        else:
            mutations[label] = False
    assert all(mutations.values()), mutations
    result = {"court": "J24G54b in-range physical referee",
              "observations": results, "mutations_rejected": mutations,
              "decision": "IN_RANGE_SIGNED_XATTR_MISBOUND_IN_PREFLIGHT_EFFECTIVE_INDEX"}
    (root / "independent-inrange-referee.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
