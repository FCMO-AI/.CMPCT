#!/usr/bin/env python3
"""Reproduce builder-independent canonical r25 implicit-v4 conformance bytes.

The generator intentionally imports no CMPCT writer/reader code. It constructs the compact filesystem-control
MessagePack value and both canonical content-profile framings from primitive struct/MessagePack/Zstandard operations,
so implementation bugs cannot regenerate their own acceptance target. G04 raw frames are assembled by hand;
PrefixGraph uses the independently invoked standard Zstandard codec at its frozen canonical payload/meta levels.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib

import msgpack
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "tests" / "conformance" / "v030-r25-implicit-v4.json"
INTERNAL = ".__cmpct_r25_internal__/filesystem-v1.msgpack"
G04_MAGIC = b"CMP25G4\0"
G04_TAIL = b"C25G4TL\0"
PREFIX_MAGIC = b"CMP25PG\0"
PREFIX_TAIL = b"C25PGTL\0"
G04_HEADER = struct.Struct("<8sQQIQQ32s32s")
G04_FOOTER = struct.Struct("<8sQQ32s32s")
PHYSICAL_HEADER = struct.Struct("<BQQI32s")
PREFIX_HEADER = struct.Struct("<8sQQ32s")
PREFIX_FOOTER = struct.Struct("<8sQQ32s")
ZSTD_MAGIC = bytes.fromhex("28b52ffd")
ZSTD_MAX_RAW_BLOCK = (1 << 17) - 1
PREFIX_PAYLOAD_LEVEL = 19
PREFIX_META_LEVEL = 12


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def pack(value) -> bytes:
    return msgpack.packb(value, use_bin_type=True, strict_types=True)


def zpack(data: bytes) -> bytes:
    """Construct the fixed raw-block Zstandard framing used by the G04 independent oracle."""
    size = len(data)
    out = bytearray(ZSTD_MAGIC)
    if size < 256:
        out += bytes([0x20, size])
    elif size < 65_792:
        out.append(0x60)
        out += (size - 256).to_bytes(2, "little")
    elif size < 1 << 32:
        out.append(0xA0)
        out += size.to_bytes(4, "little")
    else:
        out.append(0xE0)
        out += size.to_bytes(8, "little")
    if not data:
        out += (1).to_bytes(3, "little")
        return bytes(out)
    cursor = 0
    while cursor < size:
        block = data[cursor : cursor + ZSTD_MAX_RAW_BLOCK]
        cursor += len(block)
        out += ((len(block) << 3) | int(cursor == size)).to_bytes(3, "little")
        out += block
    return bytes(out)


def zcompress(data: bytes, level: int) -> bytes:
    """Invoke Zstandard independently of CMPCT at a frozen canonical PrefixGraph level."""
    return zstd.ZstdCompressor(level=level).compress(data)


def tree_sha(files: dict[str, bytes]) -> bytes:
    digest = hashlib.sha256()
    for rel in sorted(files):
        name = rel.encode("utf-8")
        raw = files[rel]
        digest.update(struct.pack("<I", len(name)))
        digest.update(name)
        digest.update(struct.pack("<Q", len(raw)))
        digest.update(raw)
    return digest.digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return sha(b"cmpct-merkle-empty-v1")
    level = [sha(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [sha(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def common_prefix(left: str, right: str) -> int:
    cursor = 0
    while cursor < min(len(left), len(right)) and left[cursor] == right[cursor]:
        cursor += 1
    return cursor


def implicit_filesystem() -> tuple[bytes, bytes, dict[str, dict]]:
    raw = (b"canonical-r25-portability\n" * 11) + bytes(range(32))
    digest = sha(raw)
    default = [0o640, 1_700_000_000_000_000_002, 1000, 1000, [["user.cmpct.golden", b"canonical-v1"]]]

    def override(meta: list) -> list:
        mask = 0
        values = []
        for bit, index in [(1, 0), (2, 1), (4, 2), (8, 3)]:
            if meta[index] != default[index]:
                mask |= bit
                values.append(meta[index] - default[index])
        if meta[4] != default[4]:
            mask |= 16
            values.append(meta[4])
        return [mask, *values]

    rows = [
        ("dir", 1, [0o755, 1_700_000_000_000_000_001, 1000, 1000, []], None),
        ("dir/hello-hard.bin", 3, [0o640, 1_700_000_000_000_000_003, 1000, 1000, []], 0),
        ("link.bin", 2, [0o777, 1_700_000_000_000_000_004, 1000, 1000, []], "dir/hello.bin"),
    ]
    explicit = []
    previous = ""
    for path, kind, metadata, payload in rows:
        prefix = common_prefix(previous, path)
        explicit.append([prefix, path[prefix:], kind, override(metadata), payload])
        previous = path
    manifest = pack([4, default, [[0]], explicit])
    expected = {
        "dir": {"kind": 1, "size": 0},
        "dir/hello.bin": {"kind": 0, "size": len(raw), "sha256": digest.hex()},
        "dir/hello-hard.bin": {"kind": 3, "size": len(raw), "sha256": digest.hex()},
        "link.bin": {"kind": 2, "size": len(b"dir/hello.bin"), "target": "dir/hello.bin"},
    }
    return manifest, raw, expected


def g04_archive(manifest: bytes, user_raw: bytes) -> bytes:
    logical = {"dir/hello.bin": user_raw, INTERNAL: manifest}
    records: list[bytes] = []
    leaves: list[bytes] = []
    offsets: list[int] = []
    nodes: list[list] = []
    files: dict[str, list] = {}
    cursor = 0
    for record_id, rel in enumerate(sorted(logical)):
        raw = logical[rel]
        digest = sha(raw)
        offsets.append(cursor)
        leaves.append(sha(raw))
        physical = PHYSICAL_HEADER.pack(0, len(raw), len(raw), zlib.crc32(raw) & 0xFFFFFFFF, digest) + raw
        records.append(physical)
        cursor += len(physical)
        node_id = len(nodes)
        nodes.append(["direct", record_id, 0, len(raw), digest])
        files[rel] = ["nodes", [node_id], len(raw), digest]
    metadata = {
        "v": 4,
        "engine": "EntropyGraph-II-v030-G04Overlay-v1",
        "tree_sha256": tree_sha(logical).hex(),
        "record_leaf_sha256": leaves,
        "record_rel_offsets": offsets,
        "physical_geometry": [None] * len(records),
        "hierarchical_geometry": {
            "max_rows": 65_536,
            "max_fields_per_row": 256,
            "max_field_descriptors": 131_072,
            "max_cell_scans": 8 * 512 * 1024,
            "max_exact_finalists": 3,
            "screen_level": 6,
            "exact_level": 19,
        },
        "max_geometry_member_read_amplification": 8.0,
        "max_decode_unit": 8 * 1024 * 1024,
        "max_decoder_memory": 96 * 1024 * 1024,
        "nodes": nodes,
        "files": files,
    }
    meta_raw = pack(metadata)
    meta_z = zpack(meta_raw)
    meta_digest = sha(meta_raw)
    merkle = merkle_root(leaves)
    header = G04_HEADER.pack(
        G04_MAGIC, len(meta_z), len(meta_raw), len(records), 8 * 1024 * 1024, 96 * 1024 * 1024, meta_digest, merkle
    )
    footer = G04_FOOTER.pack(G04_TAIL, len(meta_z), len(meta_raw), meta_digest, merkle)
    return header + meta_z + b"".join(records) + meta_z + footer


def prefix_archive(manifest: bytes, user_raw: bytes) -> bytes:
    logical = {"dir/hello.bin": user_raw, INTERNAL: manifest}
    payloads: list[bytes] = []
    records: list[list] = []
    paths = sorted(logical)
    for rel in paths:
        raw = logical[rel]
        payload = zcompress(raw, PREFIX_PAYLOAD_LEVEL)
        payloads.append(payload)
        records.append(["direct", -1, len(raw), len(payload), sha(payload), sha(raw)])
    metadata = {
        "v": 1,
        "engine": "PrefixGraph-depth1-v1",
        "tree_sha256": tree_sha(logical).hex(),
        "files": paths,
        "records": records,
        "max_dependency_depth": 1,
        "max_file_bytes": 8 * 1024 * 1024,
        "max_member_read_amplification": 8.0,
    }
    meta_raw = pack(metadata)
    meta_z = zcompress(meta_raw, PREFIX_META_LEVEL)
    meta_digest = sha(meta_raw)
    header = PREFIX_HEADER.pack(PREFIX_MAGIC, len(meta_z), len(meta_raw), meta_digest)
    footer = PREFIX_FOOTER.pack(PREFIX_TAIL, len(meta_z), len(meta_raw), meta_digest)
    return header + meta_z + b"".join(payloads) + meta_z + footer


def document() -> dict:
    manifest, user_raw, expected = implicit_filesystem()
    g04 = g04_archive(manifest, user_raw)
    prefix = prefix_archive(manifest, user_raw)
    return {
        "schema": "cmpct-v030-native-implicit-v4-golden-v1",
        "filesystem": {
            "internal_path": INTERNAL,
            "manifest_sha256": sha(manifest).hex(),
            "entries": expected,
        },
        "g04": {
            "profile": "g04-r25",
            "archive_sha256": sha(g04).hex(),
            "archive_base64": base64.b64encode(g04).decode("ascii"),
        },
        "prefixgraph": {
            "profile": "prefixgraph-r25",
            "archive_sha256": sha(prefix).hex(),
            "archive_base64": base64.b64encode(prefix).decode("ascii"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    generated = document()
    if args.check:
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        if existing != generated:
            raise SystemExit(f"implicit-v4 fixed conformance vector drifted: {args.output}")
        print(f"implicit-v4 fixed conformance vector reproduced: {args.output}")
        return
    args.output.write_text(json.dumps(generated, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
