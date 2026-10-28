from __future__ import annotations

"""Locality-safe entropy-split oracle for the v0.30 logs blocker.

``logs_and_telemetry`` mixes six large, highly repetitive raw ``.log`` files with five already-compressed
rotations (gzip/xz/zstd). Treating all eleven files as one compression population wastes both ratio and CPU: the
raw logs want cross-file context, while the compressed rotations are already entropy-dense and should usually be
copied verbatim.

This oracle therefore tests a simple source-derived architecture:
- regular ``.log`` files are packed into independently decodable <=8 MiB segments, additionally bounded so a
  selected member never causes >8x decoded-context amplification;
- known precompressed rotations (``.gz``, ``.xz``, ``.zst``) are stored verbatim with direct byte-range access;
- the segment plan, source scan, integrity hashes, compression, metadata and archive write are all charged to
  creation time;
- every candidate is fully extracted and exact-tree verified before receiving competitor credit.

No benchmark names or hidden precomputed dictionaries are used in candidate construction. This remains a
research-only disproof surface until any winning structure is expressed in canonical r25 with recovery,
Python/native/Android readers and full release authority.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import time

import msgpack
import zstandard as zstd

from benchmarks import v030_external_competitors as B
from benchmarks import v030_release_generalization as GENERAL

MAGIC = b"C30LGS1\0"
HEADER = struct.Struct("<8sQ32s")
LEVELS = (1, 3, 6, 9)
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_MEMBER_AMPLIFICATION = 8.0
RAW_LOG_SUFFIX = ".log"
PRECOMPRESSED_SUFFIXES = (".gz", ".xz", ".zst")
TARGET = "05_logs_and_telemetry"


def _source(stage: Path) -> tuple[list[dict], int]:
    rows = []
    logical = 0
    for path in sorted(item for item in stage.rglob("*") if item.is_file()):
        rel = path.relative_to(stage).as_posix()
        raw = path.read_bytes()
        logical += len(raw)
        suffix = path.suffix.lower()
        if suffix == RAW_LOG_SUFFIX:
            kind = "log"
        elif suffix in PRECOMPRESSED_SUFFIXES:
            kind = "precompressed"
        else:
            kind = "other"
        rows.append({
            "rel": rel,
            "raw": raw,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).digest(),
            "kind": kind,
        })
    return rows, logical


def _plan_log_segments(rows: list[dict]) -> tuple[list[list[int]], float, int]:
    logs = [index for index, row in enumerate(rows) if row["kind"] == "log"]
    if not logs:
        return [], 1.0, 0
    segments: list[list[int]] = []
    current: list[int] = []
    current_bytes = 0
    for index in logs:
        size = rows[index]["size"]
        proposed = current + [index]
        proposed_bytes = current_bytes + size
        min_member = min(rows[item]["size"] for item in proposed)
        if current and (
            proposed_bytes > MAX_DECODE_UNIT
            or proposed_bytes > int(MAX_MEMBER_AMPLIFICATION * max(1, min_member))
        ):
            segments.append(current)
            current = [index]
            current_bytes = size
        else:
            current = proposed
            current_bytes = proposed_bytes
    if current:
        segments.append(current)

    max_amp = 1.0
    max_unit = 0
    for segment in segments:
        decoded = sum(rows[index]["size"] for index in segment)
        max_unit = max(max_unit, decoded)
        for index in segment:
            max_amp = max(max_amp, decoded / max(1, rows[index]["size"]))
    if max_amp > MAX_MEMBER_AMPLIFICATION or max_unit > MAX_DECODE_UNIT:
        raise RuntimeError(f"entropy-split locality planner failed: amp={max_amp} unit={max_unit}")
    return segments, max_amp, max_unit


def _write_candidate(rows: list[dict], log_segments: list[list[int]], archive: Path, *, level: int) -> dict:
    started = time.perf_counter()
    compressor = zstd.ZstdCompressor(level=level, threads=0)
    segment_rows = []
    owners: dict[int, tuple[int, int, int]] = {}
    for segment_index, members in enumerate(log_segments):
        raw = b"".join(rows[index]["raw"] for index in members)
        cursor = 0
        pieces = []
        for index in members:
            length = rows[index]["size"]
            pieces.append([index, cursor, length])
            owners[index] = (segment_index, cursor, length)
            cursor += length
        blob = compressor.compress(raw)
        segment_rows.append([len(raw), hashlib.sha256(raw).digest(), pieces, blob])

    file_meta = []
    direct_blob = bytearray()
    previous = ""
    for index, row in enumerate(rows):
        rel = row["rel"]
        prefix = 0
        limit = min(len(previous), len(rel))
        while prefix < limit and previous[prefix] == rel[prefix]:
            prefix += 1
        if row["kind"] == "log":
            segment_index, offset, length = owners[index]
            storage = ["segment", segment_index, offset, length]
        else:
            offset = len(direct_blob)
            direct_blob.extend(row["raw"])
            storage = ["direct", offset, row["size"]]
        file_meta.append([prefix, rel[prefix:], row["size"], row["sha256"], storage])
        previous = rel

    body = msgpack.packb(
        ["cmpct-logs-entropy-split-v1", level, file_meta, segment_rows, bytes(direct_blob)],
        use_bin_type=True,
    )
    digest = hashlib.sha256(body).digest()
    archive.write_bytes(HEADER.pack(MAGIC, len(body), digest) + body)
    return {
        "level": level,
        "archive_bytes": archive.stat().st_size,
        "candidate_encode_s": time.perf_counter() - started,
        "log_segments": len(log_segments),
        "direct_bytes": len(direct_blob),
    }


def _extract(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short logs entropy-split archive")
    magic, body_size, digest = HEADER.unpack(raw[:HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(body_size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("logs entropy-split body identity mismatch")
    head = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 5 or head[0] != "cmpct-logs-entropy-split-v1":
        raise RuntimeError("bad logs entropy-split metadata")
    _profile, _level, files, segment_rows, direct_blob = head
    if not isinstance(direct_blob, bytes):
        raise RuntimeError("bad logs entropy-split direct blob")

    decoded_segments = []
    for row in segment_rows:
        if not isinstance(row, list) or len(row) != 4:
            raise RuntimeError("bad logs entropy-split segment")
        usize, expected_sha, pieces, blob = row
        usize = int(usize)
        if usize < 0 or usize > MAX_DECODE_UNIT or not isinstance(blob, bytes):
            raise RuntimeError("logs entropy-split segment bounds")
        payload = zstd.ZstdDecompressor().decompress(blob, max_output_size=usize)
        if len(payload) != usize or hashlib.sha256(payload).digest() != expected_sha:
            raise RuntimeError("logs entropy-split segment identity")
        decoded_segments.append((payload, pieces))

    dst.mkdir(parents=True, exist_ok=True)
    previous = ""
    seen = set()
    for index, row in enumerate(files):
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("bad logs entropy-split file row")
        prefix, suffix, size, expected_sha, storage = row
        if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad logs entropy-split path delta")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe logs entropy-split path")
        size = int(size)
        if storage[0] == "segment":
            segment_index, offset, length = map(int, storage[1:])
            payload = decoded_segments[segment_index][0]
            restored = payload[offset : offset + length]
        elif storage[0] == "direct":
            offset, length = map(int, storage[1:])
            restored = direct_blob[offset : offset + length]
        else:
            raise RuntimeError("unknown logs entropy-split storage")
        if len(restored) != size or hashlib.sha256(restored).digest() != expected_sha:
            raise RuntimeError(f"logs entropy-split file identity mismatch: {rel}")
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(restored)
        previous = rel
        seen.add(rel)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_logs_entropy_split_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_logs_entropy_split_repair")
    repair.install_generation_hooks(neutral)
    source_root = work_root / "neutral"
    neutral.build(source_root)
    repair.normalize_root(source_root)
    workload = source_root / TARGET
    key = ("neutral_hostile_v1", TARGET)
    if B._tree(workload) != accepted[key]["tree_sha256"]:
        raise RuntimeError("logs entropy-split source drift")

    expected_tree = B._tree(workload)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-entropy-split-", dir=work_root) as td:
        root = Path(td)
        stage = B._normalized_stage(workload, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        scan_started = time.perf_counter()
        rows, logical_bytes = _source(stage)
        log_segments, max_amp, max_unit = _plan_log_segments(rows)
        source_plan_s = time.perf_counter() - scan_started
        counts = {
            "log": sum(row["kind"] == "log" for row in rows),
            "precompressed": sum(row["kind"] == "precompressed" for row in rows),
            "other": sum(row["kind"] == "other" for row in rows),
        }
        candidates = []
        for level in LEVELS:
            archive = root / f"entropy-split-l{level}.bin"
            result = _write_candidate(rows, log_segments, archive, level=level)
            result["source_plan_s"] = source_plan_s
            result["create_s"] = source_plan_s + result["candidate_encode_s"]
            result["max_member_read_amplification"] = max_amp
            result["max_decode_unit_bytes"] = max_unit
            extracted = root / f"entropy-split-l{level}-out"
            _extract(archive, extracted)
            B._verify_extracted(extracted, expected_tree, f"logs-entropy-split-l{level}")
            result["tree_verified"] = True
            result["beats_zip_size"] = result["archive_bytes"] < zip_result["archive_bytes"]
            result["beats_zstd19_size"] = result["archive_bytes"] < zstd_result["archive_bytes"]
            result["beats_zip_create"] = result["create_s"] < zip_result["create_s"]
            result["beats_zstd19_create"] = result["create_s"] < zstd_result["create_s"]
            result["locality_green"] = max_amp <= MAX_MEMBER_AMPLIFICATION and max_unit <= MAX_DECODE_UNIT
            result["viable"] = result["locality_green"] and all(
                result[key]
                for key in ("beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create")
            )
            candidates.append(result)

    viable = [candidate for candidate in candidates if candidate["viable"]]
    best = min(viable, key=lambda candidate: (candidate["archive_bytes"], candidate["create_s"]), default=None)
    closest = min(
        candidates,
        key=lambda candidate: (
            max(0, int(candidate["archive_bytes"]) - int(zstd_result["archive_bytes"])),
            max(0.0, float(candidate["create_s"]) - float(zip_result["create_s"])),
            candidate["archive_bytes"],
        ),
    )
    return {
        "schema": "cmpct-v030-logs-entropy-split-oracle-v1",
        "claim_boundary": "research-only; source-derived entropy split is not canonical r25",
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "classification": {
            "raw_log_suffix": RAW_LOG_SUFFIX,
            "precompressed_suffixes": list(PRECOMPRESSED_SUFFIXES),
            "counts": counts,
        },
        "timing_boundary": "source-scan+classification+segment-plan+integrity-hash+zstd-log-segments+direct-copy+metadata+archive-write",
        "logical_bytes": logical_bytes,
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_unit,
        "zip": zip_result,
        "tar_zstd19": zstd_result,
        "candidates": candidates,
        "summary": {
            "four_way_win": best is not None,
            "best": best,
            "closest": closest,
            "all_tree_verified": all(candidate["tree_verified"] for candidate in candidates),
            "all_locality_green": all(candidate["locality_green"] for candidate in candidates),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-entropy-split-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-entropy-split.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
