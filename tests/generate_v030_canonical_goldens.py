#!/usr/bin/env python3
"""Generate tiny builder-independent canonical CMP25 acceptance archives.

This file intentionally does NOT import cmpct.builder or any v0.30 experiment writer.
It writes the fixed G0-G4 and PrefixGraph framing from primitive struct/msgpack/zstd
operations so a bug shared by the product encoder and reader cannot manufacture its
own passing golden fixture.
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
DEFAULT_OUT = ROOT / "tests" / "conformance" / "v030-r25-canonical.json"
INTERNAL = ".__cmpct_r25_internal__/filesystem-v1.msgpack"
MANIFEST_PROFILE = "cmpct-r25-filesystem-manifest-v1"
G04_ENGINE = "EntropyGraph-II-v030-G04Overlay-v1"
PREFIX_ENGINE = "PrefixGraph-depth1-v1"
G04_MAGIC = b"CMP25G4\0"
G04_TAIL = b"C25G4TL\0"
PREFIX_MAGIC = b"CMP25PG\0"
PREFIX_TAIL = b"C25PGTL\0"
G04_HEADER = struct.Struct("<8sQQIQQ32s32s")
G04_FOOTER = struct.Struct("<8sQQ32s32s")
PHYSICAL_HEADER = struct.Struct("<BQQI32s")
PREFIX_HEADER = struct.Struct("<8sQQ32s")
PREFIX_FOOTER = struct.Struct("<8sQQ32s")


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def pack(value) -> bytes:
    return msgpack.packb(value, use_bin_type=True, strict_types=True)


def zpack(data: bytes) -> bytes:
    # Footnote: zstd here is only the documented physical/meta codec. No CMPCT search,
    # graph selection, geometry heuristic, or archive writer participates in the fixture.
    return zstd.ZstdCompressor(level=6, write_checksum=True).compress(data)


def tree_sha(files: dict[str, bytes]) -> bytes:
    h = hashlib.sha256()
    for rel in sorted(files):
        name = rel.encode("utf-8")
        raw = files[rel]
        h.update(struct.pack("<I", len(name)))
        h.update(name)
        h.update(struct.pack("<Q", len(raw)))
        h.update(raw)
    return h.digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return sha(b"cmpct-merkle-empty-v1")
    level = [sha(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [sha(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def filesystem_payload() -> tuple[bytes, dict]:
    raw = (b"canonical-r25-portability\n" * 11) + bytes(range(32))
    digest = sha(raw)
    entries = [
        ["dir", "d", 0o755, 1_700_000_000_000_000_001, 1000, 1000, [], None],
        [
            "dir/hello.bin",
            "f",
            0o640,
            1_700_000_000_000_000_002,
            1000,
            1000,
            [["user.cmpct.golden", b"canonical-v1"]],
            [len(raw), digest],
        ],
        [
            "dir/hello-hard.bin",
            "h",
            0o640,
            1_700_000_000_000_000_003,
            1000,
            1000,
            [],
            "dir/hello.bin",
        ],
        [
            "link.bin",
            "l",
            0o777,
            1_700_000_000_000_000_004,
            1000,
            1000,
            [],
            "dir/hello.bin",
        ],
    ]
    manifest = pack(
        {
            "v": 1,
            "profile": MANIFEST_PROFILE,
            "internal_path": INTERNAL,
            "entries": entries,
        }
    )
    expected = {
        "dir": {"kind": 1, "size": 0},
        "dir/hello.bin": {"kind": 0, "size": len(raw), "sha256": digest.hex()},
        "dir/hello-hard.bin": {"kind": 3, "size": len(raw), "sha256": digest.hex()},
        "link.bin": {"kind": 2, "size": len(b"dir/hello.bin"), "target": "dir/hello.bin"},
    }
    return manifest, {"raw": raw, "expected": expected}


def g04_archive(manifest: bytes, user_raw: bytes) -> tuple[bytes, bytes]:
    logical = {"dir/hello.bin": user_raw, INTERNAL: manifest}
    paths = sorted(logical)
    records: list[bytes] = []
    leaves: list[bytes] = []
    offsets: list[int] = []
    nodes: list[list] = []
    files: dict[str, list] = {}
    cursor = 0
    for record_id, rel in enumerate(paths):
        raw = logical[rel]
        payload = raw  # physical codec 0 == raw
        logical_digest = sha(raw)
        offsets.append(cursor)
        leaves.append(sha(payload))
        physical = PHYSICAL_HEADER.pack(
            0,
            len(raw),
            len(payload),
            zlib.crc32(raw) & 0xFFFFFFFF,
            logical_digest,
        ) + payload
        records.append(physical)
        cursor += len(physical)
        node_id = len(nodes)
        nodes.append(["direct", record_id, 0, len(raw), logical_digest])
        files[rel] = ["nodes", [node_id], len(raw), logical_digest]

    tree = tree_sha(logical)
    metadata = {
        "v": 4,
        "engine": G04_ENGINE,
        "tree_sha256": tree.hex(),
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
        G04_MAGIC,
        len(meta_z),
        len(meta_raw),
        len(records),
        8 * 1024 * 1024,
        96 * 1024 * 1024,
        meta_digest,
        merkle,
    )
    footer = G04_FOOTER.pack(G04_TAIL, len(meta_z), len(meta_raw), meta_digest, merkle)
    return header + meta_z + b"".join(records) + meta_z + footer, tree


def prefix_archive(manifest: bytes, user_raw: bytes) -> tuple[bytes, bytes]:
    logical = {"dir/hello.bin": user_raw, INTERNAL: manifest}
    paths = sorted(logical)
    payloads: list[bytes] = []
    records: list[list] = []
    for rel in paths:
        raw = logical[rel]
        payload = zpack(raw)
        payloads.append(payload)
        records.append(["direct", -1, len(raw), len(payload), sha(payload), sha(raw)])
    tree = tree_sha(logical)
    metadata = {
        "v": 1,
        "engine": PREFIX_ENGINE,
        "tree_sha256": tree.hex(),
        "files": paths,
        "records": records,
        "max_dependency_depth": 1,
        "max_file_bytes": 8 * 1024 * 1024,
        "max_member_read_amplification": 8.0,
    }
    meta_raw = pack(metadata)
    meta_z = zpack(meta_raw)
    meta_digest = sha(meta_raw)
    header = PREFIX_HEADER.pack(PREFIX_MAGIC, len(meta_z), len(meta_raw), meta_digest)
    footer = PREFIX_FOOTER.pack(PREFIX_TAIL, len(meta_z), len(meta_raw), meta_digest)
    return header + meta_z + b"".join(payloads) + meta_z + footer, tree


def document() -> dict:
    manifest, fs = filesystem_payload()
    user_raw = fs["raw"]
    result = {
        "schema": "cmpct-v030-native-canonical-golden-v1",
        "provenance": (
            "Generated directly from frozen byte grammars by tests/generate_v030_canonical_goldens.py; "
            "no CMPCT Builder or v0.30 experiment writer imported."
        ),
        "filesystem": {
            "manifest_sha256": sha(manifest).hex(),
            "entries": fs["expected"],
            "internal_path": INTERNAL,
        },
    }
    for key, maker, profile in (
        ("g04", g04_archive, "g04-r25"),
        ("prefixgraph", prefix_archive, "prefixgraph-r25"),
    ):
        archive, tree = maker(manifest, user_raw)
        result[key] = {
            "profile": profile,
            "revision": 25,
            "archive_base64": base64.b64encode(archive).decode("ascii"),
            "archive_sha256": sha(archive).hex(),
            "tree_sha256": tree.hex(),
            "archive_size": len(archive),
        }
    return result


def render() -> str:
    return json.dumps(document(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = render()
    if args.check:
        if not args.output.is_file() or args.output.read_text() != generated:
            raise SystemExit(f"canonical golden drift: regenerate {args.output}")
        print(f"canonical goldens reproducible: {args.output}")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated)
    print(args.output)


if __name__ == "__main__":
    main()
