"""Third full-artifact CMPCT multi-root mosaic experiment.

Attempt #2 repaired eligibility: direct leaf targets could finally become mosaics.  Its failed full-artifact
record then exposed two deeper mechanisms:

* a mosaic can look spectacular against *standalone* direct storage while losing to the target's tiny
  **marginal cost inside an existing similarity-ordered solid root pack**;
* a root can be useless as a complete one-parent delta yet become valuable when several such roots jointly
  explain disjoint regions of one target.

Attempt #3 therefore changes admission, not the frozen benchmark gate:

1. exact partial-copy roots survive the bounded discovery stage even when their one-root delta is larger
   than direct storage;
2. direct leaf mosaics compete against the **marginal physical pack cost** of removing that target from
   the current v0.28 root set, not against `_direct_cost(target)`;
3. leaf promotion is greedy and bounded: at most 32 candidate leaves are considered, each with one real
   pack re-tournament across the existing six pack ceilings;
4. mosaic descriptors remain compacted to roots actually referenced by COPY operations, and all bases
   remain independent direct nodes.

The inherited v0.28 central-base assignment is still derived only from inherited v0.28 LSH edges.  New
partial-root discovery cannot rewrite the baseline and call the rewrite a mosaic win.

Footnote: this is deliberately a separate attempt file.  `entropygraph_v029_mosaic.py` (attempt #1),
`entropygraph_v029_mosaic_leaf.py` (attempt #2), and their durable failed records remain reproducible.
"""
from __future__ import annotations

import binascii
import importlib.util
import msgpack
from pathlib import Path
import sys
import time

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import choose_central_bases, delta_encode, fastcdc, lsh_candidates, similarity_sketch

HERE = Path(__file__).resolve().parent
ATTEMPT2_PATH = HERE / "entropygraph_v029_mosaic_leaf.py"


def _load_attempt2():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_attempt2", ATTEMPT2_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load mosaic attempt-2 engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


A2 = _load_attempt2()
PARENT = A2.PARENT
V028 = A2.V028
H = A2.H
zc = A2.zc
MAG = A2.MAG
TAIL = A2.TAIL
HDR = A2.HDR
FTR = A2.FTR
PH = A2.PH
CODEC_PREFLATE = A2.CODEC_PREFLATE
MAX_CHUNK = A2.MAX_CHUNK
MAX_DECODE_UNIT = A2.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = A2.MAX_DECODER_MEMORY
MIN_DELTA = A2.MIN_DELTA
PREFLATE_EXTS = A2.PREFLATE_EXTS
MAX_MOSAIC_BASES = A2.MAX_MOSAIC_BASES
MAX_MOSAIC_SOURCE_INDEX = A2.MAX_MOSAIC_SOURCE_INDEX
MAX_READ_AMP = A2.MAX_READ_AMP
MOSAIC_METADATA_BASE = A2.MOSAIC_METADATA_BASE
MOSAIC_METADATA_PER_ROOT = A2.MOSAIC_METADATA_PER_ROOT
MAX_LEAF_TOURNAMENT = 32


def _compress_record(raw: bytes, level: int = 19):
    return A2._compress_record(raw, level)


def _direct_cost(raw: bytes) -> int:
    return A2._direct_cost(raw)


def _pack_lookup(groups: list[list[int]], nodes: list[bytes]) -> dict[int, tuple[int, int]]:
    return A2._pack_lookup(groups, nodes)


def _target_read_amp(target_len: int, raw_delta_len: int, base_ids: list[int],
                     pack_lookup: dict[int, tuple[int, int]]) -> float:
    return A2._target_read_amp(target_len, raw_delta_len, base_ids, pack_lookup)


def _compact_mosaic(candidate_ids: list[int], target_id: int, nodes: list[bytes]):
    return A2._compact_mosaic(candidate_ids, target_id, nodes)


def _rank_candidates(target: int, per_target_edges: dict[int, list[tuple[int, int, int, int]]],
                     allowed_bases: set[int]) -> list[int]:
    """Rank roots by exact copied information before one-root economics.

    Attempt #2 sorted by one-root saving first.  That suppresses a root that contributes a valuable
    disjoint region but leaves the rest of the target literal, even though several such roots together
    make a very small mosaic.  Exact copied bytes are therefore the first signal here; final encoded
    mosaic bytes still decide admission.
    """
    rows = [row for row in per_target_edges.get(target, ()) if row[0] in allowed_bases]
    rows.sort(key=lambda row: (-row[2], -row[3], -row[1], row[0]))
    return [row[0] for row in rows[:MAX_MOSAIC_BASES]]


def _build_mosaic_graph(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]

    preflate_files: dict[int, bytes] = {}
    normal_files: list[int] = []
    preflate_attempts = 0
    preflate_wins = 0
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

    node_bytes: list[bytes] = []
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
            if node_id is not None and node_bytes[node_id] == part:
                exact_aliases += 1
            else:
                node_id = len(node_bytes)
                node_hash_to_id[hh] = node_id
                node_bytes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs

    sketches = [similarity_sketch(raw) for raw in node_bytes]
    inherited_edges = lsh_candidates(sketches, max_bucket=48, max_candidates=8)
    inherited_pairs = {(edge.target, edge.base): edge.shared_features for edge in inherited_edges}
    broad_pairs = dict(inherited_pairs)
    for target, base, shared in A2._position_independent_candidates(sketches, node_bytes):
        broad_pairs[(target, base)] = max(shared, broad_pairs.get((target, base), 0))

    direct_costs = [_direct_cost(raw) for raw in node_bytes]
    measured: list[tuple[int, int, int]] = []
    edge_payloads: dict[tuple[int, int], tuple[bytes, dict]] = {}
    # (base_id, one-root saving, copied bytes, shared features). Negative saving is intentionally kept
    # when the root contributes enough exact bytes to be a bounded component of a multi-root target.
    per_target_edges: dict[int, list[tuple[int, int, int, int]]] = {}
    auditions = inherited_auditions = mosaic_discovery_auditions = 0
    partial_roots_retained = 0
    for (target_id, base_id), shared in sorted(broad_pairs.items()):
        target = node_bytes[target_id]
        base = node_bytes[base_id]
        if min(len(target), len(base)) < MIN_DELTA:
            continue
        auditions += 1
        if (target_id, base_id) in inherited_pairs:
            inherited_auditions += 1
        else:
            mosaic_discovery_auditions += 1
        result = delta_encode(base, target, block=64, max_base_index=MAX_CHUNK)
        codec, payload = _compress_record(result.payload, 12)
        delta_cost = PH.size + len(payload) + 24
        saving = direct_costs[target_id] - delta_cost
        stats = {
            "saving": saving,
            "stored_cost": delta_cost,
            "copied": result.stats.copied_bytes,
            "literal": result.stats.literal_bytes,
            "shared_features": shared,
        }
        edge_payloads[(target_id, base_id)] = (result.payload, stats)
        if result.stats.copied_bytes >= max(4096, len(target) // 20):
            per_target_edges.setdefault(target_id, []).append(
                (base_id, saving, result.stats.copied_bytes, shared)
            )
            if saving <= 0:
                partial_roots_retained += 1
        if (
            (target_id, base_id) in inherited_pairs
            and saving >= max(128, direct_costs[target_id] // 50)
            and result.stats.copied_bytes >= len(target) // 4
        ):
            measured.append((target_id, base_id, saving))

    # The inherited one-base graph remains unchanged by new partial-root discovery.
    assignment = choose_central_bases(len(node_bytes), measured)
    delta_nodes = set(assignment)
    initial_roots = [node_id for node_id in range(len(node_bytes)) if node_id not in delta_nodes]
    used_as_single_base = set(assignment.values())
    direct_alive = set(initial_roots)

    # Precompute bounded leaf mosaic candidates, but do not admit them against standalone direct cost.
    # A candidate exists only to enter the physical pack-marginal tournament below.
    leaf_candidates: list[tuple[int, int, dict]] = []  # standalone potential, target_id, candidate
    leaf_auditions = 0
    for target_id in sorted(initial_roots):
        if target_id in used_as_single_base:
            continue
        allowed = {base_id for base_id in initial_roots if base_id < target_id and base_id != target_id}
        candidate_ids = _rank_candidates(target_id, per_target_edges, allowed)
        if len(candidate_ids) < 2:
            continue
        leaf_auditions += 1
        candidate = _compact_mosaic(candidate_ids, target_id, node_bytes)
        if candidate is None or candidate["copied"] < len(node_bytes[target_id]) // 3:
            continue
        preliminary_amp = (
            sum(len(node_bytes[base_id]) for base_id in candidate["base_ids"])
            + len(candidate["raw_delta"])
        ) / max(1, len(node_bytes[target_id]))
        if preliminary_amp > MAX_READ_AMP:
            continue
        potential = direct_costs[target_id] - candidate["cost"]
        candidate["preliminary_amp"] = preliminary_amp
        leaf_candidates.append((potential, target_id, candidate))

    # Hard cap tournament work even on a pathologically candidate-rich small graph. Larger standalone
    # potential only orders evaluation; it is *not* the admission baseline.
    leaf_candidates.sort(key=lambda row: (-row[0], row[1]))
    leaf_candidates = leaf_candidates[:MAX_LEAF_TOURNAMENT]

    (current_pack_cost, current_pack_amp, current_pack_limit, current_groups), current_pack_trials = V028._choose_pack_plan(
        node_bytes, sketches, sorted(direct_alive)
    )
    leaf_mosaics: dict[int, dict] = {}
    leaf_pack_tournaments = 0
    leaf_pack_rejections = 0
    leaf_dependency_rejections = 0
    leaf_net_savings = 0

    for _, target_id, candidate in leaf_candidates:
        if target_id not in direct_alive:
            continue
        if any(base_id not in direct_alive for base_id in candidate["base_ids"]):
            leaf_dependency_rejections += 1
            continue
        trial_roots = sorted(direct_alive - {target_id})
        trial_plan, trial_trials = V028._choose_pack_plan(node_bytes, sketches, trial_roots)
        trial_pack_cost, trial_pack_amp, trial_pack_limit, trial_groups = trial_plan
        trial_lookup = _pack_lookup(trial_groups, node_bytes)
        try:
            target_amp = _target_read_amp(
                len(node_bytes[target_id]), len(candidate["raw_delta"]), candidate["base_ids"], trial_lookup
            )
        except KeyError:
            leaf_dependency_rejections += 1
            continue
        leaf_pack_tournaments += 1
        marginal_pack_bytes = current_pack_cost - trial_pack_cost
        net_saving = marginal_pack_bytes - candidate["cost"]
        margin = max(128, max(0, marginal_pack_bytes) // 100)
        if target_amp > MAX_READ_AMP or net_saving <= margin:
            leaf_pack_rejections += 1
            continue

        candidate["actual_amp"] = target_amp
        candidate["marginal_pack_bytes"] = marginal_pack_bytes
        candidate["net_pack_saving"] = net_saving
        leaf_mosaics[target_id] = candidate
        leaf_net_savings += net_saving
        direct_alive.remove(target_id)
        current_pack_cost = trial_pack_cost
        current_pack_amp = trial_pack_amp
        current_pack_limit = trial_pack_limit
        current_groups = trial_groups
        current_pack_trials = trial_trials

    # `current_groups` is already the exact final pack plan after every accepted leaf tournament.
    groups = current_groups
    pack_cost = current_pack_cost
    pack_read_amp = current_pack_amp
    pack_limit = current_pack_limit
    pack_trials = current_pack_trials
    pack_lookup = _pack_lookup(groups, node_bytes)

    records: list[tuple[int, int, bytes, int, bytes]] = []
    node_desc: list[list | None] = [None] * len(node_bytes)

    def add_record(codec: int, logical: bytes, payload: bytes | None = None) -> int:
        if payload is None:
            codec, payload = _compress_record(logical)
        assert payload is not None
        records.append((codec, len(logical), payload, binascii.crc32(logical) & 0xFFFFFFFF, H(logical)))
        return len(records) - 1

    for group in groups:
        raw = b"".join(node_bytes[node_id] for node_id in group)
        codec, payload = _compress_record(raw)
        record_id = add_record(codec, raw, payload)
        offset = 0
        for node_id in group:
            length = len(node_bytes[node_id])
            node_desc[node_id] = ["direct", record_id, offset, length, H(node_bytes[node_id])]
            offset += length

    single_nodes = mosaic_upgrade_nodes = mosaic_leaf_nodes = mosaic_savings = 0
    mosaic_read_amps: list[float] = []
    mosaic_auditions = leaf_auditions

    # Existing one-base targets can upgrade using partial roots too. Their target bytes are already not
    # in the root packs, so the selected single-delta record remains the correct marginal baseline.
    for target_id, selected_base in sorted(assignment.items()):
        raw_single, single_stats = edge_payloads[(target_id, selected_base)]
        single_codec, single_payload = _compress_record(raw_single, 12)
        single_cost = PH.size + len(single_payload) + 24
        candidate_ids = _rank_candidates(target_id, per_target_edges, set(pack_lookup))
        if selected_base not in candidate_ids:
            candidate_ids = [selected_base] + candidate_ids
            candidate_ids = candidate_ids[:MAX_MOSAIC_BASES]
        chosen = None
        if len(candidate_ids) >= 2:
            mosaic_auditions += 1
            candidate = _compact_mosaic(candidate_ids, target_id, node_bytes)
            if candidate is not None:
                target_amp = _target_read_amp(
                    len(node_bytes[target_id]), len(candidate["raw_delta"]), candidate["base_ids"], pack_lookup
                )
                if (
                    target_amp <= MAX_READ_AMP
                    and candidate["copied"] >= len(node_bytes[target_id]) // 3
                    and candidate["cost"] + max(128, single_cost // 100) < single_cost
                ):
                    candidate["actual_amp"] = target_amp
                    chosen = candidate
        if chosen is None:
            record_id = add_record(single_codec, raw_single, single_payload)
            node_desc[target_id] = ["delta", selected_base, record_id, len(node_bytes[target_id]), H(node_bytes[target_id])]
            single_nodes += 1
        else:
            record_id = add_record(chosen["codec"], chosen["raw_delta"], chosen["payload"])
            node_desc[target_id] = ["mosaic", chosen["base_ids"], record_id, len(node_bytes[target_id]), H(node_bytes[target_id])]
            mosaic_upgrade_nodes += 1
            mosaic_savings += single_cost - chosen["cost"]
            mosaic_read_amps.append(chosen["actual_amp"])

    for target_id, chosen in sorted(leaf_mosaics.items()):
        record_id = add_record(chosen["codec"], chosen["raw_delta"], chosen["payload"])
        node_desc[target_id] = ["mosaic", chosen["base_ids"], record_id, len(node_bytes[target_id]), H(node_bytes[target_id])]
        mosaic_leaf_nodes += 1
        mosaic_savings += chosen["net_pack_saving"]
        mosaic_read_amps.append(chosen["actual_amp"])

    if any(desc is None for desc in node_desc):
        missing = [index for index, desc in enumerate(node_desc) if desc is None]
        raise RuntimeError(f"unassigned pack-aware mosaic nodes: {missing[:8]}")

    file_desc: dict[str, list] = {}
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

    meta = {
        "v": 1,
        "engine": "EntropyGraph-II-MultiRoot-Mosaic-PackAware-v3",
        "files": file_desc,
        "nodes": node_desc,
        "record_rel_offsets": record_rel_offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": PARENT.treehash(root),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 1,
        "max_mosaic_bases": MAX_MOSAIC_BASES,
        "max_mosaic_source_index": MAX_MOSAIC_SOURCE_INDEX,
        "pack_limit": pack_limit,
        "pack_read_amplification": pack_read_amp,
        "max_mosaic_read_amplification": max(mosaic_read_amps, default=0.0),
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
        "unique_nodes": len(node_bytes),
        "exact_chunk_aliases": exact_aliases,
        "inherited_similarity_candidates": len(inherited_edges),
        "mosaic_discovery_candidates": len(broad_pairs),
        "delta_auditions": auditions,
        "inherited_delta_auditions": inherited_auditions,
        "mosaic_discovery_auditions": mosaic_discovery_auditions,
        "partial_roots_retained": partial_roots_retained,
        "single_delta_nodes": single_nodes,
        "mosaic_auditions": mosaic_auditions,
        "mosaic_upgrade_nodes": mosaic_upgrade_nodes,
        "mosaic_leaf_nodes": mosaic_leaf_nodes,
        "mosaic_nodes": mosaic_upgrade_nodes + mosaic_leaf_nodes,
        "leaf_candidates": len(leaf_candidates),
        "leaf_pack_tournaments": leaf_pack_tournaments,
        "leaf_pack_rejections": leaf_pack_rejections,
        "leaf_dependency_rejections": leaf_dependency_rejections,
        "leaf_net_pack_savings": leaf_net_savings,
        "mosaic_estimated_record_savings": mosaic_savings,
        "adaptive_pack_limit": pack_limit,
        "pack_read_amplification": pack_read_amp,
        "max_mosaic_read_amplification": max(mosaic_read_amps, default=0.0),
        "pack_trials": pack_trials,
        "preflate_attempts": preflate_attempts,
        "preflate_wins": preflate_wins,
        "merkle_leaves": len(leaves),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
    }


# Reuse the established CMPNX9 reader and outer v0.28 portfolio.  Attempt #3 changes only graph
# construction/admission; recovery and decode semantics remain identical and continue to enforce that
# every mosaic base descriptor references an independent direct node.
PARENT._build_mosaic_graph = _build_mosaic_graph
build = PARENT.build
extract = PARENT.extract
strong_verify = PARENT.strong_verify
bench = PARENT.bench
_open_mosaic = PARENT._open_mosaic


def build_graph(root: Path, out: Path) -> dict:
    return _build_mosaic_graph(root, out)
