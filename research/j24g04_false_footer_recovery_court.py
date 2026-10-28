#!/usr/bin/env python3
"""J24G04: actual released CMPCT Builder/Reader orphan-footer recovery cost court.

Source-instrumented *call count* only. No Reader internals are replaced. The original
signed primary index must remain valid, and the same original member bytes must read
and verify on every archive. This is a scientific falsifier, not a release benchmark.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import time
from unittest.mock import patch

import msgpack

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, sha
from cmpct.reader import CMPCT
from cmpct.transactions import append_rename

PAYLOAD = b"J24G04 authentic source recovery\x00" * 59
N_CASES = (32, 128, 256)
REPETITIONS = 3


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def append_orphan_deltas(base: bytes, count: int) -> bytes:
    """Every footer is locally SHA-authentic, but no delta chain finds a checkpoint.

    The initial fake delta points to zero; every later footer points to the
    *previous* fake footer. The signed original primary index is unchanged.
    """
    assert 0 <= count <= 256
    raw = bytearray(base)
    prev = 0
    for _ in range(count):
        payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
        pos = len(raw) + len(payload)
        raw.extend(payload)
        raw.extend(
            FTR.pack(
                FMAGIC, 1, 0, 0, 0, len(payload), len(payload), prev, sha(payload)
            )
        )
        prev = pos
    return bytes(raw)


def measure_actual_reader(path: Path, member: str, expected: bytes) -> dict:
    calls = []
    original = CMPCT._decode_generation_payload

    def counted(self, footer_pos):
        calls.append(footer_pos)
        return original(self, footer_pos)

    t_wall = time.perf_counter()
    t_cpu = time.process_time()
    with patch.object(CMPCT, "_decode_generation_payload", counted):
        with CMPCT(path) as archive:
            assert archive.read(member) == expected, "primary-index fallback changed file"
            assert archive.read_range(member, 1, 11) == expected[1:12]
            archive.verify()
            assert archive.latest_footer_pos == (0 if member == "owner.bin" else archive.latest_footer_pos)
    wall = time.perf_counter() - t_wall
    cpu = time.process_time() - t_cpu
    return {
        "calls": len(calls),
        "unique_footer_positions": len(set(calls)),
        "wall_s": wall,
        "cpu_s": cpu,
    }


def main() -> None:
    out_dir = Path(os.environ.get("J24G04_ARTIFACTS", "j24g04-artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g04-") as tmp:
        td = Path(tmp)
        source = td / "tree"
        source.mkdir()
        (source / "owner.bin").write_bytes(PAYLOAD)
        pristine = td / "pristine.cmpct"
        Builder(source).build(pristine)
        base = pristine.read_bytes()

        # Negative control: the clean Builder index needs no journal traversal.
        baseline = [measure_actual_reader(pristine, "owner.bin", PAYLOAD) for _ in range(REPETITIONS)]
        assert all(x["calls"] == 0 for x in baseline), baseline

        # Real first-party committed transaction: validate the scanner's success case.
        valid = td / "valid-rename.cmpct"
        shutil.copyfile(pristine, valid)
        append_rename(valid, "owner.bin", "renamed.bin")
        valid_reads = [
            measure_actual_reader(valid, "renamed.bin", PAYLOAD)
            for _ in range(REPETITIONS)
        ]
        assert all(x["calls"] >= 1 for x in valid_reads), valid_reads

        cases = []
        for n in N_CASES:
            fake_bytes = append_orphan_deltas(base, n)
            fake = td / f"orphan-{n}.cmpct"
            fake.write_bytes(fake_bytes)
            got = [
                measure_actual_reader(fake, "owner.bin", PAYLOAD)
                for _ in range(REPETITIONS)
            ]
            expected_calls = n * (n + 1) // 2
            assert all(row["calls"] == expected_calls for row in got), (
                n, expected_calls, got
            )
            assert all(row["unique_footer_positions"] == n for row in got), (
                n, got
            )
            cases.append({
                "n": n,
                "archive_size": len(fake_bytes),
                "archive_sha256": digest(fake_bytes),
                "expected_decoder_calls": expected_calls,
                "observed": got,
                "median_wall_s": statistics.median(x["wall_s"] for x in got),
                "median_cpu_s": statistics.median(x["cpu_s"] for x in got),
            })

        # Equal-size non-magic suffix: distinguish linear byte scanning from
        # repeated authenticated footer decode/replay work. Different contents,
        # same complete stored-byte count as the largest orphan-tail case.
        biggest = append_orphan_deltas(base, N_CASES[-1])
        neutral = td / "neutral-tail.cmpct"
        neutral.write_bytes(base + b"Q" * (len(biggest) - len(base)))
        control = [
            measure_actual_reader(neutral, "owner.bin", PAYLOAD)
            for _ in range(REPETITIONS)
        ]
        assert neutral.stat().st_size == len(biggest)
        assert all(row["calls"] == 0 for row in control), control

        result = {
            "question": "J24G04-orphaned-signed-footer-candidate-scan",
            "status": "TRIANGULAR_SOURCE_DECODER_REVISITS_CONFIRMED",
            "scope": "real-installed-builder-reader; signed primary index; invalid appended delta chain",
            "primary_sha256": digest(base),
            "primary_bytes": len(base),
            "logical_sha256": digest(PAYLOAD),
            "repeat_count": REPETITIONS,
            "valid_transaction_archive_sha256": digest(valid.read_bytes()),
            "valid_transaction_calls": valid_reads,
            "baseline": baseline,
            "no_magic_tail_control": {
                "archive_size": neutral.stat().st_size,
                "archive_sha256": digest(neutral.read_bytes()),
                "observed": control,
            },
            "cases": cases,
            "product_source_changed": False,
            "release_credit": 0,
        }
        out = out_dir / "court.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("J24G04_SOURCE_EXACT_RECOVERY_COURT=" + json.dumps(result, sort_keys=True))
        print("J24G04_DECISION=TRIANGULAR_SOURCE_DECODER_REVISITS_CONFIRMED")


if __name__ == "__main__":
    main()
