"""Adversarial reader hardening for the CMPCT v0.30 Geometry IR research archive.

This layer changes **no CMPNX14 writer bytes**.  It imports the existing cell-bounded GIR safety entrypoint,
then strengthens only reader admission: MessagePack container/scalar limits, exact metadata schema checks,
one-node-to-one-record ownership, safe paths, bounded legacy materialization, and a contiguous physical table
whose last record must end exactly where the authenticated duplicate metadata begins.

Footnote: hashes authenticate bytes, not resource behavior.  An attacker can author perfectly authenticated
metadata that is expensive or structurally ambiguous.  These checks therefore run before payload decode and
are part of the reader contract rather than a substitute for integrity hashes.
"""
from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import BinaryIO

import msgpack

from experiments import entropygraph_v030_gir_safe as safe

gir = safe.gir

MAX_METADATA_FILES = 65_536
MAX_METADATA_NODES = 131_072
MAX_METADATA_CONTAINER_ITEMS = 1_000_000
MAX_TOTAL_NODE_REFS = 1_000_000
MAX_PATH_BYTES = 16 * 1024
MAX_META_BINARY_BYTES = 64
MAX_TOTAL_MATERIALIZED_BYTES = gir.MAX_DECODER_MEMORY

_original_open = gir._open


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _sha32(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != 32:
        raise RuntimeError(f"GIR {label} must be a 32-byte SHA-256")
    return value


def _bounded_relpath(rel: object) -> PurePosixPath:
    if not isinstance(rel, str) or len(rel.encode("utf-8")) > MAX_PATH_BYTES:
        raise RuntimeError("GIR path exceeds metadata policy")
    return gir._safe_relpath(rel)


def _no_duplicate_map(pairs: list[tuple[object, object]]) -> dict:
    out: dict = {}
    for key, value in pairs:
        try:
            duplicate = key in out
        except TypeError as exc:
            raise RuntimeError("GIR metadata map key is not hashable") from exc
        if duplicate:
            raise RuntimeError("GIR metadata contains duplicate map key")
        out[key] = value
    return out


def _bounded_unpack(raw: bytes) -> dict:
    """Decode MessagePack with parser ceilings before semantic validation.

    Footnote: ``MAX_DECODE_UNIT`` bounds encoded metadata bytes but not the number of Python objects a tiny
    MessagePack can request.  Parser-level array/map/string/bin limits close that allocation-amplification gap.
    """
    try:
        meta = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            object_pairs_hook=_no_duplicate_map,
            max_array_len=MAX_METADATA_CONTAINER_ITEMS,
            max_map_len=MAX_METADATA_CONTAINER_ITEMS,
            max_str_len=MAX_PATH_BYTES,
            max_bin_len=MAX_META_BINARY_BYTES,
        )
    except Exception as exc:
        raise RuntimeError(f"GIR bounded metadata decode failed: {exc}") from exc
    if not isinstance(meta, dict):
        raise RuntimeError("GIR metadata root must be a map")
    return meta


def _validate_declared_resources(meta: dict) -> None:
    if meta.get("v") != 1 or meta.get("engine") != "Geometry-IR-v1":
        raise RuntimeError("unsupported GIR metadata")
    if meta.get("max_dependency_depth") != 0:
        raise RuntimeError("GIR dependency depth exceeds policy")

    for key, ceiling in (
        ("max_chunk", gir.MAX_CHUNK),
        ("max_decode_unit", gir.MAX_DECODE_UNIT),
        ("max_decoder_memory", gir.MAX_DECODER_MEMORY),
    ):
        value = meta.get(key)
        if not _is_int(value) or value < 0 or value > ceiling:
            raise RuntimeError(f"GIR {key} exceeds policy")

    read_amp = meta.get("max_read_amplification")
    if not isinstance(read_amp, (int, float)) or isinstance(read_amp, bool) or read_amp < 0 or read_amp > 1.0:
        raise RuntimeError("GIR read-amplification declaration exceeds standalone policy")

    geometry = meta.get("geometry")
    if not isinstance(geometry, dict):
        raise RuntimeError("GIR geometry declaration must be a map")
    if geometry.get("lane_widths") != list(gir.G.LANE_WIDTHS):
        raise RuntimeError("GIR lane-width declaration mismatch")
    for key, ceiling in (
        ("max_delimiter_candidates", gir.G.MAX_DELIMITER_CANDIDATES),
        ("max_delimiter_segments", gir.G.MAX_DELIMITER_SEGMENTS),
    ):
        value = geometry.get(key)
        if not _is_int(value) or value < 0 or value > ceiling:
            raise RuntimeError(f"GIR geometry resource budget exceeds policy: {key}")

    hierarchy = meta.get("hierarchical_geometry")
    if not isinstance(hierarchy, dict):
        raise RuntimeError("GIR hierarchical resource declaration must be a map")
    for key, maximum in gir.HG.RESOURCE_LIMITS.items():
        value = hierarchy.get(key)
        if not _is_int(value) or value < 0:
            raise RuntimeError(f"GIR malformed hierarchical resource declaration: {key}")
        # Compressor levels are part of the representation identity; count/work budgets may only tighten.
        if key in {"screen_level", "exact_level"}:
            if value != int(maximum):
                raise RuntimeError(f"GIR hierarchical compressor identity mismatch: {key}")
        elif value > int(maximum):
            raise RuntimeError(f"GIR hierarchical resource budget exceeds policy: {key}")


def _validate_meta_schema(
    meta: dict,
    leaves: list[bytes],
    offsets: list[int],
    expected_count: int | None,
    expected_merkle: bytes,
) -> None:
    _validate_declared_resources(meta)

    tree = meta.get("tree_sha256")
    if not isinstance(tree, str) or len(tree) != 64 or any(ch not in "0123456789abcdef" for ch in tree):
        raise RuntimeError("GIR tree identity declaration is malformed")

    if len(leaves) > MAX_METADATA_NODES:
        raise RuntimeError("GIR record-count policy exceeded")
    if expected_count is not None and (not _is_int(expected_count) or len(leaves) != expected_count):
        raise RuntimeError("GIR record-count mismatch")
    for leaf in leaves:
        _sha32(leaf, "record leaf")
    if gir._merkle_root(leaves) != expected_merkle:
        raise RuntimeError("GIR record table / Merkle mismatch")
    if len(offsets) != len(leaves):
        raise RuntimeError("GIR record table length mismatch")
    if offsets:
        if offsets[0] != 0:
            raise RuntimeError("GIR first physical record must begin at relative offset zero")
        previous = -1
        for value in offsets:
            if not _is_int(value) or value < 0 or value <= previous:
                raise RuntimeError("GIR record offsets must be strictly increasing")
            previous = value

    nodes = meta.get("nodes")
    files = meta.get("files")
    if not isinstance(nodes, list) or not isinstance(files, dict):
        raise RuntimeError("GIR files/nodes metadata shape")
    if len(nodes) > MAX_METADATA_NODES or len(files) > MAX_METADATA_FILES:
        raise RuntimeError("GIR metadata object-count policy exceeded")
    if len(nodes) != len(leaves):
        raise RuntimeError("GIR node/physical record cardinality mismatch")

    record_ids: list[int] = []
    node_sizes: list[int] = []
    for desc in nodes:
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed GIR node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            if not _is_int(width) or width not in gir.G.LANE_WIDTHS:
                raise RuntimeError("GIR lane width out of policy")
        elif kind in {"delimiter", "hierarchical"} and len(desc) == 4:
            _, record_id, logical_size, expected = desc
        else:
            raise RuntimeError("unknown or malformed GIR node kind")
        if not _is_int(record_id) or not 0 <= record_id < len(leaves):
            raise RuntimeError("GIR node record id out of range")
        if not _is_int(logical_size) or not 0 <= logical_size <= gir.MAX_CHUNK:
            raise RuntimeError("GIR node logical size out of range")
        _sha32(expected, "logical node hash")
        record_ids.append(record_id)
        node_sizes.append(logical_size)

    if sorted(record_ids) != list(range(len(nodes))):
        # Footnote: CMPNX14 writer v1 emits exactly one physical record per logical node.  Rejecting aliases
        # prevents a hostile reader-only grammar from breaking locality/accounting without paying writer cost.
        raise RuntimeError("GIR v1 requires a one-to-one node/physical record mapping")

    total_refs = 0
    total_logical = 0
    for rel, desc in files.items():
        _bounded_relpath(rel)
        if not isinstance(desc, list) or len(desc) != 3:
            raise RuntimeError("malformed GIR file")
        node_ids, logical_size, expected = desc
        if not isinstance(node_ids, list):
            raise RuntimeError("malformed GIR file node list")
        total_refs += len(node_ids)
        if total_refs > MAX_TOTAL_NODE_REFS:
            raise RuntimeError("GIR file-node reference budget exceeded")
        if not _is_int(logical_size) or logical_size < 0:
            raise RuntimeError("GIR file logical size out of range")
        _sha32(expected, "logical file hash")
        measured = 0
        for node_id in node_ids:
            if not _is_int(node_id) or not 0 <= node_id < len(nodes):
                raise RuntimeError("GIR file node id out of range")
            measured += node_sizes[node_id]
            if measured > MAX_TOTAL_MATERIALIZED_BYTES:
                raise RuntimeError("GIR file materialization budget exceeded")
        if measured != logical_size:
            raise RuntimeError("GIR file node sizes do not match declared logical size")
        total_logical += logical_size
        if total_logical > MAX_TOTAL_MATERIALIZED_BYTES:
            # Footnote: this cap belongs to the legacy whole-archive materializer.  A streaming CMPNX14
            # extractor can later lift it while preserving the same storage grammar and per-node bounds.
            raise RuntimeError("GIR archive materialization budget exceeded")


def _decode_meta(
    comp: bytes,
    raw_size: int,
    expected_sha: bytes,
    expected_merkle: bytes,
    expected_count: int | None = None,
) -> tuple[dict, list[int]]:
    if not _is_int(raw_size) or raw_size < 0 or raw_size > gir.MAX_DECODE_UNIT:
        raise RuntimeError("GIR metadata exceeds decode ceiling")
    if len(comp) > gir.MAX_DECODE_UNIT:
        raise RuntimeError("GIR compressed metadata exceeds decode ceiling")
    raw = gir.zd(comp, raw_size)
    if len(raw) != raw_size or gir.H(raw) != expected_sha:
        raise RuntimeError("GIR metadata authentication")
    meta = _bounded_unpack(raw)
    leaves_obj = meta.get("record_leaf_sha256")
    offsets_obj = meta.get("record_rel_offsets")
    if not isinstance(leaves_obj, list) or not isinstance(offsets_obj, list):
        raise RuntimeError("GIR record table must be arrays")
    leaves = list(leaves_obj)
    offsets = list(offsets_obj)
    _validate_meta_schema(meta, leaves, offsets, expected_count, expected_merkle)
    return meta, offsets


def _physical_region_end(stream: BinaryIO) -> int:
    """Return the first byte of duplicate tail metadata, validating the footer declaration."""
    here = stream.tell()
    try:
        stream.seek(0, os.SEEK_END)
        file_size = stream.tell()
        if file_size < gir.FTR.size:
            raise RuntimeError("short GIR archive footer")
        stream.seek(file_size - gir.FTR.size)
        footer = stream.read(gir.FTR.size)
        magic, tail_mcs, tail_mus, _, _ = gir.FTR.unpack(footer)
        if magic != gir.TAIL or tail_mcs > gir.MAX_DECODE_UNIT or tail_mus > gir.MAX_DECODE_UNIT:
            raise RuntimeError("invalid GIR tail declaration")
        end = file_size - gir.FTR.size - tail_mcs
        if end < gir.HDR.size:
            raise RuntimeError("GIR tail metadata overlaps physical region")
        return end
    finally:
        stream.seek(here)


def _validate_physical_table(stream: BinaryIO, record_start: int, offsets: list[int]) -> None:
    """Prove records are in-bounds, non-aliased, gapless, and stop before duplicate metadata."""
    here = stream.tell()
    try:
        physical_end = _physical_region_end(stream)
        if record_start < gir.HDR.size or record_start > physical_end:
            raise RuntimeError("GIR physical table start out of archive bounds")
        final_end = record_start
        for index, offset in enumerate(offsets):
            absolute = record_start + offset
            if absolute < record_start or absolute + gir.PH.size > physical_end:
                raise RuntimeError("GIR physical record header outside archive")
            stream.seek(absolute)
            header = stream.read(gir.PH.size)
            if len(header) != gir.PH.size:
                raise RuntimeError("short GIR physical header")
            codec, usize, csize, _, logical_sha = gir.PH.unpack(header)
            if codec not in (gir.CODEC_RAW, gir.CODEC_ZSTD):
                raise RuntimeError("unknown GIR physical codec")
            if usize > gir.MAX_DECODE_UNIT or csize > gir.MAX_DECODE_UNIT + 1024 * 1024:
                raise RuntimeError("GIR physical record exceeds resource bound")
            _sha32(logical_sha, "physical hash")
            end = offset + gir.PH.size + csize
            if record_start + end > physical_end:
                raise RuntimeError("GIR physical payload outside archive")
            if index + 1 < len(offsets) and end != offsets[index + 1]:
                raise RuntimeError("GIR physical record table is not contiguous")
            final_end = record_start + end
        if final_end != physical_end:
            # Empty archives legitimately have no records; their record_start must still touch tail metadata.
            raise RuntimeError("GIR physical table does not terminate at duplicate metadata")
    finally:
        stream.seek(here)


def _open(path):
    # ``gir._open`` resolves ``gir._decode_meta`` dynamically.  Patching that global makes both the primary
    # and duplicate-tail recovery path share the bounded parser without cloning recovery logic.
    stream, meta, record_start, offsets = _original_open(path)
    try:
        _validate_physical_table(stream, record_start, offsets)
    except Exception:
        stream.close()
        raise
    return stream, meta, record_start, offsets


gir._decode_meta = _decode_meta
gir._open = _open

# Re-export the hardened API.  Build bytes and candidate selection remain exactly the CMPNX14 implementation.
build = gir.build
_build_gir = gir._build_gir
extract = gir.extract
strong_verify = gir.strong_verify
treehash = gir.treehash
MAX_CHUNK = gir.MAX_CHUNK
MAX_DECODE_UNIT = gir.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = gir.MAX_DECODER_MEMORY

if __name__ == "__main__":
    gir._main()
