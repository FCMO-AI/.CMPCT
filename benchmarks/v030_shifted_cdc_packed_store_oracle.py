from __future__ import annotations

"""R4 Shifted CDC packed-store oracle.

The independently-compressed CDC store is a proven terminal negative because its compressed payload floor
is already far above solid Zstd-19. This experiment changes the representation rather than tuning that family:
content-defined chunks are still deduplicated exactly, but unique chunks are kept in deterministic first-seen
order, grouped into bounded shared packs, and each pack is entropy-coded as one stream. This preserves
cross-chunk compression context within a bounded locality unit while retaining exact chunk reuse across files.

Research only. All boundary scanning, source reads, hashing/dedup, pack construction, compression, framing,
and publication are inside candidate creation time. Helper compilation is product-tool setup and is outside the
timed region. No benchmark name, source path, corpus hash, or frozen identity affects representation choices.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time

import msgpack
import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_authoritative as CMPCT

MAGIC = b"C30CDP1\0"
HEADER = struct.Struct("<8sQ32s")
MIN_CHUNK = 16 * 1024
MAX_CHUNK = 256 * 1024
MAX_PACK = 2 * 1024 * 1024
WORKERS = 4
# Mean CDC chunk, pack ceiling, zstd level. Every arm is generic and content-derived.
ARMS = (
    (64 * 1024, 1 * 1024 * 1024, 3),
    (64 * 1024, 2 * 1024 * 1024, 3),
    (64 * 1024, 2 * 1024 * 1024, 9),
    (128 * 1024, 2 * 1024 * 1024, 3),
)


def _helper() -> Path:
    raw = os.environ.get("CMPCT_CDC_HELPER")
    if not raw:
        raise RuntimeError("CMPCT_CDC_HELPER must point to the prebuilt native boundary scanner")
    path = Path(raw)
    if not path.is_file():
        raise RuntimeError("CDC boundary helper is unavailable")
    return path


def _boundaries(path: Path, average: int) -> list[int]:
    if average <= 0 or average & (average - 1):
        raise RuntimeError("CDC average must be a power of two")
    mask = average - 1
    raw = subprocess.check_output([str(_helper()), str(path), str(MIN_CHUNK), str(mask), str(MAX_CHUNK)])
    if len(raw) % 8:
        raise RuntimeError("CDC helper emitted malformed boundary stream")
    ends = [struct.unpack_from("<Q", raw, off)[0] for off in range(0, len(raw), 8)]
    size = path.stat().st_size
    if size == 0:
        if ends:
            raise RuntimeError("empty CDC source emitted boundaries")
        return []
    if not ends or ends[-1] != size:
        raise RuntimeError("CDC helper omitted terminal boundary")
    starts = [0, *ends[:-1]]
    if any(a >= b for a, b in zip(starts, ends, strict=True)):
        raise RuntimeError("CDC helper emitted non-increasing boundaries")
    if any(end - start > MAX_CHUNK for start, end in zip(starts, ends, strict=True)):
        raise RuntimeError("CDC chunk exceeds bounded decode unit")
    return ends


def _compress(raw: bytes, level: int) -> bytes:
    return zstd.ZstdCompressor(level=level, threads=0).compress(raw)


def _pack_unique(unique_raw: list[bytes], pack_limit: int) -> tuple[list[bytes], list[tuple[int, int, int]]]:
    if pack_limit <= 0 or pack_limit > MAX_PACK:
        raise RuntimeError("invalid pack limit")
    packs: list[bytearray] = []
    locs: list[tuple[int, int, int]] = []
    current = bytearray()
    for chunk in unique_raw:
        if len(chunk) > pack_limit:
            raise RuntimeError("chunk larger than pack ceiling")
        if current and len(current) + len(chunk) > pack_limit:
            packs.append(current)
            current = bytearray()
        pack_id = len(packs)
        offset = len(current)
        current.extend(chunk)
        locs.append((pack_id, offset, len(chunk)))
    if current:
        packs.append(current)
    return [bytes(p) for p in packs], locs


def build(root: Path, artifact: Path, *, average: int, pack_limit: int, level: int) -> dict:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in files):
        raise RuntimeError("packed CDC oracle requires regular files only")

    unique_raw: list[bytes] = []
    digest_to_ids: dict[bytes, list[int]] = {}
    file_specs: list[tuple[str, int, bytes, list[int]]] = []
    logical_bytes = 0
    duplicate_chunk_refs = 0

    for path in files:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        logical_bytes += len(data)
        ends = _boundaries(path, average)
        starts = [0, *ends[:-1]]
        ids: list[int] = []
        for start, end in zip(starts, ends, strict=True):
            chunk = data[start:end]
            digest = hashlib.sha256(chunk).digest()
            found = None
            for cid in digest_to_ids.get(digest, []):
                if unique_raw[cid] == chunk:
                    found = cid
                    break
            if found is None:
                found = len(unique_raw)
                unique_raw.append(chunk)
                digest_to_ids.setdefault(digest, []).append(found)
            else:
                duplicate_chunk_refs += 1
            ids.append(found)
        file_specs.append((rel, len(data), hashlib.sha256(data).digest(), ids))

    raw_packs, locs = _pack_unique(unique_raw, pack_limit)
    with ThreadPoolExecutor(max_workers=min(WORKERS, max(1, len(raw_packs))), thread_name_prefix="cmpct-cdc-pack") as pool:
        blobs = list(pool.map(lambda raw: _compress(raw, level), raw_packs))

    chunk_rows = [
        [pack_id, offset, size, hashlib.sha256(raw).digest()]
        for raw, (pack_id, offset, size) in zip(unique_raw, locs, strict=True)
    ]
    pack_rows = [[len(raw), hashlib.sha256(raw).digest(), blob] for raw, blob in zip(raw_packs, blobs, strict=True)]
    file_rows = [[rel, size, sha, ids] for rel, size, sha, ids in file_specs]
    meta = msgpack.packb(
        ["cmpct-cdc-packed-store-v1", MIN_CHUNK, average, MAX_CHUNK, pack_limit, level, file_rows, chunk_rows, pack_rows],
        use_bin_type=True,
    )
    artifact.write_bytes(HEADER.pack(MAGIC, len(meta), hashlib.sha256(meta).digest()) + meta)
    create_s = time.perf_counter() - started

    max_amp = 0.0
    for _rel, size, _sha, ids in file_specs:
        touched = {locs[cid][0] for cid in ids}
        decoded = sum(len(raw_packs[pid]) for pid in touched)
        max_amp = max(max_amp, decoded / max(1, size))

    unique_raw_bytes = sum(map(len, unique_raw))
    return {
        "archive_bytes": artifact.stat().st_size,
        "create_s": create_s,
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "average_chunk_bytes": average,
        "pack_limit_bytes": pack_limit,
        "level": level,
        "files": len(file_rows),
        "logical_bytes": logical_bytes,
        "total_chunk_refs": sum(len(row[3]) for row in file_rows),
        "unique_chunks": len(unique_raw),
        "duplicate_chunk_refs": duplicate_chunk_refs,
        "unique_raw_bytes": unique_raw_bytes,
        "exact_dedup_saving_raw_bytes": logical_bytes - unique_raw_bytes,
        "pack_count": len(raw_packs),
        "packed_payload_bytes": sum(map(len, blobs)),
        "max_decode_unit_bytes": max(map(len, raw_packs), default=0),
        "max_member_read_amplification": max_amp,
    }


def extract(artifact: Path, output: Path) -> None:
    raw = artifact.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short packed CDC artifact")
    magic, size, digest = HEADER.unpack(raw[:HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("packed CDC artifact identity mismatch")
    row = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(row, list) or len(row) != 9 or row[0] != "cmpct-cdc-packed-store-v1":
        raise RuntimeError("bad packed CDC grammar")
    _, min_chunk, average, max_chunk, pack_limit, level, files, chunks, packs = row
    if int(min_chunk) != MIN_CHUNK or int(max_chunk) != MAX_CHUNK:
        raise RuntimeError("bad packed CDC bounds")
    if int(average) <= 0 or int(pack_limit) <= 0 or int(pack_limit) > MAX_PACK or int(level) <= 0:
        raise RuntimeError("bad packed CDC profile")

    decoded_packs: list[bytes] = []
    for pack in packs:
        if not isinstance(pack, list) or len(pack) != 3:
            raise RuntimeError("bad packed CDC pack row")
        usize, sha, blob = pack
        usize = int(usize)
        if usize <= 0 or usize > MAX_PACK or not isinstance(sha, bytes) or len(sha) != 32 or not isinstance(blob, bytes):
            raise RuntimeError("bad packed CDC pack bounds")
        value = zstd.ZstdDecompressor().decompress(blob, max_output_size=usize)
        if len(value) != usize or hashlib.sha256(value).digest() != sha:
            raise RuntimeError("packed CDC pack integrity mismatch")
        decoded_packs.append(value)

    decoded_chunks: list[bytes] = []
    for chunk in chunks:
        if not isinstance(chunk, list) or len(chunk) != 4:
            raise RuntimeError("bad packed CDC chunk row")
        pack_id, offset, size, sha = chunk
        pack_id, offset, size = int(pack_id), int(offset), int(size)
        if pack_id < 0 or pack_id >= len(decoded_packs) or offset < 0 or size <= 0 or size > MAX_CHUNK:
            raise RuntimeError("bad packed CDC chunk reference")
        value = decoded_packs[pack_id][offset:offset + size]
        if len(value) != size or not isinstance(sha, bytes) or len(sha) != 32 or hashlib.sha256(value).digest() != sha:
            raise RuntimeError("packed CDC chunk integrity mismatch")
        decoded_chunks.append(value)

    output.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for file_row in files:
        if not isinstance(file_row, list) or len(file_row) != 4:
            raise RuntimeError("bad packed CDC file row")
        rel, size, sha, ids = file_row
        if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe packed CDC path")
        if not isinstance(ids, list) or not isinstance(sha, bytes) or len(sha) != 32:
            raise RuntimeError("bad packed CDC file identity")
        try:
            value = b"".join(decoded_chunks[int(cid)] for cid in ids)
        except (IndexError, ValueError, TypeError) as exc:
            raise RuntimeError("bad packed CDC file reference") from exc
        if len(value) != int(size) or hashlib.sha256(value).digest() != sha:
            raise RuntimeError("packed CDC member integrity mismatch")
        dst = output.joinpath(*Path(rel).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(value)
        seen.add(rel)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    HOSTILE.shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = HOSTILE.tree_hash(source)
    accepted = GENERAL._accepted_v029_rows()[("resemblance_hostile_v1", "01_shifted_versions")]
    if expected_tree != accepted["tree_sha256"]:
        raise RuntimeError("Shifted corpus tree drift")

    normalized_parent = work_root / "normalized-parent"
    normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")
    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zstd_work)
    if not zstd_result.get("available"):
        raise RuntimeError("solid Zstd-19 comparator unavailable")
    v029 = int(accepted["accepted_v029_bytes"])

    arms = []
    for average, pack_limit, level in ARMS:
        artifact = work_root / f"shifted-cdc-packed-a{average}-p{pack_limit}-l{level}.bin"
        result = build(stage, artifact, average=average, pack_limit=pack_limit, level=level)
        out = work_root / f"out-a{average}-p{pack_limit}-l{level}"
        extract(artifact, out)
        tree = CMPCT.treehash(out)
        strict = {
            "beats_v029_size": result["archive_bytes"] < v029,
            "beats_zip_size": result["archive_bytes"] < int(zip_result["archive_bytes"]),
            "beats_zstd19_size": result["archive_bytes"] < int(zstd_result["archive_bytes"]),
            "beats_zip_create": result["create_s"] < float(zip_result["create_s"]),
            "beats_zstd19_create": result["create_s"] < float(zstd_result["create_s"]),
            "locality_le_8x": result["max_member_read_amplification"] <= 8.0,
            "decode_unit_le_8mib": result["max_decode_unit_bytes"] <= 8 * 1024 * 1024,
        }
        strict["seven_way_win"] = all(strict.values())
        arms.append({**result, "tree_sha256": tree, "tree_verified": tree == expected_tree, "strict": strict})
        print(json.dumps({"average": average, "pack": pack_limit, "level": level, "bytes": result["archive_bytes"], "create_s": result["create_s"], "payload": result["packed_payload_bytes"], "amp": result["max_member_read_amplification"], "strict": strict}, separators=(",", ":")), flush=True)

    winners = [a for a in arms if a["tree_verified"] and a["strict"]["seven_way_win"]]
    best = min(arms, key=lambda a: (a["archive_bytes"], a["create_s"], a["pack_limit_bytes"], a["level"]))
    zstd_bytes = int(zstd_result["archive_bytes"])
    return {
        "schema": "cmpct-v030-shifted-cdc-packed-store-oracle-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "diagnosis": "D4",
        "radicality": "R4",
        "saturation_inherited": ["S1", "S3", "S4"],
        "rps": 98,
        "referee": {
            "simplest_control": "retired independent CDC store",
            "causal_hypothesis": "deduplicate exact resynchronizing chunks without discarding cross-chunk entropy context",
            "strongest_failure": "bounded packs may still destroy too much long-range context or locality may force packs too small",
            "retire_if": "optimistic packed payload remains above Zstd-19 or no arm closes at least 25% of the inherited strict size gap while satisfying locality",
        },
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "content_defined_exact_dedup": True,
            "ordered_bounded_shared_pack_context": True,
            "creation_prices_all_candidate_work": True,
            "max_pack_bytes": MAX_PACK,
            "research_only": True,
            "release_credit": False,
        },
        "tree_sha256": expected_tree,
        "accepted_v029_bytes": v029,
        "comparators": {"zip_deflate9": zip_result, "tar_zstd19_solid": zstd_result},
        "arms": arms,
        "summary": {
            "strict_wins": len(winners),
            "winning_arms": [[a["average_chunk_bytes"], a["pack_limit_bytes"], a["level"]] for a in winners],
            "best_size_bytes": best["archive_bytes"],
            "best_size_zstd_gap_bytes": best["archive_bytes"] - zstd_bytes,
            "best_payload_bytes": min(a["packed_payload_bytes"] for a in arms),
            "best_payload_zstd_gap_bytes": min(a["packed_payload_bytes"] for a in arms) - zstd_bytes,
            "promotion_signal": bool(winners),
            "decision_if_strict_win": "PROMOTE_NEXT_PREREQUISITE",
            "decision_if_payload_below_zstd_but_framing_miss": "ITERATE_SAME_FAMILY",
            "decision_if_payload_floor_above_zstd": "RETIRE_FAMILY",
            "release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
