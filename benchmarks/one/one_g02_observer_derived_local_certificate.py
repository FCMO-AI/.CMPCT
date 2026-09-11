"""ONE-G0.2 carrying-cost falsifier for an observer-derived local certificate."""
from __future__ import annotations

import ctypes
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
import zlib
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR

REPETITIONS = 101
WINDOW = 32
MASK64 = (1 << 64) - 1


class Result(ctypes.Structure):
    _fields_ = [
        ("anchors", ctypes.c_uint64),
        ("qualifying_runs", ctypes.c_uint64),
        ("observer_sink", ctypes.c_uint64),
        ("certificate_windows", ctypes.c_uint64),
        ("certificate_threshold_passes", ctypes.c_uint64),
        ("certificate_hash_checks", ctypes.c_uint64),
        ("certificate_exact_compares", ctypes.c_uint64),
        ("certificate_nominations", ctypes.c_uint64),
        ("retained_state_bytes", ctypes.c_uint64),
        ("scratch_state_bytes", ctypes.c_uint64),
    ]


def _shift(source: bytes, spacing: int | None = None) -> bytes:
    out = bytearray(b"X" + source[:-1])
    if spacing:
        for i in range(16, len(out), spacing):
            out[i] ^= 0xA7
    return bytes(out)


def _random_pair(n: int, seed: int) -> tuple[bytes, bytes]:
    return random.Random(seed).randbytes(n), random.Random(seed + 1).randbytes(n)


def _cases() -> dict[str, tuple[bytes, bytes]]:
    s4 = random.Random(73004).randbytes(4 * 1024)
    s8 = random.Random(73008).randbytes(8 * 1024)
    s64 = random.Random(73064).randbytes(64 * 1024)
    s256 = random.Random(73256).randbytes(256 * 1024)
    za = zlib.compress(random.Random(76001).randbytes(1024 * 1024), level=9)[:1024 * 1024]
    zb = zlib.compress(random.Random(76002).randbytes(1024 * 1024), level=9)[:1024 * 1024]
    basis = random.Random(77001).randbytes(4096)
    repeated = basis * 256
    return {
        "tiny_4k_shift1": (s4, _shift(s4)),
        "tiny_8k_fragmented96": (s8, _shift(s8, 96)),
        "mature_64k_shift1": (s64, _shift(s64)),
        "mature_256k_fragmented96": (s256, _shift(s256, 96)),
        "mature_256k_independent_random": _random_pair(256 * 1024, 74000),
        "mature_1m_independent_random": _random_pair(1024 * 1024, 75000),
        "mature_1m_already_compressed_like": (za, zb),
        "mature_1m_repeated_versioned": (repeated, _shift(repeated)),
    }


def _direct_window_hash(block: bytes) -> int:
    h = 0
    for value in block:
        h = ((h << 1) + _GEAR[value]) & MASK64
    return h


def _derived_hashes(data: bytes):
    h = 0
    delayed = [0] * WINDOW
    for i, value in enumerate(data):
        slot = i & (WINDOW - 1)
        old = delayed[slot]
        h = ((h << 1) + _GEAR[value]) & MASK64
        delayed[slot] = h
        if i + 1 >= WINDOW:
            yield i + 1 - WINDOW, (h - ((old << WINDOW) & MASK64)) & MASK64


def _oracle(source: bytes, target: bytes) -> tuple[bool, list[tuple[int, int]]]:
    witnesses = sorted((h, pos) for pos, h in _derived_hashes(source))[:8]
    # Independent direct-window identity check on fixed and pseudo-random positions.
    sample_positions = {0, max(0, len(source) - WINDOW), len(source) // 2}
    sample_positions.update(random.Random(len(source)).sample(range(len(source) - WINDOW + 1), 5))
    derived = dict(_derived_hashes(source))
    for pos in sample_positions:
        if derived[pos] != _direct_window_hash(source[pos : pos + WINDOW]):
            raise AssertionError(f"prefix-derived fingerprint identity failed at {pos}")
    expected = any(target.find(source[pos : pos + WINDOW]) >= 0 for _, pos in witnesses)
    return expected, witnesses


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-observer-cert-")
    so = Path(td.name) / "libobservercert.so"
    csrc = here / "native" / "one_g02_observer_derived_local_certificate.c"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-fPIC", "-shared", str(csrc), "-o", str(so),
    ], check=True)
    lib = ctypes.CDLL(str(so))
    ptr = ctypes.POINTER(ctypes.c_uint8)
    gear_ptr = ctypes.POINTER(ctypes.c_uint64)
    for name in ("one_observer_derived_baseline", "one_observer_derived_candidate"):
        fn = getattr(lib, name)
        fn.argtypes = [ptr, ptr, ctypes.c_size_t, gear_ptr, ctypes.POINTER(Result)]
        fn.restype = ctypes.c_int
    return lib, td


def _buffers(source: bytes, target: bytes):
    assert len(source) == len(target)
    a = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    b = (ctypes.c_uint8 * len(target)).from_buffer_copy(target)
    return a, b, len(source)


def _invoke(fn, a, b, n: int, gear) -> Result:
    out = Result()
    rc = fn(a, b, n, gear, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"native probe failed rc={rc}")
    return out


def _paired_timing(base_fn, cand_fn, a, b, n: int, gear):
    base_samples, cand_samples = [], []
    base = cand = None
    for rep in range(REPETITIONS):
        order = ((base_fn, base_samples, "base"), (cand_fn, cand_samples, "cand"))
        if rep & 1:
            order = tuple(reversed(order))
        for fn, samples, label in order:
            t0 = time.perf_counter_ns()
            result = _invoke(fn, a, b, n, gear)
            samples.append(time.perf_counter_ns() - t0)
            if label == "base": base = result
            else: cand = result
    assert base is not None and cand is not None
    return int(statistics.median(base_samples)), int(statistics.median(cand_samples)), base, cand


def run() -> dict[str, object]:
    lib, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows = []
    try:
        for name, (source, target) in _cases().items():
            expected_nomination, witnesses = _oracle(source, target)
            a, b, n = _buffers(source, target)
            base = _invoke(lib.one_observer_derived_baseline, a, b, n, gear)
            cand = _invoke(lib.one_observer_derived_candidate, a, b, n, gear)
            if (base.anchors, base.qualifying_runs, base.observer_sink) != (
                cand.anchors, cand.qualifying_runs, cand.observer_sink
            ):
                raise AssertionError(f"observer parity failed: {name}")
            if bool(cand.certificate_nominations) != expected_nomination:
                raise AssertionError(
                    f"independent nomination oracle mismatch: {name} expected={expected_nomination} native={cand.certificate_nominations}"
                )
            if cand.retained_state_bytes != 98 or cand.scratch_state_bytes != 256:
                raise AssertionError(f"state accounting drift: {name}")

            base_ns, cand_ns, base, cand = _paired_timing(
                lib.one_observer_derived_baseline,
                lib.one_observer_derived_candidate,
                a, b, n, gear,
            )
            negative = "random" in name or "compressed" in name
            if negative and cand.certificate_nominations:
                raise AssertionError(f"false exact nomination: {name}")
            rows.append({
                "case": name,
                "bytes": n,
                "baseline_ns": base_ns,
                "candidate_ns": cand_ns,
                "elapsed_ratio": cand_ns / base_ns,
                "anchors": int(base.anchors),
                "qualifying_run_bytes": int(base.qualifying_runs),
                "oracle_nomination": expected_nomination,
                "certificate_nominations": int(cand.certificate_nominations),
                "certificate_windows": int(cand.certificate_windows),
                "threshold_passes": int(cand.certificate_threshold_passes),
                "hash_checks": int(cand.certificate_hash_checks),
                "exact_compares": int(cand.certificate_exact_compares),
                "retained_state_bytes": int(cand.retained_state_bytes),
                "scratch_state_bytes": int(cand.scratch_state_bytes),
                "oracle_witness_max_hash": max(h for h, _ in witnesses),
            })

        mature = [r["elapsed_ratio"] for r in rows if r["bytes"] >= 64 * 1024]
        fragmented = [r["elapsed_ratio"] for r in rows if "fragmented" in r["case"] and r["bytes"] >= 64 * 1024]
        tiny = [r["elapsed_ratio"] for r in rows if r["bytes"] < 64 * 1024]
        agg = {
            "mature_median_ratio": statistics.median(mature),
            "fragmented_mature_median_ratio": statistics.median(fragmented),
            "mature_worst_ratio": max(mature),
            "tiny_median_ratio": statistics.median(tiny),
        }
        passed = (
            agg["mature_median_ratio"] <= 1.15
            and agg["fragmented_mature_median_ratio"] <= 1.15
            and agg["mature_worst_ratio"] <= 1.25
            and agg["tiny_median_ratio"] <= 1.25
        )
        return {
            "schema": "cmpct-one-g02-observer-derived-local-certificate-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "aggregates": agg,
            "decision": "advance_structural_and_full_observer_ab" if passed else "reject_observer_derived_certificate_shape",
            "claim_boundary": "native observer carrying-cost triage only; no writer/density/release claim",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_structural_and_full_observer_ab" else 1)
