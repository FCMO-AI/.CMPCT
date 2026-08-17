from __future__ import annotations

"""Locality-aware upper-bound oracle for the failed CMPCT mosaic archive frontier.

This is a diagnostic, not a production encoder.  It answers a narrower question than the existing
failure decomposition: after a direct target is removed from the v0.28 root pack, does *any* bounded
2–4-root mosaic still save real physical bytes while charging the complete decoded physical groups that
its roots live in and respecting the frozen <=8x selective-read budget?

The oracle exhaustively checks at most eight named roots on the fixed v2 stress corpus.  That search is
small enough to be useful as a falsification oracle and is explicitly forbidden from becoming runtime
candidate discovery.  A future encoder must approximate any useful result with bounded discovery.

Footnote: archive economics are measured against marginal physical bytes, not standalone target cost.
For direct targets the baseline is the selected v0.28 pack before/after removing the target.  For an
already-delta target the baseline is its existing selected delta record.  The same PH/metadata accounting
used by the prior diagnostics is retained, so this script does not create a friendlier cost model.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import shutil

import mosaic_v029_failure_diagnostics as D
from mosaic_stress_corpus_v2 import build as build_stress

MAX_READ_AMP = 8.0
MAX_ROOTS = 8
MAX_MOSAIC_BASES = 4


def _pack_lookup(groups: list[list[int]], nodes: list[bytes]) -> dict[int, tuple[int, int]]:
    lookup: dict[int, tuple[int, int]] = {}
    for group_id, group in enumerate(groups):
        decoded = sum(len(nodes[node_id]) for node_id in group)
        for node_id in group:
            lookup[node_id] = (group_id, decoded)
    return lookup


def _physical_amp(target_len: int, raw_delta_len: int, base_ids: list[int],
                  lookup: dict[int, tuple[int, int]]) -> float | None:
    groups: dict[int, int] = {}
    for base_id in base_ids:
        row = lookup.get(base_id)
        if row is None:
            return None
        group_id, decoded = row
        groups[group_id] = decoded
    return (sum(groups.values()) + raw_delta_len) / max(1, target_len)


def _named_nodes(rels: list[str], file_nodes: dict[int, list[int]], prefix: str) -> list[int]:
    file_ids = [index for index, rel in enumerate(rels) if Path(rel).name.startswith(prefix)]
    return sorted({node_id for file_id in file_ids for node_id in file_nodes[file_id]})


def _best_legal_mosaic(nodes: list[bytes], target_id: int, root_ids: list[int],
                       lookup: dict[int, tuple[int, int]]) -> dict | None:
    best = None
    limited = sorted(set(root_ids))[:MAX_ROOTS]
    for width in range(2, min(MAX_MOSAIC_BASES, len(limited)) + 1):
        for combo in combinations(limited, width):
            trial = D._mosaic_trial(combo, nodes, target_id)
            if trial is None or trial["copied"] < len(nodes[target_id]) // 3:
                continue
            amp = _physical_amp(len(nodes[target_id]), trial["raw_delta_bytes"], trial["base_ids"], lookup)
            if amp is None or amp > MAX_READ_AMP:
                continue
            row = dict(trial)
            row["physical_read_amplification"] = amp
            metric = (row["bytes"], amp, -row["copied"], tuple(row["base_ids"]))
            if best is None or metric < best[0]:
                best = (metric, row)
    return best[1] if best else None


def _diagnose(path: Path) -> dict:
    files, rels, raws, nodes, file_nodes = D._scan_nodes(path)
    graph = D._v028_graph(nodes)
    named_roots = _named_nodes(rels, file_nodes, "root-")
    target_ids = _named_nodes(rels, file_nodes, "target-")
    targets = []

    for target_id in target_ids:
        if target_id in graph["root_ids"]:
            trial_roots = sorted(node_id for node_id in graph["root_ids"] if node_id != target_id)
            trial_plan, _ = D.V028._choose_pack_plan(nodes, graph["sketches"], trial_roots)
            trial_cost, trial_amp, trial_limit, trial_groups = trial_plan
            marginal = graph["pack_cost"] - trial_cost
            lookup = _pack_lookup(trial_groups, nodes)
            legal_named = [root_id for root_id in named_roots if root_id in trial_roots]
            best = _best_legal_mosaic(nodes, target_id, legal_named, lookup)
            net = (marginal - best["bytes"]) if best else None
            margin = max(128, max(0, marginal) // 100)
            targets.append({
                "target_id": target_id,
                "kind": "direct-root-leaf",
                "target_bytes": len(nodes[target_id]),
                "baseline_pack_bytes": graph["pack_cost"],
                "without_target_pack_bytes": trial_cost,
                "marginal_target_pack_bytes": marginal,
                "trial_pack_limit": trial_limit,
                "trial_pack_amplification": trial_amp,
                "trial_groups": trial_groups,
                "best_locality_legal_mosaic": best,
                "net_physical_saving": net,
                "material_margin": margin,
                "material_positive": bool(best and net is not None and net > margin),
            })
        else:
            assigned_base = graph["assignment"].get(target_id)
            assigned = graph["delta_rows"].get((target_id, assigned_base)) if assigned_base is not None else None
            lookup = _pack_lookup(graph["groups"], nodes)
            legal_named = [root_id for root_id in named_roots if root_id in graph["root_ids"]]
            best = _best_legal_mosaic(nodes, target_id, legal_named, lookup)
            baseline = assigned["bytes"] if assigned else None
            net = (baseline - best["bytes"]) if baseline is not None and best else None
            margin = max(128, baseline // 100) if baseline is not None else None
            targets.append({
                "target_id": target_id,
                "kind": "existing-delta-target",
                "target_bytes": len(nodes[target_id]),
                "assigned_base": assigned_base,
                "assigned_delta_bytes": baseline,
                "current_groups": graph["groups"],
                "best_locality_legal_mosaic": best,
                "net_physical_saving": net,
                "material_margin": margin,
                "material_positive": bool(best and net is not None and margin is not None and net > margin),
            })

    return {
        "name": path.name,
        "tree_sha256": D.V028.treehash(path),
        "v028_pack_bytes": graph["pack_cost"],
        "v028_pack_limit": graph["pack_limit"],
        "v028_pack_read_amplification": graph["pack_amp"],
        "targets": targets,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    manifest = build_stress(work_root)
    rows = [_diagnose(work_root / row["name"]) for row in manifest["workloads"]]
    material = []
    for row in rows:
        for target in row["targets"]:
            if target["material_positive"]:
                material.append({
                    "workload": row["name"],
                    "target_id": target["target_id"],
                    "kind": target["kind"],
                    "net_physical_saving": target["net_physical_saving"],
                    "physical_read_amplification": target["best_locality_legal_mosaic"]["physical_read_amplification"],
                    "base_ids": target["best_locality_legal_mosaic"]["base_ids"],
                })
    return {
        "schema": "cmpct-mosaic-v029-locality-oracle-v1",
        "claim_boundary": (
            "diagnostic upper bound only; exhaustive <=8-root combinations are forbidden as production discovery"
        ),
        "frozen_read_amplification_budget": MAX_READ_AMP,
        "rows": rows,
        "summary": {
            "material_locality_legal_targets": len(material),
            "material_locality_legal_workloads": len({row["workload"] for row in material}),
            "net_physical_saving_upper_bound_bytes": sum(row["net_physical_saving"] for row in material),
            "material_targets": material,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Mosaic_Locality_Oracle"))
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
