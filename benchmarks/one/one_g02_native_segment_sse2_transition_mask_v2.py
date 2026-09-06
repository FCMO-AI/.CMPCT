"""ONE-G0.2 exact SSE2 transition-mask segment falsifier V2."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import _relation_cases
from benchmarks.one.one_g02_native_segment_sse2_mask import (
    Segment, Stats, ROUNDS, MATURE_MIN, SIZES, PRODUCTIVE, CONTROLS, TAIL_LENGTHS,
    PRODUCTIVE_MEDIAN_MAX, PRODUCTIVE_ROW_MAX, CONTROL_MEDIAN_MAX, CONTROL_ROW_MAX,
    HOSTILE_MEDIAN_MAX, _python_oracle, _reconstruct, _transition_hostile, _tail_case,
)

HOSTILE_ROW_MAX = 1.08


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-seg-transition-v2-")
    lib = Path(td.name) / "libseg.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", "-msse2",
        str(here / "one_g02_native_segment_sse2_transition_mask_v2_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    scalar = c.one_g02_segment_scalar_exact_v2
    candidate = c.one_g02_segment_sse2_transition_exact_v2
    for fn in (scalar, candidate):
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                       ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(Stats)]
        fn.restype = ctypes.c_int
    timed = c.one_g02_segment_sse2_transition_timed_pair_v2
    timed.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                      ctypes.POINTER(Segment), ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.c_size_t,
                      ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64)]
    timed.restype = ctypes.c_int
    return scalar, candidate, timed, td


def _signature(out, count: int):
    return tuple((int(out[i].kind), int(out[i].start), int(out[i].length)) for i in range(count))


def _row(scalar, candidate, timed, name, size, source, target, category):
    src = (ctypes.c_uint8 * max(1, size))()
    dst = (ctypes.c_uint8 * max(1, size))()
    if size:
        ctypes.memmove(src, source, size)
        ctypes.memmove(dst, target, size)
    a = (Segment * max(1, size))()
    b = (Segment * max(1, size))()
    sa, sb = Stats(), Stats()
    if scalar(src, dst, size, a, max(1, size), ctypes.byref(sa)) != 0:
        raise RuntimeError("scalar V2 authority failed")
    if candidate(src, dst, size, b, max(1, size), ctypes.byref(sb)) != 0:
        raise RuntimeError("transition-mask V2 failed")
    siga = _signature(a, int(sa.segments))
    sigb = _signature(b, int(sb.segments))
    oracle = _python_oracle(source, target)
    semantic_ok = (
        siga == oracle == sigb
        and int(sa.compared_target_bytes) == size
        and int(sb.compared_target_bytes) == size
        and _reconstruct(source, target, siga) == target
        and _reconstruct(source, target, sigb) == target
    )
    if not semantic_ok:
        raise AssertionError(f"transition-mask V2 plan/oracle mismatch: {name}/{size}")

    ans = (ctypes.c_uint64 * ROUNDS)()
    bns = (ctypes.c_uint64 * ROUNDS)()
    if timed(src, dst, size, a, b, max(1, size), ROUNDS, ans, bns) != 0:
        raise RuntimeError("transition-mask V2 timed pair failed")
    abase = float(statistics.median(int(x) for x in ans))
    bcand = float(statistics.median(int(x) for x in bns))
    return {
        "case": name, "category": category, "relation_bytes": size,
        "segments": int(sa.segments), "semantic_ok": semantic_ok,
        "scalar_median_ns": abase, "candidate_median_ns": bcand,
        "candidate_over_baseline": bcand / abase,
    }


def run():
    scalar, candidate, timed, td = _build()
    rows = []
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for name in PRODUCTIVE:
                source, target, _enabled, _shift = cases[name]
                rows.append(_row(scalar, candidate, timed, name, size, source, target, "productive"))
            for name in CONTROLS:
                source, target, _enabled, _shift = cases[name]
                rows.append(_row(scalar, candidate, timed, name, size, source, target, "control"))
            source, target = _transition_hostile(size)
            rows.append(_row(scalar, candidate, timed, "transition_hostile", size, source, target, "hostile"))
        for n in TAIL_LENGTHS:
            source, target = _tail_case(n)
            rows.append(_row(scalar, candidate, timed, "tail_boundary", n, source, target, "tail"))

        mature_productive = [r["candidate_over_baseline"] for r in rows if r["category"] == "productive" and r["relation_bytes"] >= MATURE_MIN]
        mature_control = [r["candidate_over_baseline"] for r in rows if r["category"] == "control" and r["relation_bytes"] >= MATURE_MIN]
        mature_hostile = [r["candidate_over_baseline"] for r in rows if r["category"] == "hostile" and r["relation_bytes"] >= MATURE_MIN]
        semantic_failures = sum(not bool(r["semantic_ok"]) for r in rows)
        pmed, pworst = float(statistics.median(mature_productive)), max(mature_productive)
        cmed, cworst = float(statistics.median(mature_control)), max(mature_control)
        hmed, hworst = float(statistics.median(mature_hostile)), max(mature_hostile)
        advance = (
            semantic_failures == 0
            and pmed <= PRODUCTIVE_MEDIAN_MAX and pworst <= PRODUCTIVE_ROW_MAX
            and cmed <= CONTROL_MEDIAN_MAX and cworst <= CONTROL_ROW_MAX
            and hmed <= HOSTILE_MEDIAN_MAX and hworst <= HOSTILE_ROW_MAX
        )
        return {
            "schema": "cmpct-one-g02-native-segment-sse2-transition-mask-v2",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "independent_python_oracle": True,
            "semantic_failures": semantic_failures,
            "mature_productive_median_ratio": pmed,
            "mature_productive_worst_ratio": pworst,
            "mature_control_median_ratio": cmed,
            "mature_control_worst_ratio": cworst,
            "mature_transition_hostile_median_ratio": hmed,
            "mature_transition_hostile_worst_ratio": hworst,
            "decision": "advance_segment_transition_mask_v2_to_writer" if advance else "reject_segment_transition_mask_v2_speed",
            "claim_boundary": "x86-64/SSE2 exact native segment kernel only; integrated writer and portability unproven",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_segment_transition_mask_v2_to_writer" else 1)
