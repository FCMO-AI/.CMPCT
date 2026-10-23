#!/usr/bin/env python3
"""Scientific-only SEEK_DATA/SEEK_HOLE candidate enumeration: NOT CMPCT product code.

Compare to the actual installed PR #293 recover_blob_records, preserving all
physical header claims and unverified confidence. Do not authenticate content.
"""
from __future__ import annotations

import argparse
import binascii
import errno
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import sys
import tempfile
import time

from cmpct.codec import BHDR, BMAGIC, CODEC_RAW
from cmpct.transactions import recover_blob_records

_UNSUPPORTED = {getattr(errno, k) for k in ("EINVAL", "ENOTSUP", "EOPNOTSUPP", "ENOSYS") if hasattr(errno, k)}
_WINDOW = 1024 * 1024


def sparse_candidates(path: Path, *, force_unsupported: bool = False, admit: bool = True):
    """Return legacy-identical *unverified* candidates or fall back, never partial data."""
    path = Path(path)
    fallback_reason = None
    io = {"extent_count": 0, "seek_calls": 0, "read_bytes": 0}
    if force_unsupported or not (hasattr(os, "SEEK_DATA") and hasattr(os, "SEEK_HOLE")):
        fallback_reason = "unsupported"
    else:
        st = path.stat()
        # No fixture ID, file suffix, declared content or historical benchmark
        # enters admission. Dense sources use the already proven bounded scanner.
        if admit and (st.st_size < _WINDOW or
                      getattr(st, "st_blocks", 0) * 512 >= st.st_size // 2):
            fallback_reason = "dense-or-small"
    if fallback_reason is not None:
        return recover_blob_records(path), {**io, "route": "bounded-fallback", "reason": fallback_reason}

    rows = []
    fd = os.open(path, os.O_RDONLY)
    try:
        size = os.fstat(fd).st_size
        cursor = 0
        while cursor < size:
            try:
                start = os.lseek(fd, cursor, os.SEEK_DATA)
                io["seek_calls"] += 1
            except OSError as exc:
                if exc.errno == errno.ENXIO:
                    break
                if exc.errno in _UNSUPPORTED:
                    fallback_reason = "seek-unsupported"
                    break
                raise
            if not cursor <= start < size:
                fallback_reason = "incoherent-data"
                break
            try:
                stop = min(size, os.lseek(fd, start, os.SEEK_HOLE))
                io["seek_calls"] += 1
            except OSError as exc:
                if exc.errno in _UNSUPPORTED:
                    fallback_reason = "hole-unsupported"
                    break
                raise
            if stop <= start:
                fallback_reason = "incoherent-hole"
                break
            io["extent_count"] += 1
            if io["extent_count"] > 20000:
                fallback_reason = "extent-budget"
                break

            pos = start
            carry = b""
            while pos < stop:
                chunk = os.pread(fd, min(_WINDOW, stop - pos), pos)
                io["read_bytes"] += len(chunk)
                if not chunk:
                    fallback_reason = "short-data"
                    break
                scan = carry + chunk
                origin = pos - len(carry)
                search_at = 0
                while True:
                    index = scan.find(BMAGIC, search_at)
                    if index < 0:
                        break
                    absolute = origin + index
                    # Magic is nonzero: it cannot start in a hole. The remainder
                    # of a structurally plausible 64-byte header CAN span a
                    # zero-filled hole: fetch full logical header from the file.
                    header = os.pread(fd, BHDR.size, absolute)
                    io["read_bytes"] += len(header)
                    if len(header) != BHDR.size:
                        # Near EOF matches are rejected by inherited scanner.
                        if absolute + BHDR.size <= size:
                            fallback_reason = "short-header"
                            break
                    else:
                        _, codec, _, _, usize, csize, meta_len, crc32, declared_sha = BHDR.unpack(header)
                        if absolute + BHDR.size + meta_len + csize <= size:
                            rows.append({
                                "offset": absolute, "codec": codec, "usize": usize,
                                "csize": csize, "crc32": crc32,
                                "sha256": bytes(declared_sha).hex(),
                                "verification": "unverified",
                                "generation_membership": "unknown",
                            })
                    search_at = index + 1
                if fallback_reason is not None:
                    break
                carry = scan[-(len(BMAGIC) - 1):]
                pos += len(chunk)
            if fallback_reason is not None:
                break
            cursor = stop
    finally:
        os.close(fd)
    if fallback_reason:
        # Never return partial extent results or reinterpret an incoherent
        # filesystem as an empty archive.
        return recover_blob_records(path), {**io, "route": "bounded-fallback", "reason": fallback_reason}
    return rows, {**io, "route": "sparse-seeks", "logical_bytes": size}


def _frame(seed, payload=b"small"):
    return BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(payload), len(payload), 0,
        binascii.crc32(payload) & 0xffffffff,
        random.Random(seed).randbytes(32),
    ) + payload


def _sources(folder: Path):
    # Held-out layouts are deliberately different from the local exploratory
    # trial. The biggest file is logically >4 GiB, physically sparse.
    cases = {}
    size = (4 << 30) + (320 << 10)
    p = folder / "huge"
    with p.open("wb") as f:
        f.truncate(size)
        for j, offset in enumerate((13, _WINDOW - 2, (3 << 30) + 257, size - 256)):
            f.seek(offset)
            f.write(_frame(j + 832, b"file"))
    cases["huge"] = p

    p = folder / "many-extents"
    with p.open("wb") as f:
        f.truncate(32 << 20)
        for j in range(127):
            f.seek(j * 196608 + 13)
            f.write(_frame(j + 900))
    cases["many-extents"] = p

    p = folder / "cross-hole"
    with p.open("wb") as f:
        f.truncate(8 << 20)
        f.seek(4096 - 14)
        f.write(BHDR.pack(BMAGIC, 0, 0, 0, 0, 0, 0, 0, bytes(32))[:14])
    cases["cross-hole"] = p

    p = folder / "dense"
    r = random.Random(90073)
    data = bytearray(r.randbytes(16 << 20))
    for i, offset in enumerate((36, _WINDOW - 1, len(data) - 211)):
        frame = _frame(i + 1200)
        data[offset:offset + len(frame)] = frame
    p.write_bytes(data)
    cases["dense"] = p
    return cases


def _timed(fn):
    cpu = time.process_time_ns()
    wall = time.perf_counter_ns()
    result = fn()
    return result, {"wall_ms": (time.perf_counter_ns() - wall)/1e6,
                    "cpu_ms": (time.process_time_ns() - cpu)/1e6}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--large-repeats", type=int, default=2)
    args = ap.parse_args()
    report = {"question": "Can physical sparse holes be skipped without changing unverified candidate framing?",
              "product_implementation_changed": False, "cases": {}}
    with tempfile.TemporaryDirectory(prefix="cmpct-sparse-seek-court-") as td:
        for label, path in _sources(Path(td)).items():
            expected = recover_blob_records(path)
            alt, metrics = sparse_candidates(path, admit=False)
            assert alt == expected, (label, "oracle parity", expected[:5], alt[:5])
            admitted, route = sparse_candidates(path)
            assert admitted == expected, (label, "admission parity")
            unsupported, fallback = sparse_candidates(path, force_unsupported=True)
            assert unsupported == expected and fallback["route"] == "bounded-fallback"
            counts = {"source_sha256": hashlib.sha256(
                      json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                      "candidate_count": len(expected), "logical_bytes": path.stat().st_size,
                      "allocated_bytes": getattr(path.stat(), "st_blocks", 0)*512,
                      "physical_oracle": metrics, "admission": route}
            if label in ("huge", "dense"):
                timing = {"bounded": [], "seek": []}
                count = args.large_repeats if label == "huge" else 3
                for mode in (["bounded", "seek", "seek", "bounded"] * count):
                    fn = (lambda: recover_blob_records(path)) if mode == "bounded" else (
                        lambda: sparse_candidates(path, admit=False)[0])
                    got, measurement = _timed(fn)
                    assert got == expected
                    timing[mode].append(measurement)
                counts["repeated"] = timing
                counts["medians"] = {mode: {
                    k: statistics.median(v[k] for v in samples)
                    for k in ("wall_ms", "cpu_ms")} for mode, samples in timing.items()}
            report["cases"][label] = counts
    report["decision"] = "EXACT_HEADER_PARITY_IF_ALL_ASSERTIONS_PASS; SCIENTIFIC_ONLY"
    report["limitations"] = [
        "source is synthetic, not an authenticated r24 archive",
        "filesystem SEEK_* semantics and sparse extents are OS/provider dependent",
        "no immutable snapshot under concurrent source changes",
        "inherited scanner and oracle return unverified physical header candidates",
        "process-start and import cost excluded from within-process CPU/wall timing",
        "stored bytes, decode, reader, portability and release not measured",
    ]
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
