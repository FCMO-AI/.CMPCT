#!/usr/bin/env python3
"""J24I39: count untouched raw A/B repeats; never promote research oracle to product."""
import argparse
import json
import re
import statistics
from pathlib import Path

PATTERN = re.compile(
    r"([AB]) J24I39 size=(8|32) mode=(native|stream) iter=(\d+) "
    r"wall_ns=(\d+) rchar=(\d+) vmhwm_kib=(\d+)"
)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = {str(n): {"A": [], "B": []} for n in (8, 32)}
    for line in args.raw.read_text().splitlines():
        match = PATTERN.fullmatch(line)
        assert match, ("unparsed observation", line)
        lane, size, mode, iteration, wall, chars, rss = match.groups()
        assert (lane, mode) in (("A", "native"), ("B", "stream"))
        row = {"iteration": int(iteration), "wall_ns": int(wall),
               "rchar": int(chars), "vmhwm_kib": int(rss)}
        data[size][lane].append(row)
    output = {"schema": "j24i39-file-backed-flac-rung1-v1", "product_credit": False,
              "comparators_equivalent": False,
              "reason": "B consumes detached authenticated codec stream; it does not validate archive index/preflight or hostile compressed tail",
              "cases": {}}
    for size, group in data.items():
        summaries = {}
        for lane in ("A", "B"):
            raw = group[lane]
            assert len(raw) == 16, (size, lane, len(raw))
            assert all(0 <= x["iteration"] <= 3 for x in raw)
            measurements = [x for x in raw if x["iteration"] > 0]
            assert len(measurements) == 12
            summaries[lane] = {
                "samples": len(measurements),
                "wall_ns_median": statistics.median(x["wall_ns"] for x in measurements),
                "rchar_median": statistics.median(x["rchar"] for x in measurements),
                "vmhwm_kib_median": statistics.median(x["vmhwm_kib"] for x in measurements),
                "raw": raw
            }
        a, b = summaries["A"], summaries["B"]
        output["cases"][size] = {
            "native": a, "stream": b,
            "wall_ratio": a["wall_ns_median"] / b["wall_ns_median"],
            "rchar_ratio": a["rchar_median"] / b["rchar_median"],
            "stream_rss_delta_kib": b["vmhwm_kib_median"] - a["vmhwm_kib_median"]
        }
    large = output["cases"]["32"]
    output["decision"] = (
        "STREAMING_ORACLE_VALID_AND_ARCHITECTURALLY_PROMISING"
        if large["rchar_ratio"] > 1.5 and large["stream_rss_delta_kib"] < 0
        else "STREAMING_ORACLE_VALID_BUT_COST_REQUIRES_FRAME_REVIEW"
    )
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": output["decision"], "summary": {
        k: {name: value for name, value in val.items() if name not in ("native", "stream")}
        for k, val in output["cases"].items()
    }}, sort_keys=True))
if __name__ == "__main__":
    main()
