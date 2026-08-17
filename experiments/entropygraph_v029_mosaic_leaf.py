"""Second full-artifact multi-root mosaic experiment.

Attempt #1 proved that complete artifacts can win, but it exposed an eligibility blind spot: mosaic was
only auditioned for targets that v0.28 had *already* accepted as one-base deltas.  A genuine branch merge
can be too unlike any single parent to cross that gate, which is exactly when several roots are useful.

This engine changes three mechanisms while preserving the frozen archive-level acceptance thresholds:

1. bounded position-independent candidate discovery supplements v0.28's same-band LSH;
2. a direct node may become a mosaic target only when it is a **leaf** (not a base of another selected
   delta), preserving dependency depth 1;
3. a mosaic is re-encoded against only roots that actually emitted COPY bytes, so the descriptor, reader
   materialization, metadata charge and read-amplification accounting all name the same roots.

The v0.28 central-base assignment itself is still derived only from inherited v0.28 candidate edges.  The
new discovery path may create mosaic candidates, but it cannot silently rewrite v0.28's one-base policy
and then claim the difference as a mosaic win.

Footnote: small-node exhaustive discovery is bounded to at most 64 nodes and 16 prior candidates per
node.  Larger graphs use bounded feature buckets.  This is intentionally not an unbounded all-pairs
fallback; the later generalization tranche must show whether the scalable path is sufficient on the
existing 15-workload frontier.
"""
from __future__ import annotations

import binascii
import importlib.util
import msgpack
from pathlib import Path
import struct
import sys
import time

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import choose_central_bases, delta_encode, fastcdc, lsh_candidates, similarity_sketch

HERE = Path(__file__).resolve().parent
PARENT_PATH = HERE / "entropygraph_v029_mosaic.py"


def _load_parent():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_attempt1", PARENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load mosaic attempt-1 engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARENT = _load_parent()
V028 = PARENT.V028
H = PARENT.H
zc = PARENT.zc
MAG = PARENT.MAG
TAIL = PARENT.TAIL
HDR = PARENT.HDR
FTR = PARENT.FTR
PH = PARENT.PH
CODEC_PREFLATE = PARENT.CODEC_PREFLATE
MAX_CHUNK = PARENT.MAX_CHUNK
MAX_DECODE_UNIT = PARENT.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = PARENT.MAX_DECODER_MEMORY
MIN_DELTA = PARENT.MIN_DELTA
PREFLATE_EXTS = PARENT.PREFLATE_EXTS
MAX_MOSAIC_BASES = PARENT.MAX_MOSAIC_BASES
MAX_MOSAIC_SOURCE_INDEX = PARENT.MAX_MOSAIC_SOURCE_INDEX
MAX_READ_AMP = PARENT.MAX_READ_AMP
MOSAIC_METADATA_BASE = PARENT.MOSAIC_METADATA_BASE
MOSAIC_METADATA_PER_ROOT = PARENT.MOSAIC_METADATA_PER_ROOT
MAX_DISCOVERY_CANDIDATES = 16
SMALL_GRAPH_EXHAUSTIVE_CAP = 64


def _compress_record(raw: bytes, level: int = 19):
    return PARENT._compress_record(raw, level)


def _direct_cost(raw: bytes) -> int:
    return PARENT._direct_cost(raw)


def _pack_lookup(groups: list[list[int]], nodes: list[bytes]) -> dict[int, tuple[int, int]]:
    return PARENT._pack_lookup(groups, nodes)


def _target_read_amp(target_len: int, raw_delta_len: int, base_ids: list[int],
                     pack_lookup: dict[int, tuple[int, int]]) -> float:
    return PARENT._target_read_amp(target_len, raw_delta_len, base_ids, pack_lookup)


def _position_independent_candidates(sketches, nodes: list[bytes]) -> list[tuple[int, int, int]]:
    """Return bounded `(target, base, shared-features)` candidates independent of band position.

    v0.28 keys a feature by its band number, which is correct for ordinary near-neighbor discovery but
    misses content moved from one part of an object to another.  Mosaic cares about *which roots explain
    any region*, so equal super-features are allowed to collide across bands.

    For graphs with <=64 nodes, a hard-bounded exhaustive supplement guarantees that a small branch set
    cannot be missed merely because every local minimum moved bands.  Only the 16 closest-size prior
    nodes are admitted, and final encoded bytes still decide whether any edge is useful.
    """
    buckets: dict[tuple[int, int], list[int]] = {}
    pairs: dict[tuple[int, int], int] = {}
    for target, sketch in enumerate(sketches):
        counts: dict[int, int] = {}
        for feat in set(feature for feature in sketch.features if feature):
            for size_bucket in (sketch.size_bucket - 1, sketch.size_bucket, sketch.size_bucket + 1):
                for base in buckets.get((feat, size_bucket), ()):
                    counts[base] = counts.get(base, 0) + 1
        ranked = sorted(
            counts.items(),
            key=lambda item: (-item[1], abs(len(nodes[target]) - len(nodes[item[0]])), item[0]),
        )[:MAX_DISCOVERY_CANDIDATES]
        for base, shared in ranked:
            pairs[(target, base)] = max(shared, pairs.get((target, base), 0))

        if len(nodes) <= SMALL_GRAPH_EXHAUSTIVE_CAP:
            # Footnote: this is O(64*16) at worst because both population and admitted candidates are
            # hard caps. It is an explicit small-graph correctness floor, not a hidden O(N^2) path.
            prior = list(range(target))
            prior.sort(key=lambda base: (abs(len(nodes[target]) - len(nodes[base])), base))
            for base in prior[:MAX_DISCOVERY_CANDIDATES]:
                pairs.setdefault((target, base), 0)

        for feat in set(feature for feature in sketch.features if feature):
            key = (feat, sketch.size_bucket)
            row = buckets.setdefault(key, [])
            row.append(target)
            if len(row) > 48:
                del row[: len(row) - 48]

    return [(target, base, shared) for (target, base), shared in sorted(pairs.items())]


def _compact_mosaic(candidate_ids: list[int], target_id: int, nodes: list[bytes]):
    """Encode until descriptor roots equal the roots actually referenced by COPY operations."""
    ids = list(candidate_ids[:MAX_MOSAIC_BASES])
    if len(ids) < 2:
        return None
    for _ in range(MAX_MOSAIC_BASES):
        if sum(len(nodes[node_id]) for node_id in ids) > MAX_MOSAIC_SOURCE_INDEX:
            return None
        result = mosaic_delta_encode(
            [nodes[node_id] for node_id in ids],
            nodes[target_id],
            block=64,
            max_bases=MAX_MOSAIC_BASES,
            max_source_index=MAX_MOSAIC_SOURCE_INDEX,
            max_matches_per_key=16,
        )
        slots = used_base_slots(result.stats)
        used = [ids[slot] for slot in slots]
        if len(used) < 2:
            return None
        if used == ids:
            restored = mosaic_delta_decode(
                [nodes[node_id] for node_id in ids],
                result.payload,
                expected_size=len(nodes[target_id]),
                max_bases=MAX_MOSAIC_BASES,
                max_source_bytes=MAX_MOSAIC_SOURCE_INDEX,
                max_output=MAX_CHUNK,
            )
            if restored != nodes[target_id]:
                raise RuntimeError("compacted mosaic reconstruction mismatch")
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
        ids = used
    raise RuntimeError("mosaic descriptor compaction did not converge")


def _rank_candidates(target: int, per_target_edges: dict[int, list[tuple[int, int, int, int]]],
                     allowed_bases: set[int]) -> list[int]:
    rows = [row for row in per_target_edges.get(target, ()) if row[0] in allowed_bases]
    rows.sort(key=lambda row: (-row[1], -row[2], -row[3], row[0]))
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
    for target, base, shared in _position_independent_candidates(sketches, node_bytes):
        broad_pairs[(target, base)] = max(shared, broad_pairs.get((target, base), 0))

    direct_costs = [_direct_cost(raw) for raw in node_bytes]
    measured: list[tuple[int, int, int]] = []
    edge_payloads: dict[tuple[int, int], tuple[bytes, dict]] = {}
    per_target_edges: dict[int, list[tuple[int, int, int, int]]] = {}
    auditions = 0
    inherited_auditions = 0
    mosaic_discovery_auditions = 0
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
        if result.stats.copied_bytes >= max(4096, len(target) // 20) and saving > 0:
            per_target_edges.setdefault(target_id, []).append(
                (base_id, saving, result.stats.copied_bytes, shared)
            )
        # Only inherited v0.28 edges may affect the inherited central-base assignment.
        if (
            (target_id, base_id) in inherited_pairs
            and saving >= max(128, direct_costs[target_id] // 50)
            and result.stats.copied_bytes >= len(target) // 4
        ):
            measured.append((target_id, base_id, saving))

    assignment = choose_central_bases(len(node_bytes), measured)
    delta_nodes = set(assignment)
    initial_roots = [node_id for node_id in range(len(node_bytes)) if node_id not in delta_nodes]
    used_as_single_base = set(assignment.values())

    # Direct-leaf mosaic promotion. Candidate edges always point to earlier node ids, so processing roots
    # in ascending order plus excluding already-promoted bases prevents cycles. Any node required as a
    # selected v0.28 base is protected from promotion to keep existing deltas depth-1.
    direct_alive = set(initial_roots)
    leaf_mosaics: dict[int, dict] = {}
    leaf_auditions = 0
    for target_id in sorted(initial_roots):
        if target_id in used_as_single_base:
            continue
        allowed = {base_id for base_id in direct_alive if base_id != target_id and base_id < target_id}
        candidate_ids = _rank_candidates(target_id, per_target_edges, allowed)
        if len(candidate_ids) < 2:
            continue
        leaf_auditions += 1
        candidate = _compact_mosaic(candidate_ids, target_id, node_bytes)
        if candidate is None:
            continue
        preliminary_amp = (
            sum(len(node_bytes[base_id]) for base_id in candidate["base_ids"])
            + len(candidate["raw_delta"])
        ) / max(1, len(node_bytes[target_id]))
        baseline = direct_costs[target_id]
        if (
            preliminary_amp <= MAX_READ_AMP
            and candidate["copied"] >= len(node_bytes[target_id]) // 3
            and candidate["cost"] + max(128, baseline // 100) < baseline
        ):
            candidate["preliminary_amp"] = preliminary_amp
            leaf_mosaics[target_id] = candidate
            direct_alive.remove(target_id)

    # Pack only roots that genuinely remain direct. If a tentative leaf mosaic exceeds the *actual*
    # descriptor/root pack decode budget, put that target back and recompute packing until stable.
    while True:
        root_ids = sorted(direct_alive)
        (pack_cost, pack_read_amp, pack_limit, groups), pack_trials = V028._choose_pack_plan(
            node_bytes, sketches, root_ids
        )
        pack_lookup = _pack_lookup(groups, node_bytes)
        rejected = []
        for target_id, candidate in leaf_mosaics.items():
            try:
                amp = _target_read_amp(
                    len(node_bytes[target_id]), len(candidate["raw_delta"]),
                    candidate["base_ids"], pack_lookup,
                )
            except KeyError:
                amp = float("inf")
            if amp > MAX_READ_AMP:
                rejected.append(target_id)
            else:
                candidate["actual_amp"] = amp
        if not rejected:
            break
        for target_id in rejected:
            leaf_mosaics.pop(target_id, None)
            direct_alive.add(target_id)

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

    single_nodes = 0
    mosaic_upgrade_nodes = 0
    mosaic_leaf_nodes = 0
    mosaic_savings = 0
    mosaic_read_amps: list[float] = []
    mosaic_auditions = leaf_auditions

    for target_id, selected_base in sorted(assignment.items()):
        raw_single, single_stats = edge_payloads[(target_id, selected_base)]
        single_codec, single_payload = _compress_record(raw_single, 12)
        single_cost = PH.size + len(single_payload) + 24
        allowed = set(pack_lookup)
        candidate_ids = _rank_candidates(target_id, per_target_edges, allowed)
        if selected_base not in candidate_ids:
            candidate_ids = [selected_base] + candidate_ids
            candidate_ids = candidate_ids[:MAX_MOSAIC_BASES]
        chosen = None
        if len(candidate_ids) >= 2:
            mosaic_auditions += 1
            candidate = _compact_mosaic(candidate_ids, target_id, node_bytes)
            if candidate is not None:
                target_amp = _target_read_amp(
                    len(node_bytes[target_id]), len(candidate["raw_delta"]),
                    candidate["base_ids"], pack_lookup,
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
        mosaic_savings += direct_costs[target_id] - chosen["cost"]
        mosaic_read_amps.append(chosen["actual_amp"])

    if any(desc is None for desc in node_desc):
        missing = [index for index, desc in enumerate(node_desc) if desc is None]
        raise RuntimeError(f"unassigned mosaic graph nodes: {missing[:8]}")

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
        "engine": "EntropyGraph-II-MultiRoot-Mosaic-Leaf-v2",
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
        "single_delta_nodes": single_nodes,
        "mosaic_auditions": mosaic_auditions,
        "mosaic_upgrade_nodes": mosaic_upgrade_nodes,
        "mosaic_leaf_nodes": mosaic_leaf_nodes,
        "mosaic_nodes": mosaic_upgrade_nodes + mosaic_leaf_nodes,
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


# Reuse attempt #1's outer portfolio and reader; only the graph constructor changes. The reader already
# enforces that every mosaic descriptor base is direct, unique, bounded and depth-1.
PARENT._build_mosaic_graph = _build_mosaic_graph
build = PARENT.build
extract = PARENT.extract
strong_verify = PARENT.strong_verify
bench = PARENT.bench
_open_mosaic = PARENT._open_mosaic

def build_graph(root: Path, out: Path) -> dict:
    return _build_mosaic_graph(root, out)
