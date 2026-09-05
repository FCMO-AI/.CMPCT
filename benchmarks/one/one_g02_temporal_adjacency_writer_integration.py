"""ONE-G0.2 temporal-adjacency writer integration.

Frozen by ONE_G02_TEMPORAL_ADJACENCY_WRITER_PREREG_2026-09-05.md.
Adjacent-version identity is supplied by writer context. Accepted +1 relations are
compiled only through the existing generic ONE grammar: ranged Ref plus Surprise
islands under concat. No reader-side relation operation exists.
"""
from __future__ import annotations

import ctypes
from hashlib import sha256
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
ROUNDS = 31
MAX_ROW_RATIO = 1.03
MAX_AGG_RATIO = 0.92


def _build_native():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-temporal-writer-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"),
        str(here / "one_g02_shift_relation_sparse_gate_kernel.c"),
        str(here / "one_g02_shift_relation_amortization_safe_gate_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    baseline = c.one_g02_shift_relation_safe_dispatch
    baseline.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                         ctypes.c_size_t, ctypes.POINTER(Result)]
    baseline.restype = ctypes.c_int
    candidate = c.one_g02_shift_relation_amortization_safe_gate
    candidate.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                          ctypes.c_size_t, ctypes.POINTER(Result),
                          ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_int)]
    candidate.restype = ctypes.c_int
    return baseline, candidate, td


def _root(node: int, data: bytes) -> Root:
    return Root(Ref(node), len(data), sha256(data).hexdigest())


def _literal_program(source: bytes, target: bytes) -> Program:
    nodes = (Node("surprise", surprise=source), Node("surprise", surprise=target))
    return Program(nodes, {"previous": _root(0, source), "current": _root(1, target)}, Limits())


def _relation_program_plus1(source: bytes, target: bytes) -> Program:
    """Compile target[i] relation to source[i-1] as generic concat refs/surprises."""
    if len(source) != len(target) or not source:
        return _literal_program(source, target)
    nodes: list[Node] = [Node("surprise", surprise=source)]
    parts: list[Ref] = []
    i = 0
    n = len(target)
    while i < n:
        if i > 0 and target[i] == source[i - 1]:
            start = i
            i += 1
            while i < n and target[i] == source[i - 1]:
                i += 1
            parts.append(Ref(0, start - 1, i - start))
        else:
            start = i
            i += 1
            while i < n and not (i > 0 and target[i] == source[i - 1]):
                i += 1
            node_id = len(nodes)
            nodes.append(Node("surprise", surprise=target[start:i]))
            parts.append(Ref(node_id))
    nodes.append(Node("concat", refs=tuple(parts), declared_length=n))
    target_node = len(nodes) - 1
    limits = Limits(max_nodes=4096, max_output_bytes=64*1024*1024,
                    max_work_bytes=256*1024*1024, max_depth=64)
    return Program(tuple(nodes), {"previous": _root(0, source), "current": _root(target_node, target)}, limits)


def _compile_program(source: bytes, target: bytes, enabled: bool, best_shift: int) -> tuple[Program, bool]:
    if enabled and best_shift == 1:
        return _relation_program_plus1(source, target), True
    return _literal_program(source, target), False


def _call_baseline(fn, src_arr, dst_arr, n):
    r = Result()
    rc = fn(src_arr, dst_arr, n, ctypes.byref(r))
    if rc < 0:
        raise RuntimeError(f"baseline relation dispatch failed: {rc}")
    return r, 0, False


def _call_candidate(fn, src_arr, dst_arr, n):
    r = Result(); reads = ctypes.c_uint64(); used = ctypes.c_int()
    rc = fn(src_arr, dst_arr, n, ctypes.byref(r), ctypes.byref(reads), ctypes.byref(used))
    if rc < 0:
        raise RuntimeError(f"candidate relation dispatch failed: {rc}")
    return r, int(reads.value), bool(used.value)


def _writer_once(fn, source: bytes, target: bytes, candidate: bool):
    src = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    dst = (ctypes.c_uint8 * len(target)).from_buffer_copy(target)
    if candidate:
        result, reads, used = _call_candidate(fn, src, dst, len(source))
    else:
        result, reads, used = _call_baseline(fn, src, dst, len(source))
    enabled = int(result.exact_proofs) >= 4
    program, relation_compiled = _compile_program(source, target, enabled, int(result.best_shift))
    wire, stats = encode_program(program)
    return wire, stats, result, reads, used, relation_compiled, program


def _verify(wire: bytes, source: bytes, target: bytes):
    decoded = decode_program(wire)
    outputs, stats = evaluate(decoded)
    if outputs != {"previous": source, "current": target}:
        raise AssertionError("ONE temporal writer reconstruction mismatch")
    return stats


def run():
    baseline_fn, candidate_fn, td = _build_native()
    rows = []
    try:
        ratios = []
        all_exact = all_roundtrip = all_wire_equal = all_bytes = all_rows = True
        aggregate_baseline_samples = []
        aggregate_candidate_samples = []
        frozen = [(size, case, vals) for size in SIZES for case, vals in _relation_cases(size).items()]

        # Full mixed-stream timing. Interleave order by round to limit drift bias.
        for round_id in range(ROUNDS):
            order = (("baseline", baseline_fn, False), ("candidate", candidate_fn, True))
            if round_id & 1:
                order = tuple(reversed(order))
            for name, fn, is_candidate in order:
                t0 = time.perf_counter_ns()
                for _size, _case, (source, target, _expected, _shift) in frozen:
                    _writer_once(fn, source, target, is_candidate)
                elapsed = time.perf_counter_ns() - t0
                (aggregate_candidate_samples if is_candidate else aggregate_baseline_samples).append(elapsed)

        for size in SIZES:
            size_b, size_c = [], []
            case_data = _relation_cases(size)
            for round_id in range(ROUNDS):
                order = ((baseline_fn, False), (candidate_fn, True))
                if round_id & 1:
                    order = tuple(reversed(order))
                for fn, is_candidate in order:
                    t0 = time.perf_counter_ns()
                    for source, target, _expected, _shift in case_data.values():
                        _writer_once(fn, source, target, is_candidate)
                    elapsed = time.perf_counter_ns() - t0
                    (size_c if is_candidate else size_b).append(elapsed)
            bmed = float(statistics.median(size_b)); cmed = float(statistics.median(size_c))
            ratio = cmed / bmed
            ratios.append(ratio)
            all_rows &= ratio <= MAX_ROW_RATIO

            for case, (source, target, expected_enable, expected_shift) in case_data.items():
                bwire, bstats, br, _brd, _bu, bcompiled, _bp = _writer_once(baseline_fn, source, target, False)
                cwire, cstats, cr, reads, used, ccompiled, _cp = _writer_once(candidate_fn, source, target, True)
                ben = int(br.exact_proofs) >= 4; cen = int(cr.exact_proofs) >= 4
                exact = ben == cen and (not ben or int(br.best_shift) == int(cr.best_shift))
                all_exact &= exact
                wire_equal = bwire == cwire
                all_wire_equal &= wire_equal
                bytes_equal = (bstats.total_bytes == cstats.total_bytes and
                               bstats.surprise_bytes == cstats.surprise_bytes)
                all_bytes &= bytes_equal
                bvm = _verify(bwire, source, target); cvm = _verify(cwire, source, target)
                all_roundtrip &= True
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "expected_enable": expected_enable,
                    "baseline_enabled": ben,
                    "candidate_enabled": cen,
                    "baseline_best_shift": int(br.best_shift),
                    "candidate_best_shift": int(cr.best_shift),
                    "classification_exact": exact,
                    "used_sparse_gate": used,
                    "gate_compared_bytes": reads,
                    "baseline_relation_compiled": bcompiled,
                    "candidate_relation_compiled": ccompiled,
                    "wire_equal": wire_equal,
                    "wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "control_integrity_bytes": cstats.control_integrity_bytes,
                    "stored_over_two_literal_inputs": cstats.total_bytes / (2 * size),
                    "reader_work_bytes": cvm.work_bytes,
                    "reader_materialized_bytes": cvm.materialized_bytes,
                    "reader_nodes_evaluated": cvm.nodes_evaluated,
                })

            rows.append({
                "relation_bytes": size,
                "case": "__size_timing__",
                "baseline_median_ns_five_transition_writer": bmed,
                "candidate_median_ns_five_transition_writer": cmed,
                "candidate_over_baseline": ratio,
                "row_cost_pass": ratio <= MAX_ROW_RATIO,
            })

        agg_b = float(statistics.median(aggregate_baseline_samples))
        agg_c = float(statistics.median(aggregate_candidate_samples))
        agg_ratio = agg_c / agg_b
        passed = all_exact and all_roundtrip and all_wire_equal and all_bytes and all_rows and agg_ratio <= MAX_AGG_RATIO
        return {
            "schema": "cmpct-one-g02-temporal-adjacency-writer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_rounds": ROUNDS,
            "frozen_max_row_ratio": MAX_ROW_RATIO,
            "frozen_max_aggregate_ratio": MAX_AGG_RATIO,
            "aggregate_baseline_median_ns": agg_b,
            "aggregate_candidate_median_ns": agg_c,
            "aggregate_candidate_over_baseline": agg_ratio,
            "median_size_ratio": float(statistics.median(ratios)),
            "decision": "advance_temporal_adjacency_writer_gate" if passed else "hold_temporal_writer_gate",
            "claim_boundary": "research adjacent-version writer integration only; Python object/wire construction is not product-speed authority and arbitrary pair discovery remains outside scope",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_temporal_adjacency_writer_gate" else 1)
