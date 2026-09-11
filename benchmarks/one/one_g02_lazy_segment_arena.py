"""ONE-G0.2 lazy native segment-arena resource falsifier."""
from __future__ import annotations

import argparse
import ctypes
from hashlib import sha256
import json
import os
import resource
import statistics
import subprocess
import sys

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    Segment,
    SegmentStats,
    _admit,
    _build_native,
    _native_plan,
)
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZE = 1 << 20
REPETITIONS = 7
REJECTED = ("fragmented_every32", "independent_random")
ADMITTED = ("shift_plus1", "shift_plus1_damage_quarter", "fragmented_every96")
CASES = ADMITTED + REJECTED
MIN_REJECTED_SAVING_KIB = 8 * 1024
ADMITTED_PEAK_RATIO_MAX = 1.05


def _linux_mem() -> tuple[int, int]:
    vmrss = vmhwm = 0
    with open("/proc/self/status", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                vmrss = int(line.split()[1])
            elif line.startswith("VmHWM:"):
                vmhwm = int(line.split()[1])
    return vmrss, vmhwm


def _child(arm: str, case: str) -> dict:
    source, target, expected_enable, expected_shift = _relation_cases(SIZE)[case]
    admission_fn, segment_fn, td = _build_native()
    try:
        src_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(source)
        dst_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(target)
        after_inputs_rss, after_inputs_hwm = _linux_mem()

        seg_capacity_bytes = SIZE * ctypes.sizeof(Segment)
        seg_buf = None
        if arm == "eager":
            seg_buf = (Segment * SIZE)()
        after_initial_alloc_rss, after_initial_alloc_hwm = _linux_mem()

        previous_digest = sha256(source).hexdigest()
        current_digest = sha256(target).hexdigest()
        previous_root = Root(Ref(0), SIZE, previous_digest)
        result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, SIZE)
        after_admit_rss, after_admit_hwm = _linux_mem()

        if enabled and seg_buf is None:
            seg_buf = (Segment * SIZE)()
        after_lazy_alloc_rss, after_lazy_alloc_hwm = _linux_mem()

        segment_stats = SegmentStats()
        if enabled:
            if seg_buf is None:
                raise AssertionError("admitted relation missing segment arena")
            plan = _native_plan(segment_fn, src_arr, dst_arr, SIZE, seg_buf, segment_stats)
            program, pool_stats = program_from_plan_pooled(source, target, plan, previous_root, current_digest)
            hierarchy_depth = pool_stats.hierarchy_depth
        else:
            plan = ()
            program, hierarchy_depth = _literal_program(source, target, previous_root, current_digest)
        program.validate_shape()
        wire, wire_stats = _encode_program_growable_prevalidated(program)
        outputs, vm_stats = evaluate(decode_program(wire))
        final_rss, final_hwm = _linux_mem()
        semantic_ok = (
            enabled == expected_enable
            and (not enabled or expected_shift is None or int(result.best_shift) == expected_shift)
            and outputs == {"previous": source, "current": target}
            and program.roots["previous"].sha256 == previous_digest
            and program.roots["current"].sha256 == current_digest
        )
        return {
            "arm": arm,
            "case": case,
            "expected_enable": expected_enable,
            "relation_enabled": bool(enabled),
            "best_shift": int(result.best_shift),
            "exact_proofs": int(result.exact_proofs),
            "gate_reads": gate_reads,
            "gate_used": gate_used,
            "segment_abi_bytes": ctypes.sizeof(Segment),
            "segment_capacity_bytes": seg_capacity_bytes if (arm == "eager" or enabled) else 0,
            "segments": int(segment_stats.segments),
            "hierarchy_depth": hierarchy_depth,
            "canonical_wire_bytes": wire_stats.total_bytes,
            "surprise_bytes": wire_stats.surprise_bytes,
            "reader_work_bytes": vm_stats.work_bytes,
            "semantic_ok": semantic_ok,
            "after_inputs_vmrss_kib": after_inputs_rss,
            "after_inputs_vmhwm_kib": after_inputs_hwm,
            "after_initial_alloc_vmrss_kib": after_initial_alloc_rss,
            "after_initial_alloc_vmhwm_kib": after_initial_alloc_hwm,
            "after_admission_vmrss_kib": after_admit_rss,
            "after_admission_vmhwm_kib": after_admit_hwm,
            "after_lazy_alloc_vmrss_kib": after_lazy_alloc_rss,
            "after_lazy_alloc_vmhwm_kib": after_lazy_alloc_hwm,
            "final_vmrss_kib": final_rss,
            "final_vmhwm_kib": final_hwm,
            "ru_maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        }
    finally:
        td.cleanup()


def _invoke(arm: str, case: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_g02_lazy_segment_arena", "--child", arm, case],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("lazy-segment child produced no JSON")
    return json.loads(lines[-1])


def run() -> dict:
    rows = []
    semantic_ok = True
    for case in CASES:
        samples = {"eager": [], "lazy": []}
        for rep in range(REPETITIONS):
            order = ("eager", "lazy") if rep % 2 == 0 else ("lazy", "eager")
            for arm in order:
                value = _invoke(arm, case)
                semantic_ok &= bool(value["semantic_ok"])
                samples[arm].append(value)
        eager = samples["eager"]
        lazy = samples["lazy"]
        def med(arm_rows, key):
            return float(statistics.median(row[key] for row in arm_rows))
        eager_after_admit = med(eager, "after_admission_vmrss_kib")
        lazy_after_admit = med(lazy, "after_admission_vmrss_kib")
        eager_peak = med(eager, "ru_maxrss_kib")
        lazy_peak = med(lazy, "ru_maxrss_kib")
        row = {
            "case": case,
            "expected_enable": eager[-1]["expected_enable"],
            "relation_enabled": eager[-1]["relation_enabled"],
            "best_shift": eager[-1]["best_shift"],
            "exact_proofs": eager[-1]["exact_proofs"],
            "segment_abi_bytes": eager[-1]["segment_abi_bytes"],
            "eager_segment_capacity_bytes": eager[-1]["segment_capacity_bytes"],
            "lazy_segment_capacity_bytes": lazy[-1]["segment_capacity_bytes"],
            "segments": eager[-1]["segments"],
            "canonical_wire_bytes": eager[-1]["canonical_wire_bytes"],
            "surprise_bytes": eager[-1]["surprise_bytes"],
            "eager_after_admission_vmrss_kib_median": eager_after_admit,
            "lazy_after_admission_vmrss_kib_median": lazy_after_admit,
            "lazy_current_rss_saving_kib": eager_after_admit - lazy_after_admit,
            "eager_peak_rss_kib_median": eager_peak,
            "lazy_peak_rss_kib_median": lazy_peak,
            "lazy_over_eager_peak_rss": lazy_peak / eager_peak,
            "eager_final_vmrss_kib_median": med(eager, "final_vmrss_kib"),
            "lazy_final_vmrss_kib_median": med(lazy, "final_vmrss_kib"),
        }
        rows.append(row)

    rejected_ok = all(
        row["lazy_current_rss_saving_kib"] >= MIN_REJECTED_SAVING_KIB
        and row["lazy_segment_capacity_bytes"] == 0
        for row in rows if row["case"] in REJECTED
    )
    admitted_ok = all(
        row["lazy_over_eager_peak_rss"] <= ADMITTED_PEAK_RATIO_MAX
        and row["lazy_segment_capacity_bytes"] == row["eager_segment_capacity_bytes"]
        for row in rows if row["case"] in ADMITTED
    )
    if not semantic_ok:
        decision = "INVALIDATE_LAZY_SEGMENT_ARENA"
    elif rejected_ok and admitted_ok:
        decision = "ADVANCE_LAZY_SEGMENT_ARENA"
    else:
        decision = "HOLD_LAZY_SEGMENT_ARENA"
    return {
        "schema": "cmpct-one-g02-lazy-segment-arena-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "size": SIZE,
        "repetitions": REPETITIONS,
        "min_rejected_saving_kib": MIN_REJECTED_SAVING_KIB,
        "admitted_peak_ratio_max": ADMITTED_PEAK_RATIO_MAX,
        "semantic_gates_pass": semantic_ok,
        "rejected_memory_gate_pass": rejected_ok,
        "admitted_peak_gate_pass": admitted_ok,
        "decision": decision,
        "claim_boundary": (
            "native writer resource scheduling only; same relation, segmenter, Program and wire; candidate skips "
            "maximum Segment arena on rejected roots but still pays identical admitted capacity; no timing, format, "
            "reader, arbitrary-capacity, durability, recovery, portability, v0.29/v0.30 authority"
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", nargs=2, metavar=("ARM", "CASE"))
    args = parser.parse_args()
    if args.child:
        arm, case = args.child
        if arm not in {"eager", "lazy"} or case not in CASES:
            return 2
        print(json.dumps(_child(arm, case), sort_keys=True))
        return 0
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_LAZY_SEGMENT_ARENA" else 1


if __name__ == "__main__":
    raise SystemExit(main())
