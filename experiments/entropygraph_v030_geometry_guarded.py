"""Adversarial reader hardening for the CMPCT v0.30 Geometry research seed.

This layer changes **no writer bytes**.  It imports the cell-bounded Geometry facade and replaces only
metadata decoding / physical-table admission with stricter validators before the existing reader may
materialize a logical node or file.

The current research reader returns an in-memory ``dict[str, bytes]`` for an entire archive.  Until that
implementation becomes streaming, this module also gives the whole logical output an explicit ceiling equal
to the already-declared decoder-memory budget.  That is intentionally conservative: promotion must not call
an unbounded materializer "bounded" merely because each individual node is <=512 KiB.

Footnote: a future streaming reader can remove the archive-output ceiling without changing CMPNX13 bytes.
The security law is the durable part: container counts, references, physical spans and per-operation working
sets must be bounded *before* allocation or decompression.
"""
from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import BinaryIO

import msgpack

from experiments import entropygraph_v030_geometry_safe as safe

geometry = safe.geometry

MAX_METADATA_FILES = 65_536
MAX_METADATA_NODES = 131_072
MAX_METADATA_CONTAINER_ITEMS = 1_000_000
MAX_TOTAL_NODE_REFS = 1_000_000
MAX_PATH_BYTES = 16 * 1024
MAX_META_BINARY_BYTES = 64
MAX_TOTAL_MATERIALIZED_BYTES = geometry.MAX_DECODER_MEMORY

_original_open = geometry._open


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _sha32(value: object, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != 32:
        raise RuntimeError(f"Geometry {label} must be a 32-byte SHA-256")
    return value


def _bounded_relpath(rel: object) -> PurePosixPath:
    if not isinstance(rel, str) or len(rel.encode("utf-8")) > MAX_PATH_BYTES:
        raise RuntimeError("Geometry path exceeds metadata policy")
    return geometry._safe_relpath(rel)


def _no_duplicate_map(pairs: list[tuple[object, object]]) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise RuntimeError("Geometry metadata contains duplicate map key")
        out[key] = value
    return out


def _bounded_unpack(raw: bytes) -> dict:
    """Decode MessagePack only after imposing container and scalar-size ceilings.

    Footnote: authenticating compressed metadata proves bytes were not accidentally altered; it does not
    make attacker-authored container counts safe.  These limits are therefore parser invariants, not an
    integrity substitute.
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
        raise RuntimeError(f"Geometry bounded metadata decode failed: {exc}") from exc
    if not isinstance(meta, dict):
        raise RuntimeError("Geometry metadata root must be a map")
    return meta


def _validate_meta_schema(
    meta: dict,
    leaves: list[bytes],
    offsets: list[int],
    expected_count: int | None,
    expected_merkle: bytes,
) -> None:
    if meta.get("v") != 1 or meta.get("engine") != "Geometry-Compiler-v1":
        raise RuntimeError("unsupported Geometry metadata")
    if meta.get("max_dependency_depth") != 0:
        raise RuntimeError("Geometry dependency depth exceeds policy")

    bounded_scalars = (
        ("max_chunk", geometry.MAX_CHUNK),
        ("max_decode_unit", geometry.MAX_DECODE_UNIT),
        ("max_decoder_memory", geometry.MAX_DECODER_MEMORY),
        ("max_delimiter_candidates", geometry.MAX_DELIMITER_CANDIDATES),
        ("max_delimiter_segments", geometry.MAX_DELIMITER_SEGMENTS),
    )
    for key, ceiling in bounded_scalars:
        value = meta.get(key)
        if not _is_int(value) or value < 0 or value > ceiling:
            raise RuntimeError(f"Geometry {key} exceeds policy")

    read_amp = meta.get("max_read_amplification")
    if not isinstance(read_amp, (int, float)) or isinstance(read_amp, bool) or read_amp < 0 or read_amp > 1.0:
        raise RuntimeError("Geometry read-amplification declaration exceeds seed policy")
    if meta.get("lane_widths") != list(geometry.LANE_WIDTHS):
        raise RuntimeError("Geometry lane-width declaration mismatch")

    tree = meta.get("tree_sha256")
    if not isinstance(tree, str) or len(tree) != 64 or any(ch not in "0123456789abcdef" for ch in tree):
        raise RuntimeError("Geometry tree identity declaration is malformed")

    if not isinstance(leaves, list) or not isinstance(offsets, list):
        raise RuntimeError("Geometry record table must be arrays")
    if len(leaves) > MAX_METADATA_NODES:
        raise RuntimeError("Geometry record-count policy exceeded")
    if expected_count is not None and (not _is_int(expected_count) or len(leaves) != expected_count):
        raise RuntimeError("Geometry record-count mismatch")
    for leaf in leaves:
        _sha32(leaf, "record leaf")
    if geometry._merkle_root(leaves) != expected_merkle:
        raise RuntimeError("Geometry Merkle mismatch")
    if len(offsets) != len(leaves):
        raise RuntimeError("Geometry record table length mismatch")
    if offsets:
        if offsets[0] != 0:
            raise RuntimeError("Geometry first physical record must begin at relative offset zero")
        previous = -1
        for value in offsets:
            if not _is_int(value) or value < 0 or value <= previous:
                raise RuntimeError("Geometry record offsets must be strictly increasing")
            previous = value

    nodes = meta.get("nodes")
    files = meta.get("files")
    if not isinstance(nodes, list) or not isinstance(files, dict):
        raise RuntimeError("Geometry files/nodes metadata shape")
    if len(nodes) > MAX_METADATA_NODES or len(files) > MAX_METADATA_FILES:
        raise RuntimeError("Geometry metadata object-count policy exceeded")
    if len(nodes) != len(leaves):
        # Writer v1 emits exactly one authenticated physical record per unique logical node.  Allowing
        # arbitrary aliasing here would create a second, unmeasured grammar and complicate locality proofs.
        raise RuntimeError("Geometry node/physical record cardinality mismatch")

    record_ids: list[int] = []
    node_sizes: list[int] = []
    for desc in nodes:
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed Geometry node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            if not _is_int(width) or width not in geometry.LANE_WIDTHS:
                raise RuntimeError("Geometry lane width out of policy")
        elif kind == "delimiter" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
        else:
            raise RuntimeError("unknown or malformed Geometry node kind")
        if not _is_int(record_id) or not 0 <= record_id < len(leaves):
            raise RuntimeError("Geometry node record id out of range")
        if not _is_int(logical_size) or not 0 <= logical_size <= geometry.MAX_CHUNK:
            raise RuntimeError("Geometry node logical size out of range")
        _sha32(expected, "logical node hash")
        record_ids.append(record_id)
        node_sizes.append(logical_size)

    if sorted(record_ids) != list(range(len(nodes))):
        raise RuntimeError("Geometry v1 requires a one-to-one node/physical record mapping")

    total_refs = 0
    total_logical = 0
    for rel, desc in files.items():
        _bounded_relpath(rel)
        if not isinstance(desc, list) or len(desc) != 3:
            raise RuntimeError("malformed Geometry file")
        node_ids, logical_size, expected = desc
        if not isinstance(node_ids, list):
            raise RuntimeError("malformed Geometry file node list")
        total_refs += len(node_ids)
        if total_refs > MAX_TOTAL_NODE_REFS:
            raise RuntimeError("Geometry file-node reference budget exceeded")
        if not _is_int(logical_size) or logical_size < 0:
            raise RuntimeError("Geometry file logical size out of range")
        _sha32(expected, "logical file hash")
        measured = 0
        for node_id in node_ids:
            if not _is_int(node_id) or not 0 <= node_id < len(nodes):
                raise RuntimeError("Geometry file node id out of range")
            measured += node_sizes[node_id]
            if measured > MAX_TOTAL_MATERIALIZED_BYTES:
                raise RuntimeError("Geometry file materialization budget exceeded")
        if measured != logical_size:
            raise RuntimeError("Geometry file node sizes do not match declared logical size")
        total_logical += logical_size
        if total_logical > MAX_TOTAL_MATERIALIZED_BYTES:
            # Footnote: the present reader accumulates every output file in memory.  This guard is scoped
            # to that implementation, not to the archive concept; a streaming extractor can later relax it.
            raise RuntimeError("Geometry archive materialization budget exceeded")


def _decode_meta(
    comp: bytes,
    raw_size: int,
    expected_sha: bytes,
    expected_merkle: bytes,
    expected_count: int | None = None,
) -> tuple[dict, list[int]]:
    if not _is_int(raw_size) or raw_size < 0 or raw_size > geometry.MAX_DECODE_UNIT:
        raise RuntimeError("Geometry metadata exceeds decode ceiling")
    raw = geometry.zd(comp, raw_size)
    if len(raw) != raw_size or geometry.H(raw) != expected_sha:
        raise RuntimeError("Geometry metadata authentication")
    meta = _bounded_unpack(raw)

    leaves_obj = meta.get("record_leaf_sha256")
    offsets_obj = meta.get("record_rel_offsets")
    if not isinstance(leaves_obj, list) or not isinstance(offsets_obj, list):
        raise RuntimeError("Geometry record table must be arrays")
    # Do not coerce arbitrary attacker objects through int(); only actual bounded integers are admitted.
    leaves = list(leaves_obj)
    offsets = list(offsets_obj)
    _validate_meta_schema(meta, leaves, offsets, expected_count, expected_merkle)
    return meta, offsets


def _validate_physical_table(stream: BinaryIO, record_start: int, offsets: list[int]) -> None:
    """Prove physical record spans cannot overlap or alias before any payload is decoded."""
    here = stream.tell()
    try:
        stream.seek(0, os.SEEK_END)
        file_size = stream.tell()
        if record_start < geometry.HDR.size or record_start > file_size:
            raise RuntimeError("Geometry physical table start out of archive bounds")
        for index, offset in enumerate(offsets):
            absolute = record_start + offset
            if absolute < record_start or absolute + geometry.PH.size > file_size:
                raise RuntimeError("Geometry physical record header outside archive")
            stream.seek(absolute)
            header = stream.read(geometry.PH.size)
            if len(header) != geometry.PH.size:
                raise RuntimeError("short Geometry physical header")
            codec, usize, csize, _, _ = geometry.PH.unpack(header)
            if codec not in (geometry.CODEC_RAW, geometry.CODEC_ZSTD):
                raise RuntimeError("unknown Geometry physical codec")
            if usize > geometry.MAX_DECODE_UNIT or csize > geometry.MAX_DECODE_UNIT + 1024 * 1024:
                raise RuntimeError("Geometry physical record exceeds resource bound")
            end = offset + geometry.PH.size + csize
            if record_start + end > file_size:
                raise RuntimeError("Geometry physical payload outside archive")
            if index + 1 < len(offsets) and end != offsets[index + 1]:
                # Writer v1 emits a contiguous table.  Rejecting both overlap and gaps prevents two ids
                # from aliasing one physical header and keeps locality/accounting tied to stored bytes.
                raise RuntimeError("Geometry physical record table is not contiguous")
    finally:
        stream.seek(here)


def _open(path):
    # The original function resolves ``geometry._decode_meta`` at call time, so patching that global below
    # makes both primary and authenticated-tail recovery use the bounded decoder without duplicating recovery.
    stream, meta, record_start, offsets = _original_open(path)
    try:
        _validate_physical_table(stream, record_start, offsets)
    except Exception:
        stream.close()
        raise
    return stream, meta, record_start, offsets


geometry._decode_meta = _decode_meta
geometry._open = _open

# Re-export the now doubly-bounded research API.  Build bytes are unchanged; only reader admission changed.
build = geometry.build
extract = geometry.extract
strong_verify = geometry.strong_verify
treehash = geometry.treehash
MAX_CHUNK = geometry.MAX_CHUNK
MAX_DECODE_UNIT = geometry.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = geometry.MAX_DECODER_MEMORY
MAX_DELIMITER_CELL_SCANS = safe.MAX_DELIMITER_CELL_SCANS

if __name__ == "__main__":
    geometry._main()
