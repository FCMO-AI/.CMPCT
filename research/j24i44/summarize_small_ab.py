#!/usr/bin/env python3
"""Recompute J24I44 source-exact small-WAV A/B; never award release credit."""
import argparse
import hashlib
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

LINE = re.compile(
    r"^(?P<arm>[AB]) J24I44 iter=(?P<iter>\\d+) kib=(?P<kib>\\d+)"
    r" ns=(?P<ns>\\d+) rchar=(?P<rchar>\\d+) vmhwm_kib=(?P<rss>\\d+)$"
)
ORDER = "AB B A BA AB".replace(" ", "")  # overridden by expected list below
EXPECTED_ARMS = ["A", "B", "B", "A", "B", "A", "A", "B"]
WARMUP = 4
ITERATIONS = 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    raw = a.raw.read_text()
    manifest = json.loads(a.manifest.read_text())
    selected = [
        int(k) for k, record in manifest["records"].items() if record["selected_flac"]
    ]
    assert selected, "no real Builder-selected FLAC"
    selected.sort()
    parsed = [m.groupdict() for line in raw.splitlines() if (m := LINE.fullmatch(line))]
    assert len(parsed) == len(selected) * len(EXPECTED_ARMS) * ITERATIONS, (
        "observation count mismatch", len(parsed), selected
    )
    groups = defaultdict(list)
    index = 0
    for arm in EXPECTED_ARMS:
        for kib in selected:
            batch = parsed[index:index + ITERATIONS]
            index += ITERATIONS
            assert len(batch) == ITERATIONS
            assert all(p["arm"] == arm and int(p["kib"]) == kib for p in batch)
            assert [int(p["iter"]) for p in batch] == list(range(ITERATIONS))
            groups[(arm, kib)].append(batch)
    report = {
        "schema": "j24i44-unforced-small-wav-native-ab-v1",
        "measurement": "in-process native Archive::verify_complete; 4 per-process warmups excluded",
        "interpretation": "research crossover only; not release/whole-product approval",
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "warmup_excluded_per_process": WARMUP,
        "sources": {"A": "0faa25827e7393f927252876d40e9f6cb53e5a24",
                    "B": "J24I44 HEAD; read exact GitHub head receipt"},
        "selected_sizes_kib": selected,
        "fallback_sizes_kib": sorted(int(k) for k,v in manifest["records"].items() if not v["selected_flac"]),
        "records": {},
    }
    for kib in selected:
        measures = {}
        for arm in "AB":
            batches = groups[(arm, kib)]
            runs = [
                [int(p["ns"]) for p in batch[WARMUP:]]
                for batch in batches
            ]
            rchars = {int(p["rchar"]) for batch in batches for p in batch[WARMUP:]}
            rss = [int(p["rss"]) for batch in batches for p in batch[WARMUP:]]
            samples = [x for run in runs for x in run]
            measures[arm] = {
                "median_ns": statistics.median(samples),
                "min_ns": min(samples),
                "max_ns": max(samples),
                "process_medians_ns": [statistics.median(run) for run in runs],
                "process_median_spread_percent": 100 * (
                    max(statistics.median(run) for run in runs) /
                    min(statistics.median(run) for run in runs) - 1
                ),
                "rchar_values": sorted(rchars),
                "max_vmhwm_kib": max(rss),
                "count_after_warmup": len(samples),
                "min_max_not_a_confidence_interval": True,
            }
        ratio = measures["A"]["median_ns"] / measures["B"]["median_ns"]
        report["records"][str(kib)] = {
            "A": measures["A"], "B": measures["B"],
            "old_over_new_speed_ratio": ratio,
            "new_over_old_wall_percent": 100 * (1 / ratio - 1),
            "conclusion": "NEW_FASTER" if ratio > 1 else "NEW_SLOWER",
            "a_a_and_b_b_drift_requires_interpretation": True,
        }
    a.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("J24I44_SUMMARY_PASS", json.dumps({
        k: round(v["old_over_new_speed_ratio"], 4)
        for k, v in report["records"].items()
    }, sort_keys=True))
    print("J24I44_FALLBACK_SIZES", report["fallback_sizes_kib"])


if __name__ == "__main__":
    main()
