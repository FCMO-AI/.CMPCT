#!/usr/bin/env python3
"""O196: one authentic Linux 4GiB sparse CMPCT archive, three native ZIP64 readers.

Preregistered contract: docs/v031-research/2026-10-26-o196-authentic-crosshost-zip64-prereg.md.
Scientific harness only; no CMPCT product mutation or release claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from pathlib import Path

MIB = 1 << 20
GIB = 1 << 30
TOTAL = 4 * GIB
COUNT = 4096
HASH_CHUNK = 4 * MIB


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            data = f.read(HASH_CHUNK)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def source_head():
    root = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    target = os.environ["EVIDENCE_HEAD"]
    if head != target:
        raise AssertionError(("checked out source differs from PR HEAD", head, target))
    return root, head


def custody(root):
    import cmpct.reader as reader_module
    import cmpct.builder as builder_module
    installed = {}
    for short, module in (("reader", reader_module), ("builder", builder_module)):
        source = root / "src" / "cmpct" / (short + ".py")
        active = Path(module.__file__).resolve()
        if source.resolve() == active or active.read_bytes().replace(b"\r\n", b"\n") != source.read_bytes().replace(b"\r\n", b"\n"):
            raise AssertionError(("independent source custody failed", short, str(active)))
        installed[short] = {
            "path": str(active),
            "normalized_sha256": hashlib.sha256(active.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        }
    return installed


def create_sparse(path):
    if not (hasattr(os, "pwrite") and hasattr(os, "SEEK_HOLE") and hasattr(os, "SEEK_DATA")):
        raise RuntimeError("Linux producer needs pwrite and SEEK_DATA/SEEK_HOLE")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.ftruncate(fd, TOTAL)
        for i in range(COUNT):
            marker = hashlib.blake2s(i.to_bytes(4, "little")).digest() * 128
            if os.pwrite(fd, marker, i * MIB) != 4096:
                raise IOError(("short pwrite", i))
    finally:
        os.close(fd)
    st = path.stat()
    allocated = st.st_blocks * 512
    if allocated > 64 * MIB:
        raise AssertionError(("insufficient sparse physical allocation", allocated))
    fd = os.open(path, os.O_RDONLY)
    count = 0
    offset = 0
    try:
        while offset < TOTAL:
            try:
                start = os.lseek(fd, offset, os.SEEK_DATA)
            except OSError as err:
                if err.errno == 6:
                    break
                raise
            end = os.lseek(fd, start, os.SEEK_HOLE)
            if not offset <= start < end <= TOTAL:
                raise AssertionError(("invalid host sparse extent", offset, start, end))
            count += 1
            offset = end
    finally:
        os.close(fd)
    if count < 2048:
        raise AssertionError(("filesystem coalesced sparse extents", count))
    return {"allocated_bytes": allocated, "physical_extent_count": count, "source_mtime_ns": st.st_mtime_ns}


def produce(directory, record):
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.codec import S_SPARSE
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / "authentic-r24.cmpct"
    with tempfile.TemporaryDirectory(prefix="o196-source-") as d:
        input_dir = Path(d) / "input"
        input_dir.mkdir()
        sparse = input_dir / "sparse.bin"
        record.update(create_sparse(sparse))
        t = time.perf_counter()
        record["source_sha256"] = sha_file(sparse)
        record["source_sha_wall_s"] = time.perf_counter() - t
        cpu0, t = time.process_time(), time.perf_counter()
        Builder(input_dir, workers=1).build(archive)
        record["builder_cpu_s"] = time.process_time() - cpu0
        record["builder_wall_s"] = time.perf_counter() - t
        record["source_mtime_preserved"] = sparse.stat().st_mtime_ns == record["source_mtime_ns"]
    record["archive_sha256"] = sha_file(archive)
    record["archive_bytes"] = archive.stat().st_size
    with CMPCT(archive) as reader:
        if len(reader.files) != 1:
            raise AssertionError(("unexpected entries", len(reader.files)))
        row = reader.by["sparse.bin"]
        if row[4] != TOTAL or row[6][0] != S_SPARSE or len(row[6][1]) < 2048:
            raise AssertionError(("not authentic 4GiB sparse r24", row[4], row[6][0], len(row[6][1])))
        record["authenticated_r24_sparse_extent_count"] = len(row[6][1])
    manifest = {k: record[k] for k in (
        "git_head", "source_sha256", "archive_sha256", "archive_bytes",
        "authenticated_r24_sparse_extent_count", "allocated_bytes",
        "physical_extent_count", "source_mtime_ns"
    )}
    (directory / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    record["verdict"] = "AUTHENTIC_LINUX_4GIB_SPARSE_R24_SOURCE_BUILT"
    return record


def host_peak_rss():
    if os.name != "nt":
        try:
            import resource
            n = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return {"peak_rss_observed_bytes": n if sys.platform == "darwin" else n * 1024, "peak_rss_origin": "resource.RUSAGE_SELF.ru_maxrss"}
        except Exception:
            return {"peak_rss_observed_bytes": None, "peak_rss_origin": "unavailable"}
    try:
        import ctypes
        from ctypes import wintypes
        class Pmc(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        obj = Pmc()
        obj.cb = ctypes.sizeof(obj)
        proc = ctypes.windll.kernel32.GetCurrentProcess()
        if not ctypes.windll.psapi.GetProcessMemoryInfo(proc, ctypes.byref(obj), obj.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return {"peak_rss_observed_bytes": int(obj.PeakWorkingSetSize), "peak_rss_origin": "GetProcessMemoryInfo.PeakWorkingSetSize"}
    except Exception as err:
        return {"peak_rss_observed_bytes": None, "peak_rss_origin": "unavailable: " + repr(err)}


def consume(directory, record):
    from cmpct.reader import CMPCT
    from cmpct.codec import S_SPARSE
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["git_head"] != record["git_head"]:
        raise AssertionError(("producer/consumer source differs", manifest["git_head"], record["git_head"]))
    archive = directory / "authentic-r24.cmpct"
    if archive.stat().st_size != manifest["archive_bytes"] or sha_file(archive) != manifest["archive_sha256"]:
        raise AssertionError("source archive altered during download")
    record["producer_archive_sha256"] = manifest["archive_sha256"]
    record["producer_source_sha256"] = manifest["source_sha256"]
    record["received_archive_sha256"] = sha_file(archive)
    out = directory / ("result-" + platform.system().lower() + ".zip")
    with CMPCT(archive) as reader:
        if len(reader.files) != 1:
            raise AssertionError("unexpected entries")
        row = reader.by["sparse.bin"]
        if row[4] != TOTAL or row[6][0] != S_SPARSE or len(row[6][1]) != manifest["authenticated_r24_sparse_extent_count"]:
            raise AssertionError("inconsistent received authenticated sparse representation")
        original_range = reader.read_range
        counter = {"calls": 0, "logical_bytes": 0, "max_request": 0, "range_wall_ns": 0}
        def tracked(name, start, length):
            if name != "sparse.bin" or not 0 < length <= MIB:
                raise AssertionError(("ZIP64 requested invalid range", name, start, length))
            t = time.perf_counter_ns()
            block = original_range(name, start, length)
            counter["range_wall_ns"] += time.perf_counter_ns() - t
            if len(block) != length:
                raise AssertionError(("short range", start, length, len(block)))
            counter["calls"] += 1
            counter["logical_bytes"] += len(block)
            counter["max_request"] = max(counter["max_request"], length)
            return block
        reader.read_range = tracked
        t, cpu = time.perf_counter(), time.process_time()
        reader.export_zip(out, level=6)
        record["zip_export_wall_s"] = time.perf_counter() - t
        record["zip_export_cpu_s"] = time.process_time() - cpu
        record["zip_range_observation"] = {**counter, "range_wall_s": counter["range_wall_ns"] / 1e9}
    if counter["calls"] != COUNT or counter["logical_bytes"] != TOTAL:
        raise AssertionError(("ZIP64 streaming not fully exercised", counter))
    record["zip_bytes"] = out.stat().st_size
    record["zip_sha256"] = sha_file(out)
    with zipfile.ZipFile(out) as z:
        if z.namelist() != ["sparse.bin"]:
            raise AssertionError(("bad ZIP member names", z.namelist()))
        info = z.getinfo("sparse.bin")
        if info.file_size != TOTAL:
            raise AssertionError(("ZIP64 wrong decoded member length", info.file_size))
        t, h, decoded = time.perf_counter(), hashlib.sha256(), 0
        with z.open(info) as inp:
            while True:
                data = inp.read(HASH_CHUNK)
                if not data:
                    break
                decoded += len(data)
                h.update(data)
        record["full_zip_decode_wall_s"] = time.perf_counter() - t
        record["zip_member_crc32"] = info.CRC
        record["zip_member_compressed_bytes"] = info.compress_size
        record["zip_member_logical_bytes"] = decoded
        record["zip_member_sha256"] = h.hexdigest()
        record["crc_checked_on_zip_member_eof"] = True
        if decoded != TOTAL or h.hexdigest() != manifest["source_sha256"]:
            raise AssertionError(("full ZIP64 logical SHA mismatch", decoded, h.hexdigest(), manifest["source_sha256"]))
    if sha_file(archive) != manifest["archive_sha256"]:
        raise AssertionError("reader/export mutated original CMPCT archive")
    record.update(host_peak_rss())
    record["verdict"] = "AUTHENTIC_CROSSHOST_4GIB_ZIP64_FULL_READBACK_PASS"
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["produce", "consume"], required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = {
        "schema": "cmpct-o196-authentic-crosshost-zip64-v1",
        "mode": args.mode,
        "host": platform.platform(),
        "python": sys.version,
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "verdict": "INCOMPLETE",
    }
    code = 0
    try:
        root, head = source_head()
        receipt["git_head"] = head
        receipt["installed"] = custody(root)
        if args.mode == "produce":
            produce(args.artifact_dir, receipt)
        else:
            consume(args.artifact_dir, receipt)
    except BaseException as exc:
        code = 1
        receipt["verdict"] = "FAIL_OR_INFRA_UNCLASSIFIED_NO_CREDIT"
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)
        receipt["traceback"] = traceback.format_exc(limit=16)
    finally:
        receipt.update(host_peak_rss())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("O196_VERDICT", receipt["verdict"], "GIT_HEAD", receipt.get("git_head"), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
