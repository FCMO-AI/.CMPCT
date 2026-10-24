#!/usr/bin/env python3
"""O7: public-C end-to-end same archive/tree extraction ABBA, exact source only."""
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

REPS = 7


def child_cpu():
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    return ru.ru_utime + ru.ru_stime


def main():
    assert len(sys.argv) == 3, "usage: script CONSUMER_BINARY RECEIPT"
    binary = Path(sys.argv[1]).resolve()
    receipt = Path(sys.argv[2]).resolve()
    assert binary.is_file()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-o7-") as tmp:
        home = Path(tmp)
        source = home / "source"
        source.mkdir()
        files = {}
        for i in range(512):
            name = f"entry-{i:05d}.txt"
            b = source_bytes(i)
            (source / name).write_bytes(b)
            files[name] = hashlib.sha256(b).hexdigest()
        nonpack = b"".join(
            hashlib.sha256(f"native-c-consumer-nonpack-{i}".encode()).digest()
            for i in range(2200)
        )[:70000]
        (source / "unpacked-high-entropy.bin").write_bytes(nonpack)
        files["unpacked-high-entropy.bin"] = hashlib.sha256(nonpack).hexdigest()
        archive = home / "source.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        runs = {"serial": [], "group": []}
        rows = []
        for round_id in range(REPS):
            order = ("serial", "group", "group", "serial") if round_id % 2 == 0 else (
                "group", "serial", "serial", "group"
            )
            for trial, mode in enumerate(order):
                dest = home / f"trial-{round_id}-{trial}-{mode}"
                dest.mkdir()
                cpu0 = child_cpu()
                t0 = time.perf_counter_ns()
                p = subprocess.run(
                    [str(binary), str(archive), str(dest), mode],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
                cpu_ms = (child_cpu() - cpu0) * 1e3
                line = json.loads(p.stdout.strip())
                assert line["mode"] == mode and line["members"] == len(files)
                assert line["decoded_bytes"] == sum(p.stat().st_size for p in source.iterdir())
                if mode == "group":
                    assert line["batch_count"] >= 2 and line["batched_members"] >= 512
                else:
                    assert line["batch_count"] == 0 and line["fallback"] == len(files)
                produced = {x.name: hashlib.sha256(x.read_bytes()).hexdigest()
                            for x in dest.iterdir()}
                assert produced == files, ("byte-exact tree mismatch", mode, round_id)
                entry = {
                    "round": round_id, "trial": trial, "mode": mode,
                    "wall_ms": elapsed_ms, "child_cpu_ms": cpu_ms,
                    **line
                }
                runs[mode].append(entry)
                rows.append(entry)
        summary = {
            mode: {
                "median_wall_ms": statistics.median(x["wall_ms"] for x in records),
                "median_cpu_ms": statistics.median(x["child_cpu_ms"] for x in records),
                "median_rss_kib": statistics.median(x["rss_kib"] for x in records),
                "samples": len(records),
            }
            for mode, records in runs.items()
        }
        result = {
            "schema": "cmpct-native-public-c-consumer-o7-v1",
            "status": "O7_COMPLETE",
            "same_source_sha256": archive_hash,
            "member_sha256": files,
            "source_archive_bytes": archive.stat().st_size,
            "total_payload_bytes": sum(x.stat().st_size for x in source.iterdir()),
            "summary": summary, "raw_abba": rows,
            "interpretation_limit": "test-only C consumer; process startup and output writes included; no release credit"
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "status": result["status"],
            "source_sha256": archive_hash,
            "archive_bytes": result["source_archive_bytes"],
            "payload_bytes": result["total_payload_bytes"],
            "summary": summary,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
