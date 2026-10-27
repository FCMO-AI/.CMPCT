"""J24R01 source-exact ABBA oracle: genuine installed Reader, same physical r24 archives.

Micro/selected-range research evidence only. Does NOT stand in for official release parity.
Use --worker for a fresh process, from an external directory with target PYTHONPATH.
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


def make_fixtures(repo: Path, directory: Path):
    source = repo / "tests/test_o212_sparse_admission.py"
    spec = importlib.util.spec_from_file_location("_j24r01_original_wire_oracle", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = {}
    for count in (1, 4, 4096, 65536):
        stride = 16
        logical = (b"ABCD" + b"\0" * (stride-4)) * (count-1) + b"ABCD"
        extent_rows = [[i*stride, 4, [0]] for i in range(count)]
        wire = module._archive_bytes(extent_rows, logical)
        path = directory / f"{count}.cmpct"
        path.write_bytes(wire)
        oracle = directory / f"{count}.truth"
        oracle.write_bytes(logical)
        manifest[count] = {
            "wire_bytes": len(wire),
            "wire_sha256": hashlib.sha256(wire).hexdigest(),
            "logical_bytes": len(logical),
            "logical_sha256": hashlib.sha256(logical).hexdigest(),
            "wire_path": str(path),
            "truth_path": str(oracle),
        }
    return manifest


def worker(archive: Path, expected: Path, source: str, count: int, iteration: int):
    # This interpreter is started outside the checkout. Only PYTHONPATH chooses installed source.
    import cmpct.reader as module
    from cmpct.reader import CMPCT
    try:
        import resource
    except ImportError:
        resource = None
    truth = expected.read_bytes()
    read_module_path = Path(module.__file__).resolve()
    source_sha = hashlib.sha256(read_module_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    t0 = time.perf_counter_ns(); c0 = time.process_time_ns()
    reader = CMPCT(archive)
    open_wall = (time.perf_counter_ns()-t0)/1e6
    open_cpu = (time.process_time_ns()-c0)/1e6
    try:
        positions = [
            max(0, len(truth)-4),
            max(0, len(truth)-3),
            max(0, len(truth)-2),
            max(0, len(truth)-1),
            max(0, len(truth)-16),
            max(0, len(truth)-8),
            max(0, len(truth)-20),
            max(0, len(truth)-32),
        ]
        # A late, tiny query reveals the O(E) metadata work without exporting decode cost.
        queries = [(positions[i%len(positions)], 1) for i in range(256)]
        for pos, n in queries:
            got = reader.read_range("sparse.bin", pos, n)
            if got != truth[pos:pos+n]:
                raise AssertionError((source, count, pos, got.hex()))
        t1 = time.perf_counter_ns(); c1 = time.process_time_ns()
        for pos, n in queries:
            got = reader.read_range("sparse.bin", pos, n)
            if got != truth[pos:pos+n]:
                raise AssertionError((source, count, pos, got.hex()))
        read_wall = (time.perf_counter_ns()-t1)/1e6
        read_cpu = (time.process_time_ns()-c1)/1e6
        # Different sparse positions; scan-independent correctness, not selectively cherry-picked.
        for pos in (0, 1, 3, 4, 8, len(truth)//2, len(truth)-1):
            for n in (0, 1, min(11, len(truth)-pos)):
                if pos+n <= len(truth):
                    assert reader.read_range("sparse.bin",pos,n) == truth[pos:pos+n]
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource else None
    finally:
        reader.close()
    return {
        "version": source, "extent_count": count, "iteration": iteration,
        "reader_module": str(read_module_path), "reader_source_sha256": source_sha,
        "open_wall_ms": open_wall, "open_cpu_ms": open_cpu,
        "range_batch_wall_ms": read_wall, "range_batch_cpu_ms": read_cpu,
        "peak_rss_host_units": rss,
        "archive_bytes": archive.stat().st_size, "logical_bytes": len(truth),
        "range_checks": 256 + 256 + 21,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--archive")
    p.add_argument("--truth")
    p.add_argument("--source")
    p.add_argument("--count", type=int)
    p.add_argument("--iteration", type=int, default=0)
    p.add_argument("--repo")
    p.add_argument("--base-site")
    p.add_argument("--candidate-site")
    p.add_argument("--out")
    args = p.parse_args()
    if args.worker:
        print(json.dumps(worker(Path(args.archive),Path(args.truth),args.source,args.count,args.iteration),sort_keys=True))
        return
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    observations = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24r01-") as td:
        directory = Path(td)
        fixtures = make_fixtures(repo,directory)
        # New Python interpreter with cwd outside source avoids accidental checkout imports.
        script = directory / "worker.py"
        script.write_bytes(Path(__file__).read_bytes())
        sites = {"baseline":Path(args.base_site).resolve(),"candidate":Path(args.candidate_site).resolve()}
        for iteration in range(3):
            for count in (1, 4, 4096, 65536):
                order = ("baseline","candidate","candidate","baseline") if iteration%2 == 0 else ("candidate","baseline","baseline","candidate")
                for source in order:
                    env = dict(os.environ)
                    env["PYTHONPATH"] = str(sites[source])
                    cmd = [sys.executable,str(script),"--worker","--archive",fixtures[count]["wire_path"],
                           "--truth",fixtures[count]["truth_path"],"--source",source,
                           "--count",str(count),"--iteration",str(iteration)]
                    completed = subprocess.run(cmd,cwd=directory,env=env,check=True,
                                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120)
                    observations.append(json.loads(completed.stdout.strip()))
    grouped = {}
    for count in (1,4,4096,65536):
        grouped[str(count)] = {}
        for source in ("baseline","candidate"):
            obs = [o for o in observations if o["extent_count"]==count and o["version"]==source]
            grouped[str(count)][source] = {
                name: statistics.median(o[name] for o in obs)
                for name in ("open_wall_ms","open_cpu_ms","range_batch_wall_ms","range_batch_cpu_ms")
            }
    speedup = grouped["65536"]["baseline"]["range_batch_wall_ms"]/max(1e-12,grouped["65536"]["candidate"]["range_batch_wall_ms"])
    decision = "SELECTIVE_HEADROOM_CONFIRMED" if speedup>=10 else "SELECTIVE_HEADROOM_NOT_CONFIRMED"
    result = {"schema":"j24r01-v1","decision":decision,"late_65536_speedup":speedup,
              "fixture_manifest":fixtures,"observations":observations,"medians":grouped,
              "limitations":["micro/selected-range only", "full-product parity not measured",
                             "source SHA must be verified against Git in hosted workflow",
                             "host RSS units depend on operating system"]}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("J24R01_DECISION="+decision,flush=True)
    print("J24R01_65536_MEDIAN_SPEEDUP="+format(speedup,".3f"),flush=True)
    print("J24R01_RAW_OBSERVATIONS="+str(len(observations)),flush=True)


if __name__ == "__main__":
    main()
