"""CMPCT v0.29 detached contingency oracle — One-Hop Reference Context Frames.

This oracle is intentionally dormant until the simpler stored shared-dictionary oracle is falsified.  It
measures whether a target direct/root physical record can use one *already stored* similar direct record
as raw zstd dictionary history without merging record boundaries or adding dictionary payload bytes.

The physical dependency graph is kept depth-one: candidate contexts are selected with the existing
``choose_central_bases`` policy so an encoded target can never itself become a context anchor.  In
addition, any physical record containing a direct logical node that already serves as a delta/Mosaic
base is forbidden as a context-coded target; a logical delta can therefore never acquire a hidden second
transform hop through its base record.

Footnote: cold random access pays the full decoded context record plus the target record.  The context
slice passed to zstd is capped at the final 128 KiB, but locality accounting intentionally charges the
*entire* context record because the decoder must reconstruct it before that slice exists.  No warm-cache
credit is allowed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

from cmpct.resemblance import choose_central_bases, lsh_candidates, similarity_sketch

HERE = Path(__file__).resolve().parent
DICT_HELPER_PATH = HERE / "entropygraph_v029_shared_dictionary_oracle.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


D = _load(DICT_HELPER_PATH, "cmpct_v029_reference_context_helpers")
ENGINE = D.ENGINE
PACK = D.PACK
CODEC_PREFLATE = D.CODEC_PREFLATE
MAX_CONTEXT_SLICE = 128 * 1024
MAX_CANDIDATES = 8
MAX_TOTAL_READ_AMP = 8.0
MAX_CONTEXT_ONLY_AMP = 4.0
TRANSITION_CHARGE_PER_TARGET = 32
MIN_NET_SAVING = 128 * 1024
MIN_TARGETS = 8


def _logical_base_node_ids(meta: dict) -> set[int]:
    bases: set[int] = set()
    for desc in meta["nodes"]:
        kind = desc[0]
        if kind in ("delta", "delta_pack"):
            bases.add(int(desc[1]))
        elif kind == "mosaic":
            bases.update(int(base_id) for base_id in desc[1])
        elif kind == "pack_mosaic":
            bases.update(int(base_id) for base_id in desc[4])
    return bases


def _records_containing_logical_bases(meta: dict) -> set[int]:
    nodes = meta["nodes"]
    return {
        int(nodes[node_id][1])
        for node_id in _logical_base_node_ids(meta)
        if nodes[node_id][0] == "direct"
    }


def _direct_members_by_record(meta: dict) -> dict[int, list[int]]:
    members: dict[int, list[int]] = {}
    for desc in meta["nodes"]:
        if desc[0] != "direct":
            continue
        members.setdefault(int(desc[1]), []).append(max(1, int(desc[3])))
    return members


def _context_slice(raw: bytes) -> bytes:
    return raw[-min(MAX_CONTEXT_SLICE, len(raw)):]


def measure(root: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    archive = work_root / "attempt5.cmpct"
    started = time.perf_counter()
    built = ENGINE.build(root, archive)
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != ENGINE.BASE.treehash(root):
        raise RuntimeError("attempt-5 source archive failed before reference-context oracle")

    meta, records = D._read_records(archive)
    rows = {row["record_id"]: row for row in records}
    direct_ids = sorted(D._direct_record_ids(meta))
    direct_ids = [record_id for record_id in direct_ids if rows[record_id]["codec"] != CODEC_PREFLATE]
    index_by_record = {record_id: index for index, record_id in enumerate(direct_ids)}
    record_by_index = {index: record_id for record_id, index in index_by_record.items()}
    forbidden_targets = _records_containing_logical_bases(meta)
    members = _direct_members_by_record(meta)

    sketches = [similarity_sketch(rows[record_id]["raw"]) for record_id in direct_ids]
    discovered = lsh_candidates(sketches, max_candidates=MAX_CANDIDATES)
    api = D.ZstdDictionaryAPI()
    measured_edges = []
    edge_detail: dict[tuple[int, int], dict] = {}

    for edge in discovered:
        target_record = record_by_index[int(edge.target)]
        context_record = record_by_index[int(edge.base)]
        if target_record in forbidden_targets:
            continue
        target = rows[target_record]
        context = rows[context_record]
        dictionary = _context_slice(context["raw"])
        if len(dictionary) < 8:
            continue
        payload = api.compress_verify(target["raw"], dictionary, 19)
        payload_saving = int(target["payload_bytes"]) - len(payload)
        net = payload_saving - TRANSITION_CHARGE_PER_TARGET
        if net <= 0:
            continue
        measured_edges.append((int(edge.target), int(edge.base), net))
        edge_detail[(int(edge.target), int(edge.base))] = {
            "target_record_id": target_record,
            "context_record_id": context_record,
            "shared_features": int(edge.shared_features),
            "target_logical_bytes": int(target["logical_bytes"]),
            "context_logical_bytes": int(context["logical_bytes"]),
            "context_slice_bytes": len(dictionary),
            "baseline_payload_bytes": int(target["payload_bytes"]),
            "context_payload_bytes": len(payload),
            "payload_saving_bytes": payload_saving,
            "transition_charge_bytes": TRANSITION_CHARGE_PER_TARGET,
            "net_saving_bytes": net,
        }

    assignment = choose_central_bases(len(direct_ids), measured_edges)
    selected = []
    rejected_locality = []
    for target_index, context_index in sorted(assignment.items()):
        detail = dict(edge_detail[(target_index, context_index)])
        target_record = detail["target_record_id"]
        context_record = detail["context_record_id"]
        target_raw = rows[target_record]["logical_bytes"]
        context_raw = rows[context_record]["logical_bytes"]
        target_members = members.get(target_record, [])
        if not target_members:
            continue
        worst_total = max((target_raw + context_raw) / member_len for member_len in target_members)
        worst_context = max(context_raw / member_len for member_len in target_members)
        detail["worst_total_read_amp"] = worst_total
        detail["worst_context_only_read_amp"] = worst_context
        detail["direct_members"] = len(target_members)
        if worst_total > MAX_TOTAL_READ_AMP or worst_context > MAX_CONTEXT_ONLY_AMP:
            detail["locality_reject"] = True
            rejected_locality.append(detail)
            continue
        detail["locality_reject"] = False
        selected.append(detail)

    selected_target_ids = {row["target_record_id"] for row in selected}
    selected_context_ids = {row["context_record_id"] for row in selected}
    chain_free = selected_target_ids.isdisjoint(selected_context_ids)
    logical_base_free = selected_target_ids.isdisjoint(forbidden_targets)
    net = sum(row["net_saving_bytes"] for row in selected)
    max_total = max((row["worst_total_read_amp"] for row in selected), default=0.0)
    max_context = max((row["worst_context_only_read_amp"] for row in selected), default=0.0)
    gate = bool(
        net >= MIN_NET_SAVING
        and len(selected) >= MIN_TARGETS
        and chain_free
        and logical_base_free
        and max_total <= MAX_TOTAL_READ_AMP
        and max_context <= MAX_CONTEXT_ONLY_AMP
    )

    return {
        "schema": "cmpct-v029-reference-context-oracle-v1",
        "claim_boundary": "dormant one-hop physical-context ceiling; emitted archive remains exact attempt-5 bytes",
        "source_archive": {
            "bytes": archive.stat().st_size,
            "selected": built.get("selected"),
            "records": len(records),
            "direct_non_preflate_records": len(direct_ids),
            "forbidden_context_targets": len(forbidden_targets & set(direct_ids)),
        },
        "policy": {
            "max_lsh_candidates_per_target": MAX_CANDIDATES,
            "max_context_slice_bytes": MAX_CONTEXT_SLICE,
            "max_total_read_amplification": MAX_TOTAL_READ_AMP,
            "max_context_only_read_amplification": MAX_CONTEXT_ONLY_AMP,
            "transition_charge_per_target_bytes": TRANSITION_CHARGE_PER_TARGET,
            "min_net_saving_bytes": MIN_NET_SAVING,
            "min_targets": MIN_TARGETS,
            "all_pairs_fallback": False,
            "context_targets_may_be_logical_bases": False,
            "context_targets_may_be_context_anchors": False,
        },
        "discovery": {
            "lsh_edges": len(discovered),
            "positive_exact_edges": len(measured_edges),
            "central_assignments_before_locality": len(assignment),
            "locality_rejections": len(rejected_locality),
        },
        "selected": {
            "targets": len(selected),
            "net_saving_bytes": net,
            "chain_free": chain_free,
            "logical_base_free": logical_base_free,
            "max_total_read_amplification": max_total,
            "max_context_only_read_amplification": max_context,
            "rows": selected,
        },
        "rejected_locality": rejected_locality[:32],
        "research_gate_pass": gate,
        "oracle_wall_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT dormant one-hop reference-context oracle")
    parser.add_argument("source", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Reference_Context_Oracle"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.source, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected": result["selected"], "research_gate_pass": result["research_gate_pass"]}, indent=2))


if __name__ == "__main__":
    main()
