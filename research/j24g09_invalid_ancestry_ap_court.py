#!/usr/bin/env python3
"""J24G09: actual installed CMPCT Reader exact invalid-ancestry AP certificate court.

Compare original #650 Git Reader against candidate on IDENTICAL first-party Builder
archives. No decoder or authenticity behavior is mocked; only method invocation
counts are observed. Kept independent of the existing frozen J24G07 evaluator.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import tempfile
import time
import tracemalloc
import types
from pathlib import Path
from unittest.mock import patch

import msgpack
from cmpct.builder import Builder
from cmpct.codec import FTR, FMAGIC, sha
from cmpct.reader import CMPCT as Candidate
from cmpct.transactions import append_rename
from j24g04_false_footer_recovery_court import PAYLOAD, digest

ORIGINAL_HEAD = "10a6bc150cfa0ceb8608ee826dc09650ca3f4e3d"
ORIGINAL_BLOB = "bead2ea6a09a6daaadc3ec2389cfb8853e3dd172"
CASE_N = (16_384, 16_400, 32_768)
REPEATS = 2


def original_reader():
    got = subprocess.check_output(
        ["git", "rev-parse", f"{ORIGINAL_HEAD}:src/cmpct/reader.py"], text=True
    ).strip()
    assert got == ORIGINAL_BLOB, got
    raw = subprocess.check_output(["git", "show", f"{ORIGINAL_HEAD}:src/cmpct/reader.py"])
    module = types.ModuleType("cmpct._j24g09_original_reader")
    module.__package__ = "cmpct"
    exec(compile(raw, f"<unchanged Git blob {got}>", "exec"), module.__dict__)
    return module.CMPCT


def orphan_tail(base: bytes, n: int, chained: bool) -> bytes:
    assert 0 <= n <= CASE_N[-1]
    payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
    assert len(payload) + FTR.size == 81
    raw = bytearray(base)
    prev = 0
    for _ in range(n):
        pos = len(raw) + len(payload)
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC, 1, 0, 0, 0,
                            len(payload), len(payload),
                            prev if chained else 0, sha(payload)))
        prev = pos
    assert len(raw) == len(base) + 81 * n
    return bytes(raw)


def variant_orphan_tail(base: bytes, n: int, variant: str) -> bytes:
    """Structural held-outs: generic stride, embedded magic, non-AP spacing."""
    assert variant in ("uniform", "embedded-magic", "alternating")
    raw = bytearray(base)
    prev = 0
    for i in range(n):
        delta = {"blobs": [], "ops": []}
        if variant == "uniform":
            delta["pad"] = b"1234567"
        elif variant == "embedded-magic":
            delta["pad"] = b"before" + FMAGIC + b"after"
        else:
            delta["pad"] = b"X" if i % 2 else b""
        payload = msgpack.packb(delta, use_bin_type=True)
        pos = len(raw) + len(payload)
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC, 1, 0, 0, 0,
                            len(payload), len(payload), prev, sha(payload)))
        prev = pos
    return bytes(raw)


def measure(cls, path: Path, checkpoint: int, member: str = "owner.bin") -> dict:
    decoder = cls._decode_generation_payload
    indexer = cls._index_from_footer
    calls = 0
    index_calls = 0

    def counted_decode(self, pos, *args, **kwargs):
        nonlocal calls
        calls += 1
        return decoder(self, pos, *args, **kwargs)

    def counted_index(self, pos, *args, **kwargs):
        nonlocal index_calls
        index_calls += 1
        return indexer(self, pos, *args, **kwargs)

    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    with patch.object(cls, "_decode_generation_payload", counted_decode), \
         patch.object(cls, "_index_from_footer", counted_index):
        with cls(path) as ar:
            assert ar.latest_footer_pos == checkpoint
            expected = PAYLOAD
            assert ar.read(member) == expected
            assert ar.read_range(member, 0, 19) == expected[:19]
            assert ar.read_range(member, len(expected) - 23, 23) == expected[-23:]
            ar.verify()
            depth = ar.delta_depth

    return {
        "decoder_calls": calls,
        "index_attempts": index_calls,
        "selected_footer": checkpoint,
        "depth": depth,
        "logical_sha256": digest(PAYLOAD),
        "wall_ms": (time.perf_counter_ns() - wall_start) / 1e6,
        "cpu_ms": (time.process_time_ns() - cpu_start) / 1e6,
    }


def run_pair(Historical, path, checkpoint, want_old, want_new, member="owner.bin"):
    old, new = [], []
    for i in range(REPEATS):
        for tag in (("historical", "candidate") if i % 2 == 0 else ("candidate", "historical")):
            cls = Historical if tag == "historical" else Candidate
            (old if tag == "historical" else new).append(measure(cls, path, checkpoint, member))
    assert all(x["decoder_calls"] == want_old for x in old), (want_old, old)
    assert all(x["decoder_calls"] == want_new for x in new), (want_new, new)
    assert all(x["depth"] == 0 for x in old + new) or member != "owner.bin"
    return {
        "historical": old, "candidate": new,
        "historical_median_ms": statistics.median(x["wall_ms"] for x in old),
        "candidate_median_ms": statistics.median(x["wall_ms"] for x in new),
        "historical_median_cpu_ms": statistics.median(x["cpu_ms"] for x in old),
        "candidate_median_cpu_ms": statistics.median(x["cpu_ms"] for x in new),
    }


def main():
    out = Path(os.environ.get("J24G09_ARTIFACTS", "j24g09-artifacts"))
    out.mkdir(parents=True, exist_ok=True)
    Historical = original_reader()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g09-") as td:
        root = Path(td)
        tree = root / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(PAYLOAD)
        pristine = root / "pristine.cmpct"
        Builder(tree).build(pristine)
        base = pristine.read_bytes()
        with Candidate(pristine) as ar:
            checkpoint = ar.latest_footer_pos
            assert checkpoint > 0 and ar.read("owner.bin") == PAYLOAD

        cases = []
        for n in CASE_N:
            data = orphan_tail(base, n, True)
            p = root / f"linked-{n}.cmpct"
            p.write_bytes(data)
            row = {
                "name": f"linked-{n}", "n": n, "physical_bytes": len(data),
                "archive_sha256": digest(data),
                "original_checkpoint": checkpoint,
            }
            if n < CASE_N[-1]:
                previous = n + 1 if n <= 16_384 else (
                    n * (n + 1) - 16_384 * (16_384 + 1)
                ) // 2 + 16_384 + 1
                row["paired"] = run_pair(Historical, p, checkpoint, previous, n + 1)
            else:
                # Do NOT execute the O(N^2) historical N32768 baseline.
                row["candidate_only"] = [measure(Candidate, p, checkpoint)
                                         for _ in range(REPEATS)]
                assert all(x["decoder_calls"] == n + 1 for x in row["candidate_only"])
                assert all(x["index_attempts"] <= 3 for x in row["candidate_only"])
                row["historical_calls_lower_bound"] = 134_000_000
                row["historical_not_run"] = "prohibitive known quadratic CPU"
            cases.append(row)
            print("J24G09_CASE=" + json.dumps(row, sort_keys=True), flush=True)

        n = 16_400
        flat = orphan_tail(base, n, False)
        assert len(flat) == cases[1]["physical_bytes"]
        flat_p = root / "flat.cmpct"
        flat_p.write_bytes(flat)
        flat_pair = run_pair(Historical, flat_p, checkpoint, n + 1, n + 1)
        neutral = base + b"Q" * (len(flat) - len(base))
        neutral_p = root / "neutral.cmpct"
        neutral_p.write_bytes(neutral)
        assert len(neutral) == len(flat)
        neutral_pair = run_pair(Historical, neutral_p, checkpoint, 1, 1)

        # A genuine first-party valid transaction must still take precedence.
        valid_p = root / "valid-rename.cmpct"
        valid_p.write_bytes(base)
        append_rename(valid_p, "owner.bin", "renamed.bin")
        with Candidate(valid_p) as ar:
            valid_pos = ar.latest_footer_pos
            assert valid_pos > checkpoint and ar.delta_depth == 1
        valid_pair = run_pair(Historical, valid_p, valid_pos, 2, 2, "renamed.bin")
        assert all(x["depth"] == 1 for x in
                   valid_pair["historical"] + valid_pair["candidate"])

        held_out = {}
        for variant in ("uniform", "embedded-magic", "alternating"):
            generated = variant_orphan_tail(base, 16_400, variant)
            p = root / f"{variant}.cmpct"
            p.write_bytes(generated)
            measured = measure(Candidate, p, checkpoint)
            if variant == "uniform":
                assert measured["decoder_calls"] == 16_401, measured
                assert measured["index_attempts"] <= 3, measured
            elif variant == "embedded-magic":
                # Every nested magic offset must be individually examined,
                # not mistaken for one of the exact authenticated AP members.
                assert measured["decoder_calls"] == 32_801, measured
                assert measured["index_attempts"] == 16_402, measured
            else:
                # No arithmetic certificate may accept alternating spacings.
                # This is a deliberately retained negative performance result.
                assert measured["decoder_calls"] == 278_665, measured
                assert measured["index_attempts"] == 16_401, measured
            held_out[variant] = {
                "physical_bytes": len(generated),
                "archive_sha256": digest(generated),
                "measured": measured,
            }
            print("J24G09_STRUCTURAL_HELD_OUT=" +
                  json.dumps({"type": variant, **held_out[variant]}, sort_keys=True),
                  flush=True)

        # Python-traced allocation is a diagnostic, NOT whole-process peak RSS.
        tracemalloc.start()
        memory_check = measure(Candidate, root / "linked-32768.cmpct", checkpoint)
        _, traced_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert memory_check["decoder_calls"] == 32_769
        result = {
            "status": "J24G09_CANDIDATE_AP_COURT_PASSED_WITHIN_SCOPE",
            "original_reader_blob": ORIGINAL_BLOB,
            "candidate_reader_blob": subprocess.check_output(
                ["git", "rev-parse", "HEAD:src/cmpct/reader.py"], text=True
            ).strip(),
            "original_builder_archive_sha256": digest(base),
            "original_builder_archive_bytes": len(base),
            "logical_sha256": digest(PAYLOAD),
            "repeats": REPEATS,
            "cases": cases,
            "held_out_structures": held_out,
            "tracemalloc_peak_bytes_on_repeated_n32768": traced_peak,
            "flat_control": {"archive_sha256": digest(flat), "paired": flat_pair},
            "neutral_control": {"archive_sha256": digest(neutral), "paired": neutral_pair},
            "committed_control": {"archive_sha256": digest(valid_p.read_bytes()),
                                  "paired": valid_pair},
            "product_claim": "narrow exact AP footer ancestry only",
            "unsupported": ["mutable input source", "arbitrary non-AP hostile ancestry",
                            "full RSS/system economy", "non-Linux hosts"],
            "release_credit": 0,
        }
        high = cases[1]["paired"]
        assert high["historical_median_ms"] / high["candidate_median_ms"] >= 2.0, high
        assert all(x["index_attempts"] <= 3 for x in high["candidate"]), high
        (out / "court.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("J24G09_RESULT=" + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
