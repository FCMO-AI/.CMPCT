"""ONE-G0.2 bounded Surprise pooling falsifier.

Frozen by ONE_G02_BOUNDED_SURPRISE_POOLING_PREREG_2026-09-08.md.  This is a
representation/resource experiment for already-discovered plans, not product speed or
comparator authority.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import PRODUCTIVE, _oracle_plan, _relation_cases
from benchmarks.one.one_g02_post_segment_control_cost_owner import _program_from_plan
from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.ir import Limits, Ref, Root
from experiments.one.range_vm import reconstruct_range_unverified
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = (4 * 1024, 256 * 1024, 1 << 20)
REQUEST_BYTES = 4 * 1024
MAX_RANGE_AMPLIFICATION = 2.1
HOSTILE_CASE = "fragmented_every96"


def _surprise_payload_bytes(program) -> int:
    return sum(len(node.surprise) for node in program.nodes)


def _range_rows(program, target: bytes):
    if len(target) < REQUEST_BYTES:
        return []
    offsets = (0, (len(target) - REQUEST_BYTES) // 2, len(target) - REQUEST_BYTES)
    rows = []
    for start in offsets:
        value, stats = reconstruct_range_unverified(program, "current", start, REQUEST_BYTES)
        exact = value == target[start : start + REQUEST_BYTES]
        materialized_amp = stats.materialized_bytes / REQUEST_BYTES
        work_amp = stats.work_bytes / REQUEST_BYTES
        rows.append({
            "start": start,
            "requested_bytes": REQUEST_BYTES,
            "exact": exact,
            "authenticated": stats.authenticated,
            "materialized_bytes": stats.materialized_bytes,
            "work_bytes": stats.work_bytes,
            "materialized_amplification": materialized_amp,
            "work_amplification": work_amp,
            "nodes_touched": stats.nodes_touched,
            "max_depth": stats.max_depth,
        })
    return rows


def run():
    limits = Limits()
    rows = []
    semantic_ok = True
    resource_ok = True
    surprise_ok = True
    range_ok = True
    hostile_legacy_overflow_seen = False
    hostile_pooled_valid_seen = False

    for size in SIZES:
        cases = _relation_cases(size)
        for case in PRODUCTIVE:
            source, target, expected_enable, expected_shift = cases[case]
            plan = _oracle_plan(source, target)
            previous_root = Root(Ref(0), len(source), sha256(source).hexdigest())
            current_digest = sha256(target).hexdigest()

            legacy, legacy_depth = _program_from_plan(source, target, plan, previous_root, current_digest)
            legacy_nodes = len(legacy.nodes)
            legacy_surprise = _surprise_payload_bytes(legacy)
            legacy_within_node_cap = legacy_nodes <= limits.max_nodes

            pooled, pool_stats = program_from_plan_pooled(
                source,
                target,
                plan,
                previous_root,
                current_digest,
                limits=limits,
            )
            pooled.validate_shape()
            wire, wire_stats = encode_program(pooled)
            decoded = decode_program(wire)
            outputs, vm_stats = evaluate(decoded)
            exact = outputs == {"previous": source, "current": target}
            roots_exact = (
                pooled.roots["previous"].sha256 == sha256(source).hexdigest()
                and pooled.roots["current"].sha256 == current_digest
            )
            pooled_surprise = _surprise_payload_bytes(pooled)
            this_surprise_ok = pooled_surprise == legacy_surprise
            this_resource_ok = len(pooled.nodes) <= limits.max_nodes
            semantic_ok &= exact and roots_exact
            resource_ok &= this_resource_ok
            surprise_ok &= this_surprise_ok

            range_rows = []
            if size == (1 << 20) and case == HOSTILE_CASE:
                hostile_legacy_overflow_seen = legacy_nodes > limits.max_nodes
                hostile_pooled_valid_seen = this_resource_ok
                range_rows = _range_rows(pooled, target)
                this_range_ok = all(
                    item["exact"]
                    and not item["authenticated"]
                    and item["materialized_amplification"] <= MAX_RANGE_AMPLIFICATION
                    and item["work_amplification"] <= MAX_RANGE_AMPLIFICATION
                    for item in range_rows
                )
                range_ok &= this_range_ok

            rows.append({
                "relation_bytes": size,
                "case": case,
                "expected_enable": expected_enable,
                "expected_shift": expected_shift,
                "segments": len(plan),
                "legacy_program_nodes": legacy_nodes,
                "legacy_hierarchy_depth": legacy_depth,
                "legacy_within_node_cap": legacy_within_node_cap,
                "pooled_program_nodes": len(pooled.nodes),
                "node_cap": limits.max_nodes,
                "pooled_node_headroom": limits.max_nodes - len(pooled.nodes),
                "pooled_groups": pool_stats.groups,
                "pooled_max_groups": pool_stats.max_groups,
                "pooled_group_span_bytes": pool_stats.group_span_bytes,
                "pooled_surprise_pool_nodes": pool_stats.surprise_pool_nodes,
                "pooled_group_concat_nodes": pool_stats.group_concat_nodes,
                "pooled_max_surprise_pool_bytes": pool_stats.max_surprise_pool_bytes,
                "legacy_total_surprise_payload_bytes": legacy_surprise,
                "pooled_total_surprise_payload_bytes": pooled_surprise,
                "surprise_payload_equal": this_surprise_ok,
                "canonical_wire_bytes": wire_stats.total_bytes,
                "wire_surprise_bytes": wire_stats.surprise_bytes,
                "control_integrity_bytes": wire_stats.control_integrity_bytes,
                "reader_work_bytes": vm_stats.work_bytes,
                "reader_materialized_bytes": vm_stats.materialized_bytes,
                "reader_nodes_evaluated": vm_stats.nodes_evaluated,
                "exact_reconstruction": exact,
                "root_hashes_exact": roots_exact,
                "range_rows": range_rows,
            })

    gates = {
        "semantic_exact": semantic_ok,
        "hard_resource_limits": resource_ok,
        "surprise_payload_unchanged": surprise_ok,
        "hostile_legacy_node_overflow_reproduced": hostile_legacy_overflow_seen,
        "hostile_pooled_program_valid": hostile_pooled_valid_seen,
        "hostile_4k_range_cone_at_or_below_2_1x": range_ok,
    }
    advance = all(gates.values())
    return {
        "schema": "cmpct-one-g02-bounded-surprise-pooling-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "productive_cases": list(PRODUCTIVE),
        "hostile_case": HOSTILE_CASE,
        "request_bytes": REQUEST_BYTES,
        "max_range_amplification": MAX_RANGE_AMPLIFICATION,
        "unchanged_limits": {
            "max_nodes": limits.max_nodes,
            "max_output_bytes": limits.max_output_bytes,
            "max_work_bytes": limits.max_work_bytes,
            "max_depth": limits.max_depth,
        },
        "gates": gates,
        "decision": "ADVANCE_BOUNDED_SURPRISE_POOLING" if advance else "REJECT_BOUNDED_SURPRISE_POOLING",
        "claim_boundary": (
            "already-discovered temporal plan graph granularity only; generic surprise/concat/ranged-Ref grammar; "
            "range evidence is explicitly unauthenticated and does not borrow wire indexing or selective integrity; "
            "no product-speed, arbitrary-discovery, format-release or v0.29/v0.30 superiority authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_BOUNDED_SURPRISE_POOLING" else 1)
