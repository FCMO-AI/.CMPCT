from __future__ import annotations

"""Physical-locality refinement of the recoverable logs inverse-edge profile.

v1 used one raw payload pack for all retained compressed sidecars. Although those bytes require no decompression,
a naive reader could still touch unrelated sidecar bytes. v2 stores each retained sidecar in its own authenticated
RAW pack so physical bytes touched, decoded context and logical ownership all agree. The archive grammar and reader
remain the same; only writer pack partitioning changes.

The optional ``compressed_direct_paths`` hook exists for wrappers that add small, highly compressible internal
control members such as the canonical filesystem manifest. The default is empty, preserving v2's exact historical
product-boundary bytes. A compressed direct member is represented as ordinary ``pack`` storage so locality accounts
for its decoded pack rather than pretending compressed storage is a raw range read.

``allowed_inverse_codecs`` is a productization boundary, not a benchmark shortcut: edge discovery may observe
additional standard sidecars, but the writer emits a derive edge only when the selected decoder is implemented by
all required release readers. Unsupported relations remain ordinary directly stored/segmented logical files.

Whole-archive verify/extract uses one authenticated decode session. This is deliberately separate from
``read_member``: selective reads retain the cold-cache operation boundary used by the frozen <=8x locality law,
while archive-wide operations may legitimately reuse a pack or inverse dependency already decoded earlier in the
same full-tree operation. Archive bytes and random-access semantics are unchanged.
"""

import hashlib
import os
from pathlib import Path

import msgpack

from benchmarks import v030_logs_inverse_edge_oracle as BASE
from experiments import entropygraph_v030_logs_inverse_profile as P

PROFILE = P.PROFILE
LEVEL = P.LEVEL
MAX_DECODE_UNIT = P.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = P.MAX_MEMBER_AMPLIFICATION


class Archive(P.Archive):
    """v2 reader with cold selective reads and shared full-operation decode sessions."""

    def _restore_session(
        self,
        item: int,
        *,
        member_cache: dict[int, tuple[bytes, int]],
        pack_cache: dict[int, bytes],
        active: set[int],
    ) -> tuple[bytes, int]:
        if item in member_cache:
            return member_cache[item]
        if item in active or item < 0 or item >= len(self.files):
            raise RuntimeError("logs profile dependency error")
        active.add(item)
        try:
            _prefix, _suffix, size, expected_sha, storage, _rel = self.files[item]
            size = int(size)
            kind = storage[0]
            if kind in ("pack", "raw"):
                pack_index, offset, length = map(int, storage[1:])
                pack = pack_cache.get(pack_index)
                if pack is None:
                    pack = self._read_pack(pack_index)
                    pack_cache[pack_index] = pack
                if offset < 0 or length != size or offset + length > len(pack):
                    raise RuntimeError("logs profile slice bounds")
                value = pack[offset : offset + length]
                # Context remains the cold selective-read context even though the full-tree operation reuses the
                # authenticated pack. This preserves locality evidence while avoiding repeated decompression.
                decoded_context = len(pack) if kind == "pack" else length
            elif kind == "derive":
                source_index = int(storage[1])
                if source_index == item:
                    raise RuntimeError("logs profile self dependency")
                source, source_context = self._restore_session(
                    source_index,
                    member_cache=member_cache,
                    pack_cache=pack_cache,
                    active=active,
                )
                value = BASE._decode(storage[2], source)
                decoded_context = source_context + len(value)
            else:
                raise RuntimeError("unknown logs profile storage")
            if len(value) != size or hashlib.sha256(value).digest() != expected_sha:
                raise RuntimeError("logs profile logical identity")
            member_cache[item] = (value, decoded_context)
            return member_cache[item]
        finally:
            active.discard(item)

    def verify_all(self) -> dict:
        max_amp = 1.0
        max_context = 0
        identities = []
        member_cache: dict[int, tuple[bytes, int]] = {}
        pack_cache: dict[int, bytes] = {}
        active: set[int] = set()
        for index, row in enumerate(self.files):
            value, context = self._restore_session(
                index,
                member_cache=member_cache,
                pack_cache=pack_cache,
                active=active,
            )
            size = int(row[2])
            amp = context / max(1, size)
            if amp > P.MAX_MEMBER_AMPLIFICATION or context > P.MAX_DECODE_UNIT:
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
            "full_operation_unique_packs_decoded": len(pack_cache),
            "full_operation_unique_members_restored": len(member_cache),
        }

    def extract(self, dst: Path) -> None:
        dst.mkdir(parents=True, exist_ok=True)
        member_cache: dict[int, tuple[bytes, int]] = {}
        pack_cache: dict[int, bytes] = {}
        active: set[int] = set()
        root = dst.resolve()
        for index, row in enumerate(self.files):
            target = dst / row[5]
            resolved = target.resolve()
            if resolved != root and root not in resolved.parents:
                raise RuntimeError("logs profile extraction traversal")
            target.parent.mkdir(parents=True, exist_ok=True)
            value, _context = self._restore_session(
                index,
                member_cache=member_cache,
                pack_cache=pack_cache,
                active=active,
            )
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
    import tempfile

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-recovery-") as td:
        root = Path(td)
        primary = root / "primary-damaged.cmpct"
        raw = bytearray(original)
        if len(raw) <= P.HEADER.size + 8:
            raise RuntimeError("logs profile archive too short for recovery probe")
        raw[P.HEADER.size + 3] ^= 0x5A
        primary.write_bytes(raw)
        results["primary_damage"] = strong_verify(primary)

        tail = root / "tail-damaged.cmpct"
        raw = bytearray(original)
        footer = P.FOOTER.unpack(raw[-P.FOOTER.size:])
        tail_csize = int(footer[1])
        tail_meta_offset = len(raw) - P.FOOTER.size - tail_csize
        raw[tail_meta_offset + 3] ^= 0xA5
        tail.write_bytes(raw)
        results["tail_damage"] = strong_verify(tail)

        both = root / "both-damaged.cmpct"
        raw = bytearray(original)
        raw[P.HEADER.size + 3] ^= 0x5A
        raw[tail_meta_offset + 3] ^= 0xA5
        both.write_bytes(raw)
        try:
            strong_verify(both)
            both_failed_closed = False
        except Exception:
            both_failed_closed = True
        results["both_failed_closed"] = both_failed_closed
    return results


def build(
    source: Path,
    archive: Path,
    *,
    compressed_direct_paths: set[str] | frozenset[str] | None = None,
    allowed_inverse_codecs: set[str] | frozenset[str] | None = None,
) -> dict:
    compressed_direct_paths = frozenset(compressed_direct_paths or ())
    allowed = None if allowed_inverse_codecs is None else frozenset(allowed_inverse_codecs)
    rows, edges, edge_stats = BASE._scan_and_edges(source)
    if allowed is not None:
        edges = {
            target_index: edge
            for target_index, edge in edges.items()
            if edge[1] in allowed
        }
    edge_stats = dict(edge_stats)
    edge_stats.update({
        "inverse_edges": len(edges),
        "inverse_edge_targets": [str(rows[index]["rel"]) for index in sorted(edges)],
        "inverse_edge_sources": [str(rows[edges[index][0]]["rel"]) for index in sorted(edges)],
        "inverse_edge_codecs": [str(edges[index][1]) for index in sorted(edges)],
        "allowed_inverse_codecs": None if allowed is None else sorted(allowed),
    })
    if not rows or len(rows) > P.MAX_FILES:
        raise RuntimeError("logs profile file-count bounds")
    segments, max_amp, max_unit = BASE._plan_segments(rows, edges)
    if max_amp > P.MAX_MEMBER_AMPLIFICATION or max_unit > P.MAX_DECODE_UNIT:
        raise RuntimeError("logs profile locality admission")

    packs = []
    owners: dict[int, tuple[int, int, int]] = {}
    for members in segments:
        raw = b"".join(rows[index]["raw"] for index in members)
        pack_index = len(packs)
        cursor = 0
        for index in members:
            length = int(rows[index]["size"])
            owners[index] = (pack_index, cursor, length)
            cursor += length
        packs.append(P._pack_row(raw, compress=True))

    direct_packs: dict[int, tuple[int, str]] = {}
    compressed_direct_count = 0
    for index, row in enumerate(rows):
        if index in edges or index in owners:
            continue
        rel = str(row["rel"])
        compress = rel in compressed_direct_paths
        pack_index = len(packs)
        packs.append(P._pack_row(row["raw"], compress=compress))
        direct_packs[index] = (pack_index, "pack" if compress else "raw")
        compressed_direct_count += int(compress)
    if len(packs) > P.MAX_PACKS:
        raise RuntimeError("logs profile pack-count bounds")

    files = []
    previous = ""
    for index, row in enumerate(rows):
        rel = str(row["rel"])
        if len(rel.encode("utf-8")) > P.MAX_PATH_BYTES:
            raise RuntimeError("logs profile path bound")
        prefix = BASE._common_prefix(previous, rel)
        if index in edges:
            source_index, codec = edges[index]
            storage = ["derive", int(source_index), codec]
        elif index in owners:
            pack_index, offset, length = owners[index]
            storage = ["pack", pack_index, offset, length]
        else:
            pack_index, kind = direct_packs[index]
            storage = [kind, pack_index, 0, int(row["size"])]
        files.append([prefix, rel[prefix:], int(row["size"]), row["sha256"], storage])
        previous = rel

    meta = msgpack.packb([P.PROFILE, P.LEVEL, files], use_bin_type=True)
    if len(meta) > P.MAX_META_RAW:
        raise RuntimeError("logs profile metadata too large")
    meta_comp = P._meta_compress(meta)
    if len(meta_comp) > P.MAX_META_COMP:
        raise RuntimeError("logs profile compressed metadata too large")
    meta_sha = hashlib.sha256(meta).digest()

    archive.parent.mkdir(parents=True, exist_ok=True)
    temp = archive.with_name(archive.name + ".tmp")
    with temp.open("wb") as handle:
        handle.write(P.HEADER.pack(P.MAGIC, len(meta_comp), len(meta), len(packs), meta_sha))
        handle.write(meta_comp)
        for codec, usize, payload, crc, sha in packs:
            handle.write(P.PACK_HEADER.pack(codec, usize, len(payload), crc, sha))
            handle.write(payload)
        handle.write(meta_comp)
        handle.write(P.FOOTER.pack(P.TAIL_MAGIC, len(meta_comp), len(meta), len(packs), meta_sha))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, archive)
    return {
        "profile": P.PROFILE,
        "profile_writer_revision": 2,
        "level": P.LEVEL,
        "archive_bytes": archive.stat().st_size,
        "files": len(rows),
        "packs": len(packs),
        "direct_sidecar_packs": len(direct_packs),
        "compressed_direct_packs": compressed_direct_count,
        "meta_raw_bytes": len(meta),
        "meta_comp_bytes": len(meta_comp),
        "recovery_control_copies": 2,
        "payload_copies": 1,
        "edge_detection": edge_stats,
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_unit,
    }
