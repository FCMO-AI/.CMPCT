"""ONE-G0.2 exact SSE2 segment-plan mask falsifier.

Frozen by ONE_G02_NATIVE_SEGMENT_SSE2_MASK_PREREG_2026-09-06.md.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import _relation_cases

ROUNDS = 101
MATURE_MIN = 16 * 1024
SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
PRODUCTIVE = ("shift_plus1", "shift_plus1_damage_quarter", "fragmented_every96")
CONTROLS = ("fragmented_every32", "independent_random")
TAIL_LENGTHS = (1, 2, 15, 16, 17, 31, 32, 33, 63, 64, 65)
PRODUCTIVE_MEDIAN_MAX = 0.80
PRODUCTIVE_ROW_MAX = 1.03
CONTROL_MEDIAN_MAX = 1.00
CONTROL_ROW_MAX = 1.03
HOSTILE_MEDIAN_MAX = 1.03


class Segment(ctypes.Structure):
    _fields_ = [("start", ctypes.c_uint32), ("length", ctypes.c_uint32), ("kind", ctypes.c_uint8)]


class Stats(ctypes.Structure):
    _fields_ = [("compared_target_bytes", ctypes.c_uint64), ("segments", ctypes.c_uint64)]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-seg-sse2-")
    lib = Path(td.name) / "libseg.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", "-msse2",
        str(here / "one_g02_native_segment_sse2_mask_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    scalar = c.one_g02_segment_scalar_exact
    sse2 = c.one_g02_segment_sse2_exact
    for fn in (scalar, sse2):
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                       ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(Stats)]
        fn.restype = ctypes.c_int
    timed = c.one_g02_segment_sse2_timed_pair
    timed.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                      ctypes.POINTER(Segment), ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.c_size_t,
                      ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64)]
    timed.restype = ctypes.c_int
    return scalar, sse2, timed, td


def _signature(out, count: int):
    return tuple((int(out[i].kind), int(out[i].start), int(out[i].length)) for i in range(count))


def _python_oracle(source: bytes, target: bytes):
    """Independent specification of maximal runs of is_ref(i)."""
    n = len(target)
    if len(source) != n:
        raise ValueError("source/target size mismatch")
    if n == 0:
        return ()
    out = []
    i = 0
    while i < n:
        ref = i > 0 and target[i] == source[i - 1]
        begin = i
        i += 1
        while i < n and (i > 0 and target[i] == source[i - 1]) == ref:
            i += 1
        out.append((0 if ref else 1, begin - 1 if ref else begin, i - begin))
    return tuple(out)


def _reconstruct(source: bytes, target: bytes, sig):
    pieces = []
    for kind, start, length in sig:
        pieces.append(source[start:start+length] if kind == 0 else target[start:start+length])
    return b"".join(pieces)


def _transition_hostile(n: int):
    source = bytes(((i * 131 + 17) & 255) for i in range(n))
    if n == 0:
        return source, b""
    target = bytearray(n)
    target[0] = source[0] ^ 0x5A
    for i in range(1, n):
        target[i] = source[i-1] if (i & 1) else (source[i-1] ^ 0xFF)
    return source, bytes(target)


def _tail_case(n: int):
    source = bytes(((i * 73 + 11) & 255) for i in range(n))
    target = bytearray(n)
    if n:
        target[0] = 0xA5
    for i in range(1, n):
        target[i] = source[i-1] if ((i // 3) & 1) else (source[i-1] ^ 0x3C)
    return source, bytes(target)


def _row(scalar, sse2, timed, name: str, size: int, source: bytes, target: bytes, category: str):
    src = (ctypes.c_uint8 * max(1, size))()
    dst = (ctypes.c_uint8 * max(1, size))()
    if size:
        ctypes.memmove(src, source, size)
        ctypes.memmove(dst, target, size)
    a = (Segment * max(1, size))()
    b = (Segment * max(1, size))()
    sa, sb = Stats(), Stats()
    if scalar(src, dst, size, a, max(1, size), ctypes.byref(sa)) != 0:
        raise RuntimeError("scalar segmenter failed")
    if sse2(src, dst, size, b, max(1, size), ctypes.byref(sb)) != 0:
        raise RuntimeError("SSE2 segmenter failed")
    siga = _signature(a, int(sa.segments))
    sigb = _signature(b, int(sb.segments))
    oracle = _python_oracle(source, target)
    semantic_ok = (
        siga == oracle == sigb
        and int(sa.compared_target_bytes) == size and int(sb.compared_target_bytes) == size
        and _reconstruct(source, target, siga) == target
        and _reconstruct(source, target, sigb) == target
    )
    if not semantic_ok:
        raise AssertionError(f"segment-plan/oracle mismatch: {name}/{size}")
    ans = (ctypes.c_uint64 * ROUNDS)()
    bns = (ctypes.c_uint64 * ROUNDS)()
    if timed(src, dst, size, a, b, max(1, size), ROUNDS, ans, bns) != 0:
        raise RuntimeError("timed segment pair failed")
    abase = float(statistics.median(int(x) for x in ans))
    bcand = float(statistics.median(int(x) for x in bns))
    return {
        "case": name, "category": category, "relation_bytes": size,
        "segments": int(sa.segments), "semantic_ok": semantic_ok,
        "scalar_median_ns": abase, "sse2_median_ns": bcand,
        "candidate_over_baseline": bcand / abase,
    }


def run():
    scalar, sse2, timed, td = _build()
    rows = []
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for name in PRODUCTIVE:
                source, target, _enabled, _shift = cases[name]
                rows.append(_row(scalar, sse2, timed, name, size, source, target, "productive"))
            for name in CONTROLS:
                source, target, _enabled, _shift = cases[name]
                rows.append(_row(scalar, sse2, timed, name, size, source, target, "control"))
            source, target = _transition_hostile(size)
            rows.append(_row(scalar, sse2, timed, "transition_hostile", size, source, target, "hostile"))
        for n in TAIL_LENGTHS:
            source, target = _tail_case(n)
            rows.append(_row(scalar, sse2, timed, "tail_boundary", n, source, target, "tail"))

        mature_productive = [r["candidate_over_baseline"] for r in rows if r["category"] == "productive" and r["relation_bytes"] >= MATURE_MIN]
        mature_control = [r["candidate_over_baseline"] for r in rows if r["category"] == "control" and r["relation_bytes"] >= MATURE_MIN]
        mature_hostile = [r["candidate_over_baseline"] for r in rows if r["category"] == "hostile" and r["relation_bytes"] >= MATURE_MIN]
        semantic_failures = sum(not bool(r["semantic_ok"]) for r in rows)
        pmed = float(statistics.median(mature_productive))
        pworst = max(mature_productive)
        cmed = float(statistics.median(mature_control))
        cworst = max(mature_control)
        hmed = float(statistics.median(mature_hostile))
        advance = (
            semantic_failures == 0 and pmed <= PRODUCTIVE_MEDIAN_MAX and pworst <= PRODUCTIVE_ROW_MAX
            and cmed <= CONTROL_MEDIAN_MAX and cworst <= CONTROL_ROW_MAX and hmed <= HOSTILE_MEDIAN_MAX
        )
        return {
            "schema": "cmpct-one-g02-native-segment-sse2-mask-v2",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "semantic_failures": semantic_failures,
            "independent_python_oracle": True,
            "mature_productive_median_ratio": pmed,
            "mature_productive_worst_ratio": pworst,
            "mature_control_median_ratio": cmed,
            "mature_control_worst_ratio": cworst,
            "mature_transition_hostile_median_ratio": hmed,
            "decision": "advance_segment_sse2_mask_to_writer" if advance else "reject_segment_sse2_mask_speed",
            "claim_boundary": "x86-64/SSE2 exact native segment-kernel implementation only; no writer or portability promotion",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_segment_sse2_mask_to_writer" else 1)
