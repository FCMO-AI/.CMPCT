#!/usr/bin/env python3
"""J24F08: Linux kernel VmHWM court for authentic J24F04 vs J24F05 RAW extraction.

Research-only sidecar to J24F06. Source-exact original Readers and fixtures,
fresh exec'd subprocesses, kernel /proc metrics (not inherited ru_maxrss).
"""
from __future__ import annotations

import argparse
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

from j24f04_raw_chunk_immutable_transfer import independent_revision24
from j24f06_raw_extract_economics import (
    BASE_COMMIT, BASE_READER_BLOB, CHILD_READER_BLOB,
    ROOT, digest_path, git, reader_class, source_identity_check,
)

PARENT_HEAD = "dd01be99ec33e820517f7e54b9beead416b20e19"
PREREG = "202a13484ee567e3cb6cac97d776bbd08e7f3535"
WIN_THRESHOLD_BYTES = 32 * 1024 * 1024


def kernel_memory():
    """Actual Linux process counters from /proc/self/status, all values in bytes."""
    if sys.platform != "linux":
        raise RuntimeError("J24F08 is Linux-only")
    wanted = {"VmHWM", "VmRSS", "RssAnon", "VmPeak"}
    found = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        key, _, tail = line.partition(":")
        if key in wanted:
            words = tail.strip().split()
            if len(words) != 2 or words[1] != "kB":
                raise AssertionError("invalid Linux /proc memory units for " + key)
            found[key] = int(words[0]) * 1024
    if not {"VmHWM", "VmRSS"}.issubset(found) or found["VmHWM"] <= 0:
        raise AssertionError("missing kernel process VmHWM/VmRSS")
    if found["VmHWM"] < found["VmRSS"]:
        raise AssertionError("kernel high-water below current RSS")
    return found


def memory_probe() -> int:
    before = kernel_memory()
    # Fault anonymous 20MiB in a separate process; do not contaminate Reader A/B.
    data = bytearray(20 * 1024 * 1024)
    for j in range(0, len(data), 4096):
        data[j] = 73
    after = kernel_memory()
    increase = after["VmHWM"] - before["VmHWM"]
    if increase < 16 * 1024 * 1024:
        raise AssertionError(f"positive VmHWM probe did not detect resident pages: {increase}")
    print(json.dumps(dict(probe="KERNEL_VMHWM_POSITIVE_CONTROL", before=before,
                          after=after, growth_bytes=increase, pid=os.getpid()),
                     sort_keys=True))
    return 0


def child(args) -> int:
    source = Path(args.original_reader)
    source_identity_check(source, BASE_READER_BLOB)
    cls = reader_class(source, args.arm == "window")
    archive = Path(args.archive)
    if digest_path(archive) != args.archive_sha256:
        raise AssertionError("archive changed before child reader open")
    dest = Path(args.destination)
    dest.mkdir(parents=True, exist_ok=False)

    before = kernel_memory()
    start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    with cls(archive) as reader:
        opened = kernel_memory()
        row = reader.by[args.member]
        if row[6][0] != args.storage_kind or row[4] != args.expected_length:
            raise AssertionError("wrong physical representation or member length")
        if bytes(row[5]).hex() != args.expected_sha256:
            raise AssertionError("wrong authenticated member SHA")
        reader.extractall(dest, metadata=False)
        extracted = kernel_memory()
    cpu_ns = time.process_time_ns() - cpu_start
    wall_ns = time.perf_counter_ns() - start
    closed = kernel_memory()

    highwaters = [s["VmHWM"] for s in (before, opened, extracted, closed)]
    if highwaters != sorted(highwaters):
        raise AssertionError("VmHWM unexpectedly not monotonic")
    target = dest / args.member
    digest = digest_path(target)  # excluded from measured Reader work and VmHWM sample
    size = target.stat().st_size
    if digest != args.expected_sha256 or size != args.expected_length:
        raise AssertionError("incorrect output bytes")
    ru_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = dict(
        arm=args.arm, storage_kind=args.storage_kind, size_mib=args.size_mib,
        source_blob=CHILD_READER_BLOB if args.arm == "window" else BASE_READER_BLOB,
        original_source_commit=BASE_COMMIT,
        head=git("rev-parse", "HEAD"), pid=os.getpid(),
        archive_sha256=args.archive_sha256,
        logical_sha256=args.expected_sha256, output_sha256=digest, output_bytes=size,
        wall_ns=wall_ns, cpu_ns=cpu_ns,
        kernel_before=before, kernel_after_open=opened,
        kernel_after_extract=extracted, kernel_after_close=closed,
        peak_vmhwm_bytes=closed["VmHWM"],
        incremental_vmhwm_bytes=closed["VmHWM"] - before["VmHWM"],
        ru_maxrss_reported_kib=ru_kib,
        ru_vs_kernel_bytes=int(ru_kib) * 1024 - closed["VmHWM"],
        proc_note="VmHWM is kernel child high-water; ru_maxrss is diagnostic only",
        python=sys.version.split()[0],
    )
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


def run_child(base, work, archive, member, kind, original_sha, size, archive_sha, arm, tag):
    receipt = work / f"j24f08-{tag}.json"
    command = [sys.executable, str(Path(__file__).resolve()), "--child",
               "--original-reader", str(base), "--archive", str(archive),
               "--destination", str(work / f"out-{tag}"),
               "--member", member, "--storage-kind", str(kind),
               "--expected-sha256", original_sha, "--expected-length", str(size),
               "--archive-sha256", archive_sha, "--size-mib", str(size // (1024 * 1024)),
               "--arm", arm, "--receipt", str(receipt)]
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
    if p.returncode:
        raise RuntimeError(f"J24F08 child {tag} rc={p.returncode}: {p.stdout[-1200:]} {p.stderr[-2400:]}")
    r = json.loads(receipt.read_text())
    if r["arm"] != arm or r["archive_sha256"] != archive_sha or r["output_sha256"] != original_sha:
        raise AssertionError("misattributed source/archive/output")
    return r


def controller(args) -> int:
    if sys.platform != "linux":
        raise RuntimeError("Linux-only court")
    if git("rev-parse", "HEAD:src/cmpct/reader.py") != CHILD_READER_BLOB:
        raise AssertionError("candidate Reader source drift")
    for predecessor in (BASE_COMMIT, PARENT_HEAD, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", predecessor, "HEAD"],
                       cwd=ROOT, check=True)
    import cmpct.reader as actual
    source_identity_check(Path(actual.__file__), CHILD_READER_BLOB)

    probe = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--probe"],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
    if probe.returncode:
        raise AssertionError("VmHWM positive control failed: " + probe.stderr[-1500:])
    positive = json.loads(probe.stdout.strip().splitlines()[-1])
    records = []
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def save(decision):
        output_path.write_text(json.dumps(dict(
            decision=decision, prereg_sha=PREREG, parent_head=PARENT_HEAD,
            source_whole=BASE_READER_BLOB, source_window=CHILD_READER_BLOB,
            head=git("rev-parse", "HEAD"), host=platform.platform(),
            positive_control=positive, cases=records,
            claim_scope="Linux child /proc VmHWM only; no product promotion",
        ), indent=2, sort_keys=True) + "\n")

    with tempfile.TemporaryDirectory(prefix="j24f08-") as temp:
        work = Path(temp)
        baseline = work / "historical-reader.py"
        baseline.write_bytes(subprocess.check_output(
            ["git", "show", BASE_COMMIT + ":src/cmpct/reader.py"], cwd=ROOT))
        source_identity_check(baseline, BASE_READER_BLOB)

        for size_mib in (16, 64):
            for kind in (1, 5):
                primary = hashlib.shake_256(
                    f"J24F06 exact physical RAW size={size_mib} storage={kind}".encode()
                ).digest(size_mib * 1024 * 1024)
                second = hashlib.shake_256(b"J24F06 independent sidecar").digest(1024)
                expected_sha = hashlib.sha256(primary + second).hexdigest()
                member, raw_archive, _ = independent_revision24([primary, second], kind)
                archive = work / f"j24f08-{size_mib}-{kind}.cmpct"
                archive.write_bytes(raw_archive)
                archive_sha = hashlib.sha256(raw_archive).hexdigest()
                logical_size = len(primary) + len(second)
                del primary, second, raw_archive
                trials = []
                for index, arm in enumerate(("whole", "window", "window", "whole") * 2):
                    result = run_child(baseline, work, archive, member, kind, expected_sha,
                                       logical_size, archive_sha, arm,
                                       f"{size_mib}-{kind}-{index}-{arm}")
                    if result["size_mib"] != size_mib:
                        raise AssertionError("wrong size attribution")
                    trials.append(result)
                if len({row["pid"] for row in trials}) != 8:
                    raise AssertionError("not independent children")
                whole = [row for row in trials if row["arm"] == "whole"]
                window = [row for row in trials if row["arm"] == "window"]
                metrics = {}
                for name in ("peak_vmhwm_bytes", "incremental_vmhwm_bytes",
                             "wall_ns", "cpu_ns", "ru_maxrss_reported_kib"):
                    a = statistics.median(row[name] for row in whole)
                    b = statistics.median(row[name] for row in window)
                    metrics[name] = dict(whole=a, window=b, delta=b - a,
                                         ratio=b/a if a else None)
                gain = -metrics["peak_vmhwm_bytes"]["delta"]
                classification = ("VMHWM_MEMORY_WIN" if size_mib == 64 and
                                  gain >= WIN_THRESHOLD_BYTES else
                                  "NO_CONFIRMED_MEMORY_WIN" if size_mib == 64 else
                                  "SMALL_CASE_REPORTED")
                records.append(dict(size_mib=size_mib, storage_kind=kind,
                                    archive_sha256=archive_sha,
                                    logical_sha256=expected_sha,
                                    logical_bytes=logical_size,
                                    physical_archive_bytes=archive.stat().st_size,
                                    trials=trials, medians=metrics, classification=classification))
                save("PARTIAL_RESULT")
                print("J24F08_CASE", size_mib, kind, classification,
                      json.dumps(metrics["peak_vmhwm_bytes"], sort_keys=True), flush=True)

    expected = [r for r in records if r["size_mib"] == 64]
    decision = ("VMHWM_MEMORY_WIN_BOTH_R24_MODES" if len(expected) == 2 and
                all(x["classification"] == "VMHWM_MEMORY_WIN" for x in expected)
                else "NO_CONFIRMED_BOTH_MODE_MEMORY_WIN")
    save(decision)
    print("J24F08_DECISION=" + decision, flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--original-reader")
    parser.add_argument("--archive")
    parser.add_argument("--destination")
    parser.add_argument("--member")
    parser.add_argument("--storage-kind", type=int)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-length", type=int)
    parser.add_argument("--archive-sha256")
    parser.add_argument("--size-mib", type=int)
    parser.add_argument("--arm", choices=("whole", "window"))
    parser.add_argument("--receipt")
    parser.add_argument("--output", default="j24f08-evidence/result.json")
    args = parser.parse_args()
    if args.probe:
        return memory_probe()
    if args.child:
        return child(args)
    return controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
