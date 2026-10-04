from __future__ import annotations

"""Bounded sidecar-pack follow-up for the v0.30 logs inverse-edge frontier.

The exact inverse-edge oracle already removes three redundant loose logs and beats ZIP/Zstd in both size and
creation time, but remains ~160 KiB above the immutable accepted-v0.29 byte floor. Its remaining direct payload is
mostly already-compressed gzip/xz/zstd sidecars. This oracle asks one narrow question: can those sidecars recover
enough cross-file redundancy through a *second-stage, locality-bounded* Zstd pack without spending the release
locality budget or hiding preprocessing time?

Important accounting rules:
- inverse edges are discovered by actual decompression + exact byte/SHA equality, never names;
- unmatched loose logs retain the proven bounded segment plan from the base inverse-edge oracle;
- non-derived sidecars are grouped only with the same suffix/codec family;
- a direct read is charged for the whole second-stage group it must decode;
- a derived loose-log read is charged for both that group decode and the inverse decompression output;
- every resulting read must remain <=8x and every combined decode unit <=8 MiB;
- source scan, hashes, sidecar decompression/edge discovery, both segment plans, compression, metadata and write
  are all charged to creation time;
- every candidate is fully extracted and exact-tree verified;
- admission requires the accepted-v0.29 floor *and* strict ZIP/Zstd size+creation wins.

Research only. Even a green result still needs a bounded canonical grammar, recovery and Python/native/Android
parity before selector promotion.
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
from benchmarks import v030_logs_inverse_edge_oracle as BASE

MAGIC = b"C30LGS2\0"
HEADER = struct.Struct("<8sQ32s")
LEVELS = (1, 3, 6, 9, 12)
MAX_DECODE_UNIT = BASE.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = BASE.MAX_MEMBER_AMPLIFICATION


def _raw_log_segments(rows: list[dict], edges: dict[int, tuple[int, str]]) -> list[list[int]]:
    segments, _amp, _unit = BASE._plan_segments(rows, edges)
    return segments


def _derived_targets_by_source(edges: dict[int, tuple[int, str]]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for target, (source, _codec) in edges.items():
        result.setdefault(source, []).append(target)
    return result


def _group_is_safe(
    rows: list[dict],
    group: list[int],
    derived_by_source: dict[int, list[int]],
) -> bool:
    decoded = sum(int(rows[index]["size"]) for index in group)
    if decoded > MAX_DECODE_UNIT:
        return False
    for index in group:
        size = max(1, int(rows[index]["size"]))
        if decoded / size > MAX_MEMBER_AMPLIFICATION:
            return False
        for target in derived_by_source.get(index, []):
            target_size = max(1, int(rows[target]["size"]))
            # Conservative accounting: reading the derived file decodes the packed source group, then materializes
            # the inverse-decompressed logical target. Charge both rather than pretending the edge itself is free.
            combined = decoded + target_size
            if combined > MAX_DECODE_UNIT or combined / target_size > MAX_MEMBER_AMPLIFICATION:
                return False
    return True


def _plan_direct_groups(
    rows: list[dict],
    edges: dict[int, tuple[int, str]],
    raw_segments: list[list[int]],
) -> list[list[int]]:
    raw_owned = {index for segment in raw_segments for index in segment}
    derived_targets = set(edges)
    direct = [
        index
        for index in range(len(rows))
        if index not in derived_targets and index not in raw_owned
    ]
    derived_by_source = _derived_targets_by_source(edges)
    groups: list[list[int]] = []
    for suffix in sorted({rows[index]["suffix"] for index in direct}):
        current: list[int] = []
        for index in [item for item in direct if rows[item]["suffix"] == suffix]:
            proposed = current + [index]
            if current and not _group_is_safe(rows, proposed, derived_by_source):
                groups.append(current)
                current = [index]
                if not _group_is_safe(rows, current, derived_by_source):
                    raise RuntimeError(f"single direct member cannot satisfy locality: {rows[index]['rel']}")
            else:
                current = proposed
                if not _group_is_safe(rows, current, derived_by_source):
                    raise RuntimeError(f"direct locality planning failed: {rows[index]['rel']}")
        if current:
            groups.append(current)
    return groups


def _locality(
    rows: list[dict],
    edges: dict[int, tuple[int, str]],
    raw_segments: list[list[int]],
    direct_groups: list[list[int]],
) -> tuple[float, int]:
    max_amp = 1.0
    max_unit = 0
    for segment in raw_segments:
        decoded = sum(int(rows[index]["size"]) for index in segment)
        max_unit = max(max_unit, decoded)
        for index in segment:
            max_amp = max(max_amp, decoded / max(1, int(rows[index]["size"])))
    derived_by_source = _derived_targets_by_source(edges)
    for group in direct_groups:
        decoded = sum(int(rows[index]["size"]) for index in group)
        max_unit = max(max_unit, decoded)
        for index in group:
            max_amp = max(max_amp, decoded / max(1, int(rows[index]["size"])))
            for target in derived_by_source.get(index, []):
                target_size = max(1, int(rows[target]["size"]))
                combined = decoded + target_size
                max_unit = max(max_unit, combined)
                max_amp = max(max_amp, combined / target_size)
    if max_amp > MAX_MEMBER_AMPLIFICATION or max_unit > MAX_DECODE_UNIT:
        raise RuntimeError(f"sidecar-pack locality planner failed: amp={max_amp} unit={max_unit}")
    return max_amp, max_unit


def _write_candidate(
    rows: list[dict],
    edges: dict[int, tuple[int, str]],
    raw_segments: list[list[int]],
    direct_groups: list[list[int]],
    archive: Path,
    *,
    level: int,
) -> dict:
    started = time.perf_counter()
    compressor = zstd.ZstdCompressor(level=level, threads=0)

    raw_segment_rows = []
    raw_owners: dict[int, tuple[int, int, int]] = {}
    for segment_index, members in enumerate(raw_segments):
        plain = b"".join(rows[index]["raw"] for index in members)
        cursor = 0
        pieces = []
        for index in members:
            length = int(rows[index]["size"])
            pieces.append([index, cursor, length])
            raw_owners[index] = (segment_index, cursor, length)
            cursor += length
        raw_segment_rows.append([len(plain), hashlib.sha256(plain).digest(), pieces, compressor.compress(plain)])

    direct_group_rows = []
    direct_owners: dict[int, tuple[int, int, int]] = {}
    for group_index, members in enumerate(direct_groups):
        plain = b"".join(rows[index]["raw"] for index in members)
        cursor = 0
        pieces = []
        for index in members:
            length = int(rows[index]["size"])
            pieces.append([index, cursor, length])
            direct_owners[index] = (group_index, cursor, length)
            cursor += length
        direct_group_rows.append([len(plain), hashlib.sha256(plain).digest(), pieces, compressor.compress(plain)])

    files = []
    previous = ""
    for index, row in enumerate(rows):
        prefix = BASE._common_prefix(previous, row["rel"])
        if index in edges:
            source_index, codec = edges[index]
            storage = ["derive", source_index, codec]
        elif index in raw_owners:
            segment_index, offset, length = raw_owners[index]
            storage = ["raw-segment", segment_index, offset, length]
        else:
            group_index, offset, length = direct_owners[index]
            storage = ["direct-group", group_index, offset, length]
        files.append([prefix, row["rel"][prefix:], row["size"], row["sha256"], storage])
        previous = row["rel"]

    body = msgpack.packb(
        ["cmpct-logs-inverse-edge-sidecar-pack-v1", level, files, raw_segment_rows, direct_group_rows],
        use_bin_type=True,
    )
    digest = hashlib.sha256(body).digest()
    payload = HEADER.pack(MAGIC, len(body), digest) + body
    archive.write_bytes(payload)
    return {
        "level": level,
        "archive_bytes": len(payload),
        "candidate_encode_s": time.perf_counter() - started,
        "raw_segments": len(raw_segments),
        "direct_groups": len(direct_groups),
        "direct_plain_bytes": sum(int(rows[index]["size"]) for group in direct_groups for index in group),
        "inverse_edges": len(edges),
    }


def _extract(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short logs sidecar-pack archive")
    magic, body_size, digest = HEADER.unpack(raw[:HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(body_size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("logs sidecar-pack body identity mismatch")
    head = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 5 or head[0] != "cmpct-logs-inverse-edge-sidecar-pack-v1":
        raise RuntimeError("bad logs sidecar-pack metadata")
    _profile, _level, files, raw_segment_rows, direct_group_rows = head

    paths = []
    previous = ""
    for row in files:
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("bad logs sidecar-pack file row")
        prefix, suffix, _size, _sha, _storage = row
        if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad logs sidecar-pack path delta")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in paths:
            raise RuntimeError("unsafe logs sidecar-pack path")
        paths.append(rel)
        previous = rel

    def decode_groups(group_rows, label: str) -> list[bytes]:
        decoded = []
        for row in group_rows:
            if not isinstance(row, list) or len(row) != 4:
                raise RuntimeError(f"bad {label} row")
            usize, expected_sha, _pieces, blob = row
            usize = int(usize)
            if usize < 0 or usize > MAX_DECODE_UNIT or not isinstance(blob, bytes):
                raise RuntimeError(f"{label} bounds")
            plain = zstd.ZstdDecompressor().decompress(blob, max_output_size=usize)
            if len(plain) != usize or hashlib.sha256(plain).digest() != expected_sha:
                raise RuntimeError(f"{label} identity")
            decoded.append(plain)
        return decoded

    raw_segments = decode_groups(raw_segment_rows, "raw segment")
    direct_groups = decode_groups(direct_group_rows, "direct group")
    cache: dict[int, bytes] = {}
    active: set[int] = set()

    def restore(index: int) -> bytes:
        if index in cache:
            return cache[index]
        if index in active or index < 0 or index >= len(files):
            raise RuntimeError("logs sidecar-pack dependency error")
        active.add(index)
        _prefix, _suffix, size, expected_sha, storage = files[index]
        size = int(size)
        kind = storage[0]
        if kind == "raw-segment":
            group_index, offset, length = map(int, storage[1:])
            value = raw_segments[group_index][offset : offset + length]
        elif kind == "direct-group":
            group_index, offset, length = map(int, storage[1:])
            value = direct_groups[group_index][offset : offset + length]
        elif kind == "derive":
            source_index = int(storage[1])
            value = BASE._decode(storage[2], restore(source_index))
        else:
            raise RuntimeError("unknown logs sidecar-pack storage")
        if len(value) != size or hashlib.sha256(value).digest() != expected_sha:
            raise RuntimeError(f"logs sidecar-pack logical identity mismatch: {paths[index]}")
        active.remove(index)
        cache[index] = value
        return value

    dst.mkdir(parents=True, exist_ok=True)
    for index, rel in enumerate(paths):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(restore(index))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    workload, accepted = BASE._build_target_root(work_root)
    expected_tree = B._tree(workload)

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-sidecar-pack-", dir=work_root) as td:
        root = Path(td)
        stage = B._normalized_stage(workload, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        plan_started = time.perf_counter()
        rows, edges, edge_stats = BASE._scan_and_edges(stage)
        raw_segments = _raw_log_segments(rows, edges)
        direct_groups = _plan_direct_groups(rows, edges, raw_segments)
        max_amp, max_unit = _locality(rows, edges, raw_segments, direct_groups)
        source_plan_s = time.perf_counter() - plan_started

        candidates = []
        for level in LEVELS:
            archive = root / f"sidecar-pack-l{level}.bin"
            result = _write_candidate(rows, edges, raw_segments, direct_groups, archive, level=level)
            result["source_plan_s"] = source_plan_s
            result["create_s"] = source_plan_s + result["candidate_encode_s"]
            result["max_member_read_amplification"] = max_amp
            result["max_decode_unit_bytes"] = max_unit
            extracted = root / f"sidecar-pack-l{level}-out"
            _extract(archive, extracted)
            B._verify_extracted(extracted, expected_tree, f"logs-sidecar-pack-l{level}")
            result["tree_verified"] = True
            result["beats_zip_size"] = result["archive_bytes"] < zip_result["archive_bytes"]
            result["beats_zstd19_size"] = result["archive_bytes"] < zstd_result["archive_bytes"]
            result["beats_zip_create"] = result["create_s"] < zip_result["create_s"]
            result["beats_zstd19_create"] = result["create_s"] < zstd_result["create_s"]
            result["no_regression_vs_v029"] = result["archive_bytes"] <= int(accepted["archive_bytes"])
            result["locality_green"] = max_amp <= MAX_MEMBER_AMPLIFICATION and max_unit <= MAX_DECODE_UNIT
            result["viable"] = all(result[key] for key in (
                "beats_zip_size",
                "beats_zstd19_size",
                "beats_zip_create",
                "beats_zstd19_create",
                "no_regression_vs_v029",
                "locality_green",
                "tree_verified",
            ))
            candidates.append(result)

    viable = [row for row in candidates if row["viable"]]
    best = min(viable, key=lambda row: (row["archive_bytes"], row["create_s"])) if viable else None
    closest = min(candidates, key=lambda row: (max(0, row["archive_bytes"] - int(accepted["archive_bytes"])), row["archive_bytes"]))
    return {
        "schema": "cmpct-v030-logs-inverse-edge-sidecar-pack-oracle-v1",
        "claim_boundary": "research-only bounded sidecar second-stage compression; not canonical r25",
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "accepted_v029_bytes": int(accepted["archive_bytes"]),
        "edge_detection": edge_stats,
        "timing_boundary": "source-scan+sha256+sidecar-decompression+exact-edge-detection+raw-segment-plan+direct-sidecar-group-plan+zstd-both-kinds+metadata+archive-write",
        "locality_accounting": "derived reads charge packed-source-group decoded bytes plus inverse-decompressed target bytes",
        "zip": zip_result,
        "tar_zstd19": zstd_result,
        "candidates": candidates,
        "summary": {
            "release_floor_four_way_win": bool(viable),
            "best": best,
            "closest": closest,
            "all_tree_verified": all(row["tree_verified"] for row in candidates),
            "all_locality_green": all(row["locality_green"] for row in candidates),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-sidecar-pack-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-sidecar-pack.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
