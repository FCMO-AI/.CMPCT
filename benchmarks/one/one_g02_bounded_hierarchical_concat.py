"""ONE-G0.2 bounded hierarchical concat for fragmented generic relations."""
from __future__ import annotations

from hashlib import sha256
import json
import os

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
CASES = ("shift_plus1_damage_quarter", "fragmented_every96")
MAX_WIRE_OVERHEAD = 0.005
MAX_WORK_AMP = 2.10
MAX_DEPTH = 4
OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}


def _root(node: int, data: bytes) -> Root:
    return Root(Ref(node), len(data), sha256(data).hexdigest())


def _parts(source: bytes, target: bytes):
    nodes = [Node("surprise", surprise=source)]
    parts: list[tuple[Ref, int]] = []
    i = 0
    while i < len(target):
        if i > 0 and target[i] == source[i-1]:
            start = i
            i += 1
            while i < len(target) and target[i] == source[i-1]:
                i += 1
            length = i - start
            parts.append((Ref(0, start-1, length), length))
        else:
            start = i
            i += 1
            while i < len(target) and not (i > 0 and target[i] == source[i-1]):
                i += 1
            payload = target[start:i]
            node_id = len(nodes)
            nodes.append(Node("surprise", surprise=payload))
            parts.append((Ref(node_id), len(payload)))
    return nodes, parts


def _flat(source: bytes, target: bytes) -> Program:
    nodes, parts = _parts(source, target)
    nodes.append(Node("concat", refs=tuple(r for r, _ in parts), declared_length=len(target)))
    return Program(tuple(nodes), {"previous": _root(0, source), "current": _root(len(nodes)-1, target)}, Limits())


def _hierarchical(source: bytes, target: bytes):
    limits = Limits()
    nodes, parts = _parts(source, target)
    fanout = limits.max_nodes
    depth = 1
    level = parts
    while len(level) > fanout:
        nxt: list[tuple[Ref, int]] = []
        for off in range(0, len(level), fanout):
            chunk = level[off:off+fanout]
            length = sum(n for _, n in chunk)
            node_id = len(nodes)
            nodes.append(Node("concat", refs=tuple(r for r, _ in chunk), declared_length=length))
            nxt.append((Ref(node_id), length))
        level = nxt
        depth += 1
    nodes.append(Node("concat", refs=tuple(r for r, _ in level), declared_length=len(target)))
    program = Program(tuple(nodes), {"previous": _root(0, source), "current": _root(len(nodes)-1, target)}, limits)
    return program, depth


def _max_concat_refs(program: Program) -> int:
    return max((len(n.refs) for n in program.nodes if n.op == "concat"), default=0)


def run():
    rows = []
    passed = True
    saw_flat_rejection = False
    for size in SIZES:
        cases = _relation_cases(size)
        for case in CASES:
            source, target, expected, shift = cases[case]
            assert expected and shift == 1
            flat = _flat(source, target)
            hier, depth = _hierarchical(source, target)
            flat_wire, flat_ws = encode_program(flat)
            hier_wire, hier_ws = encode_program(hier)
            flat_out, flat_vm = evaluate(flat)
            if flat_out != {"previous": source, "current": target}:
                raise AssertionError("ideal flat in-memory semantics mismatch")
            flat_decode_ok = True
            try:
                flat_dec = decode_program(flat_wire)
                flat_dec_out, _ = evaluate(flat_dec)
                flat_decode_ok = flat_dec_out == {"previous": source, "current": target}
            except OneError:
                flat_decode_ok = False
            hier_dec = decode_program(hier_wire)
            hier_out, hier_vm = evaluate(hier_dec)
            exact = hier_out == {"previous": source, "current": target}
            flat_refs = _max_concat_refs(flat)
            required = flat_refs > hier.limits.max_nodes
            if required and not flat_decode_ok:
                saw_flat_rejection = True
            surprise_equal = flat_ws.surprise_bytes == hier_ws.surprise_bytes
            max_refs = _max_concat_refs(hier)
            caps_ok = max_refs <= hier.limits.max_nodes and len(hier.nodes) <= hier.limits.max_nodes
            ops_ok = all(n.op in OPS for n in hier.nodes)
            wire_overhead = (hier_ws.total_bytes - flat_ws.total_bytes) / flat_ws.total_bytes
            no_gratuitous = required or hier_wire == flat_wire
            overhead_ok = (not required and wire_overhead == 0.0) or (required and wire_overhead <= MAX_WIRE_OVERHEAD)
            work_amp = hier_vm.work_bytes / max(1, flat_vm.work_bytes)
            depth_ok = depth <= MAX_DEPTH
            work_ok = (not required) or work_amp <= MAX_WORK_AMP
            row_pass = all((exact, surprise_equal, caps_ok, ops_ok, no_gratuitous, overhead_ok, depth_ok, work_ok))
            passed &= row_pass
            rows.append({
                "relation_bytes": size,
                "case": case,
                "flat_concat_refs": flat_refs,
                "flat_bounded_decode_ok": flat_decode_ok,
                "hierarchy_required": required,
                "hierarchy_depth": depth,
                "hierarchical_nodes": len(hier.nodes),
                "hierarchical_max_concat_refs": max_refs,
                "flat_wire_bytes": flat_ws.total_bytes,
                "hierarchical_wire_bytes": hier_ws.total_bytes,
                "wire_overhead_fraction": wire_overhead,
                "flat_surprise_bytes": flat_ws.surprise_bytes,
                "hierarchical_surprise_bytes": hier_ws.surprise_bytes,
                "flat_work_bytes": flat_vm.work_bytes,
                "hierarchical_work_bytes": hier_vm.work_bytes,
                "work_amplification": work_amp,
                "hierarchical_materialized_bytes": hier_vm.materialized_bytes,
                "hierarchical_nodes_evaluated": hier_vm.nodes_evaluated,
                "exact_reconstruction": exact,
                "row_pass": row_pass,
            })
    passed &= saw_flat_rejection
    return {
        "schema": "cmpct-one-g02-bounded-hierarchical-concat-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "saw_required_flat_bounded_decoder_rejection": saw_flat_rejection,
        "decision": "advance_bounded_hierarchical_concat" if passed else "hold_bounded_hierarchical_concat",
        "claim_boundary": "bounded generic concat representation only; discovery, writer admission, native speed, auth and comparator authority excluded",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_bounded_hierarchical_concat" else 1)
