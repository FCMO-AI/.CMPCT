"""J24G27: source-exact first-party r24 signed mtime -> ZIP cross-host falsifier.

Research-only. All decisions use *identical, physically generated* CMPCT inputs
on each host. The exporter is unmodified; no test changes its admission policy.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import platform
import sys
import traceback
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT

PAYLOAD = b"cmpct-j24g27:signed-mtime:lossless-byte-identity\n" * 17
NAME = "timestamped.bin"
CASES = {"negative_epoch": -1_000_000_000, "ordinary_2020": 1_577_880_000_000_000_000}
PUBLISHED_READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob_sha(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode("ascii") + b"\0" + b).hexdigest()


def installed_identity() -> dict:
    path = Path(inspect.getfile(CMPCT))
    data = path.read_bytes()
    raw_blob = git_blob_sha(data)
    # Git-for-Windows checkout may translate LF to CRLF before pip copies source.
    # Require *only* this reversible newline transform; all semantic source bytes
    # and the exact immutable Git blob must still match. Never ignore a real drift.
    normalized = data.replace(b"\r\n", b"\n")
    blob = git_blob_sha(normalized)
    if blob != PUBLISHED_READER_BLOB:
        raise AssertionError(f"installed Reader drifted: raw={raw_blob}, normalized={blob} != {PUBLISHED_READER_BLOB}")
    if raw_blob != blob and (b"\r\n" not in data or b"\r" in normalized):
        raise AssertionError("installed Reader has non-newline source drift")
    return {"reader_git_blob": blob, "reader_raw_git_blob": raw_blob,
            "source_newlines": "CRLF_ONLY" if raw_blob != blob else "LF",
            "reader_sha256": digest(data), "reader_path": str(path)}


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    identity = installed_identity()
    rows = {}
    for label, mtime_ns in CASES.items():
        source = output / "_source" / label
        source.mkdir(parents=True, exist_ok=True)
        p = source / NAME
        p.write_bytes(PAYLOAD)
        os.utime(p, ns=(mtime_ns, mtime_ns))
        actual_mtime = p.stat().st_mtime_ns
        if actual_mtime != mtime_ns:
            raise AssertionError(f"source filesystem timestamp changed: {actual_mtime} != {mtime_ns}")
        archive = output / f"{label}.cmpct"
        Builder(source, workers=1).build(archive)
        with CMPCT(archive) as ar:
            assert ar.read(NAME) == PAYLOAD
            assert ar.verify() == 1
            encoded_mtime = ar.by[NAME][3]
            if encoded_mtime != mtime_ns:
                raise AssertionError(f"Builder changed signed timestamp {label}: {encoded_mtime}")
        rows[label] = {
            "filename": archive.name, "archive_sha256": digest(archive.read_bytes()),
            "archive_bytes": archive.stat().st_size, "mtime_ns": mtime_ns,
            "payload_sha256": digest(PAYLOAD),
        }
    manifest = {
        "schema": "cmpct-j24g27-physical-v1",
        "source_reader_blob": PUBLISHED_READER_BLOB,
        "generator": identity, "cases": rows,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("J24G27_GENERATOR=" + json.dumps(manifest, sort_keys=True), flush=True)


def court(inputs: Path, output: Path, repeat: int) -> None:
    identity = installed_identity()
    manifest = json.loads((inputs / "manifest.json").read_text())
    if manifest["schema"] != "cmpct-j24g27-physical-v1":
        raise AssertionError("unknown physical manifest")
    if manifest["source_reader_blob"] != PUBLISHED_READER_BLOB:
        raise AssertionError("physical vector source identity drift")
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    for label, mtime_ns in CASES.items():
        info = manifest["cases"][label]
        archive = inputs / info["filename"]
        physical = archive.read_bytes()
        if digest(physical) != info["archive_sha256"] or len(physical) != info["archive_bytes"]:
            raise AssertionError(f"physical input drift for {label}")
        if info["mtime_ns"] != mtime_ns or info["payload_sha256"] != digest(PAYLOAD):
            raise AssertionError(f"manifest content/mtime drift for {label}")
        result = {
            "expected_mtime_ns": mtime_ns,
            "physical_archive_sha256": digest(physical),
            "read": "UNMEASURED", "verify": "UNMEASURED", "export": "UNMEASURED",
        }
        with CMPCT(archive) as ar:
            actual = ar.by[NAME][3]
            result["read_mtime_ns"] = actual
            assert actual == mtime_ns, (label, actual, mtime_ns)
            assert ar.read(NAME) == PAYLOAD
            result["read"] = "PASS"
            assert ar.verify() == 1
            result["verify"] = "PASS"
            target = output / f"{label}_repeat{repeat}.zip"
            try:
                ar.export_zip(target)
                result["export"] = "SUCCESS"
            except Exception as exc:
                tb = traceback.format_exc()
                result["export"] = "ERROR"
                result["exception_type"] = type(exc).__name__
                result["exception_text"] = str(exc)[:400]
                result["trace_tail"] = tb[-1200:]
                result["time_conversion_frame"] = "_zip_dos_time" in tb or "localtime" in tb
        if result["export"] == "SUCCESS":
            with zipfile.ZipFile(target) as zf:
                assert zf.namelist() == [NAME]
                assert zf.read(NAME) == PAYLOAD
                zi = zf.getinfo(NAME)
                assert 1980 <= zi.date_time[0] <= 2107
                result["dos_time"] = zi.date_time
            result["zip_bytes"] = target.stat().st_size
            result["zip_sha256"] = digest(target.read_bytes())
        if label == "ordinary_2020" and result["export"] != "SUCCESS":
            raise AssertionError("ordinary control ZIP export failed; negative cannot be attributed")
        results[label] = result
    try:
        import time
        probe = time.localtime(-1)
        localtime_probe = {"status": "SUCCESS", "year": probe.tm_year}
    except Exception as exc:
        localtime_probe = {"status": "ERROR", "type": type(exc).__name__, "text": str(exc)}
    report = {
        "schema": "cmpct-j24g27-court-v1",
        "repeat": repeat, "platform": platform.platform(), "python": sys.version,
        "identity": identity, "time_localtime_minus1": localtime_probe,
        "cases": results,
        "decision": (
            "TIMESTAMP_CONVERSION_GAP_OBSERVED"
            if results["negative_epoch"]["export"] == "ERROR"
            and results["negative_epoch"].get("time_conversion_frame", False)
            else "NO_GAP_ON_THIS_HOST"
            if results["negative_epoch"]["export"] == "SUCCESS"
            else "UNATTRIBUTED_EXPORT_ERROR"
        ),
    }
    target_report = output / f"j24g27_{platform.system().lower()}_repeat{repeat}.json"
    target_report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("J24G27_COURT=" + json.dumps(report, sort_keys=True), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("generate", "court"))
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repeat", type=int, default=1)
    args = ap.parse_args()
    if args.action == "generate":
        generate(args.output)
    else:
        if args.input is None:
            raise ValueError("court requires --input")
        court(args.input, args.output, args.repeat)


if __name__ == "__main__":
    main()
