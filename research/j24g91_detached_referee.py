#!/usr/bin/env python3
"""Detached J24G91 physical/cost audit; deliberately never imports cmpct."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import statistics
import sys

import msgpack
import zstandard

from j24g90_detached_referee import FTR, h, load_footer, chain, rebuild


def audit(n, folder, reported):
    raw = {label: (folder / f"{n}-{label}.cmpct").read_bytes() for label in "ABC"}
    physical = reported["physics"]
    for label in "ABC":
        assert len(raw[label]) == physical[label]["size"]
        assert h(raw[label]) == physical[label]["sha256"]
    assert raw["B"].startswith(raw["A"])
    assert raw["B"][:-1] == raw["C"][:-1] and raw["B"][-1] != raw["C"][-1]
    assert len(raw["B"]) == len(raw["C"]) > len(raw["A"])
    last_good = len(raw["A"]) - FTR.size
    original_chain = chain(raw["A"], last_good)
    assert len(original_chain) == 64
    rebuilt, deleted = rebuild(original_chain)
    checkpoint = load_footer(raw["B"], len(raw["B"]) - FTR.size)
    assert checkpoint["kind"] == 0 and checkpoint["prev"] == last_good
    assert checkpoint["payload"] == rebuilt
    assert len(chain(raw["B"], len(raw["B"]) - FTR.size)) == 65
    try:
        load_footer(raw["C"], len(raw["C"]) - FTR.size)
    except (AssertionError, ValueError, zstandard.ZstdError):
        rejected = True
    else:
        rejected = False
    assert rejected and raw["C"][:len(raw["A"])] == raw["A"]
    expected_sha = h(msgpack.packb(rebuilt, use_bin_type=True))
    assert len(rebuilt["files"]) == n - 63
    all_receipts = reported["semantic_proof"]["comparison"]
    assert len(all_receipts) == 6
    for variant, info in all_receipts.items():
        assert info["index_sha256"] == expected_sha
        assert info["depth"] == (0 if variant.endswith("B") else 63)
        assert info["verified"] == n - 63
        if variant in ("owned_A", "owned_C"):
            assert info["research_route"] == "onepass-owned-delete"
        elif variant == "owned_B":
            assert info["research_route"] == "checkpoint"
    assert reported["semantic_proof"]["actual_fallback_negative"]["route"] == "inherited-fallback"
    assert reported["checkpoint_extra_bytes"] == len(raw["B"]) - len(raw["A"])
    assert reported["checkpoint_overhead_ratio"] == (
        len(raw["B"]) - len(raw["A"])) / len(raw["A"])
    samples = reported["timing"]["raw"]
    labels = ("reference_A", "owned_A", "reference_B",
              "owned_B", "reference_C", "owned_C")
    assert len(samples) == 72
    summary = {}
    for key in ("wall_ns", "cpu_ns"):
        summary[key] = {}
        for variant in labels:
            sub = [s[key] for s in samples if s["variant"] == variant]
            assert len(sub) == 12 and all(v >= 0 for v in sub)
            median = statistics.median(sub)
            assert abs(median - reported["timing"]["medians"][key][variant]) < 1e-5
            summary[key][variant] = median
    wall, cpu = summary["wall_ns"], summary["cpu_ns"]
    relative = wall["reference_A"] / wall["owned_A"]
    checkpoint = wall["owned_A"] / wall["reference_B"]
    assert abs(relative - reported["timing"]["public_A_over_owned_A_wall"]) < 1e-9
    assert abs(checkpoint - reported["timing"]["checkpoint_B_over_owned_A_wall"]) < 1e-9
    assert abs(cpu["owned_A"] / cpu["reference_B"] -
               reported["timing"]["checkpoint_B_over_owned_A_cpu"]) < 1e-9
    # Attest that this detached referee refuses a directly altered physical footer,
    # without relying on the CMPCT decoder or on the reported mutation verdict.
    tamper = bytearray(raw["A"])
    tamper[last_good + FTR.size - 1] ^= 0xA5
    try:
        load_footer(bytes(tamper), last_good)
    except (AssertionError, ValueError, zstandard.ZstdError):
        mutation_rejected = True
    else:
        mutation_rejected = False
    assert mutation_rejected
    return {"archive_sha256": {k: h(v) for k, v in raw.items()},
            "footers_original": 64, "footers_checkpoint": 65,
            "deletes": len(deleted), "index_sha256": expected_sha,
            "physical_bytes": {k: len(v) for k, v in raw.items()},
            "checkpoint_extra_bytes": len(raw["B"]) - len(raw["A"]),
            "corrupt_tail_rejected": True, "hostile_referee_mutation_rejected": True,
            "median_ns": summary, "speedup_public_to_owned": relative,
            "checkpoint_to_owned_ratio": checkpoint}


def main():
    folder = Path(sys.argv[1])
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["status"] == "PASS" and receipt["product_credit"] == 0
    assert receipt["source"]["reader_git_blob"] == "e716233403dabd0966863c45635e18fa5ac6afb8"
    cases = {str(n): audit(n, folder, receipt["cases"][str(n)]) for n in (4096, 8192)}
    h_replay = all(case["speedup_public_to_owned"] >= 2 for case in cases.values())
    h_marginal = all(case["checkpoint_to_owned_ratio"] <= 1.50
                     for case in cases.values())
    h_checkpoint = all(case["checkpoint_to_owned_ratio"] >= 2
                       for case in cases.values())
    assert receipt["H_integrity"]
    assert receipt["H_replay"] == h_replay
    assert receipt["H_checkpoint_marginality"] == h_marginal
    assert receipt["H_checkpoint_survives"] == h_checkpoint
    result = {"schema": "cmpct-j24g91-independent-referee-v1", "status": "PASS",
              "source_head": receipt["source"]["head"], "cases": cases,
              "H_replay": h_replay,
              "H_checkpoint_marginality": h_marginal,
              "H_checkpoint_survives": h_checkpoint,
              "product_credit": 0}
    (folder / "detached-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24G91_DETACHED", json.dumps({
        "status": result["status"], "H_replay": h_replay,
        "H_checkpoint_marginality": h_marginal,
        "H_checkpoint_survives": h_checkpoint,
        "ratios": {n: c["checkpoint_to_owned_ratio"] for n, c in cases.items()},
    }, sort_keys=True))


if __name__ == "__main__":
    assert len(sys.argv) == 2, "usage: referee.py <evidence-dir>"
    main()
