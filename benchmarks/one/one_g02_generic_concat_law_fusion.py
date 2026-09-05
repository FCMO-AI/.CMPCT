"""ONE-G0.2 generic concat Law-fusion execution falsifier."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os

from benchmarks.one.one_g02_bounded_hierarchical_concat import CASES, SIZES, _flat, _hierarchical
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.ir import OneError, Program, Ref
from experiments.one.range_vm import reconstruct_range_unverified
from experiments.one.vm import _preflight
from experiments.one.wire import decode_program, encode_program


@dataclass(frozen=True)
class FusedStats:
    requested_bytes: int
    materialized_bytes: int
    work_bytes: int
    nodes_touched: int
    max_depth: int


class FusedConcatEvaluator:
    """Fuse nested concat traversal while retaining ordinary leaf accounting."""

    def __init__(self, program: Program):
        program.validate_shape()
        self.program = program
        self.pre = _preflight(program)
        self.work = 0
        self.materialized = 0
        self.touched: set[int] = set()
        self.active: set[tuple[int, int, int]] = set()
        self.max_depth_seen = 0

    def _charge(self, *, work: int = 0, materialized: int = 0) -> None:
        self.work += work
        self.materialized += materialized
        if self.work > self.program.limits.max_work_bytes:
            raise OneError("fused concat work exceeds declared limit")

    def _ref_length(self, ref: Ref) -> int:
        source_len = self.pre.lengths[ref.node]
        end = source_len if ref.length is None else ref.start + ref.length
        if ref.start > source_len or end < ref.start or end > source_len:
            raise OneError("range exceeds referenced output")
        return end - ref.start

    @staticmethod
    def _overlap(start: int, length: int, part_start: int, part_len: int):
        lo = max(start, part_start)
        hi = min(start + length, part_start + part_len)
        return None if hi <= lo else (lo - part_start, hi - lo)

    def _emit_ref(self, ref: Ref, start: int, length: int, depth: int, out: bytearray) -> None:
        width = self._ref_length(ref)
        if start < 0 or length < 0 or start + length > width:
            raise OneError("requested subrange exceeds reference")
        self._emit_node(ref.node, ref.start + start, length, depth, out)

    def _emit_node(self, node_id: int, start: int, length: int, depth: int, out: bytearray) -> None:
        if depth > self.program.limits.max_depth:
            raise OneError("dependency depth exceeds declared limit")
        node_len = self.pre.lengths[node_id]
        if start < 0 or length < 0 or start + length > node_len:
            raise OneError("requested range exceeds node output")
        if length == 0:
            return
        key = (node_id, start, length)
        if key in self.active:
            raise OneError("cycle in fused concat traversal")
        self.active.add(key)
        self.touched.add(node_id)
        self.max_depth_seen = max(self.max_depth_seen, depth)
        try:
            node = self.program.nodes[node_id]
            if node.op == "surprise":
                piece = node.surprise[start:start + length]
                if len(piece) != length:
                    raise OneError("Surprise range mismatch")
                self._charge(work=length, materialized=length)
                out += piece
                return
            if node.op != "concat":
                raise OneError(f"frozen concat-fusion corpus received unsupported op {node.op!r}")
            cursor = 0
            emitted_before = len(out)
            for ref in node.refs:
                part_len = self._ref_length(ref)
                overlap = self._overlap(start, length, cursor, part_len)
                if overlap is not None:
                    rel, take = overlap
                    self._emit_ref(ref, rel, take, depth + 1, out)
                cursor += part_len
            if node.surprise:
                overlap = self._overlap(start, length, cursor, len(node.surprise))
                if overlap is not None:
                    rel, take = overlap
                    piece = node.surprise[rel:rel + take]
                    self._charge(work=take, materialized=take)
                    out += piece
            if len(out) - emitted_before != length:
                raise OneError("fused concat coverage mismatch")
            if depth == 1:
                self._charge(work=length, materialized=length)
        finally:
            self.active.remove(key)

    def reconstruct_current(self) -> tuple[bytes, FusedStats]:
        root = self.program.roots["current"]
        out = bytearray()
        self._emit_ref(root.ref, 0, root.length, 1, out)
        value = bytes(out)
        if len(value) != root.length:
            raise OneError("fused root length mismatch")
        return value, FusedStats(root.length, self.materialized, self.work, len(self.touched), self.max_depth_seen)


def run():
    rows = []
    passed = True
    saw_required = False
    for size in SIZES:
        cases = _relation_cases(size)
        for case in CASES:
            source, target, expected, shift = cases[case]
            assert expected and shift == 1
            flat = _flat(source, target)
            hier, hierarchy_depth = _hierarchical(source, target)
            wire, ws = encode_program(hier)
            decoded = decode_program(wire)
            before_wire = encode_program(decoded)[0]
            flat_value, flat_stats = reconstruct_range_unverified(flat, "current", 0, len(target))
            hier_value, hier_stats = reconstruct_range_unverified(decoded, "current", 0, len(target))
            fused_value, fused_stats = FusedConcatEvaluator(decoded).reconstruct_current()
            after_wire = encode_program(decoded)[0]
            required = hierarchy_depth > 1
            saw_required |= required
            exact = flat_value == hier_value == fused_value == target
            unchanged = before_wire == wire == after_wire
            if required:
                accounting_match = (fused_stats.work_bytes == flat_stats.work_bytes and fused_stats.materialized_bytes == flat_stats.materialized_bytes)
                strict_improvement = (fused_stats.work_bytes < hier_stats.work_bytes and fused_stats.materialized_bytes < hier_stats.materialized_bytes)
            else:
                accounting_match = (fused_stats.work_bytes == hier_stats.work_bytes == flat_stats.work_bytes and fused_stats.materialized_bytes == hier_stats.materialized_bytes == flat_stats.materialized_bytes)
                strict_improvement = True
            resource_ok = fused_stats.work_bytes <= decoded.limits.max_work_bytes and fused_stats.max_depth <= decoded.limits.max_depth
            row_pass = exact and unchanged and accounting_match and strict_improvement and resource_ok
            passed &= row_pass
            rows.append({
                "relation_bytes": size, "case": case, "hierarchy_required": required,
                "wire_bytes": ws.total_bytes, "surprise_bytes": ws.surprise_bytes,
                "hierarchical_range_work_bytes": hier_stats.work_bytes,
                "ideal_flat_range_work_bytes": flat_stats.work_bytes,
                "fused_range_work_bytes": fused_stats.work_bytes,
                "hierarchical_range_materialized_bytes": hier_stats.materialized_bytes,
                "ideal_flat_range_materialized_bytes": flat_stats.materialized_bytes,
                "fused_range_materialized_bytes": fused_stats.materialized_bytes,
                "fused_over_hierarchical_work": fused_stats.work_bytes / max(1, hier_stats.work_bytes),
                "fused_over_hierarchical_materialized": fused_stats.materialized_bytes / max(1, hier_stats.materialized_bytes),
                "fused_nodes_touched": fused_stats.nodes_touched, "fused_max_depth": fused_stats.max_depth,
                "exact_reconstruction": exact, "wire_unchanged": unchanged, "row_pass": row_pass,
            })
    passed &= saw_required
    return {
        "schema": "cmpct-one-g02-generic-concat-law-fusion-v1", "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "saw_hierarchy_required": saw_required,
        "decision": "advance_generic_concat_law_fusion" if passed else "hold_generic_concat_law_fusion",
        "claim_boundary": "modeled generic concat execution only; stored representation unchanged; no native speed/auth/discovery/comparator claim",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_generic_concat_law_fusion" else 1)
