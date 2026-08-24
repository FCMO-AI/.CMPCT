from __future__ import annotations

"""Research-only physical-overhead decomposition for the encrypted-like r24 target.

The compact-control frontier proves that control-plane compaction alone cannot beat Zstd-19 on this row. This
oracle locates the rest of the gap without changing a byte: it parses the exact verified shipping r24 data span and
accounts separately for self-describing blob headers, per-record codec metadata, compressed payload bytes and
nonproductive compression (compressed+metadata bytes above the original raw size).

The hypothetical floors are deliberately labelled non-productizable. Blob headers are part of r24 salvage/recovery
semantics and cannot simply be deleted. Their purpose here is to answer whether a future bounded canonical profile
could plausibly close the measured Zstd deficit through physical framing alone, or whether a stronger payload
representation is mathematically required.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_r24_compact_control_oracle as CONTROL
from benchmarks import v030_r24_compact_control_oracle_v3 as CONTROL_V3
from cmpct import codec as R24


def _records(archive: Path) -> dict:
    payload = archive.read_bytes()
    if len(payload) < R24.HDR.size + R24.FTR.size:
        raise RuntimeError("truncated r24 archive")
    magic, version, _flags, primary_cbytes, _raw_bytes, data_bytes, _index_sha = R24.HDR.unpack_from(payload, 0)
    if magic != R24.MAGIC or int(version) != R24.VERSION:
        raise RuntimeError("not canonical r24")
    pos = R24.HDR.size + int(primary_cbytes)
    end = pos + int(data_bytes)
    if end > len(payload) - R24.FTR.size:
        raise RuntimeError("r24 data span exceeds archive")

    rows = []
    by_codec: dict[str, dict[str, int]] = {}
    while pos < end:
        if pos + R24.BHDR.size > end:
            raise RuntimeError("truncated r24 blob header")
        bmagic, codec, _flags, _reserved, usize, csize, meta_len, _meta_crc, digest = R24.BHDR.unpack_from(payload, pos)
        if bmagic != R24.BMAGIC:
            raise RuntimeError(f"bad r24 blob magic at {pos}")
        usize, csize, meta_len = int(usize), int(csize), int(meta_len)
        row_end = pos + R24.BHDR.size + meta_len + csize
        if row_end > end:
            raise RuntimeError("r24 blob record exceeds data span")
        if len(digest) != 32:
            raise RuntimeError("r24 blob digest width changed")
        codec_name = {
            R24.CODEC_RAW: "raw",
            R24.CODEC_ZSTD: "zstd",
            R24.CODEC_WAVFLAC: "wavflac",
            R24.CODEC_ZSTDDICT: "zstd-dict",
            R24.CODEC_DEFLATE: "deflate",
        }.get(int(codec), f"codec-{int(codec)}")
        nonproductive = max(0, csize + meta_len - usize)
        rows.append({
            "codec": codec_name,
            "usize": usize,
            "csize": csize,
            "meta_bytes": meta_len,
            "header_bytes": R24.BHDR.size,
            "nonproductive_compression_bytes": nonproductive,
        })
        slot = by_codec.setdefault(codec_name, {"records": 0, "usize": 0, "csize": 0, "meta_bytes": 0, "header_bytes": 0, "nonproductive_compression_bytes": 0})
        slot["records"] += 1
        slot["usize"] += usize
        slot["csize"] += csize
        slot["meta_bytes"] += meta_len
        slot["header_bytes"] += R24.BHDR.size
        slot["nonproductive_compression_bytes"] += nonproductive
        pos = row_end
    if pos != end:
        raise RuntimeError("r24 data span did not parse exactly")
    return {
        "record_count": len(rows),
        "blob_header_bytes": len(rows) * R24.BHDR.size,
        "record_meta_bytes": sum(row["meta_bytes"] for row in rows),
        "compressed_payload_bytes": sum(row["csize"] for row in rows),
        "logical_blob_bytes": sum(row["usize"] for row in rows),
        "nonproductive_compression_bytes": sum(row["nonproductive_compression_bytes"] for row in rows),
        "by_codec": by_codec,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    sources = CONTROL._build_sources(work_root / "sources")
    source = sources[CONTROL.TARGET_NAME]
    work = work_root / "work"
    work.mkdir(parents=True, exist_ok=True)
    archive = work / "shipping-r24.cmpct"
    verified = CONTROL._verified_r24(source, archive)
    index, physical = CONTROL._read_index(archive)
    compact = CONTROL._compact_once(archive)
    records = _records(archive)

    if not verified["tree_sha256"]:
        raise RuntimeError("missing verified tree identity")
    expected_data = records["blob_header_bytes"] + records["record_meta_bytes"] + records["compressed_payload_bytes"]
    if expected_data != int(physical["data_bytes"]):
        raise RuntimeError(f"physical data accounting mismatch: {expected_data} != {physical['data_bytes']}")

    # Reuse the exact same frozen competitor measurement as the evidence-safe compact-control experiment.
    target = CONTROL_V3.run(work_root / "control-reference")["target"]
    compact_projected = int(compact["projected_two_copy_archive_bytes"])
    zstd_bytes = int(target["zstd19_bytes"])
    remaining = compact_projected - zstd_bytes
    header_floor = compact_projected - records["blob_header_bytes"]
    header_meta_floor = header_floor - records["record_meta_bytes"]
    raw_choice_floor = header_meta_floor - records["nonproductive_compression_bytes"]

    return {
        "schema": "cmpct-v030-r24-physical-overhead-v1",
        "target": f"neutral_hostile_v1/{CONTROL.TARGET_NAME}",
        "verified_tree_sha256": verified["tree_sha256"],
        "shipping_r24_bytes": int(physical["archive_bytes"]),
        "compact_control_projected_bytes": compact_projected,
        "zstd19_bytes": zstd_bytes,
        "remaining_zstd_deficit_after_compact_control_bytes": remaining,
        "physical": records,
        "non_productizable_floors": {
            "compact_control_minus_all_blob_headers_bytes": header_floor,
            "minus_all_blob_headers_and_record_metadata_bytes": header_meta_floor,
            "plus_raw_choice_for_nonproductive_compression_bytes": raw_choice_floor,
        },
        "diagnosis": {
            "blob_headers_alone_can_close_remaining_gap": header_floor < zstd_bytes,
            "blob_headers_plus_record_metadata_can_close_remaining_gap": header_meta_floor < zstd_bytes,
            "framing_plus_raw_choice_can_close_remaining_gap": raw_choice_floor < zstd_bytes,
            "minimum_additional_payload_or_framing_saving_needed_bytes": max(0, remaining),
        },
        "contract": {
            "archive_bytes_changed": 0,
            "payload_bytes_changed": 0,
            "reader_or_recovery_changed": False,
            "release_effect": "none; diagnostic decomposition only",
            "warning": "hypothetical floors may remove r24 salvage framing and therefore cannot be promoted directly",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-physical-overhead-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-physical-overhead.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"physical": result["physical"], "diagnosis": result["diagnosis"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
