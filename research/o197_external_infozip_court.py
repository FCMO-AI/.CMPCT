#!/usr/bin/env python3
"""O197: independent Info-ZIP validator of genuine O196 CMPCT 4 GiB ZIP64.

Do not modify O196 or CMPCT product code. See preregistered O197 hypothesis.
This is a Linux-only, bounded-stdout, evidence-generating scientific instrument.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import zipfile
from pathlib import Path

LOGICAL = 1 << 32
READ = 4 << 20
ZIP_LOCAL = struct.Struct("<IHHHHHIIIHH")
EXTERNAL_TIMEOUT = 180


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(READ):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(args: list[str], timeout: int = EXTERNAL_TIMEOUT) -> dict:
    start = time.perf_counter()
    proc = subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    return {
        "argv": args,
        "exit_code": proc.returncode,
        "wall_s": time.perf_counter() - start,
        "stdout_tail": proc.stdout[-2048:].decode("utf-8", errors="replace"),
        "stderr_tail": proc.stderr[-2048:].decode("utf-8", errors="replace"),
    }


def stream_external(zip_path: Path) -> dict:
    start = time.perf_counter()
    digest = hashlib.sha256()
    count = 0
    chunks = 0
    largest_chunk = 0
    with tempfile.TemporaryFile() as stderr_file:
        proc = subprocess.Popen(
            ["unzip", "-p", str(zip_path), "sparse.bin"],
            stdout=subprocess.PIPE, stderr=stderr_file,
            bufsize=0,
        )
        watchdog = threading.Timer(EXTERNAL_TIMEOUT, proc.kill)
        watchdog.daemon = True
        watchdog.start()
        try:
            assert proc.stdout is not None
            with proc.stdout:
                while True:
                    block = proc.stdout.read(READ)
                    if not block:
                        break
                    digest.update(block)
                    count += len(block)
                    chunks += 1
                    largest_chunk = max(largest_chunk, len(block))
                    if count > LOGICAL:
                        proc.kill()
                        raise AssertionError("external consumer decoded beyond the authenticated logical size")
            code = proc.wait(timeout=10)
        finally:
            watchdog.cancel()
            if proc.poll() is None:
                proc.kill()
                proc.wait()
        stderr_file.seek(0)
        stderr_tail = stderr_file.read()[-2048:].decode("utf-8", errors="replace")
    return {
        "exit_code": code,
        "wall_s": time.perf_counter() - start,
        "decoded_bytes": count,
        "decoded_sha256": digest.hexdigest(),
        "bounded_pipe_read_buffer_bytes": READ,
        "largest_stdout_read_bytes": largest_chunk,
        "stdout_read_calls": chunks,
        "stderr_tail": stderr_tail,
    }


def data_start_and_sizes(path: Path) -> dict:
    with path.open("rb") as src:
        fields = ZIP_LOCAL.unpack(src.read(ZIP_LOCAL.size))
        signature, needed, flags, method, dos_time, dos_date, crc32, c32, u32, name_n, extra_n = fields
        if signature != 0x04034B50 or needed < 45 or method != 8:
            raise AssertionError(("unexpected ZIP64 member header", signature, needed, method))
        name = src.read(name_n)
        extra = src.read(extra_n)
        if name != b"sparse.bin" or u32 != 0xFFFFFFFF or c32 != 0xFFFFFFFF:
            raise AssertionError(("wrong name or ZIP64 sentinels", name, u32, c32))
        cursor = 0
        zip64 = None
        while cursor + 4 <= len(extra):
            tag, length = struct.unpack_from("<HH", extra, cursor)
            cursor += 4
            if cursor + length > len(extra):
                raise AssertionError("invalid local ZIP extra TLV")
            if tag == 1:
                if zip64 is not None or length < 16:
                    raise AssertionError("duplicate or too-short ZIP64 extra")
                zip64 = struct.unpack_from("<QQ", extra, cursor)
            cursor += length
        if cursor != len(extra) or zip64 is None or zip64[0] != LOGICAL:
            raise AssertionError(("bad ZIP64 logical count", zip64))
        return {
            "local_header_bytes": ZIP_LOCAL.size + name_n + extra_n,
            "local_compressed_bytes": zip64[1],
            "local_logical_bytes": zip64[0],
            "local_version_needed": needed,
            "local_crc32_field": crc32,
            "flag_bits": flags,
        }


def corrupted_copy(original: Path, destination: Path, header: dict) -> dict:
    shutil.copyfile(original, destination)
    data_size = header["local_compressed_bytes"]
    if data_size < 32:
        raise AssertionError("compressed stream unexpectedly tiny")
    # Change compressed bytes only. Preserve the original ZIP and its CRC/index
    # so the independent extractor, rather than our harness, must detect damage.
    relative = min(1024, data_size // 2)
    absolute = header["local_header_bytes"] + relative
    if absolute >= original.stat().st_size:
        raise AssertionError("selected corruption falls outside archive")
    with destination.open("r+b") as stream:
        stream.seek(absolute)
        old = stream.read(1)
        if len(old) != 1:
            raise AssertionError("corruption read truncated")
        stream.seek(absolute)
        stream.write(bytes([old[0] ^ 0xFF]))
    return {"relative_compressed_offset": relative,
            "absolute_zip_byte_offset": absolute,
            "original_byte": old[0],
            "corrupted_byte": old[0] ^ 0xFF,
            "corrupt_copy_sha256": hash_file(destination)}


def execute(directory: Path, producer_receipt: Path, consumer_receipt: Path, record: dict) -> None:
    root = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    expected = os.environ["EVIDENCE_HEAD"]
    record["git_head"] = actual
    record["expected_head"] = expected
    if actual != expected:
        raise AssertionError(("source checkout drift", actual, expected))
    if os.name != "posix" or platform.system() != "Linux":
        raise RuntimeError("O197 preregistered Info-ZIP court is Ubuntu/Linux-only")
    path_tool = shutil.which("unzip")
    if not path_tool:
        raise RuntimeError("INFRA_BLOCKED: independent Info-ZIP executable missing")
    record["infozip_path"] = path_tool
    version = run_checked(["unzip", "-v"], timeout=15)
    record["infozip_version"] = version
    if version["exit_code"] != 0 or "UnZip" not in version["stdout_tail"]:
        raise RuntimeError("INFRA_BLOCKED: Info-ZIP version unavailable")

    producer = json.loads(producer_receipt.read_text(encoding="utf-8"))
    consumer = json.loads(consumer_receipt.read_text(encoding="utf-8"))
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    record["inherited_court"] = {"producer_verdict": producer.get("verdict"),
                                 "consumer_verdict": consumer.get("verdict")}
    if producer.get("verdict") != "AUTHENTIC_LINUX_4GIB_SPARSE_R24_SOURCE_BUILT":
        raise AssertionError(("inherited builder did not establish input", producer.get("verdict")))
    if consumer.get("verdict") != "AUTHENTIC_CROSSHOST_4GIB_ZIP64_FULL_READBACK_PASS":
        raise AssertionError(("inherited CMPCT ZIP64 did not pass", consumer.get("verdict")))
    if manifest["git_head"] != actual or producer.get("git_head") != actual or consumer.get("git_head") != actual:
        raise AssertionError("inherited producer/consumer provenance drift")
    archive = directory / "authentic-r24.cmpct"
    zip_path = directory / "result-linux.zip"
    if hash_file(archive) != manifest["archive_sha256"]:
        raise AssertionError("input CMPCT archive hash mismatch")
    source_sha = manifest["source_sha256"]
    if consumer.get("zip_member_logical_bytes") != LOGICAL or consumer.get("zip_member_sha256") != source_sha:
        raise AssertionError("inherited source vs ZIP full hash disagreement")
    zip_sha = hash_file(zip_path)
    if zip_sha != consumer["zip_sha256"] or zip_path.stat().st_size != consumer["zip_bytes"]:
        raise AssertionError("ZIP differed from the inherited genuine installed Reader result")
    record["source_sha256"] = source_sha
    record["archive_sha256"] = manifest["archive_sha256"]
    record["zip_sha256"] = zip_sha
    record["zip_bytes"] = zip_path.stat().st_size
    record["zip64_header"] = data_start_and_sizes(zip_path)

    # The external binary must also accept a tiny independent control ZIP;
    # failure here is tool/infrastructure ambiguity, not CMPCT product evidence.
    with tempfile.TemporaryDirectory(prefix="o197-infozip-") as td:
        control = Path(td) / "known_good.zip"
        with zipfile.ZipFile(control, "w", compression=zipfile.ZIP_DEFLATED) as writer:
            writer.writestr("control.txt", "ordinary Info-ZIP readiness control")
        readiness = run_checked(["unzip", "-tqq", str(control)], timeout=30)
        record["external_small_control"] = readiness
        if readiness["exit_code"] != 0:
            raise RuntimeError("INFRA_BLOCKED: independent unzip failed ordinary known-good ZIP")
        crc = run_checked(["unzip", "-tqq", str(zip_path)])
        record["external_full_crc_test"] = crc
        if crc["exit_code"] != 0:
            raise AssertionError(("independent Info-ZIP cannot validate CMPCT-produced ZIP64", crc))
        recovered = stream_external(zip_path)
        record["external_full_stream"] = recovered
        if recovered["exit_code"] != 0 or recovered["decoded_bytes"] != LOGICAL or recovered["decoded_sha256"] != source_sha:
            raise AssertionError(("Info-ZIP external full-size/content failure", recovered))
        corrupt = Path(td) / "corrupted-copy.zip"
        record["corruption"] = corrupted_copy(zip_path, corrupt, record["zip64_header"])
        negative = run_checked(["unzip", "-tqq", str(corrupt)])
        record["external_corruption_negative"] = negative
        if negative["exit_code"] == 0:
            raise AssertionError("independent Info-ZIP did not reject altered compressed bytes")
    if hash_file(zip_path) != zip_sha or hash_file(archive) != manifest["archive_sha256"]:
        raise AssertionError("original ZIP or CMPCT changed during independent verification")
    record["verdict"] = "AUTHENTIC_4GIB_ZIP64_INFOZIP_CRC_SHA_AND_NEGATIVE_PASS"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--producer-receipt", type=Path, required=True)
    parser.add_argument("--consumer-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    opts = parser.parse_args()
    report = {"schema": "cmpct-o197-independent-infozip-v1", "status": "UNMEASURED",
              "host": platform.platform(), "python": sys.version,
              "github_event_sha": os.environ.get("GITHUB_SHA"),
              "wall_start_ns": time.time_ns(), "verdict": "INCOMPLETE"}
    exit_code = 0
    try:
        execute(opts.directory, opts.producer_receipt, opts.consumer_receipt, report)
        report["status"] = "RESULT_BEARING"
    except BaseException as error:
        exit_code = 1
        report["verdict"] = "FAIL_OR_INFRA_UNCLASSIFIED_NO_CREDIT"
        report["status"] = "FAILED_OR_BLOCKED"
        report["error_type"] = type(error).__name__
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc(limit=14)
    finally:
        report["wall_end_ns"] = time.time_ns()
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("O197_VERDICT", report["verdict"], "GIT_HEAD", report.get("git_head"), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
