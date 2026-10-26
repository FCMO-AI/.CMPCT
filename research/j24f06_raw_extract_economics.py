#!/usr/bin/env python3
"""J24F06: exact-source, same-archive, fresh-process Reader extraction economics.

Measures genuine installed CMPCT r24 Reader open+extract+close (not a codec proxy).
Parent is J24F04 whole-RAW-chunk detached snapshot; candidate is J24F05 64-KiB
owned windows. Both use the same installed package, same physical archive, and
independent Python process high-water RSS. No product mutation or gate changes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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

BASE_COMMIT = "d5aa5cbc1ef1e00b6e3c8c72cdd1598192d563a3"
CHILD_READER_BLOB = "41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e"
BASE_READER_BLOB = "8b5910725260e7b4db155ee0b393eb48a42f7efa"
PREREG = "d4c0c4a48e5584d49c59439d3664c01f0683b074"
ROOT = Path(__file__).resolve().parents[1]


def digest_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_identity_check(source: Path, expected: str) -> None:
    actual = git("hash-object", str(source))
    if actual != expected:
        raise AssertionError(f"incorrect source identity {source}: {actual} != {expected}")


def reader_class(source: Path, is_candidate: bool):
    import cmpct.reader as shipping_reader
    source_identity_check(Path(shipping_reader.__file__), CHILD_READER_BLOB)
    if is_candidate:
        return shipping_reader.CMPCT
    # Import exact original source under a distinct sibling module name, so
    # package-wide support/native components remain identical in both arms.
    name = "cmpct._j24f06_historical_reader"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot import authenticated historical Reader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.CMPCT


def linux_current_resident_bytes():
    """Secondary /proc sample; never substitute for process high-water RSS."""
    if sys.platform != "linux":
        return None
    try:
        pages = int(Path("/proc/self/statm").read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError):
        return None


def worker(args) -> int:
    source = Path(args.base_reader)
    source_identity_check(source, BASE_READER_BLOB)
    cls = reader_class(source, args.arm == "window")
    archive = Path(args.archive)
    dest = Path(args.destination)
    dest.mkdir(parents=True, exist_ok=False)

    observations = dict(calls=0, requested_bytes=0, maximum_write_bytes=0,
                        pre_extract_resident_bytes=None,
                        first_write_resident_bytes=None,
                        last_write_resident_bytes=None)
    original_write = os.write
    def observed_write(fd, payload):
        length = len(payload)
        current = linux_current_resident_bytes()
        if observations["calls"] == 0:
            observations["first_write_resident_bytes"] = current
        observations["last_write_resident_bytes"] = current
        observations["calls"] += 1
        observations["requested_bytes"] += length
        observations["maximum_write_bytes"] = max(observations["maximum_write_bytes"], length)
        return original_write(fd, payload)

    # Instrument only separate control trials. Main timed samples have no
    # Python syscall wrapper and therefore retain genuine Reader timings.
    if args.trace_writes:
        os.write = observed_write
    if args.trace_writes:
        observations["pre_extract_resident_bytes"] = linux_current_resident_bytes()
    start = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    try:
        with cls(archive) as reader:
            row = reader.by[args.member]
            if row[6][0] != args.storage_kind or row[4] != args.expected_length:
                raise AssertionError("wrong archive mode or logical length")
            if bytes(row[5]).hex() != args.expected_sha256:
                raise AssertionError("unexpected index authentication")
            reader.extractall(dest, metadata=False)
    finally:
        os.write = original_write
    cpu_ns = time.process_time_ns() - cpu0
    wall_ns = time.perf_counter_ns() - start

    # True process high-water RSS measured before independent output digest.
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux ru_maxrss is KiB; macOS ru_maxrss is bytes.
    peak_rss_bytes = rss if sys.platform == "darwin" else rss * 1024
    output = dest / args.member
    actual = digest_path(output)
    if actual != args.expected_sha256:
        raise AssertionError(f"non-lossless extraction {actual} != {args.expected_sha256}")
    output_bytes = output.stat().st_size
    if output_bytes != args.expected_length:
        raise AssertionError("non-lossless output size")

    row = dict(
        arm=args.arm, storage_kind=args.storage_kind, logical_length=args.expected_length,
        sha256=actual, archive_sha256=args.archive_sha256, output_bytes=output_bytes,
        wall_ns=wall_ns, cpu_ns=cpu_ns, peak_rss_bytes=peak_rss_bytes,
        trace_writes=args.trace_writes, write_calls=observations["calls"] if args.trace_writes else None,
        write_requested_bytes=observations["requested_bytes"] if args.trace_writes else None,
        max_write_bytes=observations["maximum_write_bytes"] if args.trace_writes else None,
        pre_extract_resident_bytes=observations["pre_extract_resident_bytes"] if args.trace_writes else None,
        first_write_resident_bytes=observations["first_write_resident_bytes"] if args.trace_writes else None,
        last_write_resident_bytes=observations["last_write_resident_bytes"] if args.trace_writes else None,
        source_blob=CHILD_READER_BLOB if args.arm == "window" else BASE_READER_BLOB,
        python=sys.version.split()[0], platform=sys.platform, pid=os.getpid()
    )
    Path(args.result).write_text(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, sort_keys=True))
    return 0


def fresh_worker(script: Path, base: Path, work: Path, archive: Path, member: str,
                 storage: int, expected_sha: str, logical_size: int,
                 archive_sha: str, arm: str, tag: str, trace: bool) -> dict:
    output = work / f"out-{tag}"
    receipt = work / f"result-{tag}.json"
    command = [sys.executable, str(script), "--worker", "--base-reader", str(base),
               "--archive", str(archive), "--destination", str(output),
               "--member", member, "--storage-kind", str(storage),
               "--expected-sha256", expected_sha, "--expected-length", str(logical_size),
               "--archive-sha256", archive_sha, "--arm", arm, "--result", str(receipt)]
    if trace:
        command.append("--trace-writes")
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                          timeout=180)
    if proc.returncode:
        raise RuntimeError(f"worker failure {tag} exit={proc.returncode} stdout={proc.stdout[-2000:]} stderr={proc.stderr[-4000:]}")
    row = json.loads(receipt.read_text())
    if row["sha256"] != expected_sha or row["archive_sha256"] != archive_sha:
        raise AssertionError("worker receipt differs from authenticated input")
    if row["trace_writes"] != trace or row["arm"] != arm:
        raise AssertionError("misattributed worker")
    return row


def median(rows: list[dict], field: str) -> float:
    return statistics.median(row[field] for row in rows)


def controller(args) -> int:
    if git("rev-parse", "HEAD:src/cmpct/reader.py") != CHILD_READER_BLOB:
        raise AssertionError("head no longer equals locked J24F05 product Reader")
    subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
                   cwd=ROOT, check=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
                   cwd=ROOT, check=True)
    import cmpct.reader as shipping_reader
    source_identity_check(Path(shipping_reader.__file__), CHILD_READER_BLOB)
    subprocess.run(["git", "merge-base", "--is-ancestor",
                    "845a2e835c858fd7986cb455bf801a48e30f7610", "HEAD"],
                   cwd=ROOT, check=True)

    all_cases = []
    with tempfile.TemporaryDirectory(prefix="j24f06-") as temporary:
        work = Path(temporary)
        base_source = work / "original-reader.py"
        historical = subprocess.check_output(
            ["git", "show", BASE_COMMIT + ":src/cmpct/reader.py"], cwd=ROOT)
        base_source.write_bytes(historical)
        source_identity_check(base_source, BASE_READER_BLOB)

        for size_mib in (16, 64):
            for storage in (1, 5):
                # Controller fixture creation happens outside all measured
                # workers and is never part of either arm's RSS or wall.
                first = hashlib.shake_256(
                    f"J24F06 exact physical RAW size={size_mib} storage={storage}".encode()
                ).digest(size_mib * 1024 * 1024)
                second = hashlib.shake_256(b"J24F06 independent sidecar").digest(1024)
                expected_sha = hashlib.sha256(first + second).hexdigest()
                member, archive_bytes, _offset = independent_revision24([first, second], storage)
                archive = work / f"real-{size_mib}-{storage}.cmpct"
                archive.write_bytes(archive_bytes)
                archive_sha = hashlib.sha256(archive_bytes).hexdigest()
                del archive_bytes, first, second

                observations = []
                # A B B A twice: fixed source, same runner, independent process.
                sequence = ["whole", "window", "window", "whole"] * 2
                for ordinal, arm in enumerate(sequence):
                    tag = f"{size_mib}-{storage}-{ordinal}-{arm}"
                    observations.append(fresh_worker(
                        Path(__file__).resolve(), base_source, work, archive, member, storage,
                        expected_sha, size_mib*1024*1024+1024, archive_sha, arm, tag, False))
                traced = []
                for arm in ("whole", "window"):
                    tag = f"{size_mib}-{storage}-instrumented-{arm}"
                    traced.append(fresh_worker(
                        Path(__file__).resolve(), base_source, work, archive, member, storage,
                        expected_sha, size_mib*1024*1024+1024, archive_sha, arm, tag, True))
                if any(v["write_requested_bytes"] != size_mib*1024*1024+1024 for v in traced):
                    raise AssertionError("stage write byte accounting incomplete")
                if traced[0]["write_calls"] <= 0 or traced[1]["write_calls"] <= traced[0]["write_calls"]:
                    raise AssertionError("expected extra bounded-window write calls not observed")
                if traced[1]["max_write_bytes"] > 65536:
                    raise AssertionError("window larger than 64KiB")

                whole = [x for x in observations if x["arm"] == "whole"]
                window = [x for x in observations if x["arm"] == "window"]
                summaries = {}
                for metric in ("wall_ns", "cpu_ns", "peak_rss_bytes"):
                    original = median(whole, metric)
                    candidate = median(window, metric)
                    summaries[metric] = dict(whole=original, window=candidate,
                                              delta=candidate-original,
                                              ratio=(candidate/original if original else None))
                all_cases.append(dict(
                    size_mib=size_mib, storage_kind=storage,
                    logical_bytes=size_mib*1024*1024+1024,
                    archive_sha256=archive_sha, logical_sha256=expected_sha,
                    physical_archive_bytes=archive.stat().st_size,
                    timed_trials=observations, trace_controls=traced,
                    medians=summaries))

    # This is a research decision, not a hidden release comparator.
    if not all(len(x["timed_trials"]) == 8 for x in all_cases):
        raise AssertionError("incomplete repeated observations")
    output = dict(
        decision="EXACT_R24_EXTRACTION_A_B_MEASURED_NO_PRODUCT_PROMOTION",
        prereg_sha=PREREG, original_source_sha=BASE_COMMIT,
        original_reader_blob=BASE_READER_BLOB, candidate_reader_blob=CHILD_READER_BLOB,
        head=git("rev-parse", "HEAD"), host=platform.platform(), python=sys.version,
        reported_memory="process peak ru_maxrss converted to bytes (fresh subprocess)",
        timing="Reader open+extract+close; no process startup or independent output hash",
        cases=all_cases)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    for case in all_cases:
        print("J24F06_CASE", case["size_mib"], case["storage_kind"], json.dumps(case["medians"], sort_keys=True))
    print("J24F06_DECISION=" + output["decision"])
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--base-reader")
    parser.add_argument("--archive")
    parser.add_argument("--destination")
    parser.add_argument("--member")
    parser.add_argument("--storage-kind", type=int)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-length", type=int)
    parser.add_argument("--archive-sha256")
    parser.add_argument("--arm", choices=("whole", "window"))
    parser.add_argument("--result")
    parser.add_argument("--trace-writes", action="store_true")
    parser.add_argument("--output", default="j24f06-evidence/result.json")
    args = parser.parse_args()
    return worker(args) if args.worker else controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
