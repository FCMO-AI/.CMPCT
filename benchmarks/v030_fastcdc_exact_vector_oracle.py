from __future__ import annotations

"""Research-only exact-semantic vectorized FastCDC headroom oracle.

This does not change product code. It asks whether the current deterministic Gear
recurrence can be evaluated faster without changing a single chunk boundary.
"""

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np

from benchmarks import v030_release_performance as PERF
from cmpct.resemblance import GEAR, Chunk, fastcdc

GEAR_NP = np.asarray(GEAR, dtype=np.uint64)


def _scan_exact(vals: np.ndarray, mask: int, h0: int = 0) -> tuple[int | None, int, int]:
    """Return (1-based cut length, final hash, conservative transient bytes).

    h_i = 2*h_(i-1)+gear_i modulo 2**64. After 64 shifts, any
    pre-window contribution is multiplied by 2**64 and vanishes exactly, so
    every later hash is the uint64 sum of the latest <=64 weighted Gear terms.
    """
    m = int(vals.size)
    if m == 0:
        return None, h0, 0
    hashes = vals.astype(np.uint64, copy=True)
    # Charge vals + hashes + one full-size shifted temporary created by NumPy.
    # This deliberately overstates the steady-state live set rather than gifting
    # the vector oracle temporary memory.
    peak_scratch = int(3 * vals.nbytes)
    if h0:
        upto = min(m, 63)
        powers = np.left_shift(np.uint64(1), np.arange(1, upto + 1, dtype=np.uint64))
        hashes[:upto] += np.uint64(h0) * powers
        peak_scratch = max(peak_scratch, int(3 * vals.nbytes + powers.nbytes))
    for shift in range(1, min(64, m)):
        # NumPy performs uint64 wraparound, exactly matching the scalar '& MASK64'.
        hashes[shift:] += vals[:-shift] << np.uint64(shift)
    hits = np.flatnonzero((hashes & np.uint64(mask)) == 0)
    if hits.size:
        j = int(hits[0])
        return j + 1, int(hashes[j]), peak_scratch
    return None, int(hashes[-1]), peak_scratch


def vector_fastcdc(data: bytes, *, min_size: int = 16 * 1024, avg_size: int = 64 * 1024,
                   max_size: int = 256 * 1024) -> tuple[list[Chunk], int]:
    n = len(data)
    if n == 0:
        return [], 0
    if not (0 < min_size <= avg_size <= max_size):
        raise ValueError("require 0 < min_size <= avg_size <= max_size")
    bits = max(1, round(avg_size.bit_length() - 1))
    small_mask = (1 << min(63, bits + 1)) - 1
    large_mask = (1 << max(1, bits - 1)) - 1
    normal = min(max_size, max(min_size + 1, avg_size))
    source = np.frombuffer(data, dtype=np.uint8)
    out: list[Chunk] = []
    peak_scratch = 0
    start = 0
    while start < n:
        hard_end = min(n, start + max_size)
        if hard_end - start <= min_size:
            out.append(Chunk(start, hard_end - start))
            break
        i = start + min_size
        early_end = min(hard_end, start + normal)
        vals = GEAR_NP[source[i:early_end]]
        got, h, scratch = _scan_exact(vals, small_mask, 0)
        peak_scratch = max(peak_scratch, scratch)
        cut = i + got if got is not None else None
        if cut is None:
            i = early_end
            vals = GEAR_NP[source[i:hard_end]]
            got, h, scratch = _scan_exact(vals, large_mask, h)
            peak_scratch = max(peak_scratch, scratch)
            if got is not None:
                cut = i + got
        if cut is None:
            cut = hard_end
        out.append(Chunk(start, cut - start))
        start = cut
    return out, peak_scratch


def _time(fn, data: bytes, repeats: int) -> tuple[float, object]:
    values = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = fn(data)
        values.append(time.perf_counter() - started)
    values.sort()
    return values[len(values) // 2], result


def run(work_root: Path, repeats: int) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpora = PERF._build_corpora(work_root / "corpus")
    source = corpora[("neutral_hostile_v1", "09_ml_artifacts")]
    files = sorted(p for p in source.rglob("*") if p.is_file() and p.stat().st_size > 512 * 1024)
    rows = []
    total_base = total_vector = 0.0
    peak_scratch = 0
    for path in files:
        data = path.read_bytes()
        kwargs = dict(min_size=32 * 1024, avg_size=128 * 1024, max_size=512 * 1024)
        base_s, base = _time(lambda b: fastcdc(b, **kwargs), data, repeats)
        vector_s, pair = _time(lambda b: vector_fastcdc(b, **kwargs), data, repeats)
        vector, scratch = pair
        if base != vector:
            raise RuntimeError(f"boundary mismatch: {path.relative_to(source)}")
        total_base += base_s
        total_vector += vector_s
        peak_scratch = max(peak_scratch, scratch)
        rows.append({
            "path": path.relative_to(source).as_posix(),
            "bytes": len(data),
            "chunks": len(base),
            "baseline_s": base_s,
            "vector_s": vector_s,
            "speedup": base_s / max(vector_s, 1e-12),
            "boundary_identity": True,
        })
    return {
        "schema": "cmpct-v030-fastcdc-exact-vector-oracle-v1",
        "release_credit": False,
        "workload": "neutral_hostile_v1/09_ml_artifacts",
        "large_file_count": len(files),
        "large_file_bytes": sum(r["bytes"] for r in rows),
        "baseline_total_s": total_base,
        "vector_total_s": total_vector,
        "aggregate_speedup": total_base / max(total_vector, 1e-12),
        "max_transient_scratch_bytes_conservative": peak_scratch,
        "all_boundaries_identical": all(r["boundary_identity"] for r in rows),
        "rows": rows,
        "claim_boundary": "Research micro/oracle only. Exact boundary identity is required, but whole-child and whole-product wall/RSS must be measured before product credit.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=2)
    args = ap.parse_args()
    result = run(args.work_root, max(1, args.repeats))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
