#!/usr/bin/env python3
"""J24G18: authentic signed footer recovery versus J24G17 native token preflight.

Scientific composition only. Source Reader is unmodified. The only experimental
change is a subclass's after-SHA, before-MessagePack token preflight.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import types

import msgpack
from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, sha
from cmpct.reader import CMPCT
from cmpct.transactions import append_rename
from j24g17_native_predecode_court import tokens, TooManyNodes

BODY = b"CMPCT-J24G18-signed-Reader-fallback\0" * 41
CAP = 65536
EXPECTED_READER_BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PARENT = "06617f194c45ebb38dda0592ff5e5196e204af80"
RELEASE_SHA = "80c358f8824ec1b20d349c92ed94c898090969b0"
RELEASE_READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"

def digest(data):
    return hashlib.sha256(data).hexdigest()

class GatedReader(CMPCT):
    def _decode_generation_payload(self, footer_pos):
        g = super()._decode_generation_payload(footer_pos)
        if g is not None:
            tokens(g[1], CAP)
        return g

class CatchAndFallbackReader(CMPCT):
    def _decode_generation_payload(self, footer_pos):
        g = super()._decode_generation_payload(footer_pos)
        if g is not None:
            try:
                tokens(g[1], CAP)
            except TooManyNodes:
                return None  # optional hypothetical policy: silently skip a signed footer
        return g

# This independent published-source control is **not** a rewrite of release semantics.
# It executes the actual historical Reader blob against the same installed
# revision-24 codec namespace, exactly as prior J24G06 comparative research.
def exact_released_reader():
    path = RELEASE_SHA + ":src/cmpct/reader.py"
    actual = subprocess.check_output(["git", "rev-parse", path], text=True).strip()
    assert actual == RELEASE_READER_BLOB, actual
    raw = subprocess.check_output(["git", "show", path])
    module = types.ModuleType("cmpct._j24g18_exact_released_reader")
    module.__package__ = "cmpct"
    exec(compile(raw, "<released Git blob " + actual + ">", "exec"), module.__dict__)
    return module.CMPCT

READERS = {"released": None, "direct": CMPCT, "gated": GatedReader,
           "catch": CatchAndFallbackReader}

def worker(path, arm):
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    result = {"status": "error", "exception": None}
    try:
        with (exact_released_reader() if arm == "released" else READERS[arm])(Path(path)) as archive:
            result = {
                "status": "opened",
                "selected_footer": archive.latest_footer_pos,
                "depth": archive.delta_depth,
                "paths": sorted(archive.by),
                "members": {},
            }
            for name in ("owner.bin", "renamed.bin"):
                if name in archive.by:
                    b = archive.read(name)
                    assert b == BODY
                    assert archive.read_range(name, 1, 17) == BODY[1:18]
                    result["members"][name] = {"sha256": digest(b), "bytes": len(b)}
            archive.verify()
    except Exception as e:
        result = {"status": "error", "exception": type(e).__name__,
                  "message": str(e)[:220]}
    result["wall_ns"] = time.perf_counter_ns() - start_wall
    result["cpu_ns"] = time.process_time_ns() - start_cpu
    result["rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(result, sort_keys=True))
    return 0

def append_delta(source, target, payload, prev):
    b = source.read_bytes()
    footer_pos = len(b) + len(payload)
    f = FTR.pack(FMAGIC, 1, 0, 0, 0, len(payload), len(payload), prev, sha(payload))
    target.write_bytes(b + payload + f)
    return {"footer": footer_pos, "payload_bytes": len(payload),
            "payload_sha256": digest(payload), "prev": prev,
            "footer_sha256": digest(f)}

def calls(case_path, arm, repeats):
    result = []
    for i in range(repeats):
        p = subprocess.run(
            [sys.executable, __file__, "--worker", str(case_path), arm],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        assert p.returncode == 0, (p.returncode, p.stderr[-1500:])
        r = json.loads(p.stdout.strip().splitlines()[-1])
        r["worker_repeat"] = i
        result.append(r)
    return result

def main(out, repeats):
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", PARENT, "HEAD"], check=True)
    assert subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
                                   text=True).strip() == EXPECTED_READER_BLOB
    assert Path(__file__).read_bytes() == subprocess.check_output(
        ["git", "show", "HEAD:research/j24g18_native_reader_court.py"])
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g18-") as d:
        root = Path(d)
        tree = root / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(BODY)
        base_path = root / "base.cmpct"
        Builder(tree).build(base_path)
        with CMPCT(base_path) as original:
            checkpoint = original.latest_footer_pos
            assert checkpoint > 0 and original.read("owner.bin") == BODY

        # Real Writer-control rename, unaffected by the preflight.
        writer = root / "writer-rename.cmpct"
        writer.write_bytes(base_path.read_bytes())
        append_rename(writer, "owner.bin", "renamed.bin")

        big = [None] * 70000
        orphan_payload = msgpack.packb(
            {"blobs": [], "ops": [], "extension": big}, use_bin_type=True)
        linked_payload = msgpack.packb(
            {"blobs": [], "ops": [["ren", "owner.bin", "renamed.bin"]],
             "extension": big}, use_bin_type=True)
        small_payload = msgpack.packb(
            {"blobs": [], "ops": [["ren", "owner.bin", "renamed.bin"]],
             "extension": [None] * 100}, use_bin_type=True)
        malformed_payload = bytes.fromhex("81 a1 78 81 91 01 c0")
        payloads = {"orphan-overcap": (orphan_payload, 0),
                    "linked-overcap": (linked_payload, checkpoint),
                    "linked-undercap": (small_payload, checkpoint),
                    "malformed-signed": (malformed_payload, checkpoint)}
        cases = {"clean": (base_path, None), "writer-rename": (writer, None)}
        physical = {}
        for case, (payload, prev) in payloads.items():
            dest = root / (case + ".cmpct")
            signed = append_delta(base_path, dest, payload, prev)
            cases[case] = (dest, signed)
        # The runner is independent of the original Builder's temporary tree.
        all_rows = {}
        for case, (file, signed) in cases.items():
            destination = out / "physical" / (case + ".cmpct")
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes(file.read_bytes())
            physical[case] = {"path": str(destination.relative_to(out)),
                              "bytes": destination.stat().st_size,
                              "sha256": digest(destination.read_bytes()),
                              "tail": signed}
            all_rows[case] = {}
            for arm in READERS:
                all_rows[case][arm] = calls(destination, arm, repeats)
        # No post-hoc threshold gardening. Semantic outcomes are frozen in prereg.
        def stable(case, arm, status, depth=None, member=None):
            rows = all_rows[case][arm]
            assert all(r["status"] == status for r in rows), (case, arm, rows)
            if depth is not None:
                assert all(r["depth"] == depth for r in rows), (case, arm, rows)
            if member is not None:
                assert all(member in r["members"] and
                           r["members"][member]["sha256"] == digest(BODY)
                           for r in rows), (case, arm, rows)
        for arm in READERS:
            stable("clean", arm, "opened", 0, "owner.bin")
            stable("writer-rename", arm, "opened", 1, "renamed.bin")
            stable("linked-undercap", arm, "opened", 1, "renamed.bin")
        stable("orphan-overcap", "released", "opened", 0, "owner.bin")
        stable("orphan-overcap", "direct", "opened", 0, "owner.bin")
        stable("orphan-overcap", "gated", "error")
        stable("orphan-overcap", "catch", "opened", 0, "owner.bin")
        stable("linked-overcap", "released", "opened", 1, "renamed.bin")
        stable("linked-overcap", "direct", "opened", 1, "renamed.bin")
        stable("linked-overcap", "gated", "error")
        stable("linked-overcap", "catch", "opened", 0, "owner.bin")
        for c in ("orphan-overcap", "linked-overcap"):
            assert all(r["exception"] == "TooManyNodes" for r in all_rows[c]["gated"])
        for arm in READERS:
            stable("malformed-signed", arm, "error")
        assert all(r["selected_footer"] == checkpoint for r in
                   all_rows["orphan-overcap"]["direct"])
        assert all(r["selected_footer"] == checkpoint for r in
                   all_rows["linked-overcap"]["catch"])
        assert all(r["selected_footer"] > checkpoint for arm in ("released", "direct")
                   for r in all_rows["linked-overcap"][arm])
        src = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        result = {"experiment": "J24G18", "head": src, "parent": PARENT,
                  "reader_blob": EXPECTED_READER_BLOB,
                  "released_reader_blob": RELEASE_READER_BLOB,
                  "released_commit": RELEASE_SHA, "cap": CAP,
                  "checkpoint": checkpoint, "body_sha256": digest(BODY),
                  "physical": physical, "repeats": repeats,
                  "observations": all_rows,
                  "decisions": {
                    "naive_default_gate": "FALSIFIED_FOR_INHERITED_ACCEPTANCE_AND_FALLBACK",
                    "catch_and_fallback_policy": "RECOVERS_ORPHAN_BUT_LOSES_VALID_GENERATION",
                    "native_counter_component_economics": "INHERITED_FROM_J24G17_NOT_REMEASURED"},
                  "product_changes": False, "release_credit": 0}
        (out / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("J24G18_DECISION=" + json.dumps(result["decisions"], sort_keys=True))
        print("J24G18_CASES=" + str(len(cases)) + " REPEATS=" + str(repeats))
        return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=2, metavar=("FILE", "ARM"))
    parser.add_argument("--out", type=Path, default=Path("j24g18-artifacts"))
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.worker:
        raise SystemExit(worker(*args.worker))
    main(args.out, args.repeats)
