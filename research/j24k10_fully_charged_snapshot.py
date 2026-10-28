"""J24K10: exact-CMPCT-component physical witness vs fully charged file-copy session.

RESEARCH ONLY. The source fixture is artificial, with synthetic unrelated archive
padding. Neither a private writable copy nor an mmap makes source bytes immutable.
This cost oracle never claims product speed, safe concurrent mutation, or release readiness.
"""
from __future__ import annotations

import hashlib
import json
import mmap
import os
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time
import zipfile

from cmpct.codec import BHDR, range_vzip
from j24k09_physical_witness_economics import fixture


def _run(reader, contents, recipe, nqueries, mode, source_file, source_size, scratch):
    source_mmap = reader.mm
    scratch_size = 0
    cache_bytes = 0
    copy_ns = 0
    try:
        start_ns = time.perf_counter_ns()
        cpu_ns = time.process_time_ns()
        if mode == "copy_then_prove_once":
            # Private scratch is a distinct file and must be fully copied per session;
            # no snapshot is gifted to the optimizer or amortized across measurements.
            with open(source_file, "rb") as src, open(scratch, "wb") as dest:
                shutil.copyfileobj(src, dest, 1024 * 1024)
                dest.flush()
            scratch_size = scratch.stat().st_size
            if scratch_size != source_size:
                raise AssertionError("short private file copy")
            copy_ns = time.perf_counter_ns() - start_ns
            copied = open(scratch, "rb")
            try:
                copied_mm = mmap.mmap(copied.fileno(), 0, access=mmap.ACCESS_READ)
                try:
                    reader.mm = copied_mm
                    physical = [reader._vzip_physical_stream_size(zipfile.ZIP_STORED, 0, i, i)
                                for i in range(1, len(recipe[2]) + 1)]
                    if any(x != 64 for x in physical):
                        raise AssertionError("wrong length in private copy")
                    cache_bytes = sys.getsizeof(physical) + sum(sys.getsizeof(x) for x in physical)

                    def size(_method, _mode, rawref, _streamref):
                        return physical[rawref - 1]

                    for _ in range(nqueries):
                        if range_vzip(recipe, contents.__getitem__, _never_deflate,
                                      len(recipe[2]) * 64 + 6, 1, size) != b"G":
                            raise AssertionError("copy-session returned incorrect suffix")
                finally:
                    reader.mm = source_mmap
                    copied_mm.close()
            finally:
                copied.close()
        elif mode == "per_query_physical":
            for _ in range(nqueries):
                if range_vzip(recipe, contents.__getitem__, _never_deflate,
                              len(recipe[2]) * 64 + 6, 1,
                              reader._vzip_physical_stream_size) != b"G":
                    raise AssertionError("physical-session returned incorrect suffix")
        else:
            raise ValueError(mode)
        elapsed = time.perf_counter_ns() - start_ns
        cpu_elapsed = time.process_time_ns() - cpu_ns
        return {"wall_ns": elapsed, "cpu_ns": cpu_elapsed,
                "copy_wall_ns": copy_ns, "copied_bytes": scratch_size,
                "extra_cache_bytes": cache_bytes}
    finally:
        reader.mm = source_mmap
        if scratch.exists():
            scratch.unlink()


def _never_deflate(*args):
    raise AssertionError("STORED source should not call Deflate")


def main():
    # Archive size is deliberately independent of logical member/stream count.
    # The additional bytes are synthetic unrelated storage: a lower-rung model,
    # NOT a valid Builder-produced revision-24 archive or complete Reader court.
    counts = (512, 4096)
    paddings = (0, 64 * 1024 * 1024)
    queries = (1, 8, 64)
    modes = ("per_query_physical", "copy_then_prove_once")
    for n in counts:
        reader, contents, recipe = fixture(n)
        with tempfile.TemporaryDirectory(prefix="j24k10-") as temp:
            path = Path(temp) / "source.bin"
            scratch = Path(temp) / "private-copy.bin"
            original = reader.mm
            for padding in paddings:
                with open(path, "wb") as f:
                    f.write(original)
                    if padding:
                        # One filesystem write call per block, not a 64 MiB Python bytes object.
                        chunk = b"Z" * (1024 * 1024)
                        for _ in range(padding // len(chunk)):
                            f.write(chunk)
                source_size = path.stat().st_size
                source_sha = hashlib.sha256(path.read_bytes()).hexdigest()
                with open(path, "rb") as source:
                    mapped = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)
                    reader.mm = mapped
                    try:
                        for q in queries:
                            raw = {m: [] for m in modes}
                            for cycle in range(5):
                                order = (modes[0], modes[1], modes[1], modes[0])
                                if cycle % 2:
                                    order = (modes[1], modes[0], modes[0], modes[1])
                                for mode in order:
                                    raw[mode].append(_run(reader, contents, recipe, q, mode,
                                                          path, source_size, scratch))
                            medians = {m: {k: statistics.median(v[k] for v in raw[m])
                                           for k in ("wall_ns", "cpu_ns", "copy_wall_ns",
                                                     "copied_bytes", "extra_cache_bytes")}
                                       for m in modes}
                            ratio = medians[modes[0]]["wall_ns"] / max(1, medians[modes[1]]["wall_ns"])
                            result = {
                                "schema": "cmpct-j24k10-quiescent-copy-cost-oracle-v1",
                                "scientific_tier": "component_only_not_installed_reader_product",
                                "source_sha256": source_sha,
                                "source_bytes": source_size,
                                "streams": n,
                                "padding_bytes": padding,
                                "queries": q,
                                "no_external_writer_during_measurement": True,
                                "copy_not_immutable_against_its_owner": True,
                                "disk_copy_not_atomic_during_source_mutation": True,
                                "source_format_not_full_r24": True,
                                "extra_mapped_archive_bytes": source_size,
                                "medians": medians,
                                "speed_ratio_physical_over_copied": ratio,
                                "raw": raw,
                            }
                            print("J24K10_RESULT=" + json.dumps(result, sort_keys=True), flush=True)
                    finally:
                        reader.mm = original
                        mapped.close()


if __name__ == "__main__":
    main()
