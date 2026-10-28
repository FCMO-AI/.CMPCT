#!/usr/bin/env python3
"""J24C21 exact-source large-physical-owner released-floor Reader court.

RESEARCH ONLY; frozen decision law in docs/v031-research/*j24c21*prereg.md.
The generation and probe operations require an actually installed CMPCT wheel;
no Builder or source-tree package imports, no per-arm fixture regeneration.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import binascii
from statistics import median

PROFILES = ("tiny_repeat_65k", "large_repeat_262k", "large_distinct_8k")
SHAPES = ("Q1_early", "Q6_spread", "Q32_spread")
ARMS = ("published", "fused", "sealed")
SOURCE_COMMITS = {
    "published": "80c358f8824ec1b20d349c92ed94c898090969b0",
    "fused": "a66fd593a83cc4c71556d3d86d835c51abd20a96",
    "sealed": "3b6a73f9205f40f11124cd9ff332407e52cebb93",
}


def deterministic_owners(profile: str):
    if profile == "tiny_repeat_65k":
        owners = [b"A", b"B"]
        refs = [i % 2 for i in range(65536)]
    elif profile == "large_repeat_262k":
        owners = [hashlib.shake_256(b"CMPCT-J24C21-A").digest(4096),
                  hashlib.shake_256(b"CMPCT-J24C21-B").digest(4096)]
        refs = [i % 2 for i in range(262144)]
    elif profile == "large_distinct_8k":
        owners = [hashlib.shake_256(b"CMPCT-J24C21-owner-" + i.to_bytes(4, "big")).digest(4096)
                  for i in range(4096)]
        refs = [(i * 2053 + 17) % len(owners) for i in range(8192)]
    else:
        raise ValueError(profile)
    return owners, refs


def ranges_for(size: int, shape: str):
    width = 8192 if size >= 8192 else min(size, 4096)
    if shape == "Q1_early":
        positions = [5]
    elif shape == "Q6_spread":
        positions = [int(size * p) for p in (.001, .19, .39, .59, .79, .97)]
    elif shape == "Q32_spread":
        positions = [int(size * (i + 0.5) / 32) for i in range(32)]
    else:
        raise ValueError(shape)
    return [(min(p, size), min(width, size - min(p, size))) for p in positions]


def slice_expected(owners, refs, start, length):
    """Independent uniform-size logical projection; no CMPCT reader dependency."""
    if not length:
        return b""
    unit = len(owners[0])
    assert unit > 0 and all(len(x) == unit for x in owners)
    idx = start // unit
    offset = start % unit
    out = bytearray()
    remaining = length
    while remaining:
        payload = owners[refs[idx]]
        n = min(remaining, unit - offset)
        out.extend(payload[offset:offset + n])
        remaining -= n
        idx += 1
        offset = 0
    return bytes(out)


def generate(output: Path):
    import msgpack
    from cmpct.codec import (
        MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
        CODEC_RAW, K_FILE, S_CHUNKS, zc, sha,
    )
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive

    output.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "j24c21-fixtures-v1", "profiles": {}}
    for profile in PROFILES:
        owners, refs = deterministic_owners(profile)
        records = bytearray()
        physical = []
        for raw in owners:
            pos = len(records)
            physical.append([pos, len(raw), len(raw), CODEC_RAW, 0])
            records.extend(BHDR.pack(BMAGIC, CODEC_RAW, 0, 0,
                                     len(raw), len(raw), 0,
                                     binascii.crc32(raw) & 0xffffffff, sha(raw)))
            records.extend(raw)
        logical_hash = hashlib.sha256()
        logical_size = 0
        for owner_id in refs:
            payload = owners[owner_id]
            logical_hash.update(payload)
            logical_size += len(payload)
        index = {
            "v": VERSION,
            "files": [["fixed.bin", K_FILE, 0o644, 946684800000000000,
                       logical_size, logical_hash.digest(), [S_CHUNKS, refs]]],
            "blobs": physical,
            "recipes": [],
            "dict_blob": None,
            "fsmeta": {},
        }
        raw_index = msgpack.packb(index, use_bin_type=True)
        encoded = zc(raw_index, 12)
        archive = (
            HDR.pack(MAGIC, VERSION, 0, len(encoded), len(raw_index),
                     len(records), sha(raw_index))
            + encoded + bytes(records) + encoded
            + FTR.pack(FMAGIC, 0, 1, 0, 0,
                       len(encoded), len(raw_index), 0, sha(raw_index))
        )
        archive_path = output / (profile + ".cmpct")
        archive_path.write_bytes(archive)
        expected = {
            shape: [
                {"start": start, "length": length,
                 "sha256": hashlib.sha256(slice_expected(owners, refs, start, length)).hexdigest()}
                for start, length in ranges_for(logical_size, shape)
            ]
            for shape in SHAPES
        }
        # This is the cheapest real signed-wire validator, not a replacement for
        # independently installed three-arm comparisons.
        assert preflight_archive(archive_path, verify_blob_headers=True)["files"] == 1
        with CMPCT(archive_path) as reader:
            assert reader.file_sha256("fixed.bin") == logical_hash.digest()
            for shape, queries in expected.items():
                for query in queries:
                    actual = reader.read_range("fixed.bin", query["start"], query["length"])
                    assert hashlib.sha256(actual).hexdigest() == query["sha256"]
                    assert len(actual) == query["length"]
        manifest["profiles"][profile] = {
            "archive": archive_path.name,
            "archive_sha256": hashlib.sha256(archive).hexdigest(),
            "archive_bytes": len(archive),
            "physical_blob_count": len(physical),
            "physical_payload_bytes": sum(map(len, owners)),
            "logical_bytes": logical_size,
            "reference_count": len(refs),
            "logical_sha256": logical_hash.hexdigest(),
            "queries": expected,
        }
    dest = output / "manifest.json"
    dest.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"generated_manifest": str(dest),
                      "profile_sha256": {p: x["archive_sha256"]
                                         for p, x in manifest["profiles"].items()}},
                     sort_keys=True))


def probe(manifest_path: Path, profile: str, shape: str):
    import cmpct.reader as module
    from cmpct.reader import CMPCT

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["profiles"][profile]
    archive_path = manifest_path.parent / entry["archive"]
    # SHA is checked outside the timed Reader session (same immutable file).
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == entry["archive_sha256"]
    expected = entry["queries"][shape]
    begin_w = time.perf_counter_ns()
    begin_c = time.process_time_ns()
    reader = CMPCT(archive_path)
    opened_w = time.perf_counter_ns()
    opened_c = time.process_time_ns()
    assert len(reader.files) == 1 and "fixed.bin" in reader.by
    listed_w = time.perf_counter_ns()
    listed_c = time.process_time_ns()
    read_w = 0
    read_c = 0
    answer_bytes = 0
    try:
        for query in expected:
            t0w = time.perf_counter_ns()
            t0c = time.process_time_ns()
            raw = reader.read_range("fixed.bin", query["start"], query["length"])
            read_c += time.process_time_ns() - t0c
            read_w += time.perf_counter_ns() - t0w
            assert len(raw) == query["length"]
            assert hashlib.sha256(raw).hexdigest() == query["sha256"], (profile, shape, query)
            answer_bytes += len(raw)
    finally:
        reader.close()
    end_w = time.perf_counter_ns()
    end_c = time.process_time_ns()
    peak_kib = None
    if sys.platform.startswith("linux"):
        peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({
        "schema": "j24c21-probe-v1",
        "profile": profile, "shape": shape,
        "source_tree_reader_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "archive_sha256": entry["archive_sha256"],
        "answer_count": len(expected), "answer_bytes": answer_bytes,
        "open_wall_ns": opened_w - begin_w, "open_cpu_ns": opened_c - begin_c,
        "list_wall_ns": listed_w - opened_w, "list_cpu_ns": listed_c - opened_c,
        "read_wall_ns": read_w, "read_cpu_ns": read_c,
        "session_wall_ns": end_w - begin_w, "session_cpu_ns": end_c - begin_c,
        "peak_rss_kib": peak_kib,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }, sort_keys=True))


def court(manifest_path: Path, interpreters: dict[str, Path], out: Path, repetitions: int):
    assert repetitions >= 4
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(manifest["profiles"]) == set(PROFILES)
    orderings = list(itertools.permutations(ARMS))
    observations = []
    for profile in PROFILES:
        for shape in SHAPES:
            for repetition in range(repetitions):
                for arm in orderings[repetition % len(orderings)]:
                    cmd = [str(interpreters[arm]), str(Path(__file__).resolve()),
                           "--probe", "--manifest", str(manifest_path.resolve()),
                           "--profile", profile, "--shape", shape]
                    t0 = time.perf_counter_ns()
                    completed = subprocess.run(cmd, capture_output=True, text=True)
                    outer_wall_ns = time.perf_counter_ns() - t0
                    if completed.returncode != 0:
                        raise RuntimeError(f"{arm} {profile} {shape} rep {repetition}: "
                                           f"{completed.stderr[-5000:]}")
                    probe_result = json.loads(completed.stdout.strip().splitlines()[-1])
                    assert probe_result["schema"] == "j24c21-probe-v1"
                    assert probe_result["archive_sha256"] == manifest["profiles"][profile]["archive_sha256"]
                    assert probe_result["profile"] == profile and probe_result["shape"] == shape
                    observations.append({**probe_result, "arm": arm,
                                         "source_commit": SOURCE_COMMITS[arm],
                                         "repetition": repetition,
                                         "outer_process_wall_ns": outer_wall_ns})
    report = {
        "schema": "j24c21-court-v1",
        "fixture_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "sources": SOURCE_COMMITS,
        "repetitions": repetitions,
        "profiles": manifest["profiles"],
        "observations": observations,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"court": str(out), "observations": len(observations),
                      "arms": SOURCE_COMMITS}, sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--probe", action="store_true")
    mode.add_argument("--court", action="store_true")
    p.add_argument("--output", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--profile", choices=PROFILES)
    p.add_argument("--shape", choices=SHAPES)
    for arm in ARMS:
        p.add_argument("--python-" + arm, type=Path)
    p.add_argument("--repetitions", type=int, default=6)
    a = p.parse_args()
    if a.generate:
        assert a.output is not None
        generate(a.output)
    elif a.probe:
        assert a.manifest is not None and a.profile and a.shape
        probe(a.manifest, a.profile, a.shape)
    else:
        assert a.manifest is not None and a.output is not None
        interpreters = {arm: getattr(a, "python_" + arm) for arm in ARMS}
        assert all(p is not None and p.is_absolute() for p in interpreters.values())
        court(a.manifest, interpreters, a.output, a.repetitions)


if __name__ == "__main__":
    main()
