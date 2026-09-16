from __future__ import annotations

"""Research-only C25CC01 self-describing blob-header byte frontier.

The locality-safe physical span is already larger than Zstd-19 even if both compact-control copies cost zero, so
control compaction alone cannot finish encrypted-like. r24's 64-byte per-record BHDR is therefore the next structural
lever, but shrinking it must not quietly delete physical salvage/recovery semantics.

This oracle prices three increasingly honest floors over the exact locality-safe payload and metadata:
1. 32-byte SHA-only: optimistic mathematical lower bound; it omits CRC and all self-description.
2. 36-byte SHA+CRC: preserves payload integrity fields but still depends on control for record framing/codec facts.
3. a self-describing varint header: retains a 4-byte resynchronization magic, codec, flags, varint usize/csize/meta_len,
   CRC32 and full SHA-256. It omits only the currently-zero reserved field. This third projection is the feasibility
   signal because it keeps enough information in every physical record to locate and decode records without either
   control copy. It is still only accounting: an actual grammar must prove hostile-input resynchronization, offset
   remapping, salvage, native/Android parity and all-15 no-regression before promotion.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_physical_overhead_oracle as OVERHEAD
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"
SHA256_BYTES = 32
CRC32_BYTES = 4
DIGEST_ONLY_HEADER_BYTES = SHA256_BYTES
INTEGRITY_HEADER_BYTES = SHA256_BYTES + CRC32_BYTES
SALVAGE_FIXED_BYTES = 4 + 1 + 1 + CRC32_BYTES + SHA256_BYTES  # magic + codec + flags + CRC32 + SHA256


def _uvarint_bytes(value: int) -> int:
    if value < 0:
        raise RuntimeError("negative field cannot be encoded as salvage uvarint")
    n = 1
    while value >= 0x80:
        value >>= 7
        n += 1
    return n


def _salvage_header_accounting(index: dict, data: bytes) -> dict:
    blobs = index.get("blobs")
    if not isinstance(blobs, list):
        raise RuntimeError("locality-safe index has invalid blob table")
    total = 0
    widths = []
    expected_off = 0
    nonzero_flags = 0
    nonzero_reserved = 0
    for blob in sorted(blobs, key=lambda row: int(row[0])):
        if not isinstance(blob, list) or len(blob) < 5:
            raise RuntimeError("locality-safe index has malformed blob row")
        off, usize, csize, codec, meta_len = (int(blob[i]) for i in range(5))
        if off != expected_off:
            raise RuntimeError(f"physical blob span is not contiguous: {off} != {expected_off}")
        if off + R24.BHDR.size > len(data):
            raise RuntimeError("truncated physical blob header")
        bmagic, bcodec, flags, reserved, busize, bcsize, bmeta_len, _crc, digest = R24.BHDR.unpack_from(data, off)
        if bmagic != R24.BMAGIC:
            raise RuntimeError("physical blob magic drift")
        if (int(busize), int(bcsize), int(bcodec), int(bmeta_len)) != (usize, csize, codec, meta_len):
            raise RuntimeError("blob table/BHDR framing disagreement")
        if len(digest) != SHA256_BYTES:
            raise RuntimeError("physical blob SHA-256 width drift")
        nonzero_flags += int(flags != 0)
        nonzero_reserved += int(reserved != 0)
        # Preserve flags even when zero so a future grammar has an explicit evolution bitfield. The old two-byte
        # reserved field is the only omitted self-description, and only because this exact candidate proves it zero.
        width = SALVAGE_FIXED_BYTES + _uvarint_bytes(usize) + _uvarint_bytes(csize) + _uvarint_bytes(meta_len)
        total += width
        widths.append(width)
        expected_off = off + R24.BHDR.size + meta_len + csize
    if expected_off != len(data):
        raise RuntimeError(f"physical blob accounting stopped at {expected_off}, data span is {len(data)}")
    if nonzero_reserved:
        raise RuntimeError("cannot elide nonzero reserved BHDR state from salvage-preserving projection")
    return {
        "header_bytes": total,
        "minimum_header_bytes": min(widths) if widths else 0,
        "maximum_header_bytes": max(widths) if widths else 0,
        "average_header_bytes": (total / len(widths)) if widths else 0.0,
        "nonzero_flags_records": nonzero_flags,
        "nonzero_reserved_records": nonzero_reserved,
        "record_count": len(widths),
        "retains_magic": True,
        "retains_codec": True,
        "retains_flags": True,
        "retains_usize": True,
        "retains_csize": True,
        "retains_meta_len": True,
        "retains_crc32": True,
        "retains_sha256": True,
    }


def _projection(current_wrapped: int, physical_data: int, current_header: int, replacement_header: int,
                fixed_framing: int, control_bytes: int, zstd_bytes: int | None = None) -> dict:
    saving = current_header - replacement_header
    projected_data = physical_data - saving
    wrapped = fixed_framing + projected_data + control_bytes
    if current_wrapped - saving != wrapped:
        raise RuntimeError("header projection does not reconcile to measured wrapped bytes")
    out = {
        "replacement_header_bytes": replacement_header,
        "projected_physical_data_bytes": projected_data,
        "projected_wrapped_bytes_with_existing_two_copy_control": wrapped,
        "bytes_saved_vs_current_wrapped": saving,
    }
    if zstd_bytes is not None:
        out.update({
            "margin_below_zstd19_bytes": zstd_bytes - wrapped,
            "strictly_smaller_than_zstd19": wrapped < zstd_bytes,
        })
    return out


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)

    candidate = work_root / "cmpct" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, candidate, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError(f"{STRATEGY_NAME} locality-safe candidate unexpectedly ineligible: {row!r}")

    index, data, physical = PROFILE._source_r24_parts(candidate)
    compact_raw, _compact = PROFILE._compact_raw(index)
    compact_level, compact_comp = PROFILE._compress_control(compact_raw)
    records = OVERHEAD._records(candidate)
    salvage = _salvage_header_accounting(index, data)

    record_count = int(records["record_count"])
    if int(records["blob_header_bytes"]) != record_count * R24.BHDR.size:
        raise RuntimeError("blob-header accounting drift")
    if salvage["record_count"] != record_count:
        raise RuntimeError("salvage/header record-count disagreement")
    if int(physical["data_bytes"]) != len(data):
        raise RuntimeError("physical-data accounting drift")

    current_wrapped = int(row["wrapped_bytes"])
    current_header_bytes = int(records["blob_header_bytes"])
    fixed_framing_bytes = int(R24.HDR.size + R24.FTR.size)
    current_control_bytes = 2 * len(compact_comp)

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])

    digest_only = _projection(
        current_wrapped, int(physical["data_bytes"]), current_header_bytes,
        record_count * DIGEST_ONLY_HEADER_BYTES, fixed_framing_bytes, current_control_bytes, zstd_bytes,
    )
    digest_only["warning"] = "optimistic lower bound: CRC32 and physical self-description are not priced"

    digest_plus_crc = _projection(
        current_wrapped, int(physical["data_bytes"]), current_header_bytes,
        record_count * INTEGRITY_HEADER_BYTES, fixed_framing_bytes, current_control_bytes, zstd_bytes,
    )
    digest_plus_crc["warning"] = "integrity-priced but control-dependent: physical salvage framing is not retained"

    salvage_varint = _projection(
        current_wrapped, int(physical["data_bytes"]), current_header_bytes,
        int(salvage["header_bytes"]), fixed_framing_bytes, current_control_bytes, zstd_bytes,
    )
    salvage_varint["header_accounting"] = salvage

    return {
        "schema": "cmpct-v030-c25cc01-derived-blob-header-oracle-v3",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "candidate": {
            "r24_bytes": int(row["r24_bytes"]),
            "current_wrapped_bytes": current_wrapped,
            "tree_sha256": row["tree_sha256"],
            "locality": row["locality"],
            "physical_data_bytes": int(physical["data_bytes"]),
            "record_count": record_count,
            "current_blob_header_bytes": current_header_bytes,
            "current_blob_header_bytes_per_record": int(R24.BHDR.size),
            "retained_sha256_bytes_per_record": SHA256_BYTES,
            "retained_crc32_bytes_per_record": CRC32_BYTES,
            "compact_control_bytes_per_copy": len(compact_comp),
            "current_total_control_bytes": current_control_bytes,
            "compact_control_level": int(compact_level),
            "record_meta_bytes_unchanged": int(records["record_meta_bytes"]),
            "compressed_payload_bytes_unchanged": int(records["compressed_payload_bytes"]),
        },
        "zstd19_bytes": zstd_bytes,
        "projection": {
            "fixed_header_footer_bytes": fixed_framing_bytes,
            "digest_only": digest_only,
            "digest_plus_crc": digest_plus_crc,
            "salvage_varint": salvage_varint,
        },
        "gate": {
            "exact_current_wrapped_accounting": current_wrapped
            == fixed_framing_bytes + int(physical["data_bytes"]) + current_control_bytes,
            "locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "full_sha256_digest_cost_retained": SHA256_BYTES == 32,
            "crc32_cost_retained_in_salvage_projection": CRC32_BYTES == 4,
            "physical_self_description_retained_in_salvage_projection": all(
                salvage[k] is True for k in (
                    "retains_magic", "retains_codec", "retains_flags", "retains_usize", "retains_csize",
                    "retains_meta_len", "retains_crc32", "retains_sha256"
                )
            ),
            "reserved_state_proven_elidable": salvage["nonzero_reserved_records"] == 0,
            "existing_control_cost_retained": True,
            "salvage_header_large_enough_to_cross_zstd19": salvage_varint["strictly_smaller_than_zstd19"],
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Target-scoped byte-accounting oracle only. Only the salvage-varint row is allowed to answer the main "
            "feasibility question because it retains record resynchronization, decoding lengths/codec, CRC32 and full "
            "SHA-256 independently of both control copies. Digest-only and digest+CRC rows are lower bounds, not "
            "promotion signals. Even a positive salvage-varint result does not define a canonical format: hostile "
            "resynchronization, offset remapping, exact salvage/recovery, native/Android readers, creation timing, "
            "all-15 no-regression and final exact-head authority remain mandatory."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--work-root", type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-derived-header-work"),
    )
    p.add_argument(
        "--output", type=Path,
        default=Path("benchmark-artifacts/v030-c25cc01-derived-header.json"),
    )
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("C25CC01 derived-blob-header oracle invalid")


if __name__ == "__main__":
    main()
