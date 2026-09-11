"""ONE-G0.2 native replay-vs-queue causal decomposition.

Superseding experiment; the prior observation-vs-full result is immutable evidence.

Referee hypothesis
------------------
The ~31% full-rescue/observation penalty on entropy-dense controls is primarily queue
construction/maintenance rather than the bounded Gear replay itself.

Frozen disproof / interpretation
--------------------------------
- replay-only must exactly match the full arm's final Gear state, considered positions,
  sparse anchors, rescue-active positions and replayed-history byte count;
- replay-only/observation median >=1.10 on either entropy-dense control means replay
  arithmetic itself is material and rejects queue-primary attribution;
- queue may be named primary only if replay-only/observation <1.10 on both entropy controls
  AND full/replay-only >1.10 on both.
This is encoder-discovery causal evidence only; no stored-byte, reader, product, comparator
or release authority.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_starvation_native_cost_decomposition import (
    ROUNDS, _ObservationResult, _bind_observation, _call_observation, _cases,
)
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _bind_gate, _call_gate


class _ReplayResult(ctypes.Structure):
    _fields_ = [
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("sparse_anchors", ctypes.c_uint64),
        ("rescue_active_positions", ctypes.c_uint64),
        ("activation_events", ctypes.c_uint64),
        ("replayed_history_bytes", ctypes.c_uint64),
        ("replay_checksum", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-replay-queue-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_starvation_observation_kernel.c"),
        str(here / "one_g02_starvation_replay_only_kernel.c"),
        str(here / "one_g02_starvation_byte_history_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)), td


def _bind_replay(lib):
    fn = lib.one_g02_starvation_replay_only_kernel
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                   ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
                   ctypes.POINTER(_ReplayResult)]
    fn.restype = ctypes.c_int
    return fn


def _call_replay(fn, gear, arr, length):
    out = _ReplayResult()
    rc = fn(arr, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"replay-only kernel failed: {rc}")
    return out


def _ratio(first, second):
    ratios = []
    for i in range(ROUNDS):
        if i % 2 == 0:
            t0 = time.perf_counter_ns(); first(); a = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); second(); b = time.perf_counter_ns() - t0
        else:
            t0 = time.perf_counter_ns(); second(); b = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); first(); a = time.perf_counter_ns() - t0
        ratios.append(b / a)
    return ratios


def run():
    lib, td = _build()
    try:
        obs_fn = _bind_observation(lib)
        replay_fn = _bind_replay(lib)
        full_fn = _bind_gate(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows = []
        for name, data in _cases().items():
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            obs = _call_observation(obs_fn, gear, arr, len(data))
            replay = _call_replay(replay_fn, gear, arr, len(data))
            full = _call_gate(full_fn, gear, arr, len(data))
            equal = (
                int(replay.final_state) == int(full.final_state) == int(obs.final_state)
                and int(replay.positions_considered) == int(full.positions_considered) == int(obs.positions_considered)
                and int(replay.sparse_anchors) == int(full.sparse_anchors) == int(obs.sparse_anchors)
                and int(replay.rescue_active_positions) == int(full.rescue_active_positions) == int(obs.rescue_active_positions)
                and int(replay.replayed_history_bytes) == int(full.replayed_history_bytes)
            )
            if not equal:
                raise AssertionError((name, "replay/full/observation semantic accounting mismatch"))
            replay_over_obs = _ratio(
                lambda: _call_observation(obs_fn, gear, arr, len(data)),
                lambda: _call_replay(replay_fn, gear, arr, len(data)),
            )
            full_over_replay = _ratio(
                lambda: _call_replay(replay_fn, gear, arr, len(data)),
                lambda: _call_gate(full_fn, gear, arr, len(data)),
            )
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "semantic_accounting_equal": equal,
                "median_replay_only_over_observation": statistics.median(replay_over_obs),
                "p90_replay_only_over_observation": sorted(replay_over_obs)[int(.9 * (len(replay_over_obs)-1))],
                "median_full_over_replay_only": statistics.median(full_over_replay),
                "p90_full_over_replay_only": sorted(full_over_replay)[int(.9 * (len(full_over_replay)-1))],
                "observation_reserved_state_bytes": int(obs.reserved_state_bytes),
                "replay_reserved_state_bytes": int(replay.reserved_state_bytes),
                "full_reserved_state_bytes": int(full.reserved_state_bytes),
                "activation_events": int(replay.activation_events),
                "replayed_history_bytes": int(replay.replayed_history_bytes),
                "full_peak_queue_entries": int(full.peak_queue_entries),
            })
        m = {r["case"]: r for r in rows}
        entropy = [m["random_1mib"], m["zlib_random_1mib"]]
        replay_material = any(r["median_replay_only_over_observation"] >= 1.10 for r in entropy)
        queue_primary = (not replay_material) and all(r["median_full_over_replay_only"] > 1.10 for r in entropy)
        if replay_material:
            decision = "reject_queue_primary_attribution_replay_is_material"
        elif queue_primary:
            decision = "advance_queue_construction_maintenance_owner_attack"
        else:
            decision = "replay_queue_decomposition_inconclusive"
        return {
            "schema": "cmpct-one-g02-starvation-replay-queue-decomposition-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "hypothesis": "queue construction/maintenance, not bounded Gear replay arithmetic, primarily owns the full-rescue regression",
            "disproof": "replay-only/observation median >=1.10 on either entropy control rejects queue-primary attribution; queue-primary requires <1.10 replay/observation and >1.10 full/replay on both",
            "decision": decision,
            "claim_boundary": "native encoder-discovery causal decomposition only; no stored-byte, reader, product, comparator, or release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
