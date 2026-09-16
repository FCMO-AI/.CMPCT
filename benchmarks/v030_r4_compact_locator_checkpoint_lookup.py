from __future__ import annotations

"""Bounded checkpoint lookup falsifier for the compact LOC1 streaming reader.

Mission Lock / Referee
======================
The v7 locator representation, direct canonical-uvarint rule, 1 MiB raw ceiling, authenticated
primary/tail/footer, 644 B group geometry and fixed 8x selective-read law are frozen. The preceding
fresh-process attribution showed that streaming validation removes retained-table RSS, but a family
lookup still rescans variable-length LOC1 records from the beginning.

This referee changes no archive bytes. It compares that exact streaming lookup against a transient,
packed checkpoint view built while validating the same raw locator. Every 256 records it retains only
five unsigned-64 scalars needed to resume canonical decoding (first key at checkpoint, byte offset,
prior key, prior group offset, record index). Checkpoints are reader state, never persisted metadata.
The stride is frozen before measurement and is derived as a coarse bounded-reader engineering choice,
not a corpus sweep.

Hypothesis
----------
On a deterministic valid near-ceiling monotone locator, packed checkpoints should remove repeated
O(raw-locator) warm lookup work while keeping reader state small and exact: 12 spread lookups must
match the existing streaming reader, candidate warm-query wall time must improve by >=10x, candidate
build+late-query wall must not exceed the baseline build+late-query wall, and packed checkpoint bytes
must stay <=128 KiB under the frozen 1 MiB raw ceiling.

Disproof
--------
False on any lookup mismatch, >128 KiB packed checkpoints, <10x warm-query speedup, or slower
build+late-query. A PASS is reader-algorithm evidence only: Python timing is not product authority,
archive bytes do not move, cold locator pread/auth/decompression remain charged, and Office/native /
held-out product integration still require their own gates.
"""

import argparse
from array import array
import bisect
import json
import os
from pathlib import Path
import time

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4
from benchmarks import v030_r4_compact_locator_parser_resource_v2 as FAST

SCHEMA = "cmpct-v030-r4-compact-locator-checkpoint-lookup-v1"
TARGET_RAW = 900_000
STRIDE = 256
MAX_CHECKPOINT_BYTES = 128 * 1024
QUERY_COUNT = 12


class FamilyIndex:
    __slots__ = ("first_keys", "byte_offsets", "prior_keys", "prior_roffs", "record_indices", "count")

    def __init__(self, count: int):
        self.first_keys = array("Q")
        self.byte_offsets = array("Q")
        self.prior_keys = array("Q")
        self.prior_roffs = array("Q")
        self.record_indices = array("Q")
        self.count = int(count)

    @property
    def packed_bytes(self) -> int:
        return sum(x.buffer_info()[1] * x.itemsize for x in (
            self.first_keys, self.byte_offsets, self.prior_keys, self.prior_roffs, self.record_indices
        ))


class CheckpointLocator:
    __slots__ = ("raw", "families", "record_count")

    def __init__(self, raw: bytes):
        if not raw.startswith(b"LOC1"):
            raise ValueError("bad locator magic")
        if len(raw) > V4.MAX_LOCATOR_RAW:
            raise RuntimeError("locator expansion bound exceeded")
        self.raw = raw
        self.families: dict[tuple[int, str], FamilyIndex] = {}
        self.record_count = 0
        off = 4
        stream_count, off = FAST._read_canonical_uvarint_fast(raw, off)
        prev_si = -1
        for _ in range(stream_count):
            si, off = FAST._read_canonical_uvarint_fast(raw, off)
            if si <= prev_si:
                raise ValueError("locator stream order/duplication")
            prev_si = si
            for fam in V1.FAMS:
                fid, off = FAST._read_canonical_uvarint_fast(raw, off)
                if fid != V1.FAM_ID[fam]:
                    raise ValueError("locator family order drift")
                count, off = FAST._read_canonical_uvarint_fast(raw, off)
                idx = FamilyIndex(count)
                key = 0
                roff = 0
                for j in range(count):
                    rec_off = off
                    prev_key = key
                    prev_roff = roff
                    dk, off = FAST._read_canonical_uvarint_fast(raw, off)
                    do, off = FAST._read_canonical_uvarint_fast(raw, off)
                    key += dk
                    roff += do
                    if j % STRIDE == 0:
                        idx.first_keys.append(key)
                        idx.byte_offsets.append(rec_off)
                        idx.prior_keys.append(prev_key)
                        idx.prior_roffs.append(prev_roff)
                        idx.record_indices.append(j)
                    self.record_count += 1
                self.families[(int(si), fam)] = idx
        if off != len(raw):
            raise ValueError("trailing locator bytes")

    @property
    def packed_checkpoint_bytes(self) -> int:
        return sum(v.packed_bytes for v in self.families.values())

    def locate(self, sf: tuple[int, str], target: int) -> int:
        idx = self.families[sf]
        if not idx.first_keys:
            raise KeyError(target)
        c = bisect.bisect_right(idx.first_keys, target) - 1
        if c < 0:
            raise KeyError(target)
        off = int(idx.byte_offsets[c])
        key = int(idx.prior_keys[c])
        roff = int(idx.prior_roffs[c])
        start_j = int(idx.record_indices[c])
        candidate = None
        # The next checkpoint first-key is > target by construction of bisect_right, so at most STRIDE
        # records (plus one terminating record) need decoding even when keys repeat.
        end_j = min(idx.count, start_j + STRIDE + 1)
        for _j in range(start_j, end_j):
            dk, off = FAST._read_canonical_uvarint_fast(self.raw, off)
            do, off = FAST._read_canonical_uvarint_fast(self.raw, off)
            key += dk
            roff += do
            if key > target:
                break
            candidate = roff
        if candidate is None:
            raise KeyError(target)
        return candidate


def _increasing_locator(target_bytes: int = TARGET_RAW) -> tuple[bytes, int]:
    # One stream, dense anchor family. dk=1/do=1 keep every record two bytes while making lookup targets
    # span the full monotone key domain instead of the duplicate-zero hostile shape used by the RSS gate.
    fixed = bytearray(b"LOC1")
    fixed += DEP.uvarint(1) + DEP.uvarint(0)
    count = max(1, (target_bytes - 32) // 2)
    while True:
        raw = bytearray(fixed)
        raw += DEP.uvarint(V1.FAM_ID["anchor"]) + DEP.uvarint(count)
        raw += b"\x01\x01" * count
        raw += DEP.uvarint(V1.FAM_ID["block"]) + DEP.uvarint(0)
        raw += DEP.uvarint(V1.FAM_ID["seed"]) + DEP.uvarint(0)
        if len(raw) <= target_bytes:
            return bytes(raw), count
        count -= 1


def _queries(count: int) -> list[int]:
    if QUERY_COUNT == 1:
        return [count]
    return [1 + ((count - 1) * i) // (QUERY_COUNT - 1) for i in range(QUERY_COUNT)]


def _time(fn):
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    out = fn()
    return out, time.process_time() - cpu0, time.perf_counter() - wall0


def run() -> dict:
    raw, count = _increasing_locator()
    qs = _queries(count)

    original = V4._read_canonical_uvarint
    V4._read_canonical_uvarint = FAST._read_canonical_uvarint_fast
    try:
        baseline, baseline_build_cpu, baseline_build_wall = _time(lambda: V4._parse_locator_streaming(raw))
        candidate, candidate_build_cpu, candidate_build_wall = _time(lambda: CheckpointLocator(raw))

        def baseline_queries():
            return [V1._locate(baseline[(0, "anchor")], q) for q in qs]

        def candidate_queries():
            return [candidate.locate((0, "anchor"), q) for q in qs]

        bvals, bq_cpu, bq_wall = _time(baseline_queries)
        cvals, cq_cpu, cq_wall = _time(candidate_queries)

        # Measure a cold-ish late-query operation as parse/build + one final-key lookup. Both paths see
        # the exact same in-memory authenticated raw bytes; locator pread/decompression are outside this
        # parser-algorithm A/B and remain product debt.
        _, b_late_cpu, b_late_wall = _time(lambda: V1._locate(V4._parse_locator_streaming(raw)[(0, "anchor")], count))
        _, c_late_cpu, c_late_wall = _time(lambda: CheckpointLocator(raw).locate((0, "anchor"), count))
    finally:
        V4._read_canonical_uvarint = original

    exact = bvals == cvals == qs
    checkpoint_bytes = candidate.packed_checkpoint_bytes
    warm_speedup = bq_wall / max(cq_wall, 1e-12)
    cold_ratio = c_late_wall / max(b_late_wall, 1e-12)
    supported = exact and checkpoint_bytes <= MAX_CHECKPOINT_BYTES and warm_speedup >= 10.0 and cold_ratio <= 1.0

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "input": {
            "raw_locator_bytes": len(raw),
            "records": count,
            "queries": qs,
            "checkpoint_stride_records": STRIDE,
        },
        "baseline_streaming_rescan": {
            "build_cpu_s": baseline_build_cpu,
            "build_wall_s": baseline_build_wall,
            "warm_queries_cpu_s": bq_cpu,
            "warm_queries_wall_s": bq_wall,
            "build_plus_late_query_cpu_s": b_late_cpu,
            "build_plus_late_query_wall_s": b_late_wall,
        },
        "checkpoint_candidate": {
            "build_cpu_s": candidate_build_cpu,
            "build_wall_s": candidate_build_wall,
            "warm_queries_cpu_s": cq_cpu,
            "warm_queries_wall_s": cq_wall,
            "build_plus_late_query_cpu_s": c_late_cpu,
            "build_plus_late_query_wall_s": c_late_wall,
            "packed_checkpoint_bytes": checkpoint_bytes,
            "checkpoint_limit_bytes": MAX_CHECKPOINT_BYTES,
            "warm_query_speedup_x": warm_speedup,
            "build_plus_late_query_ratio": cold_ratio,
        },
        "correctness": {
            "all_lookup_results_exact": exact,
            "baseline_values": bvals,
            "candidate_values": cvals,
        },
        "hypothesis": {
            "packed_checkpoints_remove_rescan_debt_with_bounded_state": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "representation_bytes_unchanged": True,
            "locator_auth_and_8x_laws_unchanged": True,
            "checkpoint_state_is_transient_reader_memory": True,
            "fixed_checkpoint_stride_no_sweep": True,
            "direct_canonical_uvarint_rule": True,
            "product_debt": "cold pread/auth/decompression; Office exact reader integration; held-out transfer; native implementation/parity; end-to-end RSS/throughput",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-compact-locator-checkpoint-lookup.json"))
    a = p.parse_args()
    d = run()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps(d, sort_keys=True))


if __name__ == "__main__":
    main()
