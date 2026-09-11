"""ONE-G0.2 native cost decomposition for deferred byte-history rescue.

Referee freeze before result-bearing execution
==============================================
The byte-history rescue preserved all 35 generator-distinct hard-rescue rows with only
4,112 B of modeled incremental history, but the compiled full rescue lost to the promoted
8 KiB tail-return selector and carried a 4,096-entry monotonic queue. This experiment
separates the always-on observation/cache cost from replay/queue materialization.

The observation arm preserves the exact Gear recurrence, sparse-anchor starvation signal,
run-dominance suppression, and 4,096-byte replay cache, but performs no replay and emits no
minimizer nominations. The full arm is the already-result-bearing byte-history rescue. Both
are compared with the current promoted selector baseline on identical inputs.

Falsification / interpretation freeze:
- any observation/full disagreement in final Gear state, positions considered, sparse anchors,
  or rescue-active positions rejects the decomposition;
- observation/baseline median >= 0.90 on either entropy-dense ~1 MiB control rejects the claim
  that the always-on observation/cache shape leaves material compute headroom;
- only if observation/baseline < 0.90 on both entropy controls AND full/observation > 1.10 on
  both may replay/queue materialization be named the primary exported compute owner.
No arm has stored-byte, reader, product-speed, or release authority.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time
import zlib

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch, _call_dispatch
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _GateResult, _bind_gate, _call_gate

ROUNDS = 13


class _ObservationResult(ctypes.Structure):
    _fields_ = [
        ("final_state", ctypes.c_uint64),
        ("history_seed", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("sparse_anchors", ctypes.c_uint64),
        ("rescue_active_positions", ctypes.c_uint64),
        ("activation_events", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-starvation-decomp-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
            str(here / "one_g02_starvation_byte_history_kernel.c"),
            str(here / "one_g02_starvation_observation_kernel.c"),
            "-o", str(lib),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_observation(lib):
    fn = lib.one_g02_starvation_observation_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_ObservationResult),
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_observation(fn, gear, arr, length: int):
    out = _ObservationResult()
    rc = fn(arr, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"starvation observation kernel failed: {rc}")
    return out


def _paired_ratios(a, b):
    ratios = []
    for i in range(ROUNDS):
        if i % 2 == 0:
            t0 = time.perf_counter_ns(); a(); ta = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); b(); tb = time.perf_counter_ns() - t0
        else:
            t0 = time.perf_counter_ns(); b(); tb = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); a(); ta = time.perf_counter_ns() - t0
        ratios.append(tb / ta)
    return ratios


def _cases():
    rnd = random.Random(8801).randbytes(1024 * 1024)
    basis = random.Random(8802).randbytes(64 * 1024)
    shifted = random.Random(8803).randbytes(512 * 1024)
    hard = random.Random(10).randbytes(4096)
    boundary = random.Random(8811).randbytes(4160)
    return {
        "random_1mib": rnd,
        "zlib_random_1mib": zlib.compress(rnd, level=9),
        "repeat_64k_basis_1mib": basis * 16,
        "shifted_512k_insert1": shifted + b"X" + shifted,
        "boundary_random_4160": boundary,
        "transfer_starved_seed10_insert1": hard + b"X" + hard,
    }


def run():
    lib, td = _build()
    try:
        observation = _bind_observation(lib)
        full = _bind_gate(lib)
        baseline = _bind_dispatch(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows = []
        correctness = True
        for name, data in _cases().items():
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            obs_once = _call_observation(observation, gear, arr, len(data))
            full_once = _call_gate(full, gear, arr, len(data))
            base_once = _call_dispatch(baseline, gear, arr, len(data))
            equal = (
                int(obs_once.final_state) == int(full_once.final_state)
                and int(obs_once.positions_considered) == int(full_once.positions_considered)
                and int(obs_once.sparse_anchors) == int(full_once.sparse_anchors)
                and int(obs_once.rescue_active_positions) == int(full_once.rescue_active_positions)
            )
            correctness &= equal
            if not equal:
                raise AssertionError((name, "observation/full gate mismatch"))

            obs_over_base = _paired_ratios(
                lambda: _call_dispatch(baseline, gear, arr, len(data)),
                lambda: _call_observation(observation, gear, arr, len(data)),
            )
            full_over_obs = _paired_ratios(
                lambda: _call_observation(observation, gear, arr, len(data)),
                lambda: _call_gate(full, gear, arr, len(data)),
            )
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "observation_full_equal": equal,
                "median_observation_over_promoted_baseline": statistics.median(obs_over_base),
                "p90_observation_over_promoted_baseline": sorted(obs_over_base)[int(0.9 * (len(obs_over_base) - 1))],
                "median_full_rescue_over_observation": statistics.median(full_over_obs),
                "p90_full_rescue_over_observation": sorted(full_over_obs)[int(0.9 * (len(full_over_obs) - 1))],
                "promoted_baseline_reserved_state_bytes": int(base_once.reserved_state_bytes),
                "observation_reserved_state_bytes": int(obs_once.reserved_state_bytes),
                "full_rescue_reserved_state_bytes": int(full_once.reserved_state_bytes),
                "sparse_anchors": int(obs_once.sparse_anchors),
                "rescue_active_positions": int(obs_once.rescue_active_positions),
                "activation_events": int(obs_once.activation_events),
                "full_replayed_history_bytes": int(full_once.replayed_history_bytes),
                "full_peak_queue_entries": int(full_once.peak_queue_entries),
            })

        by_name = {r["case"]: r for r in rows}
        entropy = [by_name["random_1mib"], by_name["zlib_random_1mib"]]
        observation_headroom = correctness and all(
            r["median_observation_over_promoted_baseline"] < 0.90 for r in entropy
        )
        replay_primary_owner = observation_headroom and all(
            r["median_full_rescue_over_observation"] > 1.10 for r in entropy
        )
        if not observation_headroom:
            decision = "reject_byte_history_observation_as_primary_compute_shape"
        elif replay_primary_owner:
            decision = "advance_replay_queue_owner_attack"
        else:
            decision = "decomposition_inconclusive_multiple_owners"

        return {
            "schema": "cmpct-one-g02-starvation-native-cost-decomposition-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "frozen_gate_gap_positions": MINIMIZER_SPAN,
            "promoted_dispatch_boundary_bytes": 8192,
            "hypothesis": "the 4,096-byte observation/cache shape leaves material negative-control compute headroom, and replay/queue materialization rather than always-on observation owns the compiled rescue regression",
            "disproof": "semantic mismatch or observation/baseline median >=0.90 on either entropy-dense control rejects observation headroom; replay is primary owner only if full/observation median >1.10 on both",
            "decision": decision,
            "claim_boundary": "native encoder-discovery causal decomposition only; no exact proof/index/Law, stored-byte, reader, product-speed, comparator, or release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
