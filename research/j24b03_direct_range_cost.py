#!/usr/bin/env python3
"""J24B03-P same-wire, original-vs-candidate direct-range cost experiment.

This is research-only. Safety semantics live in the separate J24B03 court.
Never promote this microbench to release/product evidence.
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

PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]
OFFSETS = (0, 7, 31, 63, 111)
LENGTH = 16
CALLS = 30000
ORDER = ("baseline", "candidate", "candidate", "baseline")
ROUNDS = 3


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(which: str) -> Path:
    return Path("frozen-baseline/src" if which == "baseline" else "src").resolve()


def create_inputs(root: Path):
    from j24b03_direct_blob_size_court import wire, PAYLOAD as generator_payload
    from cmpct.codec import CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE, K_FILE
    assert generator_payload == PAYLOAD
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, codec in (("raw", CODEC_RAW), ("zstd", CODEC_ZSTD), ("deflate", CODEC_DEFLATE)):
        archive, _, _ = wire(K_FILE, codec, 128)
        path = root / (name + ".cmpct")
        path.write_bytes(archive)
        entries.append({"name": name, "path": str(path.resolve()), "codec": codec,
                        "sha256": digest(path),
                        "expected_hex": [PAYLOAD[o:o + LENGTH].hex() for o in OFFSETS]})
    return entries


def vmhwm_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except OSError:
        return None
    return None


def worker(entry: dict) -> dict:
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_mod

    path = Path(entry["path"])
    assert digest(path) == entry["sha256"]
    expected = [bytes.fromhex(x) for x in entry["expected_hex"]]
    module = Path(reader_mod.__file__).resolve()
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    archive = CMPCT(path)
    open_wall_ns = time.perf_counter_ns() - t0
    open_cpu_ns = time.process_time_ns() - c0
    try:
        for _ in range(32):
            for o, target in zip(OFFSETS, expected):
                assert archive.read_range("direct.bin", o, LENGTH) == target

        checksum = 0
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        for i in range(CALLS):
            part = archive.read_range("direct.bin", OFFSETS[i % len(OFFSETS)], LENGTH)
            checksum += part[0]
        cpu = time.process_time_ns() - c0
        wall = time.perf_counter_ns() - t0
        target_checksum = (CALLS // len(expected)) * sum(v[0] for v in expected)
        assert checksum == target_checksum
    finally:
        archive.close()

    return {"archive_sha256": entry["sha256"], "profile": entry["name"],
            "reader_path": str(module), "reader_sha256": digest(module),
            "calls": CALLS, "logical_return_bytes": CALLS * LENGTH,
            "answer_checksum": checksum, "open_wall_ns": open_wall_ns,
            "open_cpu_ns": open_cpu_ns, "range_wall_ns": wall,
            "range_cpu_ns": cpu, "peak_vmhwm_kib": vmhwm_kib()}


def run_experiment(root: Path, out: Path) -> None:
    entries = create_inputs(root)
    control_sha = {}
    for arm in ("baseline", "candidate"):
        mod = source_path(arm) / "cmpct/reader.py"
        assert mod.is_file(), mod
        control_sha[arm] = digest(mod)
    assert control_sha["baseline"] != control_sha["candidate"], "the two code owners must be distinct"

    rows = []
    script = str(Path(__file__).resolve())
    for entry in entries:
        for rnd in range(ROUNDS):
            for seq, arm in enumerate(ORDER):
                env = dict(os.environ, PYTHONPATH=str(source_path(arm)))
                proc = subprocess.run([sys.executable, script, "--worker", json.dumps(entry)],
                                      capture_output=True, text=True, env=env, check=True)
                item = json.loads(proc.stdout)
                assert item["reader_sha256"] == control_sha[arm], (arm, item)
                assert Path(item["reader_path"]).resolve() == source_path(arm) / "cmpct/reader.py"
                assert item["archive_sha256"] == entry["sha256"]
                item.update({"arm": arm, "round": rnd, "order_slot": seq})
                rows.append(item)

    summaries = {}
    for profile in ("raw", "zstd", "deflate"):
        measurements = {}
        for arm in ("baseline", "candidate"):
            sample = [x for x in rows if x["profile"] == profile and x["arm"] == arm]
            assert len(sample) == 2 * ROUNDS
            measurements[arm] = {
                "range_wall_ns_per_call": statistics.median(x["range_wall_ns"] / CALLS for x in sample),
                "range_cpu_ns_per_call": statistics.median(x["range_cpu_ns"] / CALLS for x in sample),
                "open_wall_ns": statistics.median(x["open_wall_ns"] for x in sample),
                "open_cpu_ns": statistics.median(x["open_cpu_ns"] for x in sample),
                "vmhwm_kib": statistics.median(x["peak_vmhwm_kib"] for x in sample
                                               if x["peak_vmhwm_kib"] is not None),
            }
        a, b = measurements["baseline"], measurements["candidate"]
        summaries[profile] = {
            "measurements": measurements,
            "wall_ratio": b["range_wall_ns_per_call"] / a["range_wall_ns_per_call"],
            "cpu_ratio": b["range_cpu_ns_per_call"] / a["range_cpu_ns_per_call"],
            "wall_ns_additional_per_call": b["range_wall_ns_per_call"] - a["range_wall_ns_per_call"],
            "cpu_ns_additional_per_call": b["range_cpu_ns_per_call"] - a["range_cpu_ns_per_call"],
        }

    raw = summaries["raw"]
    debt = raw["wall_ratio"] >= 1.20 and raw["cpu_ratio"] >= 1.20 and raw["wall_ns_additional_per_call"] >= 500
    report = {"experiment": "J24B03-P", "rung": "source-exact micro-ABBA only",
              "design": {"calls_per_worker": CALLS, "order": list(ORDER),
                         "rounds": ROUNDS, "offsets": list(OFFSETS), "length": LENGTH},
              "source_sha256": control_sha, "archives": entries, "rows": rows,
              "summary": summaries,
              "decision": "RAW_GUARD_PERF_DEBT_SIGNAL" if debt else "NO_PREREGISTERED_RAW_DEBT_SIGNAL",
              "scope": "no merge/release; no claim of complete-product parity"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": report["decision"], "raw": raw, "records": len(rows)},
                     sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", type=str)
    p.add_argument("--run", action="store_true")
    p.add_argument("--root", type=Path, default=Path("benchmark-artifacts/j24b03-p-inputs"))
    p.add_argument("--out", type=Path, default=Path("benchmark-artifacts/j24b03-p-results.json"))
    args = p.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(json.loads(args.worker)), sort_keys=True))
    elif args.run:
        run_experiment(args.root, args.out)
    else:
        p.error("choose --worker or --run")


if __name__ == "__main__":
    main()
