#!/usr/bin/env python3
"""J24C12: independent installed-source release/strict/ABI3 Reader triplet.

Science only. Same Builder-free signed r24 bytes, independent virtualenvs,
same logical operations; stronger admission semantics are NOT attributed to
the released source. Startup and installation are recorded separately.
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

SOURCES = {
    "released": {"commit": "80c358f8824ec1b20d349c92ed94c898090969b0",
                 "reader_blob": "e716233403dabd0966863c45635e18fa5ac6afb8"},
    "strict": {"commit": "0a128ff55c7ae0f14c6bdf019a81b40f0d894eff",
               "reader_blob": "b37b786966ac1506a0439567d4a58eea472d85f8"},
    "native": {"commit": "a639570c1e9f9b36decae3893265be74a6d185b0",
               "reader_blob": "9bca5d1047f9c78984b945d7ca90e3149fe429ab"},
}
PROFILES = ((4096, 1), (65536, 1), (65536, 256), (262144, 1))
CYCLES = 3
REPEATS = 3
SEQUENCES = (("released", "strict", "native", "native", "strict", "released"),
             ("native", "strict", "released", "released", "strict", "native"))


def git_blob(data: bytes) -> str:
    if b"\r" in data.replace(b"\r\n", b""):
        raise ValueError("non-transport carriage return in installed source")
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_info(arm: str) -> dict:
    from cmpct import reader as reader_module
    path = Path(inspect.getfile(reader_module)).resolve()
    if "site-packages" not in path.parts and "dist-packages" not in path.parts:
        raise RuntimeError("source checkout imported rather than wheel: " + str(path))
    actual = git_blob(path.read_bytes())
    if actual != SOURCES[arm]["reader_blob"]:
        raise RuntimeError("installed Reader blob drift " + arm + ": " + actual)
    return {"reader_blob": actual, "reader_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "reader_path": str(path), "arm": arm, "source_commit": SOURCES[arm]["commit"]}


def highwater() -> int | None:
    if sys.platform != "linux":
        return None
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) * 1024
    except OSError:
        return None
    return None


def one_session(path: Path, fixture: dict) -> dict:
    from cmpct.reader import CMPCT
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(path) as rd:
        t1, c1 = time.perf_counter_ns(), time.process_time_ns()
        names = tuple(rd.by)
        assert names == ("fixed.bin",), names
        t2, c2 = time.perf_counter_ns(), time.process_time_ns()
        digest = hashlib.sha256()
        for at, hx in fixture["ranges"]:
            data = rd.read_range("fixed.bin", at, 16)
            if data.hex() != hx:
                raise AssertionError("incorrect range bytes: " + str(at))
            digest.update(data)
        t3, c3 = time.perf_counter_ns(), time.process_time_ns()
        if fixture["count"] == 4096:
            full = rd.read("fixed.bin")
            if hashlib.sha256(full).hexdigest() != fixture["logical_sha256"]:
                raise AssertionError("complete member mismatch")
            if rd.verify() != 1:
                raise AssertionError("full SHA verification failed")
        t4, c4 = time.perf_counter_ns(), time.process_time_ns()
    t5, c5 = time.perf_counter_ns(), time.process_time_ns()
    d = {}
    for name, lo, hi, cl, ch in (
        ("open", t0, t1, c0, c1), ("list", t1, t2, c1, c2),
        ("ranges", t2, t3, c2, c3), ("full_verify", t3, t4, c3, c4),
        ("close", t4, t5, c4, c5)):
        d[name + "_wall_ns"] = hi - lo
        d[name + "_cpu_ns"] = ch - cl
    d["session_wall_ns"] = t5 - t0
    d["session_cpu_ns"] = c5 - c0
    d["range_sha256"] = digest.hexdigest()
    return d


def worker(archive: Path, fixture_file: Path, arm: str) -> None:
    if arm not in SOURCES:
        raise ValueError("unregistered source arm")
    fixture = json.loads(fixture_file.read_text())
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive_sha != fixture["archive_sha256"]:
        raise AssertionError("signed wire drift")
    source = source_info(arm)
    native_calls = 0
    from cmpct.reader import CMPCT
    if arm == "native":
        import cmpct._chunk_admission as admission
        original = admission._scan_refs
        if original is None:
            raise RuntimeError("ABI3 absent: native arm cannot silently be strict")
        def counted(*args):
            nonlocal native_calls
            native_calls += 1
            return original(*args)
        admission._scan_refs = counted
        try:
            with CMPCT(archive) as rd:
                if not original(rd.files[0][6][1], rd.index["blobs"], rd.files[0][4]):
                    raise RuntimeError("native scanner rejected authentic geometry")
        finally:
            admission._scan_refs = original
        if native_calls != 1:
            raise RuntimeError("optional scanner never engaged in actual Reader open")
    else:
        # Matching untimed metadata/page warm-up; no native hook on these sources.
        with CMPCT(archive) as rd:
            assert len(rd.files) == 1
    samples = [one_session(archive, fixture) for _ in range(REPEATS)]
    print(json.dumps({
        "arm": arm, "source": source, "archive_sha256": archive_sha,
        "count": fixture["count"], "owners": fixture["owners"],
        "native_probe_calls": native_calls, "rss_highwater_bytes": highwater(),
        "samples": samples,
    }, sort_keys=True))


def controller(output: Path, python_bins: dict) -> None:
    for arm, py in python_bins.items():
        if not Path(py).is_file():
            raise RuntimeError("missing isolated venv interpreter " + arm + ": " + py)
    # Builder-free O215 fixture generation is a preexisting independently serialized
    # archive writer, not a call to any of the three product Builders under test.
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tests"))
    from test_o215_fixed_chunk_admission import _make_archive

    fixture_dir = output.resolve().parent / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixtures = []
    workers = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c12-cwd-") as cwd:
        for count, owners in PROFILES:
            chunks = tuple(bytes((65 + i % 23, 66, 67, 68)) for i in range(owners))
            references = [i % owners for i in range(count)]
            logical = b"".join(chunks[i] for i in references)
            wire = _make_archive(references, logical, blobs=chunks)
            archive = fixture_dir / f"r24-{count}-{owners}.cmpct"
            fixture_file = fixture_dir / f"r24-{count}-{owners}.json"
            archive.write_bytes(wire)
            offsets = (0, 8, len(logical)//2-16, len(logical)//2,
                       len(logical)-32, len(logical)-16)
            fixture = {
                "count": count, "owners": owners, "archive_bytes": len(wire),
                "logical_bytes": len(logical), "archive_sha256": hashlib.sha256(wire).hexdigest(),
                "logical_sha256": hashlib.sha256(logical).hexdigest(),
                "ranges": [(pos, logical[pos:pos+16].hex()) for pos in offsets],
                "archive": archive.name, "spec": fixture_file.name,
            }
            fixture_file.write_text(json.dumps(fixture, sort_keys=True) + "\n")
            fixtures.append(fixture)
            for cycle in range(CYCLES):
                sequence = SEQUENCES[cycle % 2]
                for slot, arm in enumerate(sequence):
                    t0 = time.perf_counter_ns()
                    call = subprocess.run(
                        [python_bins[arm], str(Path(__file__).resolve()), "--worker",
                         str(archive), str(fixture_file), arm],
                        text=True, capture_output=True, cwd=cwd, timeout=120,
                    )
                    spawn_elapsed = time.perf_counter_ns() - t0
                    if call.returncode:
                        raise RuntimeError(
                            f"J24C12 {count}/{owners} cycle={cycle} slot={slot} arm={arm}"
                            f" failed: {call.stdout[-1200:]} {call.stderr[-2000:]}"
                        )
                    row = json.loads(call.stdout)
                    row.update({"cycle": cycle, "slot": slot, "process_wall_ns": spawn_elapsed})
                    workers.append(row)
            print(f"J24C12_COMPLETE {count} refs, {owners} owners, workers={len(workers)}", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema": "cmpct-j24c12-released-reader-triplet-v1",
        "evidence_head": os.environ.get("EVIDENCE_SHA", "unbound-local"),
        "platform": sys.platform, "python": sys.version,
        "source_refs": SOURCES, "fixtures": fixtures, "workers": workers,
        "decision": {"floor_wall_ratio": 1.05, "floor_wall_extra_ms": 3.0,
                     "floor_cpu_ratio": 1.05, "floor_cpu_extra_ms": 3.0,
                     "rss_extra_bytes": 8 * 1024 * 1024},
        "limits": ["valid signed r24 fixed RAW S_CHUNKS only; no safety equivalence",
                   "non-editable isolated wheels; process spawn not part of session",
                   "3 hosts and full release matrix not claimed; Linux only"],
    }, sort_keys=True, indent=2) + "\n")
    print(f"J24C12_WORKERS={len(workers)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path)
    p.add_argument("--released-python")
    p.add_argument("--strict-python")
    p.add_argument("--native-python")
    p.add_argument("--worker", nargs=3)
    args = p.parse_args()
    if args.worker:
        worker(Path(args.worker[0]), Path(args.worker[1]), args.worker[2])
    else:
        if args.output is None or not all(
            (args.released_python, args.strict_python, args.native_python)):
            p.error("--output, --released-python, --strict-python, --native-python required")
        controller(args.output, {
            "released": args.released_python, "strict": args.strict_python,
            "native": args.native_python,
        })
