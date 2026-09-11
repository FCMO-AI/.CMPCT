"""ONE-G0.2 fixed-partition authenticated-tree fanout Pareto.

Referee freeze before result-bearing execution
==============================================
The arbitrary-alignment transfer rejected the original binary fixed-leaf grid. A remaining
causal alternative inside the same representation family is tree fanout: larger fanout stores
fewer internal levels but exposes more sibling commitments in a range proof.

This instrument exhausts a frozen practical grid instead of tuning one tree after the loss:
- roots: 64 KiB and 256 KiB;
- request: 4 KiB;
- leaf bytes: 256..4096 inclusive, step 64;
- fanout: 2,4,8,16,32,64,128,256;
- alignment: every 64 B modulo leaf plus leaf-1;
- hash bytes: 32;
- persistent sidecar: 4-byte leaf/fanout descriptor plus EVERY non-root node hash,
  including leaf hashes, so no sibling data/hash is gifted;
- proof traffic: every sibling node hash needed to authenticate the selected leaves;
- payload traffic: complete intersecting leaves.

The geometry model is content-independent. Binary anchors are cross-checked against the exact
existing auth_tree geometry. Frozen target remains <=3.5% persistent index and <=1.20x median
authenticated bytes touched at BOTH root sizes. Any verification/model-parity failure blocks.
If no point passes, tree-fanout tuning is retired and the next work must change the integrity
representation boundary rather than keep searching fixed partitions.
"""
from __future__ import annotations

import json
import math
import os
from statistics import median

ROOT_SIZES = (65_536, 262_144)
REQUEST_BYTES = 4096
LEAF_GRID = tuple(range(256, 4097, 64))
FANOUT_GRID = (2, 4, 8, 16, 32, 64, 128, 256)
ALIGNMENT_STEP = 64
HASH_BYTES = 32
MAX_INDEX_FRACTION = 0.035
MAX_MEDIAN_TOUCH_AMP = 1.20


def _widths(leaf_count: int, fanout: int) -> tuple[int, ...]:
    out = [leaf_count]
    while out[-1] > 1:
        out.append(math.ceil(out[-1] / fanout))
    return tuple(out)


def _proof_hashes(leaf_count: int, fanout: int, selected: set[int]) -> int:
    width = leaf_count
    current = set(selected)
    hashes = 0
    while width > 1:
        parents = {i // fanout for i in current}
        for parent in parents:
            lo = parent * fanout
            hi = min(width, lo + fanout)
            present = {i for i in current if i // fanout == parent}
            hashes += (hi - lo) - len(present)
        current = parents
        width = math.ceil(width / fanout)
    return hashes


def _start_for_mod(root_bytes: int, leaf_bytes: int, mod: int) -> int:
    center = (root_bytes - REQUEST_BYTES) // 2
    block = center - center % leaf_bytes
    start = block + mod
    if start + REQUEST_BYTES > root_bytes:
        start -= leaf_bytes
    if start < 0 or start + REQUEST_BYTES > root_bytes or start % leaf_bytes != mod:
        raise AssertionError("unable to realize alignment")
    return start


def _metrics(root_bytes: int, leaf_bytes: int, fanout: int) -> dict[str, float | int]:
    leaf_count = math.ceil(root_bytes / leaf_bytes)
    widths = _widths(leaf_count, fanout)
    # Root replaces the existing whole-root digest; every other node hash is persisted.
    stored_index_bytes = 4 + HASH_BYTES * (sum(widths) - 1)
    mods = list(range(0, leaf_bytes, ALIGNMENT_STEP))
    if leaf_bytes - 1 not in mods:
        mods.append(leaf_bytes - 1)
    amps: list[float] = []
    proof_hash_counts: list[int] = []
    for mod in mods:
        start = _start_for_mod(root_bytes, leaf_bytes, mod)
        first = start // leaf_bytes
        last = (start + REQUEST_BYTES - 1) // leaf_bytes
        selected = set(range(first, last + 1))
        payload = sum(min(leaf_bytes, root_bytes - i * leaf_bytes) for i in selected)
        proof_hashes = _proof_hashes(leaf_count, fanout, selected)
        touched = payload + HASH_BYTES * proof_hashes
        amps.append(touched / REQUEST_BYTES)
        proof_hash_counts.append(proof_hashes)
    amps.sort()
    proof_hash_counts.sort()
    return {
        "alignments": len(amps),
        "stored_index_bytes": stored_index_bytes,
        "stored_index_fraction": stored_index_bytes / root_bytes,
        "median_touch_amplification": median(amps),
        "max_touch_amplification": max(amps),
        "median_proof_hashes": median(proof_hash_counts),
    }


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for fanout in FANOUT_GRID:
        for leaf_bytes in LEAF_GRID:
            per_size: dict[str, object] = {}
            passes = True
            for root_bytes in ROOT_SIZES:
                m = _metrics(root_bytes, leaf_bytes, fanout)
                per_size[str(root_bytes)] = m
                if float(m["stored_index_fraction"]) > MAX_INDEX_FRACTION or float(m["median_touch_amplification"]) > MAX_MEDIAN_TOUCH_AMP:
                    passes = False
            row = {"fanout": fanout, "leaf_bytes": leaf_bytes, "per_size": per_size, "passes": passes}
            rows.append(row)
            if passes:
                candidates.append(row)

    # Exact parity anchors against the existing binary geometry at the previously measured 2 KiB point.
    anchors = {str(root): _metrics(root, 2048, 2) for root in ROOT_SIZES}
    expected = {
        "65536": {"stored_index_fraction": 0.03033447265625, "median_touch_amplification": 1.5546875},
        "262144": {"stored_index_fraction": 0.0310211181640625, "median_touch_amplification": 1.5859375},
    }
    parity_failures = []
    for root, want in expected.items():
        got = anchors[root]
        for key, value in want.items():
            if abs(float(got[key]) - value) > 1e-12:
                parity_failures.append({"root": root, "field": key, "expected": value, "got": got[key]})

    ranked = sorted(
        rows,
        key=lambda r: max(
            max(
                float(m["stored_index_fraction"]) / MAX_INDEX_FRACTION,
                float(m["median_touch_amplification"]) / MAX_MEDIAN_TOUCH_AMP,
            )
            for m in r["per_size"].values()
        ),
    )
    return {
        "schema": "cmpct-one-g02-auth-tree-fanout-pareto-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "root_sizes": list(ROOT_SIZES),
        "request_bytes": REQUEST_BYTES,
        "leaf_grid": {"min": LEAF_GRID[0], "max": LEAF_GRID[-1], "step": 64},
        "fanout_grid": list(FANOUT_GRID),
        "hash_bytes": HASH_BYTES,
        "target_max_index_fraction": MAX_INDEX_FRACTION,
        "target_max_median_touch_amplification": MAX_MEDIAN_TOUCH_AMP,
        "binary_parity_failures": parity_failures,
        "target_candidates": candidates,
        "best_five": ranked[:5],
        "decision": "fixed_partition_tree_family_has_feasible_point" if candidates and not parity_failures else "retire_fixed_partition_tree_fanout_tuning",
        "claim_boundary": "geometry/economics falsifier for authenticated fixed partitions only; no canonical wire or product authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
