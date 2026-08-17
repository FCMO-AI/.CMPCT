from __future__ import annotations

"""Mechanism diagnostics for the failed CMPCT mosaic full-artifact attempts.

This script is deliberately **not** an acceptance benchmark.  It decomposes why a primitive multi-root
win disappears inside a complete v0.28 archive:

- which parent nodes remain independent direct roots after v0.28 central-base selection;
- how much exact information each root contributes even when its one-root delta loses;
- the best bounded 2–4-root mosaic with all parents versus direct-only parents;
- a direct target's true marginal cost in the selected v0.28 solid root packs;
- whether replacing a raw target *inside the same physical pack* with a mosaic recipe can beat Zstd's
  ordinary solid-context treatment;
- whether one useful parent is unavailable only because v0.28 stored that parent as a delta.

Footnote: small exhaustive root combinations are an **oracle diagnostic** over the fixed stress corpus
(max eight named roots, combinations of at most four).  They are forbidden from becoming production
candidate discovery.  Their purpose is to tell us whether a bounded representation has headroom before
we spend another implementation tranche trying to approximate it.
"""

import argparse
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import shutil
import sys

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import choose_central_bases, delta_encode, fastcdc, lsh_candidates, similarity_sketch
from mosaic_stress_corpus_v2 import build as build_stress

ROOT = Path(__file__).resolve().parents[1]
V028_PATH = ROOT / "experiments" / "entropygraph_v028.py"
PH_META_SINGLE = 24
MOSAIC_META_BASE = 24
MOSAIC_META_ROOT = 8


def _load_v028():
    spec = importlib.util.spec_from_file_location("cmpct_mosaic_diag_v028", V028_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v0.28 engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V028 = _load_v028()


def _scan_nodes(path: Path):
    files = sorted(p for p in path.rglob("*") if p.is_file())
    rels = [p.relative_to(path).as_posix() for p in files]
    raws = [p.read_bytes() for p in files]
    nodes: list[bytes] = []
    node_hash_to_id: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    for file_id, raw in enumerate(raws):
        chunks = (
            fastcdc(raw, min_size=32 * 1024, avg_size=128 * 1024, max_size=V028.MAX_CHUNK)
            if len(raw) > V028.MAX_CHUNK
            else [type("C", (), {"offset": 0, "length": len(raw)})()]
        )
        refs = []
        for chunk in chunks:
            part = raw[chunk.offset : chunk.offset + chunk.length]
            hh = V028.H(part)
            node_id = node_hash_to_id.get(hh)
            if node_id is None or nodes[node_id] != part:
                node_id = len(nodes)
                node_hash_to_id[hh] = node_id
                nodes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs
    return files, rels, raws, nodes, file_nodes


def _v028_graph(nodes: list[bytes]):
    sketches = [similarity_sketch(raw) for raw in nodes]
    edges = lsh_candidates(sketches, max_bucket=48, max_candidates=8)
    direct_costs = [V028._direct_cost(raw) for raw in nodes]
    measured = []
    delta_rows: dict[tuple[int, int], dict] = {}
    for edge in edges:
        target = nodes[edge.target]; base = nodes[edge.base]
        if min(len(target), len(base)) < V028.MIN_DELTA:
            continue
        result = delta_encode(base, target, block=64, max_base_index=V028.MAX_CHUNK)
        codec, payload = V028._compress_record(result.payload, 12)
        stored = V028.PH.size + len(payload) + PH_META_SINGLE
        saving = direct_costs[edge.target] - stored
        delta_rows[(edge.target, edge.base)] = {
            "bytes": stored,
            "raw_delta_bytes": len(result.payload),
            "copied": result.stats.copied_bytes,
            "saving_vs_direct": saving,
        }
        if saving >= max(128, direct_costs[edge.target] // 50) and result.stats.copied_bytes >= len(target) // 4:
            measured.append((edge.target, edge.base, saving))
    assignment = choose_central_bases(len(nodes), measured)
    delta_nodes = set(assignment)
    root_ids = [node_id for node_id in range(len(nodes)) if node_id not in delta_nodes]
    plan, trials = V028._choose_pack_plan(nodes, sketches, root_ids)
    pack_cost, pack_amp, pack_limit, groups = plan
    node_group = {}
    for group_id, group in enumerate(groups):
        for node_id in group:
            node_group[node_id] = group_id
    return {
        "sketches": sketches,
        "direct_costs": direct_costs,
        "delta_rows": delta_rows,
        "assignment": assignment,
        "root_ids": root_ids,
        "pack_cost": pack_cost,
        "pack_amp": pack_amp,
        "pack_limit": pack_limit,
        "groups": groups,
        "node_group": node_group,
        "pack_trials": trials,
    }


def _single_trial(base: bytes, target: bytes) -> dict:
    result = delta_encode(base, target, block=64, max_base_index=V028.MAX_CHUNK)
    codec, payload = V028._compress_record(result.payload, 12)
    cost = V028.PH.size + len(payload) + PH_META_SINGLE
    return {
        "bytes": cost,
        "raw_delta_bytes": len(result.payload),
        "copied": result.stats.copied_bytes,
        "literal": result.stats.literal_bytes,
    }


def _mosaic_trial(base_ids: tuple[int, ...], nodes: list[bytes], target_id: int):
    bases = [nodes[node_id] for node_id in base_ids]
    if sum(map(len, bases)) > 8 * 1024 * 1024:
        return None
    result = mosaic_delta_encode(
        bases, nodes[target_id], block=64, max_bases=4,
        max_source_index=8 * 1024 * 1024, max_matches_per_key=16,
    )
    used_slots = used_base_slots(result.stats)
    used_ids = tuple(base_ids[slot] for slot in used_slots)
    if len(used_ids) < 2:
        return None
    if used_ids != base_ids:
        # Compact the descriptor/root set until payload and roots agree exactly.
        return _mosaic_trial(used_ids, nodes, target_id)
    restored = mosaic_delta_decode(
        bases, result.payload, expected_size=len(nodes[target_id]),
        max_bases=4, max_source_bytes=8 * 1024 * 1024, max_output=V028.MAX_CHUNK,
    )
    if restored != nodes[target_id]:
        raise RuntimeError("diagnostic mosaic reconstruction mismatch")
    codec, payload = V028._compress_record(result.payload, 12)
    cost = V028.PH.size + len(payload) + MOSAIC_META_BASE + MOSAIC_META_ROOT * len(base_ids)
    return {
        "base_ids": list(base_ids),
        "bytes": cost,
        "raw_delta_bytes": len(result.payload),
        "copied": result.stats.copied_bytes,
        "literal": result.stats.literal_bytes,
    }


def _best_mosaic(root_ids: list[int], nodes: list[bytes], target_id: int):
    best = None
    limited = sorted(set(root_ids))[:8]
    for width in range(2, min(4, len(limited)) + 1):
        for combo in combinations(limited, width):
            trial = _mosaic_trial(combo, nodes, target_id)
            if trial is None:
                continue
            metric = (trial["bytes"], -trial["copied"], tuple(trial["base_ids"]))
            if best is None or metric < best[0]:
                best = (metric, trial)
    return best[1] if best else None


def _pack_cost(nodes: list[bytes], group: list[int]) -> int:
    raw = b"".join(nodes[node_id] for node_id in group)
    _, payload = V028._compress_record(raw)
    return V028.PH.size + len(payload)


def _pack_local_oracle(nodes: list[bytes], graph: dict, target_id: int, named_root_ids: list[int]):
    group_id = graph["node_group"].get(target_id)
    if group_id is None:
        return None
    group = graph["groups"][group_id]
    same_group_roots = [node_id for node_id in named_root_ids if node_id in group and node_id != target_id]
    best = _best_mosaic(same_group_roots, nodes, target_id)
    if best is None:
        return {
            "group_id": group_id,
            "group_nodes": group,
            "group_decoded_bytes": sum(len(nodes[node_id]) for node_id in group),
            "same_group_named_roots": same_group_roots,
            "best": None,
        }
    base_ids = set(best["base_ids"])
    # Pack-local semantic preconditioning keeps one physical record. The target's raw slot is replaced
    # by the exact mosaic recipe bytes; all referenced bases must already live in that same decoded pack.
    transformed_parts = []
    for node_id in group:
        if node_id == target_id:
            # Recreate the exact compact payload for the winning base set.
            result = mosaic_delta_encode(
                [nodes[base_id] for base_id in best["base_ids"]], nodes[target_id],
                block=64, max_bases=4, max_source_index=8 * 1024 * 1024, max_matches_per_key=16,
            )
            transformed_parts.append(result.payload)
        else:
            transformed_parts.append(nodes[node_id])
    baseline_cost = _pack_cost(nodes, group)
    transformed_raw = b"".join(transformed_parts)
    _, transformed_payload = V028._compress_record(transformed_raw)
    transformed_cost = V028.PH.size + len(transformed_payload)
    metadata_extra = MOSAIC_META_BASE + MOSAIC_META_ROOT * len(best["base_ids"])
    net = baseline_cost - transformed_cost - metadata_extra
    return {
        "group_id": group_id,
        "group_nodes": group,
        "group_decoded_bytes": sum(len(nodes[node_id]) for node_id in group),
        "same_group_named_roots": same_group_roots,
        "baseline_physical_bytes": baseline_cost,
        "preconditioned_physical_bytes": transformed_cost,
        "descriptor_extra_bytes": metadata_extra,
        "net_estimated_saving": net,
        "read_amplification": len(transformed_raw) / max(1, len(nodes[target_id])),
        "best": best,
    }


def _diagnose_workload(path: Path) -> dict:
    files, rels, raws, nodes, file_nodes = _scan_nodes(path)
    graph = _v028_graph(nodes)
    root_file_ids = [index for index, rel in enumerate(rels) if Path(rel).name.startswith("root-")]
    target_file_ids = [index for index, rel in enumerate(rels) if Path(rel).name.startswith("target-")]
    named_root_ids = sorted({node_id for file_id in root_file_ids for node_id in file_nodes[file_id]})
    target_ids = sorted({node_id for file_id in target_file_ids for node_id in file_nodes[file_id]})
    rows = []
    for target_id in target_ids:
        single_rows = []
        for root_id in named_root_ids:
            if root_id == target_id:
                continue
            row = _single_trial(nodes[root_id], nodes[target_id])
            row.update({
                "root_id": root_id,
                "root_is_direct": root_id in graph["root_ids"],
                "root_assignment_base": graph["assignment"].get(root_id),
                "saving_vs_target_direct": graph["direct_costs"][target_id] - row["bytes"],
            })
            single_rows.append(row)
        all_mosaic = _best_mosaic(named_root_ids, nodes, target_id)
        direct_mosaic = _best_mosaic([root_id for root_id in named_root_ids if root_id in graph["root_ids"]], nodes, target_id)

        pack_marginal = None
        if target_id in graph["root_ids"]:
            trial_roots = [node_id for node_id in graph["root_ids"] if node_id != target_id]
            trial_plan, _ = V028._choose_pack_plan(nodes, graph["sketches"], trial_roots)
            trial_cost, trial_amp, trial_limit, trial_groups = trial_plan
            pack_marginal = {
                "current_pack_bytes": graph["pack_cost"],
                "without_target_pack_bytes": trial_cost,
                "marginal_target_pack_bytes": graph["pack_cost"] - trial_cost,
                "trial_pack_amplification": trial_amp,
                "trial_pack_limit": trial_limit,
            }
        assigned_base = graph["assignment"].get(target_id)
        assigned_delta = graph["delta_rows"].get((target_id, assigned_base)) if assigned_base is not None else None
        rows.append({
            "target_id": target_id,
            "target_bytes": len(nodes[target_id]),
            "target_direct_cost": graph["direct_costs"][target_id],
            "target_is_direct": target_id in graph["root_ids"],
            "assigned_base": assigned_base,
            "assigned_delta": assigned_delta,
            "single_root_trials": single_rows,
            "best_all_named_roots_mosaic": all_mosaic,
            "best_direct_named_roots_mosaic": direct_mosaic,
            "pack_marginal": pack_marginal,
            "pack_local_precondition_oracle": _pack_local_oracle(nodes, graph, target_id, named_root_ids),
        })

    return {
        "name": path.name,
        "tree_sha256": V028.treehash(path),
        "files": rels,
        "nodes": len(nodes),
        "v028_assignment": {str(key): value for key, value in sorted(graph["assignment"].items())},
        "v028_root_ids": graph["root_ids"],
        "v028_pack_bytes": graph["pack_cost"],
        "v028_pack_limit": graph["pack_limit"],
        "v028_pack_read_amplification": graph["pack_amp"],
        "v028_groups": graph["groups"],
        "named_root_node_ids": named_root_ids,
        "target_node_ids": target_ids,
        "targets": rows,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    manifest = build_stress(work_root)
    rows = [_diagnose_workload(work_root / row["name"]) for row in manifest["workloads"]]
    return {
        "schema": "cmpct-mosaic-v029-failure-diagnostics-v1",
        "claim_boundary": "diagnostic upper bounds only; exhaustive small-root oracle is not production candidate discovery",
        "corpus": manifest,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Mosaic_Failure_Diagnostics"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
