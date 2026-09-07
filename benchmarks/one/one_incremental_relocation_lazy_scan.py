#!/usr/bin/env python3
"""ONE-G0.2 lazy relocation scan vs persistent-directory A/B.

Mission lock
------------
The persistent relocation directory was rejected at exact head 017a1ef because it
adds ordinary-path carrying cost: the 256 KiB exact-repeat control measured about
1.05155x wall and 1.05153x CPU against the positional cache, just outside the
frozen 1.05x ceiling.  Yet aligned relocation itself was extremely strong.

Hypothesis: the O(previous-blocks) scan paid only after two consecutive positional
misses is cheap enough relative to avoided feature recomputation that a lazy
relocation index preserves most of the movement win.  If true, ONE-07 should prefer
no always-carried relocation directory and pay the scan only when movement evidence
actually appears.

Disproof: on aligned insertion/reorder, lazy relocation exceeds 1.20x the
persistent-directory wall or CPU cost, fails exact fingerprint equivalence, or
scans more prior blocks than the compatible prior cache contains.  Controls must
show that neither arm activates relocation on exact repeat or one sparse mutation.

This is writer-discovery evidence only.  It changes no ONE bytes or reader semantics.
"""
from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import asdict

from experiments.one.cache_relocation import observe_fingerprints_relocated

SIZES = (256 << 10, 1 << 20)
REPETITIONS = 21
BLOCK_SIZE = 4096
CHUNK_SIZE = 64


def _data(size: int) -> bytes:
    out = bytearray(size)
    for i in range(size):
        block = i // BLOCK_SIZE
        within = i % BLOCK_SIZE
        out[i] = (block * 73 + within * 131 + (within >> 4) * 17 + 29) & 0xFF
    return bytes(out)


def _cases(base: bytes):
    insertion = bytes(((i * 19 + 7) & 0xFF) for i in range(BLOCK_SIZE))
    half = (len(base) // 2 // BLOCK_SIZE) * BLOCK_SIZE
    blocks = [base[i:i + BLOCK_SIZE] for i in range(0, len(base), BLOCK_SIZE)]
    quarter = max(1, len(blocks) // 4)
    sparse = bytearray(base)
    sparse[half + 17] ^= 0x5A
    return (
        ("exact_repeat", base),
        ("sparse_mutation", bytes(sparse)),
        ("block_insert", base[:half] + insertion + base[half:]),
        ("block_reorder", b"".join(blocks[quarter:] + blocks[:quarter])),
    )


def _timed(fn):
    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    fn()
    return time.perf_counter_ns() - w0, time.process_time_ns() - c0


def _paired_medians(persistent_fn, lazy_fn):
    pw, pc, lw, lc = [], [], [], []
    for rep in range(REPETITIONS):
        order = ((persistent_fn, pw, pc), (lazy_fn, lw, lc))
        if rep % 2:
            order = tuple(reversed(order))
        for fn, walls, cpus in order:
            wall, cpu = _timed(fn)
            walls.append(wall)
            cpus.append(cpu)
    return (
        statistics.median(pw), statistics.median(pc),
        statistics.median(lw), statistics.median(lc),
    )


def main() -> int:
    rows = []
    failed = False
    for size in SIZES:
        base = _data(size)
        seed = observe_fingerprints_relocated(
            base, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE
        )
        prior_block_count = len(seed.cache.blocks)
        for case, current in _cases(base):
            def persistent_call():
                return observe_fingerprints_relocated(
                    current,
                    previous=seed.cache,
                    previous_directory=seed.directory,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                )

            def lazy_call():
                return observe_fingerprints_relocated(
                    current,
                    previous=seed.cache,
                    previous_directory=None,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                )

            persistent = persistent_call()
            lazy = lazy_call()
            if lazy.fingerprints != persistent.fingerprints:
                raise AssertionError(f"fingerprint divergence: {size=} {case=}")

            pw, pc, lw, lc = _paired_medians(persistent_call, lazy_call)
            wall_ratio = lw / pw
            cpu_ratio = lc / pc
            row = {
                "size": size,
                "case": case,
                "persistent_wall_ns": pw,
                "lazy_wall_ns": lw,
                "persistent_cpu_ns": pc,
                "lazy_cpu_ns": lc,
                "lazy_over_persistent_wall": wall_ratio,
                "lazy_over_persistent_cpu": cpu_ratio,
                "persistent_stats": asdict(persistent.stats),
                "lazy_stats": asdict(lazy.stats),
            }
            rows.append(row)

            if lazy.stats.prior_cache_index_scan_blocks > prior_block_count:
                failed = True
            if case in {"exact_repeat", "sparse_mutation"}:
                if lazy.stats.prior_cache_index_scan_blocks != 0:
                    failed = True
                if lazy.stats.relocation_gate_activations != 0:
                    failed = True
            else:
                if lazy.stats.prior_cache_index_scan_blocks != prior_block_count:
                    failed = True
                if lazy.stats.relocated_reused_blocks != persistent.stats.relocated_reused_blocks:
                    failed = True
                if wall_ratio > 1.20 or cpu_ratio > 1.20:
                    failed = True

    result = {
        "experiment": "ONE-G0.2 lazy relocation scan vs persistent directory",
        "head": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "repetitions": REPETITIONS,
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "rows": rows,
        "decision": "ADVANCE_LAZY_RELOCATION" if not failed else "KEEP_PERSISTENT_OR_REFORM",
        "scope": "Python writer-discovery causal A/B only; no archive-byte, reader, native, or product authority",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
