#!/usr/bin/env python3
"""Independent raw receipt audit for O224. Does not import experimental court."""
import collections
import json
import math
from pathlib import Path
import statistics
import sys

EXPECTED_N = (4096, 65536, 262144)
KINDS = ("fixed", "cdc")
LAYOUTS = ("repeat", "eight")
ARMS = ("plain", "skip", "instrumented")
STAGES = ("before_open", "after_decompress", "after_unpack",
          "before_validation", "after_validation", "after_open")
PREREG = "c630c7e15637c51895d70ad7ef3f8fd96f1a3214"
READER_BLOB = "dbd4ac576a05a47eae97e1e40de89cf1de440516"


def median_event(rows, stage):
    return statistics.median(next(e for e in r["events"] if e["stage"] == stage)
                             ["rss"]["VmHWM_kib"] for r in rows)


def audit(path):
    data = json.loads(Path(path).read_text())
    assert data["schema"] == "o224-reader-open-phase-rss-v1"
    assert data["prereg_commit"] == PREREG and data["reader_blob"] == READER_BLOB
    fixtures = {(f["n"], f["kind"], f["layout"]): f for f in data["fixtures"]}
    assert len(fixtures) == 12
    assert len(data["samples"]) == 112
    counts = collections.Counter()
    unique = set()
    checks = 0
    nonmonotonic_total = 0
    for s in data["samples"]:
        key = (s["n"], s["kind"], s["layout"])
        assert s["n"] in EXPECTED_N and s["kind"] in KINDS and s["layout"] in LAYOUTS
        f = fixtures[key]
        assert s["archive_sha256"] == f["archive_sha256"]
        assert s["expected_sha256"] == f["expected_sha256"]
        assert s["result_last_byte"] == f["last_byte_hex"]
        assert s["python"].startswith("3.12.")
        arm = s["arm"]
        rep = s["repeat"]
        assert arm in (*ARMS, "instrumented_trace")
        if arm == "instrumented_trace":
            assert rep == "traced_control" and s["n"] == 262144 and s["trace"]
        else:
            assert rep in (0, 1, 2) and not s["trace"]
        ident = (*key, arm, rep)
        assert ident not in unique
        unique.add(ident)
        counts[arm] += 1
        assert s["open_wall_ms"] >= 0 and s["session_wall_ms"] >= s["open_wall_ms"]
        stages = [e["stage"] for e in s["events"]]
        assert stages[0] == "before_open" and "after_open" in stages
        assert stages[-1] == "after_close"
        if arm.startswith("instrumented"):
            assert "before_validation" in stages and "after_validation" in stages
            assert stages.index("before_validation") < stages.index("after_validation")
            assert stages.index("after_validation") < stages.index("after_open")
        times = [e["time_ns"] for e in s["events"]]
        assert times == sorted(times)
        hwm = [e["rss"]["VmHWM_kib"] for e in s["events"]]
        if hwm != sorted(hwm):
            nonmonotonic_total += 1  # Explicit invalidation; preserve every raw observation.
        for event in s["events"]:
            mem = event["rss"]
            for k in ("VmRSS_kib", "VmHWM_kib", "VmSize_kib", "ru_maxrss_kib"):
                assert isinstance(mem[k], int) and mem[k] > 0
            assert mem["VmHWM_kib"] >= mem["VmRSS_kib"]
            checks += 1
    assert counts == {"plain": 36, "skip": 36, "instrumented": 36,
                      "instrumented_trace": 4}
    by_profile = {(x["kind"], x["layout"]): x for x in data["findings"]}
    assert len(by_profile) == 4
    alternative = []
    for kind in KINDS:
        for layout in LAYOUTS:
            found = by_profile[(kind, layout)]
            group = [r for r in data["samples"] if r["n"] == 262144
                     and r["kind"] == kind and r["layout"] == layout]
            subset = {arm: [r for r in group if r["arm"] == arm] for arm in ARMS}
            assert all(len(v) == 3 for v in subset.values())
            a = median_event(subset["plain"], "after_open")
            b = median_event(subset["skip"], "after_open")
            c = median_event(subset["instrumented"], "after_open")
            before = median_event(subset["instrumented"], "before_open")
            perturb = (c - a) / a
            missing = [stage for stage in STAGES if any(stage not in
                       [e["stage"] for e in row["events"]] for row in subset["instrumented"])]
            inc = {}
            if not missing:
                for left, right in zip(STAGES, STAGES[1:]):
                    inc[right] = median_event(subset["instrumented"], right) - median_event(
                        subset["instrumented"], left)
            winner = max(inc, key=inc.get) if inc else None
            ratio = inc[winner] / (c-before) if winner and c > before else None
            nonmonotonic_staged = sum(
                [e["rss"]["VmHWM_kib"] for e in row["events"]] != sorted(
                    e["rss"]["VmHWM_kib"] for e in row["events"])
                for row in subset["instrumented"])
            expected = {
                "nonmonotonic_staged_samples": nonmonotonic_staged,
                "valid_stage_claim": bool(not missing and not nonmonotonic_staged and
                                          perturb <= .15 and c > before and winner),
                "baseline_hwm_kib": a, "skip_hwm_kib": b,
                "instrumented_hwm_kib": c, "no_validation_hwm_saving_kib": a-b,
                "instrumentation_inflation_fraction": perturb,
                "growth_instrumented_kib": c-before, "missing_stages": missing,
                "stage_hwm_increment_kib": inc, "largest_stage": winner,
                "largest_stage_fraction": ratio,
            }
            for k, v in expected.items():
                seen = found[k]
                if isinstance(v, float) and v is not None:
                    assert math.isclose(seen, v, rel_tol=1e-9, abs_tol=1e-9), (k,v,seen)
                else:
                    assert seen == v, (k,v,seen)
                checks += 1
            alternative.append((perturb, a-b, ratio, winner, inc.get(winner, 0),
                                bool(not missing and perturb <= .15 and c > before and winner),
                                nonmonotonic_staged > 0))
    perturbed = any(r[0] > .15 for r in alternative)
    invalid_stage_hwm = any(r[6] for r in alternative)
    owner = (not invalid_stage_hwm and not perturbed and all(r[5] and r[2] >= .60 and r[4] >= 65536 for r in alternative)
             and len({r[3] for r in alternative}) == 1)
    decision = {
        "stage": "INVALID_STAGE_HWM_SEQUENCE" if invalid_stage_hwm else
                 "DOMINANT_PHASE_SCOPED" if owner else
                 "MEASUREMENT_PERTURBED" if perturbed else "MIXED_OR_UNRESOLVED",
        "largest_stage": alternative[0][3] if owner else None,
        "validation_counterfactual": ("VALIDATOR_COUNTERFACTUAL_HEADROOM" if
                                      all(r[1] >= 65536 for r in alternative) else
                                      "VALIDATOR_HWM_NOT_PROVEN"),
    }
    assert data["decision"] == decision, (decision, data["decision"])
    return {"audit": "PASS_NEGATIVE_STAGE_INVALID" if invalid_stage_hwm else "PASS",
            "stage_hwm_nonmonotonic_samples": nonmonotonic_total,
            "schema": data["schema"], "sample_count": len(unique),
            "metric_assertions": checks, "fixtures": len(fixtures),
            "decision": decision, "source_reader_blob": READER_BLOB}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), indent=2, sort_keys=True))
