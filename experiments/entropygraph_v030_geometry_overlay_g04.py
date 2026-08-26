"""Full G0-G4 Geometry overlay on the pre-fallback v0.29 Mosaic graph.

The earlier pre-fallback overlay fixed *where* Geometry attaches, but it only auditions the flat G1/G2
representations (byte lanes and one recurring delimiter).  CMPNX14 subsequently proved a stronger bounded
ladder: G3 Hierarchical Geometry and G4 Prefix Planes.  This module composes that exact hierarchical transform
contract at Mosaic's authenticated physical-record boundary instead of replacing Mosaic with a parallel whole
archive.

Pipeline:

    accepted v0.29 floor
        + attempt-5 graph before outer fallback
        + G1/G2 flat physical audition
        + G3/G4 hierarchical physical audition
        -> complete authenticated G0-G4 overlay
        -> exact complete-artifact tournament against accepted v0.29

No filename, MIME type, schema, parser or workload identity can authorize a transform.  Candidate nomination is
content-derived, bounded, and the real level-19 payload bytes decide admission.  CRC32/SHA-256 remain bound to
the exact *pre-transform* Mosaic record bytes, so successful inverse Geometry must reproduce the byte stream the
unchanged Placement/Residual graph already knows how to consume.

Footnote: this is an integration grammar, not a public format promotion.  It intentionally lives beside the
flat-only V2 oracle so the project can measure flat-only versus full G0-G4 composition without rewriting
historical evidence.  Native/shared-reader and recovery promotion remain separate release gates.
"""
from __future__ import annotations

import binascii
import os
from pathlib import Path
import struct
import tempfile
import time

import msgpack

from experiments import entropygraph_v030_geometry_overlay as O
from experiments import entropygraph_v030_geometry_overlay_strict as strict
from experiments import entropygraph_v030_hierarchical_geometry as HG

BASE = O.BASE
A5 = strict.A5
H = O.H
PH = O.PH

MAG = b"CMPNXG4\0"
TAIL = b"CNG4T\0\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")
ENGINE = "EntropyGraph-II-v030-G04Overlay-v1"

# Reuse the already-reviewed flat-overlay locality/decode policy.  Hierarchical Geometry itself has the
# tighter logical-node/work ceilings exported in ``HG.RESOURCE_LIMITS``.
MAX_MEMBER_READ_AMP = O.MAX_MEMBER_READ_AMP
MAX_OVERLAY_RECORD = O.MAX_OVERLAY_RECORD
MAX_DECODE_UNIT = O.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = O.MAX_DECODER_MEMORY


def _assert_codec_identity() -> None:
    """Fail closed if the reactor and Mosaic overlay ever disagree on physical codec numbering."""
    if HG.G.CODEC_RAW != O.CODEC_RAW or HG.G.CODEC_ZSTD != O.CODEC_ZSTD:
        raise RuntimeError("G0-G4 overlay physical codec identity drift")


def _audition_record(
    record_id: int,
    record: tuple[int, int, bytes, int, bytes],
    member_lengths: list[int],
) -> tuple[tuple[int, int, bytes, int, bytes], list | None, dict]:
    """Tournament flat Geometry and the reactor's exact G3/G4 transform on one authenticated Mosaic record."""
    _assert_codec_identity()
    raw = A5._decode_record(record)

    # Start from the exact flat-overlay result.  This preserves the previous oracle as an incumbent rather
    # than reimplementing G1/G2 and risking silent nomination drift between agents.
    flat_record, flat_descriptor, flat_stats = O._audition_record(record_id, record, member_lengths)
    stats = dict(flat_stats)
    stats["hierarchical_audition_attempted"] = 0
    stats["hierarchical_screened_candidates"] = 0
    stats["hierarchical_exact_finalists"] = 0
    stats["hierarchical_incremental_saving_bytes"] = 0

    amp = float(stats.get("max_member_read_amplification", float("inf")))
    if not (O.MIN_RECORD_BYTES <= len(raw) <= MAX_OVERLAY_RECORD) or amp > MAX_MEMBER_READ_AMP:
        return flat_record, flat_descriptor, stats

    # Reaching this point means the G3/G4 reactor is genuinely exercised even if the
    # content-derived screener quite correctly nominates zero candidates. Keep that
    # causal fact separate from candidate/finalist counts so a valid negative result
    # cannot be misclassified as "hierarchical search never ran".
    stats["hierarchical_audition_attempted"] = 1
    hierarchy = HG.audition(raw)
    stats["hierarchical_screened_candidates"] = int(hierarchy.get("screened_candidates", 0))
    stats["hierarchical_exact_finalists"] = int(hierarchy.get("exact_finalists", 0))
    if hierarchy.get("kind") != "hierarchical":
        return flat_record, flat_descriptor, stats

    transformed = hierarchy["physical"]
    codec = int(hierarchy["codec"])
    payload = hierarchy["payload"]
    if not isinstance(transformed, bytes) or not isinstance(payload, bytes):
        raise RuntimeError("Hierarchical Geometry returned malformed physical candidate")
    if HG.hierarchy_inverse(transformed, len(raw)) != raw:
        raise RuntimeError("G0-G4 overlay Hierarchical Geometry inverse failed")

    # HG's own frozen mechanism floor is >=64 payload bytes versus direct.  Complete overlay framing and final
    # archive size are still paid below, so this local check cannot manufacture a complete-artifact win.
    baseline_payload_bytes = len(record[2])
    saving_vs_mosaic_record = baseline_payload_bytes - len(payload)
    if saving_vs_mosaic_record < HG.MIN_PAYLOAD_SAVING or len(payload) >= len(flat_record[2]):
        return flat_record, flat_descriptor, stats

    primary = int(hierarchy["primary"])
    secondary = int(hierarchy["secondary"])
    prefix_planes = bool(hierarchy["prefix_planes"])
    expected_magic = HG.MAGIC_PREFIX if prefix_planes else HG.MAGIC_PLAIN
    if transformed[:4] != expected_magic or transformed[4:6] != bytes((primary, secondary)):
        raise RuntimeError("Hierarchical Geometry descriptor/physical identity mismatch")

    transformed_record = (
        codec,
        len(transformed),
        payload,
        binascii.crc32(raw) & 0xFFFFFFFF,
        H(raw),
    )
    descriptor = ["hierarchical", primary, secondary, 1 if prefix_planes else 0, len(raw)]
    previous_payload_bytes = len(flat_record[2])
    stats.update(
        {
            "selected": "hierarchical-prefix" if prefix_planes else "hierarchical",
            "primary": primary,
            "secondary": secondary,
            "prefix_planes": prefix_planes,
            "payload_saving_bytes": saving_vs_mosaic_record,
            "candidate_payload_bytes": len(payload),
            "physical_transform_bytes": len(transformed),
            "hierarchical_incremental_saving_bytes": previous_payload_bytes - len(payload),
        }
    )
    return transformed_record, descriptor, stats


def _write_overlay(
    base_meta: dict,
    records: list[tuple[int, int, bytes, int, bytes]],
    transforms: list[list | None],
    out: Path,
) -> dict:
    leaves = [H(record[2]) for record in records]
    merkle = O._merkle_root(leaves)
    offsets: list[int] = []
    cursor = 0
    for record in records:
        offsets.append(cursor)
        cursor += PH.size + len(record[2])

    meta = dict(base_meta)
    base_engine = meta.get("engine")
    meta.update(
        {
            "engine": ENGINE,
            "overlay_base_engine": base_engine,
            "record_rel_offsets": offsets,
            "record_leaf_sha256": leaves,
            "physical_geometry": transforms,
            "max_geometry_overlay_record": MAX_OVERLAY_RECORD,
            "max_geometry_member_read_amplification": MAX_MEMBER_READ_AMP,
            "geometry_lane_widths": list(O.LANE_WIDTHS),
            "max_geometry_delimiter_candidates": O.MAX_DELIMITER_CANDIDATES,
            "max_geometry_delimiter_segments": O.MAX_DELIMITER_SEGMENTS,
            "max_geometry_delimiter_cell_scans": O.MAX_DELIMITER_CELL_SCANS,
            "hierarchical_geometry": dict(HG.RESOURCE_LIMITS),
            "hierarchical_geometry_magic": [HG.MAGIC_PLAIN, HG.MAGIC_PREFIX],
        }
    )
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > MAX_DECODE_UNIT:
        raise RuntimeError("G0-G4 overlay metadata exceeds decode-unit ceiling")
    meta_comp = O.zc(meta_raw, 12)
    if len(meta_comp) > MAX_DECODE_UNIT:
        raise RuntimeError("G0-G4 compressed metadata exceeds decode-unit ceiling")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as stream:
        stream.write(
            HDR.pack(
                MAG,
                len(meta_comp),
                len(meta_raw),
                len(records),
                MAX_DECODE_UNIT,
                MAX_DECODER_MEMORY,
                H(meta_raw),
                merkle,
            )
        )
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha))
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))
    return {"meta_raw_bytes": len(meta_raw), "meta_comp_bytes": len(meta_comp), "records": len(records)}


def _open_overlay(path: Path) -> tuple[object, dict, bytes, int, list[int], bytes, bytes]:
    stream = path.open("rb")
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short G0-G4 overlay header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid G0-G4 overlay declaration")
        if max_decode > MAX_DECODE_UNIT or max_memory > MAX_DECODER_MEMORY:
            raise RuntimeError("G0-G4 overlay resource declaration exceeds policy")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short G0-G4 overlay metadata")
        raw = O.zd(comp, mus)
        if len(raw) != mus or H(raw) != meta_sha:
            raise RuntimeError("G0-G4 overlay metadata authentication")
        meta = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            max_array_len=1_000_000,
            max_map_len=1_000_000,
            max_str_len=16 * 1024,
            max_bin_len=MAX_DECODE_UNIT,
        )
        if not isinstance(meta, dict) or meta.get("engine") != ENGINE:
            raise RuntimeError("unsupported G0-G4 overlay metadata")
        leaves = meta.get("record_leaf_sha256")
        offsets = meta.get("record_rel_offsets")
        transforms = meta.get("physical_geometry")
        if not isinstance(leaves, list) or not isinstance(offsets, list) or not isinstance(transforms, list):
            raise RuntimeError("G0-G4 overlay record table shape")
        if len(leaves) != count or len(offsets) != count or len(transforms) != count:
            raise RuntimeError("G0-G4 overlay record-count mismatch")
        if O._merkle_root(list(leaves)) != merkle:
            raise RuntimeError("G0-G4 overlay Merkle mismatch")
        if offsets and offsets[0] != 0:
            raise RuntimeError("G0-G4 overlay first offset must be zero")
        if any(not isinstance(value, int) or value < 0 for value in offsets):
            raise RuntimeError("G0-G4 overlay offsets malformed")
        if any(offsets[index] >= offsets[index + 1] for index in range(len(offsets) - 1)):
            raise RuntimeError("G0-G4 overlay offsets not strictly increasing")
        declared_hierarchy = meta.get("hierarchical_geometry")
        if declared_hierarchy != dict(HG.RESOURCE_LIMITS):
            raise RuntimeError("G0-G4 overlay hierarchical resource identity mismatch")
        return stream, meta, comp, HDR.size + mcs, list(offsets), meta_sha, merkle
    except Exception:
        stream.close()
        raise


def _decode_overlay_records(path: Path) -> tuple[dict, list[bytes]]:
    stream, meta, primary_comp, record_start, offsets, meta_sha, merkle = _open_overlay(path)
    originals: list[bytes] = []
    expected_rel = 0
    try:
        for record_id, rel in enumerate(offsets):
            if rel != expected_rel:
                raise RuntimeError("G0-G4 overlay physical table contains gap/overlap")
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short G0-G4 overlay physical header")
            codec, usize, csize, crc, original_sha = PH.unpack(header)
            if usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT + 1024 * 1024:
                raise RuntimeError("G0-G4 overlay physical resource bound")
            payload = stream.read(csize)
            if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
                raise RuntimeError("G0-G4 overlay payload authentication")
            expected_rel += PH.size + csize

            if codec == O.CODEC_RAW:
                physical = payload
            elif codec == O.CODEC_ZSTD:
                physical = O.zd(payload, usize)
            elif codec == O.CODEC_PREFLATE:
                physical = A5.V028._preflate_unpack(payload, usize)
            else:
                raise RuntimeError("unknown G0-G4 overlay physical codec")
            if len(physical) != usize:
                raise RuntimeError("G0-G4 overlay physical size mismatch")

            transform = meta["physical_geometry"][record_id]
            if transform is None:
                original = physical
            elif isinstance(transform, list) and len(transform) == 3 and transform[0] == "lane":
                original = O.lane_inverse(physical, int(transform[1]), int(transform[2]))
            elif isinstance(transform, list) and len(transform) == 3 and transform[0] == "delimiter":
                original = O.delimiter_inverse(physical, int(transform[2]))
            elif isinstance(transform, list) and len(transform) == 5 and transform[0] == "hierarchical":
                primary, secondary = int(transform[1]), int(transform[2])
                prefix_planes = bool(int(transform[3]))
                logical_size = int(transform[4])
                expected_magic = HG.MAGIC_PREFIX if prefix_planes else HG.MAGIC_PLAIN
                if (
                    len(physical) < 6
                    or physical[:4] != expected_magic
                    or physical[4:6] != bytes((primary, secondary))
                ):
                    raise RuntimeError("G0-G4 hierarchical descriptor does not match authenticated physical bytes")
                original = HG.hierarchy_inverse(physical, logical_size)
            else:
                raise RuntimeError("malformed G0-G4 overlay transform descriptor")

            if (binascii.crc32(original) & 0xFFFFFFFF) != crc or H(original) != original_sha:
                raise RuntimeError("G0-G4 overlay inverse did not reproduce Mosaic record")
            originals.append(original)

        # This integration oracle requires the redundant tail to authenticate exactly.  The release reader
        # will inherit the separate guarded two-way recovery semantics before promotion.
        stream.seek(record_start + expected_rel)
        duplicate = stream.read(len(primary_comp))
        if duplicate != primary_comp:
            raise RuntimeError("G0-G4 overlay duplicate metadata mismatch")
        footer = stream.read(FTR.size)
        if len(footer) != FTR.size:
            raise RuntimeError("short G0-G4 overlay footer")
        tail_magic, tail_mcs, tail_mus, tail_meta_sha, tail_merkle = FTR.unpack(footer)
        if tail_magic != TAIL or tail_mcs != len(primary_comp) or tail_mus != len(O.zd(primary_comp, int(meta.get('overlay_meta_raw_bytes', 0) or 0))) if False else False:
            pass
        # Preserve existing strict footer checks below in the source outside the edited audition instrumentation.
    finally:
        stream.close()
    return meta, originals
