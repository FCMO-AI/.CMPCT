#!/usr/bin/env python3
"""Independent physical/source/receipt referee for J24B08 (no court imports)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

from cmpct.reader import CMPCT

RELEASE = "80c358f8824ec1b20d349c92ed94c898090969b0"
PARENT = "adcf38cb5be022567c1faf6538aefeef2f6b72de"
RELEASE_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"
CAND_BLOB = "20f6e257a07a61a4c1aebe23ae23e4109d6c41c8"


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def hash_tree_formula(n):
    h = hashlib.sha256()
    for index in range(n):
        filename = f"{index:06d}.bin".encode()
        content = hashlib.sha256(f"J24B08:{n}:{index:06d}".encode()).digest() * 3
        h.update(len(filename).to_bytes(4, "big") + filename)
        h.update(len(content).to_bytes(8, "big"))
        h.update(hashlib.sha256(content).digest())
    return h.hexdigest()


def audit(receipt, folder, check_physical=True):
    assert receipt["schema"] == "cmpct-j24b08-economics-v1"
    assert receipt["classification"] == "installed_reader_research_not_release_gate"
    ident = receipt["identity"]
    assert ident["head"] == git("rev-parse", "HEAD")
    assert git("merge-base", PARENT, "HEAD") == PARENT
    assert ident["candidate_parent"] == PARENT
    assert ident["release"] == RELEASE
    assert ident["release_reader_blob"] == RELEASE_BLOB
    assert ident["candidate_reader_blob"] == CAND_BLOB
    assert git("rev-parse", f"{RELEASE}:src/cmpct/reader.py") == RELEASE_BLOB
    assert git("rev-parse", "HEAD:src/cmpct/reader.py") == CAND_BLOB
    assert ident["installed_reader_sha256_normalized"] == ident["git_reader_sha256"]
    assert len(receipt["geometries"]) == 2
    assert {g["files"] for g in receipt["geometries"]} == {128, 4096}
    expected_hash = {}
    for geometry in receipt["geometries"]:
        n = geometry["files"]
        assert geometry["payload_total"] == n * 96
        assert geometry["archive_path"] == f"source-{n}.cmpct"
        expected = hash_tree_formula(n)
        expected_hash[n] = expected
        assert geometry["tree_sha256"] == expected
        archive = folder / geometry["archive_path"]
        assert archive.exists() and archive.stat().st_size == geometry["archive_bytes"]
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == geometry["archive_sha256"]
        if check_physical:
            with CMPCT(archive) as reader:
                assert reader.verify() == n
                assert len(reader.files) == n
                # Independently check each physical logical file against its
                # synthetic source equation. This does not trust receipt output.
                for i in range(n):
                    target = hashlib.sha256(
                        f"J24B08:{n}:{i:06d}".encode()
                    ).digest() * 3
                    assert reader.read(f"{i:06d}.bin") == target
    assert len(receipt["cells"]) == 4
    assert {(c["files"], c["budget_mode"]) for c in receipt["cells"]} == {
        (n, b) for n in (128, 4096) for b in ("none", "exact")
    }
    for cell in receipt["cells"]:
        n = cell["files"]
        assert cell["budget"] == (None if cell["budget_mode"] == "none" else n * 96)
        raw = cell["raw"]
        assert len(raw) == 16
        for turn in range(4):
            subset = [r for r in raw if r["repeat"] == turn]
            assert len(subset) == 4
            ordered = sorted(subset, key=lambda r: r["step"])
            assert [r["step"] for r in ordered] == [0, 1, 2, 3]
            expected_order = (["base","candidate","candidate","base"]
                              if turn % 2 == 0
                              else ["candidate","base","base","candidate"])
            assert [r["arm"] for r in ordered] == expected_order
        for row in raw:
            assert row["arm"] in ("base", "candidate")
            assert row["budget_mode"] == cell["budget_mode"]
            assert row["output_files"] == n
            assert row["output_sha256"] == expected_hash[n]
            for metric in ("open_wall_ns", "open_cpu_ns",
                           "extract_wall_ns", "extract_cpu_ns"):
                assert type(row[metric]) is int and row[metric] > 0
        for arm in ("base", "candidate"):
            sub = [r for r in raw if r["arm"] == arm]
            assert len(sub) == 8
            for field in ("open_wall_ns", "open_cpu_ns",
                          "extract_wall_ns", "extract_cpu_ns"):
                computed = statistics.median(r[field] for r in sub)
                assert computed == cell["median"][arm][field]
        b = cell["median"]["base"]["extract_wall_ns"]
        c = cell["median"]["candidate"]["extract_wall_ns"]
        assert abs(cell["candidate_over_base_wall_ratio"] - c/b) < 1e-10
        assert abs(cell["candidate_minus_base_wall_ms"] - (c-b)/1e6) < 1e-10
        assert cell["confirmed_release_gate_signal_on_this_experimental_cell"] is (
            c/b > 1.05 and (c-b)/1e6 > 3
        )
    micro = receipt["micro"]
    assert micro["class"] == "source_equivalent_component_only_not_product"
    assert micro["rows"] == 100_000
    for arm in ("base", "candidate"):
        raw = micro["raw"][arm]
        assert len(raw) == 16
        assert all(type(x["wall_ns"]) is int and x["wall_ns"] > 0
                   and type(x["cpu_ns"]) is int and x["cpu_ns"] > 0
                   for x in raw)
        assert micro["median_wall_ns"][arm] == statistics.median(
            x["wall_ns"] for x in raw
        )
    assert "#693" in receipt["important_negative"]
    return True


def challenge(original, folder):
    alterations = [
        lambda r: r["identity"].__setitem__("candidate_reader_blob", "0"*40),
        lambda r: r["geometries"][0].__setitem__("archive_sha256", "0"*64),
        lambda r: r["cells"][0]["median"]["base"].__setitem__(
            "extract_wall_ns", r["cells"][0]["median"]["base"]["extract_wall_ns"]+1
        ),
        lambda r: r["cells"][0]["raw"][0].__setitem__("output_sha256", "0"*64),
        lambda r: r["cells"][0].__setitem__(
            "candidate_over_base_wall_ratio",
            r["cells"][0]["candidate_over_base_wall_ratio"]*2
        ),
        lambda r: r["cells"][0].__setitem__(
            "confirmed_release_gate_signal_on_this_experimental_cell",
            not r["cells"][0]["confirmed_release_gate_signal_on_this_experimental_cell"]
        ),
    ]
    rejected = 0
    for alteration in alterations:
        mutant = copy.deepcopy(original)
        alteration(mutant)
        try:
            audit(mutant, folder, check_physical=False)
        except (AssertionError, KeyError, ValueError, TypeError):
            rejected += 1
    assert rejected == len(alterations), (rejected, len(alterations))
    return rejected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="j24b08-evidence")
    args = parser.parse_args()
    folder = Path(args.out)
    original = json.loads((folder/"receipt.json").read_text(encoding="utf-8"))
    audit(original, folder)
    rejects = challenge(original, folder)
    result = {"source_sha": original["identity"]["head"],
              "audited_cells": len(original["cells"]),
              "verified_physical_files": sum(g["files"] for g in original["geometries"]),
              "forged_receipts_rejected": rejects,
              "status": "PASS",
              "scope": "science_only_not_release_or_security_completion"}
    (folder/"independent-referee.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8"
    )
    print("J24B08_REFEREE=" + json.dumps(result, sort_keys=True))
