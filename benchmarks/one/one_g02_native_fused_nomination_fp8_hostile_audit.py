"""Hostile semantic audit for the ONE-G0.2 mirrored-fp8 fused-nomination candidate.

This deliberately removes the fp8 filter's selectivity: >64 distinct full keys
share one fp8 value, forcing wrap/eviction and full-key collision checks. Real
hits and post-eviction misses are then interleaved. The authoritative linear
ring and the promoted mirrored-fp8 ring must make exactly the same decisions.
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
from pathlib import Path


class LocalIndexResult(ctypes.Structure):
    _fields_ = [
        ("lookup_events", ctypes.c_uint64), ("hits", ctypes.c_uint64),
        ("full_key_checks", ctypes.c_uint64), ("fingerprint_bytes", ctypes.c_uint64),
        ("live_entries", ctypes.c_uint64), ("decision_checksum", ctypes.c_uint64),
        ("state_bytes", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fp8-hostile-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_local_index_fingerprint_view_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    fn = c.one_g02_local_index_fp_key_stream_audit
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                   ctypes.POINTER(LocalIndexResult), ctypes.POINTER(LocalIndexResult)]
    fn.restype = ctypes.c_int
    return fn, td


def _collision_wrap_stream() -> list[int]:
    # All keys have fp8 0xA5 while their full 64-bit values differ.
    prefix = 0xA5 << 56
    distinct = [prefix | ((i * 0x9E3779B97F4A7C15) & ((1 << 56) - 1)) for i in range(96)]
    # 96 distinct misses force 32 evictions after filling the 64-entry ring.
    stream = list(distinct)
    # Hits known to remain resident, repeated to audit hit decisions.
    stream += [distinct[95], distinct[64], distinct[80], distinct[95], distinct[70]]
    # Old evicted values must now be misses and re-enter, causing further wrap.
    stream += [distinct[0], distinct[1], distinct[2], distinct[3], distinct[4]]
    # Mix resident repeats and more same-fp8 distinct keys.
    stream += [distinct[95], prefix | 0x0000000000ABCDEF, distinct[4], prefix | 0x0000000000123456]
    return stream


def run() -> dict[str, object]:
    fn, td = _build()
    try:
        keys = _collision_wrap_stream()
        arr = (ctypes.c_uint64 * len(keys))(*keys)
        b, c = LocalIndexResult(), LocalIndexResult()
        rc = fn(arr, len(keys), ctypes.byref(b), ctypes.byref(c))
        exact = (
            rc == 0 and b.lookup_events == c.lookup_events and b.hits == c.hits
            and b.live_entries == c.live_entries
            and b.decision_checksum == c.decision_checksum
        )
        return {
            "schema": "cmpct-one-g02-native-fused-nomination-fp8-hostile-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "keys": len(keys),
            "all_keys_same_fp8": True,
            "distinct_prefix_keys": 96,
            "ring_capacity": 64,
            "forced_evictions_before_repeats": 32,
            "baseline_lookup_events": int(b.lookup_events),
            "candidate_lookup_events": int(c.lookup_events),
            "baseline_hits": int(b.hits),
            "candidate_hits": int(c.hits),
            "baseline_full_key_checks": int(b.full_key_checks),
            "candidate_full_key_checks": int(c.full_key_checks),
            "baseline_decision_checksum": int(b.decision_checksum),
            "candidate_decision_checksum": int(c.decision_checksum),
            "baseline_state_bytes": int(b.state_bytes),
            "candidate_state_bytes": int(c.state_bytes),
            "state_delta_bytes": int(c.state_bytes) - int(b.state_bytes),
            "decision": "hostile_fp8_exact" if exact and int(c.state_bytes)-int(b.state_bytes) == 128 else "hostile_fp8_mismatch",
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "hostile_fp8_exact" else 1)
