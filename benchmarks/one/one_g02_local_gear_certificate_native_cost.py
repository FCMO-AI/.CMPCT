"""ONE-G0.2 native carrying-cost A/B for the local Gear certificate.

Frozen by docs/one/evidence/ONE_G02_LOCAL_GEAR_CERTIFICATE_NATIVE_COST_PREREG_2026-09-05.md.
The candidate is writer-side discovery only.  It reuses the incoming Gear-table load from
one fused observation loop; exact Law acceptance remains outside this benchmark.
"""
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
from benchmarks.one.one_g02_local_gear_certificate_validation import _source_certificate

REPETITIONS = 7
CERT_WINDOW = 32
CERT_K = 8
MODELED_INCREMENTAL_STATE_BYTES = 136
ANCHOR_MASK = (1 << 10) - 1
LARGE_REPS = 16
MODE_BASELINE = 0
MODE_ROLLING = 1
MODE_CERTIFICATE = 2
MODE_CERTIFICATE_NO_REUSE = 3


def _c_source() -> str:
    gear = ",\n".join(f"UINT64_C({v})" for v in _GEAR)
    return f'''#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define CERT_WINDOW 32u
#define CERT_K 8u
#define ANCHOR_MASK UINT64_C({ANCHOR_MASK})

static const uint64_t GEAR[256] = {{
{gear}
}};

static volatile uint64_t escape_sink = 0;

static inline uint64_t rotl64(uint64_t x, unsigned r) {{
    r &= 63u;
    return (x << r) | (x >> ((64u - r) & 63u));
}}

typedef struct {{
    uint64_t checksum;
    uint64_t anchors;
    uint64_t certificate_updates;
    uint64_t outgoing_gear_lookups;
    uint64_t duplicate_incoming_gear_lookups;
    uint64_t heap_replacements;
}} one_stats;

static inline void bottom8_offer(uint64_t h, uint32_t pos,
                                 uint64_t hashes[CERT_K], uint32_t poses[CERT_K],
                                 unsigned *count, uint64_t *replacements) {{
    if (*count < CERT_K) {{
        hashes[*count] = h;
        poses[*count] = pos;
        (*count)++;
        return;
    }}
    unsigned worst = 0;
    for (unsigned j = 1; j < CERT_K; ++j) {{
        if (hashes[j] > hashes[worst] ||
            (hashes[j] == hashes[worst] && poses[j] > poses[worst]))
            worst = j;
    }}
    if (h < hashes[worst]) {{
        hashes[worst] = h;
        poses[worst] = pos;
        (*replacements)++;
    }}
}}

uint64_t one_run_mode(const uint8_t *data, size_t n, unsigned reps, int mode, one_stats *out) {{
    uint64_t total = 0, anchors = 0, cert_updates = 0, old_loads = 0, duplicate_loads = 0, replacements = 0;
    for (unsigned rep = 0; rep < reps; ++rep) {{
        uint64_t prefix = 0, rolling = 0;
        uint64_t hashes[CERT_K] = {{0}};
        uint32_t poses[CERT_K] = {{0}};
        unsigned count = 0;
        uint8_t run_value = 0;
        size_t run_length = 0;
        for (size_t i = 0; i < n; ++i) {{
            uint8_t value = data[i];
            if (run_length == 0 || value != run_value) {{ run_value = value; run_length = 1; }}
            else {{ run_length++; }}

            uint64_t incoming = GEAR[value];
            prefix = (prefix << 1) + incoming;
            if (i + 1 >= 64u && (prefix & ANCHOR_MASK) == 0) anchors++;

            if (mode != 0) {{
                uint64_t local_incoming = incoming;
                if (mode == 3) {{ local_incoming = GEAR[value]; duplicate_loads++; }}
                if (i < CERT_WINDOW) {{
                    rolling = rotl64(rolling, 1) ^ local_incoming;
                }} else {{
                    uint64_t outgoing = GEAR[data[i - CERT_WINDOW]];
                    old_loads++;
                    rolling = rotl64(rolling, 1) ^ rotl64(outgoing, CERT_WINDOW) ^ local_incoming;
                }}
                if (i + 1 >= CERT_WINDOW && mode >= 2) {{
                    bottom8_offer(rolling, (uint32_t)(i + 1 - CERT_WINDOW), hashes, poses, &count, &replacements);
                    cert_updates++;
                }}
            }}
        }}
        uint64_t cert_mix = 0;
        if (mode >= 2) for (unsigned j = 0; j < count; ++j) cert_mix ^= hashes[j] + ((uint64_t)poses[j] << (j & 31u));
        total ^= prefix + rolling + cert_mix + anchors + run_length + (uint64_t)rep;
    }}
    escape_sink ^= total;
    if (out) {{
        out->checksum = total;
        out->anchors = anchors;
        out->certificate_updates = cert_updates;
        out->outgoing_gear_lookups = old_loads;
        out->duplicate_incoming_gear_lookups = duplicate_loads;
        out->heap_replacements = replacements;
    }}
    return total;
}}

int one_certificate(const uint8_t *data, size_t n, uint64_t hashes[CERT_K], uint32_t poses[CERT_K]) {{
    if (n < CERT_WINDOW) return 0;
    uint64_t rolling = 0, replacements = 0;
    unsigned count = 0;
    for (size_t i = 0; i < n; ++i) {{
        uint64_t incoming = GEAR[data[i]];
        if (i < CERT_WINDOW) rolling = rotl64(rolling, 1) ^ incoming;
        else rolling = rotl64(rolling, 1) ^ rotl64(GEAR[data[i - CERT_WINDOW]], CERT_WINDOW) ^ incoming;
        if (i + 1 >= CERT_WINDOW)
            bottom8_offer(rolling, (uint32_t)(i + 1 - CERT_WINDOW), hashes, poses, &count, &replacements);
    }}
    return (int)count;
}}
'''


class Stats(ctypes.Structure):
    _fields_ = [
        ("checksum", ctypes.c_uint64),
        ("anchors", ctypes.c_uint64),
        ("certificate_updates", ctypes.c_uint64),
        ("outgoing_gear_lookups", ctypes.c_uint64),
        ("duplicate_incoming_gear_lookups", ctypes.c_uint64),
        ("heap_replacements", ctypes.c_uint64),
    ]


def _build_native(td: str):
    src = Path(td) / "cert_cost.c"
    so = Path(td) / "cert_cost.so"
    src.write_text(_c_source())
    subprocess.run(["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(src), "-o", str(so)], check=True)
    lib = ctypes.CDLL(str(so))
    p8 = ctypes.POINTER(ctypes.c_uint8)
    lib.one_run_mode.argtypes = [p8, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int, ctypes.POINTER(Stats)]
    lib.one_run_mode.restype = ctypes.c_uint64
    lib.one_certificate.argtypes = [p8, ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32)]
    lib.one_certificate.restype = ctypes.c_int
    return lib


def _buf(data: bytes):
    return (ctypes.c_uint8 * len(data)).from_buffer_copy(data)


def _native_certificate(lib, data: bytes) -> list[tuple[int, int]]:
    buf = _buf(data)
    hashes = (ctypes.c_uint64 * CERT_K)()
    poses = (ctypes.c_uint32 * CERT_K)()
    count = lib.one_certificate(buf, len(data), hashes, poses)
    return sorted((int(hashes[i]), int(poses[i])) for i in range(count))


def _cases() -> dict[str, bytes]:
    rnd = random.Random(77001)
    random_1m = rnd.randbytes(1024 * 1024)
    compressed = zlib.compress(random.Random(77002).randbytes(1024 * 1024), level=9)
    basis = random.Random(77003).randbytes(4096)
    version = random.Random(77004).randbytes(512 * 1024)
    alternating = (b"\x00\xff" * (512 * 1024))
    return {
        "random_1mib": random_1m,
        "compressed_like_1mib": compressed,
        "repeated_1mib": basis * 256,
        "shifted_version_1mib": version + b"X" + version[:-1],
        "zeros_1mib": b"\0" * (1024 * 1024),
        "alternating_hostile_1mib": alternating,
        "tiny_4k": random.Random(77005).randbytes(4096),
        "tiny_64b": random.Random(77006).randbytes(64),
    }


def _native_sample(lib, data: bytes, mode: int, reps: int) -> tuple[int, Stats]:
    buf = _buf(data)
    samples: list[int] = []
    last = Stats()
    for _ in range(REPETITIONS):
        st = Stats()
        t0 = time.perf_counter_ns()
        lib.one_run_mode(buf, len(data), reps, mode, ctypes.byref(st))
        samples.append(time.perf_counter_ns() - t0)
        last = st
    return int(statistics.median(samples)), last


def run() -> dict[str, object]:
    cases = _cases()
    rows: list[dict[str, object]] = []
    witness_mismatches: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cmpct_one_cert_native_") as td:
        lib = _build_native(td)
        # Freeze exact cross-language semantic equality before trusting timing.
        for name, data in cases.items():
            if _native_certificate(lib, data) != _source_certificate(data):
                witness_mismatches.append(name)

        for name, data in cases.items():
            if len(data) >= 1024 * 1024 - 1024:
                reps = LARGE_REPS
            elif len(data) >= 4096:
                reps = 1024
            else:
                reps = 65536
            times: dict[int, int] = {}
            stats: dict[int, Stats] = {}
            for mode in (MODE_BASELINE, MODE_ROLLING, MODE_CERTIFICATE, MODE_CERTIFICATE_NO_REUSE):
                times[mode], stats[mode] = _native_sample(lib, data, mode, reps)
            base = times[MODE_BASELINE]
            cert = times[MODE_CERTIFICATE]
            no_reuse = times[MODE_CERTIFICATE_NO_REUSE]
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "internal_repetitions": reps,
                "baseline_median_ns": base,
                "rolling_median_ns": times[MODE_ROLLING],
                "certificate_median_ns": cert,
                "certificate_no_reuse_median_ns": no_reuse,
                "rolling_ratio_over_baseline": times[MODE_ROLLING] / base,
                "certificate_ratio_over_baseline": cert / base,
                "certificate_ratio_over_no_reuse": cert / no_reuse,
                "modeled_incremental_state_bytes": MODELED_INCREMENTAL_STATE_BYTES,
                "modeled_extra_outgoing_byte_reads_per_pass": max(0, len(data) - CERT_WINDOW),
                "baseline_gear_lookups_per_pass": len(data),
                "fused_extra_gear_lookups_per_pass": max(0, len(data) - CERT_WINDOW),
                "no_reuse_extra_incoming_gear_lookups_per_pass": len(data),
                "certificate_updates_all_reps": int(stats[MODE_CERTIFICATE].certificate_updates),
                "heap_replacements_all_reps": int(stats[MODE_CERTIFICATE].heap_replacements),
                "native_witness_equal_reference": name not in witness_mismatches,
                "checksum": int(stats[MODE_CERTIFICATE].checksum),
            })

    large_gate_names = {"random_1mib", "compressed_like_1mib", "repeated_1mib", "shifted_version_1mib", "zeros_1mib"}
    large = [r for r in rows if r["case"] in large_gate_names]
    ratios = [float(r["certificate_ratio_over_baseline"]) for r in large]
    critical = [r for r in rows if r["case"] in {"random_1mib", "compressed_like_1mib"}]
    all_1m = [r for r in rows if int(r["input_bytes"]) >= 1024 * 1024 - 1024]
    fusion_ratios = [float(r["certificate_ratio_over_no_reuse"]) for r in large]
    gate = (
        not witness_mismatches
        and statistics.median(ratios) <= 1.20
        and all(float(r["certificate_ratio_over_baseline"]) <= 1.25 for r in critical)
        and all(float(r["certificate_ratio_over_baseline"]) <= 1.35 for r in all_1m)
        and statistics.median(fusion_ratios) <= 1.03
    )
    return {
        "schema": "cmpct-one-g02-local-gear-certificate-native-cost-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "large_internal_repetitions": LARGE_REPS,
        "modeled_incremental_state_bytes": MODELED_INCREMENTAL_STATE_BYTES,
        "native_witness_mismatches": witness_mismatches,
        "large_gate_median_certificate_ratio_over_baseline": statistics.median(ratios),
        "large_gate_median_certificate_ratio_over_no_reuse": statistics.median(fusion_ratios),
        "decision": "advance_certificate_to_end_to_end_efficiency_gate" if gate else "retire_unconditional_local_gear_certificate",
        "claim_boundary": "native carrying-cost viability only; no density, reader-speed, or end-to-end writer promotion claim",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_certificate_to_end_to_end_efficiency_gate" else 2)
