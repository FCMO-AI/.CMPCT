#!/usr/bin/env python3
"""J24G12 independent receipt referee: stdlib only, NO CMPCT import.

Recalculates original raw child-process observations and attacks the receipt.
Cannot independently reconstruct physical .cmpct bytes absent from artifact.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess

BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PARENT = "698f576a13ae1d14f248271185de3503ed839ee7"
PREREG = "991ddfa2a42bddaa8d76efdd3524a71c9de52b27"
ARMS = ("eager", "skip", "guarded")
CASES = {
    "writer-rename": (5, 2, 3, 3, 1),
    "valid-64": (3, 65, 129, 129, 64),
    "valid-512": (3, 513, 1025, 1025, 512),
    "orphan-4096": (3, 4097, 4097, 4097, 0),
    "independent-4096": (2, 4097, 4097, 4097, 0),
    "signed-malformed": (1, 1, 2, 1, 0),
}


def load_strict(path):
    def unique(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("duplicate JSON property " + k)
            out[k] = v
        return out
    def no_constant(v):
        raise ValueError("nonfinite JSON value: " + v)
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=no_constant)


def verify(d, s):
    checks = 0
    def req(ok, message):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(message)
    req(d.get("scientific_decision") == "RESEARCH_ONLY_NOT_PRODUCT_PROMOTABLE", "decision")
    req(d.get("prereg") == PREREG, "prereg")
    req(d.get("reader_blob") == BLOB and d.get("parent_head") == PARENT, "source")
    req(d.get("release_credit") == 0, "release credit")
    req(d.get("format_change") is False, "format")
    req(d.get("source_mutation_safety") is False, "mutation")
    req(d.get("whole_reader_resource_bound") is False, "resource claim")
    req(d.get("naive_skip_semantic_difference") is True, "malformed discriminator")

    expected_files = (
        "src/cmpct/reader.py",
        "research/j24g12_lazy_ancestry_court.py",
        "research/j24g12_independent_receipt_audit.py",
        "docs/v031-research/2026-10-28-j24g12-lazy-ancestry-prereg.md",
    )
    req(len(s.get("head", "")) == 40, "head receipt")
    req(s["head"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip(), "head mismatch")
    for p in expected_files:
        req(p in s["files"], "file missing " + p)
        b = Path(p).read_bytes()
        req(s["files"][p]["sha256"] == hashlib.sha256(b).hexdigest(),
            "changed checkout " + p)
        req(s["files"][p]["git_blob"] == subprocess.check_output(
            ["git", "rev-parse", "HEAD:"+p], text=True).strip(), "Git blob "+p)
    req(subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
                                text=True).strip() == BLOB, "Reader blob changed")

    req(set(d.get("cases", {})) == set(CASES), "case coverage")
    number_fields = ("wall_ms", "cpu_ms", "peak_traced_bytes",
                     "ru_maxrss_kib_linux", "decode_calls", "unpack_calls")
    for name, (repeats, eager_dec, skip_dec, guard_dec, depth) in CASES.items():
        case = d["cases"][name]
        req(case["case"] == name, "case label " + name)
        req(case["expected_depth"] == depth, "selected depth " + name)
        req(case["archive_bytes"] > 0, "physical size " + name)
        req(bool(re.fullmatch(r"[0-9a-f]{64}", case["archive_sha256"])),
            "physical digest shape "+name)
        req(set(case["raw"]) == set(ARMS), "arm coverage " + name)
        for arm, calls in zip(ARMS, (eager_dec, skip_dec, guard_dec)):
            rows = case["raw"][arm]
            req(len(rows) == repeats, "repeats " + name + "/" + arm)
            for row in rows:
                req(row["arm"] == arm, "row arm " + name)
                req(row["decode_calls"] == calls, "decode work "+name+"/"+arm)
                if name == "signed-malformed":
                    req((row["failure"] is None) == (arm == "skip"),
                        "malformed control " + arm)
                else:
                    req(row["failure"] is None, "unexpected exception "+name+"/"+arm)
                for k in number_fields:
                    v = row[k]
                    req(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0,
                        "nonfinite/negative "+name+"/"+arm+"/"+k)
            for k in number_fields:
                actual = statistics.median(r[k] for r in rows)
                claimed = case["median"][arm][k]
                req(math.isclose(actual, claimed, rel_tol=1e-10, abs_tol=1e-8),
                    "fabricated/incorrect median "+name+"/"+arm+"/"+k)
    inv = d["cases"]["orphan-4096"]["median"]
    val = d["cases"]["valid-512"]["median"]
    req(math.isclose(
        d["invalid_guarded_peak_ratio_to_eager"],
        inv["guarded"]["peak_traced_bytes"] / inv["eager"]["peak_traced_bytes"],
        rel_tol=1e-10), "invalid peak ratio")
    req(math.isclose(
        d["valid_guarded_cpu_ratio_to_eager"],
        val["guarded"]["cpu_ms"] / val["eager"]["cpu_ms"],
        rel_tol=1e-10), "valid CPU ratio")
    return checks


def attack_receipt(d, s):
    attacks = []
    def must_reject(name, mutate, source=False):
        draft = copy.deepcopy(s if source else d)
        mutate(draft)
        try:
            verify(d if source else draft, draft if source else s)
        except (AssertionError, KeyError, TypeError, ValueError):
            attacks.append(name)
        else:
            raise AssertionError("referee admitted forged receipt: "+name)

    must_reject("false-decode", lambda x: x["cases"]["orphan-4096"]["raw"]["eager"][0].__setitem__("decode_calls", 1))
    must_reject("fabricated-median", lambda x: x["cases"]["valid-512"]["median"]["guarded"].__setitem__("cpu_ms", 0.001))
    must_reject("erase-malformed-negative", lambda x: x["cases"]["signed-malformed"]["raw"]["eager"][0].__setitem__("failure", None))
    must_reject("false-release", lambda x: x.__setitem__("release_credit", 1))
    must_reject("false-source", lambda x: x["files"]["src/cmpct/reader.py"].__setitem__("sha256", "0"*64), source=True)
    try:
        json.loads('{"a":1,"a":2}', object_pairs_hook=lambda pairs: (
            (_ for _ in ()).throw(ValueError("duplicate"))
            if len(dict(pairs)) != len(pairs) else dict(pairs)))
    except ValueError:
        attacks.append("duplicate-key")
    else:
        raise AssertionError("duplicate JSON key not rejected")
    return attacks


def main():
    where = Path(os.environ.get("J24G12_ARTIFACTS", "j24g12-artifacts"))
    d = load_strict(where / "court.json")
    s = load_strict(where / "source.json")
    checks = verify(d, s)
    attacks = attack_receipt(d, s)
    out = {"source_head": s["head"], "original_raw_checks": checks,
           "forged_receipts_rejected": attacks,
           "guarded_invalid_peak_ratio": d["invalid_guarded_peak_ratio_to_eager"],
           "guarded_valid_cpu_ratio": d["valid_guarded_cpu_ratio_to_eager"],
           "naive_skip_changes_malformed_error": d["naive_skip_semantic_difference"],
           "independent_cmpct_reconstruction": False,
           "release_credit": 0}
    (where / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print("J24G12_AUDIT=" + json.dumps(out, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
