#!/usr/bin/env python3
"""O195: authentic 4 GiB sparse r24 Reader/ZIP64 A-B research, not a product patch.

Source authority: preregistration 2026-10-26-o195-sparse-range-ab-prereg.md,
O193 exact-head source. This intentionally leaves CMPCT product unmodified.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import os
import platform
import resource
import signal
import statistics
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
EXTENTS = 4096
CHUNK = MIB
HASH_CHUNK = 4 * MIB


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(HASH_CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def physical_extents(path: Path, size: int):
    if not hasattr(os, "SEEK_DATA") or not hasattr(os, "SEEK_HOLE"):
        raise RuntimeError("host lacks SEEK_DATA/SEEK_HOLE")
    fd = os.open(path, os.O_RDONLY)
    extents = []
    pos = 0
    try:
        while pos < size:
            try:
                off = os.lseek(fd, pos, os.SEEK_DATA)
            except OSError as err:
                if err.errno == 6:  # ENXIO: no further data.
                    break
                raise
            end = min(os.lseek(fd, off, os.SEEK_HOLE), size)
            if not (pos <= off < end <= size):
                raise AssertionError(("invalid host extent", pos, off, end))
            extents.append((off, end - off))
            pos = end
    finally:
        os.close(fd)
    return extents


def build_index(extents, blobs, logical_size):
    """Refuse unsorted/overlapping, negative, unbounded or inconsistent extents."""
    starts, ends = [], []
    last_end = 0
    for row in extents:
        if len(row) != 3:
            raise ValueError("bad sparse extent record")
        off, ln, ids = row
        if not isinstance(off, int) or not isinstance(ln, int):
            raise ValueError("non-integer extent bounds")
        if off < last_end or ln <= 0 or off + ln > logical_size or not ids:
            raise ValueError("unordered, overlapping or invalid sparse extent")
        if any(not isinstance(idx, int) or idx < 0 or idx >= len(blobs) for idx in ids):
            raise ValueError("out of bounds chunk ID")
        if sum(int(blobs[idx][1]) for idx in ids) != ln:
            raise ValueError("extent chunk lengths inconsistent")
        starts.append(off)
        ends.append(off + ln)
        last_end = off + ln
    if not starts:
        raise ValueError("no physical extents")
    return starts, ends


def independent_zip_sha(zip_path: Path, expected_sha: str):
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.namelist() == ["sparse.bin"], archive.namelist()
        info = archive.getinfo("sparse.bin")
        assert info.file_size == TOTAL, info.file_size
        digest = hashlib.sha256()
        logical_read = 0
        # ZipExtFile checks CRC on reaching EOF; do not call testzip() and double
        # the four-gigabyte read just to request the same CRC verification.
        with archive.open(info) as member:
            while True:
                chunk = member.read(HASH_CHUNK)
                if not chunk:
                    break
                digest.update(chunk)
                logical_read += len(chunk)
        assert logical_read == TOTAL
        assert digest.hexdigest() == expected_sha, ("wrong full ZIP member SHA", digest.hexdigest())
        return {
            "full_decoded_sha256": digest.hexdigest(),
            "full_decoded_bytes": logical_read,
            "member_crc32_from_zip": info.CRC,
            "member_compressed_bytes": info.compress_size,
            "zip64_member_file_size": info.file_size,
            "stdlib_crc_checked_on_eof": True,
        }


def run():
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.codec import S_SPARSE
    import cmpct.reader as reader_module

    def timed_out(signum, frame):
        raise TimeoutError("O195 16-minute process budget exceeded")
    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(16 * 60)  # Host experiment limit, independent of job timeout.
    # Prevent a future accidental whole-member materialization from OOM-killing
    # the hosted runner. One static process cap is not a measured RSS claim.
    cap = 2 * GIB
    old_soft, old_hard = resource.getrlimit(resource.RLIMIT_AS)
    target_soft = min(cap, old_hard) if old_hard != resource.RLIM_INFINITY else cap
    resource.setrlimit(resource.RLIMIT_AS, (target_soft, old_hard))

    root_repo = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root_repo, text=True).strip()
    requested_head = os.environ["EVIDENCE_HEAD"]
    assert head == requested_head, ("source head mismatch", head, requested_head)
    source_reader = root_repo / "src/cmpct/reader.py"
    installed_reader = Path(reader_module.__file__).resolve()
    assert installed_reader != source_reader
    source_bytes = source_reader.read_bytes().replace(b"\r\n", b"\n")
    installed_bytes = installed_reader.read_bytes().replace(b"\r\n", b"\n")
    assert installed_bytes == source_bytes, "independently installed Reader differs from exact checked-out source"

    record = {
        "schema": "cmpct-o195-authentic-sparse-range-ab-v1",
        "git_head": head,
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "installed_reader_normalized_sha256": hashlib.sha256(installed_bytes).hexdigest(),
        "host": platform.platform(),
        "logical_input_bytes": TOTAL,
        "expected_physical_extent_count": EXTENTS,
        "requested_export_chunk_bytes": CHUNK,
        "source_identity": "same authentic source/archive/installed Reader for all A/B arms",
        "no_format_or_product_mutation": True,
        "genuine_ge_4gib": False,
    }

    with tempfile.TemporaryDirectory(prefix="o195-sparse-") as td:
        base = Path(td)
        source_dir = base / "source"
        source_dir.mkdir()
        source_file = source_dir / "sparse.bin"
        fd = os.open(source_file, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.ftruncate(fd, TOTAL)
            for i in range(EXTENTS):
                marker = hashlib.blake2s(i.to_bytes(4, "little")).digest()
                actual = marker * 128  # 4 KiB distinct, physically allocated at each 1 MiB step.
                assert len(actual) == 4096
                sent = os.pwrite(fd, actual, i * MIB)
                if sent != 4096:
                    raise IOError(("short host pwrite", i, sent))
        finally:
            os.close(fd)
        st = source_file.stat()
        record["source_allocated_bytes_st_blocks"] = int(st.st_blocks * 512)
        record["source_physical_extents"] = physical_extents(source_file, TOTAL)
        record["physical_extent_count"] = len(record["source_physical_extents"])
        record["physical_extent_allocation_bytes"] = sum(n for _, n in record["source_physical_extents"])
        if st.st_blocks * 512 > 64 * MIB or len(record["source_physical_extents"]) < 2048:
            raise RuntimeError("host sparse topology not admissible to O195 high-E test")
        recorded_mtime = st.st_mtime_ns

        before = time.perf_counter()
        cpu_before = time.process_time()
        record["source_sha256"] = sha_file(source_file)
        record["independent_source_hash_wall_s"] = time.perf_counter() - before
        archive_file = base / "genuine-r24.cmpct"
        before = time.perf_counter()
        cpu_before = time.process_time()
        Builder(source_dir, workers=1).build(archive_file)
        record["builder_wall_s"] = time.perf_counter() - before
        record["builder_cpu_s"] = time.process_time() - cpu_before
        record["cmpct_archive_bytes"] = archive_file.stat().st_size
        record["cmpct_archive_sha256"] = sha_file(archive_file)
        original_archive_sha = record["cmpct_archive_sha256"]

        before = time.perf_counter()
        with CMPCT(archive_file) as reader:
            record["reader_open_wall_s"] = time.perf_counter() - before
            assert len(reader.files) == 1, reader.files
            row = reader.by["sparse.bin"]
            assert row[6][0] == S_SPARSE, ("Builder did not select genuine S_SPARSE", row[6][0])
            assert row[4] == TOTAL
            extents = row[6][1]
            record["authenticated_index_extent_count"] = len(extents)
            if len(extents) < 2048:
                raise RuntimeError("Builder extent count too small for high-E cost court")
            record["real_source_sparse_used"] = True
            starts_ends_before = time.perf_counter()
            starts, ends = build_index(extents, reader.blobs, TOTAL)
            record["index_construction_wall_s"] = time.perf_counter() - starts_ends_before
            record["index_python_object_bytes_estimate"] = (
                sys.getsizeof(starts) + sys.getsizeof(ends) +
                sum(sys.getsizeof(x) for x in ends)
            )

            bad_extents = [list(x) for x in extents]
            bad_extents[0], bad_extents[1] = bad_extents[1], bad_extents[0]
            try:
                build_index(bad_extents, reader.blobs, TOTAL)
                raise AssertionError("unordered hostile index passed validation")
            except ValueError:
                record["hostile_out_of_order_extents_rejected"] = True

            original_read_range = reader.read_range
            index_operations = {"bisect_calls": 0, "candidate_extent_visits": 0}
            def index_range(name, start, length):
                if name != "sparse.bin":
                    return original_read_range(name, start, length)
                end = start + length
                if start < 0 or length < 0 or end > TOTAL:
                    return original_read_range(name, start, length)
                output = bytearray(length)
                index_operations["bisect_calls"] += 1
                position = bisect.bisect_right(ends, start)
                while position < len(extents) and extents[position][0] < end:
                    off, ln, ids = extents[position]
                    index_operations["candidate_extent_visits"] += 1
                    cursor = off
                    for idx in ids:
                        chunk_length = reader.blobs[idx][1]
                        chunk_end = cursor + chunk_length
                        if chunk_end > start and cursor < end:
                            chunk_data = reader._blob(idx)
                            a = max(start, cursor) - cursor
                            z = min(end, chunk_end) - cursor
                            output[max(cursor, start)-start:min(chunk_end, end)-start] = chunk_data[a:z]
                        cursor = chunk_end
                    position += 1
                return bytes(output)

            # Differently rooted range samples from real host pread, including
            # allocated/hole boundaries and near-end ranges. Never use the
            # candidate Reader as its own truth oracle.
            offsets = [0, 4096, MIB-2048, MIB-128, TOTAL-MIB,
                       TOTAL-4096, TOTAL-128, 511*MIB-64, 2048*MIB+4096]
            offsets += [i*MIB+ (i*101 % (MIB-4096)) for i in range(0, EXTENTS, 127)]
            with source_file.open("rb", buffering=0) as stream:
                for off in offsets:
                    n = min(8192, TOTAL-off)
                    source = os.pread(stream.fileno(), n, off)
                    baseline = original_read_range("sparse.bin", off, n)
                    candidate = index_range("sparse.bin", off, n)
                    assert source == baseline == candidate, ("range mismatch", off, n)
            record["independent_range_sample_count"] = len(offsets)
            record["independent_range_bytes_identical"] = True

            def export_arm(kind, ordinal):
                counter = {"calls":0, "logical_requested_bytes":0,
                           "max_requested":0, "range_wall_ns":0}
                index_visits_before = index_operations["candidate_extent_visits"]
                bisects_before = index_operations["bisect_calls"]
                delegated = original_read_range if kind == "linear" else index_range
                def tracked(name, offset, length):
                    assert name == "sparse.bin"
                    assert 0 <= length <= MIB
                    start_ns = time.perf_counter_ns()
                    raw = delegated(name, offset, length)
                    counter["range_wall_ns"] += time.perf_counter_ns()-start_ns
                    counter["calls"] += 1
                    counter["logical_requested_bytes"] += length
                    counter["max_requested"] = max(counter["max_requested"], length)
                    return raw
                reader.read_range = tracked
                dest = base / ("output-" + str(ordinal) + "-" + kind + ".zip")
                begin = time.perf_counter()
                cpu = time.process_time()
                # Public export_zip must really route through O193 ZIP64 fallback
                # because this is a genuine >= 0xffffffff-byte member.
                reader.export_zip(dest, level=6)
                wall = time.perf_counter() - begin
                cpu_s = time.process_time() - cpu
                result = {
                    "kind":kind, "ordinal":ordinal,"export_wall_s":wall,
                    "export_cpu_s":cpu_s,"range_calls":counter["calls"],
                    "range_wall_s":counter["range_wall_ns"]/1e9,
                    "requested_logical_bytes":counter["logical_requested_bytes"],
                    "max_range_requested":counter["max_requested"],
                    "zip_stored_bytes":dest.stat().st_size,
                    "zip_sha256":sha_file(dest),
                    "model_original_extent_visits":len(extents)*counter["calls"],
                    "indexed_candidate_extent_visits_this_arm":index_operations["candidate_extent_visits"]-index_visits_before,
                    "indexed_bisect_calls_this_arm":index_operations["bisect_calls"]-bisects_before,
                    "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                }
                assert counter["calls"] == math.ceil(TOTAL/MIB), counter
                assert counter["logical_requested_bytes"] == TOTAL
                assert counter["max_requested"] == MIB
                record.setdefault("arms",[]).append(result)
                print("O195_ARM",kind,ordinal,round(wall,3),round(cpu_s,3),flush=True)
                return dest

            # ABBA source-controlled within-process. Does not claim independent
            # cold-state replicas or a full r24/ZIP performance-release gate.
            exports = []
            for ordinal, kind in enumerate(("linear","indexed","indexed","linear")):
                exports.append(export_arm(kind, ordinal))
            reader.read_range = original_read_range
            sizes = {x["zip_stored_bytes"] for x in record["arms"]}
            digests = {x["zip_sha256"] for x in record["arms"]}
            assert len(sizes) == 1 and len(digests) == 1, ("different ZIP bytes",sizes,digests)

            # Two differently rooted full ZIP64 readbacks. Identical ZIP bytes
            # in all four arms entail identical content for remaining two.
            record["independent_zip_decode"] = []
            for i in (0,1):
                record["independent_zip_decode"].append(
                    {"ordinal":i, **independent_zip_sha(exports[i], record["source_sha256"])}
                )
            l = [x["export_wall_s"] for x in record["arms"] if x["kind"]=="linear"]
            b = [x["export_wall_s"] for x in record["arms"] if x["kind"]=="indexed"]
            lm, bm = statistics.median(l), statistics.median(b)
            record["linear_median_export_wall_s"] = lm
            record["indexed_median_export_wall_s"] = bm
            record["indexed_full_export_wall_delta_percent"] = 100.0*(lm-bm)/lm
            record["indexed_plus_one_time_build_median_wall_s"] = bm+record["index_construction_wall_s"]
            record["index_cold_build_charged"] = True

        assert sha_file(archive_file) == original_archive_sha
        assert source_file.stat().st_mtime_ns == recorded_mtime
        record["archive_unchanged"] = True
        record["source_file_timestamp_unchanged"] = True
        record["genuine_ge_4gib"] = True
        record["final_process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        record["verdict"] = "AUTHENTIC_4GIB_SPARSE_ZIP64_ABBA_EVIDENCE_NO_PROMOTION"
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = None
    exit_code = 0
    try:
        result = run()
    except BaseException as exc:
        result = {
            "schema":"cmpct-o195-authentic-sparse-range-ab-v1",
            "verdict":"FAIL_OR_UNSUPPORTED_NO_PRODUCT_CREDIT",
            "exception":type(exc).__name__,
            "error":str(exc),
            "traceback":traceback.format_exc(limit=16),
            "evidence_head":os.environ.get("EVIDENCE_HEAD"),
        }
        exit_code = 1
    finally:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",encoding="utf-8")
        print("O195_VERDICT",result["verdict"],"EVIDENCE",args.out,flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
