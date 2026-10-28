from __future__ import annotations

"""R4 Shifted content-defined shared-chunk store oracle.

Whole-snapshot ownership is now a proven dead end: single-base patch payload has a floor above solid Zstd-19 and
bounded 2/3/4-base ownership multiplies both bytes and construction time. This family changes the owner again.
Regular files are split by a content-derived native gear hash into bounded chunks; identical chunks across files
are stored exactly once and compressed independently. Member reconstruction is only its chunk list, so byte shifts
can resynchronize without requiring another full snapshot as a base.

Research-only. Candidate creation times native boundary scanning, source rereads, SHA-256 dedup, unique-chunk
compression, metadata/framing and publication. Helper compilation is tool setup, analogous to a prebuilt product
binary, and is not timed. No benchmark name/hash/path controls selection. Every chunk is <=256 KiB and selective
member reconstruction decodes only that member's chunks.
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

MAGIC = b"C30CDC1\0"
HEADER = struct.Struct("<8sQ32s")
MIN_CHUNK = 16 * 1024
MAX_CHUNK = 256 * 1024
ARMS = ((64 * 1024, 1), (64 * 1024, 3), (128 * 1024, 1))
WORKERS = 4


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
    if not ends or ends[-1] != size or any(a >= b for a, b in zip([0, *ends[:-1]], ends)):
        raise RuntimeError("CDC helper emitted invalid boundaries")
    starts = [0, *ends[:-1]]
    if any(end - start > MAX_CHUNK or end - start <= 0 for start, end in zip(starts, ends, strict=True)):
        raise RuntimeError("CDC chunk exceeds bounded decode unit")
    return ends


def _compress(raw: bytes, level: int) -> bytes:
    return zstd.ZstdCompressor(level=level, threads=0).compress(raw)


def build(root: Path, artifact: Path, *, average: int, level: int) -> dict:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in files):
        raise RuntimeError("CDC oracle requires regular files only")

    unique_raw: list[bytes] = []
    digest_to_ids: dict[bytes, list[int]] = {}
    file_rows = []
    logical_bytes = 0
    total_chunk_refs = 0
    duplicate_chunk_refs = 0
    max_file_amp = 0.0

    for path in files:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        logical_bytes += len(data)
        ends = _boundaries(path, average)
        starts = [0, *ends[:-1]]
        ids: list[int] = []
        decoded_context = 0
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
            total_chunk_refs += 1
            decoded_context += len(chunk)
        amp = decoded_context / max(1, len(data))
        max_file_amp = max(max_file_amp, amp)
        file_rows.append([rel, len(data), hashlib.sha256(data).digest(), ids])

    with ThreadPoolExecutor(max_workers=min(WORKERS, max(1, len(unique_raw))), thread_name_prefix="cmpct-cdc") as pool:
        blobs = list(pool.map(lambda raw: _compress(raw, level), unique_raw))

    chunk_rows = [[len(raw), hashlib.sha256(raw).digest(), blob] for raw, blob in zip(unique_raw, blobs, strict=True)]
    meta = msgpack.packb(
        ["cmpct-cdc-shared-store-v1", MIN_CHUNK, average, MAX_CHUNK, level, file_rows, chunk_rows],
        use_bin_type=True,
    )
    artifact.write_bytes(HEADER.pack(MAGIC, len(meta), hashlib.sha256(meta).digest()) + meta)
    create_s = time.perf_counter() - started
    unique_raw_bytes = sum(map(len, unique_raw))
    return {
        "archive_bytes": artifact.stat().st_size,
        "create_s": create_s,
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "average_chunk_bytes": average,
        "level": level,
        "files": len(file_rows),
        "logical_bytes": logical_bytes,
        "total_chunk_refs": total_chunk_refs,
        "unique_chunks": len(unique_raw),
        "duplicate_chunk_refs": duplicate_chunk_refs,
        "unique_raw_bytes": unique_raw_bytes,
        "exact_dedup_saving_raw_bytes": logical_bytes - unique_raw_bytes,
        "unique_payload_bytes": sum(map(len, blobs)),
        "max_decode_unit_bytes": max(map(len, unique_raw), default=0),
        "max_member_read_amplification": max_file_amp,
    }


def extract(artifact: Path, output: Path) -> None:
    raw = artifact.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short CDC artifact")
    magic, size, digest = HEADER.unpack(raw[: HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("CDC artifact identity mismatch")
    row = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(row, list) or len(row) != 7 or row[0] != "cmpct-cdc-shared-store-v1":
        raise RuntimeError("bad CDC artifact grammar")
    _, min_chunk, average, max_chunk, level, files, chunks = row
    if int(min_chunk) != MIN_CHUNK or int(max_chunk) != MAX_CHUNK or int(average) <= 0 or int(level) <= 0:
        raise RuntimeError("bad CDC profile parameters")

    decoded_chunks: list[bytes] = []
    for chunk in chunks:
        if not isinstance(chunk, list) or len(chunk) != 3:
            raise RuntimeError("bad CDC chunk row")
        usize, sha, blob = chunk
        usize = int(usize)
        if usize <= 0 or usize > MAX_CHUNK or not isinstance(sha, bytes) or len(sha) != 32 or not isinstance(blob, bytes):
            raise RuntimeError("bad CDC chunk bounds")
        value = zstd.ZstdDecompressor().decompress(blob, max_output_size=usize)
        if len(value) != usize or hashlib.sha256(value).digest() != sha:
            raise RuntimeError("CDC chunk integrity mismatch")
        decoded_chunks.append(value)

    output.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for file_row in files:
        if not isinstance(file_row, list) or len(file_row) != 4:
            raise RuntimeError("bad CDC file row")
        rel, size, sha, ids = file_row
        if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe CDC path")
        if not isinstance(ids, list) or not isinstance(sha, bytes) or len(sha) != 32:
            raise RuntimeError("bad CDC file identity")
        try:
            value = b"".join(decoded_chunks[int(cid)] for cid in ids)
        except (IndexError, ValueError, TypeError) as exc:
            raise RuntimeError("bad CDC chunk reference") from exc
        if len(value) != int(size) or hashlib.sha256(value).digest() != sha:
            raise RuntimeError("CDC member integrity mismatch")
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

    normalized_parent = work_root / "normalized-parent"; normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")
    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zstd_work = work_root / "zstd-work"; zstd_work.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zstd_work)
    if not zstd_result.get("available"):
        raise RuntimeError("solid Zstd-19 comparator unavailable")
    v029 = int(accepted["accepted_v029_bytes"])

    arms = []
    for average, level in ARMS:
        artifact = work_root / f"shifted-cdc-a{average}-l{level}.bin"
        result = build(stage, artifact, average=average, level=level)
        out = work_root / f"out-a{average}-l{level}"
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
        print(json.dumps({"average": average, "level": level, "bytes": result["archive_bytes"], "create_s": result["create_s"], "unique_raw": result["unique_raw_bytes"], "strict": strict}, separators=(",", ":")), flush=True)

    winners = [a for a in arms if a["tree_verified"] and a["strict"]["seven_way_win"]]
    best = min(arms, key=lambda a: (a["archive_bytes"], a["create_s"], a["average_chunk_bytes"], a["level"]))
    return {
        "schema": "cmpct-v030-shifted-cdc-store-oracle-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "diagnosis": "D4",
        "radicality": "R4",
        "saturation": ["S1", "S3", "S4"],
        "rps": 97,
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "content_defined_chunk_ownership": True,
            "creation_prices_helper_execution_and_all_candidate_work": True,
            "helper_compilation_outside_creation_timing": True,
            "max_decode_unit_bytes": MAX_CHUNK,
            "research_only": True,
            "release_credit": False,
        },
        "tree_sha256": expected_tree,
        "accepted_v029_bytes": v029,
        "comparators": {"zip_deflate9": zip_result, "tar_zstd19_solid": zstd_result},
        "arms": arms,
        "summary": {
            "strict_wins": len(winners),
            "winning_arms": [[a["average_chunk_bytes"], a["level"]] for a in winners],
            "best_size_bytes": best["archive_bytes"],
            "best_size_zstd_gap_bytes": best["archive_bytes"] - int(zstd_result["archive_bytes"]),
            "best_exact_dedup_saving_raw_bytes": max(a["exact_dedup_saving_raw_bytes"] for a in arms),
            "promotion_signal": bool(winners),
            "decision_if_strict_win": "PROMOTE_NEXT_PREREQUISITE",
            "decision_if_size_win_time_loss": "REHABILITATE_DEBT",
            "decision_if_no_material_size_closure": "RETIRE_FAMILY",
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
