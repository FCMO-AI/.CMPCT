#!/usr/bin/env python3
"""J24G12: source-exact Reader lazy ancestry materialization oracle.

Research-only: original installed Reader versus two independent subclass
experiments on the SAME Builder/Writer-created r24 archive bytes.
No main product changes and no release/format claim.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from unittest.mock import patch

import msgpack
import cmpct.reader as product
from cmpct.builder import Builder
from cmpct.codec import FTR, FMAGIC, sha
from cmpct.transactions import append_rename

PARENT = "698f576a13ae1d14f248271185de3503ed839ee7"
READER_BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PREREG = "991ddfa2a42bddaa8d76efdd3524a71c9de52b27"
PAYLOAD = (b"J24G12-verified-owner-exact-content-" * 211) + b"tail"
OPS = [["del", "unmatched-member-%03d-from-evidence" % i] for i in range(32)]
DELTA = msgpack.packb({"blobs": [], "ops": OPS}, use_bin_type=True)


def git_source_guard():
    assert subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
                                   text=True).strip() == READER_BLOB
    assert subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
                          check=False).returncode == 0
    import cmpct.reader
    p = Path(cmpct.reader.__file__).resolve()
    assert "site-packages" in str(p), p
    assert p.read_bytes() == subprocess.check_output(
        ["git", "show", "HEAD:src/cmpct/reader.py"]), "installed source differs from Git"


def safe_replay_index(self, footer_pos, known_bad=None, known_bad_runs=None):
    """Experimental ownership change, not a permanent alternative Reader.

    First pass authenticates all footers, stores only their byte offsets/digests.
    Guarded subclass parses and drops every first-pass delta to preserve the
    inherited malformed-MessagePack error, while unsafe subclass skips parse.
    A successful replay re-authenticates and verifies unchanged first-pass bytes.
    """
    trail = []
    pos = footer_pos
    depth = 0
    seen = set()
    while pos and pos not in seen:
        if known_bad is not None and pos in known_bad:
            break
        seen.add(pos)
        g = self._decode_generation_payload(pos)
        if g is None:
            break
        kind, payload, prev = g
        if kind == 0:
            idx = msgpack.unpackb(payload, raw=False)
            for off, first_digest in reversed(trail):
                again = self._decode_generation_payload(off)
                if (again is None or again[0] != 1 or
                        sha(again[1]) != first_digest):
                    raise IOError("ancestry changed during second-pass replay")
                delta = msgpack.unpackb(again[1], raw=False)
                for b in delta.get("blobs", []):
                    idx["blobs"].append(b)
                for op in delta.get("ops", []):
                    if op[0] == "put":
                        row = op[1]
                        done = False
                        for i, x in enumerate(idx["files"]):
                            if x[0] == row[0]:
                                idx["files"][i] = row
                                done = True
                                break
                        if not done:
                            idx["files"].append(row)
                    elif op[0] == "del":
                        idx["files"] = [x for x in idx["files"] if x[0] != op[1]]
                    elif op[0] == "ren":
                        for x in idx["files"]:
                            if x[0] == op[1]:
                                x[0] = op[2]
                                break
                idx["files"].sort(key=lambda x: x[0])
            return idx, depth
        if kind != 1:
            break
        if getattr(self, "_validate_first", False):
            # Stronger semantically faithful control: retain neither object nor
            # decoded payload, but preserve malformed-delta failure.
            msgpack.unpackb(payload, raw=False)
        trail.append((pos, sha(payload)))
        depth += 1
        pos = prev
    # Exact inherited negative-proof update, unchanged budget and AP admission.
    if known_bad is not None and len(seen) > 1:
        if len(known_bad) + len(seen) <= 16384:
            known_bad.update(seen)
        else:
            certified = False
            if known_bad_runs is not None and len(known_bad_runs) < 32 and len(seen) >= 3:
                ordered = sorted(seen)
                step = ordered[1] - ordered[0]
                if step > 0 and all(
                    p == ordered[0] + i * step for i, p in enumerate(ordered)
                ):
                    known_bad_runs.append((ordered[0], ordered[-1], step))
                    certified = True
            if not certified:
                known_bad.update(seen)
    return None


class UnsafeSkipReader(product.CMPCT):
    _index_from_footer = safe_replay_index
    _validate_first = False


class GuardedDiscardReader(product.CMPCT):
    _index_from_footer = safe_replay_index
    _validate_first = True


ARMS = {"eager": product.CMPCT, "skip": UnsafeSkipReader,
        "guarded": GuardedDiscardReader}


def make_tail(base: bytes, checkpoint: int, n: int, mode: str, corrupt=False):
    raw = bytearray(base)
    last = checkpoint
    for i in range(n):
        payload = (b"\xc1" if corrupt else DELTA)
        prev = last if mode == "valid" else (last if mode == "orphan" and i > 0 else 0)
        at = len(raw) + len(payload)
        raw += payload
        raw += FTR.pack(FMAGIC, 1, 0, 0, 0, len(payload), len(payload),
                        prev, sha(payload))
        last = at
    expected_footer = last if mode == "valid" else checkpoint
    expected_depth = n if mode == "valid" else 0
    return bytes(raw), expected_footer, expected_depth


def check_member(ar, footer, depth, target):
    assert ar.latest_footer_pos == footer, (ar.latest_footer_pos, footer)
    assert ar.delta_depth == depth, (ar.delta_depth, depth)
    assert ar.read(target) == PAYLOAD
    assert ar.read_range(target, 0, 41) == PAYLOAD[:41]
    assert ar.read_range(target, len(PAYLOAD) - 43, 43) == PAYLOAD[-43:]
    ar.verify()


def worker(args):
    archive, arm, footer, depth, target = args
    cls = ARMS[arm]
    source_decode = cls._decode_generation_payload
    counts = {"decode": 0, "unpack": 0}
    original_unpack = msgpack.unpackb

    def meter_decode(self, pos):
        counts["decode"] += 1
        return source_decode(self, pos)

    def meter_unpack(*x, **k):
        counts["unpack"] += 1
        return original_unpack(*x, **k)

    tracemalloc.start()
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    problem = None
    try:
        with patch.object(cls, "_decode_generation_payload", meter_decode):
            with patch.object(msgpack, "unpackb", meter_unpack):
                with cls(Path(archive)) as ar:
                    check_member(ar, int(footer), int(depth), target)
    except Exception as exc:
        problem = {"type": type(exc).__name__, "message": str(exc)[:160]}
    wall = (time.perf_counter_ns() - t0) / 1e6
    cpu = (time.process_time_ns() - c0) / 1e6
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    info = {"arm": arm, "wall_ms": wall, "cpu_ms": cpu,
            "peak_traced_bytes": peak, "remaining_traced_bytes": current,
            "ru_maxrss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "decode_calls": counts["decode"], "unpack_calls": counts["unpack"],
            "failure": problem}
    print("J24G12_ROW=" + json.dumps(info, sort_keys=True), flush=True)


def run_case(label, archive: Path, footer: int, depth: int, target: str,
             repeat: int, expected_bad=False):
    rows = {arm: [] for arm in ARMS}
    orders = [["eager", "skip", "guarded"], ["guarded", "skip", "eager"]]
    for iteration in range(repeat):
        for arm in orders[iteration % 2]:
            args = [sys.executable, str(Path(__file__).resolve()), "--worker",
                    str(archive), arm, str(footer), str(depth), target]
            proc = subprocess.run(args, text=True, capture_output=True)
            if proc.returncode:
                raise AssertionError((label, arm, proc.returncode, proc.stderr[-3000:]))
            payloads = [ln.removeprefix("J24G12_ROW=") for ln in proc.stdout.splitlines()
                        if ln.startswith("J24G12_ROW=")]
            assert len(payloads) == 1, (label, arm, proc.stdout, proc.stderr)
            sample = json.loads(payloads[0])
            rows[arm].append(sample)
            if expected_bad:
                if arm in ("eager", "guarded"):
                    assert sample["failure"] is not None, (label, sample)
                else:
                    assert sample["failure"] is None, (label, sample)
            else:
                assert sample["failure"] is None, (label, sample)
    med = {a: {k: statistics.median(x[k] for x in samples) for k in
               ("wall_ms", "cpu_ms", "peak_traced_bytes", "ru_maxrss_kib_linux",
                "decode_calls", "unpack_calls")}
           for a, samples in rows.items()}
    out = {"case": label, "archive_bytes": archive.stat().st_size,
           "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
           "expected_footer": footer, "expected_depth": depth,
           "raw": rows, "median": med}
    print("J24G12_CASE=" + json.dumps(
        {k: v for k, v in out.items() if k != "raw"}, sort_keys=True), flush=True)
    return out


def main():
    git_source_guard()
    output = Path(os.environ.get("J24G12_ARTIFACTS", "j24g12-artifacts"))
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g12-") as tmp:
        root = Path(tmp)
        tree = root / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(PAYLOAD)
        basepath = root / "base.cmpct"
        Builder(tree).build(basepath)
        with product.CMPCT(basepath) as ar:
            checkpoint = ar.latest_footer_pos
            check_member(ar, checkpoint, 0, "owner.bin")
        base = basepath.read_bytes()
        cases = {}

        # Genuine first-party Writer: preserve a normal shallow-commit control.
        valid_writer = root / "first-party-rename.cmpct"
        valid_writer.write_bytes(base)
        append_rename(valid_writer, "owner.bin", "renamed.bin")
        with product.CMPCT(valid_writer) as ar:
            valid_writer_footer = ar.latest_footer_pos
        cases["writer-rename"] = run_case(
            "writer-rename", valid_writer, valid_writer_footer, 1, "renamed.bin", 5)

        # Same exact signed archives for eager, skip and guarded models.
        for label, mode, n, reps in [
            ("valid-64", "valid", 64, 3),
            ("valid-512", "valid", 512, 3),
            ("orphan-4096", "orphan", 4096, 3),
            ("independent-4096", "independent", 4096, 2),
        ]:
            raw, footer, depth = make_tail(base, checkpoint, n, mode)
            p = root / (label + ".cmpct")
            p.write_bytes(raw)
            cases[label] = run_case(label, p, footer, depth, "owner.bin", reps)
            a, b, c = (cases[label]["median"][key] for key in
                       ("eager", "skip", "guarded"))
            if mode == "valid":
                assert b["decode_calls"] == c["decode_calls"] == 2*n+1, (label, b, c)
                assert a["decode_calls"] == n+1, (label, a)
            else:
                assert b["decode_calls"] == c["decode_calls"] == a["decode_calls"], (
                    label, a, b, c)

        # Independent hostile control: a SHA-authentic invalid MessagePack delta
        # before a previously valid checkpoint. A naive skip changes error policy.
        raw, footer, depth = make_tail(base, checkpoint, 1, "orphan", corrupt=True)
        p = root / "signed-malformed.cmpct"
        p.write_bytes(raw)
        cases["signed-malformed"] = run_case(
            "signed-malformed", p, footer, depth, "owner.bin", 1, True)

        invalid = cases["orphan-4096"]["median"]
        valid = cases["valid-512"]["median"]
        result = {
            "scientific_decision": "RESEARCH_ONLY_NOT_PRODUCT_PROMOTABLE",
            "prereg": PREREG, "parent_head": PARENT,
            "reader_blob": READER_BLOB,
            "cases": cases,
            "invalid_guarded_peak_ratio_to_eager":
                invalid["guarded"]["peak_traced_bytes"] /
                invalid["eager"]["peak_traced_bytes"],
            "valid_guarded_cpu_ratio_to_eager":
                valid["guarded"]["cpu_ms"] / valid["eager"]["cpu_ms"],
            "naive_skip_semantic_difference": True,
            "whole_reader_resource_bound": False,
            "source_mutation_safety": False,
            "format_change": False, "release_credit": 0
        }
        (output / "court.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        print("J24G12_RESULT=" + json.dumps({
            "decision": result["scientific_decision"],
            "invalid_guarded_peak_ratio_to_eager":
                result["invalid_guarded_peak_ratio_to_eager"],
            "valid_guarded_cpu_ratio_to_eager":
                result["valid_guarded_cpu_ratio_to_eager"],
            "naive_skip_semantic_difference": True,
            "release_credit": 0}, sort_keys=True), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(sys.argv[2:])
    else:
        main()
