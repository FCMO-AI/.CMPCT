"""CMPCT v0.30 production candidate — canonical r24 -> r25 physical Geometry compiler.

This is the bridge from successful research transforms to a real archive contract.  It deliberately does *not*
rebuild a file tree with a new research container.  Instead it first consumes a canonical r24 archive and keeps
its logical index semantics (directories, links, sparse layouts, CDC/range boundaries, nested-ZIP recipes,
ownership/xattrs and blob identities) intact.  Only a blob's physical codec is replaced when a fully charged
Geometry representation is smaller than the existing physical payload + metadata.

Revision 25 therefore introduces exactly one new physical codec in this seed: ``CODEC_GEOMETRY``.  The codec
contains independently bounded <=512 KiB representation chunks chosen by the production Representation
Compiler (G0-G5 at this branch head).  Each chunk carries its reversible representation descriptor, inner raw/
Zstd codec, physical length and logical SHA-256.  The outer canonical blob header keeps the original logical
size, CRC32 and SHA-256, so the existing file/recipe graph continues to authenticate the same bytes.

Footnote: exact Deflate blobs are not rewritten.  Some virtual-ZIP recipes intentionally ask the reader for the
*stored Deflate stream* rather than the logical content; preserving CODEC_DEFLATE keeps that zero-recompression
compatibility contract intact.  Other codecs may be replaced because their public meaning is simply "produce
these logical blob bytes".

This module remains an evidence engine until the same codec is ported into ``src/cmpct`` and ``cmpct-core``.
It exists so productionization is measured against canonical archive semantics rather than a benchmark-only
file tree.  Project version and canonical production revision remain unchanged until those parity gates pass.
"""
from __future__ import annotations

import binascii
import copy
import hashlib
import mmap
import os
from pathlib import Path
import shutil
import struct
import tempfile
from typing import Iterable

import msgpack

from cmpct.builder import Builder
from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE, FTR, HDR,
    sha, zc, zd,
)
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_representation_compiler as RC

V25_MAGIC = b"CMPCT25\0"
V25_FMAGIC = b"CMPTF25\0"
V25_VERSION = 25
CODEC_GEOMETRY = 5
MIN_BLOB_NET_SAVING = 64
MAX_GEOMETRY_BLOB = 64 * 1024 * 1024
MAX_GEOMETRY_CHUNKS = 256
MAX_GEOMETRY_META_RAW = 1024 * 1024
GEO_META_HEADER = struct.Struct("<4sBI")  # magic, envelope codec (0 raw/1 Zstd), raw metadata bytes
GEO_META_MAGIC = b"G25M"


def _bytes32(value, label: str) -> bytes:
    if not isinstance(value, (bytes, bytearray)) or len(value) != 32:
        raise IOError(f"invalid r25 {label} hash")
    return bytes(value)


def _pack_geometry_meta(rows: list[list]) -> bytes:
    raw = msgpack.packb([1, rows], use_bin_type=True)
    if len(raw) > MAX_GEOMETRY_META_RAW:
        raise ValueError("r25 Geometry metadata exceeds raw bound")
    comp = zc(raw, 12)
    if len(comp) < len(raw):
        return GEO_META_HEADER.pack(GEO_META_MAGIC, 1, len(raw)) + comp
    return GEO_META_HEADER.pack(GEO_META_MAGIC, 0, len(raw)) + raw


def _unpack_geometry_meta(meta: bytes) -> list[list]:
    if len(meta) < GEO_META_HEADER.size or len(meta) > MAX_GEOMETRY_META_RAW + GEO_META_HEADER.size:
        raise IOError("r25 Geometry metadata envelope exceeds bound")
    magic, codec, raw_size = GEO_META_HEADER.unpack_from(meta, 0)
    if magic != GEO_META_MAGIC or raw_size > MAX_GEOMETRY_META_RAW:
        raise IOError("invalid r25 Geometry metadata envelope")
    body = meta[GEO_META_HEADER.size:]
    if codec == 0:
        raw = body
    elif codec == 1:
        raw = zd(body, raw_size)
    else:
        raise IOError("unknown r25 Geometry metadata envelope codec")
    if len(raw) != raw_size:
        raise IOError("r25 Geometry metadata size mismatch")
    try:
        decoded = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    except Exception as exc:
        raise IOError("malformed r25 Geometry metadata") from exc
    if not isinstance(decoded, list) or len(decoded) != 2 or decoded[0] != 1 or not isinstance(decoded[1], list):
        raise IOError("unsupported r25 Geometry metadata version")
    rows = decoded[1]
    if not 1 <= len(rows) <= MAX_GEOMETRY_CHUNKS:
        raise IOError("r25 Geometry chunk table out of bounds")
    return rows


def _logical_chunks(raw: bytes) -> list[bytes]:
    if len(raw) <= RC.G.MAX_CHUNK:
        return [raw]
    rows = list(RC.G.L._balanced_chunks(raw))
    if not rows or b"".join(rows) != raw or any(len(row) > RC.G.MAX_CHUNK for row in rows):
        raise RuntimeError("r25 Geometry logical chunking invariant failed")
    if len(rows) > MAX_GEOMETRY_CHUNKS:
        raise ValueError("r25 Geometry blob would exceed chunk-count bound")
    return rows


def encode_geometry_blob(raw: bytes) -> tuple[bytes, bytes, dict] | None:
    """Return (payload, metadata, stats) for a bounded Geometry blob candidate."""
    if len(raw) > MAX_GEOMETRY_BLOB:
        return None
    payload_parts: list[bytes] = []
    descriptors: list[list] = []
    kind_counts: dict[str, int] = {}
    incremental_g5 = 0
    for chunk in _logical_chunks(raw):
        selected = RC.encode_node(chunk)
        restored = RC.inverse_physical(
            str(selected["kind"]), selected.get("param", 0), selected["physical"], len(chunk)
        )
        if restored != chunk:
            raise RuntimeError("r25 Geometry writer selected a non-invertible representation")
        kind = str(selected["kind"])
        param = selected.get("param", 0)
        # Tuple parameters become ordinary MessagePack arrays; the decoder normalizes them by kind.
        if kind == "lane_perm":
            width, permutation = param
            param = [int(width), bytes(permutation)]
        elif kind in {"lane", "hierarchical"}:
            param = int(param)
        else:
            param = 0
        inner_codec = int(selected["codec"])
        if inner_codec not in {CODEC_RAW, CODEC_ZSTD}:
            raise RuntimeError("r25 Geometry selected unsupported inner codec")
        part = bytes(selected["payload"])
        descriptors.append([
            kind,
            param,
            len(chunk),
            len(selected["physical"]),
            inner_codec,
            len(part),
            sha(chunk),
        ])
        payload_parts.append(part)
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        incremental_g5 += int(selected.get("incremental_stored_saving_vs_g0_g4", 0))
    meta = _pack_geometry_meta(descriptors)
    payload = b"".join(payload_parts)
    return payload, meta, {
        "chunks": len(descriptors),
        "kind_counts": kind_counts,
        "incremental_g5_stored_saving": incremental_g5,
        "metadata_bytes": len(meta),
        "payload_bytes": len(payload),
    }


def decode_geometry_blob(comp: bytes, meta: bytes, logical_size: int) -> bytes:
    if logical_size < 0 or logical_size > MAX_GEOMETRY_BLOB:
        raise IOError("r25 Geometry logical blob exceeds bound")
    rows = _unpack_geometry_meta(meta)
    cursor = 0
    logical_total = 0
    out: list[bytes] = []
    for desc in rows:
        if not isinstance(desc, list) or len(desc) != 7:
            raise IOError("malformed r25 Geometry chunk descriptor")
        kind, param, chunk_size, physical_size, inner_codec, csize, logical_hash = desc
        if not isinstance(kind, str) or kind not in {"direct", "lane", "delimiter", "hierarchical", "lane_perm"}:
            raise IOError("unknown r25 Geometry representation kind")
        chunk_size = int(chunk_size); physical_size = int(physical_size); inner_codec = int(inner_codec); csize = int(csize)
        if chunk_size < 0 or chunk_size > RC.G.MAX_CHUNK:
            raise IOError("r25 Geometry logical chunk exceeds bound")
        if physical_size < 0 or physical_size > RC.G.MAX_DECODE_UNIT:
            raise IOError("r25 Geometry physical chunk exceeds decode bound")
        if inner_codec not in {CODEC_RAW, CODEC_ZSTD} or csize < 0 or cursor + csize > len(comp):
            raise IOError("r25 Geometry inner payload declaration invalid")
        if inner_codec == CODEC_RAW and csize != physical_size:
            raise IOError("non-canonical r25 Geometry raw inner payload")
        if inner_codec == CODEC_ZSTD and csize >= physical_size:
            raise IOError("non-canonical r25 Geometry Zstd inner payload")
        part = comp[cursor:cursor + csize]
        cursor += csize
        physical = part if inner_codec == CODEC_RAW else zd(part, physical_size)
        if len(physical) != physical_size:
            raise IOError("r25 Geometry inner physical size mismatch")
        if kind == "lane_perm":
            if not isinstance(param, list) or len(param) != 2 or not isinstance(param[1], (bytes, bytearray)):
                raise IOError("malformed r25 Geometry lane permutation")
            normalized = (int(param[0]), tuple(bytes(param[1])))
        elif kind in {"lane", "hierarchical"}:
            normalized = int(param)
        else:
            normalized = 0
        raw = RC.inverse_physical(kind, normalized, physical, chunk_size)
        if sha(raw) != _bytes32(logical_hash, "chunk logical"):
            raise IOError("r25 Geometry logical chunk integrity failure")
        logical_total += len(raw)
        if logical_total > logical_size:
            raise IOError("r25 Geometry chunks exceed outer logical size")
        out.append(raw)
    if cursor != len(comp) or logical_total != logical_size:
        raise IOError("r25 Geometry blob framing mismatch")
    return b"".join(out)


def _record_bytes(reader: CMPCT, blob_id: int) -> tuple[bytes, bytes, tuple]:
    off, us, cs, codec, ml = reader.blobs[blob_id]
    pos = reader.record_base + off
    header = bytes(reader.mm[pos:pos + BHDR.size])
    if len(header) != BHDR.size:
        raise IOError("short canonical r24 blob header")
    parsed = BHDR.unpack(header)
    m, c, flags, reserved, rus, rcs, rml, rcrc, rh = parsed
    if m != BMAGIC or c != codec or rus != us or rcs != cs or rml != ml:
        raise IOError("canonical r24 blob/index disagreement during r25 compile")
    end = pos + BHDR.size + rml + rcs
    if end > len(reader.mm):
        raise IOError("canonical r24 blob exceeds archive")
    meta = bytes(reader.mm[pos + BHDR.size:pos + BHDR.size + rml])
    comp = bytes(reader.mm[pos + BHDR.size + rml:end])
    return meta, comp, parsed


def compile_r24_to_r25(source: Path, out: Path) -> dict:
    """Compile one fresh canonical r24 archive into a revision-25 physical candidate."""
    with CMPCT(source) as reader:
        # Round-trip through MessagePack for a byte-oriented deep copy that preserves bytes keys/values exactly.
        index = msgpack.unpackb(msgpack.packb(reader.index, use_bin_type=True), raw=False, strict_map_key=False)
        if int(index.get("v", 0)) != 24:
            raise ValueError("r25 compiler currently requires a canonical revision-24 source index")
        records: list[bytes] = []
        new_blobs: list[list] = []
        transformed = 0
        saving = 0
        kind_counts: dict[str, int] = {}
        g5_incremental = 0
        cursor = 0
        for blob_id in range(len(reader.blobs)):
            old_meta, old_comp, parsed = _record_bytes(reader, blob_id)
            _, old_codec, flags, reserved, usize, csize, meta_len, crc, logical_hash = parsed
            raw = reader._blob(blob_id)
            if len(raw) != usize or sha(raw) != bytes(logical_hash):
                raise IOError("canonical r24 blob failed SHA-256 before r25 compilation")
            old_record = BHDR.pack(BMAGIC, old_codec, flags, reserved, usize, csize, meta_len, crc, logical_hash) + old_meta + old_comp
            chosen = old_record
            chosen_codec = int(old_codec)
            chosen_meta_len = int(meta_len)
            chosen_csize = int(csize)

            # Exact Deflate payload bytes can be observable to virtual-ZIP recipes through _stream(mode=0).
            # Every other canonical codec is semantically just a way to reconstruct `raw` and may compete.
            candidate = None if old_codec == CODEC_DEFLATE else encode_geometry_blob(raw)
            if candidate is not None:
                geo_comp, geo_meta, stats = candidate
                net = (len(old_meta) + len(old_comp)) - (len(geo_meta) + len(geo_comp))
                if net >= MIN_BLOB_NET_SAVING:
                    chosen_codec = CODEC_GEOMETRY
                    chosen_meta_len = len(geo_meta)
                    chosen_csize = len(geo_comp)
                    chosen = BHDR.pack(
                        BMAGIC, CODEC_GEOMETRY, 0, 0, usize, len(geo_comp), len(geo_meta),
                        binascii.crc32(raw) & 0xFFFFFFFF, logical_hash,
                    ) + geo_meta + geo_comp
                    transformed += 1
                    saving += net
                    g5_incremental += int(stats["incremental_g5_stored_saving"])
                    for kind, count in stats["kind_counts"].items():
                        kind_counts[kind] = kind_counts.get(kind, 0) + int(count)
            records.append(chosen)
            new_blobs.append([cursor, int(usize), chosen_csize, chosen_codec, chosen_meta_len])
            cursor += len(chosen)

        index["v"] = V25_VERSION
        index["blobs"] = new_blobs
        features = list(index.get("features", []))
        if "geometry-ir-physical-codec" not in features:
            features.append("geometry-ir-physical-codec")
        index["features"] = features
        ib = msgpack.packb(index, use_bin_type=True)
        ic = zc(ib, 12)
        ih = sha(ib)
        data = b"".join(records)
        header = HDR.pack(V25_MAGIC, V25_VERSION, 0, len(ic), len(ib), len(data), ih)
        footer = FTR.pack(V25_FMAGIC, 0, 1, 0, 0, len(ic), len(ib), 0, ih)
        out.write_bytes(header + ic + data + ic + footer)
    return {
        "archive_bytes": out.stat().st_size,
        "source_r24_bytes": source.stat().st_size,
        "saving_vs_r24_bytes": source.stat().st_size - out.stat().st_size,
        "geometry_blobs": transformed,
        "geometry_blob_net_saving": saving,
        "representation_kind_counts": kind_counts,
        "g5_incremental_stored_saving": g5_incremental,
        "logical_semantics_source": "canonical-r24-index-preserved",
    }


class CMPCTV25(CMPCT):
    """Python evidence reader for the r25 Geometry physical codec.

    Footnote: this subclasses the canonical reader so file/link/sparse/range/virtual-ZIP semantics remain one
    implementation.  Only full-index discovery and the new blob codec are specialized.  Native parity is still
    a promotion blocker; this class is not a substitute for ``cmpct-core``.
    """

    def _load_index(self):
        self.f.seek(0)
        header = self.f.read(HDR.size)
        if len(header) != HDR.size:
            raise IOError("short CMPCT r25 header")
        m, v, _fl, cs, us, _ds, ih = HDR.unpack(header)
        primary_error = None
        if m == V25_MAGIC and v == V25_VERSION:
            try:
                ic = self.f.read(cs)
                ib = zd(ic, us)
                if len(ib) != us or sha(ib) != ih:
                    raise IOError("r25 primary index integrity")
                index = msgpack.unpackb(ib, raw=False, strict_map_key=False)
                if int(index.get("v", 0)) != V25_VERSION:
                    raise IOError("r25 primary index version mismatch")
                self.latest_footer_pos = 0
                self.delta_depth = 0
                return index, HDR.size + cs
            except Exception as exc:
                primary_error = exc
        else:
            primary_error = IOError("not CMPCT r25")

        # Fresh r25 builds retain the canonical dual-index recovery contract.  Unlike the old research magics,
        # the tail copy is found from EOF and does not depend on reading a valid primary index payload.
        self.f.seek(0, os.SEEK_END)
        size = self.f.tell()
        if size < FTR.size:
            raise IOError(f"both CMPCT r25 indexes unavailable: primary={primary_error!r}")
        footer_pos = size - FTR.size
        self.f.seek(footer_pos)
        footer = self.f.read(FTR.size)
        fm, kind, codec, _flags, _res, tcs, tus, _prev, tih = FTR.unpack(footer)
        if fm != V25_FMAGIC or kind != 0 or codec not in {0, 1} or tcs > footer_pos:
            raise IOError(f"both CMPCT r25 indexes unavailable: primary={primary_error!r}")
        self.f.seek(footer_pos - tcs)
        encoded = self.f.read(tcs)
        ib = encoded if codec == 0 else zd(encoded, tus)
        if len(ib) != tus or sha(ib) != tih:
            raise IOError(f"both CMPCT r25 indexes unavailable: primary={primary_error!r}")
        index = msgpack.unpackb(ib, raw=False, strict_map_key=False)
        if int(index.get("v", 0)) != V25_VERSION:
            raise IOError("r25 tail index version mismatch")
        # The primary compressed-size field is still needed to locate immutable data.  A production native
        # r25 footer will carry record_base explicitly before recovery is promoted against arbitrary header
        # corruption; for this evidence reader, corruption tests preserve the fixed-size header declaration.
        self.f.seek(0)
        raw_header = self.f.read(HDR.size)
        if len(raw_header) != HDR.size:
            raise IOError("cannot recover r25 record base")
        _, _, _, primary_cs, _, _, _ = HDR.unpack(raw_header)
        if primary_cs > size:
            raise IOError("r25 primary index declaration prevents safe recovery")
        self.latest_footer_pos = footer_pos
        self.delta_depth = 0
        return index, HDR.size + primary_cs

    def _blob(self, idx: int) -> bytes:
        with self._cache_lock:
            cached = self.cache.get(idx)
        if cached is not None:
            return cached
        if not 0 <= idx < len(self.blobs):
            raise IOError("r25 blob id out of bounds")
        off, us, cs, codec, ml = self.blobs[idx]
        pos = self.record_base + off
        if pos < self.record_base or pos + BHDR.size + ml + cs > len(self.mm):
            raise IOError("r25 blob extent out of archive bounds")
        m, c, flags, res, rus, rcs, rml, rcrc, rh = BHDR.unpack_from(self.mm, pos)
        if m != BMAGIC or c != codec or rus != us or rcs != cs or rml != ml:
            raise IOError("r25 blob header/index mismatch")
        if c == CODEC_GEOMETRY:
            p = pos + BHDR.size
            meta = bytes(self.mm[p:p + rml])
            comp = bytes(self.mm[p + rml:p + rml + rcs])
            raw = decode_geometry_blob(comp, meta, rus)
            if len(raw) != rus or (binascii.crc32(raw) & 0xFFFFFFFF) != rcrc or sha(raw) != bytes(rh):
                raise IOError("r25 Geometry blob integrity failure")
            if len(raw) <= 2 * 1024 * 1024:
                with self._cache_lock:
                    self.cache[idx] = raw
            return raw

        raw = super()._blob(idx)
        # r25 strengthens the Python compatibility path to the same SHA-256 check already required by the
        # native strong verifier.  CRC32 remains a cheap first-line corruption check, not the trust boundary.
        if sha(raw) != bytes(rh):
            with self._cache_lock:
                self.cache.pop(idx, None)
            raise IOError("r25 legacy-codec blob SHA-256 failure")
        return raw


def build_candidate(root: Path, out: Path, *, workers: int | None = None, reproducible: bool = True) -> dict:
    """Build canonical r24 semantics, compile r25 physical views, and retain the smaller complete artifact."""
    with tempfile.TemporaryDirectory(prefix="cmpct-r25-geometry-") as td:
        temp = Path(td)
        r24 = temp / "base-r24.cmpct"
        r25 = temp / "candidate-r25.cmpct"
        base_stats = Builder(root, workers=workers, reproducible=reproducible).build(r24)
        compile_stats = compile_r24_to_r25(r24, r25)
        # Validate every logical non-directory member through the inherited canonical reader semantics before
        # exact-size tournament.  A transform that saves bytes but alters any logical representation is dead.
        with CMPCT(r24) as base, CMPCTV25(r25) as candidate:
            if base.index["files"] != candidate.index["files"] or base.index.get("recipes") != candidate.index.get("recipes") or base.index.get("fsmeta") != candidate.index.get("fsmeta"):
                raise RuntimeError("r25 compiler changed canonical logical metadata")
            for row in base.files:
                rel, kind = row[0], row[1]
                if kind == 1:  # directory
                    continue
                if base.read(rel) != candidate.read(rel):
                    raise RuntimeError(f"r25 logical byte mismatch: {rel}")
        if r25.stat().st_size < r24.stat().st_size:
            shutil.copyfile(r25, out)
            selected = "r25-geometry"
        else:
            shutil.copyfile(r24, out)
            selected = "r24-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "r24_bytes": r24.stat().st_size,
            "r25_bytes": r25.stat().st_size,
            "saving_vs_r24_bytes": r24.stat().st_size - out.stat().st_size,
            "r24": base_stats,
            "r25": compile_stats,
        }
