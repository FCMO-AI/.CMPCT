"""ONE-G0.2 selective-Crystallization economics falsifier.

Preregistered by ONE_G02_CRYSTALLIZATION_ECONOMICS_PREREG_2026-09-08.md.
This benchmark studies already-discovered generic Law + Surprise plans. It has no
v0.29/v0.30 or product-speed authority.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os

from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.range_vm import reconstruct_range_unverified
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = (64 * 1024, 256 * 1024)
SPAN_WIDTHS = (8, 9, 10, 12, 16, 24, 32, 48, 64, 96, 128, 256, 512, 1024, 2048, 4096)


def _source(size: int) -> bytes:
    return bytes(((index * 131) ^ (index >> 3) ^ 0xA7) & 0xFF for index in range(size))


def _alternating_plan(source: bytes, span_width: int):
    target = bytearray(source)
    plan = []
    reused = 0
    changed = 0
    cursor = 0
    span_index = 0
    while cursor < len(source):
        take = min(span_width, len(source) - cursor)
        if span_index % 2 == 0:
            plan.append(("ref", cursor, take, b""))
            reused += take
        else:
            for offset in range(cursor, cursor + take):
                target[offset] ^= ((span_index * 29 + offset * 7) | 1) & 0xFF
            payload = bytes(target[cursor : cursor + take])
            plan.append(("surprise", 0, take, payload))
            changed += take
        cursor += take
        span_index += 1
    return bytes(target), tuple(plan), reused, changed


def _previous_root(source: bytes) -> Root:
    return Root(Ref(0), len(source), sha256(source).hexdigest())


def _crystallized_program(source: bytes, target: bytes, limits: Limits) -> Program:
    nodes = (
        Node("surprise", surprise=source),
        Node("surprise", surprise=target),
    )
    return Program(
        nodes,
        {
            "previous": Root(Ref(0), len(source), sha256(source).hexdigest()),
            "current": Root(Ref(1), len(target), sha256(target).hexdigest()),
        },
        limits,
    )


def _measure(program: Program, source: bytes, target: bytes):
    program.validate_shape()
    wire, wire_stats = encode_program(program)
    decoded = decode_program(wire)
    outputs, vm_stats = evaluate(decoded)
    exact = outputs == {"previous": source, "current": target}
    value, range_stats = reconstruct_range_unverified(decoded, "current", 0, len(target))
    range_exact = value == target
    encoded_refs = sum(len(node.refs) for node in decoded.nodes)
    return {
        "wire_bytes": wire_stats.total_bytes,
        "surprise_bytes": wire_stats.surprise_bytes,
        "control_integrity_bytes": wire_stats.control_integrity_bytes,
        "program_nodes": len(decoded.nodes),
        "encoded_refs": encoded_refs,
        "full_evaluate_work_bytes": vm_stats.work_bytes,
        "full_evaluate_materialized_bytes": vm_stats.materialized_bytes,
        "current_range_work_bytes": range_stats.work_bytes,
        "current_range_materialized_bytes": range_stats.materialized_bytes,
        "current_range_nodes_touched": range_stats.nodes_touched,
        "exact_reconstruction": exact and range_exact,
    }


def run():
    limits = Limits()
    rows = []
    semantic_ok = True
    pre_cap_crossovers = []

    for size in SIZES:
        source = _source(size)
        previous = _previous_root(source)
        for width in SPAN_WIDTHS:
            target, plan, reused_bytes, changed_bytes = _alternating_plan(source, width)
            retained, pool_stats = program_from_plan_pooled(
                source,
                target,
                plan,
                previous,
                sha256(target).hexdigest(),
                limits=limits,
            )
            crystallized = _crystallized_program(source, target, limits)
            retained_metrics = _measure(retained, source, target)
            crystallized_metrics = _measure(crystallized, source, target)
            exact = retained_metrics["exact_reconstruction"] and crystallized_metrics["exact_reconstruction"]
            semantic_ok &= exact
            safety_fallback = pool_stats.crystallized_groups > 0
            wire_delta = retained_metrics["wire_bytes"] - crystallized_metrics["wire_bytes"]
            net_saved = -wire_delta
            is_pre_cap_crossover = exact and not safety_fallback and wire_delta >= 0
            if is_pre_cap_crossover:
                pre_cap_crossovers.append((size, width, wire_delta))

            rows.append({
                "relation_bytes": size,
                "span_width": width,
                "segments": len(plan),
                "reused_bytes": reused_bytes,
                "changed_bytes": changed_bytes,
                "reuse_fraction": reused_bytes / size,
                "max_group_refs_discovered": pool_stats.max_group_refs,
                "reader_ref_cap": limits.max_nodes,
                "safety_crystallized_groups": pool_stats.crystallized_groups,
                "safety_crystallized_bytes": pool_stats.crystallized_bytes,
                "retained": retained_metrics,
                "crystallized": crystallized_metrics,
                "wire_delta_retained_minus_crystallized": wire_delta,
                "net_bytes_saved_by_retaining_law": net_saved,
                "retained_control_bytes_per_reused_byte": (
                    retained_metrics["control_integrity_bytes"] / reused_bytes if reused_bytes else None
                ),
                "retained_refs_per_reused_byte": (
                    retained_metrics["encoded_refs"] / reused_bytes if reused_bytes else None
                ),
                "pre_hard_cap_crossover": is_pre_cap_crossover,
                "semantic_exact": exact,
            })

    gates = {
        "all_rows_semantically_exact": semantic_ok,
        "matrix_contains_pre_hard_cap_rows": any(
            row["max_group_refs_discovered"] <= limits.max_nodes and not row["safety_crystallized_groups"]
            for row in rows
        ),
    }
    valid = all(gates.values())
    if not valid:
        decision = "INVALID_CRYSTALLIZATION_ECONOMICS_EXPERIMENT"
    elif pre_cap_crossovers:
        decision = "PRE_HARD_CAP_CROSSOVER_FOUND"
    else:
        decision = "NO_PRE_HARD_CAP_CROSSOVER_ON_MATRIX"

    return {
        "schema": "cmpct-one-g02-crystallization-economics-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "span_widths": list(SPAN_WIDTHS),
        "limits": {
            "max_nodes": limits.max_nodes,
            "max_output_bytes": limits.max_output_bytes,
            "max_work_bytes": limits.max_work_bytes,
            "max_depth": limits.max_depth,
        },
        "gates": gates,
        "decision": decision,
        "pre_hard_cap_crossovers": [
            {"relation_bytes": size, "span_width": width, "wire_delta_bytes": delta}
            for size, width, delta in pre_cap_crossovers
        ],
        "claim_boundary": (
            "already-discovered synthetic 50%-reuse temporal Law economics only; same previous/source accounting; "
            "generic Surprise/ranged-Ref/concat grammar; no product speed, arbitrary discovery, format release, "
            "or v0.29/v0.30 superiority authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1 if result["decision"].startswith("INVALID") else 0)
