"""ONE-G0.2 observer-compatible band nomination before sparse relation proof.

Frozen before result-bearing execution.

Mission Lock
------------
The sparse relation gate has passed as a cheap falsifier *after* a source/target
pair is already known. Pair identity is therefore the next exported cost. This
experiment removes that gift without reopening quadratic search as the design:
a tiny set of shift-normalized byte bands nominates pairs from content, then the
promoted sparse gate and exact safe dispatcher remain authoritative.

For each object, sixteen deterministic interior probe positions are divided into
four four-byte bands. A source object contributes one zero-shift signature per
band. A later object contributes signatures for the four exact shifts already
owned by the relation proof (-2,-1,+1,+2). Matching any band nominates the prior
source/current-target pair. Pair identities are deduplicated before proof.

The signatures are deliberately plain sampled bytes rather than a new codec or
reader primitive. They are writer-only observation evidence and can be gathered
while bytes pass the fused observer. This experiment nevertheless charges 80
sampled feature bytes per object (16 source + 4*16 shifted target bytes) so the
sampling bill remains explicit rather than gifted.

Frozen corpus at each of 4, 8, 16, 32, 64, 128 and 256 KiB contains 24 objects:
one deterministic random basis, its three productive shifted derivatives, the
frozen every-32-byte relation-like negative, and nineteen generator-distinct
random distractors. The all-pairs exact safe dispatcher is the oracle/control;
its productive pair+shift set is discovered rather than assumed.

Advance requires at every size:
- 100% retention of every all-pairs productive pair and best shift;
- nominated pairs <= 20% of the all-pairs universe;
- explicit sampled feature bytes <= 2% of logical object bytes;
- end-to-end nomination + sparse-gate + exact-proof elapsed <= 1.05x all-pairs.

Across all seven sizes the median end-to-end/all-pairs elapsed ratio must be
<=0.50x. No threshold may be changed after result. A miss retires this exact
band-nomination shape, not sparse pre-proof falsification or generalized shift
Law itself.

Claim boundary: writer-side candidate nomination/discovery evidence only. The
Python index is a research instrument, not product-speed authority; stored bytes,
reader speed/access, v0.29/v0.30 comparison and release authority remain outside
this experiment.
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
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
OBJECT_COUNT = 24
DISTRACTOR_COUNT = 19
ROUNDS = 11
MAX_CANDIDATE_FRACTION = 0.20
MAX_FEATURE_READ_FRACTION = 0.02
MAX_ROW_RATIO = 1.05
MAX_MEDIAN_RATIO = 0.50
SHIFTS = (-2, -1, 1, 2)
BAND_COUNT = 4
PROBES_PER_BAND = 4


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-relation-band-nomination-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
            str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
            str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"),
            str(here / "one_g02_shift_relation_sparse_gate_kernel.c"),
            "-o", str(lib),
        ],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    safe = c.one_g02_shift_relation_safe_dispatch
    safe.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                     ctypes.c_size_t, ctypes.POINTER(Result)]
    safe.restype = ctypes.c_int
    gated = c.one_g02_shift_relation_sparse_gate
    gated.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                      ctypes.c_size_t, ctypes.POINTER(Result), ctypes.POINTER(ctypes.c_uint64)]
    gated.restype = ctypes.c_int
    return safe, gated, td


def _objects(size: int) -> list[bytes]:
    cases = _relation_cases(size)
    basis = cases["shift_plus1"][0]
    objects = [
        basis,
        cases["shift_plus1"][1],
        cases["shift_plus1_damage_quarter"][1],
        cases["fragmented_every96"][1],
        cases["fragmented_every32"][1],
    ]
    for i in range(DISTRACTOR_COUNT):
        objects.append(random.Random(31000 + size * 17 + i).randbytes(size))
    assert len(objects) == OBJECT_COUNT
    return objects


def _positions(size: int) -> tuple[int, ...]:
    pos = []
    for s in range(BAND_COUNT * PROBES_PER_BAND):
        p = ((s + 1) * size) // 17
        p = max(2, min(size - 3, p))
        pos.append(p)
    return tuple(pos)


def _nominate(objects: list[bytes]) -> tuple[set[tuple[int, int]], int]:
    size = len(objects[0])
    positions = _positions(size)
    # (band id, 4-byte source signature) -> prior object ids.
    index: dict[tuple[int, bytes], list[int]] = {}
    nominees: set[tuple[int, int]] = set()
    feature_bytes = 0

    for target_id, obj in enumerate(objects):
        # Query prior sources using shift-normalized target views. These neighboring
        # bytes can be captured during the same forward observation pass.
        for shift in SHIFTS:
            for band in range(BAND_COUNT):
                ps = positions[band * PROBES_PER_BAND:(band + 1) * PROBES_PER_BAND]
                signature = bytes(obj[p + shift] for p in ps)
                feature_bytes += PROBES_PER_BAND
                for source_id in index.get((band, signature), ()):  # dedupe below
                    nominees.add((source_id, target_id))

        # Insert the zero-shift source view after querying so self-pairs are impossible.
        for band in range(BAND_COUNT):
            ps = positions[band * PROBES_PER_BAND:(band + 1) * PROBES_PER_BAND]
            signature = bytes(obj[p] for p in ps)
            feature_bytes += PROBES_PER_BAND
            index.setdefault((band, signature), []).append(target_id)

    return nominees, feature_bytes


def _pack(objects: list[bytes]):
    size = len(objects[0])
    blob = b"".join(objects)
    arr = (ctypes.c_uint8 * len(blob)).from_buffer_copy(blob)
    return arr, size


def _ptr(arr, offset: int):
    return ctypes.cast(ctypes.byref(arr, offset), ctypes.POINTER(ctypes.c_uint8))


def _all_pairs(safe, arr, size: int, count: int) -> set[tuple[int, int, int]]:
    productive: set[tuple[int, int, int]] = set()
    for a in range(count):
        for b in range(a + 1, count):
            out = Result()
            rc = safe(_ptr(arr, a * size), _ptr(arr, b * size), size, ctypes.byref(out))
            if rc < 0:
                raise RuntimeError(f"safe dispatcher failed: {a}/{b}/{rc}")
            if int(out.exact_proofs) >= 4:
                productive.add((a, b, int(out.best_shift)))
    return productive


def _nominated_chain(gated, arr, size: int, nominees: set[tuple[int, int]]) -> tuple[set[tuple[int, int, int]], int]:
    productive: set[tuple[int, int, int]] = set()
    gate_reads = 0
    for a, b in sorted(nominees):
        out = Result()
        reads = ctypes.c_uint64()
        rc = gated(_ptr(arr, a * size), _ptr(arr, b * size), size, ctypes.byref(out), ctypes.byref(reads))
        if rc < 0:
            raise RuntimeError(f"sparse gate failed: {a}/{b}/{rc}")
        gate_reads += int(reads.value)
        if int(out.exact_proofs) >= 4:
            productive.add((a, b, int(out.best_shift)))
    return productive, gate_reads


def run():
    safe, gated, td = _build()
    rows = []
    try:
        ratios = []
        all_pass = True
        for size in SIZES:
            objects = _objects(size)
            arr, relation_size = _pack(objects)
            pair_universe = OBJECT_COUNT * (OBJECT_COUNT - 1) // 2

            # Untimed truth pass establishes the exact oracle set and candidate set.
            oracle = _all_pairs(safe, arr, relation_size, OBJECT_COUNT)
            nominees, feature_bytes = _nominate(objects)
            found, gate_reads = _nominated_chain(gated, arr, relation_size, nominees)
            retained = oracle.issubset(found)
            exact_productive = found == oracle
            candidate_fraction = len(nominees) / pair_universe
            feature_fraction = feature_bytes / (OBJECT_COUNT * relation_size)

            baseline_samples = []
            candidate_samples = []
            for _ in range(ROUNDS):
                t0 = time.perf_counter_ns()
                _all_pairs(safe, arr, relation_size, OBJECT_COUNT)
                baseline_samples.append(time.perf_counter_ns() - t0)
                t0 = time.perf_counter_ns()
                current_nominees, _ = _nominate(objects)
                _nominated_chain(gated, arr, relation_size, current_nominees)
                candidate_samples.append(time.perf_counter_ns() - t0)
            baseline_ns = float(statistics.median(baseline_samples))
            candidate_ns = float(statistics.median(candidate_samples))
            ratio = candidate_ns / baseline_ns
            ratios.append(ratio)

            row_pass = (
                retained
                and exact_productive
                and candidate_fraction <= MAX_CANDIDATE_FRACTION
                and feature_fraction <= MAX_FEATURE_READ_FRACTION
                and ratio <= MAX_ROW_RATIO
            )
            all_pass &= row_pass
            rows.append({
                "relation_bytes": size,
                "object_count": OBJECT_COUNT,
                "all_pair_count": pair_universe,
                "oracle_productive_pairs": len(oracle),
                "nominated_pair_count": len(nominees),
                "candidate_fraction_of_all_pairs": candidate_fraction,
                "feature_bytes": feature_bytes,
                "feature_read_fraction_of_logical_bytes": feature_fraction,
                "sparse_gate_compared_bytes_on_nominees": gate_reads,
                "productive_pairs_retained": retained,
                "productive_set_exact": exact_productive,
                "all_pairs_median_ns": baseline_ns,
                "nomination_gate_proof_median_ns": candidate_ns,
                "candidate_over_all_pairs": ratio,
                "row_pass": row_pass,
            })

        median_ratio = float(statistics.median(ratios))
        passed = all_pass and median_ratio <= MAX_MEDIAN_RATIO
        return {
            "schema": "cmpct-one-g02-relation-band-nomination-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_object_count": OBJECT_COUNT,
            "frozen_rounds": ROUNDS,
            "frozen_max_candidate_fraction": MAX_CANDIDATE_FRACTION,
            "frozen_max_feature_read_fraction": MAX_FEATURE_READ_FRACTION,
            "frozen_max_row_ratio": MAX_ROW_RATIO,
            "frozen_max_median_ratio": MAX_MEDIAN_RATIO,
            "median_candidate_over_all_pairs": median_ratio,
            "decision": "advance_band_nomination" if passed else "retire_band_nomination_shape",
            "claim_boundary": (
                "writer-side nomination evidence only; Python indexing is a research instrument and "
                "native fused-observer cost, stored bytes, reader speed/access, v0.29/v0.30 comparison "
                "and release authority remain outside this result"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_band_nomination" else 1)
