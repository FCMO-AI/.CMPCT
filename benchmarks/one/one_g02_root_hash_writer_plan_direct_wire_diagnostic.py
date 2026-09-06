"""Diagnostic-only first-failure locator for the ONE-G0.2 plan-direct writer.

Frozen by ONE_G02_ROOT_HASH_WRITER_PLAN_DIRECT_WIRE_DIAGNOSTIC_PREREG_2026-09-06.md.
No timing and no promotion authority.
"""
from __future__ import annotations

import ctypes
import json

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    CONTROLS,
    PRODUCTIVE,
    SIZES,
    Segment,
    _build_native,
    _oracle_plan,
    _plan_signature,
    _relation_cases,
)
from benchmarks.one.one_g02_root_hash_writer_coarse_attribution import (
    _writer_once_direct_unprofiled,
)
from benchmarks.one.one_g02_root_hash_writer_plan_direct_wire import _candidate_once
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program


def _first_diff(a: bytes, b: bytes):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else None


def _context(data: bytes, off: int | None, radius: int = 24) -> str | None:
    if off is None:
        return None
    lo = max(0, off - radius)
    hi = min(len(data), off + radius + 1)
    return data[lo:hi].hex()


def _program_signature(program):
    nodes = []
    for idx, node in enumerate(program.nodes):
        nodes.append({
            "index": idx,
            "op": node.op,
            "declared_length": node.declared_length,
            "surprise_len": len(node.surprise),
            "refs": [
                {"node": r.node, "start": r.start, "length": r.length}
                for r in node.refs
            ],
            "count": node.count,
            "value": node.value,
        })
    roots = {
        name: {
            "node": root.ref.node,
            "start": root.ref.start,
            "ref_length": root.ref.length,
            "length": root.length,
            "sha256": root.sha256,
        }
        for name, root in sorted(program.roots.items())
    }
    return {"nodes": nodes, "roots": roots}


def run():
    admission_fn, segment_fn, td = _build_native()
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, _expected_enable, _expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)

                baseline = _writer_once_direct_unprofiled(*ctx)
                candidate = _candidate_once(*ctx)
                bwire, bstats, bprogram, bresult, _breads, _bused, benabled, bplan, btraffic, bsegments, bdepth = baseline
                cwire, cstats, cresult, _creads, _cused, cenabled, cplan, ctraffic, csegments, cdepth, cnode_count = candidate

                oracle_equal = (not benabled) or (
                    _plan_signature(bplan) == _plan_signature(_oracle_plan(source, target))
                )
                try:
                    decoded_candidate = decode_program(cwire)
                    candidate_outputs, _ = evaluate(decoded_candidate)
                    candidate_exact = candidate_outputs == {"previous": source, "current": target}
                    candidate_decode_error = None
                    candidate_program_sig = _program_signature(decoded_candidate)
                except Exception as exc:  # diagnostic evidence only
                    decoded_candidate = None
                    candidate_exact = False
                    candidate_decode_error = f"{type(exc).__name__}: {exc}"
                    candidate_program_sig = None

                checks = {
                    "wire_equal": bwire == cwire,
                    "stats_equal": bstats == cstats,
                    "enabled_equal": benabled == cenabled,
                    "best_shift_equal": int(bresult.best_shift) == int(cresult.best_shift),
                    "exact_proofs_equal": int(bresult.exact_proofs) == int(cresult.exact_proofs),
                    "plan_equal": _plan_signature(bplan) == _plan_signature(cplan),
                    "traffic_equal": btraffic == ctraffic,
                    "segments_equal": bsegments == csegments,
                    "depth_equal": bdepth == cdepth,
                    "node_count_equal": len(bprogram.nodes) == cnode_count,
                    "oracle_equal": oracle_equal,
                    "candidate_exact": candidate_exact,
                }
                if not all(checks.values()):
                    off = _first_diff(bwire, cwire)
                    return {
                        "decision": "diagnostic_reproduced_first_semantic_mismatch",
                        "relation_bytes": size,
                        "case": case,
                        "checks": checks,
                        "baseline_stats": bstats.__dict__,
                        "candidate_stats": cstats.__dict__,
                        "baseline_wire_len": len(bwire),
                        "candidate_wire_len": len(cwire),
                        "first_wire_diff_offset": off,
                        "baseline_wire_context_hex": _context(bwire, off),
                        "candidate_wire_context_hex": _context(cwire, off),
                        "baseline_program": _program_signature(bprogram),
                        "candidate_decoded_program": candidate_program_sig,
                        "candidate_decode_error": candidate_decode_error,
                        "baseline_plan_signature": repr(_plan_signature(bplan)),
                        "candidate_plan_signature": repr(_plan_signature(cplan)),
                    }
        return {"decision": "diagnostic_did_not_reproduce_failure"}
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
