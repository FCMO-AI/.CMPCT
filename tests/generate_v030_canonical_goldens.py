#!/usr/bin/env python3
"""Generate builder-independent canonical CMP25 acceptance archives.

This generator deliberately does not import the CMPCT builder or any v0.30 writer. It emits fixed G0-G4 and
PrefixGraph framing from struct/msgpack plus a tiny deterministic raw-block Zstandard encoder, so a bug shared by
the product encoder/reader or a different system-zstd build cannot manufacture or drift its own passing fixture.
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
ZSTD_MAGIC = bytes.fromhex("28b52ffd")
ZSTD_MAX_RAW_BLOCK = (1 << 17) - 1


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def pack(value) -> bytes:
    return msgpack.packb(value, use_bin_type=True, strict_types=True)


def zpack(data: bytes) -> bytes:
    """Emit one deterministic single-segment Zstandard frame containing only RAW blocks.

    Footnote: compression ratio is irrelevant to a conformance golden; stable independently decodable bytes are
    the goal. RAW blocks exercise the exact Zstandard framing/decoder contract without depending on libzstd's
    optimizer decisions, version, CPU dispatch, external executable, or CMPCT implementation code.
    """
    size = len(data)
    out = bytearray(ZSTD_MAGIC)
    if size < 256:
        out.append(0x20)  # single-segment, 1-byte frame content size
        out.append(size)
    elif size < 65_792:
        out.append(0x60)  # single-segment, 2-byte FCS encoded as size-256
        out += (size - 256).to_bytes(2, "little")
    elif size < 1 << 32:
        out.append(0xA0)  # single-segment, 4-byte frame content size
        out += size.to_bytes(4, "little")
    else:
        out.append(0xE0)  # single-segment, 8-byte frame content size
        out += size.to_bytes(8, "little")

    if not data:
        out += (1).to_bytes(3, "little")  # last RAW block, zero-byte payload
        return bytes(out)
    cursor = 0
    while cursor < size:
        block = data[cursor : cursor + ZSTD_MAX_RAW_BLOCK]
        cursor += len(block)
        # Zstd block header: bit0=last, bits1..2=RAW type(0), bits3..=block size.
        header = (len(block) << 3) | int(cursor == size)
        out += header.to_bytes(3, "little")
        out += block
    return bytes(out)


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


def filesystem_payload() -> tuple[bytes, dict]:
    raw = (b"canonical-r25-portability\n" * 11) + bytes(range(32))
    digest = sha(raw)
    owner_metadata = [
        0o640,
        1_700_000_000_000_000_002,
        1000,
        1000,
        [["user.cmpct.golden", b"canonical-v1"]],
    ]
    entries = [
        ["dir", "d", 0o755, 1_700_000_000_000_000_001, 1000, 1000, [], None],
        [
            "dir/hello.bin",
            "f",
            *owner_metadata,
            [len(raw), digest],
        ],
        [
            "dir/hello-hard.bin",
            "h",
            *owner_metadata,
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
        payload = raw
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
        "schema": "cmpct-v030-native-canonical-golden-v2",
        "provenance": (
            "Generated directly from frozen byte grammars and deterministic raw-block Zstandard frames by "
            "tests/generate_v030_canonical_goldens.py; no CMPCT Builder, v0.30 writer, or external compressor "
            "implementation participates in canonical golden bytes."
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
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != generated:
            raise SystemExit(f"canonical golden drift: regenerate {args.output}")
        print(f"canonical goldens reproducible: {args.output}")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

# Footnote: raw-block Zstandard is intentionally worse compression but better conformance engineering: the
# independently committed golden bytes are a pure function of this short framing grammar and fixture content,
# not of a compressor version or optimization heuristic. Production archives still use ordinary zstd encoding.