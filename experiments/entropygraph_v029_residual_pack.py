"""CMPCT attempt #5 — bounded Residual Program Packing compiler.

Attempt #4's Placement Compiler remains the semantic source of truth.  This module first builds its
complete CMPNX10 graph unchanged, then performs one independent physical optimization: several tiny
one-base delta programs that share the same **direct** base may occupy slices of one authenticated
physical residual record.

The logical graph does not deepen.  A ``delta_pack`` target still depends on exactly one direct base and
runs the same bounded ``delta_decode`` as an ordinary ``delta`` target.  Only the physical placement of
its reconstruction program changes.

Footnote: this file intentionally does not copy attempt #4's graph-construction policy.  Reusing the
validated Placement Compiler prevents a residual-packing experiment from silently changing mosaic
selection, direct-root packing, candidate discovery, or the attempt-4 negative controls while claiming
that any resulting byte movement came from recipe packing.
"""
from __future__ import annotations

import argparse
import binascii
import importlib.util
import json
import msgpack
import os
from pathlib import Path
import shutil
import statistics
import struct
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
A4_PATH = HERE / "entropygraph_v029_mosaic_strict.py"


def _load_attempt4():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_attempt4_for_residual", A4_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load attempt-4 strict Placement Compiler")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


A4 = _load_attempt4()
P = A4.IMPL
V028 = P.V028
H = P.H
zc = P.zc
zd = P.zd
PH = P.PH
CODEC_RAW = P.CODEC_RAW
CODEC_ZSTD = P.CODEC_ZSTD
CODEC_PREFLATE = P.CODEC_PREFLATE
MAX_CHUNK = P.MAX_CHUNK
MAX_DECODE_UNIT = P.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = P.MAX_DECODER_MEMORY
MAX_MOSAIC_BASES = P.MAX_MOSAIC_BASES
MAX_MOSAIC_SOURCE_INDEX = P.MAX_MOSAIC_SOURCE_INDEX
MAX_READ_AMP = P.MAX_READ_AMP

MAG = b"CMPNX11\0"
TAIL = b"CMN11T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")

RESIDUAL_LIMITS = (4, 8, 16, 32, 64, 128, 256)  # KiB; frozen by MOSAIC_V029_ATTEMPT5.md.
MAX_RESIDUAL_PACK = 256 * 1024
MAX_ADDITIONAL_RECIPE_AMP = 2.0
DESCRIPTOR_CHARGE_PER_MEMBER = 16
MIN_RESIDUAL_NET_SAVING = 128


def treehash(root: Path) -> str:
    return P.treehash(root)


def _compress_record(raw: bytes, level: int = 19):
    return P._compress_record(raw, level)


def _read_physical_records(path: Path):
    """Return attempt-4 metadata plus exact physical record bytes.

    Unchanged records retain their original compressed payload byte-for-byte.  This is important causal
    accounting: attempt #5 should not win because a second compressor invocation happened to emit
    different bytes for records unrelated to residual packing.
    """
    stream, meta, record_start, offsets, _ = A4._open(path)
    records = []
    try:
        for record_id, rel in enumerate(offsets):
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short attempt-4 physical header during residual compile")
            codec, usize, csize, crc, logical_sha = PH.unpack(header)
            payload = stream.read(csize)
            if len(payload) != csize:
                raise RuntimeError("short attempt-4 physical payload during residual compile")
            if H(payload) != meta["record_leaf_sha256"][record_id]:
                raise RuntimeError("attempt-4 physical leaf changed during residual compile")
            records.append((codec, usize, payload, crc, logical_sha))
    finally:
        stream.close()
    return meta, records


def _decode_record(record: tuple[int, int, bytes, int, bytes]) -> bytes:
    codec, usize, payload, crc, logical_sha = record
    if usize > MAX_DECODE_UNIT:
        raise RuntimeError("residual source record exceeds decode unit")
    if codec == CODEC_RAW:
        raw = payload
    elif codec == CODEC_ZSTD:
        raw = zd(payload, usize)
    elif codec == CODEC_PREFLATE:
        raw = V028._preflate_unpack(payload, usize)
    else:
        raise RuntimeError("unknown source physical codec")
    if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
        raise RuntimeError("source physical record integrity during residual compile")
    return raw


def _delta_programs(meta: dict, records: list[tuple[int, int, bytes, int, bytes]]) -> list[dict]:
    nodes = meta["nodes"]
    programs = []
    record_users: dict[int, int] = {}
    for desc in nodes:
        kind = desc[0]
        if kind == "direct":
            record_users[desc[1]] = record_users.get(desc[1], 0) + 1
        elif kind == "delta":
            record_users[desc[2]] = record_users.get(desc[2], 0) + 1
        elif kind == "mosaic":
            record_users[desc[2]] = record_users.get(desc[2], 0) + 1
        elif kind == "pack_mosaic":
            record_users[desc[1]] = record_users.get(desc[1], 0) + 1
        else:
            raise RuntimeError(f"unexpected attempt-4 node kind: {kind}")
    for file_desc in meta["files"].values():
        if file_desc[0] == "preflate":
            record_users[file_desc[1]] = record_users.get(file_desc[1], 0) + 1

    for target_id, desc in enumerate(nodes):
        if desc[0] != "delta":
            continue
        _, base_id, record_id, target_len, expected = desc
        if not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct":
            raise RuntimeError("attempt-4 delta base is not direct")
        # Footnote: the compiler removes a dedicated physical record only when that record belongs to
        # exactly this delta node.  Shared records must never be deleted by an optimization that assumes
        # one logical owner.
        if record_users.get(record_id) != 1:
            continue
        raw_delta = _decode_record(records[record_id])
        programs.append({
            "target_id": target_id,
            "base_id": base_id,
            "record_id": record_id,
            "target_len": int(target_len),
            "expected": expected,
            "raw_delta": raw_delta,
            "raw_delta_bytes": len(raw_delta),
            "separate_physical_bytes": PH.size + len(records[record_id][2]),
        })
    return programs


def _pack_group(programs: list[dict]) -> dict:
    raw = b"".join(row["raw_delta"] for row in programs)
    codec, payload = _compress_record(raw, 12)
    separate = sum(row["separate_physical_bytes"] for row in programs)
    packed_physical = PH.size + len(payload)
    descriptor_charge = DESCRIPTOR_CHARGE_PER_MEMBER * len(programs)
    net = separate - packed_physical - descriptor_charge
    max_amp = max((len(raw) / max(1, row["target_len"]) for row in programs), default=0.0)
    return {
        "base_id": programs[0]["base_id"],
        "programs": programs,
        "raw": raw,
        "codec": codec,
        "payload": payload,
        "separate_physical_bytes": separate,
        "packed_physical_bytes": packed_physical,
        "descriptor_charge": descriptor_charge,
        "net": net,
        "max_amp": max_amp,
    }


def _plan(programs: list[dict], limit: int) -> dict:
    groups = []
    by_base: dict[int, list[dict]] = {}
    for row in programs:
        by_base.setdefault(row["base_id"], []).append(row)
    for base_id in sorted(by_base):
        current = []
        current_raw = 0
        for row in sorted(by_base[base_id], key=lambda item: item["target_id"]):
            candidate_raw = current_raw + row["raw_delta_bytes"]
            candidate = current + [row]
            candidate_amp = max(candidate_raw / max(1, member["target_len"]) for member in candidate)
            if current and (candidate_raw > limit or candidate_amp > MAX_ADDITIONAL_RECIPE_AMP):
                groups.append(_pack_group(current))
                current = [row]
                current_raw = row["raw_delta_bytes"]
            else:
                current = candidate
                current_raw = candidate_raw
        if current:
            groups.append(_pack_group(current))
    eligible = [
        group for group in groups
        if len(group["programs"]) >= 2
        and len(group["raw"]) <= MAX_RESIDUAL_PACK
        and group["max_amp"] <= MAX_ADDITIONAL_RECIPE_AMP
        and group["net"] >= MIN_RESIDUAL_NET_SAVING
    ]
    return {
        "limit": limit,
        "groups": groups,
        "eligible": eligible,
        "net": sum(group["net"] for group in eligible),
        "max_amp": max((group["max_amp"] for group in eligible), default=0.0),
    }


def _choose_plan(programs: list[dict]) -> dict:
    plans = [_plan(programs, kib * 1024) for kib in RESIDUAL_LIMITS]
    return min(plans, key=lambda row: (-row["net"], row["max_amp"], row["limit"]))


def _remap_node_desc(desc: list, record_map: dict[int, int]) -> list:
    kind = desc[0]
    if kind == "direct":
        return [kind, record_map[desc[1]], *desc[2:]]
    if kind == "delta":
        return [kind, desc[1], record_map[desc[2]], *desc[3:]]
    if kind == "mosaic":
        return [kind, desc[1], record_map[desc[2]], *desc[3:]]
    if kind == "pack_mosaic":
        return [kind, record_map[desc[1]], *desc[2:]]
    raise RuntimeError(f"unexpected node kind during record remap: {kind}")


def _compile_residual(placement: Path, out: Path) -> dict:
    started = time.perf_counter()
    meta, old_records = _read_physical_records(placement)
    programs = _delta_programs(meta, old_records)
    plan = _choose_plan(programs)
    selected_groups = plan["eligible"]

    selected_by_target: dict[int, tuple[int, int, int]] = {}
    removed_records: set[int] = set()
    for group_index, group in enumerate(selected_groups):
        offset = 0
        for row in group["programs"]:
            selected_by_target[row["target_id"]] = (group_index, offset, row["raw_delta_bytes"])
            removed_records.add(row["record_id"])
            offset += row["raw_delta_bytes"]

    if not selected_groups:
        shutil.copyfile(placement, out)
        return {
            "create_s": time.perf_counter() - started,
            "selected": False,
            "source_graph_bytes": placement.stat().st_size,
            "graph_bytes": out.stat().st_size,
            "delta_programs": len(programs),
            "residual_pack_records": 0,
            "residual_packed_delta_nodes": 0,
            "residual_raw_bytes": 0,
            "residual_estimated_net_saving": 0,
            "max_additional_recipe_read_amplification": 0.0,
            "residual_pack_limit": plan["limit"],
        }

    new_records = []
    record_map: dict[int, int] = {}
    for old_id, record in enumerate(old_records):
        if old_id in removed_records:
            continue
        record_map[old_id] = len(new_records)
        new_records.append(record)

    residual_record_ids = []
    for group in selected_groups:
        raw = group["raw"]
        payload = group["payload"]
        record_id = len(new_records)
        residual_record_ids.append(record_id)
        new_records.append((
            group["codec"], len(raw), payload,
            binascii.crc32(raw) & 0xFFFFFFFF, H(raw),
        ))

    new_nodes = []
    for target_id, desc in enumerate(meta["nodes"]):
        packed = selected_by_target.get(target_id)
        if packed is None:
            new_nodes.append(_remap_node_desc(desc, record_map))
            continue
        if desc[0] != "delta":
            raise RuntimeError("residual target stopped being an ordinary delta")
        group_index, recipe_offset, recipe_length = packed
        _, base_id, _, target_len, expected = desc
        new_nodes.append([
            "delta_pack", base_id, residual_record_ids[group_index], recipe_offset, recipe_length,
            target_len, expected,
        ])

    new_files = {}
    for rel, desc in meta["files"].items():
        if desc[0] == "preflate":
            new_files[rel] = ["preflate", record_map[desc[1]], *desc[2:]]
        elif desc[0] == "nodes":
            new_files[rel] = list(desc)
        else:
            raise RuntimeError("unexpected file descriptor during residual compile")

    leaves = [H(record[2]) for record in new_records]
    merkle = V028._merkle_root(leaves)
    rel_offsets = []
    cursor = 0
    for _, _, payload, _, _ in new_records:
        rel_offsets.append(cursor)
        cursor += PH.size + len(payload)

    new_meta = dict(meta)
    new_meta.update({
        "engine": "EntropyGraph-II-Mosaic-Placement-ResidualPack-v5",
        "files": new_files,
        "nodes": new_nodes,
        "record_rel_offsets": rel_offsets,
        "record_leaf_sha256": leaves,
        "max_residual_pack_bytes": MAX_RESIDUAL_PACK,
        "max_additional_recipe_read_amplification": MAX_ADDITIONAL_RECIPE_AMP,
        "residual_pack_records": len(selected_groups),
        "residual_packed_delta_nodes": len(selected_by_target),
    })
    meta_raw = msgpack.packb(new_meta, use_bin_type=True)
    meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(
            MAG, len(meta_comp), len(meta_raw), len(new_records), MAX_DECODE_UNIT,
            MAX_DECODER_MEMORY, H(meta_raw), merkle,
        ))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in new_records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha))
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))

    return {
        "create_s": time.perf_counter() - started,
        "selected": out.stat().st_size < placement.stat().st_size,
        "source_graph_bytes": placement.stat().st_size,
        "graph_bytes": out.stat().st_size,
        "delta_programs": len(programs),
        "residual_pack_records": len(selected_groups),
        "residual_packed_delta_nodes": len(selected_by_target),
        "residual_raw_bytes": sum(len(group["raw"]) for group in selected_groups),
        "residual_estimated_net_saving": plan["net"],
        "max_additional_recipe_read_amplification": plan["max_amp"],
        "residual_pack_limit": plan["limit"],
    }


def _open(path: Path):
    stream = path.open("rb")

    def decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                    expected_count: int | None = None, declared_decode: int | None = None,
                    declared_memory: int | None = None):
        raw = zd(comp, raw_size)
        if H(raw) != expected_sha:
            raise RuntimeError("residual metadata authentication")
        meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) > 1:
            raise RuntimeError("unsupported residual metadata")
        if int(meta.get("max_mosaic_bases", MAX_MOSAIC_BASES + 1)) > MAX_MOSAIC_BASES:
            raise RuntimeError("residual mosaic base count exceeds policy")
        if int(meta.get("max_mosaic_source_index", MAX_MOSAIC_SOURCE_INDEX + 1)) > MAX_MOSAIC_SOURCE_INDEX:
            raise RuntimeError("residual mosaic source bound exceeds policy")
        if int(meta.get("max_residual_pack_bytes", MAX_RESIDUAL_PACK + 1)) > MAX_RESIDUAL_PACK:
            raise RuntimeError("residual pack size exceeds policy")
        if float(meta.get("max_additional_recipe_read_amplification", MAX_ADDITIONAL_RECIPE_AMP + 1)) > MAX_ADDITIONAL_RECIPE_AMP:
            raise RuntimeError("residual recipe amplification exceeds policy")
        meta_decode = int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1))
        meta_memory = int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1))
        if meta_decode > MAX_DECODE_UNIT or (declared_decode is not None and meta_decode != declared_decode):
            raise RuntimeError("residual decode ceiling exceeds policy")
        if meta_memory > MAX_DECODER_MEMORY or (declared_memory is not None and meta_memory != declared_memory):
            raise RuntimeError("residual memory ceiling exceeds policy")
        leaves = list(meta.get("record_leaf_sha256", []))
        if expected_count is not None and len(leaves) != expected_count:
            raise RuntimeError("residual record-count mismatch")
        if V028._merkle_root(leaves) != expected_merkle:
            raise RuntimeError("residual Merkle mismatch")
        offsets = list(meta.get("record_rel_offsets", []))
        if len(offsets) != len(leaves):
            raise RuntimeError("residual record table mismatch")
        return meta, offsets

    primary_error = None
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short residual header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG:
            raise RuntimeError("not residual-pack research archive")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short primary residual metadata")
        meta, offsets = decode_meta(comp, mus, meta_sha, merkle, count, max_decode, max_memory)
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as exc:
        primary_error = exc

    try:
        stream.seek(-FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(FTR.size)
        if len(footer) != FTR.size:
            raise RuntimeError("short residual footer")
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL:
            raise RuntimeError("residual tail magic")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size:
            raise RuntimeError("residual tail metadata offset")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short residual tail metadata")
        meta, offsets = decode_meta(comp, mus, meta_sha, merkle)
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(
            f"no authenticated residual metadata: primary={primary_error!r}; tail={tail_error!r}"
        ) from tail_error


def _extract_residual(path: Path, dst: Path) -> None:
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    stream, meta, record_start, offsets, _ = _open(path)
    record_cache: dict[int, bytes] = {}
    node_cache: dict[int, bytes] = {}
    nodes = meta["nodes"]

    def record(record_id: int) -> bytes:
        if record_id in record_cache:
            return record_cache[record_id]
        if not 0 <= record_id < len(offsets):
            raise RuntimeError("residual record id out of range")
        stream.seek(record_start + offsets[record_id])
        header = stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short residual physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT:
            raise RuntimeError("residual physical record exceeds decode unit")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
            raise RuntimeError("residual physical Merkle leaf mismatch")
        if codec == CODEC_RAW:
            raw = payload
        elif codec == CODEC_ZSTD:
            raw = zd(payload, usize)
        elif codec == CODEC_PREFLATE:
            raw = V028._preflate_unpack(payload, usize)
        else:
            raise RuntimeError("unknown residual physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("residual physical record integrity")
        record_cache[record_id] = raw
        return raw

    def node(node_id: int) -> bytes:
        if node_id in node_cache:
            return node_cache[node_id]
        if not 0 <= node_id < len(nodes):
            raise RuntimeError("residual node id out of range")
        desc = nodes[node_id]
        kind = desc[0]
        if kind == "direct":
            _, record_id, offset, length, expected = desc
            pack = record(record_id)
            if offset > len(pack) or length > len(pack) - offset:
                raise RuntimeError("residual direct slice bounds")
            raw = pack[offset : offset + length]
        elif kind == "delta":
            _, base_id, record_id, length, expected = desc
            if nodes[base_id][0] != "direct":
                raise RuntimeError("residual delta dependency depth")
            raw = P.delta_decode(node(base_id), record(record_id), expected_size=length, max_output=MAX_CHUNK)
        elif kind == "delta_pack":
            _, base_id, record_id, recipe_offset, recipe_len, length, expected = desc
            if not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct":
                raise RuntimeError("residual packed-delta dependency depth")
            pack = record(record_id)
            if recipe_offset > len(pack) or recipe_len > len(pack) - recipe_offset:
                raise RuntimeError("residual recipe slice bounds")
            if len(pack) > MAX_RESIDUAL_PACK:
                raise RuntimeError("residual recipe record exceeds pack policy")
            if len(pack) / max(1, int(length)) > MAX_ADDITIONAL_RECIPE_AMP:
                raise RuntimeError("residual recipe member exceeds over-read policy")
            recipe = pack[recipe_offset : recipe_offset + recipe_len]
            raw = P.delta_decode(node(base_id), recipe, expected_size=length, max_output=MAX_CHUNK)
        elif kind == "mosaic":
            _, base_ids, record_id, length, expected = desc
            if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= MAX_MOSAIC_BASES:
                raise RuntimeError("residual mosaic base list bounds")
            if len(set(base_ids)) != len(base_ids) or any(not isinstance(base_id, int) for base_id in base_ids):
                raise RuntimeError("invalid residual mosaic base list")
            if any(not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct" for base_id in base_ids):
                raise RuntimeError("residual mosaic dependency depth")
            raw = P.mosaic_delta_decode(
                [node(base_id) for base_id in base_ids], record(record_id),
                expected_size=length, max_bases=MAX_MOSAIC_BASES,
                max_source_bytes=MAX_MOSAIC_SOURCE_INDEX, max_output=MAX_CHUNK,
            )
        elif kind == "pack_mosaic":
            _, record_id, offset, recipe_len, base_ids, length, expected = desc
            if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= MAX_MOSAIC_BASES:
                raise RuntimeError("residual pack-mosaic base list bounds")
            if len(set(base_ids)) != len(base_ids) or any(not isinstance(base_id, int) for base_id in base_ids):
                raise RuntimeError("invalid residual pack-mosaic base list")
            if any(not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct" for base_id in base_ids):
                raise RuntimeError("residual pack-mosaic dependency depth")
            pack = record(record_id)
            if offset > len(pack) or recipe_len > len(pack) - offset:
                raise RuntimeError("residual pack-mosaic recipe bounds")
            recipe = pack[offset : offset + recipe_len]
            raw = P.mosaic_delta_decode(
                [node(base_id) for base_id in base_ids], recipe,
                expected_size=length, max_bases=MAX_MOSAIC_BASES,
                max_source_bytes=MAX_MOSAIC_SOURCE_INDEX, max_output=MAX_CHUNK,
            )
        else:
            raise RuntimeError("unknown residual node description")
        if H(raw) != expected:
            raise RuntimeError("residual node SHA-256 mismatch")
        node_cache[node_id] = raw
        return raw

    try:
        for rel, desc in sorted(meta["files"].items()):
            if desc[0] == "preflate":
                raw = record(desc[1]); expected_size = desc[2]; expected = desc[3]
            elif desc[0] == "nodes":
                raw = b"".join(node(node_id) for node_id in desc[1]); expected_size = desc[2]; expected = desc[3]
            else:
                raise RuntimeError("unknown residual file description")
            if len(raw) != expected_size or H(raw) != expected:
                raise RuntimeError("residual file reconstruction mismatch")
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    finally:
        stream.close()


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic == MAG:
        _extract_residual(archive, dst)
    else:
        A4.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return A4.strong_verify(archive)
    stream, meta, _, offsets, merkle = _open(archive)
    stream.close()
    with tempfile.TemporaryDirectory(prefix="cmpct-residual-verify-") as td:
        dst = Path(td)
        _extract_residual(archive, dst)
        got = treehash(dst)
    if got != meta["tree_sha256"]:
        raise RuntimeError("residual logical tree root mismatch")
    return {
        "ok": True,
        "tree_sha256": got,
        "merkle_root": merkle.hex(),
        "records": len(offsets),
        "max_decode_unit": meta["max_decode_unit"],
        "max_decoder_memory": meta["max_decoder_memory"],
        "max_mosaic_bases": meta["max_mosaic_bases"],
        "max_residual_pack_bytes": meta["max_residual_pack_bytes"],
        "max_additional_recipe_read_amplification": meta["max_additional_recipe_read_amplification"],
    }


def _build_graph(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-residual-graph-") as td:
        temp = Path(td)
        placement = temp / "placement.cmpct"
        residual = temp / "residual.cmpct"
        placement_stats = A4.build_graph(root, placement)
        residual_stats = _compile_residual(placement, residual)
        if residual.stat().st_size < placement.stat().st_size:
            shutil.copyfile(residual, out)
            residual_selected = True
        else:
            shutil.copyfile(placement, out)
            residual_selected = False

    stats = dict(placement_stats)
    stats["create_s"] = time.perf_counter() - started
    stats["graph_bytes"] = out.stat().st_size
    stats["residual_selected"] = residual_selected
    stats["residual_pack_records"] = residual_stats["residual_pack_records"] if residual_selected else 0
    stats["residual_packed_delta_nodes"] = residual_stats["residual_packed_delta_nodes"] if residual_selected else 0
    stats["residual_raw_bytes"] = residual_stats["residual_raw_bytes"] if residual_selected else 0
    stats["residual_estimated_net_saving"] = residual_stats["residual_estimated_net_saving"] if residual_selected else 0
    stats["max_additional_recipe_read_amplification"] = (
        residual_stats["max_additional_recipe_read_amplification"] if residual_selected else 0.0
    )
    stats["residual_pack_limit"] = residual_stats["residual_pack_limit"]
    if residual_selected:
        stats["single_delta_nodes"] = max(
            0, int(stats.get("single_delta_nodes", 0)) - int(residual_stats["residual_packed_delta_nodes"])
        )
        stats["mosaic_estimated_record_savings"] = int(stats.get("mosaic_estimated_record_savings", 0)) + int(
            residual_stats["residual_estimated_net_saving"]
        )
    return stats


def build_graph(root: Path, out: Path) -> dict:
    return _build_graph(root, out)


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-residual-portfolio-") as td:
        temp = Path(td)
        v028_path = temp / "v028.cmpct"
        graph_path = temp / "candidate.cmpct"
        v028_stats = V028.build(root, v028_path)
        graph_stats = _build_graph(root, graph_path)
        if graph_path.stat().st_size < v028_path.stat().st_size:
            shutil.copyfile(graph_path, out)
            selected = "mosaic"
        else:
            shutil.copyfile(v028_path, out)
            selected = "v028-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v028_bytes": v028_path.stat().st_size,
            "mosaic_graph_bytes": graph_path.stat().st_size,
            "smaller_than_v028_pct": (
                (v028_path.stat().st_size - out.stat().st_size) / max(1, v028_path.stat().st_size) * 100.0
            ),
            "portfolio_create_s": time.perf_counter() - started,
            "v028": v028_stats,
            "mosaic": graph_stats,
        }


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter(); strong_verify(out); samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT attempt-5 Residual Program Packing engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("bench"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
