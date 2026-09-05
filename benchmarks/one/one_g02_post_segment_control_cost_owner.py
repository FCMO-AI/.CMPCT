"""ONE-G0.2 post-segment Program/control cost-owner diagnosis.

Frozen by ONE_G02_POST_SEGMENT_CONTROL_COST_OWNER_PREREG_2026-09-05.md.
Segment discovery is deliberately outside every timed region. This harness asks
whether generic Program graph materialization or canonical wire serialization owns
post-plan Python research-writer cost. It is not native/product speed authority.
"""
from __future__ import annotations

import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
PRODUCTIVE = ("shift_plus1", "shift_plus1_damage_quarter", "fragmented_every96")
CONTROLS = ("fragmented_every32", "independent_random")
ROUNDS = 51
OWNER_SHARE = 0.60
ROW_MAJORITY = 0.50
MIN_MAJORITY_ROWS = 15
SIZE_OWNER_SHARE = 0.55
MIN_OWNER_SIZES = 5
SEGMENT_STRUCT_BYTES = 12  # exact sizeof(Segment) from promoted native plan evidence
OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}


def _root(node: int, data: bytes) -> Root:
    return Root(Ref(node), len(data), sha256(data).hexdigest())


def _segments_plus1(source: bytes, target: bytes):
    """Untimed maximal generic +1 Ref/Surprise plan.

    Tuples are (kind, offset, length, payload). Ref offsets address source node 0.
    Surprise payload bytes are retained directly; the native plan carries offset and
    length rather than payload, but segment count/modelled struct bytes stay exact.
    """
    plan = []
    i = 0
    n = len(target)
    while i < n:
        if i > 0 and target[i] == source[i - 1]:
            start = i
            i += 1
            while i < n and target[i] == source[i - 1]:
                i += 1
            plan.append(("ref", start - 1, i - start, b""))
        else:
            start = i
            i += 1
            while i < n and not (i > 0 and target[i] == source[i - 1]):
                i += 1
            plan.append(("surprise", 0, i - start, target[start:i]))
    return tuple(plan)


def _program_from_plan(source: bytes, target: bytes, plan, previous_root: Root, current_digest: str):
    limits = Limits()
    nodes = [Node("surprise", surprise=source)]
    level: list[tuple[Ref, int]] = []
    for kind, offset, length, payload in plan:
        if kind == "ref":
            level.append((Ref(0, offset, length), length))
        else:
            node_id = len(nodes)
            nodes.append(Node("surprise", surprise=payload))
            level.append((Ref(node_id), length))

    depth = 1
    fanout = limits.max_nodes
    while len(level) > fanout:
        nxt: list[tuple[Ref, int]] = []
        for off in range(0, len(level), fanout):
            chunk = level[off:off + fanout]
            length = sum(n for _, n in chunk)
            node_id = len(nodes)
            nodes.append(Node("concat", refs=tuple(r for r, _ in chunk), declared_length=length))
            nxt.append((Ref(node_id), length))
        level = nxt
        depth += 1

    nodes.append(Node("concat", refs=tuple(r for r, _ in level), declared_length=len(target)))
    current_root = Root(Ref(len(nodes) - 1), len(target), current_digest)
    return Program(tuple(nodes), {"previous": previous_root, "current": current_root}, limits), depth


def _literal_program(source: bytes, target: bytes, previous_root: Root, current_digest: str):
    nodes = (Node("surprise", surprise=source), Node("surprise", surprise=target))
    current_root = Root(Ref(1), len(target), current_digest)
    return Program(nodes, {"previous": previous_root, "current": current_root}, Limits()), 0


def _measure(fn):
    samples = []
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(ROUNDS):
            t0 = time.perf_counter_ns()
            value = fn()
            samples.append(time.perf_counter_ns() - t0)
        return float(statistics.median(samples)), value
    finally:
        if was_enabled:
            gc.enable()


def _max_concat_refs(program: Program) -> int:
    return max((len(node.refs) for node in program.nodes if node.op == "concat"), default=0)


def _concat_refs(program: Program) -> int:
    return sum(len(node.refs) for node in program.nodes if node.op == "concat")


def _build_row(source: bytes, target: bytes, generic: bool):
    previous_root = _root(0, source)
    current_digest = sha256(target).hexdigest()
    plan = _segments_plus1(source, target) if generic else None

    def build():
        if generic:
            return _program_from_plan(source, target, plan, previous_root, current_digest)
        return _literal_program(source, target, previous_root, current_digest)

    prebuilt, depth = build()
    canonical_wire, ws = encode_program(prebuilt)

    build_ns, built_pair = _measure(build)
    built, measured_depth = built_pair
    encode_ns, encoded = _measure(lambda: encode_program(prebuilt))
    measured_wire, measured_ws = encoded
    combined_ns, combined = _measure(lambda: _build_and_encode(build))
    combined_program, combined_depth, combined_wire, combined_ws = combined

    if measured_wire != canonical_wire or combined_wire != canonical_wire:
        raise AssertionError("canonical wire changed across frozen post-plan paths")
    if measured_ws != ws or combined_ws != ws:
        raise AssertionError("wire stats changed across frozen post-plan paths")
    if measured_depth != depth or combined_depth != depth:
        raise AssertionError("hierarchy depth changed across frozen post-plan paths")

    decoded = decode_program(canonical_wire)
    outputs, vm_stats = evaluate(decoded)
    exact = outputs == {"previous": source, "current": target}
    if not exact:
        raise AssertionError("post-plan canonical reconstruction mismatch")

    ops_ok = all(node.op in OPS for node in prebuilt.nodes)
    max_refs = _max_concat_refs(prebuilt)
    caps_ok = max_refs <= prebuilt.limits.max_nodes and len(prebuilt.nodes) <= prebuilt.limits.max_nodes
    stage_total = build_ns + encode_ns
    encode_share = encode_ns / stage_total
    graph_share = build_ns / stage_total
    segment_count = len(plan) if plan is not None else 0
    segment_surprise = sum(length for kind, _off, length, _payload in plan if kind == "surprise") if plan is not None else len(target)

    return {
        "build_median_ns": build_ns,
        "encode_median_ns": encode_ns,
        "combined_median_ns": combined_ns,
        "encode_share": encode_share,
        "graph_share": graph_share,
        "canonical_wire_bytes": ws.total_bytes,
        "surprise_bytes": ws.surprise_bytes,
        "control_integrity_bytes": ws.control_integrity_bytes,
        "program_nodes": len(prebuilt.nodes),
        "concat_refs": _concat_refs(prebuilt),
        "max_concat_refs": max_refs,
        "hierarchy_depth": depth,
        "segment_count": segment_count,
        "segment_surprise_bytes": segment_surprise,
        "modeled_segment_plan_bytes": segment_count * SEGMENT_STRUCT_BYTES,
        "reader_work_bytes": vm_stats.work_bytes,
        "reader_materialized_bytes": vm_stats.materialized_bytes,
        "reader_nodes_evaluated": vm_stats.nodes_evaluated,
        "exact_reconstruction": exact,
        "ops_ok": ops_ok,
        "caps_ok": caps_ok,
    }


def _build_and_encode(build):
    program, depth = build()
    wire, ws = encode_program(program)
    return program, depth, wire, ws


def run():
    rows = []
    semantic_ok = True
    hostile_hierarchy_seen = False
    productive_encode_shares = []
    productive_graph_shares = []
    size_encode = {size: [] for size in SIZES}
    size_graph = {size: [] for size in SIZES}

    for size in SIZES:
        cases = _relation_cases(size)
        for case in PRODUCTIVE + CONTROLS:
            source, target, expected_enable, expected_shift = cases[case]
            generic = case in PRODUCTIVE
            row = _build_row(source, target, generic)
            row.update({
                "relation_bytes": size,
                "case": case,
                "expected_relation_enable": expected_enable,
                "expected_shift": expected_shift,
                "generic_relation_program": generic,
            })
            semantic_ok &= bool(row["exact_reconstruction"] and row["ops_ok"] and row["caps_ok"])
            if generic:
                productive_encode_shares.append(row["encode_share"])
                productive_graph_shares.append(row["graph_share"])
                size_encode[size].append(row["encode_share"])
                size_graph[size].append(row["graph_share"])
            if size == 256*1024 and case == "fragmented_every96":
                hostile_hierarchy_seen = row["hierarchy_depth"] > 1 and row["max_concat_refs"] == Limits().max_nodes
            rows.append(row)

    median_encode = float(statistics.median(productive_encode_shares))
    median_graph = float(statistics.median(productive_graph_shares))
    encode_majority_rows = sum(x > ROW_MAJORITY for x in productive_encode_shares)
    graph_majority_rows = sum(x > ROW_MAJORITY for x in productive_graph_shares)
    encode_owner_sizes = sum(float(statistics.median(size_encode[s])) >= SIZE_OWNER_SHARE for s in SIZES)
    graph_owner_sizes = sum(float(statistics.median(size_graph[s])) >= SIZE_OWNER_SHARE for s in SIZES)

    encode_owner = (
        median_encode >= OWNER_SHARE
        and encode_majority_rows >= MIN_MAJORITY_ROWS
        and encode_owner_sizes >= MIN_OWNER_SIZES
    )
    graph_owner = (
        median_graph >= OWNER_SHARE
        and graph_majority_rows >= MIN_MAJORITY_ROWS
        and graph_owner_sizes >= MIN_OWNER_SIZES
    )

    if not semantic_ok or not hostile_hierarchy_seen:
        decision = "invalid_post_segment_profile"
    elif encode_owner and not graph_owner:
        decision = "advance_bulk_canonical_emitter"
    elif graph_owner and not encode_owner:
        decision = "advance_program_graph_builder"
    else:
        decision = "hold_joint_post_segment_boundary"

    return {
        "schema": "cmpct-one-g02-post-segment-control-cost-owner-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "frozen_sizes": list(SIZES),
        "frozen_rounds": ROUNDS,
        "frozen_owner_share": OWNER_SHARE,
        "frozen_min_majority_rows": MIN_MAJORITY_ROWS,
        "frozen_size_owner_share": SIZE_OWNER_SHARE,
        "frozen_min_owner_sizes": MIN_OWNER_SIZES,
        "productive_rows": len(productive_encode_shares),
        "median_productive_encode_share": median_encode,
        "median_productive_graph_share": median_graph,
        "encode_majority_rows": encode_majority_rows,
        "graph_majority_rows": graph_majority_rows,
        "encode_owner_size_classes": encode_owner_sizes,
        "graph_owner_size_classes": graph_owner_sizes,
        "hostile_256k_fragmented_hierarchy_seen": hostile_hierarchy_seen,
        "semantic_gates_pass": semantic_ok,
        "decision": decision,
        "claim_boundary": (
            "post-segment Python research-harness cost ownership only; segment discovery is untimed; "
            "no native/product writer, arbitrary discovery, auth, recovery or comparator authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "invalid_post_segment_profile" else 1)
