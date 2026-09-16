"""Bounded streaming reader for the v0.30 release-candidate representations.

The compression reactors intentionally began with conservative verification adapters.  This module closes that
research debt for the two representations that the system tournament may actually publish:

- full G0-G4 Geometry over a Mosaic/Residual graph (``CMPNXG4``);
- depth-1 PrefixGraph (``CMPNXP1``).

Both readers:
- parse authenticated MessagePack under declaration/container limits and reject duplicate map keys;
- validate paths, graph/reference shapes and physical record/payload spans before logical materialization;
- accept either authenticated primary metadata or authenticated duplicate tail metadata, but reject conflicting
  authenticated copies;
- verify/extract one bounded record/node/file at a time instead of materializing the complete logical archive;
- enforce the release-wide <=8x selective decoded-context law;
- publish extraction transactionally through a sibling staging directory and restore the previous destination
  if publication fails.

The inherited accepted-v0.29 grammar still delegates to its already-released reader.  No writer bytes are
changed by this module.

Footnote: this is deliberately a reader *facade* rather than another grammar fork.  Geometry inversion and
Mosaic delta/mosaic reconstruction call the owning implementations.  That keeps the difficult reversible logic
single-sourced while making resource admission, streaming and recovery independently testable.
"""
from __future__ import annotations

import binascii
from collections import OrderedDict
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import uuid

import msgpack
import zstandard as zstd

from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_prefixgraph as PG

A5 = G04.A5
P = A5.P
H = G04.H
PH = G04.PH

MAX_META_BYTES = G04.MAX_DECODE_UNIT
MAX_FILES = 65_536
MAX_NODES = 262_144
MAX_PATH_BYTES = 16 * 1024
MAX_MEMBER_READ_AMP = 8.0
MAX_RECORD_CACHE_BYTES = 64 * 1024 * 1024
MAX_NODE_CACHE_BYTES = 32 * 1024 * 1024
DEFAULT_MAX_EXTRACT_BYTES = 64 * 1024 * 1024 * 1024
MAX_DECLARED_LOGICAL_BYTES = 8 * 1024 * 1024 * 1024 * 1024


def _safe_relpath(rel: str) -> PurePosixPath:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe v0.30 path syntax")
    if len(rel.encode("utf-8")) > MAX_PATH_BYTES:
        raise RuntimeError("v0.30 path exceeds declaration bound")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe v0.30 extraction path")
    return parsed


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        try:
            duplicate = key in result
        except TypeError as exc:
            raise RuntimeError("unhashable MessagePack map key") from exc
        if duplicate:
            raise RuntimeError("duplicate MessagePack map key")
        result[key] = value
    return result


def _bounded_unpack(raw: bytes, *, max_array_len: int, max_map_len: int) -> object:
    if len(raw) > MAX_META_BYTES:
        raise RuntimeError("v0.30 metadata exceeds decode-unit bound")
    try:
        return msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            object_pairs_hook=_pairs_no_duplicates,
            max_array_len=max_array_len,
            max_map_len=max_map_len,
            max_str_len=MAX_META_BYTES,
            max_bin_len=MAX_META_BYTES,
            max_ext_len=0,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("bounded v0.30 metadata decode failed") from exc


def _bytes32(value, label: str) -> bytes:
    if not isinstance(value, bytes) or len(value) != 32:
        raise RuntimeError(f"{label} must be a 32-byte digest")
    return value


def _int(value, label: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise RuntimeError(f"{label} integer declaration")
    if maximum is not None and value > maximum:
        raise RuntimeError(f"{label} exceeds policy")
    return value


def _tree_decl(value) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise RuntimeError("tree SHA-256 declaration")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise RuntimeError("tree SHA-256 declaration is not hex") from exc
    return value


def _cache_put(cache: OrderedDict[int, bytes], cache_bytes: list[int], key: int, value: bytes, limit: int) -> None:
    if len(value) > limit:
        return
    old = cache.pop(key, None)
    if old is not None:
        cache_bytes[0] -= len(old)
    cache[key] = value
    cache_bytes[0] += len(value)
    while cache and cache_bytes[0] > limit:
        _, evicted = cache.popitem(last=False)
        cache_bytes[0] -= len(evicted)


# ------------------------------ G0-G4 / Mosaic reader ------------------------------


def _validate_g04_transform(item) -> None:
    if item is None:
        return
    if not isinstance(item, list) or not item or not isinstance(item[0], str):
        raise RuntimeError("malformed G0-G4 transform descriptor")
    if item[0] == "lane" and len(item) == 3:
        width = _int(item[1], "lane width", minimum=1, maximum=16)
        if width not in G04.O.LANE_WIDTHS:
            raise RuntimeError("unsupported G0-G4 lane width")
        _int(item[2], "lane logical size", maximum=G04.MAX_DECODE_UNIT)
        return
    if item[0] == "delimiter" and len(item) == 3:
        _int(item[1], "delimiter byte", maximum=255)
        _int(item[2], "delimiter logical size", maximum=G04.MAX_DECODE_UNIT)
        return
    if item[0] == "hierarchical" and len(item) == 5:
        _int(item[1], "hierarchical primary", maximum=255)
        _int(item[2], "hierarchical secondary", maximum=255)
        flag = _int(item[3], "hierarchical prefix flag", maximum=1)
        if flag not in (0, 1):
            raise RuntimeError("hierarchical prefix flag")
        _int(item[4], "hierarchical logical size", maximum=G04.MAX_DECODE_UNIT)
        return
    raise RuntimeError("unknown G0-G4 transform descriptor")


def _validate_g04_node(desc, node_count: int, record_count: int) -> None:
    if not isinstance(desc, list) or not desc or not isinstance(desc[0], str):
        raise RuntimeError("malformed Mosaic node descriptor")
    kind = desc[0]
    if kind == "direct" and len(desc) == 5:
        _, record_id, offset, length, expected = desc
        _int(record_id, "direct record id", maximum=record_count - 1)
        _int(offset, "direct offset", maximum=G04.MAX_DECODE_UNIT)
        _int(length, "direct length", maximum=A5.MAX_CHUNK)
        _bytes32(expected, "direct node digest")
        return
    if kind == "delta" and len(desc) == 5:
        _, base_id, record_id, length, expected = desc
        _int(base_id, "delta base id", maximum=node_count - 1)
        _int(record_id, "delta record id", maximum=record_count - 1)
        _int(length, "delta length", maximum=A5.MAX_CHUNK)
        _bytes32(expected, "delta node digest")
        return
    if kind == "delta_pack" and len(desc) == 7:
        _, base_id, record_id, recipe_offset, recipe_len, length, expected = desc
        _int(base_id, "packed delta base id", maximum=node_count - 1)
        _int(record_id, "packed delta record id", maximum=record_count - 1)
        _int(recipe_offset, "packed delta recipe offset", maximum=A5.MAX_RESIDUAL_PACK)
        _int(recipe_len, "packed delta recipe length", maximum=A5.MAX_RESIDUAL_PACK)
        _int(length, "packed delta length", maximum=A5.MAX_CHUNK)
        _bytes32(expected, "packed delta node digest")
        return
    if kind == "mosaic" and len(desc) == 5:
        _, base_ids, record_id, length, expected = desc
        if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= A5.MAX_MOSAIC_BASES:
            raise RuntimeError("mosaic base-list declaration")
        if len(set(base_ids)) != len(base_ids):
            raise RuntimeError("duplicate mosaic base id")
        for base_id in base_ids:
            _int(base_id, "mosaic base id", maximum=node_count - 1)
        _int(record_id, "mosaic record id", maximum=record_count - 1)
        _int(length, "mosaic length", maximum=A5.MAX_CHUNK)
        _bytes32(expected, "mosaic node digest")
        return
    if kind == "pack_mosaic" and len(desc) == 7:
        _, record_id, offset, recipe_len, base_ids, length, expected = desc
        _int(record_id, "pack-mosaic record id", maximum=record_count - 1)
        _int(offset, "pack-mosaic offset", maximum=G04.MAX_DECODE_UNIT)
        _int(recipe_len, "pack-mosaic recipe length", maximum=G04.MAX_DECODE_UNIT)
        if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= A5.MAX_MOSAIC_BASES:
            raise RuntimeError("pack-mosaic base-list declaration")
        if len(set(base_ids)) != len(base_ids):
            raise RuntimeError("duplicate pack-mosaic base id")
        for base_id in base_ids:
            _int(base_id, "pack-mosaic base id", maximum=node_count - 1)
        _int(length, "pack-mosaic length", maximum=A5.MAX_CHUNK)
        _bytes32(expected, "pack-mosaic node digest")
        return
    raise RuntimeError(f"unsupported Mosaic node kind: {kind!r}")


def _validate_g04_meta(meta: object, expected_count: int | None = None) -> dict:
    if not isinstance(meta, dict) or meta.get("engine") != G04.ENGINE:
        raise RuntimeError("unsupported G0-G4 metadata")
    _tree_decl(meta.get("tree_sha256"))
    leaves = meta.get("record_leaf_sha256")
    offsets = meta.get("record_rel_offsets")
    transforms = meta.get("physical_geometry")
    nodes = meta.get("nodes")
    files = meta.get("files")
    if not isinstance(leaves, list) or not isinstance(offsets, list) or not isinstance(transforms, list):
        raise RuntimeError("G0-G4 physical table declaration")
    if not isinstance(nodes, list) or len(nodes) > MAX_NODES:
        raise RuntimeError("G0-G4 node-count declaration")
    if not isinstance(files, dict) or not 1 <= len(files) <= MAX_FILES:
        raise RuntimeError("G0-G4 file-count declaration")
    count = len(leaves)
    if expected_count is not None and count != expected_count:
        raise RuntimeError("G0-G4 header/metadata record-count mismatch")
    if len(offsets) != count or len(transforms) != count:
        raise RuntimeError("G0-G4 physical table length mismatch")
    for leaf in leaves:
        _bytes32(leaf, "G0-G4 payload leaf")
    if G04.O._merkle_root(leaves) is None:  # pragma: no cover - documents the owning Merkle dependency.
        raise RuntimeError("unreachable G0-G4 Merkle state")
    if offsets:
        if offsets[0] != 0:
            raise RuntimeError("G0-G4 first record offset must be zero")
        previous = -1
        for value in offsets:
            value = _int(value, "G0-G4 record offset")
            if value <= previous:
                raise RuntimeError("G0-G4 record offsets are not strictly increasing")
            previous = value
    for item in transforms:
        _validate_g04_transform(item)
    if meta.get("hierarchical_geometry") != dict(G04.HG.RESOURCE_LIMITS):
        raise RuntimeError("G0-G4 hierarchical resource contract drift")
    if float(meta.get("max_geometry_member_read_amplification", MAX_MEMBER_READ_AMP + 1)) > MAX_MEMBER_READ_AMP:
        raise RuntimeError("G0-G4 locality declaration exceeds release policy")
    if int(meta.get("max_decode_unit", G04.MAX_DECODE_UNIT)) > G04.MAX_DECODE_UNIT:
        raise RuntimeError("G0-G4 decode-unit declaration exceeds policy")
    if int(meta.get("max_decoder_memory", G04.MAX_DECODER_MEMORY)) > G04.MAX_DECODER_MEMORY:
        raise RuntimeError("G0-G4 decoder-memory declaration exceeds policy")

    node_count = len(nodes)
    for desc in nodes:
        _validate_g04_node(desc, node_count, count)
    # Dependency depth remains one: every delta/mosaic base must be a direct node.
    for desc in nodes:
        if desc[0] in ("delta", "delta_pack"):
            base_ids = [int(desc[1])]
        elif desc[0] == "mosaic":
            base_ids = list(desc[1])
        elif desc[0] == "pack_mosaic":
            base_ids = list(desc[4])
        else:
            base_ids = []
        if any(nodes[base_id][0] != "direct" for base_id in base_ids):
            raise RuntimeError("G0-G4 Mosaic dependency depth exceeds one")

    total_logical = 0
    for rel, desc in files.items():
        _safe_relpath(rel)
        if not isinstance(desc, list) or not desc or not isinstance(desc[0], str):
            raise RuntimeError("malformed G0-G4 file descriptor")
        if desc[0] == "preflate" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            _int(record_id, "preflate record id", maximum=count - 1)
            size = _int(logical_size, "preflate logical size", maximum=G04.MAX_DECODE_UNIT)
            _bytes32(expected, "preflate file digest")
        elif desc[0] == "nodes" and len(desc) == 4:
            _, node_ids, logical_size, expected = desc
            if not isinstance(node_ids, list):
                raise RuntimeError("G0-G4 file node-list declaration")
            for node_id in node_ids:
                _int(node_id, "file node id", maximum=node_count - 1)
            size = _int(logical_size, "file logical size", maximum=MAX_DECLARED_LOGICAL_BYTES)
            _bytes32(expected, "file digest")
        else:
            raise RuntimeError("unknown G0-G4 file descriptor")
        total_logical += size
        if total_logical > MAX_DECLARED_LOGICAL_BYTES:
            raise RuntimeError("G0-G4 aggregate logical size exceeds policy")
    return meta


def _decode_g04_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_count: int | None) -> dict:
    _int(raw_size, "G0-G4 metadata raw size", maximum=MAX_META_BYTES)
    if len(comp) > MAX_META_BYTES:
        raise RuntimeError("G0-G4 compressed metadata exceeds policy")
    raw = G04.O.zd(comp, raw_size)
    if len(raw) != raw_size or H(raw) != expected_sha:
        raise RuntimeError("G0-G4 metadata authentication")
    meta = _bounded_unpack(raw, max_array_len=MAX_NODES * 8 + 1024, max_map_len=MAX_FILES + 256)
    return _validate_g04_meta(meta, expected_count)


def _g04_open(archive: Path) -> tuple[object, dict, int, list[int], bytes, bool]:
    size = archive.stat().st_size
    stream = archive.open("rb")
    primary = None
    tail = None
    primary_error = None
    tail_error = None

    try:
        try:
            stream.seek(0)
            header = stream.read(G04.HDR.size)
            if len(header) != G04.HDR.size:
                raise RuntimeError("short G0-G4 primary header")
            magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = G04.HDR.unpack(header)
            if magic != G04.MAG:
                raise RuntimeError("not G0-G4 archive")
            _int(mcs, "G0-G4 primary compressed metadata", maximum=MAX_META_BYTES)
            _int(mus, "G0-G4 primary metadata", maximum=MAX_META_BYTES)
            _int(count, "G0-G4 primary record count", maximum=MAX_NODES)
            if max_decode > G04.MAX_DECODE_UNIT or max_memory > G04.MAX_DECODER_MEMORY:
                raise RuntimeError("G0-G4 primary resource declaration exceeds policy")
            comp = stream.read(mcs)
            if len(comp) != mcs:
                raise RuntimeError("short G0-G4 primary metadata")
            meta = _decode_g04_meta(comp, mus, meta_sha, count)
            if G04.O._merkle_root(list(meta["record_leaf_sha256"])) != merkle:
                raise RuntimeError("G0-G4 primary Merkle mismatch")
            primary = (meta, int(mcs), meta_sha, merkle)
        except Exception as exc:
            primary_error = exc

        try:
            if size < G04.FTR.size:
                raise RuntimeError("short G0-G4 tail")
            stream.seek(size - G04.FTR.size)
            footer = stream.read(G04.FTR.size)
            magic, mcs, mus, meta_sha, merkle = G04.FTR.unpack(footer)
            if magic != G04.TAIL:
                raise RuntimeError("G0-G4 tail magic")
            _int(mcs, "G0-G4 tail compressed metadata", maximum=MAX_META_BYTES)
            _int(mus, "G0-G4 tail metadata", maximum=MAX_META_BYTES)
            meta_offset = size - G04.FTR.size - mcs
            if meta_offset < G04.HDR.size:
                raise RuntimeError("G0-G4 tail metadata offset")
            stream.seek(meta_offset)
            comp = stream.read(mcs)
            if len(comp) != mcs:
                raise RuntimeError("short G0-G4 tail metadata")
            meta = _decode_g04_meta(comp, mus, meta_sha, None)
            if G04.O._merkle_root(list(meta["record_leaf_sha256"])) != merkle:
                raise RuntimeError("G0-G4 tail Merkle mismatch")
            tail = (meta, int(mcs), meta_sha, merkle, meta_offset)
        except Exception as exc:
            tail_error = exc

        if primary is None and tail is None:
            raise RuntimeError(
                f"no authenticated G0-G4 metadata: primary={primary_error!r}; tail={tail_error!r}"
            )
        if primary is not None and tail is not None and (primary[2] != tail[2] or primary[3] != tail[3]):
            raise RuntimeError("conflicting authenticated G0-G4 metadata copies")

        chosen = primary if primary is not None else tail
        assert chosen is not None
        meta = chosen[0]
        mcs = chosen[1]
        record_start = G04.HDR.size + mcs
        offsets = list(meta["record_rel_offsets"])

        expected_rel = 0
        for record_id, rel in enumerate(offsets):
            if rel != expected_rel:
                raise RuntimeError("G0-G4 physical table contains gap or overlap")
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short G0-G4 physical header during preflight")
            codec, usize, csize, _crc, _logical_sha = PH.unpack(header)
            if codec not in (G04.O.CODEC_RAW, G04.O.CODEC_ZSTD, G04.O.CODEC_PREFLATE):
                raise RuntimeError("unknown G0-G4 physical codec during preflight")
            _int(usize, "G0-G4 physical decode size", maximum=G04.MAX_DECODE_UNIT)
            _int(csize, "G0-G4 physical payload size", maximum=G04.MAX_DECODE_UNIT + 1024 * 1024)
            expected_rel += PH.size + csize
        physical_end = record_start + expected_rel
        if tail is not None:
            if physical_end != tail[4]:
                raise RuntimeError("G0-G4 physical endpoint does not bind authenticated tail")
        elif physical_end > size:
            raise RuntimeError("G0-G4 physical endpoint exceeds archive")
        return stream, meta, record_start, offsets, chosen[3], tail is not None
    except Exception:
        stream.close()
        raise


class _G04Session:
    def __init__(self, archive: Path):
        self.stream, self.meta, self.record_start, self.offsets, _merkle, self.tail_authenticated = _g04_open(archive)
        self.leaves = self.meta["record_leaf_sha256"]
        self.transforms = self.meta["physical_geometry"]
        self.nodes = self.meta["nodes"]
        self.record_cache: OrderedDict[int, bytes] = OrderedDict()
        self.record_cache_bytes = [0]
        self.node_cache: OrderedDict[int, bytes] = OrderedDict()
        self.node_cache_bytes = [0]
        self.physical_record_reads = 0
        self.max_physical_record_bytes = 0
        self.max_logical_node_bytes = 0

    def close(self) -> None:
        self.stream.close()

    def record(self, record_id: int) -> bytes:
        record_id = _int(record_id, "G0-G4 record id", maximum=len(self.offsets) - 1)
        cached = self.record_cache.pop(record_id, None)
        if cached is not None:
            self.record_cache[record_id] = cached
            return cached
        self.stream.seek(self.record_start + self.offsets[record_id])
        header = self.stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short G0-G4 physical header")
        codec, usize, csize, crc, original_sha = PH.unpack(header)
        if usize > G04.MAX_DECODE_UNIT or csize > G04.MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("G0-G4 physical resource bound")
        payload = self.stream.read(csize)
        if len(payload) != csize or H(payload) != self.leaves[record_id]:
            raise RuntimeError("G0-G4 payload authentication")
        if codec == G04.O.CODEC_RAW:
            physical = payload
        elif codec == G04.O.CODEC_ZSTD:
            physical = G04.O.zd(payload, usize)
        elif codec == G04.O.CODEC_PREFLATE:
            physical = A5.V028._preflate_unpack(payload, usize)
        else:
            raise RuntimeError("unknown G0-G4 physical codec")
        if len(physical) != usize:
            raise RuntimeError("G0-G4 physical size mismatch")

        transform = self.transforms[record_id]
        if transform is None:
            original = physical
        elif transform[0] == "lane":
            original = G04.O.lane_inverse(physical, int(transform[1]), int(transform[2]))
        elif transform[0] == "delimiter":
            original = G04.O.delimiter_inverse(physical, int(transform[2]))
        elif transform[0] == "hierarchical":
            primary, secondary = int(transform[1]), int(transform[2])
            prefix_planes = bool(int(transform[3]))
            logical_size = int(transform[4])
            expected_magic = G04.HG.MAGIC_PREFIX if prefix_planes else G04.HG.MAGIC_PLAIN
            if len(physical) < 6 or physical[:4] != expected_magic or physical[4:6] != bytes((primary, secondary)):
                raise RuntimeError("G0-G4 hierarchy descriptor/physical mismatch")
            original = G04.HG.hierarchy_inverse(physical, logical_size)
        else:  # pragma: no cover - schema admission rejects this before session construction.
            raise RuntimeError("unknown G0-G4 transform")
        if (binascii.crc32(original) & 0xFFFFFFFF) != crc or H(original) != original_sha:
            raise RuntimeError("G0-G4 inverse record integrity")
        self.physical_record_reads += 1
        self.max_physical_record_bytes = max(self.max_physical_record_bytes, len(original))
        _cache_put(self.record_cache, self.record_cache_bytes, record_id, original, MAX_RECORD_CACHE_BYTES)
        return original

    def node(self, node_id: int) -> bytes:
        node_id = _int(node_id, "G0-G4 node id", maximum=len(self.nodes) - 1)
        cached = self.node_cache.pop(node_id, None)
        if cached is not None:
            self.node_cache[node_id] = cached
            return cached
        desc = self.nodes[node_id]
        kind = desc[0]
        if kind == "direct":
            _, record_id, offset, length, expected = desc
            pack = self.record(record_id)
            if offset > len(pack) or length > len(pack) - offset:
                raise RuntimeError("G0-G4 direct slice bounds")
            raw = pack[offset : offset + length]
        elif kind == "delta":
            _, base_id, record_id, length, expected = desc
            raw = P.delta_decode(self.node(base_id), self.record(record_id), expected_size=length, max_output=A5.MAX_CHUNK)
        elif kind == "delta_pack":
            _, base_id, record_id, recipe_offset, recipe_len, length, expected = desc
            pack = self.record(record_id)
            if len(pack) > A5.MAX_RESIDUAL_PACK or recipe_offset > len(pack) or recipe_len > len(pack) - recipe_offset:
                raise RuntimeError("G0-G4 packed-delta recipe bounds")
            if len(pack) / max(1, int(length)) > A5.MAX_ADDITIONAL_RECIPE_AMP:
                raise RuntimeError("G0-G4 packed-delta read amplification")
            recipe = pack[recipe_offset : recipe_offset + recipe_len]
            raw = P.delta_decode(self.node(base_id), recipe, expected_size=length, max_output=A5.MAX_CHUNK)
        elif kind == "mosaic":
            _, base_ids, record_id, length, expected = desc
            raw = P.mosaic_delta_decode(
                [self.node(base_id) for base_id in base_ids],
                self.record(record_id),
                expected_size=length,
                max_bases=A5.MAX_MOSAIC_BASES,
                max_source_bytes=A5.MAX_MOSAIC_SOURCE_INDEX,
                max_output=A5.MAX_CHUNK,
            )
        elif kind == "pack_mosaic":
            _, record_id, offset, recipe_len, base_ids, length, expected = desc
            pack = self.record(record_id)
            if offset > len(pack) or recipe_len > len(pack) - offset:
                raise RuntimeError("G0-G4 pack-mosaic recipe bounds")
            raw = P.mosaic_delta_decode(
                [self.node(base_id) for base_id in base_ids],
                pack[offset : offset + recipe_len],
                expected_size=length,
                max_bases=A5.MAX_MOSAIC_BASES,
                max_source_bytes=A5.MAX_MOSAIC_SOURCE_INDEX,
                max_output=A5.MAX_CHUNK,
            )
        else:  # pragma: no cover - schema admission rejects this first.
            raise RuntimeError("unknown G0-G4 node kind")
        if len(raw) > A5.MAX_CHUNK or H(raw) != expected:
            raise RuntimeError("G0-G4 logical node integrity")
        self.max_logical_node_bytes = max(self.max_logical_node_bytes, len(raw))
        _cache_put(self.node_cache, self.node_cache_bytes, node_id, raw, MAX_NODE_CACHE_BYTES)
        return raw


def _consume_g04_file(session: _G04Session, rel: str, desc: list, tree, target_root: Path | None) -> int:
    safe = _safe_relpath(rel)
    expected_size = int(desc[2])
    expected_hash = desc[3]
    rel_bytes = rel.encode("utf-8")
    tree.update(len(rel_bytes).to_bytes(4, "little"))
    tree.update(rel_bytes)
    tree.update(expected_size.to_bytes(8, "little"))
    file_hash = hashlib.sha256()
    written = 0
    output = None
    try:
        if target_root is not None:
            target = target_root.joinpath(*safe.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            output = target.open("wb")
        if desc[0] == "preflate":
            chunks = [session.record(int(desc[1]))]
        else:
            chunks = (session.node(int(node_id)) for node_id in desc[1])
        for raw in chunks:
            written += len(raw)
            if written > expected_size:
                raise RuntimeError("G0-G4 streamed file exceeds declared size")
            file_hash.update(raw)
            tree.update(raw)
            if output is not None:
                output.write(raw)
    finally:
        if output is not None:
            output.close()
    if written != expected_size or file_hash.digest() != expected_hash:
        raise RuntimeError("G0-G4 streamed file integrity")
    return written


def _stream_g04(archive: Path, target_root: Path | None, max_output_bytes: int) -> dict:
    session = _G04Session(archive)
    tree = hashlib.sha256()
    logical = 0
    files = 0
    try:
        for rel in sorted(session.meta["files"]):
            logical += _consume_g04_file(session, rel, session.meta["files"][rel], tree, target_root)
            if logical > max_output_bytes:
                raise RuntimeError("G0-G4 extraction exceeds caller output budget")
            files += 1
        got = tree.hexdigest()
        expected = session.meta["tree_sha256"]
        if got != expected:
            raise RuntimeError("G0-G4 streamed tree identity mismatch")
        return {
            "ok": True,
            "engine": G04.ENGINE,
            "reader": "v030-release-streaming-g04-v1",
            "files": files,
            "logical_bytes": logical,
            "tree_sha256": got,
            "max_member_read_amplification": float(session.meta["max_geometry_member_read_amplification"]),
            "max_physical_record_bytes": session.max_physical_record_bytes,
            "max_logical_node_bytes": session.max_logical_node_bytes,
            "record_cache_peak_bound_bytes": MAX_RECORD_CACHE_BYTES,
            "node_cache_peak_bound_bytes": MAX_NODE_CACHE_BYTES,
            "physical_record_reads": session.physical_record_reads,
            "tail_metadata_authenticated": session.tail_authenticated,
        }
    finally:
        session.close()


# ------------------------------ PrefixGraph reader ------------------------------


def _validate_pg_meta(meta: object) -> dict:
    if not isinstance(meta, dict) or meta.get("v") != 1 or meta.get("engine") != "PrefixGraph-depth1-v1":
        raise RuntimeError("unsupported PrefixGraph metadata")
    _tree_decl(meta.get("tree_sha256"))
    rels = meta.get("files")
    records = meta.get("records")
    if not isinstance(rels, list) or not isinstance(records, list) or len(rels) != len(records):
        raise RuntimeError("PrefixGraph file/record table declaration")
    if not 1 <= len(records) <= PG.MAX_FILES:
        raise RuntimeError("PrefixGraph record-count policy")
    seen_paths = set()
    for rel in rels:
        _safe_relpath(rel)
        if rel in seen_paths:
            raise RuntimeError("duplicate PrefixGraph logical path")
        seen_paths.add(rel)
    for index, desc in enumerate(records):
        if not isinstance(desc, list) or len(desc) != 6:
            raise RuntimeError("malformed PrefixGraph record")
        kind, base, usize, csize, payload_sha, logical_sha = desc
        usize = _int(usize, "PrefixGraph logical size", maximum=PG.MAX_FILE_BYTES)
        _int(csize, "PrefixGraph payload size", maximum=PG.MAX_FILE_BYTES + 1024 * 1024)
        _bytes32(payload_sha, "PrefixGraph payload digest")
        _bytes32(logical_sha, "PrefixGraph logical digest")
        if kind == "direct":
            if int(base) != -1:
                raise RuntimeError("PrefixGraph direct record has a base")
        elif kind == "prefix":
            base = _int(base, "PrefixGraph base id", maximum=len(records) - 1)
            if base == index or records[base][0] != "direct":
                raise RuntimeError("PrefixGraph dependency depth exceeds one")
            anchor_size = _int(records[base][2], "PrefixGraph anchor size", maximum=PG.MAX_FILE_BYTES)
            amp = (usize + anchor_size) / max(1, usize)
            if amp > MAX_MEMBER_READ_AMP:
                raise RuntimeError("PrefixGraph selective-read amplification exceeds release policy")
        else:
            raise RuntimeError("unknown PrefixGraph record kind")
    if int(meta.get("max_dependency_depth", 99)) > 1:
        raise RuntimeError("PrefixGraph dependency-depth declaration")
    return meta


def _decode_pg_meta(comp: bytes, raw_size: int, expected_sha: bytes) -> dict:
    _int(raw_size, "PrefixGraph metadata raw size", maximum=PG.MAX_META_BYTES)
    if len(comp) > PG.MAX_META_BYTES:
        raise RuntimeError("PrefixGraph compressed metadata bound")
    raw = zstd.ZstdDecompressor().decompress(comp, max_output_size=raw_size)
    if len(raw) != raw_size or PG.H(raw) != expected_sha:
        raise RuntimeError("PrefixGraph metadata authentication")
    meta = _bounded_unpack(raw, max_array_len=PG.MAX_FILES * 8 + 64, max_map_len=PG.MAX_FILES + 64)
    return _validate_pg_meta(meta)


def _pg_open(archive: Path) -> tuple[object, dict, int, list[int], bool]:
    size = archive.stat().st_size
    stream = archive.open("rb")
    primary = None
    tail = None
    primary_error = None
    tail_error = None
    try:
        try:
            stream.seek(0)
            header = stream.read(PG.HEADER.size)
            if len(header) != PG.HEADER.size:
                raise RuntimeError("short PrefixGraph primary header")
            magic, mcs, mus, meta_sha = PG.HEADER.unpack(header)
            if magic != PG.MAGIC:
                raise RuntimeError("not PrefixGraph archive")
            _int(mcs, "PrefixGraph compressed metadata", maximum=PG.MAX_META_BYTES)
            comp = stream.read(mcs)
            if len(comp) != mcs:
                raise RuntimeError("short PrefixGraph primary metadata")
            meta = _decode_pg_meta(comp, mus, meta_sha)
            primary = (meta, int(mcs), meta_sha)
        except Exception as exc:
            primary_error = exc

        try:
            if size < PG.FOOTER.size:
                raise RuntimeError("short PrefixGraph tail")
            stream.seek(size - PG.FOOTER.size)
            footer = stream.read(PG.FOOTER.size)
            magic, mcs, mus, meta_sha = PG.FOOTER.unpack(footer)
            if magic != PG.TAIL:
                raise RuntimeError("PrefixGraph tail magic")
            _int(mcs, "PrefixGraph tail compressed metadata", maximum=PG.MAX_META_BYTES)
            meta_offset = size - PG.FOOTER.size - mcs
            if meta_offset < PG.HEADER.size:
                raise RuntimeError("PrefixGraph tail metadata offset")
            stream.seek(meta_offset)
            comp = stream.read(mcs)
            if len(comp) != mcs:
                raise RuntimeError("short PrefixGraph tail metadata")
            meta = _decode_pg_meta(comp, mus, meta_sha)
            tail = (meta, int(mcs), meta_sha, meta_offset)
        except Exception as exc:
            tail_error = exc

        if primary is None and tail is None:
            raise RuntimeError(
                f"no authenticated PrefixGraph metadata: primary={primary_error!r}; tail={tail_error!r}"
            )
        if primary is not None and tail is not None and primary[2] != tail[2]:
            raise RuntimeError("conflicting authenticated PrefixGraph metadata copies")
        chosen = primary if primary is not None else tail
        assert chosen is not None
        meta = chosen[0]
        mcs = chosen[1]
        payload_start = PG.HEADER.size + mcs
        offsets: list[int] = []
        cursor = 0
        for desc in meta["records"]:
            offsets.append(cursor)
            cursor += int(desc[3])
        payload_end = payload_start + cursor
        if tail is not None:
            if payload_end != tail[3]:
                raise RuntimeError("PrefixGraph payload endpoint does not bind authenticated tail")
        elif payload_end > size:
            raise RuntimeError("PrefixGraph payload endpoint exceeds archive")
        return stream, meta, payload_start, offsets, tail is not None
    except Exception:
        stream.close()
        raise


class _PGSession:
    def __init__(self, archive: Path):
        self.stream, self.meta, self.payload_start, self.offsets, self.tail_authenticated = _pg_open(archive)
        self.records = self.meta["records"]
        self.anchor_cache: OrderedDict[int, bytes] = OrderedDict()
        self.anchor_cache_bytes = [0]
        self.max_member_read_amplification = 1.0
        self.max_file_bytes = 0

    def close(self) -> None:
        self.stream.close()

    def _payload(self, index: int) -> bytes:
        desc = self.records[index]
        csize = int(desc[3])
        self.stream.seek(self.payload_start + self.offsets[index])
        payload = self.stream.read(csize)
        if len(payload) != csize or PG.H(payload) != desc[4]:
            raise RuntimeError("PrefixGraph payload authentication")
        return payload

    def file(self, index: int) -> bytes:
        desc = self.records[index]
        kind, base, usize, _csize, _payload_sha, expected = desc
        usize = int(usize)
        payload = self._payload(index)
        if kind == "direct":
            raw = zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
        else:
            base = int(base)
            anchor = self.anchor_cache.pop(base, None)
            if anchor is None:
                anchor_desc = self.records[base]
                anchor_payload = self._payload(base)
                anchor = zstd.ZstdDecompressor().decompress(anchor_payload, max_output_size=int(anchor_desc[2]))
                if len(anchor) != int(anchor_desc[2]) or PG.H(anchor) != anchor_desc[5]:
                    raise RuntimeError("PrefixGraph anchor logical integrity")
                _cache_put(self.anchor_cache, self.anchor_cache_bytes, base, anchor, MAX_RECORD_CACHE_BYTES)
            else:
                self.anchor_cache[base] = anchor
            amp = (usize + len(anchor)) / max(1, usize)
            self.max_member_read_amplification = max(self.max_member_read_amplification, amp)
            dictionary = zstd.ZstdCompressionDict(anchor, dict_type=zstd.DICT_TYPE_RAWCONTENT)
            raw = zstd.ZstdDecompressor(dict_data=dictionary).decompress(payload, max_output_size=usize)
        if len(raw) != usize or PG.H(raw) != expected:
            raise RuntimeError("PrefixGraph logical file integrity")
        self.max_file_bytes = max(self.max_file_bytes, len(raw))
        return raw


def _stream_pg(archive: Path, target_root: Path | None, max_output_bytes: int) -> dict:
    session = _PGSession(archive)
    tree = hashlib.sha256()
    logical = 0
    try:
        for index, rel in enumerate(session.meta["files"]):
            safe = _safe_relpath(rel)
            raw = session.file(index)
            logical += len(raw)
            if logical > max_output_bytes:
                raise RuntimeError("PrefixGraph extraction exceeds caller output budget")
            rel_bytes = rel.encode("utf-8")
            tree.update(len(rel_bytes).to_bytes(4, "little"))
            tree.update(rel_bytes)
            tree.update(len(raw).to_bytes(8, "little"))
            tree.update(raw)
            if target_root is not None:
                target = target_root.joinpath(*safe.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        got = tree.hexdigest()
        if got != session.meta["tree_sha256"]:
            raise RuntimeError("PrefixGraph streamed tree identity mismatch")
        if session.max_member_read_amplification > MAX_MEMBER_READ_AMP:
            raise RuntimeError("PrefixGraph streamed locality exceeds release policy")
        return {
            "ok": True,
            "engine": "PrefixGraph-depth1-v1",
            "reader": "v030-release-streaming-prefixgraph-v1",
            "files": len(session.meta["files"]),
            "logical_bytes": logical,
            "tree_sha256": got,
            "max_member_read_amplification": session.max_member_read_amplification,
            "max_file_bytes": session.max_file_bytes,
            "anchor_cache_peak_bound_bytes": MAX_RECORD_CACHE_BYTES,
            "tail_metadata_authenticated": session.tail_authenticated,
        }
    finally:
        session.close()


# ------------------------------ public facade ------------------------------


def _magic(archive: Path) -> bytes:
    with archive.open("rb") as stream:
        return stream.read(8)


def strong_verify(archive: Path) -> dict:
    magic = _magic(archive)
    try:
        if magic == G04.MAG:
            return _stream_g04(archive, None, MAX_DECLARED_LOGICAL_BYTES)
        if magic == PG.MAGIC:
            return _stream_pg(archive, None, MAX_DECLARED_LOGICAL_BYTES)
        result = G04.BASE.strong_verify(archive)
        result = dict(result)
        result["reader"] = "accepted-v029-reader"
        return result
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "reader": "v030-release-streaming-v1",
            "representation": (
                "g04" if magic == G04.MAG else "prefixgraph" if magic == PG.MAGIC else "accepted-v029"
            ),
        }


def _remove_backup_best_effort(backup: Path) -> None:
    try:
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink(missing_ok=True)
    except OSError:
        # Footnote: once a fully verified staging tree is published, stale-backup cleanup failure is not an
        # archive-integrity failure.  Keeping the uniquely named backup is safer than pretending publication
        # did not already succeed.
        pass


def _transactional_extract(archive: Path, dst: Path, streamer, max_output_bytes: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.v030-stage-", dir=dst.parent))
    backup = dst.parent / f".{dst.name}.v030-backup-{uuid.uuid4().hex}"
    moved_old = False
    installed_new = False
    try:
        streamer(archive, staging, max_output_bytes)
        if dst.exists() or dst.is_symlink():
            os.replace(dst, backup)
            moved_old = True
        os.replace(staging, dst)
        installed_new = True
    except Exception:
        if not installed_new:
            shutil.rmtree(staging, ignore_errors=True)
        if moved_old and not (dst.exists() or dst.is_symlink()) and (backup.exists() or backup.is_symlink()):
            os.replace(backup, dst)
        raise
    else:
        if moved_old:
            _remove_backup_best_effort(backup)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = DEFAULT_MAX_EXTRACT_BYTES) -> None:
    max_output_bytes = _int(max_output_bytes, "extraction output budget", minimum=1, maximum=MAX_DECLARED_LOGICAL_BYTES)
    magic = _magic(archive)
    if magic == G04.MAG:
        _transactional_extract(archive, dst, _stream_g04, max_output_bytes)
    elif magic == PG.MAGIC:
        _transactional_extract(archive, dst, _stream_pg, max_output_bytes)
    else:
        G04.BASE.extract(archive, dst)


def treehash(root: Path) -> str:
    return G04.treehash(root)
