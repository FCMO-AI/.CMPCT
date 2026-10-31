#!/usr/bin/env python3
"""J24I72 detached no-CMPCT physical, raw-timing and forged-receipt referee.

The independent physical parser is inherited unmodified from #871; it imports
no CMPCT product modules and authenticates footer ancestry and CMA4 records.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

from j24i70_detached_referee import physical_check

LABELS = ("public", "factored", "owned", "delete_only")
SIZES = ("4096", "8192")
PARENT = "df2edd9d61a782616d7de1f3c054841e9ebb9eb2"
PREREG = "b130e333cb94b1c43f1dc38789397fa1ebf5af7f"
REFERENCE = "129edec976efe8bb604584517de39553487fec34"
READER = "29a8be64f3acfb027750351c6a567fd82cf7dc97"
METRICS = ("whole_process_wall_ns", "import_wall_ns",
           "constructor_wall_ns", "open_plus_proof_wall_ns",
           "import_cpu_ns", "constructor_cpu_ns")


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def near(a, b):
    return finite_number(a) and finite_number(b) and math.isclose(
        a, b, rel_tol=1e-10, abs_tol=1e-7)


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def validate(receipt, evidence_root):
    check(receipt["schema"] == "cmpct-j24i72-cold-owner-v1", "schema")
    check(receipt["status"] == "PASS" and receipt["product_credit"] == 0, "status/credit")
    source = receipt["source"]
    check(receipt["head"] == source["head"], "source-head")
    check(source["j24i72_parent_head"] == PARENT
          and source["j24i72_prereg_commit"] == PREREG, "source-prereg")
    check(source["reference_head"] == REFERENCE
          and source["reader_git_blob"] == READER, "Reader source")
    check(source["j24i72_instrument_blob"].isalnum()
          and len(source["j24i72_instrument_blob"]) == 40, "instrument blob")
    check(set(receipt["cases"]) == set(SIZES), "case-size-set")
    check(receipt["protocol"]["repeats"] == 8
          and set(receipt["protocol"]["labels"]) == set(LABELS), "protocol")
    checked = {}
    for size in SIZES:
        c = receipt["cases"][size]
        n = int(size)
        check(c["expected_members"] == n - 63 and
              c["member"] == "f00063.dat", "member identity")
        expected = hashlib.sha256(
            hashlib.sha256(f"j24g90-{n}-63".encode()).digest()
        ).hexdigest()
        check(expected == c["member_sha256"], "member independent SHA")
        physical = {}
        check(set(c["physical"]) == {"A", "B"}, "physical cases")
        for label in ("A", "B"):
            descriptor = c["physical"][label]
            check(descriptor["file"] == f"{n}-{label}.cmpct", "archive filename")
            archive_path = evidence_root / descriptor["file"]
            check(archive_path.is_file(), "missing physical archive")
            raw = archive_path.read_bytes()
            check(type(descriptor["size"]) is int and
                  descriptor["size"] == len(raw), "physical size")
            check(hash_bytes(raw) == descriptor["sha256"], "physical SHA")
            physical[label] = raw
        a, b = physical["A"], physical["B"]
        check(len(b) - len(a) == c["checkpoint_extra_bytes"]
              and c["checkpoint_extra_bytes"] > 0, "checkpoint byte cost")
        # Synthesized damaged-C is only a no-CMPCT independent negative control.
        # Full original A/B physical record/ancestry proof still uses actual files.
        corrupted_c = b[:-1] + bytes([b[-1] ^ 0x5A])
        physics = physical_check(a, b, corrupted_c)
        check(physics["a_footers"] == 64
              and physics["b_terminal_checkpoint"] is True, "physical ancestry")
        check(set(c["raw"]) == {"A", "B"}
              and set(c["import_only_raw"]) == set(LABELS), "raw shape")
        independently_measured = {}
        for archive in ("A", "B"):
            independently_measured[archive] = {}
            check(set(c["raw"][archive]) == set(LABELS), "label coverage")
            for reader in LABELS:
                raw = c["raw"][archive][reader]
                check(len(raw) == 8 and
                      sorted(x["iteration"] for x in raw) == list(range(8)),
                      "eight independent child-process samples")
                expected_depth = 63 if archive == "A" else 0
                required_route = {
                    "factored": "factored" if archive == "A" else "checkpoint",
                    "owned": "owned-fresh-decoder" if archive == "A" else "checkpoint",
                    "delete_only": "onepass-owned-delete" if archive == "A" else "checkpoint",
                }
                for row in raw:
                    check(row["archive"] == archive and row["label"] == reader
                          and row["mode"] == "open", "cell ownership")
                    check(row["depth"] == expected_depth
                          and row["index_sha256"] == c["index_sha256"]
                          and row["member_sha256"] == expected
                          and row["count"] == n - 63, "child semantic receipt")
                    if reader != "public":
                        check(row["route"] == required_route[reader], "Reader route")
                    for metric in METRICS:
                        check(finite_number(row[metric]), "raw numeric")
                    check(row["whole_process_wall_ns"] >= (
                        row["import_wall_ns"] + row["open_plus_proof_wall_ns"]),
                        "child work exceeds parent process wall")
                    before, after = row.get("import_hwm_kib"), row.get("operation_hwm_kib")
                    if type(before) is int and type(after) is int:
                        check(0 <= before <= after, "process HWM decreased")
                medians = {metric: statistics.median(x[metric] for x in raw)
                           for metric in METRICS}
                for metric in METRICS:
                    check(near(c["medians"][archive][reader][metric],
                               medians[metric]), "forged median")
                independently_measured[archive][reader] = medians
        for reader in LABELS:
            rows = c["import_only_raw"][reader]
            check(len(rows) == 4 and
                  sorted(x["iteration"] for x in rows) == list(range(4)),
                  "four import controls")
            for row in rows:
                check(row["label"] == reader and row["mode"] == "import",
                      "import control ownership")
                check(finite_number(row["import_wall_ns"])
                      and finite_number(row["whole_process_wall_ns"]), "import number")
                check(row["whole_process_wall_ns"] >= row["import_wall_ns"],
                      "import exceeds parent process duration")
        gross = lambda arch, reader: independently_measured[arch][reader]["whole_process_wall_ns"]
        check(gross("A", "public") > 0 and gross("B", "public") > 0, "denominator")
        ratio_pub = gross("A", "owned") / gross("A", "public")
        ratio_b = gross("A", "owned") / gross("B", "public")
        ratio_del = gross("A", "delete_only") / gross("A", "public")
        for name, actual in (
            ("owned_A_over_public_A_gross", ratio_pub),
            ("owned_A_over_public_B_gross", ratio_b),
            ("delete_A_over_public_A_gross", ratio_del),
        ):
            check(near(c["ratios"][name], actual), "forged ratio")
        h1 = ratio_pub <= .95 and (
            gross("A", "public") - gross("A", "owned") >= 3_000_000)
        h2 = ratio_b <= 1.2
        check(c["predictions"]["H1_owned_cold_material_benefit"] is h1
              and c["predictions"]["H2_owned_A_at_most_1p2_public_B"] is h2,
              "post-hoc hypothesis label")
        checked[size] = {
            "original_A_bytes": len(a), "checkpoint_B_bytes": len(b),
            "checkpoint_extra_bytes": len(b) - len(a),
            "physical": physics, "H1": h1, "H2": h2,
            "owned_over_public_A": ratio_pub, "owned_over_public_B": ratio_b,
            "samples": 64, "import_controls": 16,
        }
    check(receipt["prospective_two_size_evidence"] == {
        "H1_8192": checked["8192"]["H1"],
        "H2_8192": checked["8192"]["H2"]}, "aggregated decision")
    return checked


def adversarial(receipt, root):
    cases = []
    for name, edit in (
        ("source-prereg", lambda x: x["source"].__setitem__(
            "j24i72_prereg_commit", "0" * 40)),
        ("median-forgery", lambda x: x["cases"]["4096"]["medians"]["A"]["public"].__setitem__(
            "whole_process_wall_ns", 12345678)),
        ("physical-sha-forgery", lambda x: x["cases"]["8192"]["physical"]["A"].__setitem__(
            "sha256", "f" * 64)),
        ("prediction-relabel", lambda x: x["cases"]["8192"]["predictions"].__setitem__(
            "H1_owned_cold_material_benefit", not x["cases"]["8192"]["predictions"]["H1_owned_cold_material_benefit"])),
        ("raw-process-time", lambda x: x["cases"]["4096"]["raw"]["A"]["owned"][0].__setitem__(
            "whole_process_wall_ns", -99)),
    ):
        candidate = copy.deepcopy(receipt)
        edit(candidate)
        try:
            validate(candidate, root)
        except (AssertionError, ValueError, KeyError, TypeError):
            cases.append(name)
        else:
            raise AssertionError("forged receipt accepted: " + name)
    return cases


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: j24i72_detached_referee.py EVIDENCE_DIRECTORY")
    evidence_root = Path(sys.argv[1])
    receipt = json.loads((evidence_root / "receipt.json").read_text())
    audit = validate(receipt, evidence_root)
    forged = adversarial(receipt, evidence_root)
    outcome = {
        "schema": "cmpct-j24i72-detached-referee-v1",
        "status": "PASS", "head": receipt["head"],
        "product_credit": 0, "host": receipt["host"],
        "cases": audit, "adversarial_refusals": forged,
        "imported_cmpct": any(k == "cmpct" or k.startswith("cmpct.")
                              for k in sys.modules),
    }
    check(not outcome["imported_cmpct"], "oracle secretly imported CMPCT")
    (evidence_root / "detached-referee.json").write_text(
        json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print("J24I72_DETACHED", json.dumps({
        "status": "PASS", "cases": {n: {k: v for k, v in c.items() if k != "physical"}
                                 for n, c in audit.items()},
        "adversarial_refusals": forged}, sort_keys=True))


if __name__ == "__main__":
    main()
