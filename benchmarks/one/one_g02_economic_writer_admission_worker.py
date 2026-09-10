from __future__ import annotations

"""Fresh-process resource worker for ONE-G0.2 economic writer admission transfer tests."""

import argparse
import json
from pathlib import Path
import resource
import statistics
import time

from experiments.one.general_law_archive import build_general_law_archive


def run(source: Path, *, economic_admission: bool, repeats: int) -> dict[str, object]:
    cpu_samples: list[float] = []
    wall_samples: list[float] = []
    wire_bytes: list[int] = []
    proof_bytes: list[int] = []
    sampled_bytes: list[int] = []

    for _ in range(repeats):
        cpu0 = time.process_time()
        wall0 = time.perf_counter()
        wire, stats = build_general_law_archive(source, economic_admission=economic_admission)
        wall_samples.append(time.perf_counter() - wall0)
        cpu_samples.append(time.process_time() - cpu0)
        wire_bytes.append(len(wire))
        proof_bytes.append(stats.discovery_exact_proof_bytes)
        sampled_bytes.append(stats.discovery_sample_bytes)

    if len(set(wire_bytes)) != 1 or len(set(proof_bytes)) != 1 or len(set(sampled_bytes)) != 1:
        raise RuntimeError("writer resource worker observed non-deterministic accounting")

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "economic_admission": economic_admission,
        "repeats": repeats,
        "median_cpu_s": statistics.median(cpu_samples),
        "median_wall_s": statistics.median(wall_samples),
        "min_cpu_s": min(cpu_samples),
        "min_wall_s": min(wall_samples),
        "peak_rss_kib": int(rss),
        "wire_bytes": wire_bytes[0],
        "discovery_exact_proof_bytes": proof_bytes[0],
        "discovery_sample_bytes": sampled_bytes[0],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--economic-admission", action="store_true")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 3:
        raise SystemExit("repeats must be >=3")
    print(json.dumps(run(args.source, economic_admission=args.economic_admission, repeats=args.repeats), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
