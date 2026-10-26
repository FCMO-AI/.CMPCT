#!/usr/bin/env python3
"""O190 exact-source real Builder→CMPCT→ZIP cross-host positive court.

Original O184 Windows negative remains frozen at its own source identity. Green
here requires real unmodified producer archives and independently installed
candidate source on all consumers; administrative workflow success is not proof.
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
DATA = {
    "pre1970": {"mtime_ns": -315619200_000_000_000, "content": b"original O184 signed year 1960 control"},
    "ordinary": {"mtime_ns": 949449600_000_000_000, "content": b"ordinary year 2000 ZIP semantics control"},
    "future": {"mtime_ns": 4417977600_000_000_000, "content": b"future signed r24 valid metadata control"},
}
ZIP_MIN = (1980, 1, 1, 0, 0, 0)
ZIP_MAX = (2107, 12, 31, 23, 59, 58)


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def identity():
    from cmpct.reader import CMPCT
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    expected = os.environ.get("EVIDENCE_HEAD")
    if expected and head != expected:
        raise AssertionError(f"head drift: {head} != {expected}")
    git = subprocess.check_output(["git", "show", "HEAD:src/cmpct/reader.py"], cwd=ROOT).replace(b"\r\n", b"\n")
    installed = Path(inspect.getfile(CMPCT)).resolve()
    actual = installed.read_bytes().replace(b"\r\n", b"\n")
    if actual != git or ROOT in installed.parents:
        raise AssertionError(f"installed Reader not exact git source: {installed}")
    return {"head": head, "reader_sha256": hashlib.sha256(git).hexdigest(),
            "installed": str(installed), "os": platform.platform(), "python": platform.python_version()}


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def build(where: Path, provenance):
    assert platform.system() == "Linux", "Linux must be the only input producer"
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    receipts = {}
    for label, spec in DATA.items():
        with tempfile.TemporaryDirectory(prefix="o190-source-") as td:
            root = Path(td) / "tree"
            root.mkdir()
            source = root / "raw.bin"
            source.write_bytes(spec["content"])
            mt = spec["mtime_ns"]
            os.utime(source, ns=(mt, mt))
            if source.stat().st_mtime_ns != mt:
                raise AssertionError(f"host did not preserve source signed mtime: {label}")
            dst = where / f"{label}.cmpct"
            Builder(root).build(dst)
            with CMPCT(dst) as archive:
                assert archive.verify() == 1
                assert archive.read("raw.bin") == spec["content"]
                assert archive.by["raw.bin"][3] == mt
            assert dst.read_bytes()[:8] == b"CMPCT24\x00"
            receipts[label] = {"sha256": sha(dst), "bytes": dst.stat().st_size,
                               "mtime_ns": mt, "payload_sha256": hashlib.sha256(spec["content"]).hexdigest()}
    result = {"schema": "cmpct-o190-producer-v1", "provenance": provenance, "archives": receipts}
    dump(where / "producer.json", result)
    return result


def receive(where: Path, provenance):
    from cmpct.reader import CMPCT
    origin = json.loads((where / "producer.json").read_text(encoding="utf-8"))
    assert origin["schema"] == "cmpct-o190-producer-v1"
    for attr in ("head", "reader_sha256"):
        assert origin["provenance"][attr] == provenance[attr], f"source drift {attr}"
    results = {}
    for label, spec in DATA.items():
        orig = origin["archives"][label]
        cmpct = where / f"{label}.cmpct"
        assert sha(cmpct) == orig["sha256"] and cmpct.stat().st_size == orig["bytes"]
        with CMPCT(cmpct) as archive:
            assert archive.verify() == 1
            assert archive.read("raw.bin") == spec["content"]
            assert archive.by["raw.bin"][3] == spec["mtime_ns"]
            out = where / f"{label}.zip"
            archive.export_zip(out)
            assert sha(cmpct) == orig["sha256"], "export mutated source"
            with zipfile.ZipFile(out) as zipped:
                assert zipped.namelist() == ["raw.bin"]
                assert zipped.testzip() is None
                assert zipped.read("raw.bin") == spec["content"]
                info = zipped.getinfo("raw.bin")
                stamp = tuple(info.date_time)
                if label == "pre1970":
                    assert stamp == ZIP_MIN, f"pre-1970 full-date floor failure: {stamp}"
                elif label == "future":
                    assert stamp == ZIP_MAX, f"post-2107 full-date ceiling failure: {stamp}"
                else:
                    t = time.localtime(spec["mtime_ns"] // 1_000_000_000)
                    assert stamp == (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, (t.tm_sec // 2) * 2), (
                        "ordinary legacy local semantics changed", stamp)
                results[label] = {"zip_bytes": out.stat().st_size, "zip_sha256": sha(out),
                                  "zip_datetime": stamp, "crc": info.CRC, "payload_sha256": orig["payload_sha256"]}
    return {"schema": "cmpct-o190-consumer-v1", "provenance": provenance,
            "origin": origin["archives"], "results": results,
            "verdict": "THREE_SIGNED_R24_ARCHIVES_ZIP_EXPORT_EXACT_AND_BOUNDED",
            "release_credit": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=["producer", "consumer"], required=True)
    ap.add_argument("--directory", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.directory.mkdir(parents=True, exist_ok=True)
    try:
        ident = identity()
        result = build(a.directory, ident) if a.role == "producer" else receive(a.directory, ident)
        status = 0
    except Exception as ex:
        result = {"schema": "cmpct-o190-blocked-v1", "verdict": "FAILED_OR_BLOCKED",
                  "error": str(ex), "exception": type(ex).__name__,
                  "traceback": traceback.format_exc()[-5000:]}
        status = 1
    dump(a.out, result)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(status)


if __name__ == "__main__":
    main()
