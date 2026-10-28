from __future__ import annotations

"""Run the multi-root target representation against the harder v2 stress corpus.

The cost model and target evaluator are imported from ``mosaic_v029_bench`` so v2 cannot quietly change
how the optimistic v0.28 floor, metadata overhead, decode verification, or locality cost is calculated.
Only the corpus becomes harder.
"""

import argparse
import json
from pathlib import Path
import time

from mosaic_stress_corpus_v2 import build as build_corpus
from mosaic_v029_bench import _measure_target


def run(corpus_root: Path) -> dict:
    started = time.perf_counter()
    manifest = build_corpus(corpus_root)
    rows = []
    for workload_meta in manifest["workloads"]:
        path = corpus_root / workload_meta["name"]
        roots = [p.read_bytes() for p in sorted(path.glob("root-*.bin"))]
        targets = sorted(path.glob("target-*.bin"))
        measured = [_measure_target(roots, target.read_bytes()) for target in targets]
        floor = sum(row["v028_optimistic_floor_bytes"] for row in measured)
        selected = sum(row["selected_bytes"] for row in measured)
        rows.append({
            **workload_meta,
            "targets_detail": measured,
            "v028_optimistic_floor_bytes": floor,
            "candidate_bytes": selected,
            "saving_vs_floor_bytes": floor - selected,
            "saving_vs_floor_pct": (floor - selected) / floor * 100.0 if floor else 0.0,
            "mosaic_selected": sum(row["selected"] == "mosaic" for row in measured),
            "max_read_amplification": max((row["mosaic_read_amplification"] for row in measured), default=0.0),
        })

    floor_total = sum(row["v028_optimistic_floor_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    return {
        "schema": "cmpct-mosaic-v029-stress-v2",
        "claim_boundary": "noisy multi-root target representation only; full archive costs remain unmeasured",
        "corpus": manifest,
        "rows": rows,
        "totals": {
            "targets": sum(row["targets"] for row in rows),
            "v028_optimistic_floor_bytes": floor_total,
            "candidate_bytes": candidate_total,
            "smaller_than_floor_pct": (floor_total - candidate_total) / floor_total * 100.0 if floor_total else 0.0,
            "mosaic_selected": sum(row["mosaic_selected"] for row in rows),
            "workloads_improved": sum(row["candidate_bytes"] < row["v028_optimistic_floor_bytes"] for row in rows),
            "workloads_regressed": sum(row["candidate_bytes"] > row["v028_optimistic_floor_bytes"] for row in rows),
            "max_read_amplification": max((row["max_read_amplification"] for row in rows), default=0.0),
            "elapsed_s": time.perf_counter() - started,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, default=Path("CMPCT_Mosaic_Stress_v2"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.corpus_root)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
