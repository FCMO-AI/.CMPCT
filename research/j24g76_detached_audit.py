#!/usr/bin/env python3
"""Detached no-CMPCT J24G76 footer and raw-receipt referee.

No import of cmpct Reader/Builder/transactions or J24G76 experiment module.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import msgpack

from j24g73_independent_wire import wire, reconstruct

CASES = {"8192-middle": 8192, "32768-tail": 32768}
LABELS = ("reference", "factored", "owned")
PERMS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")


def require(ok, label):
    if not ok:
        raise AssertionError(label)


def audit_obj(data, evidence_dir):
    require(data["schema"] == "cmpct-j24g76-owned-large-n-v1", "schema")
    require(data["status"] == "PASS" and data["product_credit"] == 0, "status")
    require(data["source"]["prereg"] == "0de1e97d7a6482c1dd08c643174385e78a5602f6", "prereg")
    require(data["source"]["head"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip(), "exact-head")
    require(data["alias_negative"]["caller_alias_mutation_visible"] is True, "alias-negative")
    require(set(data["cases"]) == set(CASES), "cases")
    require(set(data["local_h1"]) == set(CASES), "H1-cases")
    outcome = {}
    for name, n in CASES.items():
        path = Path(evidence_dir) / (name + "-physical.cmpct")
        raw = path.read_bytes()
        p = data["cases"][name]["physical"]
        require(len(raw) == p["archive_bytes"], "stored-bytes:" + name)
        require(hashlib.sha256(raw).hexdigest() == p["archive_sha256"], "physical-sha:" + name)
        entries = wire(raw)
        index, ops, start = reconstruct(entries)
        require(start == n and len(index["files"]) == n - 63, "member-count:" + name)
        require(ops == p["ops"] == {"del": 63, "ren": 0, "put": 0}, "op-count:" + name)
        removed = [d["ops"][0][1] for _, d, _, _ in reversed(entries[:-1])]
        expected = [f"f{i:05d}.dat" for i in (
            range(n // 2 - 31, n // 2 + 32) if name.endswith("middle")
            else range(n - 63, n))]
        require(removed == expected, "exact-deletion-positions:" + name)
        for row in index["files"]:
            require(row[0] not in removed, "deleted-still-present:" + name)
        index_sha = hashlib.sha256(msgpack.packb(index, use_bin_type=True)).hexdigest()
        require(index_sha == p["wire_index_sha256"], "physical-index-sha:" + name)
        # A second independent SHA mutation must not pass the wire parser.
        corrupt = bytearray(raw)
        corrupt[entries[0][2] + 63] ^= 0x5A
        try:
            wire(bytes(corrupt))
        except (AssertionError, ValueError, RuntimeError):
            pass
        else:
            raise AssertionError("wire-mutant-undetected:" + name)
        b = data["cases"][name]["benchmark"]
        samples = b["raw"]
        require(len(samples) == 36, "sample-count:" + name)
        for block in (0, 1):
            for order in PERMS:
                group = [s for s in samples if s["block"] == block and s["order"] == order]
                require(len(group) == 3, "group-count:" + name)
                require([s["variant"] for s in group] ==
                        [LABELS["ABC".index(letter)] for letter in order],
                        "not-balanced-permutation:" + name)
        for metric in ("wall_ns", "cpu_ns"):
            for label in LABELS:
                rows = [r[metric] for r in samples if r["variant"] == label]
                require(len(rows) == 12 and all(isinstance(v, int) and v >= 0 for v in rows),
                        "raw-units:" + name)
                require(statistics.median(rows) == b["median"][metric][label],
                        "median-mismatch:" + name)
        for label in LABELS:
            require(len(b["traced_peak_repeats"][label]) == 3, "peak-count:" + name)
            require(len(data["cases"][name]["rss_fresh_process"][label]) == 3,
                    "rss-count:" + name)
        require(abs(b["owned_vs_factored_wall"] -
                b["median"]["wall_ns"]["factored"] / b["median"]["wall_ns"]["owned"]) < 1e-9,
                "speedup-ratio:" + name)
        require(b["owned_minus_factored_traced_peak"] ==
                statistics.median(b["traced_peak_repeats"]["owned"]) -
                statistics.median(b["traced_peak_repeats"]["factored"]),
                "allocation-delta:" + name)
        require(data["local_h1"][name] ==
                (b["owned_vs_factored_wall"] >= 1.20 and
                 b["owned_minus_factored_traced_peak"] <= 0), "H1-relabel:" + name)
        require(data["cases"][name]["fidelity"]["preflight_files"] == n - 63,
                "preflight:" + name)
        require(data["cases"][name]["recovery"]["digest"]["recovered_depth"] == 62,
                "recovery-digest:" + name)
        require(data["cases"][name]["recovery"]["truncated"]["recovered_depth"] == 62,
                "recovery-truncation:" + name)
        outcome[name] = {"archive_sha256": p["archive_sha256"],
                         "wire_index_sha256": index_sha,
                         "initial_members": n, "live_members": n - 63,
                         "footers": len(entries),
                         "independent_tamper_refused": True,
                         "owned_vs_factored_wall": b["owned_vs_factored_wall"]}
    return outcome


def main():
    require(len(sys.argv) == 3, "usage result.json evidence-dir")
    path, root = Path(sys.argv[1]), Path(sys.argv[2])
    original = json.loads(path.read_text())
    result = audit_obj(original, root)
    # Mutation controls: the same referee must fail for fabricated measurements.
    falsifiers = [
        lambda d: d["cases"]["8192-middle"]["physical"].update(
            archive_sha256="0" * 64),
        lambda d: d["cases"]["32768-tail"]["benchmark"]["median"]["wall_ns"].update(
            owned=1),
        lambda d: d["cases"]["8192-middle"]["benchmark"]["raw"].pop(),
        lambda d: d["cases"]["8192-middle"]["physical"].update(
            ops={"del": 62, "ren": 1, "put": 0}),
        lambda d: d["source"].update(head="0" * 40),
        lambda d: d["cases"]["32768-tail"]["benchmark"]["raw"][0].update(
            variant="owned"),
    ]
    caught = 0
    for mutate in falsifiers:
        altered = copy.deepcopy(original)
        mutate(altered)
        try:
            audit_obj(altered, root)
        except (AssertionError, KeyError, IndexError, ZeroDivisionError):
            caught += 1
        else:
            raise AssertionError("detached auditor accepted fabricated receipt")
    require(caught == len(falsifiers), "tamper count")
    result_path = root / "j24g76-detached-audit.json"
    result_path.write_text(json.dumps({
        "status": "PASS", "head": original["source"]["head"],
        "physical_cases": result, "fabricated_receipts_rejected": caught,
        "cmpct_source_imported": False,
    }, sort_keys=True, indent=2) + "\n")
    print("J24G76_DETACHED_PASS", result_path, "tamper", caught)


if __name__ == "__main__":
    main()
