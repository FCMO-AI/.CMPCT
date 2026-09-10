"""ONE-G0.2 trusted-prior multi-generation lifecycle falsifier.

Frozen by ONE_G02_TRUSTED_PRIOR_CHAIN_LIFECYCLE_PREREG_2026-09-10.md.
This is independent transfer evidence; it does not touch the Genesis gate corpus.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import random
import statistics
import time

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import _build_native
from benchmarks.one.one_g02_lazy_segment_timing import _equivalent, _semantic_signature, _writer_once
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _shifted
from experiments.one.ir import Ref, Root

SIZE = 1 << 20
TRANSITIONS = (2, 4, 8)
FAMILIES = ("shift_plus1", "fragmented_every96", "independent_random")
REPETITIONS = 9


def _build_chain(family: str, transitions: int) -> list[bytes]:
    base = random.Random(51000).randbytes(SIZE)
    versions = [base]
    for generation in range(1, transitions + 1):
        previous = versions[-1]
        if family == "shift_plus1":
            current = _shifted(previous)
        elif family == "fragmented_every96":
            current = _shifted(previous, spacing=96)
        elif family == "independent_random":
            current = random.Random(52000 + generation).randbytes(SIZE)
        else:
            raise ValueError(f"unknown family: {family}")
        versions.append(current)
    return versions


def _transition(admission_fn, segment_fn, source: bytes, target: bytes, previous_digest: str):
    n = len(source)
    src_arr = (ctypes.c_uint8 * n).from_buffer_copy(source)
    dst_arr = (ctypes.c_uint8 * n).from_buffer_copy(target)
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), n, previous_digest)
    value = _writer_once(
        "lazy", admission_fn, segment_fn, source, target,
        src_arr, dst_arr, previous_root, current_digest,
    )
    return value, current_digest


def _lifecycle(arm: str, admission_fn, segment_fn, versions: list[bytes]):
    signatures = []
    wires = []
    if arm == "trusted_prior":
        prior_digest = sha256(versions[0]).hexdigest()  # charged trust establishment
    elif arm == "rehash_both":
        prior_digest = ""
    else:
        raise ValueError(f"unknown arm: {arm}")

    for source, target in zip(versions, versions[1:]):
        if arm == "rehash_both":
            prior_digest = sha256(source).hexdigest()
        value, current_digest = _transition(
            admission_fn, segment_fn, source, target, prior_digest
        )
        sig = _semantic_signature(value, source, target)
        signatures.append(sig)
        wires.append(int(sig["wire_total_bytes"]))
        if sig["previous_sha256"] != prior_digest or sig["current_sha256"] != current_digest:
            raise AssertionError("writer root identity diverged from lifecycle state")
        # The current digest has just been computed and embedded/validated by the
        # same writer transition, so it becomes the only admissible next prior.
        prior_digest = current_digest
    return signatures, wires


def _ratio(candidate: float, control: float) -> float:
    return candidate / control if control else float("inf")


def run() -> dict:
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for transitions in TRANSITIONS:
            for family in FAMILIES:
                versions = _build_chain(family, transitions)
                # Independent digest oracle for every generation, outside timings.
                oracle_digests = [sha256(value).hexdigest() for value in versions]

                control_sig, control_wires = _lifecycle(
                    "rehash_both", admission_fn, segment_fn, versions
                )
                trusted_sig, trusted_wires = _lifecycle(
                    "trusted_prior", admission_fn, segment_fn, versions
                )
                case_semantic = (
                    len(control_sig) == len(trusted_sig) == transitions
                    and control_wires == trusted_wires
                    and all(_equivalent(a, b) for a, b in zip(control_sig, trusted_sig))
                    and all(
                        trusted_sig[i]["previous_sha256"] == oracle_digests[i]
                        and trusted_sig[i]["current_sha256"] == oracle_digests[i + 1]
                        for i in range(transitions)
                    )
                )
                semantic_ok &= case_semantic

                wall = {"rehash_both": [], "trusted_prior": []}
                cpu = {"rehash_both": [], "trusted_prior": []}
                for rep in range(REPETITIONS):
                    order = (
                        ("rehash_both", "trusted_prior")
                        if rep % 2 == 0
                        else ("trusted_prior", "rehash_both")
                    )
                    for arm in order:
                        t0_wall = time.perf_counter_ns()
                        t0_cpu = time.process_time_ns()
                        sigs, emitted_wires = _lifecycle(
                            arm, admission_fn, segment_fn, versions
                        )
                        t1_cpu = time.process_time_ns()
                        t1_wall = time.perf_counter_ns()
                        # Keep timed outputs live through the timing boundary, then
                        # verify only cheap invariants after clocks stop.
                        if emitted_wires != control_wires or len(sigs) != transitions:
                            raise AssertionError("timed lifecycle changed canonical output")
                        wall[arm].append(t1_wall - t0_wall)
                        cpu[arm].append(t1_cpu - t0_cpu)

                control_wall = float(statistics.median(wall["rehash_both"]))
                trusted_wall = float(statistics.median(wall["trusted_prior"]))
                control_cpu = float(statistics.median(cpu["rehash_both"]))
                trusted_cpu = float(statistics.median(cpu["trusted_prior"]))
                rows.append({
                    "family": family,
                    "transitions": transitions,
                    "semantic_ok": case_semantic,
                    "canonical_wire_bytes_total": sum(control_wires),
                    "rehash_both_wall_ns_median": control_wall,
                    "trusted_wall_ns_median": trusted_wall,
                    "trusted_over_rehash_wall": _ratio(trusted_wall, control_wall),
                    "rehash_both_cpu_ns_median": control_cpu,
                    "trusted_cpu_ns_median": trusted_cpu,
                    "trusted_over_rehash_cpu": _ratio(trusted_cpu, control_cpu),
                    "candidate_initial_trust_hashes": 1,
                    "candidate_current_hashes": transitions,
                    "control_previous_hashes": transitions,
                    "control_current_hashes": transitions,
                })
    finally:
        if was_enabled:
            gc.enable()
        td.cleanup()

    by_key = {(row["transitions"], row["family"]): row for row in rows}
    complete = set(by_key) == {(n, family) for n in TRANSITIONS for family in FAMILIES}
    if not semantic_ok or not complete:
        decision = "INVALIDATE_TRUSTED_PRIOR_CHAIN_LIFECYCLE"
    else:
        decision_rows = {family: by_key[(8, family)] for family in FAMILIES}
        economics_ok = (
            decision_rows["shift_plus1"]["trusted_over_rehash_cpu"] <= 0.90
            and decision_rows["fragmented_every96"]["trusted_over_rehash_cpu"] <= 1.00
            and decision_rows["independent_random"]["trusted_over_rehash_cpu"] <= 0.85
            and all(row["trusted_over_rehash_wall"] <= 1.02 for row in decision_rows.values())
        )
        decision = (
            "ADVANCE_TRUSTED_PRIOR_CHAIN_LIFECYCLE"
            if economics_ok
            else "HOLD_TRUSTED_PRIOR_CHAIN_LIFECYCLE"
        )

    return {
        "schema": "cmpct-one-g02-trusted-prior-chain-lifecycle-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "size": SIZE,
        "transitions": list(TRANSITIONS),
        "families": list(FAMILIES),
        "repetitions": REPETITIONS,
        "semantic_gates_pass": semantic_ok,
        "decision": decision,
        "claim_boundary": (
            "adjacent-version chain lifecycle only; candidate charges initial prior-root SHA-256 once, then reuses each "
            "newly established current-root digest as immutable trusted state; no Genesis-gate corpus/comparator scoring, "
            "authenticated placement, filesystem traversal, decode timing, or trust-without-provenance authority"
        ),
        "rows": rows,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_TRUSTED_PRIOR_CHAIN_LIFECYCLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
