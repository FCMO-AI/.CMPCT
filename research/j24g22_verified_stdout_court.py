#!/usr/bin/env python3
"""J24G22 independent research court: verified-before-emit versus spool and unsafe range emission.

Research ONLY. No CLI/API changes, format changes or promotion rights.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BLOCK = 256 * 1024
SEED = 42022


class CountingSink:
    def __init__(self):
        self.length = 0
        self.hash = hashlib.sha256()

    def write(self, value):
        self.length += len(value)
        self.hash.update(value)
        return len(value)


def worker(archive: Path, member: str, mode: str) -> dict:
    import resource
    from cmpct.reader import CMPCT

    sink = CountingSink()
    with CMPCT(archive) as reader:
        row = reader.by[member]
        kind = row[6][0]
        size = row[4]
        baseline_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        start_cpu = time.process_time_ns()
        start_wall = time.perf_counter_ns()
        temp_bytes = 0
        error = None
        try:
            if mode == "eager":
                # Exact existing CLI boundary: read/verify before writing anything.
                raw = reader.read(member)
                sink.write(raw)
            elif mode == "premature":
                # INTENTIONAL UNSAFE ORACLE. Never install this as product.
                for off in range(0, size, BLOCK):
                    block = reader.read_range(member, off, min(BLOCK, size-off))
                    if len(block) != min(BLOCK, size-off):
                        raise IOError("short ranged member")
                    sink.write(block)
            elif mode == "spool":
                # Validating before output owns whole temporary file, not RAM.
                expected = reader.file_sha256(member)
                digest = hashlib.sha256()
                with tempfile.TemporaryFile(mode="w+b") as temporary:
                    for off in range(0, size, BLOCK):
                        block = reader.read_range(member, off, min(BLOCK, size-off))
                        if len(block) != min(BLOCK, size-off):
                            raise IOError("short ranged member")
                        temporary.write(block)
                        digest.update(block)
                        temp_bytes += len(block)
                    if digest.digest() != bytes(expected):
                        raise IOError("full logical SHA-256 mismatch before emission")
                    temporary.seek(0)
                    while True:
                        block = temporary.read(BLOCK)
                        if not block:
                            break
                        sink.write(block)
            else:
                raise ValueError(mode)
        except Exception as exc:
            error = type(exc).__name__ + ": " + str(exc)[:180]
        end_cpu = time.process_time_ns()
        end_wall = time.perf_counter_ns()
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {
            "mode": mode,
            "member": member,
            "storage": int(kind),
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "size": int(size),
            "emitted_bytes": sink.length,
            "emitted_sha256": sink.hash.hexdigest(),
            "temp_bytes_written": temp_bytes,
            "cpu_ns": end_cpu - start_cpu,
            "wall_ns": end_wall - start_wall,
            "rss_peak_kib": rss,
            "rss_increment_over_open_kib": max(0, rss - baseline_rss),
            "error": error,
            "source": str(Path(sys.modules["cmpct.reader"].__file__).resolve()),
        }


def create_evidence(workdir: Path) -> dict:
    from cmpct.builder import Builder
    from cmpct.codec import BMAGIC, BHDR, CODEC_RAW, S_BLOB
    from cmpct.reader import CMPCT

    root = workdir / "input"
    root.mkdir()
    r = random.Random(SEED)
    # Deterministic incompressible input: 0.75 MiB direct versus >1 MiB CDC.
    payloads = {"direct.bin": r.randbytes(768 * 1024), "larger.bin": r.randbytes(2 * 1024 * 1024)}
    for name, payload in payloads.items():
        (root / name).write_bytes(payload)
    original = workdir / "original.cmpct"
    Builder(root, workers=1, reproducible=True).build(original)

    shapes = {}
    with CMPCT(original) as reader:
        assert sorted(x[0] for x in reader.files) == sorted(payloads)
        for name, payload in payloads.items():
            assert reader.read(name) == payload, name
            assert hashlib.sha256(payload).digest() == reader.file_sha256(name), name
            row = reader.by[name]
            codec = reader.blobs[row[6][1]][3] if row[6][0] == S_BLOB else None
            shapes[name] = {"kind": row[6][0], "physical_codec": codec, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        direct = reader.by["direct.bin"]
        assert direct[6][0] == S_BLOB, "first-party direct input unexpectedly not S_BLOB"
        blob_index = direct[6][1]
        off, us, cs, codec, ml = reader.blobs[blob_index]
        assert codec == CODEC_RAW, "first-party direct input unexpectedly not RAW"
        pos = reader.record_base + off
        m, c, flags, reserved, rus, rcs, rml, rcrc, rh = BHDR.unpack_from(reader.mm, pos)
        assert m == BMAGIC and c == CODEC_RAW and rus == us and rcs == cs and rml == ml
        physical = pos + BHDR.size + rml + cs - 1
        assert 0 <= physical < original.stat().st_size
    corrupt = workdir / "late-corrupt.cmpct"
    shutil.copyfile(original, corrupt)
    with corrupt.open("r+b") as file:
        file.seek(physical)
        b = file.read(1)
        assert len(b) == 1
        file.seek(physical)
        file.write(bytes([b[0] ^ 0x01]))

    return {
        "cases": shapes,
        "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "corrupt_sha256": hashlib.sha256(corrupt.read_bytes()).hexdigest(),
        "original_bytes": original.stat().st_size,
        "corrupt_bytes": corrupt.stat().st_size,
        "mutated_physical_offset": physical,
        "source_bound": "published-v0.30.0-r24",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=3, metavar=("ARCHIVE", "MEMBER", "MODE"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(Path(args.worker[0]), args.worker[1], args.worker[2]), sort_keys=True))
        return
    if args.out is None:
        parser.error("--out required")
    args.out.mkdir(parents=True, exist_ok=True)
    evidence = create_evidence(args.out)
    observations = []
    for archived, member, kind in (
        ("original.cmpct", "direct.bin", "pristine-direct"),
        ("original.cmpct", "larger.bin", "pristine-large"),
        ("late-corrupt.cmpct", "direct.bin", "corrupt-late"),
    ):
        for repetition in range(3):
            for mode in ("eager", "spool", "premature"):
                command = [sys.executable, __file__, "--worker", str(args.out / archived), member, mode]
                run = subprocess.run(command, capture_output=True, text=True, check=True, timeout=90)
                item = json.loads(run.stdout)
                item.update({"case": kind, "repetition": repetition})
                observations.append(item)
    for item in observations:
        if item["case"].startswith("pristine"):
            assert item["error"] is None, item
            assert item["emitted_bytes"] == evidence["cases"][item["member"]]["bytes"], item
            assert item["emitted_sha256"] == evidence["cases"][item["member"]]["sha256"], item
        elif item["mode"] in ("spool", "eager"):
            assert item["error"] is not None and item["emitted_bytes"] == 0, item
        else:
            assert item["error"] is None and item["emitted_bytes"] > 0, item
            assert item["emitted_sha256"] != evidence["cases"]["direct.bin"]["sha256"], item
    evidence["observations"] = observations
    evidence["decision"] = "VERIFIED_STDOUT_REQUIRES_BUFFER_OR_SPOOL_OR_TWO_PASSES; PREMATURE_RANGE_EMITS_CORRUPTION"
    evidence["scope"] = "research only; no global RSS bounds or generalized product/evaluator/release claim"
    (args.out / "receipt.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"decision": evidence["decision"], "observations": len(observations),
                      "physical_archive_sha256": evidence["original_sha256"],
                      "late_corrupt_sha256": evidence["corrupt_sha256"],
                      "raw_storage": evidence["cases"]["direct.bin"]}, sort_keys=True))


if __name__ == "__main__":
    main()
