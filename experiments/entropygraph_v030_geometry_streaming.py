"""Streaming reader facade for the hardened CMPCT v0.30 Geometry research seed.

CMPNX13 is depth-0: every logical node is reconstructed from exactly one authenticated physical record.
The original research reader nevertheless materialized every file into a ``dict[str, bytes]`` before
verification/extraction.  This facade uses the guarded metadata/physical-table admission layer but streams
one <=512 KiB logical node at a time into the file hash, archive tree hash and optional destination file.

Writer bytes are unchanged.  Archive selection is unchanged.  The only purpose is to make the reader's
working set reflect the grammar's bounded locality instead of the total logical size of the archive.

Footnote: the guarded metadata layer currently retains a conservative 96 MiB *declared logical archive*
ceiling because other research callers can still invoke the legacy whole-materializer directly.  This
streaming path removes the implementation reason for that ceiling; lifting it safely is a later API cleanup,
not a storage-format change.
"""
from __future__ import annotations

import binascii
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

from experiments import entropygraph_v030_geometry_guarded as guarded

geometry = guarded.geometry


class _StreamingSession:
    def __init__(self, archive: Path):
        self.stream, self.meta, self.record_start, self.offsets = geometry._open(archive)
        self.nodes = self.meta["nodes"]
        self.leaves = self.meta["record_leaf_sha256"]
        self.max_logical_node_bytes = 0
        self.max_physical_record_bytes = 0
        self.physical_record_reads = 0

    def close(self) -> None:
        self.stream.close()

    def _record(self, record_id: int) -> bytes:
        if not 0 <= record_id < len(self.offsets):
            raise RuntimeError("Geometry record id out of range")
        self.stream.seek(self.record_start + self.offsets[record_id])
        header = self.stream.read(geometry.PH.size)
        if len(header) != geometry.PH.size:
            raise RuntimeError("short Geometry physical header")
        codec, usize, csize, crc, logical_sha = geometry.PH.unpack(header)
        if usize > geometry.MAX_DECODE_UNIT or csize > geometry.MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("Geometry physical record exceeds resource bound")
        payload = self.stream.read(csize)
        if len(payload) != csize or geometry.H(payload) != self.leaves[record_id]:
            raise RuntimeError("Geometry payload authentication")
        if codec == geometry.CODEC_RAW:
            raw = payload
        elif codec == geometry.CODEC_ZSTD:
            raw = geometry.zd(payload, usize)
        else:
            raise RuntimeError("unknown Geometry physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or geometry.H(raw) != logical_sha:
            raise RuntimeError("Geometry physical integrity")
        self.max_physical_record_bytes = max(self.max_physical_record_bytes, len(raw))
        self.physical_record_reads += 1
        return raw

    def node(self, node_id: int) -> bytes:
        if not 0 <= node_id < len(self.nodes):
            raise RuntimeError("Geometry node id out of range")
        desc = self.nodes[node_id]
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed Geometry node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = self._record(int(record_id))
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            raw = geometry.L.lane_inverse(self._record(int(record_id)), int(width), int(logical_size))
        elif kind == "delimiter" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = geometry.delimiter_inverse(self._record(int(record_id)), int(logical_size))
        else:
            raise RuntimeError("unknown or malformed Geometry node kind")
        if len(raw) != int(logical_size) or len(raw) > geometry.MAX_CHUNK or geometry.H(raw) != expected:
            raise RuntimeError("Geometry logical node integrity")
        self.max_logical_node_bytes = max(self.max_logical_node_bytes, len(raw))
        return raw


def _is_geometry(archive: Path) -> bool:
    with archive.open("rb") as stream:
        return stream.read(8) == geometry.MAG


def _consume_file(
    session: _StreamingSession,
    rel: str,
    desc: list,
    tree: "hashlib._Hash",
    target: Path | None,
) -> int:
    if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
        raise RuntimeError("malformed Geometry file")
    safe = geometry._safe_relpath(rel)
    node_ids, logical_size, expected = desc
    if not isinstance(node_ids, list) or not isinstance(logical_size, int) or isinstance(logical_size, bool):
        raise RuntimeError("malformed Geometry file declaration")

    rel_bytes = rel.encode("utf-8")
    tree.update(len(rel_bytes).to_bytes(4, "little")); tree.update(rel_bytes)
    tree.update(int(logical_size).to_bytes(8, "little"))
    file_hash = hashlib.sha256()
    written = 0
    output = None
    try:
        if target is not None:
            target = target.joinpath(*safe.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            output = target.open("wb")
        for node_id in node_ids:
            raw = session.node(int(node_id))
            written += len(raw)
            if written > logical_size:
                raise RuntimeError("Geometry streamed file exceeds declared logical size")
            file_hash.update(raw); tree.update(raw)
            if output is not None:
                output.write(raw)
    finally:
        if output is not None:
            output.close()
    if written != logical_size or file_hash.digest() != expected:
        raise RuntimeError("Geometry streamed logical file integrity")
    return written


def _stream_archive(archive: Path, target: Path | None) -> dict:
    session = _StreamingSession(archive)
    tree = hashlib.sha256(); logical_bytes = 0; files = 0
    try:
        for rel in sorted(session.meta["files"]):
            logical_bytes += _consume_file(session, rel, session.meta["files"][rel], tree, target)
            files += 1
        got = tree.hexdigest()
        if got != session.meta.get("tree_sha256"):
            raise RuntimeError("Geometry streamed tree identity mismatch")
        return {
            "ok": True,
            "files": files,
            "logical_bytes": logical_bytes,
            "tree_sha256": got,
            "engine": session.meta.get("engine"),
            "reader": "Geometry-streaming-v1",
            "max_logical_node_bytes": session.max_logical_node_bytes,
            "max_physical_record_bytes": session.max_physical_record_bytes,
            "physical_record_reads": session.physical_record_reads,
        }
    finally:
        session.close()


def strong_verify(archive: Path) -> dict:
    if not _is_geometry(archive):
        return geometry.BASE.strong_verify(archive)
    return _stream_archive(archive, None)


def extract(archive: Path, dst: Path) -> None:
    if not _is_geometry(archive):
        geometry.BASE.extract(archive, dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.geometry-stage-", dir=dst.parent))
    try:
        _stream_archive(archive, staging)
        # Footnote: destructive destination replacement happens only after every node, file hash and the
        # archive-wide tree hash have passed.  A corrupt archive therefore cannot leave a half-written
        # destination merely because verification failed near the end of extraction.
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        os.replace(staging, dst)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def build(root: Path, out: Path) -> dict:
    return geometry.build(root, out)


def treehash(root: Path) -> str:
    return geometry.treehash(root)


if __name__ == "__main__":
    # Keep command-line behavior delegated to the research grammar.  Promotion can expose a stable CLI only
    # after this streaming facade and native/shared-reader parity have their own conformance contract.
    geometry._main()
