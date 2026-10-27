#!/usr/bin/env python3
"""J24V03: installed-source, same-wire full sparse verify fresh-process A/B.
Historical control is exact J24V01 PR #613; candidate is a separate stacked Reader patch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

RELEASE = "3b2bf3c2e033fa27d77b2355821dc0087aa46873"
OWNER = "9b4c2dfce9d735e4bb38dc9ca88de4b174c0bdb6"


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        while part := f.read(1024 * 1024):
            digest.update(part)
    return digest.hexdigest()


def own_peak_kib():
    # Unlike RUSAGE_CHILDREN, this is the current process's own kernel peak.
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmHWM:"):
            return int(line.split()[1])
    raise RuntimeError("Linux /proc VmHWM is mandatory for this court")


def physical_fixture(root, size_mib):
    from cmpct.builder import Builder
    from cmpct.codec import K_FILE, K_HARDLINK, S_SPARSE
    from cmpct.reader import CMPCT

    size = size_mib * 1024 * 1024
    src = root / ("input-" + str(size_mib))
    src.mkdir(parents=True, exist_ok=True)
    file = src / "payload.bin"
    # Three nonadjacent, different-size data extents force genuine hole handling.
    with file.open("wb") as f:
        f.seek(1 * 1024 * 1024 + 123)
        f.write(b"start-J24V03" * 61)
        f.seek(size // 2 + 4099)
        f.write(hashlib.sha256(str(size).encode()).digest() * 121)
        f.seek(size - 4096)
        f.write(b"Z" * 4096)
    assert file.stat().st_size == size
    os.link(file, src / 'z-alias.bin')
    target = root / ("sparse-" + str(size_mib) + ".cmpct")
    Builder(src).build(target)
    with CMPCT(target) as reader:
        assert len(reader.files) == 2, reader.files
        assert reader.by['z-alias.bin'][1] == K_HARDLINK
        row = reader.by["payload.bin"]
        assert row[1] == K_FILE and row[6][0] == S_SPARSE, "Builder did not emit S_SPARSE"
        assert row[4] == file.stat().st_size
        assert reader.verify() == 2
    return {
        "size_mib": size_mib,
        "logical_size": file.stat().st_size,
        "logical_sha256": sha_file(file),
        "archive_sha256": sha_file(target),
        "archive_bytes": target.stat().st_size,
        "archive": str(target.resolve()),
        "storage_kind": int(row[6][0]),
        "extent_count": len(row[6][1]),
    }


def worker(a):
    from cmpct.reader import CMPCT
    import cmpct.reader as module

    actual = Path(module.__file__).resolve()
    source = (Path(a.source) / "src" / "cmpct" / "reader.py").resolve()
    assert actual == source, (actual, source)
    assert sha_file(actual) == a.reader_sha, "wrong installed-source Reader"
    assert sha_file(a.archive) == a.archive_sha, "archive mutated across A/B"
    before = own_peak_kib()
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    with CMPCT(Path(a.archive)) as reader:
        row = reader.by["payload.bin"]
        assert row[4] == a.logical_size, "logical length drift"
        assert reader.verify() == 2
    cpu = time.process_time_ns() - cpu0
    wall = time.perf_counter_ns() - wall0
    after = own_peak_kib()
    print(json.dumps({
        "mode": a.mode, "size_mib": a.size_mib,
        "source_path": str(actual), "reader_sha256": a.reader_sha,
        "archive_sha256": a.archive_sha,
        "verified": 2, "logical_size": a.logical_size,
        "cpu_ns": cpu, "wall_ns": wall,
        "before_peak_kib": before, "peak_kib": after,
        "incremental_peak_kib": max(0, after - before),
    }, sort_keys=True))


def court(a):
    root = Path(a.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    candidate, baseline = Path(a.candidate).resolve(), Path(a.baseline).resolve()
    reader_paths = {
        "candidate": candidate / "src" / "cmpct" / "reader.py",
        "baseline": baseline / "src" / "cmpct" / "reader.py",
    }
    source_sha = {mode: sha_file(p) for mode, p in reader_paths.items()}
    assert source_sha["baseline"] != source_sha["candidate"], "invalid identical comparison"
    # Build with *candidate* once, then reuse immutable exact same bytes for both modes.
    sys.path.insert(0, str(candidate / "src"))
    from cmpct.reader import CMPCT
    assert Path(sys.modules[CMPCT.__module__].__file__).resolve() == reader_paths["candidate"]
    fixtures = [physical_fixture(root, mib) for mib in (64, 256)]
    samples = []
    for fixture in fixtures:
        for round_id in range(3):
            for position, mode in enumerate(("baseline", "candidate", "candidate", "baseline")):
                source = candidate if mode == "candidate" else baseline
                args = [
                    sys.executable, str(Path(__file__).resolve()), "worker",
                    "--mode", mode, "--size-mib", str(fixture["size_mib"]),
                    "--source", str(source),
                    "--reader-sha", source_sha[mode],
                    "--archive", fixture["archive"], "--archive-sha", fixture["archive_sha256"],
                    "--logical-size", str(fixture["logical_size"]),
                ]
                env = os.environ.copy()
                env["PYTHONPATH"] = str(source / "src")
                try:
                    result = subprocess.run(args, cwd=root, env=env, capture_output=True,
                                            text=True, timeout=100, check=True)
                except subprocess.CalledProcessError as exc:
                    raise RuntimeError(f"worker failed {mode} {fixture['size_mib']}: {exc.stderr}") from exc
                observation = json.loads(result.stdout.strip())
                observation.update(round=round_id, position=position)
                samples.append(observation)
    summary = {}
    for f in fixtures:
        n = f["size_mib"]
        by = {mode: [x for x in samples if x["size_mib"] == n and x["mode"] == mode]
              for mode in ("baseline", "candidate")}
        summary[str(n)] = {
            mode: {key: statistics.median(x[key] for x in group)
                   for key in ("cpu_ns", "wall_ns", "peak_kib", "incremental_peak_kib")}
            for mode, group in by.items()
        }
    report = {
        "schema": "j24v03-source-exact-sparse-verify-abba-v1",
        "release_commit": RELEASE, "candidate_owner_commit": OWNER,
        "reader_sha256": source_sha, "fixtures": fixtures, "observations": samples,
        "summary": summary, "process_count": len(samples),
        "conclusion": "UNDECIDED_UNTIL_INDEPENDENT_REFEREE"
    }
    (root / "abba-raw.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"process_count": len(samples), "summary": summary}, sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    w = sub.add_parser("worker")
    for name, t in (("mode", str), ("size-mib", int), ("source", str),
                    ("reader-sha", str), ("archive", str), ("archive-sha", str),
                    ("logical-size", int)):
        w.add_argument("--" + name, type=t, required=True)
    c = sub.add_parser("court")
    for name in ("candidate", "baseline", "output"):
        c.add_argument("--" + name, required=True)
    a = p.parse_args()
    if a.command == "worker":
        worker(a)
    else:
        court(a)


if __name__ == "__main__":
    main()
