#!/usr/bin/env python3
"""O209: original r24 Reader physical decode-unit / logical read-request court.

Independent research instrument. Does not patch production Reader or loosen any invariant.
Only the 'producer' runs full verify(); fresh measurement children perform selective reads.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import time

MIB = 1024 * 1024
LOGICAL_MIB = 64
NAME = "payload.bin"
POSIX_NS = 946684800 * 1_000_000_000


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _pattern() -> bytes:
    return hashlib.shake_256(b"cmpct-o209-public-synthetic-source-v1").digest(1024)


def _build_inputs(folder: Path) -> dict:
    import msgpack
    from cmpct.codec import (
        BHDR, BMAGIC, CODEC_ZSTD, FMAGIC, FTR, HDR, K_FILE,
        MAGIC, S_BLOB, S_CHUNKS, VERSION, zc,
    )
    from cmpct.reader import CMPCT

    folder.mkdir(parents=True, exist_ok=True)
    source = _pattern() * (LOGICAL_MIB * MIB // len(_pattern()))
    assert len(source) == LOGICAL_MIB * MIB
    source_sha = _sha(source).hex()
    sample_sha = _sha(source[:MIB]).hex()
    variants = {}
    for representation in ("single", "chunked"):
        physical_parts = [source] if representation == "single" else [
            source[i:i + MIB] for i in range(0, len(source), MIB)
        ]
        records, blobs = [], []
        offset = 0
        t0 = time.perf_counter()
        c0 = time.process_time()
        for physical in physical_parts:
            compressed = zc(physical, 1)
            header = BHDR.pack(
                BMAGIC, CODEC_ZSTD, 0, 0, len(physical), len(compressed),
                0, binascii.crc32(physical) & 0xFFFFFFFF, _sha(physical)
            )
            record = header + compressed
            records.append(record)
            blobs.append([offset, len(physical), len(compressed), CODEC_ZSTD, 0])
            offset += len(record)
        storage = [S_BLOB, 0] if representation == "single" else [
            S_CHUNKS, list(range(len(blobs)))
        ]
        index = {
            "v": VERSION,
            "files": [[NAME, K_FILE, 0o644, POSIX_NS, len(source), _sha(source), storage]],
            "blobs": blobs,
            "recipes": [],
        }
        index_raw = msgpack.packb(index, use_bin_type=True)
        index_compressed = zc(index_raw, 1)
        index_sha = _sha(index_raw)
        archive = folder / f"{representation}.cmpct"
        with archive.open("wb") as stream:
            stream.write(HDR.pack(
                MAGIC, VERSION, 0, len(index_compressed),
                len(index_raw), offset, index_sha
            ))
            stream.write(index_compressed)
            for record in records:
                stream.write(record)
            stream.write(index_compressed)
            stream.write(FTR.pack(
                FMAGIC, 0, 1, 0, 0,
                len(index_compressed), len(index_raw), 0, index_sha
            ))
        build_wall = time.perf_counter() - t0
        build_cpu = time.process_time() - c0
        # Real installed Reader, not monkeypatched state.
        with CMPCT(archive) as reader:
            assert reader.verify() == 1, "full-content verification failed"
            assert _sha(reader.read(NAME)).hex() == source_sha
            assert reader.by[NAME][6][0] == (S_BLOB if representation == "single" else S_CHUNKS)
            assert len(reader.blobs) == (1 if representation == "single" else LOGICAL_MIB)
        variants[representation] = {
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": _sha(archive.read_bytes()).hex(),
            "blob_count": len(blobs),
            "total_record_bytes": offset,
            "total_compressed_payload_bytes": sum(b[2] for b in blobs),
            "logical_bytes": len(source),
            "source_sha256": source_sha,
            "sample_sha256": sample_sha,
            "build_wall_s": build_wall,
            "build_cpu_s": build_cpu,
        }
    return variants


def _vmhwm_kib() -> int:
    text = Path("/proc/self/status").read_text()
    for line in text.splitlines():
        if line.startswith("VmHWM:"):
            return int(line.split()[1])
    raise RuntimeError("Linux VmHWM unavailable; do not substitute Python tracemalloc")


def _consume(archive: Path, scenario: str, reference_sha: str) -> dict:
    from cmpct.codec import CODEC_ZSTD, S_BLOB, S_CHUNKS
    from cmpct.reader import CMPCT
    before_kib = _vmhwm_kib()
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    starts = [] if scenario == "open-only" else (
        [LOGICAL_MIB // 2 * MIB] if scenario == "mid" else
        [0, LOGICAL_MIB // 2 * MIB, (LOGICAL_MIB - 1) * MIB]
    )
    with CMPCT(archive) as reader:
        assert reader.by[NAME][4] == LOGICAL_MIB * MIB
        physical_decoded = 0
        physical_frame_max = 0
        for start in starts:
            if reader.by[NAME][6][0] == S_BLOB:
                selected_indices = [reader.by[NAME][6][1]]
            elif reader.by[NAME][6][0] == S_CHUNKS:
                selected_indices = [start // MIB]
            else:
                raise AssertionError("unexpected storage representation")
            for idx in selected_indices:
                blob = reader.blobs[idx]
                assert blob[3] == CODEC_ZSTD
                physical_decoded += blob[1]
                physical_frame_max = max(physical_frame_max, blob[1])
            result = reader.read_range(NAME, start, MIB)
            if len(result) != MIB or _sha(result).hex() != reference_sha:
                raise AssertionError("Reader range differed from original source")
        # Opening/reading the very same file handle is the purpose of the measurement.
        wall_ns = time.perf_counter_ns() - t0
        cpu_ns = time.process_time_ns() - c0
        after_kib = _vmhwm_kib()
    return {
        "scenario": scenario,
        "archive": archive.name,
        "num_ranges": len(starts),
        "range_request_max_bytes": MIB if starts else 0,
        "physical_decoded_bytes_derived": physical_decoded,
        "physical_frame_max_bytes": physical_frame_max,
        "VmHWM_before_KiB": before_kib,
        "VmHWM_after_KiB": after_kib,
        "VmHWM_increment_KiB": max(0, after_kib - before_kib),
        "ru_maxrss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "wall_ns": wall_ns,
        "cpu_ns": cpu_ns,
        "exact_range_sha_match": True,
    }


def _child(argv: list[str]) -> None:
    archive = Path(argv[0])
    scenario = argv[1]
    sample_sha = argv[2]
    print(json.dumps(_consume(archive, scenario, sample_sha), sort_keys=True))


def _run(out: Path, repetitions: int) -> None:
    if not sys.platform.startswith("linux") or not Path("/proc/self/status").exists():
        raise RuntimeError("O209 local VmHWM experiment is explicitly Linux-only")
    if repetitions < 3:
        raise ValueError("at least three independent trials required")
    import cmpct.reader
    repo = Path(__file__).resolve().parents[1]
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    reader_blob = subprocess.check_output(
        ["git", "hash-object", "src/cmpct/reader.py"], cwd=repo, text=True
    ).strip()
    tool_blob = subprocess.check_output(
        ["git", "hash-object", "research/o209_physical_decode_unit_court.py"], cwd=repo, text=True
    ).strip()
    target = out.parent / "source"
    variants = _build_inputs(target)
    observations = []
    # Alternating fresh child processes. No tracemalloc; producer memory excluded.
    for repetition in range(repetitions):
        sequence = ("single", "chunked") if repetition % 2 == 0 else ("chunked", "single")
        for variant in sequence:
            for scenario in ("open-only", "mid", "three"):
                command = [
                    sys.executable, str(Path(__file__).resolve()), "_child",
                    str(target / f"{variant}.cmpct"), scenario,
                    variants[variant]["sample_sha256"],
                ]
                child = subprocess.run(command, capture_output=True, text=True, check=True)
                payload = json.loads(child.stdout)
                payload.update({"variant": variant, "repetition": repetition})
                observations.append(payload)
    def median_kib(variant: str, scenario: str) -> float:
        return float(statistics.median(
            x["VmHWM_increment_KiB"] for x in observations
            if x["variant"] == variant and x["scenario"] == scenario
        ))
    memory_margin_mib = (median_kib("single", "mid") - median_kib("chunked", "mid")) / 1024
    decision = ("MATERIAL_PHYSICAL_UNIT_RSS_AMPLIFICATION" if memory_margin_mib >= 32
                else "NO_MATERIAL_RSS_DELTA_ESTABLISHED")
    outcome = {
        "schema": "cmpct-o209-v1",
        "evidence_class": "authentic-revision24-python-reader-range-not-full-zip64-product",
        "git_head": git_head,
        "reader_git_blob": reader_blob,
        "instrument_git_blob": tool_blob,
        "host": {
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "kernel": os.uname().release,
        },
        "source": {
            "generator": "public-constant-1024-byte-Shake256-block-repeat",
            "logical_bytes": LOGICAL_MIB * MIB,
            "sample_bytes": MIB,
            "variants": variants,
        },
        "raw_observations": observations,
        "summary": {
            "single_mid_increment_median_KiB": median_kib("single", "mid"),
            "chunked_mid_increment_median_KiB": median_kib("chunked", "mid"),
            "single_open_only_increment_median_KiB": median_kib("single", "open-only"),
            "chunked_open_only_increment_median_KiB": median_kib("chunked", "open-only"),
            "mid_rss_margin_MiB": memory_margin_mib,
            "decision": decision,
            "repetitions": repetitions,
        },
        "limitations": [
            "Single Linux host and highly repetitive synthetic input",
            "Physical decoded-work derived from original Reader control flow, not an I/O profiler",
            "Different physical layouts have different complete stored bytes",
            "Full source verify executed only in producer phase and intentionally excluded from range RSS",
            "Requested range cap is not a bound on native physical-frame allocation",
            "No ZIP export, release benchmark, cold-device I/O, Windows or macOS measurements",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(outcome, sort_keys=True, indent=2) + "\n")
    print(json.dumps(outcome["summary"], sort_keys=True))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("run", "_child"))
    p.add_argument("args", nargs="*")
    ns = p.parse_args()
    if ns.mode == "_child":
        if len(ns.args) != 3:
            raise SystemExit("child: archive scenario expected_sample_sha256")
        _child(ns.args)
    else:
        if len(ns.args) not in (1, 2):
            raise SystemExit("run: output.json [repetitions]")
        _run(Path(ns.args[0]), int(ns.args[1]) if len(ns.args) == 2 else 3)


if __name__ == "__main__":
    main()
