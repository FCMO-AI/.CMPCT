"""ONE-G0.2 generic relation-granularity frontier.

Mission Lock / Referee
======================
The promoted bounded block-relation gate proves that non-redundant add8/XOR structure can
be nominated and exactly verified at 64-byte adjacency without reopening an unbounded
search. That is not yet a representation result. A dense 1 MiB stream of 64-byte
parent/child pairs would require 24,577 nodes if each verified pair were compiled naively
into the existing Surprise + Fill + add8/xor + root-Concat grammar, far above the current
4096-node resource contract.

Falsifiable hypothesis
----------------------
The useful relation principle survives if relation granularity grows: at least one block
size in 512..4096 bytes must encode the exact 1 MiB unique-parent relation corpus in the
*existing six-op ONE grammar*, remain within max_nodes=4096, and use <=55% of the literal
ONE wire bytes. No new opcode, widened node limit, interleave primitive, hidden codec, or
reader discovery is allowed.

Disproof / hostile rules
------------------------
- The 64-byte 1 MiB geometry must be reported as a node-budget failure, not silently
  admitted by raising limits.
- Every admissible candidate must reconstruct byte-exactly through the independent
  reference evaluator and preserve the same SHA-256 root.
- Both add8 and XOR are required; relation operands use only existing Surprise + Fill.
- Wire bytes come from experiments.one.wire.encode_program, including control/integrity.
- Native prepared-plan replay is diagnostic only: density cannot hide execution cost and
  speed cannot earn promotion by itself in this representation-granularity experiment.
- Inputs contain independently generated parent blocks and one transformed child each;
  exact duplicate aligned blocks invalidate the row.

This maps representation overhead, not a canonical format revision.
"""
from __future__ import annotations

from hashlib import sha256
import json
import random
import statistics
import time

from experiments.one.generic_execution_plan import compile_execution_plan
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.native_plan_bulk import execute_native_bulk_plan
from experiments.one.vm import evaluate
from experiments.one.wire import encode_program

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
BLOCKS = (64, 128, 256, 512, 1024, 2048, 4096)
OPS = ("add8", "xor")
MAX_NODES = 4096
MAX_1MIB_WIRE_RATIO = 0.55
REPLAY_REPETITIONS = 7


def _limits() -> Limits:
    return Limits(
        max_nodes=MAX_NODES,
        max_output_bytes=2 * 1024 * 1024,
        max_work_bytes=128 * 1024 * 1024,
        max_depth=8,
    )


def _root(node: int, data: bytes) -> dict[str, Root]:
    return {"root": Root(Ref(node), len(data), sha256(data).hexdigest())}


def _literal(data: bytes) -> Program:
    node = Node("surprise", surprise=data, declared_length=len(data))
    return Program((node,), _root(0, data), _limits())


def _case(op: str, size: int, block: int) -> tuple[bytes, list[tuple[bytes, int]]]:
    assert size % (2 * block) == 0
    rng = random.Random(0x6A7A0000 ^ size ^ (block << 4) ^ (0xA8 if op == "add8" else 0x58))
    pairs: list[tuple[bytes, int]] = []
    chunks: list[bytes] = []
    pair_count = size // (2 * block)
    for pair in range(pair_count):
        parent = bytes(rng.randrange(256) for _ in range(block))
        value = ((17 + 2 * pair) & 0xFF) or 19 if op == "add8" else ((0xA5 + 2 * pair) & 0xFF) or 0xA7
        child = (
            bytes((byte + value) & 0xFF for byte in parent)
            if op == "add8"
            else bytes(byte ^ value for byte in parent)
        )
        pairs.append((parent, value))
        chunks.extend((parent, child))
    return b"".join(chunks), pairs


def _has_duplicate_blocks(data: bytes, block: int) -> bool:
    seen: set[bytes] = set()
    for start in range(0, len(data), block):
        chunk = data[start : start + block]
        if chunk in seen:
            return True
        seen.add(chunk)
    return False


def _candidate(data: bytes, pairs: list[tuple[bytes, int]], op: str, block: int) -> Program | None:
    # One parent Surprise, one constant Fill, and one existing relation node per pair,
    # followed by one root Concat. Ref fan-in must obey the same max_nodes envelope.
    node_count = 3 * len(pairs) + 1
    root_ref_count = 2 * len(pairs)
    if node_count > MAX_NODES or root_ref_count > MAX_NODES:
        return None
    nodes: list[Node] = []
    root_refs: list[Ref] = []
    for parent, value in pairs:
        parent_id = len(nodes)
        nodes.append(Node("surprise", surprise=parent, declared_length=block))
        fill_id = len(nodes)
        nodes.append(Node("fill", count=block, value=value, declared_length=block))
        relation_id = len(nodes)
        nodes.append(Node(op, refs=(Ref(parent_id), Ref(fill_id)), declared_length=block))
        root_refs.extend((Ref(parent_id), Ref(relation_id)))
    root_id = len(nodes)
    nodes.append(Node("concat", refs=tuple(root_refs), declared_length=len(data)))
    return Program(tuple(nodes), _root(root_id, data), _limits())


def _median_native_replay(program: Program) -> tuple[int, int]:
    plan = compile_execution_plan(program)
    walls: list[int] = []
    cpus: list[int] = []
    # Warm native build and one semantic replay before timing.
    execute_native_bulk_plan(plan)
    for _ in range(REPLAY_REPETITIONS):
        w0, c0 = time.perf_counter_ns(), time.process_time_ns()
        execute_native_bulk_plan(plan)
        walls.append(time.perf_counter_ns() - w0)
        cpus.append(time.process_time_ns() - c0)
    return int(statistics.median(walls)), int(statistics.median(cpus))


def decide(rows: list[dict]) -> str:
    expected = {(size, block, op) for size in SIZES for block in BLOCKS for op in OPS}
    observed = {(row["size"], row["block"], row["op"]) for row in rows}
    if len(rows) != len(expected) or observed != expected:
        return "INVALIDATE_RELATION_GRANULARITY_FRONTIER"
    if any(row["duplicate_blocks"] for row in rows):
        return "INVALIDATE_RELATION_GRANULARITY_FRONTIER"
    if any(row["admissible"] and not row["semantic_ok"] for row in rows):
        return "INVALIDATE_RELATION_GRANULARITY_FRONTIER"

    # The fine-grain mismatch is part of the hypothesis: do not hide it by relaxing limits.
    fine_1mib = [row for row in rows if row["size"] == 1024 * 1024 and row["block"] == 64]
    if len(fine_1mib) != 2 or any(row["admissible"] for row in fine_1mib):
        return "INVALIDATE_RELATION_GRANULARITY_FRONTIER"

    decisive = [
        row for row in rows
        if row["size"] == 1024 * 1024 and row["block"] >= 512 and row["admissible"]
    ]
    for op in OPS:
        op_rows = [row for row in decisive if row["op"] == op]
        if not op_rows or min(row["wire_ratio_vs_literal"] for row in op_rows) > MAX_1MIB_WIRE_RATIO:
            return "HOLD_RELATION_GRANULARITY_FRONTIER"
    return "ADVANCE_RELATION_GRANULARITY_FRONTIER"


def main() -> int:
    rows: list[dict] = []
    literal_cache: dict[tuple[str, int, int], tuple[Program, int, int, int]] = {}
    for size in SIZES:
        for block in BLOCKS:
            if size % (2 * block):
                raise AssertionError((size, block))
            for op in OPS:
                data, pairs = _case(op, size, block)
                duplicate = _has_duplicate_blocks(data, block)
                literal = _literal(data)
                literal_wire, literal_stats = encode_program(literal)
                literal_out, literal_eval = evaluate(literal)
                if literal_out["root"] != data:
                    raise AssertionError("literal semantic mismatch")
                candidate = _candidate(data, pairs, op, block)
                row = {
                    "size": size,
                    "block": block,
                    "op": op,
                    "pair_count": len(pairs),
                    "expected_node_count": 3 * len(pairs) + 1,
                    "duplicate_blocks": duplicate,
                    "admissible": candidate is not None,
                    "literal_wire_bytes": len(literal_wire),
                    "literal_control_integrity_bytes": literal_stats.control_integrity_bytes,
                    "semantic_ok": False,
                    "candidate_wire_bytes": None,
                    "candidate_control_integrity_bytes": None,
                    "wire_ratio_vs_literal": None,
                    "wire_ratio_vs_source": None,
                    "work_ratio_vs_literal": None,
                    "materialized_ratio_vs_literal": None,
                    "native_wall_ratio_vs_literal": None,
                    "native_cpu_ratio_vs_literal": None,
                }
                if candidate is not None:
                    wire, stats = encode_program(candidate)
                    outputs, ev = evaluate(candidate)
                    row["semantic_ok"] = outputs["root"] == data
                    row["candidate_wire_bytes"] = len(wire)
                    row["candidate_control_integrity_bytes"] = stats.control_integrity_bytes
                    row["wire_ratio_vs_literal"] = len(wire) / len(literal_wire)
                    row["wire_ratio_vs_source"] = len(wire) / len(data)
                    row["work_ratio_vs_literal"] = ev.work_bytes / literal_eval.work_bytes
                    row["materialized_ratio_vs_literal"] = ev.materialized_bytes / max(1, literal_eval.materialized_bytes)

                    # Only the 1 MiB feasible frontier gets hosted replay timing. This is
                    # diagnostic, not a promotion gate, and keeps the experiment focused.
                    if size == 1024 * 1024:
                        lw, lc = _median_native_replay(literal)
                        cw, cc = _median_native_replay(candidate)
                        row["native_wall_ratio_vs_literal"] = cw / lw
                        row["native_cpu_ratio_vs_literal"] = cc / lc
                rows.append(row)

    decision = decide(rows)
    decisive = [row for row in rows if row["size"] == 1024 * 1024 and row["admissible"]]
    payload = {
        "experiment": "ONE-G0.2 generic relation granularity frontier",
        "decision": decision,
        "max_nodes": MAX_NODES,
        "max_1mib_wire_ratio": MAX_1MIB_WIRE_RATIO,
        "replay_repetitions": REPLAY_REPETITIONS,
        "best_1mib_add8_wire_ratio": min(row["wire_ratio_vs_literal"] for row in decisive if row["op"] == "add8"),
        "best_1mib_xor_wire_ratio": min(row["wire_ratio_vs_literal"] for row in decisive if row["op"] == "xor"),
        "rows": rows,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if decision == "ADVANCE_RELATION_GRANULARITY_FRONTIER" else 1


if __name__ == "__main__":
    raise SystemExit(main())
