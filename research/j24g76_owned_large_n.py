#!/usr/bin/env python3
"""J24G76 held-out physical large-N owned-decoder replay court; research only.

Source-exact J24G74 inheritance; no shipping Reader, Writer or format edits.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import sys
import tempfile
import time
import tracemalloc

import msgpack

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct import transactions as tx
from cmpct.validation import preflight_archive
from j24g73_reader_open import FactoredCMPCT, sha256_file
from j24g74_owned_decoder_court import (
    OwnedCMPCT, source_attest, timed_open, run_rss, owned_factored_fresh,
)
from j24g64_mixed_fsmeta_oracle import fingerprint
from j24g73_independent_wire import wire, reconstruct

PREREG = "0de1e97d7a6482c1dd08c643174385e78a5602f6"
CASES = ((8192, "middle"), (32768, "tail"))
LABELS = ("reference", "factored", "owned")
PERMS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")
DEPTH = 63


def source_contract():
    """Inherit exact source attestations and require immutable prereg ancestry."""
    import subprocess
    root = Path(__file__).resolve().parents[1]
    inherited = source_attest()
    head = inherited["head"]
    subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, head],
                   cwd=root, check=True)
    return {"head": head, "prereg": PREREG,
            "inherited": inherited,
            "experiment_blob": subprocess.check_output(
                ["git", "rev-parse", "HEAD:research/j24g76_owned_large_n.py"],
                cwd=root, text=True).strip()}


def chosen_indices(n, position):
    if position == "middle":
        return range(n // 2 - 31, n // 2 + 32)
    if position == "tail":
        return range(n - DEPTH, n)
    raise ValueError(position)


def create_physical(root, n, position):
    src = root / f"input-{n}-{position}"
    src.mkdir()
    create_start = time.perf_counter_ns()
    for i in range(n):
        (src / f"f{i:05d}.dat").write_bytes(
            hashlib.sha256(f"j24g76-{n}-{i}".encode()).digest())
    archive = root / f"large-{n}-{position}.cmpct"
    Builder(src, workers=1, reproducible=False).build(archive)
    builder_ns = time.perf_counter_ns() - create_start
    deletion_start = time.perf_counter_ns()
    deleted = []
    for i in chosen_indices(n, position):
        name = f"f{i:05d}.dat"
        tx.append_delete(archive, name)
        deleted.append(name)
    append_ns = time.perf_counter_ns() - deletion_start
    return archive, set(deleted), {"builder_including_tree_ns": builder_ns,
                                  "append_63_wall_ns": append_ns}


def physical_oracle(path, n, deleted):
    raw = path.read_bytes()
    original_sha = hashlib.sha256(raw).hexdigest()
    entries = wire(raw)  # no-CMPCT footer+SHA+Zstd+MessagePack parser
    reconstructed, counts, initial = reconstruct(entries)
    assert initial == n
    assert counts == {"del": DEPTH, "ren": 0, "put": 0}
    assert len(reconstructed["files"]) == n - DEPTH
    assert all(row[0] not in deleted for row in reconstructed["files"])
    index_digest = fingerprint(reconstructed)
    # Verify that our physical parser actually rejects a SHA manipulation.
    tamper = bytearray(raw)
    footer_position = entries[0][2]
    tamper[footer_position + 63] ^= 0xA5
    try:
        wire(bytes(tamper))
    except (AssertionError, ValueError, RuntimeError):
        refused = True
    else:
        refused = False
    assert refused, "no-CMPCT auditor failed to reject footer mutation"
    assert sha256_file(path) == original_sha
    return reconstructed, {
        "archive_bytes": len(raw), "archive_sha256": original_sha,
        "wire_index_sha256": index_digest, "footers": len(entries),
        "initial_members": initial, "final_members": len(reconstructed["files"]),
        "ops": counts, "tampered_footer_rejected": refused,
    }


def byte_identity(path, n, deleted, independent_index):
    original_sha = sha256_file(path)
    members = {f"f{i:05d}.dat" for i in range(n)} - deleted
    results = {}
    with CMPCT(path) as a, FactoredCMPCT(path) as b, OwnedCMPCT(path) as c:
        assert a.delta_depth == b.delta_depth == c.delta_depth == DEPTH
        assert b._research_route == "factored"
        assert c._research_route == "owned-fresh-decoder"
        assert a.latest_footer_pos == b.latest_footer_pos == c.latest_footer_pos
        assert a.index == b.index == c.index == independent_index
        expected_wire = msgpack.packb(a.index, use_bin_type=True)
        assert msgpack.packb(b.index, use_bin_type=True) == expected_wire
        assert msgpack.packb(c.index, use_bin_type=True) == expected_wire
        assert set(a.by) == set(b.by) == set(c.by) == members
        assert a.verify() == b.verify() == c.verify() == len(members)
        for name in sorted(members):
            i = int(name[1:6])
            expected = hashlib.sha256(f"j24g76-{n}-{i}".encode()).digest()
            assert a.read(name) == b.read(name) == c.read(name) == expected, name
        # Read-side public aliases remain mutable after construction; DO NOT
        # reinterpret this private ownership experiment as a public API guarantee.
        exposed = c.index["files"][0]
        original_name = exposed[0]
        exposed[0] = "__j24g76_public_mutability_probe__"
        assert c.files[0][0] == "__j24g76_public_mutability_probe__"
        exposed[0] = original_name
        results["public_reader_descriptors_mutable"] = True
    pf = preflight_archive(path)
    assert pf["files"] == len(members) and pf["delta_depth"] == DEPTH
    results["preflight_files"] = pf["files"]
    assert sha256_file(path) == original_sha
    return results


def corrupt_tail_recovery(path):
    payload = path.read_bytes()
    outcomes = {}
    for kind, modified in (
        ("digest", payload[:-1] + bytes([payload[-1] ^ 0xA5])),
        ("truncated", payload[:-17]),
    ):
        with tempfile.TemporaryDirectory(prefix="j24g76-recovery-") as temp:
            candidate = Path(temp) / (kind + ".cmpct")
            candidate.write_bytes(modified)
            with CMPCT(candidate) as a, FactoredCMPCT(candidate) as b, OwnedCMPCT(candidate) as c:
                assert a.delta_depth == b.delta_depth == c.delta_depth == DEPTH - 1
                assert a.index == b.index == c.index
                assert fingerprint(a.index) == fingerprint(c.index)
                outcomes[kind] = {"recovered_depth": c.delta_depth,
                                  "index_sha256": fingerprint(c.index)}
    return outcomes


def adversarial_alias_negative():
    base = {"files": [["a", 1], ["b", 2]], "blobs": []}
    delta = [{"blobs": [], "ops": [["ren", "a", "z"]]}]
    previous = copy.deepcopy(base)
    output, route = owned_factored_fresh(base, delta)
    assert route == "owned-fresh-decoder"
    assert base is output and base != previous
    return {"caller_alias_mutation_visible": True,
            "route": route, "shipping_recommendation": "PRIVATE_DECODER_ONLY"}


def measured_open(path):
    for label in LABELS:
        timed_open(path, label)
    samples = []
    for block in range(2):
        for order in PERMS:
            for letter in order:
                label = LABELS["ABC".index(letter)]
                samples.append({"block": block, "order": order, "variant": label,
                                **timed_open(path, label)})
    medians = {
        key: {label: statistics.median(row[key] for row in samples if row["variant"] == label)
              for label in LABELS}
        for key in ("wall_ns", "cpu_ns")
    }
    traced = {}
    for label in LABELS:
        peaks = []
        for _ in range(3):
            tracemalloc.start()
            tracemalloc.reset_peak()
            timed_open(path, label)
            peaks.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        traced[label] = peaks
    assert len(samples) == 36
    assert {label: sum(x["variant"] == label for x in samples) for label in LABELS} == {
        label: 12 for label in LABELS}
    return {"raw": samples, "median": medians, "traced_peak_repeats": traced,
            "owned_vs_factored_wall": medians["wall_ns"]["factored"] /
                                      medians["wall_ns"]["owned"],
            "owned_minus_factored_traced_peak": statistics.median(traced["owned"]) -
                                                statistics.median(traced["factored"])}


def main():
    evidence_dir = Path(os.environ.get("J24G76_EVIDENCE_DIR", "evidence"))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "cmpct-j24g76-owned-large-n-v1",
               "source": source_contract(), "host": platform.platform(),
               "platform": sys.platform, "status": "RUNNING",
               "product_credit": 0, "cases": {},
               "alias_negative": adversarial_alias_negative()}
    try:
        with tempfile.TemporaryDirectory(prefix="j24g76-court-") as temp:
            root = Path(temp)
            for n, position in CASES:
                identifier = f"{n}-{position}"
                archive, deleted, build_cost = create_physical(root, n, position)
                independent, physical = physical_oracle(archive, n, deleted)
                fidelity = byte_identity(archive, n, deleted, independent)
                recovery = corrupt_tail_recovery(archive)
                benchmark = measured_open(archive)
                rss = run_rss(archive)
                dest = evidence_dir / (identifier + "-physical.cmpct")
                shutil.copyfile(archive, dest)
                assert sha256_file(dest) == physical["archive_sha256"]
                receipt["cases"][identifier] = {
                    "physical": physical, "fidelity": fidelity,
                    "recovery": recovery, "benchmark": benchmark,
                    "rss_fresh_process": rss, "build_cost": build_cost}
        receipt["local_h1"] = {
            name: (case["benchmark"]["owned_vs_factored_wall"] >= 1.20 and
                   case["benchmark"]["owned_minus_factored_traced_peak"] <= 0)
            for name, case in receipt["cases"].items()}
        receipt["status"] = "PASS"
    except BaseException as exc:
        receipt["status"] = "FAIL"
        receipt["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        result = evidence_dir / "j24g76-result.json"
        result.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print("J24G76_RECEIPT", result, "status", receipt["status"])
        print("J24G76_H1", receipt.get("local_h1"))


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("Run without CLI arguments")
    main()
