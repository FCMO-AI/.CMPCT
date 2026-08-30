from __future__ import annotations

"""Research-only C25CC02 self-indexed RAW physical/control composition oracle.

C25CC01 is now exactly disproved for encrypted-like: its locality-safe physical span plus ordinary fixed framing is
already 117 bytes larger than Zstd-19 even if both control copies cost zero bytes. This oracle changes the ownership
boundary instead of shaving the impossible envelope.

For archives whose physical records are all RAW, unflagged, metadata-free and size-preserving, the ordinary r24 blob
table duplicates facts that already live in every physical record. C25CC02 projects a self-indexing record grammar:
``magic:u32 | payload_len:u32 | sha256:32`` followed by raw payload. Codec=RAW and meta_len=0 become profile-level
facts. Scanning the authenticated records reconstructs the *exact* ordinary r24 blob table (offset, usize, csize,
codec, meta_len), so the compact semantic control can omit ``b`` entirely while retaining two authenticated copies.
The projection keeps the ordinary 136-byte r24 header/footer cost as a conservative fixed-framing charge.

This is not a shipping grammar. It grants zero selector/release credit and cannot weaken locality, recovery, output
identity or SHA-256. A positive result only authorizes implementing the bounded grammar and timing its complete
construction/verification boundary against ZIP and Zstd-19.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

import msgpack

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

TARGET_SUFFIX = "07_incompressible_and_encrypted_like"
STRATEGY_NAME = "descending_greedy"
SELF_HEADER = struct.Struct("<4sI32s")
SELF_MAGIC = b"C2R0"
LEVELS = CONTROL.LEVELS


def _scan_current_raw_records(data: bytes) -> tuple[list[list[int]], int]:
    """Prove the source physical span is eligible and reconstruct its current blob table from bytes alone."""
    blobs: list[list[int]] = []
    at = 0
    payload_bytes = 0
    while at < len(data):
        if at + R24.BHDR.size > len(data):
            raise RuntimeError("truncated source r24 record header")
        magic, codec, flags, reserved, usize, csize, meta_len, crc32, digest = R24.BHDR.unpack_from(data, at)
        if magic != R24.BMAGIC:
            raise RuntimeError("source r24 record magic mismatch")
        if int(codec) != R24.CODEC_RAW or int(flags) != 0 or int(reserved) != 0 or int(meta_len) != 0:
            raise RuntimeError("source physical record is not eligible for self-indexed RAW profile")
        if int(usize) != int(csize):
            raise RuntimeError("self-indexed RAW profile requires usize == csize")
        start = at + R24.BHDR.size
        end = start + int(csize)
        if end > len(data):
            raise RuntimeError("truncated source r24 RAW payload")
        payload = data[start:end]
        if hashlib.sha256(payload).digest() != bytes(digest):
            raise RuntimeError("source r24 RAW record SHA mismatch")
        # CRC is intentionally not repeated in the proposed grammar: SHA-256 remains the stronger required integrity
        # owner. The exact source blob table itself never contained CRC or SHA, only the five fields below.
        if (R24.binascii.crc32(payload) & 0xFFFFFFFF) != int(crc32):
            raise RuntimeError("source r24 RAW record CRC mismatch")
        blobs.append([at, int(usize), int(csize), int(codec), int(meta_len)])
        payload_bytes += int(csize)
        at = end
    if at != len(data):
        raise RuntimeError("source r24 record scan trailing bytes")
    return blobs, payload_bytes


def _project_self_indexed_data(data: bytes) -> tuple[int, list[list[int]], int]:
    """Return projected bytes and the exact ordinary blob table reconstructed from the proposed record stream."""
    projected_blobs: list[list[int]] = []
    source_at = 0
    projected_at = 0
    payload_bytes = 0
    records = 0
    while source_at < len(data):
        magic, codec, flags, reserved, usize, csize, meta_len, _crc32, digest = R24.BHDR.unpack_from(data, source_at)
        if magic != R24.BMAGIC or int(codec) != R24.CODEC_RAW or int(flags) or int(reserved) or int(meta_len):
            raise RuntimeError("self-indexed RAW projection encountered an ineligible record")
        if int(usize) != int(csize):
            raise RuntimeError("self-indexed RAW projection requires size-preserving records")
        payload_start = source_at + R24.BHDR.size
        payload_end = payload_start + int(csize)
        payload = data[payload_start:payload_end]
        if hashlib.sha256(payload).digest() != bytes(digest):
            raise RuntimeError("self-indexed RAW projection source SHA mismatch")
        # Proposed record is independently discoverable/salvageable by magic, bounded payload length and SHA-256.
        _encoded_header = SELF_HEADER.pack(SELF_MAGIC, int(csize), bytes(digest))
        projected_blobs.append([projected_at, int(usize), int(csize), R24.CODEC_RAW, 0])
        projected_at += SELF_HEADER.size + int(csize)
        payload_bytes += int(csize)
        records += 1
        source_at = payload_end
    return projected_at, projected_blobs, payload_bytes


def _best_control(index: dict, derived_blobs: list[list[int]]) -> dict:
    compact = CONTROL._compact_index(index)
    if compact["b"] != derived_blobs:
        raise RuntimeError("physical scan did not reconstruct the exact ordinary blob table")
    stripped = dict(compact)
    stripped.pop("b")
    envelope = {"x": list(index["features"]), "c": stripped}
    raw = msgpack.packb(envelope, use_bin_type=True)
    rows = []
    for level in LEVELS:
        comp = R24.zc(raw, level)
        rows.append((len(comp), int(level), comp))
    comp_bytes, level, _comp = min(rows, key=lambda row: (row[0], row[1]))

    restored_compact = dict(stripped)
    restored_compact["b"] = derived_blobs
    expanded = CONTROL._expand_index(restored_compact, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("self-indexed RAW semantic control failed exact index reconstruction")
    return {
        "raw_bytes": len(raw),
        "comp_bytes_per_copy": int(comp_bytes),
        "level": int(level),
        "semantic_index_roundtrip_exact": True,
        "blob_table_omitted_from_control": True,
        "two_authenticated_control_copies": True,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, TARGET_SUFFIX)

    candidate = work_root / "candidate" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, candidate, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError(f"locality-safe source candidate unexpectedly ineligible: {row!r}")
    index, data, physical = PROFILE._source_r24_parts(candidate)
    scanned_blobs, source_payload_bytes = _scan_current_raw_records(data)
    if scanned_blobs != index["blobs"]:
        raise RuntimeError("ordinary r24 blob table is not derivable from physical scan")

    projected_data_bytes, projected_blobs, projected_payload_bytes = _project_self_indexed_data(data)
    if source_payload_bytes != projected_payload_bytes:
        raise RuntimeError("self-indexed RAW projection changed payload bytes")
    control = _best_control(index, projected_blobs)

    fixed_framing_bytes = int(R24.HDR.size + R24.FTR.size)
    projected_complete = fixed_framing_bytes + projected_data_bytes + 2 * int(control["comp_bytes_per_copy"])

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])
    strict_margin = zstd_bytes - projected_complete

    locality = row["locality"]
    result = {
        "schema": "cmpct-v030-c25cc02-self-indexed-raw-oracle-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "source": {
            "r24_bytes": int(row["r24_bytes"]),
            "c25cc01_bytes": int(row["wrapped_bytes"]),
            "physical_data_bytes": int(physical["data_bytes"]),
            "logical_payload_bytes": int(source_payload_bytes),
            "physical_record_count": len(scanned_blobs),
            "current_record_header_bytes": int(physical["data_bytes"]) - int(source_payload_bytes),
            "tree_sha256": row["tree_sha256"],
        },
        "candidate": {
            "self_record_header_bytes": SELF_HEADER.size,
            "projected_record_header_bytes": len(projected_blobs) * SELF_HEADER.size,
            "projected_physical_data_bytes": int(projected_data_bytes),
            "fixed_framing_bytes": fixed_framing_bytes,
            "control": control,
            "projected_complete_bytes": int(projected_complete),
            "zstd19_bytes": zstd_bytes,
            "strict_margin_below_zstd19_bytes": int(strict_margin),
            "payload_bytes_changed": False,
            "per_record_sha256_retained": True,
            "record_magic_retained": True,
            "record_length_retained": True,
            "raw_codec_is_profile_level_fact": True,
            "metadata_free_is_admission_fact": True,
        },
        "locality": locality,
        "gate": {
            "source_blob_table_derived_exactly": scanned_blobs == index["blobs"],
            "semantic_index_roundtrip_exact": bool(control["semantic_index_roundtrip_exact"]),
            "payload_bytes_unchanged": source_payload_bytes == projected_payload_bytes,
            "locality_within_8x": float(locality["max_member_read_amplification"]) <= 8.0,
            "decode_unit_within_8mib": int(locality["max_decode_unit_bytes"]) <= 8 * 1024 * 1024,
            "projected_complete_beats_zstd19": projected_complete < zstd_bytes,
            "experiment_valid": True,
            "release_credit": False,
        },
        "promotion_signal": projected_complete < zstd_bytes,
        "release_credit": False,
        "claim_boundary": (
            "Target-scoped size/reconstruction oracle only. The proposed grammar is admitted from physical RAW/meta-"
            "free structure, not workload identity. Positive evidence authorizes implementing and timing the format; "
            "it does not authorize selector or release promotion."
        ),
    }
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc02-self-indexed-raw-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc02-self-indexed-raw.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
