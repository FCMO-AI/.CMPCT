#!/usr/bin/env python3
"""J24Z01: bounded libzstd streaming oracle against O209 authentic 64MiB S_BLOB.

Research-only: uses the *same archive bytes* as the original CMPCT Reader, and
fully charges decoded CRC32/SHA256 work. Not a Reader patch or release benchmark.
Linux-only: kernel /proc/self/status VmHWM measures fresh child processes.
"""
from __future__ import annotations

import argparse
import binascii
import ctypes
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

MIB = 1024 * 1024
WINDOW = 64 * 1024
NAME = "payload.bin"


class InBuf(ctypes.Structure):
    _fields_ = [("src", ctypes.c_void_p), ("size", ctypes.c_size_t), ("pos", ctypes.c_size_t)]


class OutBuf(ctypes.Structure):
    _fields_ = [("dst", ctypes.c_void_p), ("size", ctypes.c_size_t), ("pos", ctypes.c_size_t)]


class Stream:
    def __init__(self):
        path = ctypes.util.find_library("zstd")
        if not path:
            raise RuntimeError("system libzstd unavailable: no dependency downgrade")
        self.lib = ctypes.CDLL(path)
        L = self.lib
        L.ZSTD_createDStream.argtypes = []
        L.ZSTD_createDStream.restype = ctypes.c_void_p
        L.ZSTD_initDStream.argtypes = [ctypes.c_void_p]
        L.ZSTD_initDStream.restype = ctypes.c_size_t
        L.ZSTD_decompressStream.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(OutBuf), ctypes.POINTER(InBuf)
        ]
        L.ZSTD_decompressStream.restype = ctypes.c_size_t
        L.ZSTD_isError.argtypes = [ctypes.c_size_t]
        L.ZSTD_isError.restype = ctypes.c_uint
        L.ZSTD_getErrorName.argtypes = [ctypes.c_size_t]
        L.ZSTD_getErrorName.restype = ctypes.c_char_p
        L.ZSTD_freeDStream.argtypes = [ctypes.c_void_p]
        L.ZSTD_freeDStream.restype = ctypes.c_size_t
        L.ZSTD_versionString.argtypes = []
        L.ZSTD_versionString.restype = ctypes.c_char_p
        self.version = L.ZSTD_versionString().decode()

    def check(self, value):
        if self.lib.ZSTD_isError(value):
            raise IOError("libzstd streaming error: " + self.lib.ZSTD_getErrorName(value).decode())
        return value


def vmhwm_kib():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmHWM:"):
            return int(line.split()[1])
    raise RuntimeError("Linux VmHWM unavailable")


def stream_range(archive: Path, reader, start: int, length: int, fault: str = ""):
    """One authentic Zstd S_BLOB: bounded input/output, full CRC/SHA, strict EOS."""
    from cmpct.codec import BHDR, BMAGIC, CODEC_ZSTD, S_BLOB
    row = reader.by[NAME]
    if row[6][0] != S_BLOB:
        raise AssertionError("not single physical S_BLOB")
    idx = row[6][1]
    off, us, cs, codec, ml = reader.blobs[idx]
    pos = reader.record_base + off
    magic, c, flags, reserved, rus, rcs, rml, crc_expected, sha_expected = BHDR.unpack_from(reader.mm, pos)
    if (magic != BMAGIC or codec != CODEC_ZSTD or c != CODEC_ZSTD
            or us != rus or cs != rcs or ml != rml or ml != 0
            or start < 0 or length < 0 or start + length > us):
        raise IOError("authenticated blob header or range mismatch")
    base = pos + BHDR.size + rml
    if base + cs > len(reader.mm):
        raise IOError("compressed frame extends outside archive")

    z = Stream()
    ctx = z.lib.ZSTD_createDStream()
    if not ctx:
        raise MemoryError("ZSTD_createDStream returned NULL")
    fd = os.open(archive, os.O_RDONLY)
    try:
        z.check(z.lib.ZSTD_initDStream(ctx))
        # Negative controls inject errors into the decoder-visible frame only,
        # never mutate the genuine archive or its authenticated headers.
        available = cs - (1 if fault == "truncate" else 0)
        virtual_suffix = 1 if fault == "trailing" else 0
        data_left = available + virtual_suffix
        current = b""
        current_pos = 0
        produced = 0
        crc = 0
        digest = hashlib.sha256()
        selected = bytearray()
        decode_calls = 0
        max_input = 0
        max_output = 0
        exhausted = False
        while True:
            if current_pos == len(current) and data_left:
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
                    current = b"Z"  # deliberate extra byte after authenticated Zstd frame
                data_left -= len(current)
                current_pos = 0
                max_input = max(max_input, len(current))
            inraw = ctypes.create_string_buffer(current)
            ib = InBuf(ctypes.cast(inraw, ctypes.c_void_p), len(current), current_pos)
            out_raw = ctypes.create_string_buffer(WINDOW)
            ob = OutBuf(ctypes.cast(out_raw, ctypes.c_void_p), WINDOW, 0)
            previous = current_pos
            remaining = z.check(z.lib.ZSTD_decompressStream(ctx, ctypes.byref(ob), ctypes.byref(ib)))
            decode_calls += 1
            if decode_calls > max(4096, (us // WINDOW) * 8 + 4096):
                raise IOError("stream stalled or decode call limit reached")
            current_pos = ib.pos
            piece = out_raw.raw[:ob.pos]
            if piece:
                chunk_start = produced
                produced += len(piece)
                if produced > us:
                    raise IOError("decompressed frame over declared size")
                crc = binascii.crc32(piece, crc)
                digest.update(piece)
                if chunk_start < start + length and produced > start:
                    a = max(start - chunk_start, 0)
                    b = min(start + length - chunk_start, len(piece))
                    selected.extend(piece[a:b])
            max_output = max(max_output, ob.pos)
            if remaining == 0:
                if data_left or current_pos != len(current):
                    raise IOError("trailing compressed data after first frame")
                exhausted = True
                break
            if ob.pos == 0 and current_pos == previous and not data_left and current_pos == len(current):
                raise IOError("truncated or non-progressing Zstd frame")
        if not exhausted or produced != us:
            raise IOError("decompressed length mismatch")
        if crc & 0xffffffff != crc_expected or digest.digest() != sha_expected:
            raise IOError("authenticated physical CRC32/SHA256 mismatch")
        if len(selected) != length:
            raise IOError("selected range length mismatch")
        # The file index's member SHA must be linked to the physical direct blob.
        if row[5] is None or bytes(row[5]) != sha_expected:
            raise IOError("logical-to-physical direct blob SHA mismatch")
        return bytes(selected), {
            "physical_decoded_bytes": produced,
            "decode_calls": decode_calls,
            "max_input_block": max_input,
            "max_output_block": max_output,
            "selected_bytes": len(selected),
            "full_crc32_verified": True,
            "full_sha256_verified": True,
            "zstd_version": z.version,
        }
    finally:
        os.close(fd)
        z.lib.ZSTD_freeDStream(ctx)


def measure_child(archive, mode, expected_sample_sha):
    from cmpct.reader import CMPCT
    before = vmhwm_kib()
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(archive) as reader:
        if mode == "control":
            result = reader.read_range(NAME, 32 * MIB, MIB)
            evidence = {"source": "authentic-CMPCT-read_range",
                        "physical_decoded_bytes": 64 * MIB}
        elif mode == "stream":
            result, evidence = stream_range(archive, reader, 32 * MIB, MIB)
        elif mode == "open-only":
            result = b""
            evidence = {"source": "open-only"}
        else:
            raise ValueError(mode)
        wall_ns = time.perf_counter_ns() - t0
        cpu_ns = time.process_time_ns() - c0
        after = vmhwm_kib()
    if mode != "open-only":
        if len(result) != MIB or hashlib.sha256(result).hexdigest() != expected_sample_sha:
            raise AssertionError("selected bytes differed from original source")
    return {"mode": mode, "wall_ns": wall_ns, "cpu_ns": cpu_ns,
            "VmHWM_before_KiB": before, "VmHWM_after_KiB": after,
            "VmHWM_increment_KiB": max(0, after - before), **evidence}


def run(out: Path, rounds: int):
    if not sys.platform.startswith("linux") or not Path("/proc/self/status").exists():
        raise RuntimeError("J24Z01 requires Linux VmHWM; no guessed cross-host result")
    if rounds < 3:
        raise ValueError("minimum 3 fresh independent rounds")
    from o209_physical_decode_unit_court import _build_inputs
    repo = Path(__file__).resolve().parents[1]
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    reader_blob = subprocess.check_output(
        ["git", "hash-object", "src/cmpct/reader.py"], cwd=repo, text=True).strip()
    tool_blob = subprocess.check_output(
        ["git", "hash-object", "research/j24z01_zstd_stream_oracle.py"], cwd=repo, text=True).strip()
    parent_blob = subprocess.check_output(
        ["git", "hash-object", "research/o209_physical_decode_unit_court.py"],
        cwd=repo, text=True).strip()
    archives = _build_inputs(out.parent / "source")
    single = out.parent / "source" / "single.cmpct"
    sample_sha = archives["single"]["sample_sha256"]
    # First prove explicit invalid-frame rejection in the unmodified archive,
    # outside fresh child performance accounting.
    from cmpct.reader import CMPCT
    negatives = {}
    with CMPCT(single) as reader:
        for fault in ("corrupt", "truncate", "trailing"):
            try:
                stream_range(single, reader, 32 * MIB, MIB, fault=fault)
            except (IOError, ValueError, RuntimeError) as exc:
                negatives[fault] = {"rejected": True, "exception": str(exc)}
            else:
                raise AssertionError("unsafe decoder accepted " + fault)
    observations = []
    for repetition in range(rounds):
        order = ("control", "stream") if repetition % 2 == 0 else ("stream", "control")
        for mode in (*order, "open-only"):
            cmd = [sys.executable, str(Path(__file__).resolve()), "_child",
                   str(single), mode, sample_sha]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            point = json.loads(proc.stdout)
            point["repetition"] = repetition
            observations.append(point)
    def med(mode, key):
        return statistics.median(x[key] for x in observations if x["mode"] == mode)
    a = med("control", "VmHWM_increment_KiB")
    b = med("stream", "VmHWM_increment_KiB")
    mem_mib = (a - b) / 1024.0
    cpu_ratio = med("stream", "cpu_ns") / max(1, med("control", "cpu_ns"))
    wall_ratio = med("stream", "wall_ns") / max(1, med("control", "wall_ns"))
    decision = ("NO_MATERIAL_MEMORY_GAIN" if mem_mib < 32
                else "MEMORY_SEED_WITH_THROUGHPUT_DEBT"
                if max(cpu_ratio, wall_ratio) > 2.0 else "STREAMING_ORACLE_CONTINUE")
    result = {
        "schema": "cmpct-j24z01-v1",
        "evidence_class": "research-only one-native-Zstd-frame Linux selected-range oracle",
        "git_head": git_head, "reader_git_blob": reader_blob,
        "oracle_git_blob": tool_blob, "o209_original_instrument_blob": parent_blob,
        "same_archive": archives["single"],
        "original_control": archives["chunked"],
        "negative_decoder_cases": negatives,
        "raw_observations": observations,
        "summary": {"control_median_increment_KiB": a,
                    "stream_median_increment_KiB": b,
                    "memory_margin_MiB": mem_mib,
                    "stream_over_control_cpu_ratio": cpu_ratio,
                    "stream_over_control_wall_ratio": wall_ratio,
                    "decision": decision, "repetitions": rounds},
        "limitations": [
            "Linux-only native library oracle; not product Reader source or native shipping ABI",
            "Full frame decoded to verify CRC/SHA; selective memory not selective decode work",
            "Original 64 MiB repeating-pattern synthetic input, not held-out corpora",
            "Host kernel VmHWM increments are isolated fresh-process measures, not release RSS",
            "File source race not tested; directory publication, ZIP64, portability unmeasured",
            "System libzstd is an experimental dependency; package-owned Rust Zstd still governs product",
            "Chunked comparison is separately charged for +69894 physical container bytes"
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("run", "_child"))
    p.add_argument("args", nargs="*")
    ns = p.parse_args()
    if ns.mode == "_child":
        if len(ns.args) != 3:
            raise SystemExit("_child ARCHIVE MODE EXPECTED_SHA")
        print(json.dumps(measure_child(Path(ns.args[0]), ns.args[1], ns.args[2]), sort_keys=True))
    else:
        if len(ns.args) not in (1, 2):
            raise SystemExit("run OUT_JSON [N_REPETITIONS]")
        run(Path(ns.args[0]), int(ns.args[1]) if len(ns.args) == 2 else 3)


if __name__ == "__main__":
    main()
