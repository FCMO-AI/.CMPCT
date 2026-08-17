"""CMPCT v0.30 Lattice oracle — measured lane transforms plus elastic direct packs.

This is a causal oracle, not yet a public format.  It starts from the real accepted v0.29 attempt-5
compiler, opens the research graph that compiler actually emits, and asks a narrow question: how many
stored bytes can be removed if *pure-direct* physical records are allowed to (a) expose fixed-width byte
lanes before the existing Zstd backend and (b) fuse up to the already-declared 8 MiB decode ceiling while
every directly addressable member remains at <=8x cold-read amplification?

The oracle intentionally charges transformed members 16 bytes each rather than claiming metadata is
free.  It also ignores metadata savings from removing physical records, so its reported candidate size is
conservative.  A later emitter must beat this accounting with exact serialized metadata before promotion.

Footnote: no filename extension, MIME guess, corpus name, or private identity participates in transform
admission.  Width 2/4/8/16 candidates are auditioned from bytes alone, and the real physical compressor
prices every retained group.  This keeps the mechanism useful even when the input's semantic type is
unknown or deliberately misleading.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
A5_PATH = HERE / "entropygraph_v029_residual_pack.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A5 = _load(A5_PATH, "cmpct_v030_lattice_attempt5")
A4 = A5.A4
P = A5.P
V028 = A5.V028
PH = A5.PH
H = A5.H

WIDTHS = (1, 2, 4, 8, 16)
MAX_PACK_BYTES = 8 * 1024 * 1024
MAX_READ_AMP = 8.0
TRANSFORM_DESCRIPTOR_CHARGE = 16
MAX_GROUP_EVALS = 768
MIN_TRANSFORM_BYTES = 256


def treehash(root: Path) -> str:
    return P.treehash(root)


def lane_transpose(raw: bytes, width: int) -> bytes:
    """Reorder byte positions lane-major without changing length."""
    if width == 1 or len(raw) < max(MIN_TRANSFORM_BYTES, width * 2):
        return raw
    cells = len(raw) // width
    main = cells * width
    if cells < 2:
        return raw
    return b"".join(raw[lane:main:width] for lane in range(width)) + raw[main:]


def lane_inverse(encoded: bytes, width: int, logical_size: int) -> bytes:
    """Inverse ``lane_transpose`` with an explicit logical length bound.

    Footnote: keeping the original logical length in the inverse API makes malformed future descriptors
    fail closed instead of letting Python slicing quietly manufacture a differently shaped byte stream.
    """
    if logical_size != len(encoded):
        raise RuntimeError("lane transform length changed")
    if width == 1 or logical_size < max(MIN_TRANSFORM_BYTES, width * 2):
        return encoded
    cells = logical_size // width
    main = cells * width
    out = bytearray(logical_size)
    cursor = 0
    for lane in range(width):
        lane_bytes = encoded[cursor : cursor + cells]
        if len(lane_bytes) != cells:
            raise RuntimeError("short lane during inverse transform")
        out[lane:main:width] = lane_bytes
        cursor += cells
    out[main:] = encoded[cursor:]
    return bytes(out)


def _compress_cost(raw: bytes) -> tuple[int, int, int]:
    codec, payload = P._compress_record(raw, 19)
    return PH.size + len(payload), codec, len(payload)


def _open_any_graph(path: Path):
    with path.open("rb") as stream:
        magic = stream.read(8)
    if magic == A5.MAG:
        return A5._open(path)
    return A4._open(path)


def _read_records(path: Path):
    stream, meta, record_start, offsets, _ = _open_any_graph(path)
    records = []
    try:
        for record_id, rel in enumerate(offsets):
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short Lattice source physical header")
            codec, usize, csize, crc, logical_sha = PH.unpack(header)
            payload = stream.read(csize)
            if len(payload) != csize:
                raise RuntimeError("short Lattice source payload")
            if H(payload) != meta["record_leaf_sha256"][record_id]:
                raise RuntimeError("Lattice source physical leaf mismatch")
            records.append((codec, usize, payload, crc, logical_sha))
    finally:
        stream.close()
    return meta, records


def _decode_record(record) -> bytes:
    codec, usize, payload, crc, logical_sha = record
    if usize > A5.MAX_DECODE_UNIT:
        raise RuntimeError("Lattice source record exceeds decode ceiling")
    if codec == A5.CODEC_RAW:
        raw = payload
    elif codec == A5.CODEC_ZSTD:
        raw = A5.zd(payload, usize)
    elif codec == A5.CODEC_PREFLATE:
        raw = V028._preflate_unpack(payload, usize)
    else:
        raise RuntimeError("unknown Lattice source physical codec")
    if len(raw) != usize:
        raise RuntimeError("Lattice source record size mismatch")
    if (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
        raise RuntimeError("Lattice source record integrity mismatch")
    return raw


def _record_users(meta: dict) -> tuple[dict[int, int], dict[int, list[tuple]]]:
    users: dict[int, int] = {}
    direct: dict[int, list[tuple]] = {}

    def use(record_id: int) -> None:
        users[record_id] = users.get(record_id, 0) + 1

    for node_id, desc in enumerate(meta["nodes"]):
        kind = desc[0]
        if kind == "direct":
            _, record_id, offset, length, expected = desc
            use(record_id)
            direct.setdefault(record_id, []).append(
                (node_id, int(offset), int(length), expected)
            )
        elif kind == "delta":
            use(desc[2])
        elif kind == "delta_pack":
            use(desc[2])
        elif kind == "mosaic":
            use(desc[2])
        elif kind == "pack_mosaic":
            use(desc[1])
        else:
            raise RuntimeError(f"unexpected Lattice source node kind: {kind}")

    for desc in meta["files"].values():
        if desc[0] == "preflate":
            use(desc[1])
        elif desc[0] != "nodes":
            raise RuntimeError(f"unexpected Lattice source file kind: {desc[0]}")
    return users, direct


def _pure_direct_groups(meta: dict, records: list[tuple]) -> list[dict]:
    users, direct = _record_users(meta)
    groups = []
    for record_id in sorted(direct):
        members = sorted(direct[record_id], key=lambda row: (row[1], row[0]))
        if users.get(record_id) != len(members):
            continue
        raw_record = _decode_record(records[record_id])
        cursor = 0
        decoded_members = []
        valid = True
        for node_id, offset, length, expected in members:
            if offset != cursor or length < 0 or offset + length > len(raw_record):
                valid = False
                break
            raw = raw_record[offset : offset + length]
            if H(raw) != expected:
                raise RuntimeError("pure-direct logical slice authentication failed")
            decoded_members.append({
                "node_id": node_id,
                "source_record_id": record_id,
                "length": length,
                "raw": raw,
                "expected": expected,
            })
            cursor += length
        if not valid or cursor != len(raw_record) or not decoded_members:
            continue
        groups.append({
            "source_record_ids": (record_id,),
            "members": decoded_members,
            "raw_bytes": len(raw_record),
            "source_physical_bytes": PH.size + len(records[record_id][2]),
        })
    return groups


def _member_variant(member: dict, width: int, cache: dict) -> bytes:
    key = (member["node_id"], width)
    value = cache.get(key)
    if value is None:
        value = lane_transpose(member["raw"], width)
        if lane_inverse(value, width, member["length"]) != member["raw"]:
            raise RuntimeError("Lattice lane transform failed exact inverse check")
        cache[key] = value
    return value


def _plan_patterns(members: list[dict], cache: dict) -> list[tuple[int, ...]]:
    patterns: list[tuple[int, ...]] = []
    patterns.append(tuple(1 for _ in members))
    for width in WIDTHS[1:]:
        patterns.append(tuple(
            width if member["length"] >= max(MIN_TRANSFORM_BYTES, width * 2) else 1
            for member in members
        ))

    # Footnote: the mixed candidate is not inferred from file type.  Each member independently auditions
    # the same reversible widths under the real compressor, then the *combined* record is priced again.
    # Independent choices are therefore only a proposal generator; they never bypass whole-record cost.
    mixed = []
    for member in members:
        best = None
        for width in WIDTHS:
            transformed = _member_variant(member, width, cache)
            cost, _, _ = _compress_cost(transformed)
            charged = cost + (TRANSFORM_DESCRIPTOR_CHARGE if width != 1 else 0)
            rank = (charged, width)
            if best is None or rank < best[0]:
                best = (rank, width)
        mixed.append(best[1])
    patterns.append(tuple(mixed))

    # Preserve order while deduplicating identical width assignments.
    return list(dict.fromkeys(patterns))


def _evaluate_group(group: dict, transform_cache: dict, eval_cache: dict) -> dict:
    key = tuple(group["source_record_ids"])
    cached = eval_cache.get(key)
    if cached is not None:
        return cached
    if len(eval_cache) >= MAX_GROUP_EVALS:
        raise RuntimeError("Lattice exact group-evaluation cap reached")

    members = group["members"]
    raw_bytes = sum(member["length"] for member in members)
    if raw_bytes > MAX_PACK_BYTES:
        raise RuntimeError("Lattice candidate exceeds 8 MiB decode ceiling")
    worst_amp = max(raw_bytes / max(1, member["length"]) for member in members)
    if worst_amp > MAX_READ_AMP + 1e-12:
        raise RuntimeError("Lattice candidate exceeds per-member locality")

    best = None
    for pattern in _plan_patterns(members, transform_cache):
        transformed_parts = [
            _member_variant(member, width, transform_cache)
            for member, width in zip(members, pattern)
        ]
        physical_raw = b"".join(transformed_parts)
        if len(physical_raw) != raw_bytes:
            raise RuntimeError("Lattice transform changed group byte length")
        physical_cost, codec, payload_bytes = _compress_cost(physical_raw)
        transformed_members = sum(width != 1 for width in pattern)
        descriptor_charge = transformed_members * TRANSFORM_DESCRIPTOR_CHARGE
        complete_cost = physical_cost + descriptor_charge
        row = {
            "source_record_ids": key,
            "members": members,
            "raw_bytes": raw_bytes,
            "pattern": pattern,
            "transformed_members": transformed_members,
            "physical_bytes": physical_cost,
            "descriptor_charge": descriptor_charge,
            "complete_cost": complete_cost,
            "codec": codec,
            "payload_bytes": payload_bytes,
            "worst_member_amp": worst_amp,
        }
        rank = (complete_cost, transformed_members, pattern)
        if best is None or rank < best[0]:
            best = (rank, row)
    result = best[1]
    eval_cache[key] = result
    return result


def _merge_group(left: dict, right: dict) -> dict | None:
    ids = tuple(sorted(left["source_record_ids"] + right["source_record_ids"]))
    # Keep member order deterministic by original physical record, then node id.  The oracle is already
    # testing a new transform; reordering members too would conflate two mechanisms in the same claim.
    members = sorted(
        left["members"] + right["members"],
        key=lambda member: (member["source_record_id"], member["node_id"]),
    )
    raw_bytes = sum(member["length"] for member in members)
    if raw_bytes > MAX_PACK_BYTES:
        return None
    worst_amp = max(raw_bytes / max(1, member["length"]) for member in members)
    if worst_amp > MAX_READ_AMP + 1e-12:
        return None
    return {
        "source_record_ids": ids,
        "members": members,
        "raw_bytes": raw_bytes,
        "source_physical_bytes": left["source_physical_bytes"] + right["source_physical_bytes"],
    }


def optimize_graph(archive: Path) -> dict:
    meta, records = _read_records(archive)
    source_groups = _pure_direct_groups(meta, records)
    transform_cache: dict[tuple[int, int], bytes] = {}
    eval_cache: dict[tuple[int, ...], dict] = {}

    active = []
    for source in source_groups:
        evaluated = _evaluate_group(source, transform_cache, eval_cache)
        active.append({**source, "best": evaluated})

    singleton_source = sum(group["source_physical_bytes"] for group in active)
    singleton_optimized = sum(group["best"]["complete_cost"] for group in active)
    singleton_saving = singleton_source - singleton_optimized
    fusions = []

    while len(active) > 1 and len(eval_cache) < MAX_GROUP_EVALS:
        best_pair = None
        for i, left in enumerate(active):
            for j in range(i + 1, len(active)):
                right = active[j]
                merged = _merge_group(left, right)
                if merged is None:
                    continue
                try:
                    evaluated = _evaluate_group(merged, transform_cache, eval_cache)
                except RuntimeError as exc:
                    if "evaluation cap" in str(exc):
                        break
                    raise
                current_cost = left["best"]["complete_cost"] + right["best"]["complete_cost"]
                saving = current_cost - evaluated["complete_cost"]
                if saving <= 0:
                    continue
                rank = (
                    saving,
                    -evaluated["worst_member_amp"],
                    -evaluated["raw_bytes"],
                    tuple(-record_id for record_id in evaluated["source_record_ids"]),
                )
                if best_pair is None or rank > best_pair[0]:
                    best_pair = (rank, i, j, merged, evaluated, saving)
            if len(eval_cache) >= MAX_GROUP_EVALS:
                break
        if best_pair is None:
            break
        _, i, j, merged, evaluated, saving = best_pair
        fused = {**merged, "best": evaluated}
        fusions.append({
            "source_record_ids": list(evaluated["source_record_ids"]),
            "saving_vs_current_bytes": saving,
            "raw_bytes": evaluated["raw_bytes"],
            "worst_member_amp": evaluated["worst_member_amp"],
            "pattern": list(evaluated["pattern"]),
            "transformed_members": evaluated["transformed_members"],
        })
        active[i] = fused
        del active[j]

    source_physical = sum(group["source_physical_bytes"] for group in active)
    optimized_physical = sum(group["best"]["complete_cost"] for group in active)
    saving = source_physical - optimized_physical
    transformed_members = sum(group["best"]["transformed_members"] for group in active)
    worst_amp = max((group["best"]["worst_member_amp"] for group in active), default=0.0)
    max_group = max((group["best"]["raw_bytes"] for group in active), default=0)

    return {
        "eligible_pure_direct_records": len(source_groups),
        "eligible_direct_members": sum(len(group["members"]) for group in source_groups),
        "source_physical_bytes": source_physical,
        "optimized_complete_bytes": optimized_physical,
        "saving_bytes": saving,
        "singleton_transform_saving_bytes": singleton_saving,
        "additional_fusion_saving_bytes": saving - singleton_saving,
        "final_groups": len(active),
        "fusions": fusions,
        "transformed_members": transformed_members,
        "max_group_bytes": max_group,
        "worst_member_amp": worst_amp,
        "exact_group_evaluations": len(eval_cache),
        "descriptor_charge_per_transformed_member": TRANSFORM_DESCRIPTOR_CHARGE,
        "max_pack_bytes": MAX_PACK_BYTES,
        "max_read_amp": MAX_READ_AMP,
        "groups": [
            {
                "source_record_ids": list(group["best"]["source_record_ids"]),
                "raw_bytes": group["best"]["raw_bytes"],
                "complete_cost": group["best"]["complete_cost"],
                "pattern": list(group["best"]["pattern"]),
                "transformed_members": group["best"]["transformed_members"],
                "worst_member_amp": group["best"]["worst_member_amp"],
            }
            for group in active
        ],
    }


def run(root: Path, work_root: Path, output: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    graph = work_root / "attempt5-graph.cmpct"
    accepted = work_root / "accepted-v029.cmpct"

    graph_started = time.perf_counter()
    graph_stats = A5.build_graph(root, graph)
    graph_create_s = time.perf_counter() - graph_started
    oracle_started = time.perf_counter()
    oracle = optimize_graph(graph)
    oracle_s = time.perf_counter() - oracle_started
    accepted_started = time.perf_counter()
    accepted_stats = A5.build(root, accepted)
    accepted_create_s = time.perf_counter() - accepted_started

    verified = A5.strong_verify(accepted)
    source_tree = treehash(root)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("accepted v0.29 strong verification failed during Lattice oracle")

    graph_bytes = graph.stat().st_size
    accepted_bytes = accepted.stat().st_size
    estimated = graph_bytes - oracle["saving_bytes"]
    result = {
        "schema": "cmpct-v030-lattice-oracle-v1",
        "source_tree_sha256": source_tree,
        "attempt5_graph_bytes": graph_bytes,
        "accepted_v029_bytes": accepted_bytes,
        "oracle_candidate_bytes_conservative": estimated,
        "saving_vs_attempt5_graph_bytes": oracle["saving_bytes"],
        "saving_vs_accepted_v029_bytes": accepted_bytes - estimated,
        "beats_accepted_v029": estimated < accepted_bytes,
        "oracle": oracle,
        "timing": {
            "attempt5_graph_create_s": graph_create_s,
            "oracle_s": oracle_s,
            "accepted_v029_create_s": accepted_create_s,
        },
        "accepted_build": {
            "selected": accepted_stats.get("selected"),
            "archive_bytes": accepted_stats.get("archive_bytes"),
            "attempt5_bytes": accepted_stats.get("mosaic_graph_bytes"),
            "v028_bytes": accepted_stats.get("v028_bytes"),
        },
        "claim_boundary": (
            "conservative detached physical oracle; transformed descriptors and exact emitter/reader are not yet promoted"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.work_root, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
