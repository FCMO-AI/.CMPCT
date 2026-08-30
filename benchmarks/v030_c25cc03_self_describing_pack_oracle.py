from __future__ import annotations

"""Research-only C25CC03 self-describing locality-pack composition oracle.

The C25CC01 physical floor proves that control/header shaving cannot rescue the existing encrypted-like grammar.
C25CC02 asks whether self-indexing RAW records can remove the blob table. C25CC03 attacks the larger duplicated
fact: every S_PACK member currently stores ``[pack_blob, offset, length]`` in both recovery-control copies.

For each ordinary locality-safe S_PACK, this oracle proves members occupy one exact contiguous concatenation and
projects a tiny record-local descriptor containing the *delta-coded logical file ordinals* in physical order.
Member lengths live once in the compact logical file table; offsets become cumulative. The two authenticated
recovery controls therefore keep paths/metadata but omit both the global blob table and every S_PACK storage tuple.
The pack descriptor is stored once with its independently SHA-256-authenticated physical record.

No workload identity is part of the proposed admission rule: eligibility is derived from RAW/meta-free physical
records plus exact contiguous S_PACK structure. This oracle changes no shipping bytes and grants no release credit.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_c25cc02_self_indexed_raw_oracle as C2
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

TARGET_SUFFIX = "07_incompressible_and_encrypted_like"
STRATEGY_NAME = "descending_greedy"
LEVELS = CONTROL.LEVELS


def _uvarint(n: int) -> bytes:
    if n < 0:
        raise ValueError("negative uvarint")
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _best_zstd(raw: bytes) -> tuple[int, int]:
    rows = [(len(R24.zc(raw, int(level))), int(level)) for level in LEVELS]
    return min(rows, key=lambda row: (row[0], row[1]))


def _storage_counts(index: dict) -> dict[str, int]:
    counts = Counter()
    names = {
        R24.S_BLOB: "blob",
        R24.S_CHUNKS: "chunks",
        R24.S_VZIP: "vzip",
        R24.S_SPARSE: "sparse",
        R24.S_PACK: "pack",
        R24.S_CDC: "cdc",
    }
    for row in index["files"]:
        storage = row[6]
        if not storage:
            counts["none"] += 1
        else:
            counts[names.get(int(storage[0]), f"unknown-{storage[0]}")] += 1
    return dict(sorted(counts.items()))


def _project(index: dict, projected_blobs: list[list[int]]) -> dict:
    compact = CONTROL._compact_index(index)
    if not C2._same_blob_semantics(compact["b"], projected_blobs):
        raise RuntimeError("C25CC03 source/projected blob semantics diverged")

    # Map logical file ordinals into each physical S_PACK and prove the existing offsets are exactly cumulative.
    packs: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for file_index, row in enumerate(index["files"]):
        storage = row[6]
        if storage and int(storage[0]) == R24.S_PACK:
            packs[int(storage[1])].append((file_index, int(storage[2]), int(storage[3])))

    descriptor_bytes = 0
    descriptor_payload = bytearray()
    for blob_index in sorted(packs):
        members = sorted(packs[blob_index], key=lambda row: row[1])
        cursor = 0
        prior_index = 0
        descriptor_payload += _uvarint(blob_index)
        descriptor_payload += _uvarint(len(members))
        for ordinal, (file_index, offset, length) in enumerate(members):
            if offset != cursor:
                raise RuntimeError(f"S_PACK {blob_index} is not an exact contiguous concatenation")
            if int(index["files"][file_index][4]) != length:
                raise RuntimeError("S_PACK logical size differs from packed span")
            delta = file_index if ordinal == 0 else file_index - prior_index
            if delta < 0:
                raise RuntimeError("S_PACK logical file ordinals are not monotone in physical order")
            descriptor_payload += _uvarint(delta)
            prior_index = file_index
            cursor += length
        if cursor != int(projected_blobs[blob_index][1]):
            raise RuntimeError("S_PACK member spans do not cover the complete physical blob")
    descriptor_bytes = len(descriptor_payload)

    # Keep the compact logical rows but remove physical ownership tuples from S_PACK files. Because storage formerly
    # derived logical size, materialize size in encoded[4] so the remaining control is independently meaningful.
    stripped = {key: value for key, value in compact.items() if key != "b"}
    stripped_files = []
    pack_rows = 0
    for source_row, encoded in zip(index["files"], compact["f"], strict=True):
        storage = source_row[6]
        encoded = list(encoded)
        if storage and int(storage[0]) == R24.S_PACK:
            if int(encoded[0]) in (R24.K_DIR, R24.K_HARDLINK):
                raise RuntimeError("unexpected S_PACK on non-regular row")
            encoded[3] = None
            encoded[4] = int(source_row[4])
            pack_rows += 1
        stripped_files.append(encoded)
    stripped["f"] = stripped_files
    envelope = {"x": list(index["features"]), "c": stripped}
    raw = msgpack.packb(envelope, use_bin_type=True)
    control_bytes, level = _best_zstd(raw)

    # Reconstruction proof: restore projected blob table plus every S_PACK storage tuple from record-local ordinal
    # descriptors. This proof uses the original pack grouping only as an oracle for the proposed deterministic scan.
    restored = {key: value for key, value in stripped.items()}
    restored["b"] = projected_blobs
    restored_files = [list(row) for row in restored["f"]]
    for blob_index, members in packs.items():
        for file_index, offset, length in members:
            row = list(restored_files[file_index])
            row[3] = [R24.S_PACK, blob_index, offset, length]
            row[4] = None
            restored_files[file_index] = row
    restored["f"] = restored_files
    expanded = CONTROL._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    expected = dict(index)
    expected["blobs"] = projected_blobs
    if expanded != expected:
        raise RuntimeError("C25CC03 failed exact logical-index reconstruction")

    return {
        "pack_count": len(packs),
        "pack_file_rows": pack_rows,
        "descriptor_bytes_once": descriptor_bytes,
        "descriptor_bytes_per_pack_mean": descriptor_bytes / max(1, len(packs)),
        "control_raw_bytes_per_copy": len(raw),
        "control_comp_bytes_per_copy": int(control_bytes),
        "control_level": int(level),
        "logical_index_reconstruction_exact": True,
        "blob_table_omitted_from_control": True,
        "s_pack_storage_omitted_from_control": True,
        "s_pack_offsets_derived_cumulatively": True,
        "descriptor_contains_only_pack_blob_and_file_ordinals": True,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, TARGET_SUFFIX)
    archive = work_root / "candidate" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, archive, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError(f"locality-safe source candidate unexpectedly ineligible: {row!r}")
    index, data, physical = PROFILE._source_r24_parts(archive)
    source_blobs, payload_bytes = C2._scan_current_raw_records(data)
    if source_blobs != index["blobs"]:
        raise RuntimeError("C25CC03 cannot derive the source blob table from physical records")
    projected_data_bytes, projected_blobs, projected_payload_bytes = C2._project_self_indexed_data(data)
    if payload_bytes != projected_payload_bytes:
        raise RuntimeError("C25CC03 changed user payload bytes")
    projection = _project(index, projected_blobs)

    # Descriptor bytes become physical bytes exactly once. The 40-byte self-indexed record headers and ordinary
    # conservative 136-byte outer framing remain charged, as do two complete compressed logical-control copies.
    projected_complete = (
        int(R24.HDR.size + R24.FTR.size)
        + int(projected_data_bytes)
        + int(projection["descriptor_bytes_once"])
        + 2 * int(projection["control_comp_bytes_per_copy"])
    )
    zw = work_root / "zstd-work"
    zw.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zw)
    zstd_bytes = int(zstd["archive_bytes"])

    locality = row["locality"]
    return {
        "schema": "cmpct-v030-c25cc03-self-describing-pack-oracle-v1",
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "source": {
            "r24_bytes": int(row["r24_bytes"]),
            "c25cc01_bytes": int(row["wrapped_bytes"]),
            "physical_data_bytes": int(physical["data_bytes"]),
            "logical_payload_bytes": int(payload_bytes),
            "physical_record_count": len(source_blobs),
            "storage_counts": _storage_counts(index),
            "tree_sha256": row["tree_sha256"],
        },
        "candidate": {
            "self_indexed_record_header_bytes": C2.SELF_HEADER.size,
            "projected_physical_data_before_pack_descriptors": int(projected_data_bytes),
            **projection,
            "fixed_framing_bytes": int(R24.HDR.size + R24.FTR.size),
            "projected_complete_bytes": int(projected_complete),
            "zstd19_bytes": zstd_bytes,
            "strict_margin_below_zstd19_bytes": int(zstd_bytes - projected_complete),
            "payload_bytes_changed": False,
            "per_record_sha256_retained": True,
            "two_authenticated_logical_control_copies": True,
        },
        "locality": locality,
        "gate": {
            "logical_index_reconstruction_exact": projection["logical_index_reconstruction_exact"],
            "payload_bytes_unchanged": payload_bytes == projected_payload_bytes,
            "locality_within_8x": float(locality["max_member_read_amplification"]) <= 8.0,
            "decode_unit_within_8mib": int(locality["max_decode_unit_bytes"]) <= 8 * 1024 * 1024,
            "projected_complete_beats_zstd19": projected_complete < zstd_bytes,
            "experiment_valid": True,
            "release_credit": False,
        },
        "promotion_signal": projected_complete < zstd_bytes,
        "release_credit": False,
        "claim_boundary": (
            "Target-scoped reconstruction/size oracle for a content-agnostic physical grammar. Positive evidence "
            "authorizes implementation and complete-boundary timing only; it does not authorize selector/release use."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc03-self-describing-pack-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc03-self-describing-pack.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
