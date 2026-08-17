from __future__ import annotations

"""Bounded residual-program packing oracle for the post-attempt-4 CMPCT frontier.

Attempt #4 misses the frozen v2 coverage gate by one workload.  The strongest remaining structural case
is ``05_compressed_stream_avalan``: v0.28/attempt #4 store many tiny depth-1 delta programs as separate
physical records even though those programs share bases and instruction structure.

This diagnostic asks whether co-packing reconstruction programs can save real physical bytes *without*
changing the dependency graph.  It groups only programs that share the same direct base, evaluates a
small fixed set of residual-pack ceilings, charges every packed member for the entire decoded residual
pack, and applies an explicit conservative descriptor charge before reporting a win.

Footnote: this is an oracle for physical representation, not a format implementation.  It does not alter
canonical revision 24, the frozen mosaic gate, or the attempt-4 engine.  A green result only earns an
attempt-5 implementation tranche with reader/recovery tests and complete-artifact measurement.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import mosaic_v029_failure_diagnostics as D
from mosaic_stress_corpus_v2 import build as build_stress
from cmpct.resemblance import delta_encode

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT4_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-full-artifact-attempt4.json"

RESIDUAL_LIMITS = (4, 8, 16, 32, 64, 128, 256)  # KiB
MAX_RESIDUAL_PACK = 256 * 1024
MAX_ADDITIONAL_RECIPE_AMP = 2.0
DESCRIPTOR_CHARGE_PER_MEMBER = 16
MIN_NET_SAVING = 128


def _attempt4_rows() -> dict[str, dict]:
    record = json.loads(ATTEMPT4_HISTORY.read_text(encoding="utf-8"))
    return {row["name"]: row for row in record["v2_rows"]}


def _delta_programs(nodes: list[bytes], graph: dict) -> list[dict]:
    rows = []
    for target_id, base_id in sorted(graph["assignment"].items()):
        result = delta_encode(nodes[base_id], nodes[target_id], block=64, max_base_index=D.V028.MAX_CHUNK)
        codec, payload = D.V028._compress_record(result.payload, 12)
        rows.append({
            "target_id": target_id,
            "base_id": base_id,
            "target_bytes": len(nodes[target_id]),
            "raw_delta": result.payload,
            "raw_delta_bytes": len(result.payload),
            "separate_codec": codec,
            "separate_payload_bytes": len(payload),
            "separate_physical_bytes": D.V028.PH.size + len(payload),
        })
    return rows


def _pack_group(programs: list[dict]) -> dict:
    raw = b"".join(row["raw_delta"] for row in programs)
    codec, payload = D.V028._compress_record(raw, 12)
    separate = sum(row["separate_physical_bytes"] for row in programs)
    packed = D.V028.PH.size + len(payload)
    descriptor_charge = DESCRIPTOR_CHARGE_PER_MEMBER * len(programs)
    net = separate - packed - descriptor_charge
    max_amp = max((len(raw) / max(1, row["target_bytes"]) for row in programs), default=0.0)
    return {
        "base_id": programs[0]["base_id"],
        "target_ids": [row["target_id"] for row in programs],
        "members": len(programs),
        "raw_program_bytes": len(raw),
        "separate_physical_bytes": separate,
        "packed_payload_bytes": len(payload),
        "packed_physical_bytes": packed,
        "descriptor_charge_bytes": descriptor_charge,
        "net_physical_saving": net,
        "max_additional_recipe_read_amplification": max_amp,
    }


def _plan(programs: list[dict], limit: int) -> dict:
    groups = []
    by_base: dict[int, list[dict]] = {}
    for row in programs:
        by_base.setdefault(row["base_id"], []).append(row)

    for base_id in sorted(by_base):
        current: list[dict] = []
        current_raw = 0
        for row in sorted(by_base[base_id], key=lambda item: item["target_id"]):
            candidate_raw = current_raw + row["raw_delta_bytes"]
            candidate_members = current + [row]
            candidate_amp = max(
                candidate_raw / max(1, member["target_bytes"]) for member in candidate_members
            )
            if (
                current
                and (candidate_raw > limit or candidate_amp > MAX_ADDITIONAL_RECIPE_AMP)
            ):
                groups.append(_pack_group(current))
                current = [row]
                current_raw = row["raw_delta_bytes"]
            else:
                current = candidate_members
                current_raw = candidate_raw
        if current:
            groups.append(_pack_group(current))

    eligible = [
        group for group in groups
        if group["members"] >= 2
        and group["raw_program_bytes"] <= MAX_RESIDUAL_PACK
        and group["max_additional_recipe_read_amplification"] <= MAX_ADDITIONAL_RECIPE_AMP
        and group["net_physical_saving"] >= MIN_NET_SAVING
    ]
    return {
        "limit_bytes": limit,
        "groups": groups,
        "eligible_groups": eligible,
        "eligible_programs": sum(group["members"] for group in eligible),
        "net_physical_saving": sum(group["net_physical_saving"] for group in eligible),
        "max_additional_recipe_read_amplification": max(
            (group["max_additional_recipe_read_amplification"] for group in eligible), default=0.0
        ),
    }


def _diagnose(path: Path, attempt4_row: dict) -> dict:
    _, _, _, nodes, _ = D._scan_nodes(path)
    graph = D._v028_graph(nodes)
    programs = _delta_programs(nodes, graph)
    plans = [_plan(programs, kib * 1024) for kib in RESIDUAL_LIMITS]
    best = min(
        plans,
        key=lambda row: (
            -row["net_physical_saving"],
            row["max_additional_recipe_read_amplification"],
            row["limit_bytes"],
        ),
    ) if plans else None
    saving = best["net_physical_saving"] if best else 0
    projected_graph = attempt4_row["mosaic_graph_bytes"] - saving
    projected_candidate = min(attempt4_row["v028_bytes"], projected_graph)
    return {
        "name": path.name,
        "tree_sha256": D.V028.treehash(path),
        "delta_programs": len(programs),
        "attempt4_selected": attempt4_row["selected"],
        "v028_bytes": attempt4_row["v028_bytes"],
        "attempt4_graph_bytes": attempt4_row["mosaic_graph_bytes"],
        "attempt4_deficit_vs_v028_bytes": attempt4_row["mosaic_graph_bytes"] - attempt4_row["v028_bytes"],
        "plans": plans,
        "best_plan": best,
        "projected_attempt5_graph_bytes": projected_graph,
        "projected_candidate_bytes": projected_candidate,
        "projected_new_complete_artifact_win": projected_graph < attempt4_row["v028_bytes"],
        "projected_saving_vs_v028_bytes": max(0, attempt4_row["v028_bytes"] - projected_candidate),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    manifest = build_stress(work_root)
    attempt4 = _attempt4_rows()
    rows = [_diagnose(work_root / row["name"], attempt4[row["name"]]) for row in manifest["workloads"]]
    new_wins = [row for row in rows if row["projected_new_complete_artifact_win"] and row["attempt4_selected"] != "mosaic"]
    return {
        "schema": "cmpct-mosaic-v029-residual-pack-oracle-v1",
        "claim_boundary": (
            "diagnostic projection only; exact residual-pack grammar/metadata bytes require an attempt-5 implementation"
        ),
        "contract": {
            "grouping": "same direct base, deterministic target order",
            "residual_pack_limits_kib": list(RESIDUAL_LIMITS),
            "max_residual_pack_bytes": MAX_RESIDUAL_PACK,
            "max_additional_recipe_read_amplification": MAX_ADDITIONAL_RECIPE_AMP,
            "descriptor_charge_per_member_bytes": DESCRIPTOR_CHARGE_PER_MEMBER,
            "minimum_group_net_saving_bytes": MIN_NET_SAVING,
            "dependency_depth_change": 0,
        },
        "rows": rows,
        "summary": {
            "projected_new_complete_artifact_wins": len(new_wins),
            "projected_new_win_workloads": [row["name"] for row in new_wins],
            "projected_new_saving_vs_v028_bytes": sum(row["projected_saving_vs_v028_bytes"] for row in new_wins),
            "max_additional_recipe_read_amplification": max(
                (row["best_plan"]["max_additional_recipe_read_amplification"] for row in rows if row["best_plan"]),
                default=0.0,
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Mosaic_Residual_Pack_Oracle"))
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
