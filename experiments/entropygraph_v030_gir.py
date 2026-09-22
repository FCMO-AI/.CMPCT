"""CMPCT v0.30 research — self-contained Geometry IR archive (CMPNX14).

CMPNX14 is the first research grammar that makes the Geometry ladder pay complete archive costs.  Every
logical node independently tournaments the already-proven Geometry-v1 portfolio (direct, byte lanes, flat
delimiter transpose) against Hierarchical Geometry / Prefix Planes.  The chosen physical view is then stored
inside one authenticated archive with duplicated metadata, physical CRC/SHA-256, payload Merkle leaves and
exact logical hashes.

This is intentionally *not* a canonical format revision.  ``build`` still tournaments the complete CMPNX14
artifact against the accepted v0.29 release engine and emits v0.29 unchanged whenever GIR loses.  A later
Mosaic integration may reuse this transform compiler at the physical-record boundary, but this standalone
archive exists first so framing, descriptor and recovery costs cannot hide behind detached payload oracles.

Footnote: code is deliberately explicit rather than patching the CMPNX13 reader at runtime.  A new node kind
must have a new magic and an independently reviewable reader contract; otherwise an old research reader could
silently reinterpret bytes it was never designed to understand.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
import time

import msgpack

from experiments import entropygraph_v030_geometry as G
from experiments import entropygraph_v030_hierarchical_geometry as HG

H = G.H
zc = G.zc
zd = G.zd
PH = G.PH
BASE = G.BASE
L = G.L
CODEC_RAW = G.CODEC_RAW
CODEC_ZSTD = G.CODEC_ZSTD
MAX_CHUNK = G.MAX_CHUNK
MAX_DECODE_UNIT = G.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = G.MAX_DECODER_MEMORY

MAG = b"CMPNX14\0"
TAIL = b"CMN14T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")
META_LEVEL = 12


def treehash(root: Path) -> str:
    return G.treehash(root)


def _merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return H(b"cmpct-gir-merkle-empty-v1")
    level = [H(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [H(b"\x01" + level[index] + level[index + 1]) for index in range(0, len(level), 2)]
    return level[0]


def _encode_node(raw: bytes) -> dict:
    """Tournament G0/G1/G2 against G3/G4 using actual stored payload bytes.

    The incumbent comes from CMPNX13's existing node audition.  Hierarchical Geometry is allowed to replace
    it only when its physical payload is strictly smaller.  This means adding G3/G4 cannot regress a node
    relative to the previous Geometry portfolio even before the complete-v0.29 archive fallback runs.
    """
    incumbent = G._encode_node(raw)
    best = {
        "kind": incumbent["kind"],
        "param": incumbent.get("param", 0),
        "physical": incumbent["physical"],
        "codec": int(incumbent["codec"]),
        "payload": incumbent["payload"],
        "payload_bytes": int(incumbent["payload_bytes"]),
        "saving_vs_direct": int(incumbent.get("saving", 0)),
        "hierarchical_screened_candidates": 0,
        "hierarchical_exact_finalists": 0,
    }
    hierarchical = HG.audition(raw)
    best["hierarchical_screened_candidates"] = int(hierarchical["screened_candidates"])
    best["hierarchical_exact_finalists"] = int(hierarchical["exact_finalists"])
    if hierarchical["kind"] == "hierarchical" and int(hierarchical["payload_bytes"]) < best["payload_bytes"]:
        # Footnote: HGT2/HGP2 carry their separator and prefix-plane parameters inside the authenticated
        # transformed physical stream.  The node descriptor therefore needs only the logical size/hash;
        # duplicating parameters in metadata would create two sources of truth for the inverse program.
        best = {
            "kind": "hierarchical",
            "param": 1 if hierarchical["prefix_planes"] else 0,
            "physical": hierarchical["physical"],
            "codec": int(hierarchical["codec"]),
            "payload": hierarchical["payload"],
            "payload_bytes": int(hierarchical["payload_bytes"]),
            "saving_vs_direct": int(hierarchical["saving_bytes"]),
            "hierarchical_screened_candidates": int(hierarchical["screened_candidates"]),
            "hierarchical_exact_finalists": int(hierarchical["exact_finalists"]),
        }
    return best


def _build_gir(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]

    nodes: list[bytes] = []
    by_hash: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    aliases = 0
    for file_id, raw in enumerate(raws):
        refs: list[int] = []
        for part in L._balanced_chunks(raw):
            digest = H(part)
            node_id = by_hash.get(digest)
            if node_id is not None and nodes[node_id] == part:
                aliases += 1
            else:
                node_id = len(nodes)
                by_hash[digest] = node_id
                nodes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs

    records: list[tuple[int, int, bytes, int, bytes]] = []
    descriptors: list[list] = []
    kind_counts = {"direct": 0, "lane": 0, "delimiter": 0, "hierarchical": 0}
    hierarchical_prefix_nodes = 0
    payload_saving = 0
    screened_candidates = 0
    exact_finalists = 0
    for raw in nodes:
        chosen = _encode_node(raw)
        physical = chosen["physical"]
        payload = chosen["payload"]
        codec = int(chosen["codec"])
        if len(physical) > MAX_DECODE_UNIT:
            raise RuntimeError("GIR physical node exceeds decode ceiling")
        record_id = len(records)
        records.append((
            codec,
            len(physical),
            payload,
            binascii.crc32(physical) & 0xFFFFFFFF,
            H(physical),
        ))
        kind = str(chosen["kind"])
        if kind == "lane":
            descriptors.append(["lane", record_id, int(chosen["param"]), len(raw), H(raw)])
        elif kind == "delimiter":
            descriptors.append(["delimiter", record_id, len(raw), H(raw)])
        elif kind == "hierarchical":
            descriptors.append(["hierarchical", record_id, len(raw), H(raw)])
            hierarchical_prefix_nodes += int(bool(chosen["param"]))
        elif kind == "direct":
            descriptors.append(["direct", record_id, len(raw), H(raw)])
        else:
            raise RuntimeError(f"unknown GIR writer node kind: {kind}")
        kind_counts[kind] += 1
        payload_saving += int(chosen["saving_vs_direct"])
        screened_candidates += int(chosen["hierarchical_screened_candidates"])
        exact_finalists += int(chosen["hierarchical_exact_finalists"])

    file_desc = {
        rel: [file_nodes[file_id], len(raws[file_id]), H(raws[file_id])]
        for file_id, rel in enumerate(rels)
    }
    leaves = [H(payload) for _, _, payload, _, _ in records]
    merkle = _merkle_root(leaves)
    offsets: list[int] = []
    cursor = 0
    for _, _, payload, _, _ in records:
        offsets.append(cursor)
        cursor += PH.size + len(payload)

    meta = {
        "v": 1,
        "engine": "Geometry-IR-v1",
        "files": file_desc,
        "nodes": descriptors,
        "record_rel_offsets": offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": treehash(root),
        "max_chunk": MAX_CHUNK,
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 0,
        "max_read_amplification": 1.0,
        "geometry": {
            "lane_widths": list(G.LANE_WIDTHS),
            "max_delimiter_candidates": G.MAX_DELIMITER_CANDIDATES,
            "max_delimiter_segments": G.MAX_DELIMITER_SEGMENTS,
        },
        "hierarchical_geometry": dict(HG.RESOURCE_LIMITS),
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > MAX_DECODE_UNIT:
        raise RuntimeError("GIR metadata exceeds decode ceiling")
    meta_comp = zc(meta_raw, META_LEVEL)
    with out.open("wb") as stream:
        stream.write(HDR.pack(
            MAG,
            len(meta_comp),
            len(meta_raw),
            len(records),
            MAX_DECODE_UNIT,
            MAX_DECODER_MEMORY,
            H(meta_raw),
            merkle,
        ))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha))
            stream.write(payload)
        # Duplicated authenticated metadata preserves the recovery experiment inherited from CMPNX13.
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))

    return {
        "create_s": time.perf_counter() - started,
        "graph_bytes": out.stat().st_size,
        "files": len(files),
        "unique_nodes": len(nodes),
        "exact_chunk_aliases": aliases,
        "node_kind_counts": kind_counts,
        "hierarchical_prefix_nodes": hierarchical_prefix_nodes,
        "transform_payload_saving_bytes": payload_saving,
        "hierarchical_screened_candidates": screened_candidates,
        "hierarchical_exact_finalists": exact_finalists,
        "max_read_amplification": 1.0,
        "max_dependency_depth": 0,
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
    }


def build(root: Path, out: Path) -> dict:
    """Tournament the complete GIR artifact against accepted v0.29 bytes."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-gir-v030-") as td:
        temp = Path(td)
        base_path = temp / "v029.cmpct"
        gir_path = temp / "gir.cmpct"
        base_stats = BASE.build(root, base_path)
        gir_stats = _build_gir(root, gir_path)
        base_bytes = base_path.stat().st_size
        gir_bytes = gir_path.stat().st_size
        if gir_bytes < base_bytes:
            shutil.copyfile(gir_path, out)
            selected = "gir"
        else:
            shutil.copyfile(base_path, out)
            selected = "v029-fallback"
        candidate_bytes = out.stat().st_size
        return {
            "selected": selected,
            "archive_bytes": candidate_bytes,
            "v029_bytes": base_bytes,
            "gir_graph_bytes": gir_bytes,
            "saving_vs_v029_bytes": base_bytes - candidate_bytes,
            "smaller_than_v029_pct": (base_bytes - candidate_bytes) / max(1, base_bytes) * 100.0,
            "portfolio_create_s": time.perf_counter() - started,
            "v029": base_stats,
            "gir": gir_stats,
        }


def _decode_meta(
    comp: bytes,
    raw_size: int,
    expected_sha: bytes,
    expected_merkle: bytes,
    expected_count: int | None = None,
) -> tuple[dict, list[int]]:
    if raw_size > MAX_DECODE_UNIT or len(comp) > MAX_DECODE_UNIT:
        raise RuntimeError("GIR metadata exceeds decode ceiling")
    raw = zd(comp, raw_size)
    if H(raw) != expected_sha:
        raise RuntimeError("GIR metadata authentication")
    meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    if meta.get("v") != 1 or meta.get("engine") != "Geometry-IR-v1":
        raise RuntimeError("unsupported GIR metadata")
    if int(meta.get("max_dependency_depth", 99)) != 0:
        raise RuntimeError("GIR dependency depth exceeds policy")
    if float(meta.get("max_read_amplification", 999.0)) > 1.0:
        raise RuntimeError("GIR read amplification exceeds standalone policy")
    if int(meta.get("max_chunk", MAX_CHUNK + 1)) > MAX_CHUNK:
        raise RuntimeError("GIR chunk ceiling exceeds policy")
    if int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1)) > MAX_DECODE_UNIT:
        raise RuntimeError("GIR decode ceiling exceeds policy")
    if int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1)) > MAX_DECODER_MEMORY:
        raise RuntimeError("GIR memory ceiling exceeds policy")

    geometry = meta.get("geometry", {})
    if int(geometry.get("max_delimiter_candidates", G.MAX_DELIMITER_CANDIDATES + 1)) > G.MAX_DELIMITER_CANDIDATES:
        raise RuntimeError("GIR delimiter candidate budget exceeds policy")
    if int(geometry.get("max_delimiter_segments", G.MAX_DELIMITER_SEGMENTS + 1)) > G.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("GIR delimiter segment budget exceeds policy")
    hierarchy = meta.get("hierarchical_geometry", {})
    for key, maximum in HG.RESOURCE_LIMITS.items():
        value = hierarchy.get(key)
        if value is None:
            raise RuntimeError(f"GIR missing hierarchical resource declaration: {key}")
        # Screening/exact levels are identities rather than maxima. Resource-count fields may only tighten.
        if key in {"screen_level", "exact_level"}:
            if int(value) != int(maximum):
                raise RuntimeError(f"GIR hierarchical compressor identity mismatch: {key}")
        elif int(value) > int(maximum):
            raise RuntimeError(f"GIR hierarchical resource budget exceeds policy: {key}")

    leaves = list(meta.get("record_leaf_sha256", []))
    offsets = [int(value) for value in meta.get("record_rel_offsets", [])]
    if expected_count is not None and len(leaves) != expected_count:
        raise RuntimeError("GIR record-count mismatch")
    if len(offsets) != len(leaves) or _merkle_root(leaves) != expected_merkle:
        raise RuntimeError("GIR record table / Merkle mismatch")
    if offsets != sorted(offsets) or any(value < 0 for value in offsets):
        raise RuntimeError("GIR record offsets are not monotonic")
    return meta, offsets


def _open(path: Path):
    stream = path.open("rb")
    primary_error: Exception | None = None
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short GIR header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid GIR primary declaration")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short GIR primary metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle, count)
        if int(meta["max_decode_unit"]) != max_decode or int(meta["max_decoder_memory"]) != max_memory:
            raise RuntimeError("GIR header/meta resource mismatch")
        return stream, meta, HDR.size + mcs, offsets
    except Exception as exc:
        primary_error = exc

    try:
        stream.seek(-FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(FTR.size)
        if len(footer) != FTR.size:
            raise RuntimeError("short GIR footer")
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid GIR tail declaration")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size:
            raise RuntimeError("GIR tail metadata offset")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short GIR tail metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle)
        # Footnote: recovery still needs the bounded primary metadata length only to locate physical records;
        # the logical table itself comes from authenticated duplicate tail metadata.
        stream.seek(0)
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("cannot recover GIR record start")
        _, primary_mcs, _, _, _, _, _, _ = HDR.unpack(header)
        if primary_mcs > MAX_DECODE_UNIT:
            raise RuntimeError("GIR primary metadata declaration exceeds bound")
        return stream, meta, HDR.size + primary_mcs, offsets
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(
            f"no authenticated GIR metadata: primary={primary_error!r}; tail={tail_error!r}"
        ) from tail_error


def _materialize_files(path: Path) -> tuple[dict[str, bytes], dict]:
    stream, meta, record_start, offsets = _open(path)
    records: dict[int, bytes] = {}
    node_cache: dict[int, bytes] = {}
    nodes = list(meta["nodes"])
    leaves = list(meta["record_leaf_sha256"])

    def record(record_id: int) -> bytes:
        if record_id in records:
            return records[record_id]
        if not 0 <= record_id < len(offsets):
            raise RuntimeError("GIR record id out of range")
        stream.seek(record_start + offsets[record_id])
        header = stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short GIR physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("GIR physical record exceeds resource bound")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != leaves[record_id]:
            raise RuntimeError("GIR payload authentication")
        if codec == CODEC_RAW:
            raw = payload
        elif codec == CODEC_ZSTD:
            raw = zd(payload, usize)
        else:
            raise RuntimeError("unknown GIR physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("GIR physical integrity")
        records[record_id] = raw
        return raw

    def node(node_id: int) -> bytes:
        if node_id in node_cache:
            return node_cache[node_id]
        if not 0 <= node_id < len(nodes):
            raise RuntimeError("GIR node id out of range")
        desc = nodes[node_id]
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed GIR node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = record(int(record_id))
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            raw = L.lane_inverse(record(int(record_id)), int(width), int(logical_size))
        elif kind == "delimiter" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = G.delimiter_inverse(record(int(record_id)), int(logical_size))
        elif kind == "hierarchical" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = HG.hierarchy_inverse(record(int(record_id)), int(logical_size))
        else:
            raise RuntimeError("unknown or malformed GIR node kind")
        if len(raw) != int(logical_size) or len(raw) > MAX_CHUNK or H(raw) != expected:
            raise RuntimeError("GIR logical node integrity")
        node_cache[node_id] = raw
        return raw

    output: dict[str, bytes] = {}
    try:
        files = meta.get("files", {})
        if not isinstance(files, dict):
            raise RuntimeError("malformed GIR file table")
        for rel, desc in files.items():
            if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
                raise RuntimeError("malformed GIR file")
            node_ids, logical_size, expected = desc
            if not isinstance(node_ids, list):
                raise RuntimeError("malformed GIR file node list")
            data = b"".join(node(int(node_id)) for node_id in node_ids)
            if len(data) != int(logical_size) or H(data) != expected:
                raise RuntimeError("GIR logical file integrity")
            output[rel] = data
    finally:
        stream.close()
    return output, meta


def _safe_relpath(rel: str) -> PurePosixPath:
    if not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe GIR path syntax")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe GIR extraction path")
    return parsed


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        BASE.extract(archive, dst)
        return
    files, _ = _materialize_files(archive)
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    root = dst.resolve()
    for rel, data in files.items():
        parsed = _safe_relpath(rel)
        target = dst.joinpath(*parsed.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        resolved_parent = target.parent.resolve()
        if root != resolved_parent and root not in resolved_parent.parents:
            raise RuntimeError("GIR extraction escaped destination")
        target.write_bytes(data)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return BASE.strong_verify(archive)
    try:
        files, meta = _materialize_files(archive)
        digest = hashlib.sha256()
        for rel in sorted(files):
            rel_bytes = rel.encode("utf-8")
            data = files[rel]
            digest.update(len(rel_bytes).to_bytes(4, "little"))
            digest.update(rel_bytes)
            digest.update(len(data).to_bytes(8, "little"))
            digest.update(data)
        tree_sha = digest.hexdigest()
        expected = str(meta.get("tree_sha256", ""))
        return {
            "ok": tree_sha == expected,
            "tree_sha256": tree_sha,
            "expected_tree_sha256": expected,
            "files": len(files),
            "engine": "Geometry-IR-v1",
        }
    except Exception as exc:
        return {"ok": False, "error": repr(exc), "engine": "Geometry-IR-v1"}


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("root", type=Path)
    build_parser.add_argument("archive", type=Path)
    extract_parser = sub.add_parser("extract")
    extract_parser.add_argument("archive", type=Path)
    extract_parser.add_argument("destination", type=Path)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        print(json.dumps(build(args.root, args.archive), indent=2, sort_keys=True))
    elif args.command == "extract":
        extract(args.archive, args.destination)
    else:
        result = strong_verify(args.archive)
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result.get("ok"):
            raise SystemExit(1)


if __name__ == "__main__":
    _main()
