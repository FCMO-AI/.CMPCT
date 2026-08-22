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
"""

import hashlib
import os
from pathlib import Path

import msgpack

from benchmarks import v030_logs_inverse_edge_oracle as BASE
from experiments import entropygraph_v030_logs_inverse_profile as P

Archive = P.Archive
extract = P.extract
strong_verify = P.strong_verify
recovery_probe = P.recovery_probe
PROFILE = P.PROFILE
LEVEL = P.LEVEL
MAX_DECODE_UNIT = P.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = P.MAX_MEMBER_AMPLIFICATION


def build(
    source: Path,
    archive: Path,
    *,
    compressed_direct_paths: set[str] | frozenset[str] | None = None,
) -> dict:
    compressed_direct_paths = frozenset(compressed_direct_paths or ())
    rows, edges, edge_stats = BASE._scan_and_edges(source)
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
