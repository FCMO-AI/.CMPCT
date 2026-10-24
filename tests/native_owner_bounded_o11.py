#!/usr/bin/env python3
"""O11: exact-source public-C owner-bounded vs original eager/group/stream courts.

Not a shipping extractor. Same archive, process-inclusive ABBA, independent
per-file hashes, self-process VmHWM, explicit RAW and multi-owner controls.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
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
from native_pack_stream_o10 import prepare as prepare_o10

REPS = 3
MODES = ("serial_eager", "group_eager", "stream", "owner_bounded")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare_cohort(home: Path, name: str) -> tuple[Path, dict[str, str], int]:
    if name in ("pack_512", "raw_128"):
        return prepare_o10(home, name)
    assert name == "pack_2048"
    source = home / (name + "-source")
    source.mkdir()
    expected = {}
    for i in range(2048):
        member = f"entry-{i:05d}.txt"
        data = source_bytes(i)
        (source / member).write_bytes(data)
        expected[member] = sha(data)
    archive = home / (name + ".cmpct")
    Builder(source, workers=1, reproducible=True).build(archive)
    return archive, expected, sum(p.stat().st_size for p in source.iterdir())


def child_cpu() -> float:
    u = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u.ru_utime + u.ru_stime


def sample(bins: dict[str, Path], mode: str, archive: Path, dest: Path) -> dict:
    if mode in ("serial_eager", "group_eager"):
        args = [str(bins["eager"]), str(archive), str(dest),
                "serial" if mode == "serial_eager" else "group"]
    else:
        args = [str(bins[mode]), str(archive), str(dest)]
    cpu_start = child_cpu()
    begin = time.perf_counter_ns()
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    wall_ms = (time.perf_counter_ns() - begin) / 1e6
    cpu_ms = (child_cpu() - cpu_start) * 1000
    assert p.returncode == 0, (mode, p.returncode, p.stderr[:1500])
    row = json.loads(p.stdout.strip())
    assert row["mode"] == {
        "serial_eager": "serial", "group_eager": "group",
        "stream": "stream", "owner_bounded": "owner_bounded",
    }[mode], row
    assert row["rss_kib"] > 0
    return {"mode": mode, "wall_ms": wall_ms, "cpu_ms": cpu_ms, **row}


def exact_output(dest: Path, expected: dict[str, str]) -> None:
    actual = {p.name: sha(p.read_bytes()) for p in dest.iterdir()}
    assert actual == expected, (
        "byte-exact original source disagreement",
        set(actual) ^ set(expected),
        [(k, actual.get(k), v) for k, v in expected.items()
         if actual.get(k) != v][:3],
    )


def hostile_leaf(binary: Path, archive: Path, home: Path) -> dict:
    dest = home / "hostile-target"
    dest.mkdir()
    outside = home / "external-canary"
    canary = b"O11-EXTERNAL-CANARY-UNTOUCHED"
    outside.write_bytes(canary)
    leaf = "entry-00000.bin"
    (dest / leaf).symlink_to(outside)
    p = subprocess.run([str(binary), str(archive), str(dest)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert p.returncode != 0, ("unsafe existing leaf accepted", p.stdout)
    assert outside.read_bytes() == canary, "symlink canary overwritten"
    assert (dest / leaf).is_symlink()
    return {"status": "PASS", "leaf": leaf, "returncode": p.returncode,
            "external_sha256": sha(canary), "stderr": p.stderr.strip()[:300]}


def main() -> None:
    assert len(sys.argv) == 5, (
        "usage: court O7_EAGER_BINARY O10_STREAM_BINARY O11_OWNER_BINARY RESULT.json"
    )
    binaries = {
        "eager": Path(sys.argv[1]).resolve(),
        "stream": Path(sys.argv[2]).resolve(),
        "owner_bounded": Path(sys.argv[3]).resolve(),
    }
    assert all(p.is_file() for p in binaries.values())
    receipt = Path(sys.argv[4]).resolve()
    with tempfile.TemporaryDirectory(prefix="cmpct-o11-") as tmp:
        home = Path(tmp)
        cohorts: dict[str, dict] = {}
        raw_rows: list[dict] = []
        for name in ("pack_512", "pack_2048", "raw_128"):
            archive, expected, logical_bytes = prepare_cohort(home, name)
            archive_hash = sha(archive.read_bytes())
            archive_size = archive.stat().st_size
            samples = {mode: [] for mode in MODES}
            for rep in range(REPS):
                # Balanced reverse-order blocks include the process startup, actual
                # native ABI, filesystem publication and original-source SHA oracle.
                if rep == 0:
                    order = ("stream", "owner_bounded", "group_eager", "serial_eager",
                             "serial_eager", "group_eager", "owner_bounded", "stream")
                elif rep == 1:
                    order = ("owner_bounded", "stream", "serial_eager", "group_eager",
                             "group_eager", "serial_eager", "stream", "owner_bounded")
                else:
                    order = ("group_eager", "serial_eager", "stream", "owner_bounded",
                             "owner_bounded", "stream", "serial_eager", "group_eager")
                for trial, mode in enumerate(order):
                    dest = home / f"{name}-{rep}-{trial}-{mode}"
                    dest.mkdir()
                    row = sample(binaries, mode, archive, dest)
                    exact_output(dest, expected)
                    assert row["members"] == len(expected), row
                    assert row["decoded_bytes"] == logical_bytes, row
                    if mode == "owner_bounded":
                        assert row["max_staging_bytes"] <= 16 * 1024 * 1024
                        assert row["batched_members"] + row["fallback"] == len(expected)
                        if name.startswith("pack_"):
                            assert row["batch_count"] >= (2 if name == "pack_512" else 3), (
                                "proposed batching mechanism did not actually fire", row
                            )
                            assert row["batched_members"] >= len(expected) - 1
                        else:
                            assert row["batch_count"] == 0 and row["fallback"] == len(expected)
                    if mode == "group_eager" and name.startswith("pack_"):
                        assert row["batch_count"] >= 2
                    row.update(cohort=name, round=rep, trial=trial,
                               archive_sha256=archive_hash)
                    raw_rows.append(row)
                    samples[mode].append(row)
                    # Avoid 32MiB * 24 retained filesystem output beyond current trial.
                    for leaf in dest.iterdir():
                        leaf.unlink()
                    dest.rmdir()
            summary = {
                mode: {
                    "n": len(s),
                    "wall_median_ms": statistics.median(r["wall_ms"] for r in s),
                    "cpu_median_ms": statistics.median(r["cpu_ms"] for r in s),
                    "rss_median_kib": statistics.median(r["rss_kib"] for r in s),
                    "rss_range_kib": [min(r["rss_kib"] for r in s),
                                      max(r["rss_kib"] for r in s)],
                }
                for mode, s in samples.items()
            }
            cohorts[name] = {
                "source_archive_sha256": archive_hash,
                "archive_bytes": archive_size, "logical_bytes": logical_bytes,
                "members": len(expected), "summary": summary,
                "owner_bounded_batches": samples["owner_bounded"][0]["batch_count"],
                "owner_bounded_max_stage": max(r["max_staging_bytes"]
                                                for r in samples["owner_bounded"]),
            }
        raw_archive = home / "raw_128.cmpct"
        hostile = hostile_leaf(binaries["owner_bounded"], raw_archive, home)
        assert len(raw_rows) == len(cohorts) * REPS * 8
        result = {
            "schema": "cmpct-native-owner-bounded-cohort-o11-v1",
            "head": os.environ.get("EVIDENCE_HEAD", "UNSET"),
            "status": "O11_COMPLETE",
            "cohorts": cohorts, "raw_abba": raw_rows,
            "hostile_preexisting_symlink": hostile,
            "interpretation_limit": (
                "Research-only POSIX root-level C consumer; no archive format or native "
                "ABI changes. Full logical source SHA checked separately per trial. "
                "No whole-tree atomicity, cross-process source snapshot, general "
                "filesystem name semantics, authenticated RAW range, or release claim."
            ),
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": result["status"], "summary": {
            key: value["summary"] for key, value in cohorts.items()},
            "hostile": hostile["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
