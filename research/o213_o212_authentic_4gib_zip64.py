#!/usr/bin/env python3
"""O213: independent exact-head O212 Reader full 4GiB ZIP64 composition court.

Adapted from O196 source Git blob 47f3ce4d4a1ef61f89748e3699e863e2ab104e0e,
with original Builder and physical ZIP64 oracle preserved. O196 science is not
rewritten and no Reader implementation is changed.

Preregistered contract: docs/v031-research/2026-10-27-o213-authentic-post-admission-zip64-prereg.md.
Scientific harness only; no CMPCT product mutation or release claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import struct
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


# A second-root structural witness: parse the physical ZIP64 local header
# without trusting ZipFile's own index parser to verify its own writer.
ZIP_LOCAL_HEADER = struct.Struct("<IHHHHHIIIHH")


def inspect_zip64_local_header(path, expected_logical, expected_compressed):
    with Path(path).open("rb") as handle:
        raw = handle.read(ZIP_LOCAL_HEADER.size)
        if len(raw) != ZIP_LOCAL_HEADER.size:
            raise AssertionError("truncated ZIP64 local header")
        sig, need, flags, method, dos_time, dos_date, crc, c32, u32, name_n, extra_n = ZIP_LOCAL_HEADER.unpack(raw)
        if sig != 0x04034b50 or need < 45 or method != 8:
            raise AssertionError(("invalid ZIP64 local header", sig, need, method))
        name = handle.read(name_n)
        extra = handle.read(extra_n)
        if name != b"sparse.bin" or c32 != 0xFFFFFFFF or u32 != 0xFFFFFFFF:
            raise AssertionError(("bad ZIP64 local member or 32-bit size sentinel", name, c32, u32))
        pos, zip64 = 0, None
        while pos + 4 <= len(extra):
            tag, size = struct.unpack_from("<HH", extra, pos)
            pos += 4
            if pos + size > len(extra):
                raise AssertionError("ZIP extra TLV out of bounds")
            if tag == 1:
                if zip64 is not None or size < 16:
                    raise AssertionError("invalid or repeated ZIP64 extra block")
                zip64 = struct.unpack_from("<QQ", extra, pos)
            pos += size
        if pos != len(extra) or zip64 != (expected_logical, expected_compressed):
            raise AssertionError(("ZIP64 local true size mismatch", zip64, expected_logical, expected_compressed))
        return {"local_version_needed": need, "size_sentinels": True,
                "local_uncompressed_bytes_64bit": zip64[0],
                "local_compressed_bytes_64bit": zip64[1], "raw_extra_length": len(extra)}


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
    with tempfile.TemporaryDirectory(prefix="o213-source-") as d:
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
        # ctypes' default c_int return truncates Win64 pseudo HANDLE values.
        # Bind the actual WinAPI types instead of silently dropping RSS evidence.
        kernel = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Pmc), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        proc = kernel.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(proc, ctypes.byref(obj), obj.cb):
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
        record["independent_zip64_local_header"] = inspect_zip64_local_header(
            out, TOTAL, info.compress_size
        )
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
    if sys.platform.startswith("linux"):
        record["external_infozip"] = infozip_external_readback(out, manifest["source_sha256"])
        if os.environ.get("O213_BASE_SITE"):
            record["same_runner_admission_abba"] = compare_open_admission(archive, os.environ["O213_BASE_SITE"])
    record["verdict"] = "O213_POST_O212_AUTHENTIC_4GIB_ZIP64_FULL_READBACK_PASS"
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["produce", "consume"], required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = {
        "schema": "cmpct-o213-post-o212-authentic-crosshost-zip64-v1",
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
        print("O213_VERDICT", receipt["verdict"], "GIT_HEAD", receipt.get("git_head"), flush=True)
    return code


# O213 extensions: differently rooted external consumer and same-runner attribution.
# These are research witnesses, not release benchmark authority.
def infozip_external_readback(zip_path, expected_sha):
    import shutil
    unzip = shutil.which("unzip")
    if not unzip:
        return {"available": False, "verdict": "UNMEASURED_TOOL_ABSENT"}
    t0, cpu0 = time.perf_counter(), time.process_time()
    crc = subprocess.run([unzip, "-t", str(zip_path)], capture_output=True, text=True, timeout=180)
    if crc.returncode:
        raise AssertionError(("independent Info-ZIP CRC failed", crc.returncode, crc.stderr[-1000:]))
    crc_wall = time.perf_counter() - t0
    p = subprocess.Popen([unzip, "-p", str(zip_path), "sparse.bin"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    h, amount = hashlib.sha256(), 0
    t0 = time.perf_counter()
    try:
        while True:
            piece = p.stdout.read(4*MIB)
            if not piece:
                break
            amount += len(piece)
            h.update(piece)
        p.stdout.close()
        status = p.wait(timeout=180)
        stderr = p.stderr.read(1024)
        p.stderr.close()
        if status or amount != TOTAL or h.hexdigest() != expected_sha:
            raise AssertionError(("Info-ZIP complete content mismatch", status, amount, h.hexdigest(), expected_sha, stderr))
    finally:
        if p.poll() is None:
            p.kill()
            p.wait()
    return {"available": True, "crc_returncode": crc.returncode, "crc_wall_s": crc_wall,
            "full_decode_wall_s": time.perf_counter()-t0, "full_decoded_bytes": amount,
            "full_sha256": h.hexdigest(), "verdict": "PASS_INDEPENDENT_INFOZIP_FULL_4GIB"}


PROBE = r"""
import hashlib, json, os, subprocess, sys, time, resource
from pathlib import Path
import cmpct.reader as mod
from cmpct.reader import CMPCT
archive = sys.argv[1]
actual = Path(mod.__file__).read_bytes().replace(b'\r\n',b'\n')
blob = subprocess.check_output(['git','hash-object','--stdin'],input=actual).decode().strip()
assert blob == os.environ['O213_EXPECT_READER_BLOB'], (blob,os.environ['O213_EXPECT_READER_BLOB'])
start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
with CMPCT(archive) as reader:
    row = reader.by['sparse.bin']
    assert row[4] == 4*(1<<30)
    assert reader.read_range('sparse.bin',0,4)
wall = time.perf_counter_ns()-start_wall
cpu = time.process_time_ns()-start_cpu
print(json.dumps({'blob':blob,'wall_ns':wall,'cpu_ns':cpu,
                  'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},sort_keys=True))
"""

def compare_open_admission(archive, baseline_site):
    import statistics
    expected={"baseline":"d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44",
              "candidate":"ee598eec46531c4da44d90d37b67f783b0ab3299"}
    observations=[]
    for pair in range(8):
        order=("baseline","candidate") if pair%2==0 else ("candidate","baseline")
        for label in order:
            env=os.environ.copy()
            env.pop("PYTHONPATH",None)
            if label=="baseline":
                env["PYTHONPATH"]=baseline_site
            env["O213_EXPECT_READER_BLOB"]=expected[label]
            result=subprocess.run([sys.executable,"-c",PROBE,str(archive)],cwd=tempfile.gettempdir(),
                                  env=env,capture_output=True,text=True,timeout=60)
            if result.returncode:
                raise AssertionError(("open admission probe failed",label,result.stdout,result.stderr[-1600:]))
            receipt=json.loads(result.stdout.strip().splitlines()[-1])
            if receipt["blob"]!=expected[label]:
                raise AssertionError(("installed Reader blob drift",label,receipt["blob"]))
            receipt["variant"]=label
            receipt["pair"]=pair
            observations.append(receipt)
    baseline=[p for p in observations if p["variant"]=="baseline"]
    candidate=[p for p in observations if p["variant"]=="candidate"]
    median=lambda rows,k: statistics.median(q[k] for q in rows)
    wall_delta_ns=median(candidate,"wall_ns")-median(baseline,"wall_ns")
    cpu_delta_ns=median(candidate,"cpu_ns")-median(baseline,"cpu_ns")
    rss_delta_kib=median(candidate,"maxrss_kib")-median(baseline,"maxrss_kib")
    return {"observations":observations,
            "median_baseline_open_wall_ns":median(baseline,"wall_ns"),
            "median_candidate_open_wall_ns":median(candidate,"wall_ns"),
            "incremental_median_wall_ns":wall_delta_ns,
            "incremental_median_cpu_ns":cpu_delta_ns,
            "incremental_median_peak_rss_kib":rss_delta_kib,
            "preregistered_30ms_wall_discriminator_met":wall_delta_ns<=30_000_000,
            "preregistered_16mib_rss_discriminator_met":rss_delta_kib<=16384,
            "verdict":"MEASURED_RESEARCH_ONLY"}



if __name__ == "__main__":
    raise SystemExit(main())
