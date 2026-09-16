from __future__ import annotations

"""H-EFFORT-5 held-out RAW-terminal transfer referee.

Frozen by docs/V030_RAW_TERMINAL_GATE_MISSION_LOCK_2026-09-13.md.
This instrument never modifies the encoder. It asks whether the existing level-1
RAW fallback is an exact hard terminal for later compression effort on five
structurally different hostile workloads that H-EFFORT-4 did not use.
"""

import argparse
import json
from pathlib import Path
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_adaptive_effort_economics_referee as H4

EXPECTED_NAMES = (
    "01_shifted_versions",
    "02_false_neighbors",
    "03_boundary_churn",
    "04_deflate_family",
    "05_incompressible",
)
RAW_CODEC = 0
LATER_LEVELS = (3, 6, 9, 12, 19)


def _level(row: dict, level: int) -> dict:
    return next(item for item in row["curve"] if int(item["level"]) == level)


def _summarize(rows: list[dict]) -> dict:
    raw_rows = [row for row in rows if int(_level(row, 1)["codec"]) == RAW_CODEC]
    counterexamples: list[dict] = []
    workload_raw_counts: dict[str, int] = {}
    workload_total_counts: dict[str, int] = {}

    avoided_cpu = 0.0
    avoided_wall = 0.0
    raw_bytes = 0
    closest_later_delta = None

    for row in rows:
        workload_total_counts[row["workload"]] = workload_total_counts.get(row["workload"], 0) + 1

    for row in raw_rows:
        workload = row["workload"]
        workload_raw_counts[workload] = workload_raw_counts.get(workload, 0) + 1
        raw_bytes += int(row["raw_bytes"])
        avoided_cpu += float(row["historical"]["cumulative_cpu_s"])
        avoided_wall += float(row["historical"]["cumulative_wall_s"])

        l1 = _level(row, 1)
        l1_bytes = int(l1["bytes"])
        later = [_level(row, level) for level in LATER_LEVELS]
        best = min(later, key=lambda item: (int(item["bytes"]), int(item["level"])))
        delta = int(best["bytes"]) - l1_bytes
        if closest_later_delta is None or delta < closest_later_delta:
            closest_later_delta = delta
        if delta < 0:
            counterexamples.append(
                {
                    "workload": workload,
                    "pack_index": int(row["pack_index"]),
                    "raw_sha256": row["raw_sha256"],
                    "raw_bytes": int(row["raw_bytes"]),
                    "level1_bytes": l1_bytes,
                    "winning_level": int(best["level"]),
                    "winning_bytes": int(best["bytes"]),
                    "byte_gain": -delta,
                    "winning_cpu_s": float(best["cpu_s"]),
                    "winning_wall_s": float(best["wall_s"]),
                }
            )

    applicable_surfaces = sorted(name for name, count in workload_raw_counts.items() if count > 0)
    if counterexamples:
        verdict = "RAW_TERMINAL_FALSIFIED"
    elif len(applicable_surfaces) < 2:
        verdict = "RAW_TERMINAL_INSUFFICIENT_TRANSFER"
    else:
        verdict = "RAW_TERMINAL_TRANSFERS"

    return {
        "verdict": verdict,
        "packs": len(rows),
        "level1_raw_packs": len(raw_rows),
        "level1_nonraw_packs": len(rows) - len(raw_rows),
        "applicable_workload_families": applicable_surfaces,
        "workload_raw_pack_counts": workload_raw_counts,
        "workload_total_pack_counts": workload_total_counts,
        "level1_raw_pack_bytes": raw_bytes,
        "avoided_historical_post_l1_cpu_s": avoided_cpu,
        "avoided_historical_post_l1_wall_s": avoided_wall,
        "closest_later_bytes_minus_l1_raw": closest_later_delta,
        "counterexample_count": len(counterexamples),
        "counterexamples": counterexamples,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("raw-terminal-transfer.json"))
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="cmpct-h-effort-5-") as td:
        root = Path(td)
        corpus = root / "corpus"
        manifest = HOSTILE.build(corpus)
        observed = tuple(row["name"] for row in manifest["workloads"])
        if observed != EXPECTED_NAMES:
            raise RuntimeError(
                f"hostile transfer substrate drift: expected={EXPECTED_NAMES!r} observed={observed!r}"
            )

        rows: list[dict] = []
        work = root / "work"
        for item in manifest["workloads"]:
            name = item["name"]
            rows.extend(H4._workload_rows(corpus / name, {"name": name}, work / name))

    summary = _summarize(rows)
    out = {
        "schema": "cmpct-v030-raw-terminal-transfer-referee-v1",
        "status": "held-out R0/R3 research evidence; no selector/product/release credit",
        "mission_lock": "docs/V030_RAW_TERMINAL_GATE_MISSION_LOCK_2026-09-13.md",
        "source_generator": "benchmarks/resemblance_hostile_corpus_v1.py",
        "substrate_manifest": manifest,
        "levels": list(H4.LEVELS),
        "repetitions": H4.REPS,
        "raw_codec": RAW_CODEC,
        "rows": rows,
        "summary": summary,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["verdict"] == "RAW_TERMINAL_INSUFFICIENT_TRANSFER":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
