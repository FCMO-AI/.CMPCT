"""Independent O217 receipt arithmetic/shape auditor; no CMPCT Reader import.

This audits hosted experiment receipts, not the original physical archive bytes or a
third-party full-product execution. Does not convert a research win into release evidence.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics

EXPECTED_SHAPES = {
    "one-ref": (1, 1),
    "repeated-4096": (4096, 1),
    "repeated-65536": (65536, 1),
    "repeated-262144": (262144, 1),
    "mixed-256-65536": (65536, 256),
    "distinct-4096": (4096, 4096),
}
METHODS = {"original", "fast", "batched", "unguarded"}
VAL_BLOB = "51c2849061f99a4afeddb7666956b24566ce7de0"
O216_BLOB = "7002fe2db2bfc41fffbc94584cc1904922d1c1fb"


def near(a, b):
    assert math.isfinite(a) and math.isfinite(b), (a, b)
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9), (a, b)


def audit(path: Path):
    raw = path.read_bytes()
    data = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    checks = 0
    def require(ok, label):
        nonlocal checks
        assert ok, label
        checks += 1

    require(data["science_only"] is True, "research only")
    require(data["validator_blob"] == VAL_BLOB, "validator Git blob")
    require(data["source_o216"].endswith("@" + O216_BLOB), "O216 immutable baseline")
    require(len(data["head"]) == 40, "complete source head")
    cases = data["cases"]
    require(len(cases) == 25, "19 inherited + 6 held-out semantic cases")
    assert len({c["case"] for c in cases}) == 25
    positive = {"valid-single", "valid-duplicate", "valid-empty", "valid-heavy", "mixed-positive"}
    negative = {"bad-bool", "bad-float", "bad-neg", "bad-outside", "bad-late",
                "bad-late-bound", "invalid-heavy-tail", "mixed-under",
                "mixed-outside", "mixed-late-bool", "mixed-late-float",
                "mixed-late-negative"}
    by_case = {c["case"]: c for c in cases}
    for name in positive:
        require(by_case[name]["outcome"]["ok"] is True, f"positive {name}")
    for name in negative:
        require(by_case[name]["outcome"]["ok"] is False, f"negative {name}")
        require(by_case[name]["outcome"]["type"] == "ValidationError", f"type {name}")
    fixtures = data["fixtures"]
    require(len(fixtures) == len(EXPECTED_SHAPES), "number of experimental shapes")
    require({f["profile"] for f in fixtures} == set(EXPECTED_SHAPES), "shape names")
    read_shas = set()
    validator_shas = set()
    all_rows = []
    for f in fixtures:
        profile = f["profile"]
        n, d = EXPECTED_SHAPES[profile]
        require((f["count"], f["distinct"]) == (n, d), f"shape {profile}")
        require(len(f["archive_sha256"]) == 64, f"archive SHA {profile}")
        require(f["archive_bytes"] >= 100, f"physical bytes {profile}")
        obs = f["observations"]
        require(len(obs) == 24, f"24 workers {profile}")
        per_mode = collections.Counter((x["cycle"], x["mode"]) for x in obs)
        for cycle in range(3):
            for mode in METHODS:
                require(per_mode[(cycle, mode)] == 2, f"paired {profile} {cycle} {mode}")
        summary = {}
        for mode in METHODS:
            arm = [x for x in obs if x["mode"] == mode]
            require(len(arm) == 6, f"arm process count {profile}/{mode}")
            for o in arm:
                for key in ("wall_ns", "cpu_ns"):
                    nums = o[key]
                    require(len(nums) == 5, f"raw count {profile}/{mode}/{key}")
                    for value in nums:
                        require(type(value) is int and value > 0, f"raw ns {profile}/{mode}/{key}")
                read_shas.add(o["reader_source_sha256"])
                validator_shas.add(o["validation_source_sha256"])
                require(o["platform"].startswith("linux"), "Linux-only science scope")
            summary[mode] = {
                "median_worker_wall_ns": statistics.median(statistics.median(o["wall_ns"]) for o in arm),
                "median_worker_cpu_ns": statistics.median(statistics.median(o["cpu_ns"]) for o in arm),
            }
        for mode in METHODS:
            for key in ("median_worker_wall_ns", "median_worker_cpu_ns"):
                near(summary[mode][key], f["summary"][mode][key])
                checks += 1
        orig, fast, batched, unguarded = [summary[m]["median_worker_wall_ns"] for m in
                                           ("original", "fast", "batched", "unguarded")]
        near(f["baseline_to_fast_ratio"], orig / fast)
        near(f["fast_to_batched_ratio"], fast / batched)
        near(f["batched_to_unguarded_ratio"], batched / unguarded)
        near(f["fast_to_unguarded_oracle_ratio"], fast / unguarded)
        near(f["fast_extra_wall_ms"], (fast - unguarded) / 1e6)
        checks += 5
        expected_debt = fast / unguarded > 2 and (
            (n == 65536 and (fast - unguarded) / 1e6 > 5)
            or (n == 262144 and (fast - unguarded) / 1e6 > 20))
        require(f["still_material_debt"] is expected_debt, f"debt predicate {profile}")
        all_rows.append((profile, n, d, fast / batched, batched / unguarded))
    require(len(read_shas) == 1, "single Reader identity")
    require(len(validator_shas) == 1, "single validator identity")
    gain = all(v >= 1.25 for _, n, d, v, _ in all_rows if n >= 65536 and d == 1)
    diverse_red = any(v < 0.70 for _, _, d, v, _ in all_rows if d > 1)
    require(data["high_n_strict_gain_predicate"] is gain, "gain predicate")
    require(data["diverse_regression_predicate"] is diverse_red, "diverse predicate")
    expected = ("BATCHED_REF_SEMANTICS_MATCH_AND_HIGH_N_GAIN" if gain and not diverse_red
                else "BATCHED_REF_OWNER_COUNTER_INSUFFICIENT_OR_NARROW")
    require(data["classification"] == expected, "classification")
    receipt = {
        "schema": "o217-independent-raw-replay-v1",
        "science_only": True,
        "source_head": data["head"],
        "source_validator_git_blob": data["validator_blob"],
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "independent_checks_pass": checks,
        "discrepancies": 0,
        "original_cases": len(cases),
        "processes": sum(len(f["observations"]) for f in fixtures),
        "timed_samples_per_metric": sum(len(o["wall_ns"]) for f in fixtures for o in f["observations"]),
        "classification": expected,
        "comparisons": [{"shape": profile, "refs": n, "distinct": d,
                         "fast_over_batch_ratio": ratio, "batch_over_unsafe_ratio": unsafe}
                        for profile, n, d, ratio, unsafe in all_rows],
        "scope_limit": "Receipt replay, not independent Reader/physical-archive replication",
    }
    return receipt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = audit(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("O217_INDEPENDENT_REPLAY=PASS", result["independent_checks_pass"])
    print("O217_INDEPENDENT_DECISION=" + result["classification"])


if __name__ == "__main__":
    main()
