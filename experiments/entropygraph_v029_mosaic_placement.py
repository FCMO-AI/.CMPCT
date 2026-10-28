"""CMPCT multi-root Mosaic Placement Compiler — full-artifact research attempt #4.

This experimental engine adds three physical embodiments to the validated bounded mosaic primitive:
pack-local semantic recipes, locality-aware direct-root co-packs, and target-relative small-mosaic
upgrades. It remains outside canonical revision-24 grammar and is evaluated only through the unchanged
v0.29 research gate.

Footnote: attempts #1–#3 remain separate executable files. This module does not rewrite their failed
mechanisms; it consumes their preserved evidence to change physical placement economics.
"""
from __future__ import annotations

import binascii
import importlib.util
from itertools import combinations
import msgpack
import os
from pathlib import Path
import shutil
import statistics
import struct
import sys
import tempfile
import time

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import (
    choose_central_bases,
    delta_decode,
    delta_encode,
    fastcdc,
    lsh_candidates,
    similarity_order,
    similarity_sketch,
)

HERE = Path(__file__).resolve().parent
A3_PATH = HERE / "entropygraph_v029_mosaic_packaware.py"


def _load_attempt3():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_attempt3_for_placement", A3_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load mosaic attempt-3 engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


A3 = _load_attempt3()
A2 = A3.A2
PARENT = A3.PARENT
V028 = A3.V028
H = A3.H
zc = A3.zc
zd = PARENT.zd

MAG = b"CMPNX10\0"
TAIL = b"CMN10T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")
PH = A3.PH
CODEC_RAW = PARENT.CODEC_RAW
CODEC_ZSTD = PARENT.CODEC_ZSTD
CODEC_PREFLATE = A3.CODEC_PREFLATE
MAX_CHUNK = A3.MAX_CHUNK
MAX_DECODE_UNIT = A3.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = A3.MAX_DECODER_MEMORY
MIN_DELTA = A3.MIN_DELTA
PREFLATE_EXTS = A3.PREFLATE_EXTS
MAX_MOSAIC_BASES = A3.MAX_MOSAIC_BASES
MAX_MOSAIC_SOURCE_INDEX = A3.MAX_MOSAIC_SOURCE_INDEX
MAX_READ_AMP = A3.MAX_READ_AMP
MOSAIC_METADATA_BASE = A3.MOSAIC_METADATA_BASE
MOSAIC_METADATA_PER_ROOT = A3.MOSAIC_METADATA_PER_ROOT
MAX_NOMINATED_ROOTS = 8
MAX_SUBSET_TRIALS = 154
MAX_DEDICATED_COPACK = 2 * 1024 * 1024
PACK_LOCAL_MIN_NET = 64


def treehash(root: Path) -> str:
    return PARENT.treehash(root)


def _compress_record(raw: bytes, level: int = 19):
    return PARENT._compress_record(raw, level)


def _direct_cost(raw: bytes) -> int:
    return PARENT._direct_cost(raw)


def _contribution_floor(target_size: int) -> int:
    # Small targets cannot satisfy the historical absolute 4 KiB mosaic floor. Keep a narrow relative
    # path for >=1 KiB targets without changing inherited v0.28 single-delta policy.
    if target_size < 1024:
        return target_size + 1
    if target_size < 32 * 1024:
        return max(256, target_size // 8)
    return max(4096, target_size // 20)


def _position_independent_candidates(sketches, nodes: list[bytes]):
    return A2._position_independent_candidates(sketches, nodes)


def _compact_mosaic(base_ids: tuple[int, ...] | list[int], target_id: int, nodes: list[bytes]):
    ids = list(base_ids)
    if len(ids) < 2 or len(ids) > MAX_MOSAIC_BASES:
        return None
    for _ in range(MAX_MOSAIC_BASES):
        if sum(len(nodes[node_id]) for node_id in ids) > MAX_MOSAIC_SOURCE_INDEX:
            return None
        result = mosaic_delta_encode(
            [nodes[node_id] for node_id in ids], nodes[target_id],
            block=64, max_bases=MAX_MOSAIC_BASES,
            max_source_index=MAX_MOSAIC_SOURCE_INDEX, max_matches_per_key=16,
        )
        used = [ids[slot] for slot in used_base_slots(result.stats)]
        if len(used) < 2:
            return None
        if used != ids:
            ids = used
            continue
        restored = mosaic_delta_decode(
            [nodes[node_id] for node_id in ids], result.payload,
            expected_size=len(nodes[target_id]), max_bases=MAX_MOSAIC_BASES,
            max_source_bytes=MAX_MOSAIC_SOURCE_INDEX, max_output=MAX_CHUNK,
        )
        if restored != nodes[target_id]:
            raise RuntimeError("placement mosaic reconstruction mismatch")
        codec, payload = _compress_record(result.payload, 12)
        cost = PH.size + len(payload) + MOSAIC_METADATA_BASE + MOSAIC_METADATA_PER_ROOT * len(ids)
        return {
            "base_ids": ids,
            "raw_delta": result.payload,
            "codec": codec,
            "payload": payload,
            "cost": cost,
            "copied": result.stats.copied_bytes,
            "literal": result.stats.literal_bytes,
        }
    raise RuntimeError("placement mosaic compaction did not converge")


def _bounded_best_mosaic(target_id: int, rows: list[tuple[int, int, int, int]],
                         allowed_bases: set[int], nodes: list[bytes]):
    # Rank nominated roots by exact copied information. The subset tournament then lets stored bytes,
    # not the ranking heuristic, choose the legal 2–4-root explanation.
    ranked = [row for row in rows if row[0] in allowed_bases]
    ranked.sort(key=lambda row: (-row[2], -row[3], -row[1], row[0]))
    pool = [row[0] for row in ranked[:MAX_NOMINATED_ROOTS]]
    best = None
    trials = 0
    for width in range(2, min(MAX_MOSAIC_BASES, len(pool)) + 1):
        for combo in combinations(pool, width):
            trials += 1
            if trials > MAX_SUBSET_TRIALS:
                break
            candidate = _compact_mosaic(combo, target_id, nodes)
            if candidate is None:
                continue
            metric = (candidate["cost"], -candidate["copied"], tuple(candidate["base_ids"]))
            if best is None or metric < best[0]:
                best = (metric, candidate)
        if trials > MAX_SUBSET_TRIALS:
            break
    return (best[1] if best else None), trials


def _pack_payload(group: list[int], nodes: list[bytes], replacements: dict[int, dict]) -> bytes:
    return b"".join(
        replacements[node_id]["raw_delta"] if node_id in replacements else nodes[node_id]
        for node_id in group
    )


def _group_cost(group: list[int], nodes: list[bytes], replacements: dict[int, dict]) -> int:
    raw = _pack_payload(group, nodes, replacements)
    _, payload = _compress_record(raw)
    return PH.size + len(payload)


def _groups_cost(groups: list[list[int]], nodes: list[bytes], replacements: dict[int, dict]) -> int:
    return sum(_group_cost(group, nodes, replacements) for group in groups if group)


def _node_group(groups: list[list[int]]) -> dict[int, int]:
    out = {}
    for group_id, group in enumerate(groups):
        for node_id in group:
            out[node_id] = group_id
    return out


def _max_group_amp(groups: list[list[int]], nodes: list[bytes], replacements: dict[int, dict]) -> float:
    worst = 0.0
    for group in groups:
        decoded = sum(
            len(replacements[node_id]["raw_delta"]) if node_id in replacements else len(nodes[node_id])
            for node_id in group
        )
        for node_id in group:
            if node_id in replacements:
                continue
            worst = max(worst, decoded / max(1, len(nodes[node_id])))
    return worst


def _mosaic_read_amp(candidate: dict, groups: list[list[int]], nodes: list[bytes], target_id: int) -> float:
    lookup = _node_group(groups)
    decoded_by_group: dict[int, int] = {}
    for base_id in candidate["base_ids"]:
        group_id = lookup[base_id]
        if group_id not in decoded_by_group:
            decoded_by_group[group_id] = sum(len(nodes[node_id]) for node_id in groups[group_id])
    return (sum(decoded_by_group.values()) + len(candidate["raw_delta"])) / max(1, len(nodes[target_id]))


def _copack_groups(groups: list[list[int]], target_id: int, base_ids: list[int], sketches, nodes: list[bytes]):
    selected = set(base_ids)
    result = []
    for group in groups:
        kept = [node_id for node_id in group if node_id != target_id and node_id not in selected]
        if kept:
            result.append(kept)
    dedicated = similarity_order(sketches, list(base_ids))
    if sum(len(nodes[node_id]) for node_id in dedicated) > MAX_DEDICATED_COPACK:
        return None
    result.append(dedicated)
    return result


def _build_graph(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]

    preflate_files: dict[int, bytes] = {}
    normal_files: list[int] = []
    preflate_attempts = preflate_wins = 0
    for file_id, (path, raw) in enumerate(zip(files, raws)):
        packed = None
        if path.suffix.lower() in PREFLATE_EXTS and 4096 <= len(raw) <= MAX_DECODE_UNIT:
            preflate_attempts += 1
            packed = V028._preflate_pack(raw, path.suffix)
        direct = _direct_cost(raw)
        if packed is not None and PH.size + len(packed) + 24 < direct:
            preflate_files[file_id] = packed
            preflate_wins += 1
        else:
            normal_files.append(file_id)

    nodes: list[bytes] = []
    node_hash_to_id: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    exact_aliases = 0
    for file_id in normal_files:
        raw = raws[file_id]
        chunks = (
            fastcdc(raw, min_size=32 * 1024, avg_size=128 * 1024, max_size=MAX_CHUNK)
            if len(raw) > MAX_CHUNK
            else [type("C", (), {"offset": 0, "length": len(raw)})()]
        )
        refs = []
        for chunk in chunks:
            part = raw[chunk.offset : chunk.offset + chunk.length]
            hh = H(part)
            node_id = node_hash_to_id.get(hh)
            if node_id is not None and nodes[node_id] == part:
                exact_aliases += 1
            else:
                node_id = len(nodes)
                node_hash_to_id[hh] = node_id
                nodes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs

    sketches = [similarity_sketch(raw) for raw in nodes]
    inherited_edges = lsh_candidates(sketches, max_bucket=48, max_candidates=8)
    inherited_pairs = {(edge.target, edge.base): edge.shared_features for edge in inherited_edges}
    broad_pairs = dict(inherited_pairs)
    for target_id, base_id, shared in _position_independent_candidates(sketches, nodes):
        broad_pairs[(target_id, base_id)] = max(shared, broad_pairs.get((target_id, base_id), 0))

    direct_costs = [_direct_cost(raw) for raw in nodes]
    measured = []
    edge_payloads: dict[tuple[int, int], tuple[bytes, dict]] = {}
    per_target: dict[int, list[tuple[int, int, int, int]]] = {}
    auditions = inherited_auditions = discovery_auditions = partial_roots = 0
    for (target_id, base_id), shared in sorted(broad_pairs.items()):
        target = nodes[target_id]; base = nodes[base_id]
        if min(len(target), len(base)) < MIN_DELTA:
            continue
        auditions += 1
        if (target_id, base_id) in inherited_pairs:
            inherited_auditions += 1
        else:
            discovery_auditions += 1
        result = delta_encode(base, target, block=64, max_base_index=MAX_CHUNK)
        codec, payload = _compress_record(result.payload, 12)
        stored = PH.size + len(payload) + 24
        saving = direct_costs[target_id] - stored
        stats = {
            "saving": saving,
            "stored_cost": stored,
            "copied": result.stats.copied_bytes,
            "literal": result.stats.literal_bytes,
            "shared_features": shared,
        }
        edge_payloads[(target_id, base_id)] = (result.payload, stats)
        if result.stats.copied_bytes >= _contribution_floor(len(target)):
            per_target.setdefault(target_id, []).append((base_id, saving, result.stats.copied_bytes, shared))
            if saving <= 0:
                partial_roots += 1
        # Inherited central assignment is deliberately unchanged by broader mosaic discovery.
        if (
            (target_id, base_id) in inherited_pairs
            and saving >= max(128, direct_costs[target_id] // 50)
            and result.stats.copied_bytes >= len(target) // 4
        ):
            measured.append((target_id, base_id, saving))

    assignment = choose_central_bases(len(nodes), measured)
    delta_nodes = set(assignment)
    root_ids = [node_id for node_id in range(len(nodes)) if node_id not in delta_nodes]
    used_as_single_base = set(assignment.values())
    (_, baseline_pack_amp, baseline_pack_limit, baseline_groups), pack_trials = V028._choose_pack_plan(
        nodes, sketches, root_ids
    )
    groups = [list(group) for group in baseline_groups]
    replacements: dict[int, dict] = {}
    current_pack_cost = _groups_cost(groups, nodes, replacements)
    protected_bases: set[int] = set(used_as_single_base)

    leaf_candidates = []
    subset_trials = 0
    for target_id in sorted(root_ids, reverse=True):
        if target_id in protected_bases:
            continue
        allowed = {base_id for base_id in root_ids if base_id < target_id and base_id != target_id}
        candidate, trials = _bounded_best_mosaic(target_id, per_target.get(target_id, []), allowed, nodes)
        subset_trials += trials
        if candidate is None or candidate["copied"] < len(nodes[target_id]) // 3:
            continue
        leaf_candidates.append((target_id, candidate))

    pack_local: dict[int, dict] = {}
    external_leaf: dict[int, dict] = {}
    pack_local_trials = pack_local_accepts = 0
    copack_trials = copack_accepts = 0
    placement_rejections = 0
    placement_net_savings = 0

    # Descending target ids plus protected-base tracking preserves a flat DAG even when several targets
    # share one group: a node already used as a base can never later be transformed into a recipe.
    for target_id, candidate in leaf_candidates:
        if target_id in protected_bases:
            continue
        if any(base_id not in _node_group(groups) or base_id in replacements for base_id in candidate["base_ids"]):
            placement_rejections += 1
            continue

        lookup = _node_group(groups)
        target_group = lookup.get(target_id)
        base_groups = {lookup[base_id] for base_id in candidate["base_ids"]}
        accepted = False

        # Embodiment 1: semantic recipe inside the physical group already needed for target + bases.
        if target_group is not None and base_groups == {target_group}:
            pack_local_trials += 1
            group = groups[target_group]
            old_cost = _group_cost(group, nodes, replacements)
            trial_replacements = dict(replacements)
            trial_replacements[target_id] = candidate
            new_cost = _group_cost(group, nodes, trial_replacements)
            descriptor_extra = MOSAIC_METADATA_BASE + MOSAIC_METADATA_PER_ROOT * len(candidate["base_ids"])
            decoded = sum(
                len(candidate["raw_delta"]) if node_id == target_id else
                (len(replacements[node_id]["raw_delta"]) if node_id in replacements else len(nodes[node_id]))
                for node_id in group
            )
            amp = decoded / max(1, len(nodes[target_id]))
            net = old_cost - new_cost - descriptor_extra
            if amp <= MAX_READ_AMP and net >= PACK_LOCAL_MIN_NET:
                replacements[target_id] = candidate
                candidate["actual_amp"] = amp
                candidate["placement_net_saving"] = net
                pack_local[target_id] = candidate
                pack_local_accepts += 1
                placement_net_savings += net
                protected_bases.update(candidate["base_ids"])
                current_pack_cost = _groups_cost(groups, nodes, replacements)
                accepted = True

        if accepted:
            continue

        # Embodiment 2: remove the target and physically co-locate only the direct roots its recipe uses.
        if target_group is None or any(base_id in protected_bases and base_id not in used_as_single_base for base_id in candidate["base_ids"]):
            placement_rejections += 1
            continue
        trial_groups = _copack_groups(groups, target_id, candidate["base_ids"], sketches, nodes)
        if trial_groups is None:
            placement_rejections += 1
            continue
        copack_trials += 1
        dedicated = trial_groups[-1]
        dedicated_decoded = sum(len(nodes[node_id]) for node_id in dedicated)
        target_amp = (dedicated_decoded + len(candidate["raw_delta"])) / max(1, len(nodes[target_id]))
        base_amp = max((dedicated_decoded / max(1, len(nodes[node_id])) for node_id in dedicated), default=0.0)
        if target_amp > MAX_READ_AMP or base_amp > MAX_READ_AMP:
            placement_rejections += 1
            continue
        new_pack_cost = _groups_cost(trial_groups, nodes, replacements)
        marginal = current_pack_cost - new_pack_cost
        net = marginal - candidate["cost"]
        margin = max(128, max(0, marginal) // 100)
        if net <= margin:
            placement_rejections += 1
            continue
        candidate["actual_amp"] = target_amp
        candidate["placement_net_saving"] = net
        candidate["dedicated_group"] = list(dedicated)
        groups = trial_groups
        current_pack_cost = new_pack_cost
        external_leaf[target_id] = candidate
        copack_accepts += 1
        placement_net_savings += net
        protected_bases.update(candidate["base_ids"])

    # Inherited single-delta targets may upgrade to external mosaic records. The target already lives
    # outside root packs, so the inherited single record is the correct marginal baseline.
    external_upgrades: dict[int, dict] = {}
    upgrade_trials = upgrade_accepts = 0
    current_lookup = _node_group(groups)
    for target_id, selected_base in sorted(assignment.items()):
        raw_single, single_stats = edge_payloads[(target_id, selected_base)]
        single_codec, single_payload = _compress_record(raw_single, 12)
        single_cost = PH.size + len(single_payload) + 24
        allowed = set(current_lookup)
        candidate, trials = _bounded_best_mosaic(target_id, per_target.get(target_id, []), allowed, nodes)
        subset_trials += trials
        if candidate is None or candidate["copied"] < len(nodes[target_id]) // 3:
            continue
        upgrade_trials += 1
        amp = _mosaic_read_amp(candidate, groups, nodes, target_id)
        if amp <= MAX_READ_AMP and candidate["cost"] + max(128, single_cost // 100) < single_cost:
            candidate["actual_amp"] = amp
            candidate["single_cost"] = single_cost
            external_upgrades[target_id] = candidate
            upgrade_accepts += 1
            protected_bases.update(candidate["base_ids"])

    records: list[tuple[int, int, bytes, int, bytes]] = []
    node_desc: list[list | None] = [None] * len(nodes)

    def add_record(codec: int, logical: bytes, payload: bytes | None = None) -> int:
        if payload is None:
            codec, payload = _compress_record(logical)
        assert payload is not None
        records.append((codec, len(logical), payload, binascii.crc32(logical) & 0xFFFFFFFF, H(logical)))
        return len(records) - 1

    # Write final physical groups. A pack-local target occupies recipe bytes in the group instead of raw
    # logical bytes; its descriptor reconstructs the logical node from direct bases after pack decode.
    for group in groups:
        payload_parts = []
        layout = {}
        offset = 0
        for node_id in group:
            part = replacements[node_id]["raw_delta"] if node_id in replacements else nodes[node_id]
            payload_parts.append(part)
            layout[node_id] = (offset, len(part))
            offset += len(part)
        logical_pack = b"".join(payload_parts)
        codec, payload = _compress_record(logical_pack)
        record_id = add_record(codec, logical_pack, payload)
        for node_id in group:
            entry_offset, entry_len = layout[node_id]
            if node_id in replacements:
                candidate = replacements[node_id]
                node_desc[node_id] = [
                    "pack_mosaic", record_id, entry_offset, entry_len, candidate["base_ids"],
                    len(nodes[node_id]), H(nodes[node_id]),
                ]
            else:
                node_desc[node_id] = ["direct", record_id, entry_offset, entry_len, H(nodes[node_id])]

    single_nodes = mosaic_upgrade_nodes = mosaic_external_leaf_nodes = 0
    max_mosaic_amps = [candidate["actual_amp"] for candidate in replacements.values()]
    estimated_savings = sum(candidate.get("placement_net_saving", 0) for candidate in replacements.values())

    for target_id, selected_base in sorted(assignment.items()):
        chosen = external_upgrades.get(target_id)
        if chosen is None:
            raw_single, _ = edge_payloads[(target_id, selected_base)]
            codec, payload = _compress_record(raw_single, 12)
            record_id = add_record(codec, raw_single, payload)
            node_desc[target_id] = ["delta", selected_base, record_id, len(nodes[target_id]), H(nodes[target_id])]
            single_nodes += 1
        else:
            record_id = add_record(chosen["codec"], chosen["raw_delta"], chosen["payload"])
            node_desc[target_id] = ["mosaic", chosen["base_ids"], record_id, len(nodes[target_id]), H(nodes[target_id])]
            mosaic_upgrade_nodes += 1
            max_mosaic_amps.append(chosen["actual_amp"])
            estimated_savings += chosen["single_cost"] - chosen["cost"]

    for target_id, chosen in sorted(external_leaf.items()):
        record_id = add_record(chosen["codec"], chosen["raw_delta"], chosen["payload"])
        node_desc[target_id] = ["mosaic", chosen["base_ids"], record_id, len(nodes[target_id]), H(nodes[target_id])]
        mosaic_external_leaf_nodes += 1
        max_mosaic_amps.append(chosen["actual_amp"])
        estimated_savings += chosen.get("placement_net_saving", 0)

    if any(desc is None for desc in node_desc):
        missing = [index for index, desc in enumerate(node_desc) if desc is None]
        raise RuntimeError(f"unassigned placement nodes: {missing[:8]}")

    file_desc = {}
    for file_id, rel in enumerate(rels):
        raw = raws[file_id]
        if file_id in preflate_files:
            packed = preflate_files[file_id]
            record_id = len(records)
            records.append((CODEC_PREFLATE, len(raw), packed, binascii.crc32(raw) & 0xFFFFFFFF, H(raw)))
            file_desc[rel] = ["preflate", record_id, len(raw), H(raw)]
        else:
            file_desc[rel] = ["nodes", file_nodes[file_id], len(raw), H(raw)]

    leaves = [H(payload) for _, _, payload, _, _ in records]
    merkle = V028._merkle_root(leaves)
    record_rel_offsets = []
    cursor = 0
    for _, _, payload, _, _ in records:
        record_rel_offsets.append(cursor)
        cursor += PH.size + len(payload)

    # Physical context can only shrink for pack-local substitutions; dedicated co-packs are explicitly
    # <=2 MiB and <=8x for every base. Keep the inherited weighted metric plus actual mosaic target max.
    pack_read_amp = max(baseline_pack_amp, _max_group_amp(groups, nodes, replacements))
    meta = {
        "v": 1,
        "engine": "EntropyGraph-II-Mosaic-Placement-Compiler-v4",
        "files": file_desc,
        "nodes": node_desc,
        "record_rel_offsets": record_rel_offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": treehash(root),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 1,
        "max_mosaic_bases": MAX_MOSAIC_BASES,
        "max_mosaic_source_index": MAX_MOSAIC_SOURCE_INDEX,
        "pack_limit": baseline_pack_limit,
        "pack_read_amplification": pack_read_amp,
        "max_mosaic_read_amplification": max(max_mosaic_amps, default=0.0),
        "preflate_required": bool(preflate_files),
        "preflate_bridge_contract": "microsoft/preflate-rs 0.7.6 via pinned CMPCT bridge" if preflate_files else None,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT,
                              MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, hh in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, hh))
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))

    return {
        "create_s": time.perf_counter() - started,
        "graph_bytes": out.stat().st_size,
        "files": len(files),
        "unique_nodes": len(nodes),
        "exact_chunk_aliases": exact_aliases,
        "inherited_similarity_candidates": len(inherited_edges),
        "mosaic_discovery_candidates": len(broad_pairs),
        "delta_auditions": auditions,
        "inherited_delta_auditions": inherited_auditions,
        "mosaic_discovery_auditions": discovery_auditions,
        "partial_roots_retained": partial_roots,
        "subset_trials": subset_trials,
        "single_delta_nodes": single_nodes,
        "mosaic_auditions": pack_local_trials + copack_trials + upgrade_trials,
        "pack_local_trials": pack_local_trials,
        "pack_local_mosaic_nodes": pack_local_accepts,
        "copack_trials": copack_trials,
        "copack_mosaic_nodes": copack_accepts,
        "mosaic_upgrade_nodes": mosaic_upgrade_nodes,
        "mosaic_external_leaf_nodes": mosaic_external_leaf_nodes,
        "mosaic_leaf_nodes": pack_local_accepts + mosaic_external_leaf_nodes,
        "small_mosaic_upgrades": sum(1 for node_id in external_upgrades if len(nodes[node_id]) < 4096),
        "mosaic_nodes": pack_local_accepts + mosaic_external_leaf_nodes + mosaic_upgrade_nodes,
        "placement_rejections": placement_rejections,
        "placement_net_savings": placement_net_savings,
        "mosaic_estimated_record_savings": estimated_savings,
        "adaptive_pack_limit": baseline_pack_limit,
        "pack_read_amplification": pack_read_amp,
        "max_mosaic_read_amplification": max(max_mosaic_amps, default=0.0),
        "pack_trials": pack_trials,
        "preflate_attempts": preflate_attempts,
        "preflate_wins": preflate_wins,
        "merkle_leaves": len(leaves),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
    }


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-mosaic-placement-") as td:
        v028_path = Path(td) / "v028.cmpct"
        placement_path = Path(td) / "placement.cmpct"
        v028_stats = V028.build(root, v028_path)
        placement_stats = _build_graph(root, placement_path)
        if placement_path.stat().st_size < v028_path.stat().st_size:
            shutil.copyfile(placement_path, out)
            selected = "mosaic"
        else:
            shutil.copyfile(v028_path, out)
            selected = "v028-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v028_bytes": v028_path.stat().st_size,
            "mosaic_graph_bytes": placement_path.stat().st_size,
            "smaller_than_v028_pct": (v028_path.stat().st_size - out.stat().st_size) / max(1, v028_path.stat().st_size) * 100.0,
            "portfolio_create_s": time.perf_counter() - started,
            "v028": v028_stats,
            "mosaic": placement_stats,
        }


def _open(path: Path):
    stream = path.open("rb")

    def decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                    expected_count: int | None = None, declared_decode: int | None = None,
                    declared_memory: int | None = None):
        raw = zd(comp, raw_size)
        if H(raw) != expected_sha:
            raise RuntimeError("placement metadata authentication")
        meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) > 1:
            raise RuntimeError("unsupported placement metadata")
        if int(meta.get("max_mosaic_bases", MAX_MOSAIC_BASES + 1)) > MAX_MOSAIC_BASES:
            raise RuntimeError("placement mosaic base count exceeds policy")
        if int(meta.get("max_mosaic_source_index", MAX_MOSAIC_SOURCE_INDEX + 1)) > MAX_MOSAIC_SOURCE_INDEX:
            raise RuntimeError("placement mosaic source bound exceeds policy")
        meta_decode = int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1))
        meta_memory = int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1))
        if meta_decode > MAX_DECODE_UNIT or (declared_decode is not None and meta_decode != declared_decode):
            raise RuntimeError("placement decode ceiling exceeds policy")
        if meta_memory > MAX_DECODER_MEMORY or (declared_memory is not None and meta_memory != declared_memory):
            raise RuntimeError("placement memory ceiling exceeds policy")
        leaves = list(meta.get("record_leaf_sha256", []))
        if expected_count is not None and len(leaves) != expected_count:
            raise RuntimeError("placement record-count mismatch")
        if V028._merkle_root(leaves) != expected_merkle:
            raise RuntimeError("placement Merkle mismatch")
        offsets = list(meta.get("record_rel_offsets", []))
        if len(offsets) != len(leaves):
            raise RuntimeError("placement record table mismatch")
        return meta, offsets

    primary_error = None
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short placement header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG:
            raise RuntimeError("not placement research archive")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short primary placement metadata")
        meta, offsets = decode_meta(comp, mus, meta_sha, merkle, count, max_decode, max_memory)
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as exc:
        primary_error = exc

    try:
        stream.seek(-FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(FTR.size)
        if len(footer) != FTR.size:
            raise RuntimeError("short placement footer")
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL:
            raise RuntimeError("placement tail magic")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size:
            raise RuntimeError("placement tail metadata offset")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short placement tail metadata")
        meta, offsets = decode_meta(comp, mus, meta_sha, merkle)
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(f"no authenticated placement metadata: primary={primary_error!r}; tail={tail_error!r}") from tail_error


def _extract_placement(path: Path, dst: Path) -> None:
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
            raise RuntimeError("placement record id out of range")
        stream.seek(record_start + offsets[record_id])
        header = stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short placement physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT:
            raise RuntimeError("placement physical record exceeds decode unit")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
            raise RuntimeError("placement physical Merkle leaf mismatch")
        if codec == CODEC_RAW:
            raw = payload
        elif codec == CODEC_ZSTD:
            raw = zd(payload, usize)
        elif codec == CODEC_PREFLATE:
            raw = V028._preflate_unpack(payload, usize)
        else:
            raise RuntimeError("unknown placement physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("placement physical record integrity")
        record_cache[record_id] = raw
        return raw

    def node(node_id: int) -> bytes:
        if node_id in node_cache:
            return node_cache[node_id]
        if not 0 <= node_id < len(nodes):
            raise RuntimeError("placement node id out of range")
        desc = nodes[node_id]
        kind = desc[0]
        if kind == "direct":
            _, record_id, offset, length, expected = desc
            pack = record(record_id)
            if offset > len(pack) or length > len(pack) - offset:
                raise RuntimeError("placement direct slice bounds")
            raw = pack[offset : offset + length]
        elif kind == "delta":
            _, base_id, record_id, length, expected = desc
            if nodes[base_id][0] != "direct":
                raise RuntimeError("placement delta dependency depth")
            raw = delta_decode(node(base_id), record(record_id), expected_size=length, max_output=MAX_CHUNK)
        elif kind == "mosaic":
            _, base_ids, record_id, length, expected = desc
            if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= MAX_MOSAIC_BASES:
                raise RuntimeError("placement mosaic base list bounds")
            if len(set(base_ids)) != len(base_ids) or any(not isinstance(base_id, int) for base_id in base_ids):
                raise RuntimeError("invalid placement mosaic base list")
            if any(not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct" for base_id in base_ids):
                raise RuntimeError("placement mosaic dependency depth")
            raw = mosaic_delta_decode(
                [node(base_id) for base_id in base_ids], record(record_id),
                expected_size=length, max_bases=MAX_MOSAIC_BASES,
                max_source_bytes=MAX_MOSAIC_SOURCE_INDEX, max_output=MAX_CHUNK,
            )
        elif kind == "pack_mosaic":
            _, record_id, offset, recipe_len, base_ids, length, expected = desc
            if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= MAX_MOSAIC_BASES:
                raise RuntimeError("pack-mosaic base list bounds")
            if len(set(base_ids)) != len(base_ids) or any(not isinstance(base_id, int) for base_id in base_ids):
                raise RuntimeError("invalid pack-mosaic base list")
            if any(not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct" for base_id in base_ids):
                raise RuntimeError("pack-mosaic dependency depth")
            pack = record(record_id)
            if offset > len(pack) or recipe_len > len(pack) - offset:
                raise RuntimeError("pack-mosaic recipe bounds")
            recipe = pack[offset : offset + recipe_len]
            raw = mosaic_delta_decode(
                [node(base_id) for base_id in base_ids], recipe,
                expected_size=length, max_bases=MAX_MOSAIC_BASES,
                max_source_bytes=MAX_MOSAIC_SOURCE_INDEX, max_output=MAX_CHUNK,
            )
        else:
            raise RuntimeError("unknown placement node description")
        if H(raw) != expected:
            raise RuntimeError("placement node SHA-256 mismatch")
        node_cache[node_id] = raw
        return raw

    try:
        for rel, desc in sorted(meta["files"].items()):
            if desc[0] == "preflate":
                raw = record(desc[1]); expected_size = desc[2]; expected = desc[3]
            elif desc[0] == "nodes":
                raw = b"".join(node(node_id) for node_id in desc[1]); expected_size = desc[2]; expected = desc[3]
            else:
                raise RuntimeError("unknown placement file description")
            if len(raw) != expected_size or H(raw) != expected:
                raise RuntimeError("placement file reconstruction mismatch")
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    finally:
        stream.close()


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic == MAG:
        _extract_placement(archive, dst)
    else:
        V028.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return V028.strong_verify(archive)
    stream, meta, _, offsets, merkle = _open(archive)
    stream.close()
    with tempfile.TemporaryDirectory(prefix="cmpct-placement-verify-") as td:
        dst = Path(td)
        _extract_placement(archive, dst)
        got = treehash(dst)
    if got != meta["tree_sha256"]:
        raise RuntimeError("placement logical tree root mismatch")
    return {
        "ok": True,
        "tree_sha256": got,
        "merkle_root": merkle.hex(),
        "records": len(offsets),
        "max_decode_unit": meta["max_decode_unit"],
        "max_decoder_memory": meta["max_decoder_memory"],
        "max_mosaic_bases": meta["max_mosaic_bases"],
    }


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter(); strong_verify(out); samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result
