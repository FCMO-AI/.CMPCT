#!/usr/bin/env python3
"""O24 research-only private snapshot control against O23 source mutation.

No product/format changes; preregistration is a separate earlier commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cmpct.codec import BHDR, sha
from cmpct.reader import CMPCT
from v031_pack_physical_sha_court import archive_bytes
from v031_verify_extract_source_lifetime_o23 import (
    digest, in_place, must_reject_sha, view,
)


def snapshot(source: Path, target: Path) -> int:
    """Copy one complete source incarnation into a private regular file."""
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    count = 0
    try:
        with open(source, "rb") as src, os.fdopen(fd, "wb") as dst:
            fd = -1
            while True:
                block = src.read(1024 * 1024)
                if not block:
                    break
                dst.write(block)
                count += len(block)
            dst.flush()
            os.fsync(dst.fileno())
    finally:
        if fd >= 0:
            os.close(fd)
    return count


def test_mutation(root: Path, name: str, packed: bool, original: bytes, mutant: bytes) -> dict:
    before_image = archive_bytes(original, original, packed=packed)
    after_image = archive_bytes(original, mutant, packed=packed)
    assert len(before_image) == len(after_image) and before_image != after_image
    source = root / (name + "-mutable.cmpct")
    source.write_bytes(before_image)
    before_stat = source.stat()
    private_root = root / (name + "-private")
    private_root.mkdir(mode=0o700)
    os.chmod(private_root, 0o700)
    private_archive = private_root / "verified-source.cmpct"
    copied = snapshot(source, private_archive)
    assert copied == len(before_image)
    assert digest(private_archive.read_bytes()) == digest(before_image)
    assert private_archive.stat().st_mode & 0o777 == 0o600

    # Mutate the original inode AFTER the private copy, while leaving the
    # authenticated index and its physical SHA commitment unchanged.
    fd = os.open(source, os.O_RDWR)
    try:
        in_place(fd, after_image)
    finally:
        os.close(fd)
    after_stat = source.stat()
    assert (before_stat.st_dev, before_stat.st_ino, before_stat.st_size) == (
        after_stat.st_dev, after_stat.st_ino, after_stat.st_size
    )
    assert digest(source.read_bytes()) == digest(after_image)
    assert digest(private_archive.read_bytes()) == digest(before_image)
    assert bytes(before_image[:64]) == bytes(after_image[:64])
    assert digest(original) != digest(mutant)
    assert sha(original) != sha(mutant)
    assert must_reject_sha(source, packed) == digest(mutant)

    with CMPCT(private_archive) as reader:
        assert reader.verify() == (2 if packed else 1)
        destination = root / (name + "-restored")
        reader.extractall(destination, metadata=False)
    out = view(destination, packed)
    assert out == original, "private snapshot published content not verified in its own archive"

    # A copy made AFTER the source mutation cannot magically verify its
    # original SHA; stage policy must fail closed on the already-bad source.
    badcopy = private_root / "already-mutated.cmpct"
    assert snapshot(source, badcopy) == copied
    assert digest(badcopy.read_bytes()) == digest(after_image)
    assert must_reject_sha(badcopy, packed) == digest(mutant)
    return {
        "case": name,
        "logical_bytes": len(original),
        "stored_archive_bytes": copied,
        "original_archive_sha256": digest(before_image),
        "modified_source_archive_sha256": digest(after_image),
        "snapshot_archive_sha256": digest(private_archive.read_bytes()),
        "source_inode_and_size_stable": True,
        "original_source_mutated_after_snapshot": True,
        "postmutation_fresh_source_sha_reject": True,
        "postmutation_copy_sha_reject": True,
        "private_snapshot_verify": "PASS",
        "private_snapshot_extraction_sha256": digest(out),
        "verified_original_logical_sha256": digest(original),
        "snapshot_temp_stored_bytes": copied,
        "minimum_additional_snapshot_read_bytes": copied,
        "minimum_additional_snapshot_write_bytes": copied,
        "physical_sha_stale_after_source_mutation": True,
        "snapshot_verified_before_extraction": True,
    }


def one_child(source: Path, packed: bool, expected: str, mode: str) -> dict:
    # Material timing excludes Python startup, fixture generation, output
    # oracle hashing and cleanup equally in both arms.
    with tempfile.TemporaryDirectory(prefix="cmpct-o24-child-") as dirname:
        root = Path(dirname)
        input_path = source
        t0 = time.perf_counter_ns()
        c0 = time.process_time_ns()
        copied = 0
        if mode == "snapshot":
            input_path = root / "source.cmpct"
            copied = snapshot(source, input_path)
        with CMPCT(input_path) as reader:
            assert reader.verify() == (2 if packed else 1)
            dest = root / "output"
            reader.extractall(dest, metadata=False)
        cpu = (time.process_time_ns() - c0) / 1e6
        wall = (time.perf_counter_ns() - t0) / 1e6
        output = view(dest, packed)
        assert digest(output) == expected
        return {
            "mode": mode,
            "operation_wall_ms": wall,
            "operation_cpu_ms": cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "source_bytes": source.stat().st_size,
            "snapshot_copied_bytes": copied,
            "output_sha256": digest(output),
            "source_archive_sha256": digest(source.read_bytes()),
        }


def child_main(opts: argparse.Namespace) -> None:
    print(json.dumps(one_child(opts.archive, opts.packed, opts.expected, opts.mode), sort_keys=True))


def cost_court(root: Path, name: str, packed: bool, original: bytes) -> dict:
    fixture = root / (name + "-stable.cmpct")
    image = archive_bytes(original, original, packed=packed)
    fixture.write_bytes(image)
    assert digest(fixture.read_bytes()) == digest(image)
    records = []
    for block in range(5):
        order = ["direct", "snapshot"] if block % 2 == 0 else ["snapshot", "direct"]
        for mode in order:
            command = [
                sys.executable, str(Path(__file__).resolve()),
                "--child", "--archive", str(fixture), "--mode", mode,
                "--expected", digest(original),
            ]
            if packed:
                command.append("--packed")
            run_start = time.perf_counter_ns()
            proc = subprocess.run(command, capture_output=True, text=True, check=True)
            total_ms = (time.perf_counter_ns() - run_start) / 1e6
            rec = json.loads(proc.stdout)
            assert rec["output_sha256"] == digest(original)
            assert rec["source_archive_sha256"] == digest(image)
            assert rec["snapshot_copied_bytes"] == (len(image) if mode == "snapshot" else 0)
            rec.update({"block": block, "fresh_process_wall_ms": total_ms})
            records.append(rec)
    def med(key: str, mode: str) -> float:
        return statistics.median(row[key] for row in records if row["mode"] == mode)
    summary = {
        "case": name,
        "archive_bytes": len(image),
        "logical_bytes": len(original),
        "sample_count": len(records),
        "direct_operation_wall_ms": med("operation_wall_ms", "direct"),
        "snapshot_operation_wall_ms": med("operation_wall_ms", "snapshot"),
        "direct_fresh_process_wall_ms": med("fresh_process_wall_ms", "direct"),
        "snapshot_fresh_process_wall_ms": med("fresh_process_wall_ms", "snapshot"),
        "direct_operation_cpu_ms": med("operation_cpu_ms", "direct"),
        "snapshot_operation_cpu_ms": med("operation_cpu_ms", "snapshot"),
        "direct_peak_rss_kib": med("peak_rss_kib", "direct"),
        "snapshot_peak_rss_kib": med("peak_rss_kib", "snapshot"),
    }
    summary["operation_wall_ratio"] = summary["snapshot_operation_wall_ms"] / summary["direct_operation_wall_ms"]
    summary["peak_rss_delta_kib"] = summary["snapshot_peak_rss_kib"] - summary["direct_peak_rss_kib"]
    summary["snapshot_written_bytes_per_operation"] = len(image)
    summary["source_copy_read_bytes_per_operation"] = len(image)
    summary["economic_classification"] = (
        "COSTLY_BOUNDARY" if len(original) >= 4 * 1024 * 1024
        and (summary["operation_wall_ratio"] > 3
             or summary["peak_rss_delta_kib"] > 10 * 1024)
        else "BOUNDED_IN_THIS_SCIENTIFIC_TEST"
    )
    return {"summary": summary, "raw": records}


def main() -> dict:
    tiny = (b"source-lifetime-pack-A:" * 4)[:64] + (b"source-lifetime-pack-B:" * 4)[:64]
    large = hashlib.shake_256(b"cmpct-O24-private-snapshot").digest(4 * 1024 * 1024)
    assert len(tiny) == 128 and len(large) == 4 * 1024 * 1024
    cases = [
        ("micro_pack_128", True, tiny),
        ("direct_raw_128", False, tiny),
        ("pack_4mib", True, large),
        ("direct_raw_4mib", False, large),
    ]
    with tempfile.TemporaryDirectory(prefix="cmpct-o24-") as dirname:
        root = Path(dirname)
        mutations, costs = {}, {}
        for name, packed, original in cases:
            altered = original[:-1] + bytes([original[-1] ^ 1])
            mutations[name] = test_mutation(root, name, packed, original, altered)
            costs[name] = cost_court(root, name, packed, original)
    return {
        "status": "PASS",
        "scientific_decision": "PRIVATE_SNAPSHOT_SUFFICES_FOR_TESTED_POSTCOPY_SOURCE_REWRITE",
        "scope": "RESEARCH_NOT_PRODUCT_PROMOTION",
        "base_pr": 376,
        "parent_source_sha": "3493f4e3cfbad6c295161f63ec163a6b78d60692",
        "mutations": mutations,
        "costs": costs,
        "limitations": [
            "Source is mutated after completed copy, not during copy",
            "No externally signed authenticity or immutable-source guarantee",
            "No crash-atomic whole-tree publication or hostile destination safety proof",
            "Private source copied in full; no product Reader source modification",
            "Linux CPython 3.11 scoped results; no Windows/macOS/native claim",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--mode", choices=("direct", "snapshot"))
    parser.add_argument("--expected")
    parser.add_argument("--packed", action="store_true")
    parser.add_argument("--out", type=Path)
    opts = parser.parse_args()
    if opts.child:
        child_main(opts)
    else:
        result = main()
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if opts.out:
            opts.out.parent.mkdir(parents=True, exist_ok=True)
            opts.out.write_text(payload, encoding="utf-8")
        print(payload)
