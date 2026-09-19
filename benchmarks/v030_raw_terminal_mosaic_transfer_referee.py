from __future__ import annotations

"""H-EFFORT-5B independent Mosaic hostile court for the RAW hard-terminal hypothesis."""

import argparse
import json
from pathlib import Path
import tempfile

from benchmarks import mosaic_hostile_corpus_v1 as MOSAIC
from benchmarks import v030_adaptive_effort_economics_referee as H4

EXPECTED_NAMES = (
    "01_two_parent_branch_merge",
    "02_four_way_cherry_pick",
    "03_reordered_two_parent_merge",
    "04_source_tree_merge",
    "05_single_parent_control",
    "06_false_mosaic_sources",
    "07_incompressible_control",
    "08_duplicate_root_pressure",
)
LATER_LEVELS = (3, 6, 9, 12, 19)
RAW_CODEC = 0


def _level(row: dict, level: int) -> dict:
    return next(item for item in row["curve"] if int(item["level"]) == level)


def summarize(rows: list[dict]) -> dict:
    raw_rows = [row for row in rows if int(_level(row, 1)["codec"]) == RAW_CODEC]
    total_by: dict[str, int] = {}
    raw_by: dict[str, int] = {}
    counterexamples: list[dict] = []
    raw_bytes = 0
    avoided_cpu = avoided_wall = 0.0
    closest_delta: int | None = None

    for row in rows:
        total_by[row["workload"]] = total_by.get(row["workload"], 0) + 1

    for row in raw_rows:
        name = row["workload"]
        raw_by[name] = raw_by.get(name, 0) + 1
        raw_bytes += int(row["raw_bytes"])
        avoided_cpu += float(row["historical"]["cumulative_cpu_s"])
        avoided_wall += float(row["historical"]["cumulative_wall_s"])
        l1 = _level(row, 1)
        later = [_level(row, level) for level in LATER_LEVELS]
        best = min(later, key=lambda item: (int(item["bytes"]), int(item["level"])))
        delta = int(best["bytes"]) - int(l1["bytes"])
        closest_delta = delta if closest_delta is None else min(closest_delta, delta)
        if delta < 0:
            counterexamples.append(
                {
                    "workload": name,
                    "pack_index": int(row["pack_index"]),
                    "raw_sha256": row["raw_sha256"],
                    "raw_bytes": int(row["raw_bytes"]),
                    "level1_bytes": int(l1["bytes"]),
                    "winning_level": int(best["level"]),
                    "winning_bytes": int(best["bytes"]),
                    "byte_gain": -delta,
                    "winning_cpu_s": float(best["cpu_s"]),
                    "winning_wall_s": float(best["wall_s"]),
                }
            )

    applicable = sorted(name for name, count in raw_by.items() if count)
    if counterexamples:
        verdict = "RAW_TERMINAL_SECOND_COURT_FALSIFIED"
    elif len(applicable) < 2:
        verdict = "RAW_TERMINAL_SECOND_COURT_INSUFFICIENT"
    else:
        verdict = "RAW_TERMINAL_SECOND_COURT_TRANSFERS"

    return {
        "verdict": verdict,
        "packs": len(rows),
        "level1_raw_packs": len(raw_rows),
        "level1_nonraw_packs": len(rows) - len(raw_rows),
        "level1_raw_pack_bytes": raw_bytes,
        "applicable_workload_families": applicable,
        "workload_raw_pack_counts": raw_by,
        "workload_total_pack_counts": total_by,
        "avoided_historical_post_l1_cpu_s": avoided_cpu,
        "avoided_historical_post_l1_wall_s": avoided_wall,
        "closest_later_bytes_minus_l1_raw": closest_delta,
        "counterexample_count": len(counterexamples),
        "counterexamples": counterexamples,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("raw-terminal-mosaic-transfer.json"))
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="cmpct-h-effort-5b-") as td:
        root = Path(td)
        corpus = root / "corpus"
        manifest = MOSAIC.build(corpus)
        observed = tuple(row["name"] for row in manifest["workloads"])
        if observed != EXPECTED_NAMES:
            raise RuntimeError(
                f"Mosaic hostile substrate drift: expected={EXPECTED_NAMES!r} observed={observed!r}"
            )
        rows: list[dict] = []
        for item in manifest["workloads"]:
            name = item["name"]
            rows.extend(H4._workload_rows(corpus / name, {"name": name}, root / "work" / name))

    summary = summarize(rows)
    out = {
        "schema": "cmpct-v030-raw-terminal-mosaic-transfer-v1",
        "status": "independent hostile R0/R3 evidence; no selector/product/release credit",
        "mission_lock": "docs/V030_RAW_TERMINAL_MOSAIC_TRANSFER_MISSION_LOCK_2026-09-13.md",
        "source_generator": "benchmarks/mosaic_hostile_corpus_v1.py",
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
    if summary["verdict"] == "RAW_TERMINAL_SECOND_COURT_INSUFFICIENT":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
