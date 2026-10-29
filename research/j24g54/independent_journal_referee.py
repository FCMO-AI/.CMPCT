"""J24G54: independent r24 journal/footer/xattr-ordinal referee.

No cmpct imports. Checks authentic same physical archive before and after a
committed deletion, and defends against altered physical receipts.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
EXPECTED = {"a-owner.bin", "b-delete.bin", "z-survivor.bin"}


def sha(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def decode_payload(raw: bytes, codec: int, usize: int) -> bytes:
    assert codec in (0, 1)
    data = (raw if codec == 0 else
            zstd.ZstdDecompressor().decompress(raw, max_output_size=usize + 1))
    assert len(data) == usize
    return data


def footer(data: bytes, pos: int) -> tuple[dict, int, int]:
    assert 0 <= pos <= len(data) - FTR.size
    magic, kind, codec, flags, reserved, csize, usize, previous, digest = FTR.unpack_from(data, pos)
    assert (magic, flags, reserved) == (b"CMPTF24\x00", 0, 0)
    assert kind in (0, 1) and codec in (0, 1)
    assert 0 < csize <= pos and 0 < usize < 8 * 1024 * 1024
    payload = decode_payload(data[pos - csize:pos], codec, usize)
    assert sha(payload) == digest
    decoded = msgpack.unpackb(payload, raw=False)
    assert isinstance(decoded, dict)
    return decoded, previous, kind


def inspect(before: bytes, after: bytes, expected_case: str) -> dict:
    assert before and after.startswith(before)
    assert len(after) > len(before) + FTR.size
    magic, revision, flags, csize, usize, body_span, digest = HDR.unpack_from(before)
    assert (magic, revision, flags) == (b"CMPCT24\x00", 24, 0)
    assert 0 < csize and 0 < usize < 8 * 1024 * 1024
    raw_primary = decode_payload(before[HDR.size:HDR.size + csize], 1, usize)
    assert sha(raw_primary) == digest
    primary = msgpack.unpackb(raw_primary, raw=False)
    assert set(x[0] for x in primary["files"]) == EXPECTED
    assert len(primary["files"]) == 3
    body_start = HDR.size + csize
    body_end = body_start + body_span
    assert body_end <= len(before) - FTR.size
    for off, blob_us, blob_cs, codec, meta_len in primary["blobs"]:
        at = body_start + off
        physical = BHDR.unpack_from(before, at)
        assert physical[0] == b"CMA4"
        assert (physical[1], physical[4], physical[5], physical[6]) == (
            codec, blob_us, blob_cs, meta_len)
        assert at + BHDR.size + meta_len + blob_cs <= body_end

    basepos = len(before) - FTR.size
    checkpoint, baseprev, basekind = footer(before, basepos)
    assert basekind == 0 and baseprev == 0
    assert checkpoint == primary
    delta_pos = len(after) - FTR.size
    delta, previous, kind = footer(after, delta_pos)
    assert kind == 1 and previous == basepos
    assert delta["blobs"] == []
    assert delta["ops"] == [["del", "b-delete.bin"]]
    assert after[body_start:body_end] == before[body_start:body_end]
    attrs = primary["fsmeta"].get("xattrs", [])
    names = [r[0] for r in primary["files"]]
    signed = {names[entry[0]]: entry[1] for entry in attrs}
    assert set(signed).issubset({"a-owner.bin", "z-survivor.bin"})
    required = {
        "both_survivors": {"a-owner.bin", "z-survivor.bin"},
        "late_survivor": {"z-survivor.bin"},
        "early_survivor": {"a-owner.bin"},
        "no_xattrs": set(),
    }[expected_case]
    assert set(signed) == required
    # Independent semantic comparator: signed metadata is owned by logical
    # identity; journal deletion does not delete either surviving owner.
    survivor_names = ["a-owner.bin", "z-survivor.bin"]
    expected_final_attrs = {survivor_names.index(name): value for name, value in signed.items()}
    positional_preflight_attrs = {entry[0]: entry[1] for entry in attrs}
    out_of_bounds = any(i >= len(survivor_names) for i in positional_preflight_attrs)
    assert out_of_bounds == (expected_case in ("both_survivors", "late_survivor"))
    return {
        "case": expected_case, "sha256_before": sha(before).hex(),
        "sha256_after": sha(after).hex(), "body_sha256": sha(before[body_start:body_end]).hex(),
        "checkpoint_offset": basepos, "delta_offset": delta_pos,
        "delta_parent": previous, "initial_xattr_ordinals": sorted(positional_preflight_attrs),
        "expected_final_xattr_ordinals": sorted(expected_final_attrs),
        "out_of_range_if_ordinals_not_rekeyed": out_of_bounds,
        "signed_owner_paths": sorted(signed), "actual_wire_delta_authenticated": True,
    }


def main(root: Path) -> None:
    observations = {}
    for case in ("both_survivors", "late_survivor", "early_survivor", "no_xattrs"):
        before = (root / f"{case}-before.cmpct").read_bytes()
        after = (root / f"{case}-after.cmpct").read_bytes()
        receipt = json.loads((root / f"{case}-receipt.json").read_text())
        observed = inspect(before, after, case)
        assert receipt["before_sha256"] == observed["sha256_before"]
        assert receipt["after_sha256"] == observed["sha256_after"]
        assert receipt["marked_names"] == observed["signed_owner_paths"]
        assert bool(receipt["preflight_exception"]) == observed["out_of_range_if_ordinals_not_rekeyed"]
        assert receipt["reader_verify"] == 2 and receipt["native_xattr_readback"]
        observations[case] = observed

    # Mutation controls on exact same signed physical input, without changing
    # evaluator or rewriting existing evidence.
    base = (root / "both_survivors-after.cmpct").read_bytes()
    before = (root / "both_survivors-before.cmpct").read_bytes()
    positions = {
        "new_footer_digest": len(base) - 1,
        "delta_payload": len(base) - FTR.size - 1,
        "checkpoint_footer_digest": len(before) - 1,
        "primary_index": HDR.size,
        "blob_header": HDR.size + HDR.unpack_from(base)[3],
    }
    rejected = {}
    for label, position in positions.items():
        damaged = bytearray(base)
        damaged[position] ^= 1
        try:
            inspect(before if label != "checkpoint_footer_digest" else bytes(damaged[:len(before)]),
                    bytes(damaged), "both_survivors")
        except (AssertionError, ValueError, KeyError, TypeError,
                zstd.ZstdError, msgpack.UnpackException, struct.error):
            rejected[label] = True
        else:
            rejected[label] = False
    assert all(rejected.values()), rejected
    result = {
        "court": "J24G54 independent physical journal parser",
        "host": sys.platform, "observations": observations,
        "independent_mutations_rejected": rejected,
        "result": "SIGNED_JOURNAL_DELETE_EXPOSES_STALE_PREFLIGHT_XATTR_ORDINALS",
        "limits": "source-exact unmerged candidate; distinct from release evidence",
    }
    (root / "independent-referee.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
