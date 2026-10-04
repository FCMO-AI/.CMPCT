from __future__ import annotations

"""Recoverable bounded profile prototype for the v0.30 logs inverse-edge winner.

This module deliberately pays the product taxes omitted by the first research oracle: fixed level-12 semantics,
separate authenticated payload packs, duplicated authenticated *control metadata only* for two-way primary/tail
recovery, bounded declarations, exact per-file SHA-256 identity and a reader that can strongly verify the whole
logical tree. The large payload is never duplicated for recovery.

It is still an experiment, not canonical r25 dispatch. Promotion remains blocked on canonical filesystem-manifest
integration plus native/Android parity, malformed/fuzz coverage and the full release authority. The purpose of
this profile is to determine whether the measured four-way logs win survives honest framing and recovery bytes.
"""

import binascii
import hashlib
import os
from pathlib import Path
import shutil
import struct
import tempfile
from typing import BinaryIO

import msgpack
import zstandard as zstd

from benchmarks import v030_logs_inverse_edge_oracle as BASE

MAGIC = b"C25LG12\0"
TAIL_MAGIC = b"C25L12T\0"
PROFILE = "cmpct-r25-logs-inverse-v1"
LEVEL = 12
META_LEVEL = 3
MAX_META_RAW = 2 * 1024 * 1024
MAX_META_COMP = 2 * 1024 * 1024
MAX_PACKS = 64
MAX_FILES = 4096
MAX_PATH_BYTES = 4096
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_MEMBER_AMPLIFICATION = 8.0
HEADER = struct.Struct("<8sQQI32s")  # magic, meta_csize, meta_usize, pack_count, SHA256(meta raw)
FOOTER = struct.Struct("<8sQQI32s")
PACK_HEADER = struct.Struct("<BQQI32s")  # codec, usize, csize, CRC32(raw), SHA256(raw)
CODEC_RAW = 0
CODEC_ZSTD = 1


def _meta_compress(raw: bytes) -> bytes:
    return zstd.ZstdCompressor(level=META_LEVEL, threads=0).compress(raw)


def _meta_decompress(comp: bytes, usize: int) -> bytes:
    if usize < 0 or usize > MAX_META_RAW or len(comp) > MAX_META_COMP:
        raise RuntimeError("logs profile metadata bounds")
    raw = zstd.ZstdDecompressor().decompress(comp, max_output_size=usize)
    if len(raw) != usize:
        raise RuntimeError("logs profile metadata size mismatch")
    return raw


def _pack_row(raw: bytes, *, compress: bool) -> tuple[int, int, bytes, int, bytes]:
    if len(raw) > MAX_DECODE_UNIT:
        raise RuntimeError("logs profile pack exceeds decode-unit policy")
    if compress:
        payload = zstd.ZstdCompressor(level=LEVEL, threads=0).compress(raw)
        codec = CODEC_ZSTD
    else:
        payload = raw
        codec = CODEC_RAW
    return codec, len(raw), payload, binascii.crc32(raw) & 0xFFFFFFFF, hashlib.sha256(raw).digest()


def build(source: Path, archive: Path) -> dict:
    rows, edges, edge_stats = BASE._scan_and_edges(source)
    if not rows or len(rows) > MAX_FILES:
        raise RuntimeError("logs profile file-count bounds")
    segments, max_amp, max_unit = BASE._plan_segments(rows, edges)
    if max_amp > MAX_MEMBER_AMPLIFICATION or max_unit > MAX_DECODE_UNIT:
        raise RuntimeError("logs profile locality admission")

    packs: list[tuple[int, int, bytes, int, bytes]] = []
    owners: dict[int, tuple[int, int, int]] = {}
    for members in segments:
        raw = b"".join(rows[index]["raw"] for index in members)
        pack_index = len(packs)
        cursor = 0
        for index in members:
            length = int(rows[index]["size"])
            owners[index] = (pack_index, cursor, length)
            cursor += length
        packs.append(_pack_row(raw, compress=True))

    direct = bytearray()
    direct_offsets: dict[int, tuple[int, int]] = {}
    for index, row in enumerate(rows):
        if index in edges or index in owners:
            continue
        offset = len(direct)
        direct.extend(row["raw"])
        direct_offsets[index] = (offset, int(row["size"]))
    direct_pack = len(packs)
    if direct:
        if len(direct) > MAX_DECODE_UNIT:
            raise RuntimeError("logs profile direct pack exceeds decode-unit policy")
        packs.append(_pack_row(bytes(direct), compress=False))
    if len(packs) > MAX_PACKS:
        raise RuntimeError("logs profile pack-count bounds")

    files = []
    previous = ""
    for index, row in enumerate(rows):
        rel = str(row["rel"])
        if len(rel.encode("utf-8")) > MAX_PATH_BYTES:
            raise RuntimeError("logs profile path bound")
        prefix = BASE._common_prefix(previous, rel)
        if index in edges:
            source_index, codec = edges[index]
            storage = ["derive", int(source_index), codec]
        elif index in owners:
            pack_index, offset, length = owners[index]
            storage = ["pack", pack_index, offset, length]
        else:
            offset, length = direct_offsets[index]
            storage = ["raw", direct_pack, offset, length]
        files.append([prefix, rel[prefix:], int(row["size"]), row["sha256"], storage])
        previous = rel

    meta = msgpack.packb([PROFILE, LEVEL, files], use_bin_type=True)
    if len(meta) > MAX_META_RAW:
        raise RuntimeError("logs profile metadata too large")
    meta_comp = _meta_compress(meta)
    if len(meta_comp) > MAX_META_COMP:
        raise RuntimeError("logs profile compressed metadata too large")
    meta_sha = hashlib.sha256(meta).digest()

    archive.parent.mkdir(parents=True, exist_ok=True)
    temp = archive.with_name(archive.name + ".tmp")
    with temp.open("wb") as handle:
        handle.write(HEADER.pack(MAGIC, len(meta_comp), len(meta), len(packs), meta_sha))
        handle.write(meta_comp)
        for codec, usize, payload, crc, sha in packs:
            handle.write(PACK_HEADER.pack(codec, usize, len(payload), crc, sha))
            handle.write(payload)
        handle.write(meta_comp)
        handle.write(FOOTER.pack(TAIL_MAGIC, len(meta_comp), len(meta), len(packs), meta_sha))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, archive)
    return {
        "profile": PROFILE,
        "level": LEVEL,
        "archive_bytes": archive.stat().st_size,
        "files": len(rows),
        "packs": len(packs),
        "meta_raw_bytes": len(meta),
        "meta_comp_bytes": len(meta_comp),
        "recovery_control_copies": 2,
        "payload_copies": 1,
        "edge_detection": edge_stats,
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_unit,
    }


class Archive:
    def __init__(self, path: Path):
        self.path = path
        self.handle: BinaryIO = path.open("rb")
        self.file_size = path.stat().st_size
        self.recovery_route = "primary"
        meta, meta_csize, pack_count = self._read_metadata()
        self.meta_csize = meta_csize
        self.files = self._parse_meta(meta)
        self.pack_offsets = self._scan_packs(pack_count)

    def close(self) -> None:
        self.handle.close()

    def __enter__(self) -> "Archive":
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    def _read_metadata_copy(self, comp: bytes, usize: int, expected_sha: bytes) -> bytes:
        raw = _meta_decompress(comp, int(usize))
        if hashlib.sha256(raw).digest() != expected_sha:
            raise RuntimeError("logs profile metadata authentication")
        return raw

    def _read_metadata(self) -> tuple[bytes, int, int]:
        primary_error: Exception | None = None
        try:
            self.handle.seek(0)
            header = self.handle.read(HEADER.size)
            if len(header) != HEADER.size:
                raise RuntimeError("short logs profile header")
            magic, csize, usize, pack_count, expected_sha = HEADER.unpack(header)
            if magic != MAGIC or csize > MAX_META_COMP or usize > MAX_META_RAW or pack_count > MAX_PACKS:
                raise RuntimeError("logs profile primary header bounds")
            comp = self.handle.read(csize)
            if len(comp) != csize:
                raise RuntimeError("short logs profile primary metadata")
            return self._read_metadata_copy(comp, usize, expected_sha), int(csize), int(pack_count)
        except Exception as exc:
            primary_error = exc

        try:
            if self.file_size < HEADER.size + FOOTER.size:
                raise RuntimeError("short logs profile archive")
            self.handle.seek(-FOOTER.size, os.SEEK_END)
            footer = self.handle.read(FOOTER.size)
            tail_magic, csize, usize, pack_count, expected_sha = FOOTER.unpack(footer)
            if tail_magic != TAIL_MAGIC or csize > MAX_META_COMP or usize > MAX_META_RAW or pack_count > MAX_PACKS:
                raise RuntimeError("logs profile tail header bounds")
            meta_offset = self.file_size - FOOTER.size - int(csize)
            if meta_offset < HEADER.size + int(csize):
                raise RuntimeError("logs profile tail metadata overlap")
            self.handle.seek(meta_offset)
            comp = self.handle.read(csize)
            if len(comp) != csize:
                raise RuntimeError("short logs profile tail metadata")
            self.recovery_route = "tail"
            return self._read_metadata_copy(comp, usize, expected_sha), int(csize), int(pack_count)
        except Exception as tail_error:
            raise RuntimeError(
                f"no authenticated logs profile metadata: primary={primary_error!r}; tail={tail_error!r}"
            ) from tail_error

    def _parse_meta(self, raw: bytes) -> list:
        head = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        if not isinstance(head, list) or len(head) != 3 or head[0] != PROFILE or int(head[1]) != LEVEL:
            raise RuntimeError("unsupported logs profile metadata")
        files = head[2]
        if not isinstance(files, list) or not files or len(files) > MAX_FILES:
            raise RuntimeError("logs profile file table bounds")
        previous = ""
        seen = set()
        for index, row in enumerate(files):
            if not isinstance(row, list) or len(row) != 5:
                raise RuntimeError("bad logs profile file row")
            prefix, suffix, size, sha, storage = row
            if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
                raise RuntimeError("bad logs profile path delta")
            rel = previous[:prefix] + suffix
            if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
                raise RuntimeError("unsafe logs profile path")
            if len(rel.encode("utf-8")) > MAX_PATH_BYTES or int(size) < 0 or not isinstance(sha, bytes) or len(sha) != 32:
                raise RuntimeError("logs profile file bounds")
            if not isinstance(storage, list) or not storage:
                raise RuntimeError("bad logs profile storage")
            row.append(rel)
            seen.add(rel)
            previous = rel
        return files

    def _scan_packs(self, pack_count: int) -> list[tuple[int, int, int, int, int, bytes]]:
        self.handle.seek(HEADER.size + self.meta_csize)
        offsets = []
        for _ in range(pack_count):
            header = self.handle.read(PACK_HEADER.size)
            if len(header) != PACK_HEADER.size:
                raise RuntimeError("short logs profile pack header")
            codec, usize, csize, crc, sha = PACK_HEADER.unpack(header)
            if codec not in (CODEC_RAW, CODEC_ZSTD) or usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT:
                raise RuntimeError("logs profile pack bounds")
            offset = self.handle.tell()
            if offset + csize > self.file_size:
                raise RuntimeError("logs profile pack extent")
            offsets.append((offset, int(codec), int(usize), int(csize), int(crc), sha))
            self.handle.seek(csize, os.SEEK_CUR)
        expected_tail_meta = self.file_size - FOOTER.size - self.meta_csize
        if self.handle.tell() != expected_tail_meta:
            raise RuntimeError("logs profile pack table/tail boundary mismatch")
        return offsets

    def _read_pack(self, index: int) -> bytes:
        if index < 0 or index >= len(self.pack_offsets):
            raise RuntimeError("logs profile pack index")
        offset, codec, usize, csize, crc, sha = self.pack_offsets[index]
        self.handle.seek(offset)
        payload = self.handle.read(csize)
        if len(payload) != csize:
            raise RuntimeError("short logs profile pack")
        if codec == CODEC_RAW:
            raw = payload
        else:
            raw = zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or hashlib.sha256(raw).digest() != sha:
            raise RuntimeError("logs profile pack identity")
        return raw

    def _paths(self) -> list[str]:
        return [row[5] for row in self.files]

    def read_member(self, index: int) -> tuple[bytes, int]:
        cache: dict[int, tuple[bytes, int]] = {}
        active: set[int] = set()

        def restore(item: int) -> tuple[bytes, int]:
            if item in cache:
                return cache[item]
            if item in active or item < 0 or item >= len(self.files):
                raise RuntimeError("logs profile dependency error")
            active.add(item)
            _prefix, _suffix, size, expected_sha, storage, _rel = self.files[item]
            size = int(size)
            kind = storage[0]
            if kind in ("pack", "raw"):
                pack_index, offset, length = map(int, storage[1:])
                pack = self._read_pack(pack_index)
                if offset < 0 or length != size or offset + length > len(pack):
                    raise RuntimeError("logs profile slice bounds")
                value = pack[offset : offset + length]
                decoded_context = len(pack) if kind == "pack" else length
            elif kind == "derive":
                source_index = int(storage[1])
                if source_index == item:
                    raise RuntimeError("logs profile self dependency")
                source, source_context = restore(source_index)
                value = BASE._decode(storage[2], source)
                decoded_context = source_context + len(value)
            else:
                raise RuntimeError("unknown logs profile storage")
            if len(value) != size or hashlib.sha256(value).digest() != expected_sha:
                raise RuntimeError("logs profile logical identity")
            active.remove(item)
            cache[item] = (value, decoded_context)
            return cache[item]

        return restore(index)

    def verify_all(self) -> dict:
        max_amp = 1.0
        max_context = 0
        identities = []
        for index, row in enumerate(self.files):
            value, context = self.read_member(index)
            size = int(row[2])
            amp = context / max(1, size)
            if amp > MAX_MEMBER_AMPLIFICATION or context > MAX_DECODE_UNIT:
                raise RuntimeError("logs profile locality violation")
            max_amp = max(max_amp, amp)
            max_context = max(max_context, context)
            identities.append((row[5], size, hashlib.sha256(value).hexdigest()))
        return {
            "ok": True,
            "files": len(self.files),
            "identities": identities,
            "recovery_route": self.recovery_route,
            "max_member_read_amplification": max_amp,
            "max_decode_unit_bytes": max_context,
        }

    def extract(self, dst: Path) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        for index, row in enumerate(self.files):
            target = dst / row[5]
            resolved = target.resolve()
            root = dst.resolve()
            if resolved != root and root not in resolved.parents:
                raise RuntimeError("logs profile extraction traversal")
            target.parent.mkdir(parents=True, exist_ok=True)
            value, _context = self.read_member(index)
            target.write_bytes(value)


def strong_verify(path: Path) -> dict:
    with Archive(path) as archive:
        return archive.verify_all()


def extract(path: Path, dst: Path) -> None:
    with Archive(path) as archive:
        archive.extract(dst)


def recovery_probe(path: Path) -> dict:
    original = path.read_bytes()
    results = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-recovery-") as td:
        root = Path(td)
        primary = root / "primary-damaged.cmpct"
        raw = bytearray(original)
        if len(raw) <= HEADER.size + 8:
            raise RuntimeError("logs profile archive too short for recovery probe")
        raw[HEADER.size + 3] ^= 0x5A
        primary.write_bytes(raw)
        results["primary_damage"] = strong_verify(primary)

        tail = root / "tail-damaged.cmpct"
        raw = bytearray(original)
        footer = FOOTER.unpack(raw[-FOOTER.size:])
        tail_csize = int(footer[1])
        tail_meta_offset = len(raw) - FOOTER.size - tail_csize
        raw[tail_meta_offset + 3] ^= 0xA5
        tail.write_bytes(raw)
        results["tail_damage"] = strong_verify(tail)

        both = root / "both-damaged.cmpct"
        raw = bytearray(original)
        raw[HEADER.size + 3] ^= 0x5A
        raw[tail_meta_offset + 3] ^= 0xA5
        both.write_bytes(raw)
        try:
            strong_verify(both)
            both_failed_closed = False
        except Exception:
            both_failed_closed = True
        results["both_failed_closed"] = both_failed_closed
    return results
