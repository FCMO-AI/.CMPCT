#!/usr/bin/env python3
"""O36 research-only authentic r24 A/B: original O31 vs disposable exact-hit prototype.

The historical owner/product, byte-frozen scientific corpus and source-bound
fresh-process child are reused from O33. No product changes are committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

import research_o33_reader_hardlink_economics as o33

OWNER_SHA = "0edb7bc6e832deb1b403fea50c36e655da9844fd"
OWNER_READER_BLOB = "de9accf6607aca7cf70dfe71d7b299a02e298a2d"
INSTRUMENT_BLOB = "8aabcc100843475068031e39a8a4cfb74edfddac"


def run(owner: Path, oracle: Path, out: Path, reps: int) -> dict:
    if reps < 8 or reps % 2:
        raise ValueError("At least eight even-count fresh processes per source/shape required")
    owner, oracle, out = owner.resolve(), oracle.resolve(), out.resolve()
    if owner == oracle:
        raise ValueError("A/B sources must be distinct")
    out.mkdir(parents=True, exist_ok=True)
    # O33 itself authenticates every r24 corpus with independent structural
    # preflight and complete Reader SHA/range/verify before any timed process.
    cases = o33.generate(out / "archives")
    observations = []
    summaries = []
    child = Path(o33.__file__).resolve()
    for case in cases:
        for quartet in range(reps // 2):
            order = ("owner", "oracle", "oracle", "owner") if quartet % 2 == 0 else (
                "oracle", "owner", "owner", "oracle"
            )
            for label in order:
                source = owner if label == "owner" else oracle
                cmd = [sys.executable, str(child), "--child",
                       "--source", str(source), "--archive", case["path"],
                       "--samples", ",".join(case["samples"])]
                env = {**os.environ, "PYTHONHASHSEED": "0"}
                start = time.perf_counter_ns()
                proc = subprocess.run(cmd, capture_output=True, text=True,
                                      env=env, timeout=90, check=False)
                outer_ms = (time.perf_counter_ns() - start) / 1e6
                if proc.returncode:
                    raise RuntimeError(
                        f"O36 {label} {case['shape']}/{case['size']} child failed: "
                        f"{proc.returncode}\n{proc.stdout}\n{proc.stderr}"
                    )
                values = json.loads(proc.stdout.strip())
                if values["files"] != case["size"]:
                    raise RuntimeError("Authenticated file count mismatch")
                observations.append({
                    "shape": case["shape"], "size": case["size"],
                    "label": label, "quartet": quartet, "complete_ms": outer_ms,
                    "archive_sha256": case["sha256"], **values,
                })
        subset = [v for v in observations if v["shape"] == case["shape"]
                  and v["size"] == case["size"]]
        orig = [v for v in subset if v["label"] == "owner"]
        fast = [v for v in subset if v["label"] == "oracle"]
        if len(orig) != reps or len(fast) != reps:
            raise RuntimeError("Incomplete fresh-process ABBA court")
        fields = ("construct_ms", "cpu_construct_ms", "complete_ms",
                  "import_ms", "rss_post_kib", "hwm_delta_kib")
        def med(values: list[dict], metric: str) -> float:
            return statistics.median([v[metric] for v in values])
        costs = {field: {"owner": med(orig, field), "oracle": med(fast, field)}
                 for field in fields}
        elapsed = costs["construct_ms"]
        gain = elapsed["owner"] - elapsed["oracle"]
        speedup = elapsed["owner"] / elapsed["oracle"]
        summary = {
            "shape": case["shape"], "size": case["size"],
            "metrics": costs, "constructor_gain_ms": gain,
            "constructor_speedup": speedup,
            "reps_per_source": reps, "archive_sha256": case["sha256"],
        }
        summaries.append(summary)
        print("O36_RESULT " + json.dumps(summary, sort_keys=True), flush=True)
    fanout = next(v for v in summaries if v["shape"] == "fanout" and v["size"] == 4096)
    plain = next(v for v in summaries if v["shape"] == "plain" and v["size"] == 4096)
    p = plain["metrics"]["construct_ms"]
    plain_regression = p["oracle"] - p["owner"]
    semantic_oracle_value = (
        fanout["constructor_gain_ms"] >= 2.0
        and not (plain_regression >= 3.0 and plain_regression / p["owner"] >= .10)
    )
    report = {
        "experiment": "O36", "tier": "DISPOSABLE_SOURCE_ORACLE_NOT_PRODUCT",
        "source_owner_sha": OWNER_SHA,
        "source_owner_reader_blob": OWNER_READER_BLOB,
        "frozen_o33_instrument_blob": INSTRUMENT_BLOB,
        "owner_path": str(owner), "prototype_path": str(oracle),
        "prototype_reader_sha256": hashlib.sha256(
            (oracle / "cmpct" / "reader.py").read_bytes()
        ).hexdigest(),
        "python": sys.version, "platform": platform.platform(),
        "source_semantics": "O31 exact-hit-on-prevalidated-raw-name; original fallback",
        "criteria": {
            "fanout_4096_constructor_gain_at_least_ms": 2.0,
            "plain_4096_regression_requires_relative_and_absolute": [0.10, 3.0],
        },
        "research_decision": (
            "WORTH_PRODUCT_OWNER_REVIEW_NOT_RELEASE" if semantic_oracle_value
            else "INSUFFICIENT_ECONOMIC_HEADROOM_RETIRE_OR_NARROW"
        ),
        "corpus": cases, "summaries": summaries, "raw": observations,
        "limitations": [
            "Linux-only source experiment, not a product release or change.",
            "A disposable worktree patch is measured but never committed to src/cmpct.",
            "No truly cold Linux page cache claim despite fresh interpreters.",
            "Authentic r24 RAW one-owner isolates Reader logical index and hardlink graph.",
            "Original owner compatibility/hostile tests are an independent mandatory CI step.",
            "Observed gain on synthetic graph is not generic filesystem/corpus throughput.",
            "No native ABI, compression ratio, extraction race, or full parity credit.",
        ],
    }
    path = out / "o36-raw.json"
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("O36_RECEIPT " + json.dumps({
        "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "decision": report["research_decision"],
    }, sort_keys=True), flush=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-source", type=Path, required=True)
    parser.add_argument("--prototype-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=8)
    args = parser.parse_args()
    run(args.owner_source, args.prototype_source, args.out, args.reps)


if __name__ == "__main__":
    main()
