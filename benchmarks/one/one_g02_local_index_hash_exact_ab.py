"""ONE-G0.2 exact local-ring hash-index causal A/B.

Frozen by ONE_G02_LOCAL_INDEX_HASH_EXACT_PREREG_2026-09-06.md.
The candidate preserves the 64-entry ring as authoritative storage and adds a
bounded 128-bucket locator.  All real-input scanning and timing is native.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_relation_shared_observer_validation import _cases

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
CASES = (
    "shift_plus1", "damage_quarter", "fragmented_every96",
    "hostile_fixed_bands", "fragmented_every32", "independent_random",
)
ROUNDS = 17
MAX_PROBE_RATIO = 0.30
MAX_MEDIAN = 0.90
MAX_ROW = 1.03
MAX_STATE_RATIO = 2.50


class Result(ctypes.Structure):
    _fields_ = [
        ("lookup_events", ctypes.c_uint64),
        ("hits", ctypes.c_uint64),
        ("probes", ctypes.c_uint64),
        ("tombstones_created", ctypes.c_uint64),
        ("max_probe", ctypes.c_uint64),
        ("live_entries", ctypes.c_uint64),
        ("decision_checksum", ctypes.c_uint64),
        ("state_bytes", ctypes.c_uint64),
    ]


def _mix64(x: int) -> int:
    mask = (1 << 64) - 1
    x &= mask
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & mask
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & mask
    x ^= x >> 31
    return x & mask


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-local-hash-")
    lib = Path(td.name) / "liblocalhash.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_local_index_hash_exact_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    audit = c.one_g02_local_index_hash_audit
    audit.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                      ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(Result), ctypes.POINTER(Result)]
    audit.restype = ctypes.c_int
    measure = c.one_g02_local_index_hash_measure
    measure.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(Result), ctypes.POINTER(Result)]
    measure.restype = ctypes.c_int
    stream = c.one_g02_local_index_hash_key_stream_audit
    stream.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                       ctypes.POINTER(Result), ctypes.POINTER(Result)]
    stream.restype = ctypes.c_int
    return audit, measure, stream, td


def _collision_stream() -> list[int]:
    # Fill one low bucket with many distinct keys, then revisit earlier keys after
    # repeated evictions.  This attacks clustering/tombstone correctness rather
    # than pretending random byte corpora are a hash-table adversary.
    keys: list[int] = []
    x = 0
    while len(keys) < 192:
        if (_mix64(x) & 127) == 7:
            keys.append(x)
        x += 1
    return keys[:96] + keys[16:80] + keys[96:192] + keys[32:96]


def _cyclic_bytes(size: int) -> bytes:
    motif = bytes((i * 29 + (i >> 2) * 7) & 255 for i in range(257))
    return (motif * ((size + len(motif) - 1) // len(motif)))[:size]


def run() -> dict[str, object]:
    audit, measure, stream, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows: list[dict[str, object]] = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                generated = _cases(size, seed)
                data_cases = {name: generated[name][0] + generated[name][1] for name in CASES}
                data_cases["cyclic_local_hits"] = _cyclic_bytes(2 * size)
                for name, data in data_cases.items():
                    arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                    b0, c0 = Result(), Result()
                    rc = audit(arr, len(data), gear, ctypes.byref(b0), ctypes.byref(c0))
                    if rc != 0:
                        raise RuntimeError(f"semantic audit rc={rc} at {(size, seed, name)}")
                    base_samples: list[float] = []
                    cand_samples: list[float] = []
                    # Keep the native batch modest on large rows; each measure
                    # already executes A/B-B/A and all scan/Gear work is charged.
                    batch = 8 if size <= 16 * 1024 else (4 if size <= 64 * 1024 else 2)
                    last_b, last_c = b0, c0
                    for _ in range(ROUNDS):
                        bn, cn, br, cr = ctypes.c_double(), ctypes.c_double(), Result(), Result()
                        rc = measure(arr, len(data), gear, batch, ctypes.byref(bn), ctypes.byref(cn), ctypes.byref(br), ctypes.byref(cr))
                        if rc != 0:
                            raise RuntimeError(f"native measure rc={rc} at {(size, seed, name)}")
                        base_samples.append(float(bn.value)); cand_samples.append(float(cn.value))
                        last_b, last_c = br, cr
                    bmed = statistics.median(base_samples); cmed = statistics.median(cand_samples)
                    # The C kernel counts the lookup used to locate an eviction,
                    # but its defensive second bucket walk is not charged in the
                    # raw probe counter.  Gate on a conservative upper bound so
                    # probe evidence cannot be made optimistic by instrumentation.
                    candidate_probe_upper = int(last_c.probes + last_c.tombstones_created * last_c.max_probe)
                    rows.append({
                        "relation_bytes": size, "input_bytes": len(data), "seed": seed, "case": name,
                        "baseline_ns": bmed, "candidate_ns": cmed,
                        "candidate_over_baseline": cmed / bmed,
                        "lookup_events": int(last_b.lookup_events), "hits": int(last_b.hits),
                        "baseline_probes": int(last_b.probes), "candidate_raw_probes": int(last_c.probes),
                        "candidate_conservative_probe_upper": candidate_probe_upper,
                        "candidate_max_probe": int(last_c.max_probe),
                        "candidate_tombstones": int(last_c.tombstones_created),
                        "baseline_state_bytes": int(last_b.state_bytes), "candidate_state_bytes": int(last_c.state_bytes),
                        "state_ratio": int(last_c.state_bytes) / int(last_b.state_bytes),
                        "decision_checksum_exact": int(last_b.decision_checksum) == int(last_c.decision_checksum),
                    })

        hostile_keys = _collision_stream()
        key_arr = (ctypes.c_uint64 * len(hostile_keys))(*hostile_keys)
        hb, hc = Result(), Result()
        hrc = stream(key_arr, len(hostile_keys), ctypes.byref(hb), ctypes.byref(hc))
        hostile = {
            "key_count": len(hostile_keys), "audit_rc": hrc,
            "decision_checksum_exact": int(hb.decision_checksum) == int(hc.decision_checksum),
            "hits_exact": int(hb.hits) == int(hc.hits),
            "live_entries_exact": int(hb.live_entries) == int(hc.live_entries),
            "baseline_probes": int(hb.probes), "candidate_raw_probes": int(hc.probes),
            "candidate_max_probe": int(hc.max_probe), "candidate_tombstones": int(hc.tombstones_created),
        }

        semantic_ok = (
            hrc == 0 and bool(hostile["decision_checksum_exact"]) and bool(hostile["hits_exact"])
            and bool(hostile["live_entries_exact"])
            and all(bool(r["decision_checksum_exact"]) for r in rows)
        )
        total_bprobes = sum(int(r["baseline_probes"]) for r in rows)
        total_cupper = sum(int(r["candidate_conservative_probe_upper"]) for r in rows)
        probe_ratio = total_cupper / total_bprobes if total_bprobes else float("inf")
        size_medians: dict[str, float] = {}
        for size in SIZES:
            vals = [float(r["candidate_over_baseline"]) for r in rows if int(r["relation_bytes"]) == size]
            size_medians[str(size)] = float(statistics.median(vals))
        mature_size_medians = [v for k, v in size_medians.items() if int(k) >= 16 * 1024]
        worst_row = max(float(r["candidate_over_baseline"]) for r in rows)
        state_ratio = max(float(r["state_ratio"]) for r in rows)
        perf_ok = (
            probe_ratio <= MAX_PROBE_RATIO
            and all(v <= MAX_MEDIAN for v in mature_size_medians)
            and worst_row <= MAX_ROW
            and state_ratio <= MAX_STATE_RATIO
        )
        if not semantic_ok:
            decision = "reject_exact_local_index_hash"
        elif perf_ok:
            decision = "advance_exact_local_index_hash"
        else:
            decision = "hold_exact_local_index_hash"
        return {
            "schema": "cmpct-one-g02-local-index-hash-exact-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "semantic_ok": semantic_ok,
            "aggregate_candidate_probe_upper_over_baseline": probe_ratio,
            "size_medians_candidate_over_baseline": size_medians,
            "worst_row_candidate_over_baseline": worst_row,
            "max_state_ratio": state_ratio,
            "hostile_collision_stream": hostile,
            "decision": decision,
            "claim_boundary": "native local-index lookup causal A/B only; not fused-observer, writer, density, or comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "reject_exact_local_index_hash" else 1)
