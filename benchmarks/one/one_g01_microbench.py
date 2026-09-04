"""ONE-G0.1 deterministic representation/resource microbenchmark.

This is an early semantic/overhead instrument, not a product-speed or v0.29/v0.30 win
claim. It charges the complete experimental wire, including Law/control, resource
limits, root identity and Surprise, and times the deliberately-simple Python reference
paths separately.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import time
from hashlib import sha256

from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

LIMITS = Limits(max_nodes=64, max_output_bytes=2 * 1024 * 1024, max_work_bytes=16 * 1024 * 1024, max_depth=16)
REPETITIONS = 11


def _root(ref: Ref, value: bytes) -> Root:
    return Root(ref, len(value), sha256(value).hexdigest())


def _random_bytes(size: int, seed: int) -> bytes:
    return random.Random(seed).randbytes(size)


def tiny_literal_case() -> tuple[Program, int]:
    value = b"x"
    return Program(nodes=(Node("surprise", surprise=value, declared_length=1),), roots={"tiny": _root(Ref(0), value)}, limits=LIMITS), 1


def tiny_repeat_case() -> tuple[Program, int]:
    value = b"A" * 16
    return Program(
        nodes=(Node("surprise", surprise=b"A", declared_length=1), Node("repeat", refs=(Ref(0),), count=16, declared_length=16)),
        roots={"tiny-repeat": _root(Ref(1), value)},
        limits=LIMITS,
    ), len(value)


def literal_case() -> tuple[Program, int]:
    value = _random_bytes(65536, 1)
    p = Program(nodes=(Node("surprise", surprise=value, declared_length=len(value)),), roots={"literal": _root(Ref(0), value)}, limits=LIMITS)
    return p, len(value)


def repeat_case() -> tuple[Program, int]:
    base = _random_bytes(64, 2)
    value = base * 1024
    p = Program(
        nodes=(Node("surprise", surprise=base, declared_length=64), Node("repeat", refs=(Ref(0),), count=1024, declared_length=len(value))),
        roots={"repeat": _root(Ref(1), value)},
        limits=LIMITS,
    )
    return p, len(value)


def sparse_case() -> tuple[Program, int]:
    value = b"\0" * 65536
    p = Program(nodes=(Node("fill", value=0, count=len(value), declared_length=len(value)),), roots={"sparse": _root(Ref(0), value)}, limits=LIMITS)
    return p, len(value)


def reuse_case() -> tuple[Program, int]:
    source = _random_bytes(65536, 3)
    clone = source
    p = Program(
        nodes=(Node("surprise", surprise=source, declared_length=len(source)), Node("concat", refs=(Ref(0),), declared_length=len(clone))),
        roots={"clone": _root(Ref(1), clone), "source": _root(Ref(0), source)},
        limits=LIMITS,
    )
    return p, len(source) + len(clone)


def multi_parent_case() -> tuple[Program, int]:
    left = _random_bytes(32768, 4)
    right = _random_bytes(32768, 5)
    child = bytes(a ^ b for a, b in zip(left, right))
    p = Program(
        nodes=(
            Node("surprise", surprise=left, declared_length=len(left)),
            Node("surprise", surprise=right, declared_length=len(right)),
            Node("xor", refs=(Ref(0), Ref(1)), declared_length=len(child)),
        ),
        roots={"child": _root(Ref(2), child), "left": _root(Ref(0), left), "right": _root(Ref(1), right)},
        limits=LIMITS,
    )
    return p, len(left) + len(right) + len(child)


CASES = {
    "tiny_literal": tiny_literal_case,
    "tiny_repeat": tiny_repeat_case,
    "literal": literal_case,
    "repeat": repeat_case,
    "sparse": sparse_case,
    "reuse": reuse_case,
    "multi_parent_xor": multi_parent_case,
}


def _median_ns(fn) -> int:
    values: list[int] = []
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        fn()
        values.append(time.perf_counter_ns() - start)
    return int(statistics.median(values))


def _throughput_mib_s(byte_count: int, elapsed_ns: int) -> float:
    return (byte_count / (1024 * 1024)) / (elapsed_ns / 1_000_000_000) if elapsed_ns else float("inf")


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, factory in CASES.items():
        program, logical_bytes = factory()
        wire, wire_stats = encode_program(program)
        decoded = decode_program(wire)
        outputs, eval_stats = evaluate(decoded)
        assert sum(len(value) for value in outputs.values()) == logical_bytes

        encode_ns = _median_ns(lambda: encode_program(program))
        decode_wire_ns = _median_ns(lambda: decode_program(wire))
        evaluate_ns = _median_ns(lambda: evaluate(decoded))
        rows.append(
            {
                "case": name,
                "logical_bytes": logical_bytes,
                "wire_bytes": wire_stats.total_bytes,
                "surprise_bytes": wire_stats.surprise_bytes,
                "control_integrity_bytes": wire_stats.control_integrity_bytes,
                "wire_minus_logical_bytes": wire_stats.total_bytes - logical_bytes,
                "wire_per_logical": wire_stats.total_bytes / logical_bytes,
                "reference_encode_median_ns": encode_ns,
                "reference_wire_decode_median_ns": decode_wire_ns,
                "reference_evaluate_median_ns": evaluate_ns,
                "reference_evaluate_mib_s": _throughput_mib_s(logical_bytes, evaluate_ns),
                "charged_work_bytes": eval_stats.work_bytes,
                "materialized_bytes": eval_stats.materialized_bytes,
                "max_depth": eval_stats.max_depth,
                "nodes_evaluated": eval_stats.nodes_evaluated,
            }
        )
    return {
        "schema": "cmpct-one-g01-microbench-v1",
        "experimental_version": "ONE-G0.1",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "claim_boundary": "reference semantic/complete-wire evidence only; not product-speed or comparator-release evidence",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
