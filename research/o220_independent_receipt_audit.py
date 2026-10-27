#!/usr/bin/env python3
"""Independent O220 raw-receipt verifier (no CMPCT source import, no trust in summaries).

Reject duplicate JSON keys, nonfinite numbers, missing/duplicate worker pairs, and
outcomes inconsistent with the prospectively frozen median materiality test.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from pathlib import Path
import statistics

COUNTS = (4096, 65536, 262144)
MODES = ("rust_cli", "python_cli")
SAMPLES_PER_MODE = 9


def strict_pairs(pairs):
    d = {}
    for key, val in pairs:
        if key in d:
            raise ValueError("duplicate JSON key: " + key)
        d[key] = val
    return d


def no_constant(value):
    raise ValueError("nonfinite JSON constant " + value)


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=strict_pairs,
                      parse_constant=no_constant)


def req_int(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("expected integer at least " + str(minimum))
    return value


def req_float(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("nonfinite/non-numeric summary")
    return float(value)


def near(a, b):
    if not math.isclose(req_float(a), req_float(b), rel_tol=1e-9, abs_tol=1e-3):
        raise ValueError("raw/summary metric mismatch")


def audit(x):
    src = x["source"]
    for name in ("head", "reader_blob", "native_core_blob", "native_executable_sha256"):
        z = src[name]
        if not isinstance(z, str) or len(z) not in (40, 64) or any(c not in "0123456789abcdef" for c in z):
            raise ValueError("invalid source identity: " + name)
    if src["reader_blob"] != "dbd4ac576a05a47eae97e1e40de89cf1de440516":
        raise ValueError("inherited reader changed")
    cases = x["semantic_controls"]
    if [c["case"] for c in cases] != [
            "valid-4096", "valid-65536", "valid-262144",
            "primary-overdeclared", "missing-physical-ref"]:
        raise ValueError("incomplete semantic controls")
    for i, case in enumerate(cases):
        if set(case["acceptance"]) != set(MODES):
            raise ValueError("missing CLI admission control")
        for mode in MODES:
            if case["acceptance"][mode] is not (i < 3):
                raise ValueError("semantic acceptance mismatch")
            if (case["return_codes"][mode] == 0) is not case["acceptance"][mode]:
                raise ValueError("return code mismatch")
        if i < 3 and case["successful_cross_language_ranges"] != 3:
            raise ValueError("cross-language range count mismatch")
        req_int(case["archive_bytes"], 1)
        if len(case["archive_sha256"]) != 64:
            raise ValueError("archive digest missing")
    journal = x["journal_counterexample"]
    if not (journal["python_accepts_later_valid_checkpoint"]
            and journal["native_rejects_invalid_primary"]
            and journal["semantic_equivalence"] is False):
        raise ValueError("signed journal semantic veto not demonstrated")
    profiles = x["profiles"]
    if len(profiles) != 3 or [p["reference_count"] for p in profiles] != list(COUNTS):
        raise ValueError("missing/duplicate profile")
    summary = []
    for p in profiles:
        req_int(p["archive_bytes"], 1)
        if len(p["archive_sha256"]) != 64:
            raise ValueError("archive SHA absent")
        if len(p["samples"]) != 2 * SAMPLES_PER_MODE:
            raise ValueError("wrong number of raw samples")
        seen = set()
        grouped = {mode: [] for mode in MODES}
        for row in p["samples"]:
            pair = req_int(row["pair"])
            mode = row["mode"]
            if pair >= SAMPLES_PER_MODE or mode not in MODES or (pair, mode) in seen:
                raise ValueError("bad/duplicate pair mode")
            seen.add((pair, mode))
            for name, lower in (("wall_ns", 1), ("cpu_ns", 0), ("maxrss_kib", 1)):
                req_int(row[name], lower)
            grouped[mode].append(row)
        if seen != {(i, mode) for i in range(SAMPLES_PER_MODE) for mode in MODES}:
            raise ValueError("missing pair")
        calculated = {}
        for mode in MODES:
            calculated[mode] = {}
            for metric in ("wall_ns", "cpu_ns", "maxrss_kib"):
                value = statistics.median(r[metric] for r in grouped[mode])
                near(p["summary"][mode][metric], value)
                calculated[mode][metric] = value
        rust = calculated["rust_cli"]["wall_ns"]
        py = calculated["python_cli"]["wall_ns"]
        ratio = py / rust
        saved_ms = (py - rust) / 1e6
        near(p["python_to_native_wall_ratio"], ratio)
        near(p["python_minus_native_ms"], saved_ms)
        summary.append({"count": p["reference_count"], "rust_wall_ns": rust,
                        "python_wall_ns": py, "py_to_native": ratio,
                        "saved_ms": saved_ms,
                        "rust_peak_rss_kib": calculated["rust_cli"]["maxrss_kib"],
                        "python_peak_rss_kib": calculated["python_cli"]["maxrss_kib"]})
    material = summary[-1]["py_to_native"] >= 2.0 and summary[-1]["saved_ms"] >= 5.0
    decision = ("PRIMARY_ONLY_NATIVE_ECONOMIC_HEADROOM_WITH_RECOVERY_DEBT" if material
                else "NATIVE_CLI_NO_MATERIAL_FULL_PROCESS_GAIN_WITH_RECOVERY_DEBT")
    if x["decision"] != decision or x["preregistered_materiality_met"] is not material:
        raise ValueError("decision changed after results")
    if x.get("scope") != "science only; CLI-to-CLI startup included; no native journal equivalence":
        raise ValueError("claim scope drift")
    return {"classification": decision, "result": "PASS", "source_head": src["head"],
            "profile_replay": summary, "journal_semantic_veto": True,
            "raw_samples_audited": 54}


def self_test(x):
    valid = audit(x)
    attacks = []
    def negative(label, mutation):
        item = copy.deepcopy(x)
        mutation(item)
        try:
            audit(item)
        except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError):
            attacks.append(label)
            return
        raise AssertionError("tampering escaped audit: " + label)
    negative("duplicate_sample", lambda t: t["profiles"][0]["samples"].__setitem__(
        0, copy.deepcopy(t["profiles"][0]["samples"][1])))
    negative("lost_sample", lambda t: t["profiles"][0]["samples"].pop())
    negative("forged_median", lambda t: t["profiles"][1]["summary"]["rust_cli"].__setitem__(
        "wall_ns", 1))
    negative("forged_ratio", lambda t: t["profiles"][2].__setitem__(
        "python_to_native_wall_ratio", 999.0))
    negative("forged_decision", lambda t: t.__setitem__("decision", "PROMOTE"))
    negative("journal_veto_removed", lambda t: t["journal_counterexample"].__setitem__(
        "semantic_equivalence", True))
    negative("semantic_false_accept", lambda t: t["semantic_controls"][3]["acceptance"].__setitem__(
        "rust_cli", True))
    negative("raw_nonfinite", lambda t: t["profiles"][0]["samples"][0].__setitem__(
        "wall_ns", float("nan")))
    if len(attacks) != 8:
        raise ValueError("incomplete mutation court")
    return {"negative_mutations_rejected": attacks, "baseline": valid["result"]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    x = read(args.input)
    result = audit(x)
    result["self_test"] = self_test(x)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("O220_INDEPENDENT_RECEIPT_CHECK=PASS", flush=True)
    print("O220_NEGATIVE_RECEIPT_MUTATIONS=%d" % len(result["self_test"]["negative_mutations_rejected"]), flush=True)


if __name__ == "__main__":
    main()
