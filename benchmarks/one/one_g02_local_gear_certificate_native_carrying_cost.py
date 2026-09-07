"""ONE-G0.2 native carrying-cost probe for the bounded local Gear certificate."""
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


class Result(ctypes.Structure):
    _fields_ = [
        ("anchors", ctypes.c_uint64),
        ("qualifying_runs", ctypes.c_uint64),
        ("observer_sink", ctypes.c_uint64),
        ("certificate_windows", ctypes.c_uint64),
        ("certificate_hash_checks", ctypes.c_uint64),
        ("certificate_exact_compares", ctypes.c_uint64),
        ("certificate_nominations", ctypes.c_uint64),
        ("certificate_state_bytes", ctypes.c_uint64),
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


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-cert-cost-")
    so = Path(td.name) / "libcertcost.so"
    csrc = here / "native" / "one_g02_local_gear_certificate_carrying_cost.c"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-fPIC", "-shared", str(csrc), "-o", str(so),
    ], check=True)
    lib = ctypes.CDLL(str(so))
    ptr = ctypes.POINTER(ctypes.c_uint8)
    gear_ptr = ctypes.POINTER(ctypes.c_uint64)
    for name in ("one_g02_certificate_probe_baseline", "one_g02_certificate_probe_candidate"):
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


def _paired_timing(base_fn, cand_fn, a, b, n: int, gear) -> tuple[int, int, Result, Result]:
    base_samples: list[int] = []
    cand_samples: list[int] = []
    base = cand = None
    for rep in range(REPETITIONS):
        order = ((base_fn, base_samples, "base"), (cand_fn, cand_samples, "cand"))
        if rep & 1:
            order = tuple(reversed(order))
        for fn, samples, label in order:
            t0 = time.perf_counter_ns()
            result = _invoke(fn, a, b, n, gear)
            samples.append(time.perf_counter_ns() - t0)
            if label == "base":
                base = result
            else:
                cand = result
    assert base is not None and cand is not None
    return int(statistics.median(base_samples)), int(statistics.median(cand_samples)), base, cand


def run() -> dict[str, object]:
    lib, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows: list[dict[str, object]] = []
    try:
        for name, (source, target) in _cases().items():
            a, b, n = _buffers(source, target)
            # Warm-up and parity happen outside the timed region. Input copies also stay outside.
            base = _invoke(lib.one_g02_certificate_probe_baseline, a, b, n, gear)
            cand = _invoke(lib.one_g02_certificate_probe_candidate, a, b, n, gear)
            if (base.anchors, base.qualifying_runs, base.observer_sink) != (
                cand.anchors, cand.qualifying_runs, cand.observer_sink
            ):
                raise AssertionError(f"observer parity failed: {name}")
            if cand.certificate_state_bytes != 136:
                raise AssertionError(f"certificate state drift: {name}={cand.certificate_state_bytes}")

            base_ns, cand_ns, base, cand = _paired_timing(
                lib.one_g02_certificate_probe_baseline,
                lib.one_g02_certificate_probe_candidate,
                a, b, n, gear,
            )
            negative = "random" in name or "compressed" in name
            if negative and cand.certificate_nominations:
                raise AssertionError(f"false exact certificate nomination: {name}")
            rows.append({
                "case": name,
                "bytes": n,
                "baseline_ns": base_ns,
                "candidate_ns": cand_ns,
                "elapsed_ratio": cand_ns / base_ns,
                "anchors": int(base.anchors),
                "qualifying_run_bytes": int(base.qualifying_runs),
                "certificate_windows": int(cand.certificate_windows),
                "certificate_hash_checks": int(cand.certificate_hash_checks),
                "certificate_exact_compares": int(cand.certificate_exact_compares),
                "certificate_nominations": int(cand.certificate_nominations),
                "certificate_state_bytes": int(cand.certificate_state_bytes),
            })

        mature = [r["elapsed_ratio"] for r in rows if r["bytes"] >= 64 * 1024]
        fragmented = [r["elapsed_ratio"] for r in rows if "fragmented" in r["case"] and r["bytes"] >= 64 * 1024]
        tiny = [r["elapsed_ratio"] for r in rows if r["bytes"] < 64 * 1024]
        aggregates = {
            "mature_median_ratio": statistics.median(mature),
            "fragmented_mature_median_ratio": statistics.median(fragmented),
            "mature_worst_ratio": max(mature),
            "tiny_median_ratio": statistics.median(tiny),
        }
        passed = (
            aggregates["mature_median_ratio"] <= 1.08
            and aggregates["fragmented_mature_median_ratio"] <= 1.10
            and aggregates["mature_worst_ratio"] <= 1.15
            and aggregates["tiny_median_ratio"] <= 1.15
        )
        return {
            "schema": "cmpct-one-g02-local-gear-certificate-native-carrying-cost-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "aggregates": aggregates,
            "decision": "advance_full_promoted_observer_ab" if passed else "reject_present_certificate_carrying_shape",
            "claim_boundary": "native hot-loop carrying-cost triage only; no writer/density/release claim",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_full_promoted_observer_ab" else 1)
