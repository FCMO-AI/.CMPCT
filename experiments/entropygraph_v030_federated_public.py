from __future__ import annotations

"""Bounded public-reader surface for the C25EG01 federated r25 candidate.

This module does not promote C25EG01 into the shipping selector.  It turns the already-green productization
candidate into a reader-shaped profile: authenticated public member listing, selective member reconstruction,
filesystem-manifest semantics, and operation-derived locality accounting.  The implementation deliberately
mirrors the frozen CMPNX5 recipe grammar while reading the dedicated C25EG01 identity emitted by
``entropygraph_v030_federated_candidate``.

Every physical pack touched by a selected member is CRC32- and SHA-256-authenticated before use.  Public file
identity is then checked against the authenticated canonical filesystem manifest.  Directories are not readable;
symlinks expose their canonical target bytes; hardlinks resolve to their deterministic regular owner.  The
filesystem manifest is control-plane state and is not charged to member decoded-context accounting, matching the
existing r25 locality contract.

Native/Android dispatch remains closed.  This reader is a Python semantic-owner/preparity step only and cannot
satisfy release authority by itself.
"""

import binascii
import bz2
import gzip
import hashlib
import lzma
from pathlib import Path
import zlib
import zipfile

from experiments import entropygraph_v030_federated_candidate as CAND

FS = CAND.FS
V25 = CAND.V25
MAX_MEMBER_AMPLIFICATION = CAND.MAX_MEMBER_AMPLIFICATION
MAX_DECODE_UNIT = CAND.MAX_DECODE_UNIT


class FederatedPublicError(RuntimeError):
    pass


def _graph_read(archive: Path, requested_path: str) -> tuple[bytes, dict]:
    """Reconstruct one graph-owned logical member and return exact physical-pack locality."""
    archive = Path(archive).resolve()
    with CAND._engine(archive):
        handle, meta, offsets = V25.open_ar()
        try:
            pack_sizes = [int(row[2]) for row in offsets]
            if pack_sizes and max(pack_sizes) > MAX_DECODE_UNIT:
                raise FederatedPublicError("federated physical pack exceeds 8 MiB decode ceiling")
            files = {str(path): desc for path, desc in meta.get("files", [])}
            for pi, entries in meta.get("micro", []):
                off = 0
                for path, size in entries:
                    files[str(path)] = ["plain", [["slice", int(pi), off, int(size)]], int(size)]
                    off += int(size)
            if requested_path not in files:
                raise KeyError(requested_path)

            stream_packs = [
                (int(start), int(pi), int(size)) for start, pi, size in meta.get("stream_packs", [])
            ]
            pack_cache: dict[int, bytes] = {}
            file_cache: dict[str, tuple[bytes, set[int]]] = {}
            active: set[str] = set()

            def pack(index: int) -> bytes:
                if index in pack_cache:
                    return pack_cache[index]
                if index < 0 or index >= len(offsets):
                    raise FederatedPublicError("federated pack index out of range")
                off, codec, usize, csize, crc, expected_sha = offsets[index]
                usize = int(usize)
                csize = int(csize)
                if usize < 0 or usize > MAX_DECODE_UNIT or csize < 0 or csize > MAX_DECODE_UNIT:
                    raise FederatedPublicError("federated pack bounds")
                handle.seek(int(off))
                payload = handle.read(csize)
                if len(payload) != csize:
                    raise FederatedPublicError("truncated federated pack")
                if int(codec) == 1:
                    raw = V25.zd(payload, usize)
                elif int(codec) == 0:
                    raw = payload
                else:
                    raise FederatedPublicError("unsupported federated pack codec")
                if (
                    len(raw) != usize
                    or (binascii.crc32(raw) & 0xFFFFFFFF) != int(crc)
                    or hashlib.sha256(raw).digest() != bytes(expected_sha)
                ):
                    raise FederatedPublicError("federated pack identity failure")
                pack_cache[index] = raw
                return raw

            def object_bytes(refs: list) -> tuple[bytes, set[int]]:
                chunks: list[bytes] = []
                touched: set[int] = set()
                for ref in refs:
                    if not isinstance(ref, list) or not ref:
                        raise FederatedPublicError("malformed federated object reference")
                    kind = ref[0]
                    if kind == "slice":
                        _kind, pi, off, length = ref
                        pi, off, length = int(pi), int(off), int(length)
                        raw = pack(pi)
                        if off < 0 or length < 0 or off + length > len(raw):
                            raise FederatedPublicError("federated object slice bounds")
                        chunks.append(raw[off : off + length])
                    elif kind == "whole":
                        _kind, pi, length = ref
                        pi, length = int(pi), int(length)
                        raw = pack(pi)
                        if length < 0 or length > len(raw):
                            raise FederatedPublicError("federated whole-object bounds")
                        chunks.append(raw[:length])
                    else:
                        raise FederatedPublicError("unsupported federated object reference")
                    touched.add(pi)
                return b"".join(chunks), touched

            def stream_slice(offset: int, length: int) -> tuple[bytes, set[int]]:
                end = offset + length
                chunks: list[bytes] = []
                touched: set[int] = set()
                for slab_start, pi, slab_size in stream_packs:
                    slab_end = slab_start + slab_size
                    if slab_end <= offset:
                        continue
                    if slab_start >= end:
                        break
                    raw = pack(pi)
                    start = max(offset, slab_start) - slab_start
                    stop = min(end, slab_end) - slab_start
                    chunks.append(raw[start:stop])
                    touched.add(pi)
                value = b"".join(chunks)
                if len(value) != length:
                    raise FederatedPublicError("federated stream slice did not cover requested range")
                return value, touched

            def restore(path: str) -> tuple[bytes, set[int]]:
                if path in file_cache:
                    value, touched = file_cache[path]
                    return value, set(touched)
                if path in active or path not in files:
                    raise FederatedPublicError("federated reconstruction dependency error")
                active.add(path)
                desc = files[path]
                typ = desc[0]
                touched: set[int] = set()
                if typ == "plain":
                    value, touched = object_bytes(desc[1])
                    expected_len = int(desc[2])
                elif typ == "zipstreams":
                    skeleton, skeleton_packs = object_bytes(desc[1])
                    literal_lengths = [int(value) for value in desc[2]]
                    streams = [(int(row[0]), int(row[1])) for row in desc[3]]
                    chunks: list[bytes] = []
                    cursor = 0
                    touched |= skeleton_packs
                    for index, (stream_offset, stream_len) in enumerate(streams):
                        literal_len = literal_lengths[index]
                        chunks.append(skeleton[cursor : cursor + literal_len])
                        cursor += literal_len
                        stream, packs = stream_slice(stream_offset, stream_len)
                        chunks.append(stream)
                        touched |= packs
                    chunks.append(skeleton[cursor : cursor + literal_lengths[-1]])
                    value = b"".join(chunks)
                    expected_len = int(desc[4])
                elif typ == "inflate_stream":
                    stream, packs = stream_slice(int(desc[1]), int(desc[2]))
                    method = int(desc[3])
                    value = zlib.decompress(stream, -15) if method == zipfile.ZIP_DEFLATED else stream
                    touched |= packs
                    expected_len = int(desc[4])
                elif typ == "decode_file":
                    source, packs = restore(str(desc[1]))
                    codec = str(desc[2])
                    expected_len = int(desc[3])
                    if codec == "gzip":
                        value = gzip.decompress(source)
                    elif codec == "xz":
                        value = lzma.decompress(source)
                    elif codec == "bzip2":
                        value = bz2.decompress(source)
                    elif codec == "zstd":
                        value = V25.zd(source, expected_len)
                    else:
                        raise FederatedPublicError(f"unsupported federated inverse codec {codec!r}")
                    touched |= packs
                elif typ == "splice":
                    residual, packs = object_bytes(desc[1])
                    literal_lengths = [int(value) for value in desc[2]]
                    children = [str(value) for value in desc[3]]
                    chunks = []
                    cursor = 0
                    touched |= packs
                    for index, child in enumerate(children):
                        literal_len = literal_lengths[index]
                        chunks.append(residual[cursor : cursor + literal_len])
                        cursor += literal_len
                        child_bytes, child_packs = restore(child)
                        chunks.append(child_bytes)
                        touched |= child_packs
                    chunks.append(residual[cursor : cursor + literal_lengths[-1]])
                    value = b"".join(chunks)
                    expected_len = int(desc[4])
                else:
                    raise FederatedPublicError(f"unsupported federated recipe {typ!r}")
                if len(value) != expected_len:
                    raise FederatedPublicError(f"federated logical length mismatch for {path!r}")
                active.remove(path)
                file_cache[path] = (value, set(touched))
                return value, touched

            value, touched = restore(requested_path)
            decoded_context = sum(pack_sizes[index] for index in touched)
            amplification = decoded_context / max(1, len(value))
            if amplification > MAX_MEMBER_AMPLIFICATION:
                raise FederatedPublicError("federated selected member exceeds 8x locality ceiling")
            return value, {
                "logical_bytes": len(value),
                "decoded_context_bytes": decoded_context,
                "amplification": amplification,
                "pack_count": len(touched),
                "profile": "federated-eg01",
            }
        finally:
            handle.close()


def _manifest(archive: Path) -> dict:
    raw, _stats = _graph_read(Path(archive), FS.FILESYSTEM_MANIFEST)
    return FS.decode_manifest(
        raw,
        max_path_bytes=CAND.MAX_PATH_BYTES,
        max_entries=CAND.MAX_MANIFEST_ENTRIES,
    )


def list_members(archive: Path) -> list[dict]:
    decoded = _manifest(Path(archive))
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    result = []
    for row in sorted(decoded["manifest"]["entries"], key=lambda item: item[0]):
        rel, kind, mode, mtime_ns, _uid, _gid, _xattrs, extra = row
        if kind == "f":
            size = int(extra[0])
        elif kind == "h":
            size = int(decoded["regular"][extra][0])
        elif kind == "l":
            size = len(extra.encode("utf-8"))
        else:
            size = 0
        result.append(
            {
                "path": rel,
                "kind": names[kind],
                "size": size,
                "mode": int(mode),
                "mtime_ns": int(mtime_ns),
            }
        )
    return result


def read_member_with_stats(archive: Path, rel: str) -> tuple[bytes, dict]:
    decoded = _manifest(Path(archive))
    rows = FS.entry_map(decoded)
    if rel not in rows:
        raise KeyError(rel)
    row = rows[rel]
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        raw = row[7].encode("utf-8")
        return raw, {
            "logical_bytes": len(raw),
            "decoded_context_bytes": len(raw),
            "amplification": 1.0,
            "pack_count": 0,
            "profile": "federated-eg01-symlink",
        }
    owner = rel if kind == "f" else str(row[7])
    value, stats = _graph_read(Path(archive), owner)
    expected_size, expected_sha = decoded["regular"][owner]
    if len(value) != int(expected_size) or hashlib.sha256(value).digest() != bytes(expected_sha):
        raise FederatedPublicError("federated public member identity mismatch")
    return value, stats


def read_member(archive: Path, rel: str) -> bytes:
    return read_member_with_stats(archive, rel)[0]


def strong_verify(archive: Path) -> dict:
    return CAND.strong_verify(Path(archive))


def extract(archive: Path, destination: Path) -> None:
    CAND.extract(Path(archive), Path(destination))
