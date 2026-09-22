from __future__ import annotations

"""Hostile transfer for transient compact-LOC1 checkpoints.

Mission Lock / Hostile Reviewer
===============================
The checkpoint candidate from `v030_r4_compact_locator_checkpoint_lookup.py` is frozen: stride 256,
five packed u64 scalars per checkpoint, direct canonical-uvarint decode, no archive-byte changes.
The first referee used strictly increasing one-byte deltas. This transfer attacks two assumptions that
could make that result a false win: long runs of duplicate keys (dk=0) and variable-length canonical
uvarints for both key and locator-offset deltas.

Hypothesis
----------
Without changing the candidate or stride, every sampled lookup on both hostile valid locators must
match the existing streaming LOC1 reader exactly. The duplicate-key corpus must include targets at the
start/middle/end of duplicate runs and across checkpoint boundaries. The variable-width corpus must
exercise 1/2/3/4-byte uvarints and targets spanning the full family.

Disproof
--------
One mismatch, unexpected acceptance of a missing target, parser cardinality drift, or checkpoint-state
ceiling breach falsifies transfer. Timing is recorded diagnostically but is not an acceptance gate here:
this test exists to attack correctness/generalization, not retune speed.
"""

import argparse
import json
import os
from pathlib import Path
import random
import time

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4
from benchmarks import v030_r4_compact_locator_parser_resource_v2 as FAST
from benchmarks import v030_r4_compact_locator_checkpoint_lookup as CP

SCHEMA = "cmpct-v030-r4-compact-locator-checkpoint-hostile-transfer-v1"
SEED = 0xC030C0DE
MAX_STATE = CP.MAX_CHECKPOINT_BYTES


def _encode_family(records: list[tuple[int, int]]) -> bytes:
    raw = bytearray(b"LOC1")
    raw += DEP.uvarint(1) + DEP.uvarint(0)
    raw += DEP.uvarint(V1.FAM_ID["anchor"]) + DEP.uvarint(len(records))
    pk = 0
    po = 0
    for key, roff in records:
        if key < pk or roff < po:
            raise ValueError("records must be monotone")
        raw += DEP.uvarint(key - pk) + DEP.uvarint(roff - po)
        pk, po = key, roff
    raw += DEP.uvarint(V1.FAM_ID["block"]) + DEP.uvarint(0)
    raw += DEP.uvarint(V1.FAM_ID["seed"]) + DEP.uvarint(0)
    return bytes(raw)


def _duplicate_records() -> list[tuple[int, int]]:
    rows: list[tuple[int, int]] = []
    key = 0
    roff = 0
    # Deliberately place duplicate runs across stride boundaries: run lengths are not divisors of 256.
    for run in range(1800):
        key += 1 + (run % 7 == 0)
        length = 173 if run % 5 == 0 else 41
        for j in range(length):
            roff += 1 + ((run + j) % 3 == 0)
            rows.append((key, roff))
    return rows


def _variable_records() -> list[tuple[int, int]]:
    rng = random.Random(SEED)
    rows: list[tuple[int, int]] = []
    key = 0
    roff = 0
    widths = [1, 127, 128, 16_383, 16_384, 2_097_151, 2_097_152, 268_435_455]
    for i in range(12_000):
        # Keep total values inside u64 while forcing canonical encodings through 1/2/3/4-byte regions.
        dk = widths[i % len(widths)]
        do = widths[(i * 5 + 3) % len(widths)]
        # Occasionally create duplicate keys; correctness must be the last locator offset at target.
        if i % 29 == 0:
            dk = 0
        # Add small deterministic jitter without changing width class for most samples.
        if dk and dk < 1_000_000:
            dk += rng.randrange(0, min(7, max(1, dk)))
        if do < 1_000_000:
            do += rng.randrange(0, min(7, max(1, do)))
        key += dk
        roff += do
        rows.append((key, roff))
    return rows


def _targets(rows: list[tuple[int, int]], duplicate_focus: bool) -> list[int]:
    keys = [k for k, _ in rows]
    out = {keys[0], keys[-1], keys[len(keys)//2]}
    # Around checkpoint boundaries.
    for i in range(CP.STRIDE, len(keys), CP.STRIDE):
        for j in (i-2, i-1, i, min(len(keys)-1, i+1), min(len(keys)-1, i+2)):
            out.add(keys[j])
    if duplicate_focus:
        # Explicitly sample beginnings/middles/ends of duplicate runs.
        start = 0
        while start < len(keys):
            end = start + 1
            while end < len(keys) and keys[end] == keys[start]:
                end += 1
            out.add(keys[start])
            if start > 0:
                out.add(keys[start-1])
            if end < len(keys):
                out.add(keys[end])
            start = end
    # Bound runtime while remaining deterministic and covering whole key space.
    ordered = sorted(out)
    if len(ordered) <= 320:
        return ordered
    step = (len(ordered)-1) / 319.0
    return [ordered[round(i*step)] for i in range(320)]


def _exercise(name: str, rows: list[tuple[int, int]], duplicate_focus: bool) -> dict:
    raw = _encode_family(rows)
    original = V4._read_canonical_uvarint
    V4._read_canonical_uvarint = FAST._read_canonical_uvarint_fast
    try:
        baseline = V4._parse_locator_streaming(raw)
        candidate = CP.CheckpointLocator(raw)
        targets = _targets(rows, duplicate_focus)
        mismatches = []
        cpu0 = time.process_time(); wall0 = time.perf_counter()
        for t in targets:
            try:
                b = V1._locate(baseline[(0, "anchor")], t)
                be = None
            except Exception as e:  # exact exception class is diagnostic; candidate must agree on presence.
                b = None; be = type(e).__name__
            try:
                c = candidate.locate((0, "anchor"), t)
                ce = None
            except Exception as e:
                c = None; ce = type(e).__name__
            if (b, be) != (c, ce):
                mismatches.append({"target": t, "baseline": b, "baseline_error": be, "candidate": c, "candidate_error": ce})
                if len(mismatches) >= 20:
                    break
        cpu = time.process_time()-cpu0; wall = time.perf_counter()-wall0
    finally:
        V4._read_canonical_uvarint = original
    return {
        "name": name,
        "raw_locator_bytes": len(raw),
        "records": len(rows),
        "targets": len(targets),
        "checkpoint_bytes": candidate.packed_checkpoint_bytes,
        "checkpoint_ceiling_bytes": MAX_STATE,
        "record_count_exact": candidate.record_count == len(rows),
        "mismatches": mismatches,
        "all_exact": not mismatches,
        "query_cpu_s": cpu,
        "query_wall_s": wall,
    }


def run() -> dict:
    cases = [
        _exercise("duplicate_runs", _duplicate_records(), True),
        _exercise("variable_uvarints", _variable_records(), False),
    ]
    supported = all(c["all_exact"] and c["record_count_exact"] and c["checkpoint_bytes"] <= MAX_STATE for c in cases)
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "cases": cases,
        "hypothesis": {"checkpoint_correctness_transfers_to_hostile_valid_locators": supported},
        "contract": {
            "candidate_unchanged": True,
            "checkpoint_stride_records": CP.STRIDE,
            "representation_bytes_unchanged": True,
            "auth_and_locality_laws_unchanged": True,
            "no_speed_threshold_tuning": True,
            "diagnostic_only": True,
            "release_credit": False,
        },
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-compact-locator-checkpoint-hostile-transfer.json"))
    a=p.parse_args()
    d=run()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True)+"\n")
    print(json.dumps(d, sort_keys=True))


if __name__ == "__main__":
    main()
