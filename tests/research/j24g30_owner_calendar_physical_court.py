#!/usr/bin/env python3
"""J24G30 inherited physical product court: same physical signed-r24 inputs; old/candidate installed Readers.

The first-party Builder runs on Ubuntu only. All consumers receive identical saved bytes.
A baseline acceptance discrepancy is recorded, not hidden or renamed a green product test.
"""
from __future__ import annotations
import argparse
import calendar
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

NAME = "timestamped.bin"
PAYLOAD = b"cmpct-j24g27:signed-mtime:lossless-byte-identity\n" * 17
CASES = {
    "negative_epoch": -1_000_000_000,
    "zero_epoch": 0,
    "pre_1980_1979": 283_996_800_000_000_000,
    "ordinary_2020": 1_577_880_000_000_000_000,
    "upper_2107_control": 4_354_689_600_000_000_000,  # 2107-12-30 UTC
    "upper_2108_leap": 4_359_960_000_000_000_000,  # 2108-02-29 UTC
    "upper_2108_ordinary": 4_360_046_400_000_000_000,  # 2108-03-01 UTC
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def identity() -> dict:
    expected = os.environ["EXPECTED_READER_BLOB"]
    installed = Path(inspect.getfile(CMPCT)).read_bytes()
    normalized = installed.replace(b"\r\n", b"\n")
    assert git_blob(normalized) == expected, (git_blob(normalized), expected)
    assert b"\r" not in normalized, "installed source contains unexpected CR bytes"
    return {"git_blob": expected, "raw_git_blob": git_blob(installed), "sha256": sha(installed),
            "newline_conversion": git_blob(installed) != expected}


def generate(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    info = {}
    for label, mt in CASES.items():
        source = root / "source" / label
        source.mkdir(parents=True, exist_ok=True)
        member = source / NAME
        member.write_bytes(PAYLOAD)
        os.utime(member, ns=(mt, mt))
        assert member.stat().st_mtime_ns == mt
        archive = root / (label + ".cmpct")
        Builder(source, workers=1).build(archive)
        with CMPCT(archive) as ar:
            assert ar.by[NAME][3] == mt
            assert ar.read(NAME) == PAYLOAD
            assert ar.verify() == 1
        blob = archive.read_bytes()
        info[label] = {"archive": archive.name, "size": len(blob), "sha256": sha(blob),
                       "mtime_ns": mt, "payload_sha256": sha(PAYLOAD)}
    manifest = {"schema": "j24g30-owner-composition-fixed-first-party-r24-v1", "generator": identity(),
                "cases": info, "reader_patch_base": "ca01d885fedc8ffc343b9c3c624eddd134158452"}
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("J24G30_GENERATED=" + json.dumps(manifest, sort_keys=True), flush=True)


def court(inputs: Path, output: Path, mode: str, repeat: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((inputs / "manifest.json").read_text())
    assert manifest["schema"] == "j24g30-owner-composition-fixed-first-party-r24-v1"
    got = {}
    for label, mt in CASES.items():
        meta = manifest["cases"][label]
        path = inputs / meta["archive"]
        physical = path.read_bytes()
        assert (sha(physical), len(physical)) == (meta["sha256"], meta["size"])
        assert meta["mtime_ns"] == mt and meta["payload_sha256"] == sha(PAYLOAD)
        result = {"physical_sha256": sha(physical), "mtime_ns": mt,
                  "read": "NOT_RUN", "verify": "NOT_RUN", "zip": "NOT_RUN"}
        with CMPCT(path) as ar:
            assert ar.by[NAME][3] == mt, "signed source metadata not retained"
            assert ar.read(NAME) == PAYLOAD
            result["read"] = "PASS"
            assert ar.verify() == 1
            result["verify"] = "PASS"
            out = output / (label + ".zip")
            try:
                ar.export_zip(out)
                result["zip"] = "SUCCESS"
            except Exception as exc:
                result["zip"] = "ERROR"
                result["error_type"] = type(exc).__name__
                result["error"] = str(exc)[:300]
                result["trace_tail"] = traceback.format_exc()[-800:]
        if result["zip"] == "SUCCESS":
            with zipfile.ZipFile(out) as z:
                assert z.namelist() == [NAME]
                assert z.read(NAME) == PAYLOAD
                dt = z.getinfo(NAME).date_time
                assert 1980 <= dt[0] <= 2107
                result["dos_datetime"] = list(dt)
                # Read the exact ZIP DOS header through the independent stdlib parser.
                # Old Reader may encode 2107-02-29 (impossible); preserve the negative.
                result["gregorian_valid"] = 1 <= dt[2] <= calendar.monthrange(dt[0], dt[1])[1]
            result["zip_sha256"] = sha(out.read_bytes())
            result["zip_length"] = out.stat().st_size
        if label == "ordinary_2020":
            assert result["zip"] == "SUCCESS", result
        if mode == "candidate":
            assert result["zip"] == "SUCCESS", result
            assert result["gregorian_valid"], result
            if label in ("negative_epoch", "zero_epoch", "pre_1980_1979"):
                assert result["dos_datetime"] == [1980, 1, 1, 0, 0, 0], result
            if label.startswith("upper_2108"):
                assert result["dos_datetime"] == [2107, 12, 31, 23, 59, 58], result
        got[label] = result
    report = {"schema": "j24g30-owner-composition-product-court-v1", "mode": mode,
              "source": identity(), "platform": platform.platform(),
              "python": sys.version, "repeat": repeat, "cases": got}
    (output / ("j24g28_" + mode + "_" + str(repeat) + ".json")).write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("J24G30_COURT=" + json.dumps(report, sort_keys=True), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["generate", "court"])
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--mode", choices=["baseline", "candidate"], default="candidate")
    ap.add_argument("--repeat", type=int, default=1)
    args = ap.parse_args()
    if args.action == "generate":
        generate(args.output)
    else:
        assert args.input is not None
        court(args.input, args.output, args.mode, args.repeat)


if __name__ == "__main__":
    main()
