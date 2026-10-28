#!/usr/bin/env python3
"""J24G07: source-exact installed Reader upper-cap replay-work falsifier.

No product source change. Genuine SHA-valid orphan footer records, Builder checkpoint,
read/range/verify, physical stored-byte controls, direct decode-call counting.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import msgpack

from cmpct.builder import Builder
from cmpct.codec import FTR, FMAGIC, sha
from cmpct.reader import CMPCT
from j24g04_false_footer_recovery_court import PAYLOAD, digest

CAP = 16_384
CASE_N = (CAP, CAP + 16)
REPEATS = 2


def orphan_tail(base: bytes, n: int, chained: bool) -> bytes:
    """Same grammar as J24G04; this research court extends bounded N beyond 256."""
    assert 0 <= n <= 16_400
    raw = bytearray(base)
    payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
    prev = 0
    for _ in range(n):
        pos = len(raw) + len(payload)
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC, 1, 0, 0, 0,
                            len(payload), len(payload), prev if chained else 0, sha(payload)))
        prev = pos
    assert len(raw) == len(base) + n * (len(payload) + FTR.size)
    assert len(payload) + FTR.size == 81
    return bytes(raw)


def predicted_calls(n: int, cap: int = CAP) -> int:
    if n <= cap:
        return n + 1
    return (n * (n + 1) - cap * (cap + 1)) // 2 + cap + 1


def measure(path: Path, checkpoint: int) -> dict:
    calls = 0
    unique = set()
    decode = CMPCT._decode_generation_payload

    def instrument(self, pos):
        nonlocal calls
        calls += 1
        unique.add(pos)
        return decode(self, pos)

    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    with patch.object(CMPCT, "_decode_generation_payload", instrument):
        with CMPCT(path) as archive:
            assert archive.latest_footer_pos == checkpoint
            assert archive.delta_depth == 0
            assert archive.read("owner.bin") == PAYLOAD
            assert archive.read_range("owner.bin", 0, 17) == PAYLOAD[:17]
            assert archive.read_range("owner.bin", len(PAYLOAD) - 7, 7) == PAYLOAD[-7:]
            archive.verify()
    return {
        "decoder_calls": calls,
        "unique_decoded_positions": len(unique),
        "selected_checkpoint": checkpoint,
        "delta_depth": 0,
        "wall_ms": (time.perf_counter_ns() - start_wall) / 1e6,
        "cpu_ms": (time.process_time_ns() - start_cpu) / 1e6,
        "logical_sha256": digest(PAYLOAD),
    }


def main():
    artifacts = Path(os.environ.get("J24G07_ARTIFACTS", "j24g07-artifacts"))
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g07-") as temp:
        td = Path(temp)
        src = td / "source"
        src.mkdir()
        (src / "owner.bin").write_bytes(PAYLOAD)
        clean = td / "checkpoint.cmpct"
        Builder(src).build(clean)
        original = clean.read_bytes()
        with CMPCT(clean) as ar:
            checkpoint = ar.latest_footer_pos
            assert checkpoint > 0 and ar.read("owner.bin") == PAYLOAD

        cases = []
        linked_by_n = {}
        for n in CASE_N:
            data = orphan_tail(original, n, True)
            p = td / ("chain-" + str(n) + ".cmpct")
            p.write_bytes(data)
            rows = [measure(p, checkpoint) for _ in range(REPEATS)]
            expected = predicted_calls(n)
            assert all(x["decoder_calls"] == expected for x in rows), (n, expected, rows)
            assert all(x["unique_decoded_positions"] == n + 1 for x in rows), rows
            cases.append({
                "type": "linked",
                "n": n,
                "physical_bytes": len(data),
                "archive_sha256": digest(data),
                "predicted_decoder_calls": expected,
                "runs": rows,
                "median_wall_ms": statistics.median(x["wall_ms"] for x in rows),
                "median_cpu_ms": statistics.median(x["cpu_ms"] for x in rows),
            })
            linked_by_n[n] = cases[-1]
            print("J24G07_LINKED_CASE=" + json.dumps(cases[-1], sort_keys=True), flush=True)

        # Distinguish ancestry overlap from identical stored bytes / scan cost.
        n = CASE_N[-1]
        flat = orphan_tail(original, n, False)
        flat_path = td / "flat.cmpct"
        flat_path.write_bytes(flat)
        neutral = original + b"Q" * (len(flat) - len(original))
        neutral_path = td / "neutral.cmpct"
        neutral_path.write_bytes(neutral)
        assert len(flat) == len(neutral) == linked_by_n[n]["physical_bytes"]
        controls = {}
        for name, path, data, want in [
            ("flat", flat_path, flat, n + 1),
            ("neutral", neutral_path, neutral, 1),
        ]:
            runs = [measure(path, checkpoint) for _ in range(REPEATS)]
            assert all(x["decoder_calls"] == want for x in runs), (name, runs)
            controls[name] = {
                "physical_bytes": len(data),
                "archive_sha256": digest(data),
                "expected_decoder_calls": want,
                "runs": runs,
                "median_wall_ms": statistics.median(x["wall_ms"] for x in runs),
                "median_cpu_ms": statistics.median(x["cpu_ms"] for x in runs),
            }
            print("J24G07_CONTROL=" + json.dumps({"name": name, **controls[name]}, sort_keys=True), flush=True)

        low = linked_by_n[CAP]
        high = linked_by_n[CAP + 16]
        ratio = high["median_wall_ms"] / low["median_wall_ms"]
        work_ratio = high["predicted_decoder_calls"] / low["predicted_decoder_calls"]
        outcome = {
            "question": "J24G07 16,384-position negative footer cache bounds memory but not replay work",
            "decision": "ABOVE_CAP_DECODE_REPLAY_CLIFF_CONFIRMED",
            "product_source_changed": False,
            "release_credit": 0,
            "reader_git_blob": "bead2ea6a09a6daaadc3ec2389cfb8853e3dd172",
            "source_builder_archive_sha256": digest(original),
            "source_builder_archive_bytes": len(original),
            "logical_sha256": digest(PAYLOAD),
            "original_checkpoint": checkpoint,
            "source_ftr_bytes_per_delta": 81,
            "memory_cap_positions": CAP,
            "repeats_per_case": REPEATS,
            "cases": cases,
            "controls": controls,
            "predicted_and_observed_call_ratio": work_ratio,
            "observed_median_wall_ratio": ratio,
            "limitations": "one source-exact Ubuntu installed Reader; wall/CPU noisy; no full promotion claim",
        }
        assert high["predicted_decoder_calls"] == 278_665
        assert work_ratio >= 16.9
        (artifacts / "court.json").write_text(json.dumps(outcome, sort_keys=True, indent=2) + "\n")
        print("J24G07_RECEIPT=" + json.dumps(outcome, sort_keys=True), flush=True)
        print("J24G07_DECISION=ABOVE_CAP_DECODE_REPLAY_CLIFF_CONFIRMED", flush=True)


if __name__ == "__main__":
    main()
