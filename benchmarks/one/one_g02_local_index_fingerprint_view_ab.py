"""ONE-G0.2 compact fingerprint ring-view A/B.

Frozen by ONE_G02_LOCAL_INDEX_FINGERPRINT_VIEW_PREREG_2026-09-06.md and its
hostile amendment. The candidate keeps the authoritative 64-entry ring and
adds a duplicated 128-byte fingerprint view so logical ring order is one
contiguous memchr span.
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
MAX_FULL_KEY_RATIO = 0.10
MAX_MEDIAN = 0.90
MAX_ROW = 1.03
MAX_STATE_RATIO = 1.10
MAX_HIT_RICH = 1.03


class Result(ctypes.Structure):
    _fields_ = [
        ("lookup_events", ctypes.c_uint64),
        ("hits", ctypes.c_uint64),
        ("full_key_checks", ctypes.c_uint64),
        ("fingerprint_bytes", ctypes.c_uint64),
        ("live_entries", ctypes.c_uint64),
        ("decision_checksum", ctypes.c_uint64),
        ("state_bytes", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-local-fp-")
    lib = Path(td.name) / "liblocalfp.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_local_index_fingerprint_view_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    audit = c.one_g02_local_index_fp_audit
    audit.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                      ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(Result), ctypes.POINTER(Result)]
    audit.restype = ctypes.c_int
    measure = c.one_g02_local_index_fp_measure
    measure.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(Result), ctypes.POINTER(Result)]
    measure.restype = ctypes.c_int
    stream = c.one_g02_local_index_fp_key_stream_audit
    stream.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                       ctypes.POINTER(Result), ctypes.POINTER(Result)]
    stream.restype = ctypes.c_int
    stream_measure = c.one_g02_local_index_fp_key_stream_measure
    stream_measure.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
                               ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                               ctypes.POINTER(Result), ctypes.POINTER(Result)]
    stream_measure.restype = ctypes.c_int
    return audit, measure, stream, stream_measure, td


def _same_fingerprint_stream() -> list[int]:
    keys = [((0xA5 << 56) | i) for i in range(192)]
    return keys[:96] + keys[16:80] + keys[96:192] + keys[32:96]


def _hit_rich_stream() -> list[int]:
    # 64 distinct live keys with deliberately varied high-byte fingerprints,
    # then 4,096 guaranteed hits cycling those same keys.
    warm = [(((i * 37) & 0xFF) << 56) | (UINT := (i * 0x9E3779B97F4A7C15 & ((1 << 56) - 1))) for i in range(64)]
    return warm + [warm[i & 63] for i in range(4096)]


def _cyclic_bytes(size: int) -> bytes:
    # Structured byte input retained from the original preregistration.  It is
    # not treated as a guaranteed local-hit generator; the hostile amendment
    # adds the explicit key-stream hit control below.
    motif = bytes((i * 29 + (i >> 2) * 7) & 255 for i in range(257))
    return (motif * ((size + len(motif) - 1) // len(motif)))[:size]


def run() -> dict[str, object]:
    audit, measure, stream, stream_measure, td = _build()
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
                    bs: list[float] = []
                    cs: list[float] = []
                    batch = 8 if size <= 16 * 1024 else (4 if size <= 64 * 1024 else 2)
                    last_b, last_c = b0, c0
                    for _ in range(ROUNDS):
                        bn, cn, br, cr = ctypes.c_double(), ctypes.c_double(), Result(), Result()
                        rc = measure(arr, len(data), gear, batch, ctypes.byref(bn), ctypes.byref(cn), ctypes.byref(br), ctypes.byref(cr))
                        if rc != 0:
                            raise RuntimeError(f"native measure rc={rc} at {(size, seed, name)}")
                        bs.append(float(bn.value)); cs.append(float(cn.value)); last_b, last_c = br, cr
                    bmed, cmed = statistics.median(bs), statistics.median(cs)
                    rows.append({
                        "relation_bytes": size, "input_bytes": len(data), "seed": seed, "case": name,
                        "baseline_ns": bmed, "candidate_ns": cmed,
                        "candidate_over_baseline": cmed / bmed,
                        "lookup_events": int(last_b.lookup_events), "hits": int(last_b.hits),
                        "baseline_full_key_checks": int(last_b.full_key_checks),
                        "candidate_full_key_checks": int(last_c.full_key_checks),
                        "candidate_fingerprint_bytes": int(last_c.fingerprint_bytes),
                        "baseline_state_bytes": int(last_b.state_bytes), "candidate_state_bytes": int(last_c.state_bytes),
                        "state_ratio": int(last_c.state_bytes) / int(last_b.state_bytes),
                        "decision_checksum_exact": int(last_b.decision_checksum) == int(last_c.decision_checksum),
                    })

        hostile_keys = _same_fingerprint_stream()
        hostile_arr = (ctypes.c_uint64 * len(hostile_keys))(*hostile_keys)
        hb, hc = Result(), Result()
        hrc = stream(hostile_arr, len(hostile_keys), ctypes.byref(hb), ctypes.byref(hc))
        hostile = {
            "key_count": len(hostile_keys), "audit_rc": hrc,
            "decision_checksum_exact": int(hb.decision_checksum) == int(hc.decision_checksum),
            "hits_exact": int(hb.hits) == int(hc.hits),
            "live_entries_exact": int(hb.live_entries) == int(hc.live_entries),
            "baseline_full_key_checks": int(hb.full_key_checks),
            "candidate_full_key_checks": int(hc.full_key_checks),
            "candidate_fingerprint_bytes": int(hc.fingerprint_bytes),
        }

        hit_keys = _hit_rich_stream()
        hit_arr = (ctypes.c_uint64 * len(hit_keys))(*hit_keys)
        hit_bs: list[float] = []
        hit_cs: list[float] = []
        hit_b = hit_c = Result()
        for _ in range(ROUNDS):
            bn, cn, br, cr = ctypes.c_double(), ctypes.c_double(), Result(), Result()
            rc = stream_measure(hit_arr, len(hit_keys), 32, ctypes.byref(bn), ctypes.byref(cn), ctypes.byref(br), ctypes.byref(cr))
            if rc != 0:
                raise RuntimeError(f"hit-rich native measure rc={rc}")
            hit_bs.append(float(bn.value)); hit_cs.append(float(cn.value)); hit_b, hit_c = br, cr
        hit_bmed, hit_cmed = statistics.median(hit_bs), statistics.median(hit_cs)
        hit_rich = {
            "key_count": len(hit_keys),
            "expected_hits_after_warmup": 4096,
            "baseline_ns": hit_bmed, "candidate_ns": hit_cmed,
            "candidate_over_baseline": hit_cmed / hit_bmed,
            "baseline_hits": int(hit_b.hits), "candidate_hits": int(hit_c.hits),
            "hits_exact": int(hit_b.hits) == int(hit_c.hits),
            "baseline_full_key_checks": int(hit_b.full_key_checks),
            "candidate_full_key_checks": int(hit_c.full_key_checks),
            "decision_checksum_exact": int(hit_b.decision_checksum) == int(hit_c.decision_checksum),
            "live_entries_exact": int(hit_b.live_entries) == int(hit_c.live_entries),
        }

        semantic_ok = (
            hrc == 0 and bool(hostile["decision_checksum_exact"]) and bool(hostile["hits_exact"])
            and bool(hostile["live_entries_exact"])
            and bool(hit_rich["decision_checksum_exact"]) and bool(hit_rich["hits_exact"])
            and bool(hit_rich["live_entries_exact"]) and int(hit_rich["baseline_hits"]) == 4096
            and all(bool(r["decision_checksum_exact"]) for r in rows)
        )
        total_b = sum(int(r["baseline_full_key_checks"]) for r in rows)
        total_c = sum(int(r["candidate_full_key_checks"]) for r in rows)
        full_key_ratio = total_c / total_b if total_b else float("inf")
        size_medians: dict[str, float] = {}
        for size in SIZES:
            vals = [float(r["candidate_over_baseline"]) for r in rows if int(r["relation_bytes"]) == size]
            size_medians[str(size)] = float(statistics.median(vals))
        mature = [v for k, v in size_medians.items() if int(k) >= 16 * 1024]
        worst = max(float(r["candidate_over_baseline"]) for r in rows)
        state_ratio = max(float(r["state_ratio"]) for r in rows)
        hostile_work_ok = int(hostile["candidate_full_key_checks"]) <= int(hostile["baseline_full_key_checks"])
        hit_work_ok = int(hit_rich["candidate_full_key_checks"]) <= int(hit_rich["baseline_full_key_checks"])
        hit_time_ok = float(hit_rich["candidate_over_baseline"]) <= MAX_HIT_RICH
        perf_ok = (
            full_key_ratio <= MAX_FULL_KEY_RATIO and all(v <= MAX_MEDIAN for v in mature)
            and worst <= MAX_ROW and state_ratio <= MAX_STATE_RATIO and hostile_work_ok
            and hit_work_ok and hit_time_ok
        )
        decision = (
            "reject_local_index_fingerprint_view" if not semantic_ok else
            "advance_local_index_fingerprint_view" if perf_ok else
            "hold_local_index_fingerprint_view"
        )
        return {
            "schema": "cmpct-one-g02-local-index-fingerprint-view-ab",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "semantic_ok": semantic_ok,
            "aggregate_candidate_full_key_checks_over_baseline": full_key_ratio,
            "size_medians_candidate_over_baseline": size_medians,
            "worst_row_candidate_over_baseline": worst,
            "max_state_ratio": state_ratio,
            "hostile_same_fingerprint_stream": hostile,
            "hit_rich_stream": hit_rich,
            "decision": decision,
            "claim_boundary": "native exact local-index causal A/B only; duplicated fingerprint view and true hit-rich control fully charged; not fused-observer, writer, density, or comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "reject_local_index_fingerprint_view" else 1)
