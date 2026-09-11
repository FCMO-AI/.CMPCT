"""ONE-G0.2 sparse native relation-signal carrying-cost rehabilitation.

This is a causally different descendant of the full-signal native carrying-cost test.
It does NOT relax that experiment's thresholds. It asks whether relation statistics can
be sampled sparsely while the common run/reuse observation remains a full one-pass scan.

Mechanism
---------
- run morphology: every byte, unchanged;
- aligned 64-byte FNV reuse evidence: every byte/chunk, unchanged;
- add8 first-difference evidence: every 16th position;
- lag-64 XOR evidence: every 16th position, reading data[p-64] directly;
- no 64-byte relation ring is maintained;
- sampled evidence uses the same 7/8 dominance rule and a 16-sample floor, equivalent
  to the original 256-pair minimum in represented source span.

The candidate remains writer-side nomination only. Any nominated Law still requires
exact downstream proof. Sampled support counts are not granted authority as exact
addressable-byte estimates.

Frozen gates
------------
The exact 24 original cells remain mandatory and decisions must equal the full Python
oracle on every cell. In addition, six generator-distinct 1 MiB positive variants are
required: three add8 ramps with different starts/deltas and three XOR chains with
independent bases/masks. All must preserve their required relation nomination.

Advance iff:
- all 30 unique rows are present;
- all decisions equal independent/full-signal oracle decisions;
- common run/reuse state equals the native baseline;
- source scan remains exactly 1.0x input;
- median candidate/baseline wall and CPU <= 1.30x;
- median 1 MiB wall and CPU <= 1.30x;
- no 1 MiB row exceeds 1.40x on either wall or CPU;
- every 1 MiB candidate row sustains >= 200 MiB/s wall and CPU.

Small-row ratio outliers are retained but do not individually veto because the fixed
FFI/copy envelope can dominate sub-millisecond rows; the median and 1 MiB gates prevent
that from becoming a loophole. A future integrated observer must still charge the real
product boundary.

Pre-result correction
---------------------
Source `6212fa48dea72373551bddb7252d1905d157aa94` is inadmissible for this experiment.
Its source-to-source replacement patterns targeted an obsolete compact C spelling and
therefore left the full-signal candidate unchanged. This repaired descendant hard-fails
at import if the intended sparse transformation is not present. No scientific threshold,
matrix row, sample stride, or interpretation rule changed.
"""
from __future__ import annotations

import ctypes
import json
import random
import statistics
import time

import benchmarks.one.one_g02_native_multi_law_carry as full
from benchmarks.one.one_g02_multi_law_gate import FAMILIES, SIZES, make_case
from experiments.one.multi_law_gate import observe_multi_law_gate

REPETITIONS = 21
SAMPLE_STRIDE = 16
MAX_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_ROW_OVERHEAD = 1.40
MIN_1MIB_THROUGHPUT_MIB_S = 200.0

_RING_DECL = "    uint8_t ring[LAG] = {0};\n"
_FULL_RELATION_BODY = """        if (p) {
            const uint8_t d = (uint8_t)(v - previous);
            ++delta[d];
            ++arithmetic_pairs;
        }
        previous = v;

        if (p >= LAG) {
            const uint8_t relation = (uint8_t)(v ^ ring[p % LAG]);
            ++xhist[relation];
            ++xor_pairs;
        }
        ring[p % LAG] = v;
"""
_SPARSE_RELATION_BODY = """        if (p && ((p & 15u) == 0)) {
            const uint8_t d = (uint8_t)(v - previous);
            ++delta[d];
            ++arithmetic_pairs;
        }
        previous = v;

        if (p >= LAG && ((p & 15u) == 0)) {
            const uint8_t relation = (uint8_t)(v ^ data[p - LAG]);
            ++xhist[relation];
            ++xor_pairs;
        }
"""
_FULL_ADD8 = "    const int add8 = arithmetic_pairs >= 256 && delta_idx != 0 &&\n"
_SPARSE_ADD8 = "    const int add8 = arithmetic_pairs >= 16 && delta_idx != 0 &&\n"
_FULL_XOR = "    const int xor_nom = xor_pairs >= 256 && xor_idx != 0 &&\n"
_SPARSE_XOR = "    const int xor_nom = xor_pairs >= 16 && xor_idx != 0 &&\n"

# Derive the sparse kernel from the frozen full-signal source so the baseline and every
# non-relation operation stay byte-for-byte identical. Each replacement must match
# exactly once; otherwise fail before compiling/timing rather than benchmark the wrong arm.
for needle in (_RING_DECL, _FULL_RELATION_BODY, _FULL_ADD8, _FULL_XOR):
    if full._C_SOURCE.count(needle) != 1:
        raise RuntimeError("sparse carrying-cost source transform no longer matches full kernel")

_SPARSE_SOURCE = full._C_SOURCE.replace(_RING_DECL, "")
_SPARSE_SOURCE = _SPARSE_SOURCE.replace(_FULL_RELATION_BODY, _SPARSE_RELATION_BODY)
_SPARSE_SOURCE = _SPARSE_SOURCE.replace(_FULL_ADD8, _SPARSE_ADD8)
_SPARSE_SOURCE = _SPARSE_SOURCE.replace(_FULL_XOR, _SPARSE_XOR)

if _SPARSE_SOURCE == full._C_SOURCE:
    raise RuntimeError("sparse carrying-cost transform was a no-op")
if "p & 15u" not in _SPARSE_SOURCE or "data[p - LAG]" not in _SPARSE_SOURCE:
    raise RuntimeError("sparse carrying-cost transform missing sampled relation logic")
if "ring[LAG]" in _SPARSE_SOURCE or "arithmetic_pairs >= 256" in _SPARSE_SOURCE or "xor_pairs >= 256" in _SPARSE_SOURCE:
    raise RuntimeError("sparse carrying-cost transform retained full-signal relation state")


def _build_sparse_library() -> ctypes.CDLL:
    import subprocess
    import tempfile
    from pathlib import Path
    build = Path(tempfile.mkdtemp(prefix="cmpct-one-native-multi-law-sparse-"))
    source = build / "kernel.c"
    output = build / "libgate.so"
    source.write_text(_SPARSE_SOURCE)
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    for name in ("one_gate_baseline", "one_gate_candidate"):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(full._GateOut)]
        fn.restype = ctypes.c_int
    return lib


_LIB: ctypes.CDLL | None = None


def _lib() -> ctypes.CDLL:
    global _LIB
    if _LIB is None:
        _LIB = _build_sparse_library()
    return _LIB


def _call(name: str, data: bytes) -> full._GateOut:
    n = len(data)
    buf = (ctypes.c_uint8 * n).from_buffer_copy(data) if n else None
    ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out = full._GateOut()
    rc = getattr(_lib(), name)(ptr, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"{name} failed: {rc}")
    return out


def _measure(data: bytes):
    baseline = _call("one_gate_baseline", data)
    candidate = _call("one_gate_candidate", data)
    bw: list[int] = []
    bc: list[int] = []
    cw: list[int] = []
    cc: list[int] = []
    for rep in range(REPETITIONS):
        order = ("candidate", "baseline") if rep & 1 else ("baseline", "candidate")
        for arm in order:
            name = "one_gate_candidate" if arm == "candidate" else "one_gate_baseline"
            t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
            out = _call(name, data)
            wall = time.perf_counter_ns() - t0w
            cpu = time.process_time_ns() - t0c
            if arm == "candidate":
                candidate = out
                cw.append(wall)
                cc.append(cpu)
            else:
                baseline = out
                bw.append(wall)
                bc.append(cpu)
    return (
        baseline,
        candidate,
        statistics.median(bw) / 1e9,
        statistics.median(bc) / 1e9,
        statistics.median(cw) / 1e9,
        statistics.median(cc) / 1e9,
    )


def _decision(out: full._GateOut) -> tuple[bool, bool, bool, bool]:
    return bool(out.run), bool(out.reuse), bool(out.add8), bool(out.xor_nom)


def _oracle_decision(data: bytes) -> tuple[bool, bool, bool, bool]:
    d = observe_multi_law_gate(data).decision
    return d.run, d.reuse, d.add8, d.xor


def _transfer_cases() -> list[tuple[str, bytes]]:
    n = 1024 * 1024
    rows: list[tuple[str, bytes]] = []
    for i, (start, delta) in enumerate(((3, 1), (231, 17), (99, 251))):
        rows.append((f"transfer_add8_{i}", bytes((start + delta * p) & 255 for p in range(n))))
    for i, mask in enumerate((0x01, 0xA7, 0xFE)):
        rng = random.Random(0xA11CE + i)
        out = bytearray(rng.randrange(256) for _ in range(64))
        while len(out) < n:
            prev = out[-64:]
            out.extend(bytes(v ^ mask for v in prev))
        rows.append((f"transfer_xor_{i}", bytes(out[:n])))
    return rows


def decide(rows: list[dict]) -> str:
    if len(rows) != 30 or len({(r["size"], r["family"]) for r in rows}) != 30:
        return "INVALIDATE_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if any(not r["semantic_equal"] or not r["baseline_common_equal"] for r in rows):
        return "INVALIDATE_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if any(r["source_scan_ratio"] != 1.0 for r in rows):
        return "INVALIDATE_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if statistics.median(r["wall_ratio"] for r in rows) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if statistics.median(r["cpu_ratio"] for r in rows) > MAX_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY"
    mib = [r for r in rows if r["size"] == 1024 * 1024]
    if statistics.median(r["wall_ratio"] for r in mib) > MAX_1MIB_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if statistics.median(r["cpu_ratio"] for r in mib) > MAX_1MIB_MEDIAN_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if max(r["wall_ratio"] for r in mib) > MAX_1MIB_ROW_OVERHEAD or max(r["cpu_ratio"] for r in mib) > MAX_1MIB_ROW_OVERHEAD:
        return "HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY"
    if any(
        r["candidate_wall_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S
        or r["candidate_cpu_mib_s"] < MIN_1MIB_THROUGHPUT_MIB_S
        for r in mib
    ):
        return "HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY"
    return "ADVANCE_NATIVE_MULTI_LAW_SPARSE_CARRY"


def main() -> int:
    cases = [(family, size, make_case(family, size)) for size in SIZES for family in FAMILIES]
    cases += [(family, 1024 * 1024, data) for family, data in _transfer_cases()]
    rows = []
    for family, size, data in cases:
        b, c, bw, bc, cw, cc = _measure(data)
        common = (
            bool(b.run) == bool(c.run)
            and bool(b.reuse) == bool(c.reuse)
            and int(b.run_support) == int(c.run_support)
            and int(b.reuse_support) == int(c.reuse_support)
            and int(b.retained_entries) == int(c.retained_entries)
        )
        mib = size / (1024 * 1024)
        rows.append(
            {
                "size": size,
                "family": family,
                "semantic_equal": _decision(c) == _oracle_decision(data),
                "baseline_common_equal": common,
                "source_scan_ratio": c.source_scan_bytes / max(1, c.input_bytes),
                "baseline_wall_seconds": bw,
                "baseline_cpu_seconds": bc,
                "candidate_wall_seconds": cw,
                "candidate_cpu_seconds": cc,
                "wall_ratio": cw / bw,
                "cpu_ratio": cc / bc,
                "candidate_wall_mib_s": mib / cw,
                "candidate_cpu_mib_s": mib / cc,
                "candidate_decision": [
                    name
                    for name, flag in zip(("run", "reuse", "add8", "xor"), _decision(c))
                    if flag
                ],
            }
        )
    decision = decide(rows)
    mib_rows = [r for r in rows if r["size"] == 1024 * 1024]
    print(
        json.dumps(
            {
                "experiment": "ONE-G0.2 sparse native multi-Law carrying cost",
                "decision": decision,
                "sample_stride": SAMPLE_STRIDE,
                "repetitions": REPETITIONS,
                "median_wall_ratio": statistics.median(r["wall_ratio"] for r in rows),
                "median_cpu_ratio": statistics.median(r["cpu_ratio"] for r in rows),
                "median_1mib_wall_ratio": statistics.median(r["wall_ratio"] for r in mib_rows),
                "median_1mib_cpu_ratio": statistics.median(r["cpu_ratio"] for r in mib_rows),
                "worst_1mib_wall_ratio": max(r["wall_ratio"] for r in mib_rows),
                "worst_1mib_cpu_ratio": max(r["cpu_ratio"] for r in mib_rows),
                "rows": rows,
            },
            sort_keys=True,
        )
    )
    return 0 if decision == "ADVANCE_NATIVE_MULTI_LAW_SPARSE_CARRY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
