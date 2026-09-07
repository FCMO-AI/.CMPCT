"""ONE-G0.2 bulk-digest generalization probe.

This experiment asks whether morphology selection is actually necessary. If the
chunk-bulk digest observer preserves emitted opportunities and is faster across generic
families, the simpler ONE direction is one generic observer rather than a permanent
morphology-specific writer branch.
"""
from __future__ import annotations

import json
import random
import statistics
import time
import zlib

from experiments.one.morphology_gate import _observe_bulk_digest
from experiments.one.observe import observe

SIZES = (256 * 1024, 1024 * 1024)
REPETITIONS = 15
WARMUPS = 3
MAX_RELATIVE_WALL_FOR_GENERAL_WIN = 0.95
MAX_RELATIVE_CPU_FOR_GENERAL_WIN = 0.95


def numeric(size: int) -> bytes:
    rows = []
    i = 0
    total = 0
    while total < size:
        row = f"{1700000000+i:010d},{(i*7919)%100000000:08d}.{i%997:03d},{(i*37)%360:03d}\n".encode()
        rows.append(row)
        total += len(row)
        i += 1
    return b"".join(rows)[:size]


def structured(size: int) -> bytes:
    rows = []
    i = 0
    total = 0
    while total < size:
        row = f'{{"id":{i},"kind":"evt-{i%113}","value":"{(i*2654435761)&0xffffffff:08x}"}}\n'.encode()
        rows.append(row)
        total += len(row)
        i += 1
    return b"".join(rows)[:size]


def random_bytes(size: int) -> bytes:
    rng = random.Random(0x0C01)
    return rng.randbytes(size)


def compressed_like(size: int) -> bytes:
    seed = structured(max(size * 3, 1024 * 1024))
    packed = zlib.compress(seed, 9)
    if len(packed) >= size:
        return packed[:size]
    repeats = (size + len(packed) - 1) // len(packed)
    return (packed * repeats)[:size]


def repetitive(size: int) -> bytes:
    block = (b"ONE-LAW-SURPRISE-0123456789|" * 4)[:64]
    return (block * ((size + len(block) - 1) // len(block)))[:size]


def bulk(data: bytes):
    return _observe_bulk_digest(
        data,
        min_run=8,
        chunk_size=64,
        max_index_entries=1 << 16,
        classifier_bytes=0,
    )


def timed(fn, data: bytes) -> tuple[int, int]:
    w0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    fn(data)
    return time.perf_counter_ns() - w0, time.process_time_ns() - c0


def row(family: str, data: bytes) -> dict[str, object]:
    ref = observe(data)
    cand = bulk(data)
    assert cand.runs == ref.runs
    assert cand.reuse == ref.reuse
    assert cand.stats.reuse_opportunity_bytes == ref.stats.reuse_opportunity_bytes

    for _ in range(WARMUPS):
        observe(data)
        bulk(data)

    rw: list[int] = []
    rc: list[int] = []
    bw: list[int] = []
    bc: list[int] = []
    for rep in range(REPETITIONS):
        if rep % 2 == 0:
            w, c = timed(observe, data); rw.append(w); rc.append(c)
            w, c = timed(bulk, data); bw.append(w); bc.append(c)
        else:
            w, c = timed(bulk, data); bw.append(w); bc.append(c)
            w, c = timed(observe, data); rw.append(w); rc.append(c)

    ref_wall = statistics.median(rw)
    ref_cpu = statistics.median(rc)
    bulk_wall = statistics.median(bw)
    bulk_cpu = statistics.median(bc)
    return {
        "family": family,
        "size": len(data),
        "wall_ratio": bulk_wall / ref_wall,
        "cpu_ratio": bulk_cpu / ref_cpu,
        "reference_wall_ns": int(ref_wall),
        "bulk_wall_ns": int(bulk_wall),
        "reference_cpu_ns": int(ref_cpu),
        "bulk_cpu_ns": int(bulk_cpu),
        "reuse_bytes": ref.stats.reuse_opportunity_bytes,
        "run_bytes": ref.stats.run_opportunity_bytes,
        "reference_source_read_bytes": ref.stats.total_source_read_bytes,
        "bulk_source_read_bytes": cand.stats.total_source_read_bytes,
        "opportunity_parity": True,
    }


def main() -> None:
    families = (
        ("numeric", numeric),
        ("structured", structured),
        ("random", random_bytes),
        ("compressed_like", compressed_like),
        ("repetitive", repetitive),
    )
    rows = [row(name, maker(size)) for size in SIZES for name, maker in families]
    general_wins = [
        r for r in rows
        if r["wall_ratio"] <= MAX_RELATIVE_WALL_FOR_GENERAL_WIN
        and r["cpu_ratio"] <= MAX_RELATIVE_CPU_FOR_GENERAL_WIN
    ]
    print(json.dumps({
        "experiment": "ONE-G0.2 bulk digest generalization",
        "purpose": "decide whether morphology selection is simpler than generic bulk digest",
        "repetitions": REPETITIONS,
        "general_win_threshold": {
            "wall": MAX_RELATIVE_WALL_FOR_GENERAL_WIN,
            "cpu": MAX_RELATIVE_CPU_FOR_GENERAL_WIN,
        },
        "rows": rows,
        "rows_meeting_general_win_threshold": len(general_wins),
        "total_rows": len(rows),
        "decision_rule": (
            "Do not replace generic observe solely from this probe. If all hostile rows "
            "preserve opportunities and most/all materially beat FNV64, run the broader "
            "corpus and RSS test; otherwise keep or reform morphology selection."
        ),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
