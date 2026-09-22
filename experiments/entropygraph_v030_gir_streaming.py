"""Node-streamed reader facade for the hardened CMPNX14 Geometry IR research archive.

CMPNX14 is depth-0: every logical node reconstructs from one authenticated physical record and is bounded by
``MAX_CHUNK``.  The original research reader nevertheless caches every physical record, every reconstructed
node and every output file before verification/extraction.  This facade keeps the guarded metadata/physical
admission layer but consumes one logical node at a time into file/tree hashes and an optional staged output.

Writer bytes, transform nomination and complete-artifact selection are unchanged.

Footnote: ``entropygraph_v030_gir_guarded`` still retains a conservative whole-archive logical-size ceiling
because legacy callers can invoke the old materializer directly.  This streaming path removes the *memory*
reason for that ceiling.  Lifting the metadata policy itself should happen only when all public read paths are
streaming and have an explicit archive-size contract.
"""
from __future__ import annotations

import binascii
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from experiments import entropygraph_v030_gir_guarded as guarded


gir = guarded.gir


class _StreamingSession:
    def __init__(self, archive: Path):
        self.stream, self.meta, self.record_start, self.offsets = gir._open(archive)
        self.nodes = self.meta["nodes"]
        self.leaves = self.meta["record_leaf_sha256"]
        self.max_logical_node_bytes = 0
        self.max_physical_record_bytes = 0
        self.physical_record_reads = 0

    def close(self) -> None:
        self.stream.close()

    def _record(self, record_id: int) -> bytes:
        if not 0 <= record_id < len(self.offsets):
            raise RuntimeError("GIR record id out of range")
        self.stream.seek(self.record_start + self.offsets[record_id])
        header = self.stream.read(gir.PH.size)
        if len(header) != gir.PH.size:
            raise RuntimeError("short GIR physical header")
        codec, usize, csize, crc, logical_sha = gir.PH.unpack(header)
        if usize > gir.MAX_DECODE_UNIT or csize > gir.MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("GIR physical record exceeds resource bound")
        payload = self.stream.read(csize)
        if len(payload) != csize or gir.H(payload) != self.leaves[record_id]:
            raise RuntimeError("GIR payload authentication")
        if codec == gir.CODEC_RAW:
            raw = payload
        elif codec == gir.CODEC_ZSTD:
            raw = gir.zd(payload, usize)
        else:
            raise RuntimeError("unknown GIR physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or gir.H(raw) != logical_sha:
            raise RuntimeError("GIR physical integrity")
        self.max_physical_record_bytes = max(self.max_physical_record_bytes, len(raw))
        self.physical_record_reads += 1
        return raw

    def node(self, node_id: int) -> bytes:
        if not 0 <= node_id < len(self.nodes):
            raise RuntimeError("GIR node id out of range")
        desc = self.nodes[node_id]
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed GIR node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = self._record(record_id)
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            raw = gir.L.lane_inverse(self._record(record_id), width, logical_size)
        elif kind == "delimiter" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = gir.G.delimiter_inverse(self._record(record_id), logical_size)
        elif kind == "hierarchical" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = gir.HG.hierarchy_inverse(self._record(record_id), logical_size)
        else:
            raise RuntimeError("unknown or malformed GIR node kind")
        if len(raw) != logical_size or len(raw) > gir.MAX_CHUNK or gir.H(raw) != expected:
            raise RuntimeError("GIR logical node integrity")
        self.max_logical_node_bytes = max(self.max_logical_node_bytes, len(raw))
        return raw


def _is_gir(archive: Path) -> bool:
    with archive.open("rb") as stream:
        return stream.read(8) == gir.MAG


def _consume_file(
    session: _StreamingSession,
    rel: str,
    desc: list,
    tree: "hashlib._Hash",
    target_root: Path | None,
) -> int:
    if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
        raise RuntimeError("malformed GIR file")
    safe = gir._safe_relpath(rel)
    node_ids, logical_size, expected = desc
    if not isinstance(node_ids, list) or not isinstance(logical_size, int) or isinstance(logical_size, bool):
        raise RuntimeError("malformed GIR file declaration")

    rel_bytes = rel.encode("utf-8")
    tree.update(len(rel_bytes).to_bytes(4, "little"))
    tree.update(rel_bytes)
    tree.update(logical_size.to_bytes(8, "little"))

    file_hash = hashlib.sha256()
    written = 0
    output = None
    try:
        if target_root is not None:
            target = target_root.joinpath(*safe.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            output = target.open("wb")
        for node_id in node_ids:
            # Footnote: no node cache is intentional. A repeated logical reference is read exactly when its
            # logical bytes are consumed, keeping working memory O(MAX_CHUNK) rather than O(unique archive).
            raw = session.node(node_id)
            written += len(raw)
            if written > logical_size:
                raise RuntimeError("GIR streamed file exceeds declared logical size")
            file_hash.update(raw)
            tree.update(raw)
            if output is not None:
                output.write(raw)
    finally:
        if output is not None:
            output.close()

    if written != logical_size or file_hash.digest() != expected:
        raise RuntimeError("GIR streamed logical file integrity")
    return written


def _stream_archive(archive: Path, target_root: Path | None) -> dict:
    session = _StreamingSession(archive)
    tree = hashlib.sha256()
    logical_bytes = 0
    files = 0
    try:
        for rel in sorted(session.meta["files"]):
            logical_bytes += _consume_file(session, rel, session.meta["files"][rel], tree, target_root)
            files += 1
        got = tree.hexdigest()
        expected = session.meta.get("tree_sha256")
        if got != expected:
            raise RuntimeError("GIR streamed tree identity mismatch")
        return {
            "ok": True,
            "files": files,
            "logical_bytes": logical_bytes,
            "tree_sha256": got,
            "expected_tree_sha256": expected,
            "engine": "Geometry-IR-v1",
            "reader": "Geometry-IR-streaming-v1",
            "max_logical_node_bytes": session.max_logical_node_bytes,
            "max_physical_record_bytes": session.max_physical_record_bytes,
            "physical_record_reads": session.physical_record_reads,
        }
    finally:
        session.close()


def strong_verify(archive: Path) -> dict:
    if not _is_gir(archive):
        return gir.BASE.strong_verify(archive)
    try:
        return _stream_archive(archive, None)
    except Exception as exc:
        return {"ok": False, "error": repr(exc), "engine": "Geometry-IR-v1", "reader": "Geometry-IR-streaming-v1"}


def _remove_backup_best_effort(backup: Path) -> None:
    """Remove an obsolete pre-publication backup without turning successful publication into false failure."""
    try:
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink(missing_ok=True)
    except OSError:
        # Footnote: once the fully verified replacement is published, cleanup failure is not archive failure.
        # Leaving a uniquely named backup is safer than reporting extraction failure after state already moved.
        pass


def extract(archive: Path, dst: Path) -> None:
    if not _is_gir(archive):
        gir.BASE.extract(archive, dst)
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.gir-stage-", dir=dst.parent))
    backup = dst.parent / f".{dst.name}.gir-backup-{uuid.uuid4().hex}"
    moved_old = False
    installed_new = False
    try:
        _stream_archive(archive, staging)

        # Footnote: extraction first verifies the complete staged tree. Only then does it move the previous
        # destination aside and publish the new directory. If publication itself fails, the old destination
        # is restored rather than being destroyed before archive verification has completed.
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


def build(root: Path, out: Path) -> dict:
    return gir.build(root, out)


def _build_gir(root: Path, out: Path) -> dict:
    return gir._build_gir(root, out)


def treehash(root: Path) -> str:
    return gir.treehash(root)


if __name__ == "__main__":
    # Keep the research CLI delegated to the owning grammar. Promotion should expose a stable streaming CLI
    # only after native/shared-reader parity and golden-vector compatibility are independently proven.
    gir._main()
