#!/usr/bin/env python3
"""O184: authentic revision-24 signed-time ZIP export cross-host falsifier.

Green science can mean confirmed product failure; JSON must be read for the verdict.
This file changes no Reader/Writer code or historical conformance evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OLD_NS = -315619200_000_000_000  # 1960-01-01 UTC, within signed i64.
NORMAL_NS = 949449600_000_000_000  # 2000-02-03 UTC.
OLD_BYTES = b"O184 pre-1970 signed timestamp payload, authentic r24."
NORMAL_BYTES = b"O184 ordinary DOS-compatible timestamp control."
EXPECTED = {
    "old": ("old.txt", OLD_NS, OLD_BYTES),
    "normal": ("modern.txt", NORMAL_NS, NORMAL_BYTES),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity() -> dict:
    from cmpct.reader import CMPCT
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    required = os.environ.get("EVIDENCE_HEAD")
    if required and required != head:
        raise AssertionError(f"wrong checked-out head: {head}, expected {required}")
    source = subprocess.check_output(
        ["git", "show", "HEAD:src/cmpct/reader.py"], cwd=ROOT
    ).replace(b"\r\n", b"\n")
    installed = Path(inspect.getfile(CMPCT)).resolve()
    real = installed.read_bytes().replace(b"\r\n", b"\n")
    if source != real:
        raise AssertionError("installed Reader bytes differ from checked-out Git HEAD")
    if ROOT in installed.parents:
        raise AssertionError("Reader imported from source checkout, not installed wheel")
    return {
        "head": head,
        "reader_sha256": hashlib.sha256(source).hexdigest(),
        "installed_reader": str(installed),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def write(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def build(args, provenance):
    if platform.system() != "Linux":
        raise AssertionError("single-authority archive producer must be Linux")
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT

    receipt = {"schema": "cmpct-o184-signed-time-crosshost-v1", "provenance": provenance, "archives": {}}
    for label, (name, mtime, payload) in EXPECTED.items():
        with tempfile.TemporaryDirectory(prefix="o184-origin-") as td:
            root = Path(td) / "source"
            root.mkdir()
            p = root / name
            p.write_bytes(payload)
            os.utime(p, ns=(mtime, mtime))
            if p.stat().st_mtime_ns != mtime:
                raise AssertionError(f"Linux source host failed signed timestamp control {label}")
            archive = args.directory / (label + ".cmpct")
            Builder(root).build(archive)
            with CMPCT(archive) as ar:
                if ar.verify() != 1 or ar.read(name) != payload:
                    raise AssertionError(f"authentic built r24 verification failed {label}")
                if ar.by[name][3] != mtime:
                    raise AssertionError(f"signed mtime changed in r24 archive {label}")
            if archive.read_bytes()[:8] != b"CMPCT24\x00":
                raise AssertionError("wrong format revision")
            receipt["archives"][label] = {
                "name": name,
                "sha256": sha(archive),
                "bytes": archive.stat().st_size,
                "mtime_ns": mtime,
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
            }
    write(args.directory / "producer.json", receipt)
    return {"verdict": "LINUX_AUTHENTIC_R24_INPUTS_FROZEN", **receipt}


def one_export(label: str, archive: Path, expected: dict, target: Path):
    from cmpct.reader import CMPCT

    name, mtime, payload = EXPECTED[label]
    if sha(archive) != expected["sha256"] or archive.stat().st_size != expected["bytes"]:
        raise AssertionError(f"input archive mismatch for {label}")
    with CMPCT(archive) as ar:
        if ar.verify() != 1 or ar.read(name) != payload:
            raise AssertionError(f"Reader rejected pristine {label} archive")
        if ar.by[name][3] != mtime:
            raise AssertionError(f"authenticated mtime altered for {label}")
        direct = {"successful": False}
        try:
            dos_time, dos_date = ar._zip_dos_time(mtime)
            direct = {"successful": True, "dos_time": dos_time, "dos_date": dos_date}
        except Exception as e:
            direct = {"successful": False, "exception": type(e).__name__, "message": str(e)}
        export = {"successful": False}
        try:
            ar.export_zip(target)
            with zipfile.ZipFile(target) as zipped:
                if zipped.testzip() is not None or zipped.namelist() != [name]:
                    raise AssertionError(f"invalid ZIP inventory/CRC for {label}")
                if zipped.read(name) != payload:
                    raise AssertionError(f"ZIP content mismatch for {label}")
                info = zipped.getinfo(name)
                export = {
                    "successful": True, "zip_sha256": sha(target),
                    "zip_bytes": target.stat().st_size,
                    "zip_dos_datetime": list(info.date_time),
                    "zip_payload_sha256": hashlib.sha256(zipped.read(name)).hexdigest(),
                }
        except Exception as e:
            export = {
                "successful": False, "exception": type(e).__name__, "message": str(e),
                "traceback": traceback.format_exc()[-3000:],
            }
    if sha(archive) != expected["sha256"]:
        raise AssertionError(f"ZIP attempted export modified CMPCT source {label}")
    return {"direct_conversion": direct, "export": export}


def receive(args, provenance):
    producer = json.loads((args.directory / "producer.json").read_text(encoding="utf-8"))
    if producer["schema"] != "cmpct-o184-signed-time-crosshost-v1":
        raise AssertionError("unknown original receipt schema")
    if producer["provenance"]["head"] != provenance["head"]:
        raise AssertionError("producer/consumer exact Git HEAD differs")
    if producer["provenance"]["reader_sha256"] != provenance["reader_sha256"]:
        raise AssertionError("producer/consumer original installed Reader source differs")
    results = {}
    for label in ("normal", "old"):
        results[label] = one_export(
            label, args.directory / (label + ".cmpct"),
            producer["archives"][label],
            args.directory / (label + ".zip")
        )
    if not results["normal"]["export"]["successful"]:
        raise AssertionError("ordinary 2000 ZIP control failed; cannot attribute old-time failure")
    old = results["old"]["export"]
    if old["successful"]:
        verdict = "PRE1970_ZIP_EXPORT_AUTHENTIC_SUCCESS_HYPOTHESIS_FALSIFIED"
    elif "_zip_dos_time" in old.get("traceback", "") and old["exception"] in (
        "OSError", "ValueError", "OverflowError"):
        verdict = "PRODUCT_NEGATIVE_PRE1970_DOS_CONVERSION_EXCEPTION"
    else:
        verdict = "OTHER_ZIP_EXPORT_FAILURE_UNATTRIBUTED"
    if verdict == "OTHER_ZIP_EXPORT_FAILURE_UNATTRIBUTED":
        raise AssertionError(f"unattributed ZIP export failure: {old}")
    return {
        "schema": "cmpct-o184-signed-time-consumer-v1",
        "provenance": provenance, "origin": producer["archives"],
        "host": platform.system(), "results": results, "verdict": verdict,
        "product_promotable": False, "release_credit": False
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("producer", "consumer"), required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    try:
        provenance = identity()
        result = build(args, provenance) if args.role == "producer" else receive(args, provenance)
        status = 0
    except Exception as exc:
        status = 1
        result = {
            "schema": "cmpct-o184-execution-failure-v1", "role": args.role,
            "verdict": "BLOCKED_OR_UNCLASSIFIED", "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-5000:],
        }
    write(args.out, result)
    print(json.dumps(result, sort_keys=True, default=str))
    raise SystemExit(status)


if __name__ == "__main__":
    main()
