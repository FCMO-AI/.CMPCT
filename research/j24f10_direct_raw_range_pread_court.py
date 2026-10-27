#!/usr/bin/env python3
"""J24F10: authentic direct-RAW S_BLOB range read versus same-inode truncation.

Independent revision-24 fixture, exact historical Reader control, crash-isolated
SIGBUS negative, same-inode truncation and different-inode name replacement.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

import msgpack

from j24f04_raw_chunk_immutable_transfer import HDR, BHDR, FTR, blob_sha

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_BLOB = "a6a74068b34d726fc38bc151e5f191ce2dd45993"
CANDIDATE_BLOB = "9f3172cd850e17202feac71651780d0cc989541c"
SIZE = 2 * 1024 * 1024 + 4096
NAME = "independent-direct-raw.bin"


def sha(v):
    return hashlib.sha256(v).hexdigest()


def source_fixture():
    from cmpct.codec import zc
    raw = hashlib.shake_256(b"J24F10 independent direct RAW range transfer").digest(SIZE)
    physical = BHDR.pack(
        b"CMA4", 0, 0, 0, len(raw), len(raw), 0,
        binascii.crc32(raw) & 0xffffffff, hashlib.sha256(raw).digest()
    ) + raw
    index = {
        "v": 24,
        "files": [[NAME, 0, 0o644, 0, len(raw), hashlib.sha256(raw).digest(), [0, 0]]],
        "blobs": [[0, len(raw), len(raw), 0, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {},
        "features": [],
    }
    unpacked = msgpack.packb(index, use_bin_type=True)
    zipped = zc(unpacked, 3)
    head = HDR.pack(b"CMPCT24\x00", 24, 0, len(zipped), len(unpacked),
                    len(physical), hashlib.sha256(unpacked).digest())
    foot = FTR.pack(b"CMPTF24\x00", 0, 1, 0, 0, len(zipped), len(unpacked), 0,
                    hashlib.sha256(unpacked).digest())
    archive = head + zipped + physical + zipped + foot
    assert archive[len(head)+len(zipped)+BHDR.size:
                   len(head)+len(zipped)+BHDR.size+len(raw)] == raw
    return raw, archive


def get_reader(which, historical):
    if which == "candidate":
        import cmpct.reader as reader_mod
    else:
        assert blob_sha(historical.read_bytes()) == HISTORICAL_BLOB
        spec = importlib.util.spec_from_file_location(
            "cmpct._j24f10_historical_reader", historical
        )
        assert spec and spec.loader
        reader_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader_mod)
    return reader_mod.CMPCT


def actor(path, action):
    before = os.stat(path)
    if action == "truncate":
        with open(path, "r+b", buffering=0) as handle:
            assert os.fstat(handle.fileno()).st_ino == before.st_ino
            os.ftruncate(handle.fileno(), 0)
            os.fsync(handle.fileno())
        after = os.stat(path)
        assert before.st_ino == after.st_ino and before.st_dev == after.st_dev
        assert after.st_size == 0
    elif action == "replace":
        other = path.with_name(path.name + ".replaced")
        other.write_bytes(b"Z" * before.st_size)
        assert os.stat(other).st_ino != before.st_ino
        os.replace(other, path)
        after = os.stat(path)
        assert before.st_ino != after.st_ino and after.st_size == before.st_size
    else:
        raise ValueError(action)
    return {"pid": os.getpid(), "action": action,
            "before_inode": before.st_ino, "after_inode": after.st_ino,
            "before_size": before.st_size, "after_size": after.st_size}


def child_case(target, which, action, historical):
    raw, archive = source_fixture()
    src = target / "direct-raw.cmpct"
    src.write_bytes(archive)
    Reader = get_reader(which, historical)
    checks, reports, preads = [], [], []
    with Reader(src) as reader:
        assert reader.by[NAME][4] == len(raw)
        assert reader.blobs[0][3] == 0
        assert bytes(reader.by[NAME][5]) == hashlib.sha256(raw).digest()
        assert reader.file_sha256(NAME) == hashlib.sha256(raw).digest()
        assert reader.read_range(NAME, 0, 512) == raw[:512]
        assert reader.read_range(NAME, SIZE // 2, 65536) == raw[SIZE//2:SIZE//2+65536]
        assert reader.read_range(NAME, SIZE-37, 37) == raw[-37:]
        assert reader.read_range(NAME, SIZE, 0) == b""
        for a,b in ((-1, 2), (SIZE-10, 20), (0, -1)):
            try:
                reader.read_range(NAME, a, b)
            except ValueError:
                checks.append("range-refused")
            else:
                raise AssertionError("invalid range accepted")
        if action != "none":
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--actor",
                 str(src), action], capture_output=True, text=True, check=True,
                timeout=20,
            )
            report = json.loads(result.stdout.strip())
            assert report["pid"] != os.getpid()
            reports.append(report)
            print("ACTOR_TRUTH=" + json.dumps(report, sort_keys=True), flush=True)
        real_pread = os.pread
        def audited_pread(fd, length, offset):
            if fd == reader.f.fileno():
                preads.append([length, offset])
            return real_pread(fd, length, offset)
        os.pread = audited_pread
        error = None
        output = None
        try:
            try:
                output = reader.read_range(NAME, SIZE-32768, 32768)
            except (IOError, OSError) as exc:
                error = type(exc).__name__ + ": " + str(exc)
        finally:
            os.pread = real_pread

    if action == "truncate":
        safe = which == "candidate" and error is not None and output is None
        assert safe, "candidate did not fail closed under same-inode truncation"
    else:
        safe = error is None and output == raw[-32768:]
        assert safe, "stable/replaced inode exact range lost"
    if which == "candidate" and action != "truncate":
        assert len(preads) >= 2, "descriptor not used for physical header and payload"
        assert all(n <= 32768 for n, _ in preads), "read amplified beyond requested range"
        assert any(n == 32768 for n, _ in preads), "payload pread not observed"
    if which == "candidate" and action == "truncate":
        assert preads, "candidate did not attempt descriptor access"
    result = {
        "which": which, "action": action, "platform": sys.platform,
        "original_sha256": sha(raw), "archive_sha256": sha(archive),
        "result_sha256": sha(output) if output is not None else None,
        "requested_length": 32768, "actual_length": len(output) if output else 0,
        "exception": error, "actor": reports[0] if reports else None,
        "source_pread_requests": preads, "range_rejections": len(checks),
        "outcome": "PASS" if safe else "FAIL",
    }
    print("RESULT_JSON=" + json.dumps(result, sort_keys=True), flush=True)


def controller(historical, output):
    import cmpct.reader as candidate
    assert os.name == "posix" and hasattr(os, "pread")
    loc = Path(candidate.__file__).resolve()
    assert not loc.is_relative_to(ROOT), "candidate must be installed outside checkout"
    assert blob_sha(loc.read_bytes()) == CANDIDATE_BLOB
    assert blob_sha(historical.read_bytes()) == HISTORICAL_BLOB
    cases = []
    with tempfile.TemporaryDirectory(prefix="j24f10-court-") as td:
        for which in ("historical", "candidate"):
            for action in ("none", "replace", "truncate"):
                p = Path(td) / (which + "-" + action)
                p.mkdir()
                cmd = [sys.executable, str(Path(__file__).resolve()), "--child",
                       str(p), which, action, str(historical)]
                result = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
                values = [json.loads(x.split("=",1)[1])
                          for x in result.stdout.splitlines()
                          if x.startswith("RESULT_JSON=")]
                actors = [json.loads(x.split("=",1)[1])
                          for x in result.stdout.splitlines()
                          if x.startswith("ACTOR_TRUTH=")]
                record = {"which": which, "action": action,
                          "returncode": result.returncode,
                          "signal": -result.returncode if result.returncode < 0 else None,
                          "result": values[0] if values else None,
                          "actor": actors[0] if actors else None,
                          "stderr_tail": result.stderr[-1200:]}
                if which == "historical" and action == "truncate":
                    assert result.returncode == -signal.SIGBUS, record
                    assert len(actors) == 1 and actors[0]["after_size"] == 0
                    assert not values, record
                else:
                    assert result.returncode == 0 and len(values) == 1, record
                    assert values[0]["outcome"] == "PASS", record
                    assert values[0]["range_rejections"] == 3, record
                    if action != "none":
                        assert len(actors) == 1, record
                cases.append(record)
    receipt = {
        "schema": "j24f10-direct-raw-range-v1",
        "historical_reader_blob": HISTORICAL_BLOB,
        "candidate_reader_blob": CANDIDATE_BLOB,
        "platform": sys.platform,
        "cases": cases,
        "decision": "DIRECT_RAW_RANGE_PREAD_TRUNCATION_FAIL_CLOSED",
        "nonclaims": [
            "general mmap S_PACK/compressed/S_SPARSE Reader recovery",
            "Win32 no-pread fallback", "raw selective-rate performance parity",
            "publication identity Issue #528", "release promotion",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    for rec in cases:
        print("J24F10_CASE=" + json.dumps(
            {k: rec[k] for k in ("which","action","returncode","signal")},
            sort_keys=True
        ), flush=True)
    print("J24F10_DECISION=" + receipt["decision"], flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--actor", nargs=2)
    parser.add_argument("--child", nargs=4)
    a = parser.parse_args()
    if a.actor:
        print(json.dumps(actor(Path(a.actor[0]), a.actor[1]), sort_keys=True))
    elif a.child:
        d, which, action, source = a.child
        child_case(Path(d), which, action, Path(source))
    else:
        if not a.parent or not a.output:
            parser.error("--parent and --output are required")
        controller(a.parent, a.output)


if __name__ == "__main__":
    main()
