from __future__ import annotations

"""Exact inverse-edge oracle for the v0.30 logs blocker.

The frozen logs workload contains six loose ``.log`` files plus gzip/xz/zstd rotations whose decompressed bytes
are exact copies of three of those loose files. v0.25's strongest representation exploited the safe direction of
that relationship: retain the already-compressed logical sidecar byte-for-byte, and derive the redundant loose
file through a cheap standard decompressor. No recompression determinism is required.

This targeted oracle isolates that mechanism from the old research graph:
- sidecar relationships are discovered by actual decompression + exact SHA/byte equality, never by filename;
- every compressed sidecar remains a directly readable logical file with its original bytes;
- a matching loose log stores only an inverse edge to the sidecar; unmatched loose logs are packed into bounded
  independently decodable Zstd segments;
- source scan, hashing, inverse-edge discovery/decompression, compression, metadata and archive write are all
  charged to creation time;
- every candidate is fully extracted and exact-tree verified;
- candidate admission also includes the accepted-v0.29 byte floor, not only ZIP/Zstd competitors.

Research only. A winning result still requires a bounded canonical r25 grammar, recovery semantics and
Python/native/Android parity before selector promotion.
"""

import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import struct
import tempfile
import time

import msgpack
import zstandard as zstd

from benchmarks import v030_external_competitors as B
from benchmarks import v030_release_generalization as GENERAL

MAGIC = b"C30LGI1\0"
HEADER = struct.Struct("<8sQ32s")
LEVELS = (1, 3, 6, 9)
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_MEMBER_AMPLIFICATION = 8.0
TARGET = "05_logs_and_telemetry"
RAW_LOG_SUFFIX = ".log"
SIDE_CAR_CODECS = {".gz": "gzip", ".xz": "xz", ".zst": "zstd"}
CODEC_RANK = {"zstd": 0, "gzip": 1, "xz": 2}


def _decode(codec: str, raw: bytes, *, max_output: int = MAX_DECODE_UNIT) -> bytes:
    if codec == "gzip":
        out = gzip.decompress(raw)
    elif codec == "xz":
        out = lzma.decompress(raw)
    elif codec == "zstd":
        out = zstd.ZstdDecompressor().decompress(raw, max_output_size=max_output)
    else:
        raise RuntimeError(f"unknown inverse-edge codec: {codec}")
    if len(out) > max_output:
        raise RuntimeError("inverse-edge decoded output exceeds policy")
    return out


def _scan_and_edges(stage: Path) -> tuple[list[dict], dict[int, tuple[int, str]], dict]:
    rows = []
    for path in sorted(item for item in stage.rglob("*") if item.is_file()):
        raw = path.read_bytes()
        rows.append({
            "rel": path.relative_to(stage).as_posix(),
            "raw": raw,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).digest(),
            "suffix": path.suffix.lower(),
        })

    raw_logs = {
        (row["size"], row["sha256"]): index
        for index, row in enumerate(rows)
        if row["suffix"] == RAW_LOG_SUFFIX
    }
    candidates: dict[int, list[tuple[int, int, str]]] = {}
    decoded_sidecars = 0
    decoded_bytes = 0
    for source_index, row in enumerate(rows):
        codec = SIDE_CAR_CODECS.get(row["suffix"])
        if codec is None:
            continue
        plain = _decode(codec, row["raw"])
        decoded_sidecars += 1
        decoded_bytes += len(plain)
        key = (len(plain), hashlib.sha256(plain).digest())
        target_index = raw_logs.get(key)
        if target_index is None or plain != rows[target_index]["raw"]:
            continue
        candidates.setdefault(target_index, []).append((CODEC_RANK[codec], source_index, codec))

    edges: dict[int, tuple[int, str]] = {}
    for target_index, options in candidates.items():
        _rank, source_index, codec = min(options)
        edges[target_index] = (source_index, codec)
    return rows, edges, {
        "decoded_sidecars": decoded_sidecars,
        "decoded_sidecar_plain_bytes": decoded_bytes,
        "inverse_edges": len(edges),
        "inverse_edge_targets": [rows[index]["rel"] for index in sorted(edges)],
        "inverse_edge_sources": [rows[edges[index][0]]["rel"] for index in sorted(edges)],
    }


def _plan_segments(rows: list[dict], edges: dict[int, tuple[int, str]]) -> tuple[list[list[int]], float, int]:
    candidates = [
        index for index, row in enumerate(rows)
        if row["suffix"] == RAW_LOG_SUFFIX and index not in edges
    ]
    segments: list[list[int]] = []
    current: list[int] = []
    current_bytes = 0
    for index in candidates:
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
    # Inverse edges decode exactly one selected loose logical file from one sidecar; their decoded logical context
    # is therefore that file itself (1x). Direct sidecars are also 1x range reads.
    if max_amp > MAX_MEMBER_AMPLIFICATION or max_unit > MAX_DECODE_UNIT:
        raise RuntimeError(f"inverse-edge locality planner failed: amp={max_amp} unit={max_unit}")
    return segments, max_amp, max_unit


def _common_prefix(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    return index


def _write_candidate(
    rows: list[dict],
    edges: dict[int, tuple[int, str]],
    segments: list[list[int]],
    archive: Path,
    *,
    level: int,
) -> dict:
    started = time.perf_counter()
    compressor = zstd.ZstdCompressor(level=level, threads=0)
    segment_rows = []
    owners: dict[int, tuple[int, int, int]] = {}
    for segment_index, members in enumerate(segments):
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

    direct_blob = bytearray()
    direct_offsets: dict[int, tuple[int, int]] = {}
    for index, row in enumerate(rows):
        if index in edges or index in owners:
            continue
        offset = len(direct_blob)
        direct_blob.extend(row["raw"])
        direct_offsets[index] = (offset, row["size"])

    files = []
    previous = ""
    for index, row in enumerate(rows):
        prefix = _common_prefix(previous, row["rel"])
        if index in edges:
            source_index, codec = edges[index]
            storage = ["derive", source_index, codec]
        elif index in owners:
            segment_index, offset, length = owners[index]
            storage = ["segment", segment_index, offset, length]
        else:
            offset, length = direct_offsets[index]
            storage = ["direct", offset, length]
        files.append([prefix, row["rel"][prefix:], row["size"], row["sha256"], storage])
        previous = row["rel"]

    body = msgpack.packb(
        ["cmpct-logs-inverse-edge-v1", level, files, segment_rows, bytes(direct_blob)],
        use_bin_type=True,
    )
    digest = hashlib.sha256(body).digest()
    archive.write_bytes(HEADER.pack(MAGIC, len(body), digest) + body)
    return {
        "level": level,
        "archive_bytes": archive.stat().st_size,
        "candidate_encode_s": time.perf_counter() - started,
        "segments": len(segments),
        "direct_bytes": len(direct_blob),
        "inverse_edges": len(edges),
    }


def _extract(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short logs inverse-edge archive")
    magic, body_size, digest = HEADER.unpack(raw[:HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(body_size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("logs inverse-edge body identity mismatch")
    head = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 5 or head[0] != "cmpct-logs-inverse-edge-v1":
        raise RuntimeError("bad logs inverse-edge metadata")
    _profile, _level, files, segment_rows, direct_blob = head
    if not isinstance(direct_blob, bytes):
        raise RuntimeError("bad logs inverse-edge direct blob")

    paths = []
    previous = ""
    for row in files:
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("bad logs inverse-edge file row")
        prefix, suffix, _size, _sha, _storage = row
        if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad logs inverse-edge path delta")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in paths:
            raise RuntimeError("unsafe logs inverse-edge path")
        paths.append(rel)
        previous = rel

    decoded_segments = []
    for row in segment_rows:
        if not isinstance(row, list) or len(row) != 4:
            raise RuntimeError("bad logs inverse-edge segment")
        usize, expected_sha, pieces, blob = row
        usize = int(usize)
        if usize < 0 or usize > MAX_DECODE_UNIT or not isinstance(blob, bytes):
            raise RuntimeError("logs inverse-edge segment bounds")
        payload = zstd.ZstdDecompressor().decompress(blob, max_output_size=usize)
        if len(payload) != usize or hashlib.sha256(payload).digest() != expected_sha:
            raise RuntimeError("logs inverse-edge segment identity")
        decoded_segments.append(payload)

    cache: dict[int, bytes] = {}
    active: set[int] = set()

    def restore(index: int) -> bytes:
        if index in cache:
            return cache[index]
        if index in active:
            raise RuntimeError("logs inverse-edge dependency cycle")
        if index < 0 or index >= len(files):
            raise RuntimeError("logs inverse-edge file index")
        active.add(index)
        _prefix, _suffix, size, expected_sha, storage = files[index]
        size = int(size)
        kind = storage[0]
        if kind == "direct":
            offset, length = map(int, storage[1:])
            value = direct_blob[offset : offset + length]
        elif kind == "segment":
            segment_index, offset, length = map(int, storage[1:])
            value = decoded_segments[segment_index][offset : offset + length]
        elif kind == "derive":
            source_index = int(storage[1])
            codec = storage[2]
            source = restore(source_index)
            value = _decode(codec, source)
        else:
            raise RuntimeError("unknown logs inverse-edge storage")
        if len(value) != size or hashlib.sha256(value).digest() != expected_sha:
            raise RuntimeError(f"logs inverse-edge logical identity mismatch: {paths[index]}")
        active.remove(index)
        cache[index] = value
        return value

    dst.mkdir(parents=True, exist_ok=True)
    for index, rel in enumerate(paths):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(restore(index))


def _build_target_root(work_root: Path):
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_logs_inverse_edge_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_logs_inverse_edge_repair")
    repair.install_generation_hooks(neutral)
    source_root = work_root / "neutral"
    source_root.mkdir(parents=True, exist_ok=True)
    # This is a targeted oracle: build only the one deterministic producer rather than spending minutes creating
    # unrelated media/office/database workloads. Repair hooks are installed before producer invocation.
    neutral.corpus_logs(source_root)
    repair.normalize_root(source_root)
    workload = source_root / TARGET
    key = ("neutral_hostile_v1", TARGET)
    if B._tree(workload) != accepted[key]["tree_sha256"]:
        raise RuntimeError("logs inverse-edge source drift")
    return workload, accepted[key]


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    workload, accepted = _build_target_root(work_root)
    expected_tree = B._tree(workload)

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-inverse-edge-", dir=work_root) as td:
        root = Path(td)
        stage = B._normalized_stage(workload, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        scan_started = time.perf_counter()
        rows, edges, edge_stats = _scan_and_edges(stage)
        segments, max_amp, max_unit = _plan_segments(rows, edges)
        source_plan_s = time.perf_counter() - scan_started
        candidates = []
        for level in LEVELS:
            archive = root / f"inverse-edge-l{level}.bin"
            result = _write_candidate(rows, edges, segments, archive, level=level)
            result["source_plan_s"] = source_plan_s
            result["create_s"] = source_plan_s + result["candidate_encode_s"]
            result["max_member_read_amplification"] = max_amp
            result["max_decode_unit_bytes"] = max_unit
            extracted = root / f"inverse-edge-l{level}-out"
            _extract(archive, extracted)
            B._verify_extracted(extracted, expected_tree, f"logs-inverse-edge-l{level}")
            result["tree_verified"] = True
            result["beats_zip_size"] = result["archive_bytes"] < zip_result["archive_bytes"]
            result["beats_zstd19_size"] = result["archive_bytes"] < zstd_result["archive_bytes"]
            result["beats_zip_create"] = result["create_s"] < zip_result["create_s"]
            result["beats_zstd19_create"] = result["create_s"] < zstd_result["create_s"]
            result["no_regression_vs_v029"] = result["archive_bytes"] <= int(accepted["accepted_v029_bytes"])
            result["locality_green"] = max_amp <= MAX_MEMBER_AMPLIFICATION and max_unit <= MAX_DECODE_UNIT
            result["viable"] = result["locality_green"] and result["no_regression_vs_v029"] and all(
                result[key]
                for key in ("beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create")
            )
            candidates.append(result)

    viable = [candidate for candidate in candidates if candidate["viable"]]
    best = min(viable, key=lambda candidate: (candidate["archive_bytes"], candidate["create_s"]), default=None)
    closest = min(
        candidates,
        key=lambda candidate: (
            max(0, int(candidate["archive_bytes"]) - int(accepted["accepted_v029_bytes"])),
            max(0, int(candidate["archive_bytes"]) - int(zstd_result["archive_bytes"])),
            max(0.0, float(candidate["create_s"]) - float(zip_result["create_s"])),
            candidate["archive_bytes"],
        ),
    )
    return {
        "schema": "cmpct-v030-logs-inverse-edge-oracle-v1",
        "claim_boundary": "research-only exact inverse edges; not canonical r25",
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "accepted_v029_bytes": int(accepted["accepted_v029_bytes"]),
        "edge_detection": edge_stats,
        "timing_boundary": "source-scan+sha256+sidecar-decompression+exact-edge-detection+segment-plan+zstd-unmatched-logs+direct-sidecars+metadata+archive-write",
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_unit,
        "zip": zip_result,
        "tar_zstd19": zstd_result,
        "candidates": candidates,
        "summary": {
            "release_floor_four_way_win": best is not None,
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
        default=Path("benchmark-artifacts/v030-logs-inverse-edge-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-inverse-edge.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
