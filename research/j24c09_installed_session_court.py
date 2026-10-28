#!/usr/bin/env python3
"""J24C09: exact-source installed ABI3 versus strict fallback, actual selective sessions.

Research-only. Source and signed wire are identical between arms. Only the
private native scanner callable is disabled for strict control. Do not present
constructor-only timings as whole-product performance.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

import cmpct.reader as reader_module
import cmpct._chunk_admission as admission
from cmpct.reader import CMPCT

SOURCE_BLOBS = {
    "reader": "9bca5d1047f9c78984b945d7ca90e3149fe429ab",
    "admission": "432e86f73f3f1751c04ccbb0e45858c18531da1d",
}
PROFILES = ((4096, 1), (65536, 1), (65536, 256), (262144, 1))
CYCLES = 3
REPEATS = 3


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def source_info() -> dict:
    reader = Path(inspect.getfile(reader_module)).resolve()
    module = Path(inspect.getfile(admission)).resolve()
    if not any(p in reader.parts for p in ("site-packages", "dist-packages")):
        raise RuntimeError("not an installed Reader wheel: " + str(reader))
    result = {
        "reader_git_blob": git_blob(reader.read_bytes()),
        "admission_git_blob": git_blob(module.read_bytes()),
        "reader_sha256": hashlib.sha256(reader.read_bytes()).hexdigest(),
        "admission_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "installed_path": str(reader),
    }
    for name, digest in SOURCE_BLOBS.items():
        if result[name + "_git_blob"] != digest:
            raise RuntimeError("unexpected installed " + name + " source SHA")
    return result


def high_water_rss() -> int | None:
    if sys.platform == "linux":
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) * 1024
        except OSError:
            return None
    if sys.platform == "darwin":
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except (OSError, ImportError):
            return None
    return None


def one_session(path: Path, spec: dict) -> dict:
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    with CMPCT(path) as reader:
        opened_wall = time.perf_counter_ns()
        opened_cpu = time.process_time_ns()
        names = tuple(reader.by)
        if names != ("fixed.bin",):
            raise AssertionError("unexpected logical index")
        listed_wall = time.perf_counter_ns()
        listed_cpu = time.process_time_ns()

        h = hashlib.sha256()
        for at, expected in spec["ranges"]:
            answer = reader.read_range("fixed.bin", at, 16)
            if answer.hex() != expected:
                raise AssertionError("wrong selective bytes at " + str(at))
            h.update(answer)
        ranged_wall = time.perf_counter_ns()
        ranged_cpu = time.process_time_ns()

        if spec["count"] == 4096:
            full = reader.read("fixed.bin")
            if hashlib.sha256(full).hexdigest() != spec["logical_sha256"]:
                raise AssertionError("wrong full read")
            if reader.verify() != 1:
                raise AssertionError("strong verify rejected valid signed archive")
        verified_wall = time.perf_counter_ns()
        verified_cpu = time.process_time_ns()

    wall_end = time.perf_counter_ns()
    cpu_end = time.process_time_ns()
    return {
        "open_wall_ns": opened_wall - wall0,
        "open_cpu_ns": opened_cpu - cpu0,
        "list_wall_ns": listed_wall - opened_wall,
        "list_cpu_ns": listed_cpu - opened_cpu,
        "ranges_wall_ns": ranged_wall - listed_wall,
        "ranges_cpu_ns": ranged_cpu - listed_cpu,
        "full_verify_wall_ns": verified_wall - ranged_wall,
        "full_verify_cpu_ns": verified_cpu - ranged_cpu,
        "close_wall_ns": wall_end - verified_wall,
        "close_cpu_ns": cpu_end - verified_cpu,
        "session_wall_ns": wall_end - wall0,
        "session_cpu_ns": cpu_end - cpu0,
        "range_digest": h.hexdigest(),
    }


def worker(path: Path, spec_path: Path, mode: str) -> None:
    if mode not in ("strict", "native"):
        raise RuntimeError("unknown arm")
    spec = json.loads(spec_path.read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != spec["archive_sha256"]:
        raise RuntimeError("archive identity mismatch")
    source = source_info()
    if admission._scan_refs is None:
        raise RuntimeError("required installed ABI3 is missing")
    calls = 0
    if mode == "native":
        # Untimed instrument only; timed sessions restore the original function.
        native = admission._scan_refs
        def counted(*args):
            nonlocal calls
            calls += 1
            return native(*args)
        admission._scan_refs = counted
        try:
            with CMPCT(path) as rd:
                if len(rd.files) != 1:
                    raise RuntimeError("invalid engagement probe")
        finally:
            admission._scan_refs = native
        if calls != 1:
            raise RuntimeError("installed native scanner not engaged exactly once")
    else:
        admission._scan_refs = None
        # Equal untimed warm-up for strict arm: otherwise native's engagement
        # probe would give it an extra page-cache/metadata warm-up.
        with CMPCT(path) as rd:
            if len(rd.files) != 1:
                raise RuntimeError("invalid strict engagement control")
    # Retain the exact same source and loaded product; the control only disables
    # its optional native predicate. Each timed session opens its own Reader.
    samples = [one_session(path, spec) for _ in range(REPEATS)]
    print(json.dumps({
        "mode": mode,
        "native_engagement_probe_calls": calls,
        "native_timed": mode == "native",
        "source": source,
        "archive_sha256": spec["archive_sha256"],
        "count": spec["count"],
        "owners": spec["owners"],
        "rss_highwater_bytes": high_water_rss(),
        "samples": samples,
    }, sort_keys=True))


def controller(output: Path) -> None:
    if admission._scan_refs is None:
        raise RuntimeError("actual installed cp311 ABI3 extension required")
    source = source_info()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tests"))
    from test_o215_fixed_chunk_admission import _make_archive

    raw = []
    fixtures = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c09-sessions-") as td:
        td_path = Path(td)
        for count, owners in PROFILES:
            blobs = tuple(bytes((65 + i % 23, 66, 67, 68)) for i in range(owners))
            refs = [i % owners for i in range(count)]
            logical = b"".join(blobs[i] for i in refs)
            wire = _make_archive(refs, logical, blobs=blobs)
            path = td_path / ("signed-" + str(count) + "-" + str(owners) + ".cmpct")
            spec_path = td_path / ("signed-" + str(count) + "-" + str(owners) + ".json")
            offsets = (0, 8, len(logical)//2 - 16, len(logical)//2,
                       len(logical) - 32, len(logical) - 16)
            spec = {
                "count": count, "owners": owners,
                "archive_bytes": len(wire), "logical_bytes": len(logical),
                "archive_sha256": hashlib.sha256(wire).hexdigest(),
                "logical_sha256": hashlib.sha256(logical).hexdigest(),
                "ranges": [(at, logical[at:at+16].hex()) for at in offsets],
            }
            fixtures.append(spec)
            path.write_bytes(wire)
            spec_path.write_text(json.dumps(spec, sort_keys=True))
            for cycle in range(CYCLES):
                sequence = ("strict", "native", "native", "strict") if cycle % 2 == 0 else (
                    "native", "strict", "strict", "native")
                for slot, mode in enumerate(sequence):
                    start = time.perf_counter_ns()
                    p = subprocess.run([
                        sys.executable, str(Path(__file__).resolve()), "--worker",
                        str(path), str(spec_path), mode,
                    ], cwd=td, text=True, capture_output=True, timeout=120)
                    elapsed = time.perf_counter_ns() - start
                    if p.returncode:
                        raise RuntimeError("worker failure " + str((count, owners, cycle, mode))
                                           + " stdout=" + p.stdout[-1500:]
                                           + " stderr=" + p.stderr[-2000:])
                    receipt = json.loads(p.stdout)
                    if receipt["source"] != source:
                        raise RuntimeError("worker source drift")
                    receipt.update({"cycle": cycle, "slot": slot, "process_wall_ns": elapsed})
                    raw.append(receipt)
            print("J24C09_COMPLETE count=" + str(count) + " owners=" + str(owners), flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema": "cmpct-j24c09-installed-selective-session-v1",
        "evidence_head": os.environ.get("EVIDENCE_SHA", "unbound-local"),
        "platform": sys.platform, "python": sys.version, "source": source,
        "fixtures": fixtures, "raw_workers": raw,
        "preregistered": {"large_one_owner_wall_ratio_min": 1.5,
                          "rss_growth_max_bytes": 8 * 1024 * 1024,
                          "cycles": CYCLES, "repeats": REPEATS},
        "limitations": [
            "research product session, not full release/create/extract/update benchmark",
            "full read plus SHA verify only for 4096 refs; high-count full read unmeasured",
            "OS page cache warmed; process spawn separately accounted",
            "RSS unavailable is unknown, not zero",
        ],
    }, sort_keys=True, indent=2) + "\n")
    print("J24C09_WORKERS=" + str(len(raw)) + " SHA=" + source["reader_git_blob"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path)
    p.add_argument("--worker", nargs=3)
    args = p.parse_args()
    if args.worker:
        worker(Path(args.worker[0]), Path(args.worker[1]), args.worker[2])
    else:
        if args.output is None:
            p.error("--output required")
        controller(args.output)
