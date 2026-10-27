#!/usr/bin/env python3
"""J24Z02: preregistered reusable 64KiB Zstd output ownership court.

Independent RESEARCH ORACLE only. The original J24Z01 implementation, the CMPCT
Reader, format, verification gates and test definitions are not modified.
"""
from __future__ import annotations

import argparse
import binascii
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

from j24z01_zstd_stream_oracle import (
    MIB, WINDOW, NAME, InBuf, OutBuf, Stream, stream_range, vmhwm_kib,
)


def pooled_range(archive: Path, reader, start: int, length: int, fault: str = ""):
    """Same full-frame integrity as J24Z01, with one reused bounded output buffer."""
    from cmpct.codec import BHDR, BMAGIC, CODEC_ZSTD, S_BLOB

    row = reader.by[NAME]
    if row[6][0] != S_BLOB:
        raise AssertionError("unexpected physical storage")
    idx = row[6][1]
    off, us, cs, codec, ml = reader.blobs[idx]
    pos = reader.record_base + off
    magic, c, flags, reserved, rus, rcs, rml, crc_expected, sha_expected = BHDR.unpack_from(
        reader.mm, pos
    )
    if (magic != BMAGIC or codec != CODEC_ZSTD or c != CODEC_ZSTD
            or us != rus or cs != rcs or ml != rml or ml != 0
            or start < 0 or length < 0 or start + length > us):
        raise IOError("authenticated blob header or range mismatch")
    base = pos + BHDR.size + rml
    if base + cs > len(reader.mm):
        raise IOError("compressed frame outside archive")

    z = Stream()
    ctx = z.lib.ZSTD_createDStream()
    if not ctx:
        raise MemoryError("cannot create Zstd streaming decoder")
    fd = os.open(archive, os.O_RDONLY)
    # The output allocation and its ctypes pointer are reused, while every
    # hash/write-visible piece is consumed *synchronously* before the next
    # decompressStream call mutates this same private buffer. Source remains
    # a pinned descriptor with bounded copies of compressed input.
    in_raw = ctypes.create_string_buffer(WINDOW)
    out_raw = ctypes.create_string_buffer(WINDOW)
    in_pointer = ctypes.cast(in_raw, ctypes.c_void_p)
    out_pointer = ctypes.cast(out_raw, ctypes.c_void_p)
    out_view = memoryview(out_raw).cast("B")
    try:
        z.check(z.lib.ZSTD_initDStream(ctx))
        available = cs - (1 if fault == "truncate" else 0)
        virtual_suffix = 1 if fault == "trailing" else 0
        data_left = available + virtual_suffix
        current_size = 0
        current_pos = 0
        produced = 0
        crc = 0
        digest = hashlib.sha256()
        selected = bytearray()
        decode_calls = 0
        max_input = 0
        max_output = 0
        decoded_materialized_bytes = 0
        while True:
            if current_pos == current_size and data_left:
                next_n = min(WINDOW, data_left)
                src_offset = available + virtual_suffix - data_left
                if src_offset < available:
                    source_n = min(next_n, available - src_offset)
                    current = os.pread(fd, source_n, base + src_offset)
                    if len(current) != source_n:
                        raise IOError("truncated physical read")
                    if fault == "corrupt" and src_offset <= cs // 2 < src_offset + source_n:
                        mutated = bytearray(current)
                        mutated[cs // 2 - src_offset] ^= 0x40
                        current = bytes(mutated)
                else:
                    current = b"Z"  # deliberate decoder-visible trailing byte
                ctypes.memmove(in_pointer, current, len(current))
                current_size = len(current)
                data_left -= current_size
                current_pos = 0
                max_input = max(max_input, current_size)

            ib = InBuf(in_pointer, current_size, current_pos)
            ob = OutBuf(out_pointer, WINDOW, 0)
            previous = current_pos
            remaining = z.check(z.lib.ZSTD_decompressStream(
                ctx, ctypes.byref(ob), ctypes.byref(ib)
            ))
            decode_calls += 1
            if decode_calls > max(4096, (us // WINDOW) * 8 + 4096):
                raise IOError("decoder failed to finish within bounded calls")
            current_pos = ib.pos
            if ob.pos:
                # No out_raw.raw[:ob.pos] 64-KiB bytes allocation per iteration.
                piece = out_view[:ob.pos]
                chunk_start = produced
                produced += ob.pos
                if produced > us:
                    raise IOError("decoded content exceeds declared length")
                crc = binascii.crc32(piece, crc)
                digest.update(piece)
                if chunk_start < start + length and produced > start:
                    a = max(start - chunk_start, 0)
                    b = min(start + length - chunk_start, ob.pos)
                    selected.extend(piece[a:b])
            max_output = max(max_output, ob.pos)
            if remaining == 0:
                if data_left or current_pos != current_size:
                    raise IOError("trailing compressed data after first frame")
                break
            if ob.pos == 0 and current_pos == previous and not data_left and current_pos == current_size:
                raise IOError("truncated or non-progressing frame")
        if produced != us:
            raise IOError("decoded length differs from authenticated header")
        if crc & 0xffffffff != crc_expected or digest.digest() != sha_expected:
            raise IOError("full-frame CRC32/SHA256 mismatch")
        if len(selected) != length:
            raise IOError("selected range length differs")
        if row[5] is None or bytes(row[5]) != sha_expected:
            raise IOError("member-to-physical SHA256 mismatch")
        return bytes(selected), {
            "physical_decoded_bytes": produced,
            "decode_calls": decode_calls,
            "max_input_block": max_input,
            "max_output_block": max_output,
            "selected_bytes": len(selected),
            "full_crc32_verified": True,
            "full_sha256_verified": True,
            "zstd_version": z.version,
            "pooled_output_allocation_bytes": WINDOW,
            "decoded_materialized_bytes": decoded_materialized_bytes,
            "selected_materialized_bytes": len(selected),
        }
    finally:
        out_view.release()
        os.close(fd)
        z.lib.ZSTD_freeDStream(ctx)


def measure_child(archive: Path, mode: str, expected_sha: str):
    from cmpct.reader import CMPCT
    before = vmhwm_kib()
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    with CMPCT(archive) as reader:
        if mode == "control":
            result = reader.read_range(NAME, 32 * MIB, MIB)
            details = {"physical_decoded_bytes": 64 * MIB, "source": "CMPCT.read_range"}
        elif mode == "reference":
            result, details = stream_range(archive, reader, 32 * MIB, MIB)
        elif mode == "pooled":
            result, details = pooled_range(archive, reader, 32 * MIB, MIB)
        else:
            raise ValueError(mode)
        wall = time.perf_counter_ns() - wall0
        cpu = time.process_time_ns() - cpu0
        after = vmhwm_kib()
    assert len(result) == MIB and hashlib.sha256(result).hexdigest() == expected_sha
    return {
        "mode": mode, "wall_ns": wall, "cpu_ns": cpu,
        "VmHWM_before_KiB": before, "VmHWM_after_KiB": after,
        "VmHWM_increment_KiB": max(0, after - before), **details,
    }


def git_blob(repo: Path, path: str) -> str:
    return subprocess.check_output(
        ["git", "hash-object", path], cwd=repo, text=True
    ).strip()


def run(output: Path, rounds: int):
    if not sys.platform.startswith("linux") or not Path("/proc/self/status").exists():
        raise RuntimeError("Linux VmHWM required: no fabricated cross-host results")
    if rounds < 5:
        raise ValueError("minimum 5 independent fresh-process rounds")
    from cmpct.reader import CMPCT
    from o209_physical_decode_unit_court import _build_inputs

    repo = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    fixture_dir = output.parent / "j24z02-fixture"
    archives = _build_inputs(fixture_dir)
    archive = fixture_dir / "single.cmpct"
    expected_sha = archives["single"]["sample_sha256"]
    negatives = {}
    with CMPCT(archive) as reader:
        for arm, method in (
            ("reference", stream_range), ("pooled", pooled_range)
        ):
            cases = {}
            for fault in ("corrupt", "truncate", "trailing"):
                try:
                    method(archive, reader, 32 * MIB, MIB, fault=fault)
                except (OSError, ValueError, RuntimeError) as exc:
                    cases[fault] = {"rejected": True, "error_type": type(exc).__name__,
                                    "message": str(exc)}
                else:
                    raise AssertionError(f"{arm} accepted hostile frame {fault}")
            negatives[arm] = cases

    observations = []
    for cycle in range(rounds):
        # Rotate arms, not just alternating the two candidate arms.
        order = [("control", "reference", "pooled"),
                 ("pooled", "reference", "control"),
                 ("reference", "control", "pooled")][cycle % 3]
        for mode in order:
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "_child",
                 str(archive), mode, expected_sha],
                text=True, capture_output=True, check=True,
            )
            point = json.loads(child.stdout)
            point["cycle"] = cycle
            observations.append(point)

    def median(arm, key):
        return statistics.median(
            v[key] for v in observations if v["mode"] == arm
        )
    ref_cpu = median("reference", "cpu_ns")
    ref_wall = median("reference", "wall_ns")
    pooled_cpu = median("pooled", "cpu_ns")
    pooled_wall = median("pooled", "wall_ns")
    rss_margin = (median("pooled", "VmHWM_increment_KiB")
                  - median("reference", "VmHWM_increment_KiB")) / 1024.0
    improvement_cpu = 1 - pooled_cpu / ref_cpu
    improvement_wall = 1 - pooled_wall / ref_wall
    decision = ("POOLED_PYTHON_CONTINUE" if improvement_cpu >= 0.15
                and improvement_wall >= 0.15 and rss_margin <= 4
                else "POOLED_PYTHON_NOT_PRODUCT_PRIORITY")
    evidence = {
        "schema": "cmpct-j24z02-v1",
        "evidence_class": "independent Python/native research oracle; no product credit",
        "git_head": head,
        "reader_blob": git_blob(repo, "src/cmpct/reader.py"),
        "reference_blob": git_blob(repo, "research/j24z01_zstd_stream_oracle.py"),
        "candidate_blob": git_blob(repo, "research/j24z02_pooled_stream_court.py"),
        "fixture_builder_blob": git_blob(repo, "research/o209_physical_decode_unit_court.py"),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "same_archive": archives["single"],
        "physical_chunk_comparison": archives["chunked"],
        "hostile_frame_rejection": negatives,
        "raw_observations": observations,
        "summary": {
            "rounds": rounds,
            "control_median_cpu_ns": median("control", "cpu_ns"),
            "reference_median_cpu_ns": ref_cpu,
            "pooled_median_cpu_ns": pooled_cpu,
            "control_median_wall_ns": median("control", "wall_ns"),
            "reference_median_wall_ns": ref_wall,
            "pooled_median_wall_ns": pooled_wall,
            "reference_median_rss_increment_KiB": median("reference", "VmHWM_increment_KiB"),
            "pooled_median_rss_increment_KiB": median("pooled", "VmHWM_increment_KiB"),
            "pooled_minus_reference_rss_MiB": rss_margin,
            "pooled_cpu_fractional_improvement": improvement_cpu,
            "pooled_wall_fractional_improvement": improvement_wall,
            "decision": decision,
        },
        "limitations": [
            "One synthetic highly-compressible source, Linux host only",
            "Not a CMPCT product implementation or native shipping API",
            "Full logical 64MiB decoded for exact integrity despite 1MiB selective output",
            "No complete ZIP64 export or hostile changing-source/publication guarantee",
            "Kernel high-water measurement and process-start details are recorded, not product gate",
            "The original J24Z01 reference and Reader are immutable controls",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    print(json.dumps(evidence["summary"], sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "_child"))
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args()
    if ns.mode == "_child":
        if len(ns.args) != 3:
            raise SystemExit("_child ARCHIVE MODE SHA256")
        print(json.dumps(
            measure_child(Path(ns.args[0]), ns.args[1], ns.args[2]),
            sort_keys=True,
        ))
    else:
        if len(ns.args) not in (1, 2):
            raise SystemExit("run OUTPUT_JSON [ROUNDS]")
        run(Path(ns.args[0]), int(ns.args[1]) if len(ns.args) == 2 else 5)


if __name__ == "__main__":
    main()
