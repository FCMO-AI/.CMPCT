#!/usr/bin/env python3
"""O205: genuine sparse high-E cold-process strict-admission cost court.

Scientific instrumentation only. No patch to CMPCT product or existing validators.
Prerecorded decision criteria: docs/v031-research/2026-10-26-o205-sparse-admission-cost-prereg.md.
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
import tracemalloc
import traceback

MIB = 1 << 20
GIB = 1 << 30
LOGICAL_SIZE = 4 * GIB
EXPECTED_EXTENTS = 4096
ROUNDS = 8
MODES = ("A", "B", "C", "D")


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * MIB), b""):
            h.update(block)
    return h.hexdigest()


def sparse_extent_geometry(storage, blobs, logical_size):
    """Lower-rung in-memory geometry ONLY; cannot replace strict preflight.

    This conservative oracle enforces exactly the sparse relation at issue #533,
    not general archive policy: no physical-header bounds, index decoding caps,
    generation recovery checks, path aliasing or decompression resource limits.
    """
    from cmpct.codec import S_SPARSE
    if not isinstance(storage, (list, tuple)) or len(storage) != 2 or storage[0] != S_SPARSE:
        raise ValueError("expected sparse storage")
    extents = storage[1]
    if not isinstance(extents, list):
        raise ValueError("extents not array")
    last = 0
    for extent in extents:
        if not isinstance(extent, (list, tuple)) or len(extent) != 3:
            raise ValueError("bad sparse extent")
        off, ln, ids = extent
        if type(off) is not int or type(ln) is not int or off < last or ln < 1:
            raise ValueError("invalid extent position/length or order")
        if off + ln > logical_size or not isinstance(ids, list) or not ids:
            raise ValueError("out-of-bounds extent or empty references")
        accounted = 0
        for idx in ids:
            if type(idx) is not int or idx < 0 or idx >= len(blobs):
                raise ValueError("invalid blob reference")
            actual = blobs[idx][1]
            if type(actual) is not int or actual < 0:
                raise ValueError("invalid blob size")
            accounted += actual
        if accounted != ln:
            raise ValueError("sparse declared extent length disagrees with blob lengths")
        last = off + ln
    return len(extents)


def worker(args):
    # Load the same installed package in all four arms *before* timing begins.
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_module
    from cmpct.validation import preflight_archive
    from cmpct.codec import S_SPARSE

    repo = Path(os.environ["GITHUB_WORKSPACE"])
    assert Path(reader_module.__file__).resolve() != (repo / "src/cmpct/reader.py").resolve()
    installed = Path(reader_module.__file__).read_bytes().replace(b"\r\n", b"\n")
    committed = (repo / "src/cmpct/reader.py").read_bytes().replace(b"\r\n", b"\n")
    assert installed == committed, "installed Reader differs from HEAD"
    archive = args.archive
    got_sha = file_sha(archive)
    assert got_sha == args.archive_sha, "archive changed"

    # Peak is process-level RSS. tracemalloc is additional Python-allocation-only evidence.
    if args.trace_memory:
        tracemalloc.start()
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    if args.mode in ("B", "C"):
        pf = preflight_archive(archive, verify_blob_headers=args.mode == "C")
        assert pf["version"] == 24 and pf["files"] == 1
        assert pf["archive_bytes"] == archive.stat().st_size
    else:
        pf = None
    with CMPCT(archive) as reader:
        assert len(reader.files) == 1
        row = reader.files[0]
        assert row[0] == "sparse.bin" and row[4] == LOGICAL_SIZE
        assert row[6][0] == S_SPARSE
        assert len(row[6][1]) >= 2048
        if args.mode == "D":
            checked = sparse_extent_geometry(row[6], reader.blobs, LOGICAL_SIZE)
            assert checked == len(row[6][1])
        count = len(row[6][1])
    wall = time.perf_counter_ns() - start_wall
    cpu = time.process_time_ns() - start_cpu
    if args.trace_memory:
        _, py_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    else:
        py_peak = None
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux ru_maxrss is KiB; this court only runs Ubuntu.
    return {
        "mode": args.mode,
        "trace_memory": args.trace_memory,
        "wall_ns": wall,
        "cpu_ns": cpu,
        "python_tracemalloc_peak_bytes": py_peak,
        "process_peak_rss_kib": rss,
        "extents": count,
        "archive_sha256": got_sha,
        "installed_reader_normalized_sha256": hashlib.sha256(installed).hexdigest(),
        "strict_preflight": pf,
    }


def physical_extents(path: Path):
    extents = []
    fd = os.open(path, os.O_RDONLY)
    try:
        pos = 0
        while pos < LOGICAL_SIZE:
            try:
                off = os.lseek(fd, pos, os.SEEK_DATA)
            except OSError as exc:
                if exc.errno == 6:  # ENXIO
                    break
                raise
            end = min(LOGICAL_SIZE, os.lseek(fd, off, os.SEEK_HOLE))
            assert pos <= off < end <= LOGICAL_SIZE
            extents.append((off, end - off))
            pos = end
    finally:
        os.close(fd)
    return extents


def run(args):
    if sys.platform != "linux" or not hasattr(os, "pwrite"):
        raise RuntimeError("O205 high-E physical source requires Linux pwrite and SEEK_DATA")
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_module

    repo = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    assert head == os.environ["EVIDENCE_HEAD"], ("not exact HEAD", head, os.environ["EVIDENCE_HEAD"])
    # Receipts are intentionally untracked; require no tracked working-tree source changes.\n    assert subprocess.run(["git", "diff", "--quiet"], cwd=repo, check=False).returncode == 0
    installed = Path(reader_module.__file__).read_bytes().replace(b"\r\n", b"\n")
    source = (repo / "src/cmpct/reader.py").read_bytes().replace(b"\r\n", b"\n")
    assert installed == source and Path(reader_module.__file__).resolve() != (repo / "src/cmpct/reader.py").resolve()

    record = {
        "schema": "cmpct-o205-sparse-admission-cost-v1",
        "source_head": head,
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "source_reader_git_blob": subprocess.check_output(["git","rev-parse","HEAD:src/cmpct/reader.py"],cwd=repo,text=True).strip(),
        "source_validation_git_blob": subprocess.check_output(["git","rev-parse","HEAD:src/cmpct/validation.py"],cwd=repo,text=True).strip(),
        "court_git_blob": subprocess.check_output(["git","rev-parse","HEAD:research/o205_sparse_admission_cost_court.py"],cwd=repo,text=True).strip(),
        "prereg_git_blob": subprocess.check_output(["git","rev-parse","HEAD:docs/v031-research/2026-10-26-o205-sparse-admission-cost-prereg.md"],cwd=repo,text=True).strip(),
        "installed_reader_normalized_sha256": hashlib.sha256(installed).hexdigest(),
        "host": platform.platform(),
        "python": platform.python_version(),
        "product_source_modified": False,
        "requested_logical_bytes": LOGICAL_SIZE,
        "raw_workers": [],
    }

    with tempfile.TemporaryDirectory(prefix="o205-high-e-") as td:
        base = Path(td)
        src = base / "src"
        src.mkdir()
        orig = src / "sparse.bin"
        fd = os.open(orig, os.O_CREAT | os.O_TRUNC | os.O_RDWR, 0o600)
        try:
            os.ftruncate(fd, LOGICAL_SIZE)
            for i in range(EXPECTED_EXTENTS):
                marker = hashlib.blake2s(i.to_bytes(4, "little")).digest()
                written = os.pwrite(fd, marker * 128, i * MIB)
                assert written == 4096
        finally:
            os.close(fd)
        extents = physical_extents(orig)
        physical = orig.stat().st_blocks * 512
        record["source_allocated_bytes"] = physical
        record["source_physical_extents"] = len(extents)
        record["source_physical_extent_total_bytes"] = sum(length for _, length in extents)
        if physical > 64 * MIB or len(extents) < 2048:
            raise RuntimeError("physical sparse source did not retain high-E topology")

        archive = base / "truth-r24.cmpct"
        t = time.perf_counter_ns()
        Builder(src, workers=1).build(archive)
        record["builder_wall_ns"] = time.perf_counter_ns() - t
        record["archive_bytes"] = archive.stat().st_size
        record["archive_sha256"] = file_sha(archive)
        # Strong genuine-Builder and payload controls, outside comparative timed sections.
        with CMPCT(archive) as r:
            assert len(r.files) == 1 and r.files[0][4] == LOGICAL_SIZE
            count = sparse_extent_geometry(r.files[0][6], r.blobs, LOGICAL_SIZE)
            assert count >= 2048, "Builder did not preserve high-E S_SPARSE"
            record["indexed_sparse_extent_count"] = count
            record["range_spot_checks"] = []
            for n in (0, 17, 2048, 4095):
                observed = r.read_range("sparse.bin", n * MIB, 32)
                expected = hashlib.blake2s(n.to_bytes(4, "little")).digest()
                assert observed == expected
                record["range_spot_checks"].append(n)
            assert r.read_range("sparse.bin", 4096, 32) == b"\x00" * 32
            valid_storage = r.files[0][6]
            bad = [list(row) for row in valid_storage[1]]
            bad[0], bad[1] = bad[1], bad[0]
            try:
                sparse_extent_geometry([valid_storage[0], bad], r.blobs, LOGICAL_SIZE)
            except ValueError:
                record["oracle_rejects_unsorted_control"] = True
            else:
                raise AssertionError("geometry oracle accepts deliberately unsorted extents")
            bad = [list(row) for row in valid_storage[1]]
            bad[0][1] = bad[0][1] - 1
            try:
                sparse_extent_geometry([valid_storage[0], bad], r.blobs, LOGICAL_SIZE)
            except ValueError:
                record["oracle_rejects_length_mismatch_control"] = True
            else:
                raise AssertionError("geometry oracle accepts inconsistent declared length")

        for round_idx in range(ROUNDS):
            shift = round_idx % 4
            order = MODES[shift:] + MODES[:shift]
            for mode in order:
                for trace_memory in (False, True):
                    command = [
                        sys.executable, str(Path(__file__).resolve()), "--worker",
                        "--mode", mode, "--archive", str(archive), "--archive-sha", record["archive_sha256"]
                    ]
                    if trace_memory:
                        command.append("--trace-memory")
                    p = subprocess.run(command, cwd=base, capture_output=True, text=True, timeout=120)
                    if p.returncode:
                        raise RuntimeError(f"worker {mode} trace={trace_memory} round {round_idx} failed rc={p.returncode}: {p.stderr[-3000:]}")
                    sample = json.loads(p.stdout.strip().splitlines()[-1])
                    assert sample["mode"] == mode and sample["trace_memory"] is trace_memory
                    assert sample["archive_sha256"] == record["archive_sha256"]
                    assert sample["extents"] == count
                    assert sample["installed_reader_normalized_sha256"] == record["installed_reader_normalized_sha256"]
                    sample["round"] = round_idx
                    record["raw_workers"].append(sample)

        summaries = {}
        traced_summaries = {}
        for mode in MODES:
            for trace_memory, output in ((False, summaries), (True, traced_summaries)):
                xs = [r for r in record["raw_workers"] if r["mode"] == mode and r["trace_memory"] is trace_memory]
                assert len(xs) == ROUNDS
                output[mode] = {
                    "median_wall_ms": statistics.median(r["wall_ns"] for r in xs) / 1e6,
                    "median_cpu_ms": statistics.median(r["cpu_ns"] for r in xs) / 1e6,
                    "median_peak_rss_kib": statistics.median(r["process_peak_rss_kib"] for r in xs),
                    "median_peak_tracemalloc_bytes": statistics.median(r["python_tracemalloc_peak_bytes"] for r in xs) if trace_memory else None,
                    "min_wall_ms": min(r["wall_ns"] for r in xs) / 1e6,
                    "max_wall_ms": max(r["wall_ns"] for r in xs) / 1e6,
                }
        record["summaries"] = summaries
        record["traced_summaries"] = traced_summaries
        record["incremental_full_preflight_wall_ms"] = summaries["C"]["median_wall_ms"] - summaries["A"]["median_wall_ms"]
        record["incremental_full_preflight_peak_rss_kib"] = summaries["C"]["median_peak_rss_kib"] - summaries["A"]["median_peak_rss_kib"]
        record["incremental_geometry_only_wall_ms"] = summaries["D"]["median_wall_ms"] - summaries["A"]["median_wall_ms"]
        if (record["incremental_full_preflight_wall_ms"] <= 30
              and record["incremental_full_preflight_peak_rss_kib"] <= 16 * 1024):
            record["decision"] = "FULL_STRICT_PREFLIGHT_CHEAP_ENOUGH_FOR_NEXT_OWNER_INTEGRATION_TEST"
        elif record["incremental_geometry_only_wall_ms"] <= 5:
            record["decision"] = "PREFER_STUDYING_SHARED_INDEX_TIME_ADMISSION_OVER_DUPLICATE_PREFLIGHT"
        else:
            record["decision"] = "ADMISSION_COST_FORK_AMBIGUOUS"
        record["caveat"] = "Research-scale warm-page-cache Linux process comparison; not complete release/reader open safety or full-product performance."
        return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--trace-memory", action="store_true")
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--archive-sha")
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.worker:
        assert args.archive and args.archive_sha and args.mode
        print(json.dumps(worker(args), sort_keys=True))
        return
    assert args.out
    try:
        result = run(args)
        print("O205_DECISION=" + result["decision"])
    except Exception as exc:
        result = {
            "schema": "cmpct-o205-sparse-admission-cost-v1",
            "decision": "INCONCLUSIVE_INFRA_OR_INSTRUMENT_FAILURE",
            "error": repr(exc), "traceback": traceback.format_exc(),
        }
        print("O205_ERROR=" + repr(exc), file=sys.stderr)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        raise
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
