#!/usr/bin/env python3
"""O10 research-only: same-source/native-ABI eager-all versus 64-KiB stream."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time

from cmpct.builder import Builder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_batch_abi import source_bytes

REPS = 3
LARGE_FILE_SIZE = 256 * 1024


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def child_cpu() -> float:
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    return ru.ru_utime + ru.ru_stime


def prepare(home: Path, cohort: str) -> tuple[Path, dict[str, str], int]:
    source = home / (cohort + "-source")
    source.mkdir()
    expected: dict[str, str] = {}
    if cohort == "pack_512":
        for i in range(512):
            name = f"entry-{i:05d}.txt"
            b = source_bytes(i)
            (source / name).write_bytes(b)
            expected[name] = sha(b)
    else:
        n = int(cohort.removeprefix("raw_"))
        for i in range(n):
            name = f"entry-{i:05d}.bin"
            b = random.Random(51000 + i).randbytes(LARGE_FILE_SIZE)
            (source / name).write_bytes(b)
            expected[name] = sha(b)
    archive = home / (cohort + ".cmpct")
    Builder(source, workers=1, reproducible=True).build(archive)
    assert archive.is_file()
    return archive, expected, sum(f.stat().st_size for f in source.iterdir())


def exact_output(dest: Path, expected: dict[str, str]) -> None:
    actual = {p.name: sha(p.read_bytes()) for p in dest.iterdir()}
    assert actual == expected, (
        "source-exact output disagreement", set(actual) ^ set(expected),
        [(k, actual.get(k), v) for k, v in expected.items() if actual.get(k) != v][:3],
    )


def execute(binary: Path, archive: Path, dest: Path, mode: str) -> dict:
    cpu0 = child_cpu()
    t0 = time.perf_counter_ns()
    args = [str(binary), str(archive), str(dest)]
    if mode == "eager":
        args.append("serial")
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    wall_ms = (time.perf_counter_ns() - t0) / 1e6
    cpu_ms = (child_cpu() - cpu0) * 1000
    assert p.returncode == 0, (mode, p.returncode, p.stderr[:1000])
    line = json.loads(p.stdout.strip())
    assert line["mode"] == ("serial" if mode == "eager" else "stream"), line
    return {**line, "mode": mode, "wall_ms": wall_ms, "cpu_ms": cpu_ms}


def run_hostile_leaf(stream: Path, archive: Path, expected: dict[str, str], home: Path) -> dict:
    dest = home / "symlink-dest"
    dest.mkdir()
    target = home / "outside-canary"
    canary = b"DO-NOT-MODIFY-EXTERNAL-SENTINEL"
    target.write_bytes(canary)
    # All emitted entries are direct root-level paths. One preexisting leaf must
    # be refused, rather than fopen()-following it to an external target.
    first = sorted(expected)[0]
    (dest / first).symlink_to(target)
    p = subprocess.run(
        [str(stream), str(archive), str(dest)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    assert p.returncode != 0, ("hostile existing symlink silently accepted", p.stdout)
    assert target.read_bytes() == canary, "external symlink target overwritten"
    assert (dest / first).is_symlink()
    return {"status": "PASS", "leaf": first, "returncode": p.returncode,
            "external_sha256": sha(canary), "stderr": p.stderr.strip()[:250]}


def main() -> None:
    assert len(sys.argv) == 4, "usage: court O7_EAGER_BINARY O10_STREAM_BINARY RESULT.json"
    eager = Path(sys.argv[1]).resolve()
    stream = Path(sys.argv[2]).resolve()
    receipt = Path(sys.argv[3]).resolve()
    assert eager.is_file() and stream.is_file()
    with tempfile.TemporaryDirectory(prefix="cmpct-o10-") as tmp:
        home = Path(tmp)
        raw: list[dict] = []
        cohorts: dict[str, dict] = {}
        for name in ["raw_16", "raw_64", "raw_128", "pack_512"]:
            archive, expected, logical_bytes = prepare(home, name)
            archive_sha = sha(archive.read_bytes())
            samples = {"eager": [], "stream": []}
            for repeat in range(REPS):
                order = (
                    ["eager", "stream", "stream", "eager"]
                    if repeat % 2 == 0 else
                    ["stream", "eager", "eager", "stream"]
                )
                for trial, mode in enumerate(order):
                    dest = home / f"{name}-{repeat}-{trial}-{mode}"
                    dest.mkdir()
                    row = execute(eager if mode == "eager" else stream, archive, dest, mode)
                    exact_output(dest, expected)
                    assert row["members"] == len(expected)
                    assert row["decoded_bytes"] == logical_bytes
                    row.update(cohort=name, repeat=repeat, trial=trial)
                    samples[mode].append(row)
                    raw.append(row)
                    # Limit disk footprint so the court does not create O(corpus*trials)
                    # retained output data while measuring per-process resource usage.
                    for child in dest.iterdir():
                        child.unlink()
                    dest.rmdir()
            summary = {
                mode: {
                    "median_wall_ms": statistics.median(x["wall_ms"] for x in records),
                    "median_cpu_ms": statistics.median(x["cpu_ms"] for x in records),
                    "median_rss_kib": statistics.median(x["rss_kib"] for x in records),
                    "rss_range_kib": [min(x["rss_kib"] for x in records),
                                      max(x["rss_kib"] for x in records)],
                    "n": len(records),
                } for mode, records in samples.items()
            }
            cohorts[name] = {
                "source_archive_sha256": archive_sha,
                "archive_bytes": archive.stat().st_size,
                "logical_bytes": logical_bytes,
                "files": len(expected),
                "summary": summary,
            }
        # Fail-closed symlink leaf test is not a claim of full-tree atomicity.
        archive, expected, _ = prepare(home, "hostile-source") if False else (
            home / "raw_16.cmpct",
            {f"entry-{i:05d}.bin": "" for i in range(16)},
            0,
        )
        hostile = run_hostile_leaf(stream, archive, expected, home)
        assert len(raw) == len(cohorts) * REPS * 4
        result = {
            "schema": "cmpct-native-bounded-stream-o10-v1",
            "source_head_expected": os.environ.get("EVIDENCE_HEAD", "UNSET"),
            "status": "O10_COURT_COMPLETE",
            "cohorts": cohorts,
            "hostile_leaf": hostile,
            "raw_abba": raw,
            "interpretation": (
                "Research-only root-file public C ABI client. Same source archives "
                "and logical output verified independently; no shipping extractor, "
                "no ABI correctness claim for mutable sources or authenticated RAW whole-file "
                "snapshots, no general purpose filesystem publication semantics."
            ),
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": result["status"], "hostile_leaf": hostile["status"],
                          "summary": {k: v["summary"] for k, v in cohorts.items()}},
                         sort_keys=True))


if __name__ == "__main__":
    main()
