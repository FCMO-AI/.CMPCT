"""J24R03: source-exact, site-isolated sparse locality transfer ABBA.

Research-only: source must be unchanged Reader owners #569/#584, with
identical r24 bytes, read semantics and separate process startup boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

COUNTS = (1, 4, 4096, 65536)
REGIMES = ("front", "middle", "tail", "balanced", "span")


def queries_for(count: int, regime: str, size: int):
    """Fixed position distribution, with no corpus-id dependent tuning."""
    assert regime in REGIMES and size == (count-1)*16+4
    anchors = {"front": 0, "middle": count//2, "tail": count-1}
    queries = []
    for i in range(128):
        if regime == "balanced":
            location = ("front", "middle", "tail")[i % 3]
        elif regime == "span":
            location = "middle"
        else:
            location = regime
        base = 16 * anchors[location]
        offset = (0, 1, 3, 4, 8, 11)[i % 6]
        start = min(size-1, base+offset)
        if regime == "span":
            requested = (16, 64, 256, 512)[i % 4]
        else:
            requested = (1, 4, 12)[i % 3]
        length = min(requested, size-start)
        assert 0 <= start < size and 1 <= length <= size-start
        queries.append((start, length))
    return queries


def manifest_fixtures(repo: Path, destination: Path):
    source = repo / "tests" / "test_o212_sparse_admission.py"
    spec = importlib.util.spec_from_file_location("j24r03_exact_wire", source)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    manifest = {}
    destination.mkdir(parents=True, exist_ok=True)
    for count in COUNTS:
        logical = (b"ABCD" + b"\0" * 12) * (count-1) + b"ABCD"
        extents = [[i*16, 4, [0]] for i in range(count)]
        wire = mod._archive_bytes(extents, logical)
        path = destination / f"sparse-{count}.cmpct"
        truth = destination / f"sparse-{count}.truth"
        path.write_bytes(wire)
        truth.write_bytes(logical)
        manifest[str(count)] = {
            "archive": str(path), "truth": str(truth),
            "archive_bytes": len(wire), "logical_bytes": len(logical),
            "archive_sha256": hashlib.sha256(wire).hexdigest(),
            "logical_sha256": hashlib.sha256(logical).hexdigest(),
        }
    return manifest


def worker(args):
    import cmpct.reader as reader_module
    from cmpct.reader import CMPCT
    try:
        import resource
    except ImportError:
        resource = None
    archive, truth_path = Path(args.archive), Path(args.truth)
    truth = truth_path.read_bytes()
    queries = queries_for(args.count, args.regime, len(truth))
    module_path = Path(reader_module.__file__).resolve()
    source_sha = hashlib.sha256(module_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    reader = CMPCT(archive)
    open_wall = (time.perf_counter_ns()-t0)/1e6
    open_cpu = (time.process_time_ns()-c0)/1e6
    try:
        for start, length in queries:
            got = reader.read_range("sparse.bin", start, length)
            if got != truth[start:start+length]:
                raise AssertionError((args.source, args.count, args.regime, start, length))
        t1, c1 = time.perf_counter_ns(), time.process_time_ns()
        for start, length in queries:
            got = reader.read_range("sparse.bin", start, length)
            if got != truth[start:start+length]:
                raise AssertionError((args.source, args.count, args.regime, start, length))
        read_wall = (time.perf_counter_ns()-t1)/1e6
        read_cpu = (time.process_time_ns()-c1)/1e6
        assert reader.read_range("sparse.bin", len(truth), 0) == b""
        try:
            reader.read_range("sparse.bin", len(truth), 1)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-bounds request admitted")
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource else None
    finally:
        reader.close()
    digest = hashlib.sha256(json.dumps(queries, separators=(",", ":")).encode()).hexdigest()
    return {
        "source": args.source, "extent_count": args.count, "regime": args.regime,
        "round": args.round, "reader_module": str(module_path),
        "reader_source_sha256": source_sha, "archive_bytes": archive.stat().st_size,
        "logical_bytes": len(truth), "query_digest": digest, "query_checks": 258,
        "open_wall_ms": open_wall, "open_cpu_ms": open_cpu,
        "range_wall_ms": read_wall, "range_cpu_ms": read_cpu,
        "own_peak_rss_platform_units": rss,
    }


def court(args):
    repo, out, base_site, candidate_site = [Path(x).resolve() for x in
                                          (args.repo, args.out, args.base_site, args.candidate_site)]
    out.parent.mkdir(parents=True, exist_ok=True)
    fixture_manifest = manifest_fixtures(repo, out.parent / "fixtures")
    sites = {"baseline": base_site, "candidate": candidate_site}
    observations = []
    raw_jl = out.parent / "partial-observations.jsonl"
    with tempfile.TemporaryDirectory(prefix="j24r03-workers-") as td:
        remote = Path(td) / "worker.py"
        remote.write_bytes(Path(__file__).read_bytes())
        for round_ in range(3):
            for count in COUNTS:
                for regime in REGIMES:
                    order = ("baseline", "candidate", "candidate", "baseline") if round_ % 2 == 0 else ("candidate", "baseline", "baseline", "candidate")
                    for source in order:
                        manifest = fixture_manifest[str(count)]
                        env = dict(os.environ)
                        env["PYTHONPATH"] = str(sites[source])
                        cmd = [sys.executable, str(remote), "--worker",
                               "--archive", manifest["archive"], "--truth", manifest["truth"],
                               "--source", source, "--count", str(count),
                               "--regime", regime, "--round", str(round_)]
                        completed = subprocess.run(cmd, cwd=td, env=env, capture_output=True,
                                                   text=True, timeout=180)
                        if completed.returncode:
                            with (out.parent / "worker-failure.log").open("a", encoding="utf-8") as f:
                                f.write(json.dumps({"cmd": cmd, "stdout": completed.stdout,
                                                    "stderr": completed.stderr, "returncode": completed.returncode}) + "\n")
                            raise RuntimeError(f"{source}/{count}/{regime}/{round_} failed: {completed.stderr[-2000:]}")
                        record = json.loads(completed.stdout.strip())
                        observations.append(record)
                        with raw_jl.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(record, sort_keys=True) + "\n")
    medians = {}
    for count in COUNTS:
        medians[str(count)] = {}
        for regime in REGIMES:
            medians[str(count)][regime] = {}
            for source in sites:
                selected = [x for x in observations if x["extent_count"] == count
                            and x["regime"] == regime and x["source"] == source]
                medians[str(count)][regime][source] = {
                    field: statistics.median(v[field] for v in selected)
                    for field in ("open_wall_ms", "open_cpu_ms", "range_wall_ms", "range_cpu_ms")
                }
    result = {"schema": "j24r03-locality-v1", "manifest": fixture_manifest,
              "observations": observations, "medians": medians,
              "limitations": ["Selected range only; no complete official parity",
                              "Linux host only for timing", "Archive size unchanged between versions",
                              "RSS high water is not a per-range delta"]}
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("J24R03_ORIGINAL_OBSERVATIONS="+str(len(observations)), flush=True)
    for count in (4096, 65536):
        for regime in REGIMES:
            group = medians[str(count)][regime]
            speedup = group["baseline"]["range_wall_ms"] / group["candidate"]["range_wall_ms"]
            print(f"J24R03_{count}_{regime}_SPEEDUP={speedup:.3f}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    for flag in ("archive", "truth", "source", "regime", "repo", "base-site", "candidate-site", "out"):
        ap.add_argument("--"+flag)
    ap.add_argument("--count", type=int)
    ap.add_argument("--round", type=int, default=0)
    args = ap.parse_args()
    if args.worker:
        print(json.dumps(worker(args), sort_keys=True))
    else:
        court(args)


if __name__ == "__main__":
    main()
