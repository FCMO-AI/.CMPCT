#!/usr/bin/env python3
"""J24C22: same signed J24C21 r24 archive, full-physical-owner Reader triplet.

Science only: original published, unsafe fused (timing only), and sealed wheels.
Preregistration is an earlier Git commit; this instrument never changes controls.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
from pathlib import Path
import subprocess
import sys
import time
from statistics import median

SOURCE_COMMITS = {
    "published": "80c358f8824ec1b20d349c92ed94c898090969b0",
    "fused": "a66fd593a83cc4c71556d3d86d835c51abd20a96",
    "sealed": "3b6a73f9205f40f11124cd9ff332407e52cebb93",
}
READER_HASHES = {
    "published": "83be3f08f7fafb1fd638fda6140bbe1af6676c261be10acc9ea8f8b633beefff",
    "fused": "b9d7c86d021f26a252d2d8cb4d2ba6cbf4613b9fb743abf1a8264a2343a4ecfe",
    "sealed": "ccb5dfcd45bbef16c880a85b2f66cd91a8b48fa5f42ddab8c506205404f66a5b",
}
SIGNED_SHA = "eb695e0236db6d8d7e7896fcc8d3a2b69a47a66f601e47c8c333879176f58067"
PROFILE = "large_distinct_8k"
SHAPES = ("Q1_early", "Q16_front_full", "Q16_tail_full")
ARMS = ("published", "fused", "sealed")
OWNER_BYTES = 4096
NOWNERS = 4096
WINDOW = 1 << 20
SOURCE_SCHEMA = "j24c22-full-owner-workset-v1"
PROBE_SCHEMA = "j24c22-full-owner-probe-v1"
COURT_SCHEMA = "j24c22-full-owner-court-v1"


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha_path(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        while chunk := fd.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def owner(identifier: int):
    return hashlib.shake_256(
        b"CMPCT-J24C21-owner-" + identifier.to_bytes(4, "big")
    ).digest(OWNER_BYTES)


def owner_index(ref: int):
    return (ref * 2053 + 17) % NOWNERS


def full_queries(offset: int):
    return [(offset + i * WINDOW, WINDOW) for i in range(16)]


def expected_bytes(start: int, length: int, owners: list[bytes]):
    # Independently derive each exact logical range, with no Reader import.
    assert start % OWNER_BYTES == 0 and length % OWNER_BYTES == 0
    first = start // OWNER_BYTES
    count = length // OWNER_BYTES
    return b"".join(owners[owner_index(i)] for i in range(first, first + count))


def derive(manifest_path: Path, output: Path):
    parent = json.loads(manifest_path.read_bytes())
    assert parent["schema"] == "j24c21-fixtures-v1"
    entry = parent["profiles"][PROFILE]
    path = manifest_path.parent / entry["archive"]
    assert sha_path(path) == SIGNED_SHA == entry["archive_sha256"]
    assert entry["logical_bytes"] == 32 * WINDOW
    assert entry["physical_payload_bytes"] == 16 * WINDOW
    assert entry["physical_blob_count"] == NOWNERS
    assert entry["reference_count"] == 8192
    owners = [owner(i) for i in range(NOWNERS)]
    groups = {
        "Q1_early": [tuple((q["start"], q["length"])) for q in entry["queries"]["Q1_early"]],
        "Q16_front_full": full_queries(0),
        "Q16_tail_full": full_queries(16 * WINDOW),
    }
    query_groups = {}
    for shape, ranges in groups.items():
        queries = []
        touched = set()
        for start, length in ranges:
            assert 0 <= start and 0 <= length and start + length <= 32 * WINDOW
            first = start // OWNER_BYTES
            after = (start + length + OWNER_BYTES - 1) // OWNER_BYTES
            touched.update(owner_index(i) for i in range(first, after))
            if start % OWNER_BYTES == 0 and length % OWNER_BYTES == 0:
                expected = expected_bytes(start, length, owners)
            else:
                first_byte = first * OWNER_BYTES
                chunks = b"".join(owners[owner_index(i)] for i in range(first, after))
                expected = chunks[start - first_byte:start - first_byte + length]
            assert len(expected) == length
            queries.append({"start": start, "length": length,
                            "sha256": hashlib.sha256(expected).hexdigest()})
        if shape.startswith("Q16_"):
            assert len(ranges) == 16 and sum(q["length"] for q in queries) == 16 * WINDOW
            assert len(touched) == NOWNERS, (shape, len(touched))
        query_groups[shape] = {
            "queries": queries, "distinct_owners_touched": len(touched),
            "unique_owner_payload_bytes": len(touched) * OWNER_BYTES,
            "answer_bytes": sum(q["length"] for q in queries),
        }
    # In addition to query SHA, recompute a deterministic ordered answer-stream digest.
    for shape, group in query_groups.items():
        digest = hashlib.sha256()
        for q in group["queries"]:
            s, n = q["start"], q["length"]
            first = s // OWNER_BYTES
            after = (s + n + OWNER_BYTES - 1) // OWNER_BYTES
            gathered = b"".join(owners[owner_index(i)] for i in range(first, after))
            digest.update(gathered[s % OWNER_BYTES:s % OWNER_BYTES + n])
        group["combined_answer_sha256"] = digest.hexdigest()
    work = {
        "schema": SOURCE_SCHEMA,
        "parent_fixture_manifest_sha256": sha_path(manifest_path),
        "parent_fixture_profile": PROFILE,
        "signed_archive": entry["archive"],
        "signed_archive_sha256": SIGNED_SHA,
        "archive_bytes": entry["archive_bytes"],
        "logical_bytes": entry["logical_bytes"],
        "source_commits": SOURCE_COMMITS,
        "source_reader_hashes": READER_HASHES,
        "shapes": query_groups,
    }
    dump(output, work)
    print(json.dumps({"derived": str(output), "shapes": {
        s: {"owners": w["distinct_owners_touched"], "bytes": w["answer_bytes"]}
        for s, w in query_groups.items()}}, sort_keys=True))


def probe(workset_path: Path, manifest_path: Path, shape: str, arm: str):
    import cmpct.reader as installed
    from cmpct.reader import CMPCT

    work = json.loads(workset_path.read_text(encoding="utf-8"))
    assert work["schema"] == SOURCE_SCHEMA
    assert work["parent_fixture_manifest_sha256"] == sha_path(manifest_path)
    archive = manifest_path.parent / work["signed_archive"]
    assert sha_path(archive) == work["signed_archive_sha256"] == SIGNED_SHA
    reader_hash = hashlib.sha256(Path(installed.__file__).read_bytes()).hexdigest()
    assert reader_hash == READER_HASHES[arm], (arm, reader_hash)
    questions = work["shapes"][shape]["queries"]
    begin_wall = time.perf_counter_ns()
    begin_cpu = time.process_time_ns()
    reader = CMPCT(archive)
    opened_wall = time.perf_counter_ns()
    opened_cpu = time.process_time_ns()
    assert len(reader.files) == 1 and "fixed.bin" in reader.by
    listed_wall = time.perf_counter_ns()
    listed_cpu = time.process_time_ns()
    read_wall = read_cpu = read_bytes = 0
    concatenated = hashlib.sha256()
    try:
        for q in questions:
            t0wall = time.perf_counter_ns()
            t0cpu = time.process_time_ns()
            got = reader.read_range("fixed.bin", q["start"], q["length"])
            read_wall += time.perf_counter_ns() - t0wall
            read_cpu += time.process_time_ns() - t0cpu
            assert len(got) == q["length"]
            assert hashlib.sha256(got).hexdigest() == q["sha256"], (shape, q)
            read_bytes += len(got)
            concatenated.update(got)
    finally:
        reader.close()
    end_wall = time.perf_counter_ns()
    end_cpu = time.process_time_ns()
    assert concatenated.hexdigest() == work["shapes"][shape]["combined_answer_sha256"]
    peak = None
    if sys.platform.startswith("linux"):
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({
        "schema": PROBE_SCHEMA, "arm": arm, "shape": shape,
        "signed_archive_sha256": SIGNED_SHA,
        "source_commit": SOURCE_COMMITS[arm], "installed_reader_sha256": reader_hash,
        "answer_count": len(questions), "answer_bytes": read_bytes,
        "answer_stream_sha256": concatenated.hexdigest(),
        "open_wall_ns": opened_wall - begin_wall, "open_cpu_ns": opened_cpu - begin_cpu,
        "list_wall_ns": listed_wall - opened_wall, "list_cpu_ns": listed_cpu - opened_cpu,
        "read_wall_ns": read_wall, "read_cpu_ns": read_cpu,
        "session_wall_ns": end_wall - begin_wall, "session_cpu_ns": end_cpu - begin_cpu,
        "peak_rss_kib": peak, "python": sys.version.split()[0],
        "platform": platform.platform(),
    }, sort_keys=True))


def court(workset: Path, manifest: Path, python_arms: dict[str, Path],
          output: Path, repetitions: int):
    assert repetitions >= 4
    work = json.loads(workset.read_bytes())
    assert set(work["shapes"]) == set(SHAPES)
    permutations = list(itertools.permutations(ARMS))
    rows = []
    for shape in SHAPES:
        for repeat in range(repetitions):
            for arm in permutations[repeat % len(permutations)]:
                cmd = [str(python_arms[arm]), str(Path(__file__).resolve()), "--probe",
                       "--workset", str(workset.resolve()), "--manifest", str(manifest.resolve()),
                       "--shape", shape, "--arm", arm]
                start = time.perf_counter_ns()
                process = subprocess.run(cmd, capture_output=True, text=True)
                external = time.perf_counter_ns() - start
                if process.returncode:
                    raise RuntimeError(f"{shape}/{arm}/{repeat} FAILED: "
                                       f"{process.stderr[-4000:]} / {process.stdout[-1000:]}")
                probe_result = json.loads(process.stdout.strip().splitlines()[-1])
                assert probe_result["schema"] == PROBE_SCHEMA
                assert probe_result["arm"] == arm and probe_result["shape"] == shape
                rows.append({**probe_result, "repeat": repeat,
                             "outer_process_wall_ns": external})
    report = {
        "schema": COURT_SCHEMA, "workset_sha256": sha_path(workset),
        "parent_fixture_manifest_sha256": sha_path(manifest),
        "source_commits": SOURCE_COMMITS, "source_reader_hashes": READER_HASHES,
        "repetitions": repetitions, "observations": rows,
    }
    dump(output, report)
    print(json.dumps({"court": str(output), "observations": len(rows),
                      "workset_sha256": report["workset_sha256"]}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--derive", action="store_true")
    modes.add_argument("--probe", action="store_true")
    modes.add_argument("--court", action="store_true")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workset", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--shape", choices=SHAPES)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--repetitions", type=int, default=6)
    for arm in ARMS:
        parser.add_argument("--python-" + arm, type=Path)
    args = parser.parse_args()
    if args.derive:
        assert args.output is not None
        derive(args.manifest, args.output)
    elif args.probe:
        assert args.workset is not None and args.shape and args.arm
        probe(args.workset, args.manifest, args.shape, args.arm)
    else:
        assert args.workset is not None and args.output is not None
        python_arms = {arm: getattr(args, "python_" + arm) for arm in ARMS}
        assert all(p is not None and p.is_absolute() for p in python_arms.values())
        court(args.workset, args.manifest, python_arms, args.output, args.repetitions)


if __name__ == "__main__":
    main()
