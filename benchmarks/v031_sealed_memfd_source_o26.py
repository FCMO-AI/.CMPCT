#!/usr/bin/env python3
"""O26 scientific oracle: kernel-sealed Linux memfd as immutable CMPCT source.
No product or format changes. Parent experiment O24 remains independent.
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import math
import mmap
import os
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cmpct.reader import CMPCT
from v031_pack_physical_sha_court import archive_bytes
from v031_verify_extract_source_lifetime_o23 import digest, in_place, must_reject_sha, view
from v031_private_verified_snapshot_o24 import snapshot

FLAGS = (fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW |
         fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
BLOCK = 1024 * 1024
PAGE = os.sysconf("SC_PAGE_SIZE")


def sealed_copy(source: Path) -> tuple[int, int]:
    """Create *independent* full archive copy, then make kernel reject further writes."""
    fd = os.memfd_create("cmpct-o26-source", os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
    written = 0
    try:
        with source.open("rb") as stream:
            while chunk := stream.read(BLOCK):
                at = 0
                while at < len(chunk):
                    n = os.write(fd, chunk[at:])
                    if n <= 0:
                        raise OSError("short memfd write")
                    at += n
                written += len(chunk)
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, FLAGS)
        got = fcntl.fcntl(fd, fcntl.F_GET_SEALS)
        if got & FLAGS != FLAGS:
            raise AssertionError("missing memfd seal bits")
        if os.fstat(fd).st_size != written:
            raise AssertionError("snapshot length mismatch")
        return fd, written
    except BaseException:
        os.close(fd)
        raise


def proc_path(fd: int) -> Path:
    return Path(f"/proc/self/fd/{fd}")


def hash_fd(fd: int) -> str:
    h = hashlib.sha256()
    offset = 0
    while block := os.pread(fd, BLOCK, offset):
        h.update(block)
        offset += len(block)
    return h.hexdigest()


def deny_write(fd: int) -> dict:
    """Check actual access to the inherited kernel FD and independently reopened proc FD."""
    errors = {}
    for label, action in (
        ("owner_pwrite", lambda: os.pwrite(fd, b"!", 0)),
        ("owner_truncate", lambda: os.ftruncate(fd, 0)),
    ):
        try:
            action()
        except OSError as exc:
            errors[label] = exc.errno
        else:
            raise AssertionError(f"sealed memfd accepted {label}")
    child_code = (
        "import errno,json,os,sys; "
        "fd=int(sys.argv[1]); other=sys.argv[2]; out={}; "
        "exec('for label,fn in [(\"inherited_pwrite\",lambda: os.pwrite(fd,b\"!\",0)),"
        "(\"reopened_pwrite\",lambda: os.pwrite(os.open(other,os.O_RDWR),b\"!\",0))]:\\n"
        " try: fn(); out[label]=0\\n except OSError as e: out[label]=e.errno\\n'); "
        "print(json.dumps(out))"
    )
    child = subprocess.run(
        [sys.executable, "-c", child_code, str(fd),
         f"/proc/{os.getpid()}/fd/{fd}"],
        pass_fds=(fd,), capture_output=True, text=True, check=True,
    )
    child_results = json.loads(child.stdout)
    errors.update(child_results)
    for label, code in errors.items():
        if code not in (errno.EPERM, errno.EACCES):
            raise AssertionError(f"unproven seal refusal {label}: errno={code}")
    if "reopened_pwrite" not in errors:
        raise AssertionError("child reopening control was omitted")
    return errors



def mapping_seal_court(fd: int) -> dict:
    """Different syscall root: shared map refused, private COW map cannot change inode."""
    # Positive control distinguishes unsupported mmap from a seal-specific denial.
    control = os.memfd_create("cmpct-o26-unsealed-control", os.MFD_ALLOW_SEALING)
    try:
        os.write(control, b"unsealed control")
        with mmap.mmap(control, 1, flags=mmap.MAP_SHARED,
                       prot=mmap.PROT_READ | mmap.PROT_WRITE) as mapping:
            mapping[0:1] = b"U"
        assert os.pread(control, 1, 0) == b"U", "unsealed shared mmap not writable"
    finally:
        os.close(control)

    try:
        with mmap.mmap(fd, 1, flags=mmap.MAP_SHARED,
                       prot=mmap.PROT_READ | mmap.PROT_WRITE) as mapping:
            mapping[0:1] = b"!"
    except OSError as exc:
        shared_errno = exc.errno
    else:
        raise AssertionError("sealed archive accepted writable shared mmap")
    if shared_errno not in (errno.EPERM, errno.EACCES):
        raise AssertionError(f"mmap failed for wrong reason: errno={shared_errno}")

    before = hash_fd(fd)
    with mmap.mmap(fd, 1, flags=mmap.MAP_PRIVATE,
                   prot=mmap.PROT_READ | mmap.PROT_WRITE) as mapping:
        first = mapping[0:1]
        mapping[0:1] = bytes([first[0] ^ 1])
        assert mapping[0:1] != first, "private mapping did not change"
    assert hash_fd(fd) == before, "private COW mapping altered sealed source"
    return {
        "unsealed_shared_mapping_writable": True,
        "sealed_shared_mapping_denied_errno": shared_errno,
        "private_mapping_copy_on_write": True,
        "sealed_source_digest_preserved": True,
    }


def mutation_case(root: Path, name: str, packed: bool, original: bytes) -> dict:
    mutant = original[:-1] + bytes([original[-1] ^ 1])
    good = archive_bytes(original, original, packed=packed)
    bad = archive_bytes(original, mutant, packed=packed)
    if len(good) != len(bad) or good == bad:
        raise AssertionError("invalid same-size authenticated mutation court")
    path = root / (name + "-mutable.cmpct")
    path.write_bytes(good)
    initial = path.stat()
    fd, copied = sealed_copy(path)
    try:
        assert copied == len(good)
        snapshot_sha = hash_fd(fd)
        assert snapshot_sha == digest(good)
        seals = fcntl.fcntl(fd, fcntl.F_GET_SEALS)
        # First attack the independent sealed clone, not only the original path.
        denial = deny_write(fd)
        assert hash_fd(fd) == snapshot_sha
        with path.open("r+b") as f:
            in_place(f.fileno(), bad)
        after = path.stat()
        assert (initial.st_dev, initial.st_ino, initial.st_size) == (
            after.st_dev, after.st_ino, after.st_size)
        assert digest(path.read_bytes()) == digest(bad)
        assert hash_fd(fd) == snapshot_sha
        assert must_reject_sha(path, packed) == digest(mutant)
        with CMPCT(proc_path(fd)) as reader:
            assert reader.verify() == (2 if packed else 1)
            # O26b: hostile operations at the exact verified->extracted boundary.
            postverify_denial = deny_write(fd)
            postverify_mapping = mapping_seal_court(fd)
            assert hash_fd(fd) == snapshot_sha
            dest = root / (name + "-output")
            reader.extractall(dest, metadata=False)
        restored = view(dest, packed)
        assert restored == original, "sealed source published changed bytes"
        # A late copy of already-stale physical bytes must fail the same SHA court.
        late, late_size = sealed_copy(path)
        try:
            assert late_size == copied
            assert hash_fd(late) == digest(bad)
            assert must_reject_sha(proc_path(late), packed) == digest(mutant)
        finally:
            os.close(late)
        return {
            "case": name, "member_bytes": len(original),
            "archive_bytes": copied, "source_inode_unchanged": True,
            "seal_bits": seals, "required_seal_bits": FLAGS,
            "write_denials": denial,
            "source_sha_original": digest(good),
            "source_sha_changed": digest(bad),
            "sealed_archive_sha": snapshot_sha,
            "output_sha": digest(restored),
            "expected_original_output_sha": digest(original),
            "same_user_write_attempts_rejected": True,
            "postverify_write_denials": postverify_denial,
            "postverify_mapping_control": postverify_mapping,
            "fresh_mutant_sha_rejected": True,
            "late_sealed_clone_sha_rejected": True,
            "memfd_minimum_page_charge": math.ceil(copied / PAGE) * PAGE,
            "copy_read_bytes": copied, "copy_write_bytes": copied,
            "result": "PASS",
        }
    finally:
        os.close(fd)


def timed_child(path: Path, packed: bool, expected: str, mode: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-o26-timed-") as temp:
        folder = Path(temp)
        archive = path
        fd = None
        copied = 0
        t0 = time.perf_counter_ns()
        cpu0 = time.process_time_ns()
        if mode == "disk":
            archive = folder / "private.cmpct"
            copied = snapshot(path, archive)
        elif mode == "memfd":
            fd, copied = sealed_copy(path)
            archive = proc_path(fd)
        try:
            with CMPCT(archive) as reader:
                assert reader.verify() == (2 if packed else 1)
                destination = folder / "restored"
                reader.extractall(destination, metadata=False)
        finally:
            if fd is not None:
                os.close(fd)
        cpu_ms = (time.process_time_ns() - cpu0) / 1e6
        wall_ms = (time.perf_counter_ns() - t0) / 1e6
        result = view(destination, packed)
        assert digest(result) == expected
        return {
            "mode": mode,
            "operation_wall_ms": wall_ms,
            "operation_cpu_ms": cpu_ms,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "archive_bytes": path.stat().st_size,
            "copy_read_bytes": copied, "copy_write_bytes": copied,
            "temp_disk_bytes": copied if mode == "disk" else 0,
            "min_memfd_pages": math.ceil(copied / PAGE) * PAGE if mode == "memfd" else 0,
            "output_sha": digest(result),
        }


def economics(root: Path, name: str, packed: bool, original: bytes) -> dict:
    path = root / (name + "-stable.cmpct")
    image = archive_bytes(original, original, packed=packed)
    path.write_bytes(image)
    expected = digest(original)
    records = []
    # Prospective Latin-square rotation: five blocks of all three arms in fresh processes.
    arms = ("direct", "disk", "memfd")
    for block in range(5):
        order = arms[block % 3:] + arms[:block % 3]
        if block % 2:
            order = tuple(reversed(order))
        for mode in order:
            command = [sys.executable, str(Path(__file__).resolve()),
                       "--child", "--archive", str(path),
                       "--expected", expected, "--mode", mode]
            if packed:
                command.append("--packed")
            start = time.perf_counter_ns()
            run = subprocess.run(command, capture_output=True, text=True, check=True)
            child_wall_ms = (time.perf_counter_ns() - start) / 1e6
            row = json.loads(run.stdout)
            assert row["output_sha"] == expected
            assert row["copy_read_bytes"] == (0 if mode == "direct" else len(image))
            row.update({"block": block, "fresh_process_wall_ms": child_wall_ms})
            records.append(row)
    med = lambda mode, key: statistics.median(
        v[key] for v in records if v["mode"] == mode)
    return {
        "raw": records,
        "medians": {mode: {
            "operation_wall_ms": med(mode, "operation_wall_ms"),
            "operation_cpu_ms": med(mode, "operation_cpu_ms"),
            "fresh_process_wall_ms": med(mode, "fresh_process_wall_ms"),
            "peak_rss_kib": med(mode, "peak_rss_kib"),
        } for mode in arms},
        "archive_bytes": len(image), "samples": len(records),
    }


def main() -> dict:
    tiny = (b"source-lifetime-pack-A:" * 4)[:64] + (
        b"source-lifetime-pack-B:" * 4)[:64]
    large = hashlib.shake_256(b"cmpct-O26-sealed-source").digest(4 * 1024 * 1024)
    cases = [
        ("pack_128", True, tiny), ("raw_128", False, tiny),
        ("pack_4mib", True, large), ("raw_4mib", False, large),
    ]
    assert len(tiny) == 128
    with tempfile.TemporaryDirectory(prefix="cmpct-o26-") as d:
        root = Path(d)
        observations = {}
        costs = {}
        for label, packed, original in cases:
            observations[label] = mutation_case(root, label, packed, original)
            costs[label] = economics(root, label, packed, original)
    return {
        "status": "PASS", "scientific_scope": "LINUX_SEALED_SOURCE_ONLY",
        "interpretation": "SEALED_MEMFD_PREVENTED_TESTED_POSTCOPY_SOURCE_REWRITES",
        "platform": {"kernel": os.uname().release, "page_bytes": PAGE,
                     "python": sys.version.split()[0]},
        "cases": observations, "economics": costs,
        "limits": [
            "Full N-byte independent archive copy and at least N bytes of tmpfs-backed pages",
            "No consistent-cut proof when original changes during copy",
            "No safe destination tree, atomic whole-tree publication or crash recovery claim",
            "No provenance signature, privileged process-control adversary or cross-platform claim",
            "No release or product performance credit",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--mode", choices=("direct", "disk", "memfd"))
    parser.add_argument("--packed", action="store_true")
    parser.add_argument("--expected", type=str)
    parser.add_argument("--out", type=Path)
    opts = parser.parse_args()
    if opts.child:
        print(json.dumps(timed_child(opts.archive, opts.packed, opts.expected, opts.mode),
                         sort_keys=True))
    else:
        payload = json.dumps(main(), indent=2, sort_keys=True) + "\n"
        if opts.out:
            opts.out.parent.mkdir(parents=True, exist_ok=True)
            opts.out.write_text(payload)
        print(payload)
