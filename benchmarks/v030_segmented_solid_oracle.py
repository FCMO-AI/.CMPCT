from __future__ import annotations

"""Locality-bounded solid-stream research oracle for CMPCT v0.30.

The cheap solid experiments are only useful if their compression advantage survives the release locality laws.
This oracle therefore constructs independent Zstd segments with two hard invariants *before* compression:

* no decoded segment exceeds 8 MiB;
* for every small member sharing a segment, segment logical bytes / member logical bytes <= 8.0.

Files larger than 8 MiB are split into independent <=8 MiB pieces; reading the complete member therefore decodes
exactly that member's logical bytes (1x amplification).  Smaller files are greedily grouped only while the 8x
bound remains true for the smallest member in the segment.  Empty files own no decoded payload.

The archive is research-only.  It uses a compact MessagePack manifest plus independently compressed segment
payloads and a whole-body SHA-256.  It measures path order and extension-grouped order, multiple Zstd levels and
both serial and four-worker segment compression.  Every candidate is fully extracted and exact-tree verified.
Ties against ZIP or solid tar+Zstd-19 are failures.

A positive result still cannot authorize v0.30 release; it is evidence that a canonical r25 segmented-solid profile
could be worth implementing with the existing strong/member integrity, native/Android parity and product-pricing
requirements rather than evidence that those obligations already exist.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
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

MAGIC = b"C30SEG3\0"
HEADER = struct.Struct("<8sQ32s")
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_MEMBER_AMPLIFICATION = 8.0
LEVELS = (1, 3, 6, 9, 12)
VARIANTS = ("segment-path", "segment-ext")
WORKER_OPTIONS = (1, 4)


def _common_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


def _ordered_files(stage: Path, variant: str) -> list[Path]:
    files = B._files(stage)
    if variant == "segment-path":
        return files
    return sorted(files, key=lambda p: (p.suffix.lower(), p.name.lower(), p.relative_to(stage).as_posix()))


def _source(stage: Path, variant: str) -> tuple[list[dict], int]:
    rows = []
    total = 0
    previous = ""
    for path in _ordered_files(stage, variant):
        raw = path.read_bytes()
        rel = path.relative_to(stage).as_posix()
        prefix = _common_prefix(previous, rel)
        rows.append({"prefix": prefix, "suffix": rel[prefix:], "rel": rel, "raw": raw})
        previous = rel
        total += len(raw)
    return rows, total


def _segment(rows: list[dict]) -> tuple[list[dict], list[list[int]], float, int]:
    """Return segments, per-file segment ids, max member amplification and max decode unit."""
    segments: list[dict] = []
    owners: list[list[int]] = [[] for _ in rows]
    pending: list[tuple[int, int, bytes]] = []
    pending_total = 0
    pending_min = None

    def flush() -> None:
        nonlocal pending, pending_total, pending_min
        if not pending:
            return
        sid = len(segments)
        pieces = [(idx, offset, len(raw)) for idx, offset, raw in pending]
        payload = b"".join(raw for _idx, _offset, raw in pending)
        if len(payload) != pending_total or len(payload) > MAX_DECODE_UNIT:
            raise RuntimeError("segmented-solid decode-unit invariant")
        segments.append({"pieces": pieces, "raw": payload})
        for idx, _offset, _raw in pending:
            if sid not in owners[idx]:
                owners[idx].append(sid)
        pending = []
        pending_total = 0
        pending_min = None

    for idx, row in enumerate(rows):
        raw = row["raw"]
        size = len(raw)
        if size == 0:
            continue
        if size > MAX_DECODE_UNIT:
            flush()
            offset = 0
            while offset < size:
                piece = raw[offset : offset + MAX_DECODE_UNIT]
                sid = len(segments)
                segments.append({"pieces": [(idx, offset, len(piece))], "raw": piece})
                owners[idx].append(sid)
                offset += len(piece)
            continue

        next_total = pending_total + size
        next_min = size if pending_min is None else min(pending_min, size)
        allowed = next_total <= MAX_DECODE_UNIT and next_total <= MAX_MEMBER_AMPLIFICATION * max(1, next_min)
        if pending and not allowed:
            flush()
            next_total = size
            next_min = size
        pending.append((idx, 0, raw))
        pending_total = next_total
        pending_min = next_min
    flush()

    max_amp = 0.0
    max_unit = max((len(segment["raw"]) for segment in segments), default=0)
    for idx, row in enumerate(rows):
        size = len(row["raw"])
        if size == 0:
            continue
        decoded = sum(len(segments[sid]["raw"]) for sid in owners[idx])
        amp = decoded / size
        max_amp = max(max_amp, amp)
        if amp > MAX_MEMBER_AMPLIFICATION + 1e-12:
            raise RuntimeError(f"segmented-solid locality invariant: {amp}")
    return segments, owners, max_amp, max_unit


def _compress_one(raw: bytes, level: int) -> bytes:
    return zstd.ZstdCompressor(level=level, threads=0).compress(raw)


def _write_candidate(rows: list[dict], segments: list[dict], owners: list[list[int]], archive: Path, *, variant: str, level: int, workers: int) -> dict:
    started = time.perf_counter()
    raw_segments = [segment["raw"] for segment in segments]
    if workers == 1 or len(raw_segments) <= 1:
        compressed = [_compress_one(raw, level) for raw in raw_segments]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-segment-zstd") as pool:
            compressed = list(pool.map(lambda raw: _compress_one(raw, level), raw_segments))

    file_meta = []
    previous = ""
    for idx, row in enumerate(rows):
        rel = row["rel"]
        prefix = _common_prefix(previous, rel)
        file_meta.append([prefix, rel[prefix:], len(row["raw"]), owners[idx]])
        previous = rel
    segment_meta = []
    for segment, blob in zip(segments, compressed, strict=True):
        segment_meta.append([[list(piece) for piece in segment["pieces"]], len(segment["raw"]), blob])
    body = msgpack.packb(["cmpct-segmented-solid-v3", variant, file_meta, segment_meta], use_bin_type=True)
    digest = hashlib.sha256(body).digest()
    archive.write_bytes(HEADER.pack(MAGIC, len(body), digest) + body)
    return {
        "variant": variant,
        "level": level,
        "workers": workers,
        "archive_bytes": archive.stat().st_size,
        "compress_manifest_hash_write_s": time.perf_counter() - started,
    }


def _extract(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short segmented-solid archive")
    magic, body_size, digest = HEADER.unpack(raw[:HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(body_size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("segmented-solid body identity mismatch")
    head = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 4 or head[0] != "cmpct-segmented-solid-v3":
        raise RuntimeError("bad segmented-solid metadata")
    _profile, variant, files, segment_rows = head
    if variant not in VARIANTS or not isinstance(files, list) or not isinstance(segment_rows, list):
        raise RuntimeError("bad segmented-solid profile")

    decoded_segments: list[bytes] = []
    piece_maps: list[list[list[int]]] = []
    for row in segment_rows:
        if not isinstance(row, list) or len(row) != 3:
            raise RuntimeError("bad segmented-solid segment")
        pieces, usize, blob = row
        usize = int(usize)
        if usize < 0 or usize > MAX_DECODE_UNIT or not isinstance(blob, bytes):
            raise RuntimeError("segmented-solid segment bounds")
        payload = zstd.ZstdDecompressor().decompress(blob, max_output_size=usize)
        if len(payload) != usize:
            raise RuntimeError("segmented-solid segment length")
        decoded_segments.append(payload)
        piece_maps.append(pieces)

    assembled = [bytearray(int(row[2])) for row in files]
    coverage = [0 for _ in files]
    for sid, (payload, pieces) in enumerate(zip(decoded_segments, piece_maps, strict=True)):
        cursor = 0
        for piece in pieces:
            if not isinstance(piece, list) or len(piece) != 3:
                raise RuntimeError("bad segmented-solid piece")
            file_idx, offset, length = map(int, piece)
            if file_idx < 0 or file_idx >= len(files) or length < 0 or cursor + length > len(payload):
                raise RuntimeError("segmented-solid piece bounds")
            end = offset + length
            if offset < 0 or end > len(assembled[file_idx]):
                raise RuntimeError("segmented-solid member bounds")
            assembled[file_idx][offset:end] = payload[cursor:cursor+length]
            coverage[file_idx] += length
            cursor += length
        if cursor != len(payload):
            raise RuntimeError("unowned segmented-solid segment bytes")

    dst.mkdir(parents=True, exist_ok=True)
    previous = ""
    seen: set[str] = set()
    for idx, row in enumerate(files):
        if not isinstance(row, list) or len(row) != 4:
            raise RuntimeError("bad segmented-solid file row")
        prefix, suffix, size, _segment_ids = row
        if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad segmented-solid path delta")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe segmented-solid path")
        if coverage[idx] != int(size):
            raise RuntimeError("segmented-solid member coverage")
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes(assembled[idx]))
        previous = rel
        seen.add(rel)


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-segmented-solid-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        candidates = []
        variant_stats = {}
        logical_files = logical_bytes = 0
        for variant in VARIANTS:
            pack_started = time.perf_counter()
            rows, logical_bytes = _source(stage, variant)
            segments, owners, max_amp, max_unit = _segment(rows)
            pack_source_s = time.perf_counter() - pack_started
            logical_files = len(rows)
            variant_stats[variant] = {
                "segments": len(segments),
                "pack_source_s": pack_source_s,
                "max_member_read_amplification": max_amp,
                "max_decode_unit_bytes": max_unit,
            }
            for level in LEVELS:
                for workers in WORKER_OPTIONS:
                    archive = root / f"{variant}-l{level}-w{workers}.bin"
                    result = _write_candidate(rows, segments, owners, archive, variant=variant, level=level, workers=workers)
                    result["pack_source_s"] = pack_source_s
                    result["create_s"] = pack_source_s + float(result["compress_manifest_hash_write_s"])
                    result["max_member_read_amplification"] = max_amp
                    result["max_decode_unit_bytes"] = max_unit
                    extracted = root / f"{variant}-l{level}-w{workers}-out"
                    _extract(archive, extracted)
                    B._verify_extracted(extracted, expected_tree, f"segmented-solid-{variant}-l{level}-w{workers}")
                    result["tree_verified"] = True
                    result["beats_zip_size"] = result["archive_bytes"] < zip_result["archive_bytes"]
                    result["beats_zstd19_size"] = result["archive_bytes"] < zstd_result["archive_bytes"]
                    result["beats_zip_create"] = result["create_s"] < zip_result["create_s"]
                    result["beats_zstd19_create"] = result["create_s"] < zstd_result["create_s"]
                    result["locality_green"] = max_amp <= MAX_MEMBER_AMPLIFICATION and max_unit <= MAX_DECODE_UNIT
                    result["viable"] = result["locality_green"] and all(result[k] for k in (
                        "beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create"
                    ))
                    candidates.append(result)

        viable = [c for c in candidates if c["viable"]]
        best = min(viable, key=lambda c: (c["archive_bytes"], c["create_s"], c["variant"], c["level"], c["workers"])) if viable else None
        closest = min(candidates, key=lambda c: (
            max(0, int(c["archive_bytes"]) - int(zstd_result["archive_bytes"])),
            max(0.0, float(c["create_s"]) - float(zip_result["create_s"])),
            c["archive_bytes"], c["create_s"]
        ))
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "logical_files": logical_files,
            "logical_bytes": logical_bytes,
            "variant_stats": variant_stats,
            "timing_boundary": "source-scan+segment-plan+zstd-segments+manifest+sha256+archive-write",
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidates": candidates,
            "viable_candidate": best,
            "closest_candidate": closest,
            "closest_zstd_size_gap_bytes": max(0, int(closest["archive_bytes"]) - int(zstd_result["archive_bytes"])),
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_segment_solid_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_segment_solid_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_segment_solid_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            if B._tree(workload) != accepted[key]["tree_sha256"]:
                raise RuntimeError(f"segmented-solid source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            best = row["viable_candidate"]
            print(json.dumps({
                "label": row["label"],
                "viable": None if best is None else [best["variant"], best["level"], best["workers"], best["archive_bytes"], best["create_s"]],
                "closest_zstd_gap": row["closest_zstd_size_gap_bytes"],
                "max_amp": max(v["max_member_read_amplification"] for v in row["variant_stats"].values()),
                "max_decode_unit": max(v["max_decode_unit_bytes"] for v in row["variant_stats"].values()),
            }, separators=(",", ":")), flush=True)

    viable_rows = [row for row in rows if row["viable_candidate"] is not None]
    return {
        "schema": "cmpct-v030-segmented-solid-oracle-v1",
        "claim_boundary": "research-only; locality-bounded but not canonical r25 and cannot authorize release",
        "max_member_read_amplification": MAX_MEMBER_AMPLIFICATION,
        "max_decode_unit_bytes": MAX_DECODE_UNIT,
        "levels": list(LEVELS),
        "variants": list(VARIANTS),
        "worker_options": list(WORKER_OPTIONS),
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "viable_workloads": len(viable_rows),
            "all_workloads_viable": len(viable_rows) == len(rows),
            "viable_labels": [row["label"] for row in viable_rows],
            "all_candidates_locality_green": all(c["locality_green"] for row in rows for c in row["candidates"]),
            "aggregate_closest_zstd_gap_bytes": sum(int(row["closest_zstd_size_gap_bytes"]) for row in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-segmented-solid-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-segmented-solid.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
