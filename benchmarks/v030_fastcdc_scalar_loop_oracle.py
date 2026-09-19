from __future__ import annotations

"""Zero-dependency exact FastCDC loop-shape oracle for the ML create residual.

Research only: this deliberately does not mutate cmpct.resemblance.fastcdc.
"""

import argparse
import json
import shutil
import time
from pathlib import Path

from benchmarks import v030_release_performance as PERF
from cmpct.resemblance import GEAR, MASK64, Chunk, fastcdc


def candidate_fastcdc(data: bytes, *, min_size: int = 16 * 1024, avg_size: int = 64 * 1024,
                      max_size: int = 256 * 1024) -> list[Chunk]:
    n = len(data)
    if n == 0:
        return []
    if not (0 < min_size <= avg_size <= max_size):
        raise ValueError("require 0 < min_size <= avg_size <= max_size")
    bits = max(1, round(avg_size.bit_length() - 1))
    small_mask = (1 << min(63, bits + 1)) - 1
    large_mask = (1 << max(1, bits - 1)) - 1
    normal = min(max_size, max(min_size + 1, avg_size))
    gear = GEAR
    mask64 = MASK64
    source = data
    out: list[Chunk] = []
    append = out.append
    start = 0
    while start < n:
        hard_end = min(n, start + max_size)
        if hard_end - start <= min_size:
            append(Chunk(start, hard_end - start))
            break
        begin = start + min_size
        h = 0
        early_end = min(hard_end, start + normal)
        cut = 0
        for i in range(begin, early_end):
            h = ((h << 1) + gear[source[i]]) & mask64
            if h & small_mask == 0:
                cut = i + 1
                break
        if not cut:
            for i in range(early_end, hard_end):
                h = ((h << 1) + gear[source[i]]) & mask64
                if h & large_mask == 0:
                    cut = i + 1
                    break
        if not cut:
            cut = hard_end
        append(Chunk(start, cut - start))
        start = cut
    return out


def _median_wall(fn, data: bytes, repeats: int) -> tuple[float, list[Chunk]]:
    samples = []
    result: list[Chunk] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = fn(data)
        samples.append(time.perf_counter() - t0)
    samples.sort()
    return samples[len(samples) // 2], result


def run(work_root: Path, repeats: int) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpora = PERF._build_corpora(work_root / "corpus")
    source = corpora[("neutral_hostile_v1", "09_ml_artifacts")]
    files = sorted(p for p in source.rglob("*") if p.is_file())
    kwargs = dict(min_size=32 * 1024, avg_size=128 * 1024, max_size=512 * 1024)
    rows = []
    baseline_total = candidate_total = 0.0
    for path in files:
        data = path.read_bytes()
        baseline_s, baseline = _median_wall(lambda b: fastcdc(b, **kwargs), data, repeats)
        candidate_s, candidate = _median_wall(lambda b: candidate_fastcdc(b, **kwargs), data, repeats)
        if candidate != baseline:
            raise RuntimeError(f"chunk-boundary mismatch: {path.relative_to(source)}")
        baseline_total += baseline_s
        candidate_total += candidate_s
        rows.append({
            "path": path.relative_to(source).as_posix(),
            "bytes": len(data),
            "chunks": len(baseline),
            "baseline_s": baseline_s,
            "candidate_s": candidate_s,
            "speedup": baseline_s / max(candidate_s, 1e-12),
            "boundary_identity": True,
        })
    return {
        "schema": "cmpct-v030-fastcdc-scalar-loop-oracle-v1",
        "release_credit": False,
        "python_runtime": "must be recorded by execution environment",
        "workload": "neutral_hostile_v1/09_ml_artifacts",
        "file_count": len(files),
        "bytes": sum(r["bytes"] for r in rows),
        "baseline_total_s": baseline_total,
        "candidate_total_s": candidate_total,
        "aggregate_speedup": baseline_total / max(candidate_total, 1e-12),
        "all_boundaries_identical": all(r["boundary_identity"] for r in rows),
        "rows": rows,
        "claim_boundary": "Research micro/A-B only. Product credit requires exact CPython 3.11 hosted child/whole-product evidence and unchanged bytes/thresholds.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()
    result = run(args.work_root, max(1, args.repeats))
    import platform
    result["python_runtime"] = platform.python_version()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
