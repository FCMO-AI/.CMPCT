#!/usr/bin/env python3
"""J24G14 adaptive ancestry ownership O1 oracle; research subclass only.

The inherited product Reader is NOT modified. A fixed raw-payload retention
budget chooses eager one-pass replay or guarded two-pass replay while preserving
the original signed MessagePack parse/error boundary.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time

import msgpack
import cmpct.reader as product
from cmpct.builder import Builder
from cmpct.transactions import append_rename
from cmpct.codec import sha
from j24g12_lazy_ancestry_court import (
    PAYLOAD, GuardedDiscardReader, check_member, git_source_guard, make_tail,
)

PARENT = "0684f5d694afc1abccc397ced3bcd1ef3356cb81"
PREREG = "8bb541f3746ca1c766b86d559488c4de726c15be"
READER_BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
RETAINED_RAW_BUDGET = 1024 * 1024
ARMS = {"eager": product.CMPCT, "guarded": GuardedDiscardReader}
CASES = (
    ("writer-rename", "writer", 1, 3),
    ("valid-64", "valid", 64, 3),
    ("valid-512", "valid", 512, 3),
    ("valid-2048", "valid", 2048, 3),
    ("orphan-4096", "orphan", 4096, 3),
    ("independent-4096", "independent", 4096, 3),
    ("signed-malformed", "malformed", 1, 1),
)


def apply_delta(idx, delta):
    """Mirror exactly the production revision-24 replay semantics."""
    for blob in delta.get("blobs", []):
        idx["blobs"].append(blob)
    for op in delta.get("ops", []):
        if op[0] == "put":
            row = op[1]
            done = False
            for i, entry in enumerate(idx["files"]):
                if entry[0] == row[0]:
                    idx["files"][i] = row
                    done = True
                    break
            if not done:
                idx["files"].append(row)
        elif op[0] == "del":
            idx["files"] = [entry for entry in idx["files"] if entry[0] != op[1]]
        elif op[0] == "ren":
            for entry in idx["files"]:
                if entry[0] == op[1]:
                    entry[0] = op[2]
                    break
    idx["files"].sort(key=lambda entry: entry[0])


class AdaptiveReader(product.CMPCT):
    def __init__(self, path):
        self.adaptive_switches = 0
        self.max_retained_raw_bytes = 0
        super().__init__(path)

    def _index_from_footer(self, footer_pos, known_bad=None, known_bad_runs=None):
        pos = footer_pos
        depth = 0
        seen = set()
        retained = []  # (offset, parsed object, authenticated raw payload)
        proofs = []    # (offset, first-pass SHA) only after memory-pressure switch
        retained_raw_bytes = 0
        deferred = False
        while pos and pos not in seen:
            if known_bad is not None and pos in known_bad:
                break
            seen.add(pos)
            generation = self._decode_generation_payload(pos)
            if generation is None:
                break
            kind, payload, prev = generation
            if kind == 0:
                idx = msgpack.unpackb(payload, raw=False)
                if deferred:
                    for at, first_sha in reversed(proofs):
                        again = self._decode_generation_payload(at)
                        if (again is None or again[0] != 1 or
                                sha(again[1]) != first_sha):
                            raise IOError("ancestry changed during deferred replay")
                        apply_delta(idx, msgpack.unpackb(again[1], raw=False))
                else:
                    for _, parsed, _ in reversed(retained):
                        apply_delta(idx, parsed)
                return idx, depth
            if kind != 1:
                break
            # Signed malformed MessagePack must still raise at this same point.
            parsed = msgpack.unpackb(payload, raw=False)
            if deferred:
                proofs.append((pos, sha(payload)))
            elif retained_raw_bytes + len(payload) <= RETAINED_RAW_BUDGET:
                retained.append((pos, parsed, payload))
                retained_raw_bytes += len(payload)
                if retained_raw_bytes > self.max_retained_raw_bytes:
                    self.max_retained_raw_bytes = retained_raw_bytes
            else:
                # One-time transition changes retention model, not format policy.
                proofs = [(at, sha(raw)) for at, _, raw in retained]
                retained.clear()
                retained_raw_bytes = 0
                deferred = True
                self.adaptive_switches += 1
                proofs.append((pos, sha(payload)))
            depth += 1
            pos = prev
        # Retain inherited exact negative-footer proof behavior, including
        # non-arithmetic fallback (no false-positive range skipping).
        if known_bad is not None and len(seen) > 1:
            if len(known_bad) + len(seen) <= 16384:
                known_bad.update(seen)
            else:
                certified = False
                if (known_bad_runs is not None and len(known_bad_runs) < 32
                        and len(seen) >= 3):
                    ordered = sorted(seen)
                    step = ordered[1] - ordered[0]
                    if (step > 0 and all(
                        at == ordered[0] + i * step
                        for i, at in enumerate(ordered)
                    )):
                        known_bad_runs.append((ordered[0], ordered[-1], step))
                        certified = True
                if not certified:
                    known_bad.update(seen)
        return None


ARMS["adaptive"] = AdaptiveReader


def source_guard():
    git_source_guard()
    assert platform.system() == "Linux"
    for ancestor in (PARENT, PREREG):
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
            check=False,
        ).returncode == 0
    assert subprocess.check_output(
        ["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
        text=True,
    ).strip() == READER_BLOB
    source = Path("research/j24g14_adaptive_ancestry_court.py")
    assert source.read_bytes() == subprocess.check_output(
        ["git", "show", "HEAD:" + source.as_posix()]
    )


def worker(path, arm, footer, depth, member, malformed):
    assert arm in ARMS
    assert bool(int(malformed)) in (True, False)
    cls = ARMS[arm]
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    problem = None
    switches = 0
    max_bytes = 0
    try:
        with cls(Path(path)) as reader:
            check_member(reader, int(footer), int(depth), member)
            switches = getattr(reader, "adaptive_switches", 0)
            max_bytes = getattr(reader, "max_retained_raw_bytes", 0)
    except Exception as exc:
        problem = {"type": type(exc).__name__, "message": str(exc)[:180]}
    cpu_ns = time.process_time_ns() - started_cpu
    wall_ns = time.perf_counter_ns() - started_wall
    row = {
        "arm": arm,
        "cpu_ns": cpu_ns,
        "wall_ns": wall_ns,
        "rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "archive_bytes": Path(path).stat().st_size,
        "archive_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "failure": problem,
        "adaptive_switches": switches,
        "max_retained_raw_bytes": max_bytes,
        "budget_raw_bytes": RETAINED_RAW_BUDGET,
        "reader_blob": READER_BLOB,
    }
    print("J24G14_ROW=" + json.dumps(row, sort_keys=True), flush=True)
    assert (problem is not None) == bool(int(malformed)), problem


def run_case(label, archive, footer, depth, member, repeats, malformed):
    raw = {arm: [] for arm in ARMS}
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    for iteration in range(repeats):
        order = tuple(ARMS) if iteration % 2 == 0 else tuple(reversed(tuple(ARMS)))
        for arm in order:
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker",
                 str(archive), arm, str(footer), str(depth), member,
                 "1" if malformed else "0"],
                capture_output=True, text=True, check=False,
            )
            if proc.returncode:
                raise RuntimeError((label, arm, proc.returncode,
                                    proc.stdout[-1200:], proc.stderr[-2000:]))
            rows = [x.removeprefix("J24G14_ROW=") for x in proc.stdout.splitlines()
                    if x.startswith("J24G14_ROW=")]
            assert len(rows) == 1
            row = json.loads(rows[0])
            assert row["archive_sha256"] == digest
            assert row["archive_bytes"] == archive.stat().st_size
            assert (row["failure"] is not None) == malformed
            assert row["max_retained_raw_bytes"] <= RETAINED_RAW_BUDGET
            raw[arm].append(row)
    med = {
        arm: {
            key: statistics.median(sample[key] for sample in rows)
            for key in ("cpu_ns", "wall_ns", "rss_kib", "adaptive_switches",
                        "max_retained_raw_bytes")
        }
        for arm, rows in raw.items()
    }
    return {
        "case": label, "repetitions": repeats, "malformed": malformed,
        "sha256": digest, "archive_bytes": archive.stat().st_size,
        "expected_footer": footer, "expected_depth": depth,
        "median": med, "raw": raw,
        "adaptive_cpu_ratio_to_eager":
            med["adaptive"]["cpu_ns"] / med["eager"]["cpu_ns"],
        "adaptive_rss_ratio_to_eager":
            med["adaptive"]["rss_kib"] / med["eager"]["rss_kib"],
    }


def main():
    source_guard()
    out = Path(os.environ.get("J24G14_ARTIFACTS", "j24g14-artifacts"))
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g14-") as td:
        root = Path(td)
        tree = root / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(PAYLOAD)
        basepath = root / "base.cmpct"
        Builder(tree).build(basepath)
        with product.CMPCT(basepath) as reader:
            checkpoint = reader.latest_footer_pos
            check_member(reader, checkpoint, 0, "owner.bin")
        base = basepath.read_bytes()
        cases = {}
        for name, mode, n, repeats in CASES:
            path = root / (name + ".cmpct")
            if mode == "writer":
                path.write_bytes(base)
                append_rename(path, "owner.bin", "renamed.bin")
                with product.CMPCT(path) as reader:
                    footer = reader.latest_footer_pos
                depth, member = 1, "renamed.bin"
            else:
                data, footer, depth = make_tail(
                    base, checkpoint, n,
                    "orphan" if mode == "malformed" else mode,
                    corrupt=(mode == "malformed"),
                )
                path.write_bytes(data)
                member = "owner.bin"
            c = run_case(name, path, footer, depth, member, repeats,
                         malformed=(mode == "malformed"))
            cases[name] = c
            print("J24G14_CASE=" + json.dumps({
                "case": name, "median": c["median"],
                "adaptive_cpu_ratio_to_eager": c["adaptive_cpu_ratio_to_eager"],
                "adaptive_rss_ratio_to_eager": c["adaptive_rss_ratio_to_eager"],
            }, sort_keys=True), flush=True)
        result = {
            "scientific_decision": "RESEARCH_ONLY_PENDING_PRODUCT_GATES",
            "parent_head": PARENT, "prereg_commit": PREREG,
            "reader_blob": READER_BLOB,
            "head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "raw_payload_budget_bytes": RETAINED_RAW_BUDGET,
            "cases": cases, "release_credit": 0, "format_changed": False,
            "global_memory_bound_proven": False,
            "source_mutation_safety_proven": False,
        }
        (out / "court.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("J24G14_RESULT=" + json.dumps({
            "valid512_cpu_ratio": cases["valid-512"]["adaptive_cpu_ratio_to_eager"],
            "invalid4096_cpu_ratio": cases["orphan-4096"]["adaptive_cpu_ratio_to_eager"],
            "invalid4096_rss_ratio": cases["orphan-4096"]["adaptive_rss_ratio_to_eager"],
            "deep2048_cpu_ratio": cases["valid-2048"]["adaptive_cpu_ratio_to_eager"],
            "release_credit": 0,
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(*sys.argv[2:])
    else:
        main()
