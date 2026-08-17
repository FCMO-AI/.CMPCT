"""CMPCT v0.30 production-candidate recovery contract for canonical r25 Geometry.

The first r25 evidence writer reused revision-24's footer shape.  Its duplicate tail index was authenticated, but
recovery still needed the *primary* header's compressed-index length to rediscover the physical record base.  A
corrupted primary declaration could therefore make a healthy tail index insufficient for safe recovery.

This successor keeps the same logical r25 index and Geometry blob grammar while replacing only the fresh-build
footer with a self-locating form:

``magic, kind, codec, flags, reserved, index_csize, index_usize, prev_footer, record_base, index_sha256``.

The reader validates the authenticated tail index, the explicit record base, and the complete canonical blob
extent table before returning an index.  If the tail is damaged, an independently valid primary header/index
can still recover the archive.  If both are valid they must describe the same record base and identical index.

Footnote: the footer's ``record_base`` is not trusted merely because it sits next to an index hash.  It is
accepted only when every authenticated blob descriptor forms one contiguous region beginning there and ending
exactly where the authenticated tail-index copy begins.  This turns a corrupted offset into a failed recovery
rather than a seek into attacker-chosen bytes.

This is still an evidence reader/writer until the same footer/codec is implemented in ``src/cmpct`` and the
memory-safe native reader.  Transaction generations remain a separate release gate.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import struct
import tempfile

import msgpack

from cmpct.codec import BHDR, HDR, sha, zd
from experiments import canonical_v25_geometry as V25

V25_FTR = struct.Struct("<8sBBBBQQQQ32s")
MAX_INDEX_COMPRESSED = 256 * 1024 * 1024
MAX_INDEX_RAW = 256 * 1024 * 1024

_original_compile = V25.compile_r24_to_r25
_original_build_candidate = V25.build_candidate


def _canonical_blob_span(index: dict, record_base: int, data_end: int) -> int:
    if type(record_base) is not int or type(data_end) is not int or record_base < HDR.size or data_end < record_base:
        raise IOError("invalid r25 physical data bounds")
    blobs = index.get("blobs")
    if not isinstance(blobs, list):
        raise IOError("r25 index missing blob table")
    cursor = 0
    for blob_id, desc in enumerate(blobs):
        if not isinstance(desc, list) or len(desc) != 5:
            raise IOError("malformed r25 blob descriptor")
        off, usize, csize, codec, meta_len = desc
        if any(type(value) is not int for value in (off, usize, csize, codec, meta_len)):
            raise IOError("non-canonical r25 blob descriptor integer")
        if off != cursor or usize < 0 or csize < 0 or meta_len < 0:
            raise IOError("r25 blob table is not canonical contiguous storage")
        extent = BHDR.size + meta_len + csize
        if extent < BHDR.size or record_base + cursor + extent > data_end:
            raise IOError(f"r25 blob {blob_id} exceeds declared physical region")
        cursor += extent
    if record_base + cursor != data_end:
        raise IOError("r25 blob table does not exactly cover physical data region")
    return cursor


def _decode_index(encoded: bytes, codec: int, usize: int, digest: bytes) -> dict:
    if type(usize) is not int or usize < 0 or usize > MAX_INDEX_RAW:
        raise IOError("r25 index raw size exceeds bound")
    if codec == 0:
        raw = encoded
    elif codec == 1:
        raw = zd(encoded, usize)
    else:
        raise IOError("unsupported r25 index codec")
    if len(raw) != usize or sha(raw) != bytes(digest):
        raise IOError("r25 index authentication failure")
    try:
        index = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    except Exception as exc:
        raise IOError("malformed r25 index") from exc
    if not isinstance(index, dict) or int(index.get("v", 0)) != V25.V25_VERSION:
        raise IOError("r25 index version mismatch")
    return index


def _try_primary(stream, file_size: int):
    stream.seek(0)
    header = stream.read(HDR.size)
    if len(header) != HDR.size:
        raise IOError("short r25 primary header")
    magic, version, _flags, csize, usize, data_span, digest = HDR.unpack(header)
    if magic != V25.V25_MAGIC or version != V25.V25_VERSION:
        raise IOError("not canonical r25 primary header")
    if csize > MAX_INDEX_COMPRESSED or usize > MAX_INDEX_RAW:
        raise IOError("r25 primary index declaration exceeds bound")
    record_base = HDR.size + int(csize)
    data_end = record_base + int(data_span)
    if record_base < HDR.size or data_end > file_size:
        raise IOError("r25 primary physical span exceeds archive")
    stream.seek(HDR.size)
    encoded = stream.read(csize)
    if len(encoded) != csize:
        raise IOError("short r25 primary index")
    index = _decode_index(encoded, 1, int(usize), digest)
    _canonical_blob_span(index, record_base, data_end)
    return index, record_base


def _try_tail(stream, file_size: int):
    if file_size < V25_FTR.size:
        raise IOError("short r25 recovery footer")
    footer_pos = file_size - V25_FTR.size
    stream.seek(footer_pos)
    raw_footer = stream.read(V25_FTR.size)
    if len(raw_footer) != V25_FTR.size:
        raise IOError("short r25 recovery footer")
    magic, kind, codec, flags, reserved, csize, usize, prev, record_base, digest = V25_FTR.unpack(raw_footer)
    if magic != V25.V25_FMAGIC or kind != 0 or flags != 0 or reserved != 0 or prev != 0:
        raise IOError("unsupported r25 recovery footer declaration")
    if csize > MAX_INDEX_COMPRESSED or usize > MAX_INDEX_RAW or csize > footer_pos:
        raise IOError("r25 tail index declaration exceeds bound")
    tail_index_start = footer_pos - int(csize)
    if record_base < HDR.size or record_base > tail_index_start:
        raise IOError("r25 recovery record base outside physical region")
    stream.seek(tail_index_start)
    encoded = stream.read(csize)
    if len(encoded) != csize:
        raise IOError("short r25 tail index")
    index = _decode_index(encoded, int(codec), int(usize), digest)
    _canonical_blob_span(index, int(record_base), tail_index_start)
    return index, int(record_base)


def compile_r24_to_r25(source: Path, out: Path) -> dict:
    """Build the historical r25 physical candidate, then replace its footer with the self-locating contract."""
    with tempfile.TemporaryDirectory(prefix="cmpct-r25-selflocating-") as td:
        old_path = Path(td) / "historical-r25.cmpct"
        stats = _original_compile(source, old_path)
        data = old_path.read_bytes()
        if len(data) < V25.FTR.size + HDR.size:
            raise RuntimeError("historical r25 candidate is unexpectedly short")
        magic, kind, codec, flags, reserved, csize, usize, prev, digest = V25.FTR.unpack_from(
            data, len(data) - V25.FTR.size
        )
        if magic != V25.V25_FMAGIC or kind != 0 or prev != 0:
            raise RuntimeError("historical r25 footer is not a fresh full-index footer")
        hmagic, hver, _hflags, primary_csize, _husize, _data_span, _hdigest = HDR.unpack_from(data, 0)
        if hmagic != V25.V25_MAGIC or hver != V25.V25_VERSION:
            raise RuntimeError("historical r25 header identity drift")
        record_base = HDR.size + int(primary_csize)
        new_footer = V25_FTR.pack(
            V25.V25_FMAGIC, kind, codec, flags, reserved,
            int(csize), int(usize), 0, record_base, digest,
        )
        out.write_bytes(data[:-V25.FTR.size] + new_footer)
    result = dict(stats)
    result.update({
        "archive_bytes": out.stat().st_size,
        "saving_vs_r24_bytes": source.stat().st_size - out.stat().st_size,
        "self_locating_tail": True,
        "record_base_in_footer": record_base,
        "recovery_footer_bytes": V25_FTR.size,
    })
    return result


class CMPCTV25(V25.CMPCTV25):
    """r25 evidence reader with independent primary/tail recovery and canonical physical-span validation."""

    def _load_index(self):
        self.f.seek(0, os.SEEK_END)
        file_size = self.f.tell()
        primary = tail = None
        primary_error = tail_error = None
        try:
            primary = _try_primary(self.f, file_size)
        except Exception as exc:
            primary_error = exc
        try:
            tail = _try_tail(self.f, file_size)
        except Exception as exc:
            tail_error = exc

        if primary is not None and tail is not None:
            primary_index, primary_base = primary
            tail_index, tail_base = tail
            if primary_base != tail_base or primary_index != tail_index:
                raise IOError("r25 primary/tail indexes disagree")
            self.latest_footer_pos = file_size - V25_FTR.size
            self.delta_depth = 0
            return tail_index, tail_base
        if tail is not None:
            self.latest_footer_pos = file_size - V25_FTR.size
            self.delta_depth = 0
            return tail[0], tail[1]
        if primary is not None:
            self.latest_footer_pos = 0
            self.delta_depth = 0
            return primary[0], primary[1]
        raise IOError(
            f"both CMPCT r25 indexes unavailable: primary={primary_error!r}; tail={tail_error!r}"
        )


def build_candidate(root: Path, out: Path, *, workers: int | None = None, reproducible: bool = True) -> dict:
    """Canonical r24-vs-self-locating-r25 complete artifact tournament."""
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT

    with tempfile.TemporaryDirectory(prefix="cmpct-r25-recovery-portfolio-") as td:
        temp = Path(td)
        r24 = temp / "base-r24.cmpct"
        r25 = temp / "candidate-r25.cmpct"
        base_stats = Builder(root, workers=workers, reproducible=reproducible).build(r24)
        compile_stats = compile_r24_to_r25(r24, r25)
        with CMPCT(r24) as base, CMPCTV25(r25) as candidate:
            if (
                base.index["files"] != candidate.index["files"]
                or base.index.get("recipes") != candidate.index.get("recipes")
                or base.index.get("dict_blob") != candidate.index.get("dict_blob")
                or base.index.get("fsmeta") != candidate.index.get("fsmeta")
            ):
                raise RuntimeError("r25 compiler changed canonical logical metadata")
            for row in base.files:
                if row[1] == 1:  # K_DIR; keep the historical test surface independent of a private import.
                    continue
                if base.read(row[0]) != candidate.read(row[0]):
                    raise RuntimeError(f"r25 logical byte mismatch: {row[0]}")
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
