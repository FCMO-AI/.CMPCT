#!/usr/bin/env python3
"""J24B03-M2: held-out upper-scale source-exact Reader full-session ABBA. Research, not release evidence."""
from __future__ import annotations
import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]
SCALES = (1, 131072, 262144)
ORDER = ("baseline", "candidate", "candidate", "baseline")
ROUNDS = 3


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_path(arm):
    return Path("frozen-baseline/src" if arm == "baseline" else "src").resolve()


def create_image(n):
    import msgpack
    from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_FILE, MAGIC, S_BLOB, VERSION, sha, zc
    files = [[f"direct-{i:06d}.bin", K_FILE, 0o644, 0, 128, None, [S_BLOB, 0]]
             for i in range(n)]
    index = {"v": VERSION, "files": files, "blobs": [[0, 128, 128, CODEC_RAW, 0]],
             "recipes": [], "dict_blob": None,
             "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
             "features": []}
    plain = msgpack.packb(index, use_bin_type=True)
    comp = zc(plain, 3)
    frame = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, 128, 128, 0,
                      binascii.crc32(PAYLOAD) & 0xffffffff, sha(PAYLOAD)) + PAYLOAD
    head = HDR.pack(MAGIC, VERSION, 0, len(comp), len(plain), len(frame), sha(plain))
    foot = FTR.pack(FMAGIC, 0, 1, 0, 0, len(comp), len(plain), 0, sha(plain))
    return head + comp + frame + comp + foot


def expected_checksum(n):
    return sum(PAYLOAD[(i * 7) % 121] for i in range(n))


def create_inputs(root):
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for n in SCALES:
        raw = create_image(n)
        path = (root / f"direct-{n}.cmpct").resolve()
        path.write_bytes(raw)
        entries.append({"name": str(n), "path": str(path), "n": n,
                        "archive_sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw), "expected_checksum": expected_checksum(n)})
    assert len({x["archive_sha256"] for x in entries}) == len(SCALES)
    return entries


def vmhwm_kib():
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except OSError:
        pass
    return None


def worker(entry):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    import cmpct.reader as reader_mod
    import cmpct.validation as validation_mod
    path = Path(entry["path"])
    assert digest(path) == entry["archive_sha256"]
    n = entry["n"]
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    archive = CMPCT(path)
    open_wall_ns = time.perf_counter_ns() - t0
    open_cpu_ns = time.process_time_ns() - c0
    checksum = 0
    try:
        assert len(archive.files) == n and len(archive.blobs) == 1
        for i in sorted({0, n // 2, n - 1}):
            assert archive.read(f"direct-{i:06d}.bin") == PAYLOAD
        assert archive.read_range("direct-000000.bin", 0, 0) == b""
        assert archive.read_range("direct-000000.bin", 128, 0) == b""
        t1, c1 = time.perf_counter_ns(), time.process_time_ns()
        for i in range(n):
            part = archive.read_range(f"direct-{i:06d}.bin", (i * 7) % 121, 8)
            assert len(part) == 8
            checksum += part[0]
        read_wall_ns = time.perf_counter_ns() - t1
        read_cpu_ns = time.process_time_ns() - c1
    finally:
        archive.close()
    session_wall_ns = time.perf_counter_ns() - t0
    session_cpu_ns = time.process_time_ns() - c0
    assert checksum == entry["expected_checksum"]
    session_peak = vmhwm_kib()
    p0, pc0 = time.perf_counter_ns(), time.process_time_ns()
    preflight_archive(path)
    preflight_wall_ns = time.perf_counter_ns() - p0
    preflight_cpu_ns = time.process_time_ns() - pc0
    reader_path = Path(reader_mod.__file__).resolve()
    validator_path = Path(validation_mod.__file__).resolve()
    return {"profile": n, "archive_sha256": entry["archive_sha256"],
            "reader_path": str(reader_path), "reader_sha256": digest(reader_path),
            "validation_path": str(validator_path), "validation_sha256": digest(validator_path),
            "files": n, "physical_blobs": 1, "physical_archive_bytes": entry["bytes"],
            "checksum": checksum, "open_wall_ns": open_wall_ns, "open_cpu_ns": open_cpu_ns,
            "read_wall_ns": read_wall_ns, "read_cpu_ns": read_cpu_ns,
            "session_wall_ns": session_wall_ns, "session_cpu_ns": session_cpu_ns,
            "preflight_wall_ns": preflight_wall_ns, "preflight_cpu_ns": preflight_cpu_ns,
            "peak_vmhwm_session_kib": session_peak,
            "peak_vmhwm_total_kib": vmhwm_kib()}


METRICS = ("open_wall_ns", "open_cpu_ns", "read_wall_ns", "read_cpu_ns",
           "session_wall_ns", "session_cpu_ns", "preflight_wall_ns", "preflight_cpu_ns",
           "peak_vmhwm_session_kib", "peak_vmhwm_total_kib")


def summarize(rows):
    summary = {}
    for n in SCALES:
        pair = {}
        for arm in ("baseline", "candidate"):
            subset = [x for x in rows if x["profile"] == n and x["arm"] == arm]
            assert len(subset) == 2 * ROUNDS
            pair[arm] = {k: statistics.median(x[k] for x in subset) for k in METRICS}
        delta = {k: pair["candidate"][k] - pair["baseline"][k] for k in METRICS}
        ratios = {k: pair["candidate"][k] / pair["baseline"][k] for k in METRICS}
        summary[str(n)] = {"arms": pair, "delta": delta, "ratio": ratios}
    return summary


def decision(summary):
    session = preflight = False
    for n in (131072, 262144):
        ratios = summary[str(n)]["ratio"]
        delta = summary[str(n)]["delta"]
        if ((ratios["session_wall_ns"] >= 1.10 and ratios["session_cpu_ns"] >= 1.10
             and delta["session_wall_ns"] >= 25_000_000
             and delta["session_cpu_ns"] >= 25_000_000)
            or delta["peak_vmhwm_session_kib"] >= 8192):
            session = True
        if (ratios["preflight_wall_ns"] >= 1.15 and ratios["preflight_cpu_ns"] >= 1.15
            and delta["preflight_wall_ns"] >= 50_000_000
            and delta["preflight_cpu_ns"] >= 50_000_000):
            preflight = True
    return ("MATERIAL_DIRECT_SESSION_AND_PREFLIGHT_DEBT" if session and preflight else
            "MATERIAL_DIRECT_SESSION_DEBT" if session else
            "MATERIAL_DIRECT_PREFLIGHT_DEBT" if preflight else
            "NO_PREREGISTERED_MACRO_DEBT_SIGNAL")


def run(root, out):
    archives = create_inputs(root)
    source = {arm: {"reader": digest(source_path(arm) / "cmpct/reader.py"),
                    "validation": digest(source_path(arm) / "cmpct/validation.py")}
              for arm in ("baseline", "candidate")}
    assert source["baseline"] != source["candidate"]
    rows = []
    script = str(Path(__file__).resolve())
    for entry in archives:
        for rnd in range(ROUNDS):
            for slot, arm in enumerate(ORDER):
                env = dict(os.environ, PYTHONPATH=str(source_path(arm)))
                proc = subprocess.run([sys.executable, script, "--worker", json.dumps(entry)],
                                      capture_output=True, text=True, env=env, check=True)
                row = json.loads(proc.stdout)
                assert row["reader_sha256"] == source[arm]["reader"]
                assert row["validation_sha256"] == source[arm]["validation"]
                assert Path(row["reader_path"]).resolve() == source_path(arm) / "cmpct/reader.py"
                assert row["archive_sha256"] == entry["archive_sha256"]
                rows.append({**row, "arm": arm, "round": rnd, "order_slot": slot})
    summary = summarize(rows)
    report = {"experiment": "J24B03-M2", "rung": "authentic r24 source-exact direct session ABBA",
              "design": {"scales": list(SCALES), "order": list(ORDER), "rounds": ROUNDS},
              "source_sha256": source, "archives": archives, "rows": rows,
              "summary": summary, "decision": decision(summary),
              "scope": "one host, direct dedup RAW; no full matrix or release claim"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": report["decision"], "processes": len(rows),
                      "session_262144": summary["262144"]}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=str)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("benchmark-artifacts/j24b03-m2-inputs"))
    parser.add_argument("--out", type=Path, default=Path("benchmark-artifacts/j24b03-m2-results.json"))
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(json.loads(args.worker)), sort_keys=True))
    elif args.run:
        run(args.root, args.out)
    else:
        parser.error("choose --worker or --run")


if __name__ == "__main__":
    main()
