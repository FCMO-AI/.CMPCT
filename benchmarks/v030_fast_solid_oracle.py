from __future__ import annotations

"""Fast solid-stream oracle for the v0.30 size+creation-speed contract.

This remains deliberately research-only: it does not create canonical r24/r25 bytes and cannot satisfy a release
receipt. Its purpose is to test whether a much cheaper solid representation has enough raw size/speed headroom to
justify productization. Every candidate is charged for source scanning, metadata construction, integrity hashing,
compression and archive publication, then fully extracted and checked against the frozen regular-file tree.

The first oracle showed only 3/15 strict wins, but most misses were tiny while every row carried a 32-byte SHA-256
per file inside the compressed stream. That tax is especially distorted on the 5,000-file corpus. v2 therefore
compares three *honest* metadata/integrity layouts while preserving exact round-trip verification:

``sha32-path``
    Original path-ordered rows with a full per-file SHA-256. This is the conservative control.
``compact-path``
    Path-ordered prefix-delta names + sizes, protected by one archive payload SHA-256.
``compact-ext``
    The same compact metadata, but payload members are deterministically grouped by extension before compression.
    Extraction restores original paths, so ordering is a compression decision rather than a semantic change.

The compact variants are not proposed as the final integrity model. A canonical implementation would still have
to satisfy the existing strong/member-integrity and <=8x locality requirements, likely with authenticated segment
hashes. This oracle only answers the prior question: is metadata/order overhead the reason a fast solid core misses
Zstd by a few KiB, or is the compression substrate itself insufficient?
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

MAGIC = b"C30SLD2\0"
HEADER = struct.Struct("<8sQ32s")
LEVELS = (1, 3, 6, 9, 12, 15, 19)
VARIANTS = ("sha32-path", "compact-path", "compact-ext")


def _common_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


def _ordered_files(stage: Path, variant: str) -> list[Path]:
    files = B._files(stage)
    if variant != "compact-ext":
        return files
    return sorted(
        files,
        key=lambda path: (
            path.suffix.lower(),
            path.name.lower(),
            path.relative_to(stage).as_posix(),
        ),
    )


def _pack_source(stage: Path, variant: str) -> tuple[bytes, int, int]:
    rows: list[list[object]] = []
    chunks: list[bytes] = []
    offset = 0
    previous = ""
    files = _ordered_files(stage, variant)
    for path in files:
        raw = path.read_bytes()
        rel = path.relative_to(stage).as_posix()
        if variant == "sha32-path":
            rows.append([rel, offset, len(raw), hashlib.sha256(raw).digest()])
        else:
            prefix = _common_prefix(previous, rel)
            rows.append([prefix, rel[prefix:], len(raw)])
            previous = rel
        chunks.append(raw)
        offset += len(raw)

    profile = "cmpct-fast-solid-sha32-v2" if variant == "sha32-path" else "cmpct-fast-solid-compact-v2"
    meta = msgpack.packb([profile, variant, rows], use_bin_type=True)
    payload = meta + b"".join(chunks)
    return payload, len(files), offset


def _write_candidate(payload: bytes, archive: Path, level: int, variant: str) -> dict:
    started = time.perf_counter()
    digest = hashlib.sha256(payload).digest()
    compressed = zstd.ZstdCompressor(level=level, threads=0).compress(payload)
    archive.write_bytes(HEADER.pack(MAGIC, len(payload), digest) + compressed)
    return {
        "variant": variant,
        "level": level,
        "archive_bytes": archive.stat().st_size,
        "compression_and_write_s": time.perf_counter() - started,
    }


def _decode_rows(head: list[object], content: bytes) -> list[tuple[str, bytes, bytes | None]]:
    if len(head) != 3 or not isinstance(head[0], str) or not isinstance(head[1], str) or not isinstance(head[2], list):
        raise RuntimeError("bad fast-solid metadata")
    profile, variant, rows = head
    decoded: list[tuple[str, bytes, bytes | None]] = []
    cursor = 0
    previous = ""
    for row in rows:
        if variant == "sha32-path":
            if not isinstance(row, list) or len(row) != 4:
                raise RuntimeError("bad sha32 row")
            rel, offset, size, digest = row
            start = int(offset)
            end = start + int(size)
            member = content[start:end]
            expected = bytes(digest)
            if start != cursor:
                raise RuntimeError("non-contiguous sha32 offsets")
        else:
            if not isinstance(row, list) or len(row) != 3:
                raise RuntimeError("bad compact row")
            prefix, suffix, size = row
            if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
                raise RuntimeError("bad compact path delta")
            rel = previous[:prefix] + suffix
            start = cursor
            end = start + int(size)
            member = content[start:end]
            expected = None
            previous = rel
        if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in Path(rel).parts:
            raise RuntimeError("unsafe fast-solid path")
        if len(member) != int(size):
            raise RuntimeError("fast-solid member length mismatch")
        if expected is not None and hashlib.sha256(member).digest() != expected:
            raise RuntimeError("fast-solid member identity mismatch")
        decoded.append((rel, member, expected))
        cursor = end
    if cursor != len(content):
        raise RuntimeError("fast-solid payload has trailing/unowned content")
    return decoded


def _extract_candidate(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short fast-solid oracle archive")
    magic, usize, expected_payload_sha = HEADER.unpack(raw[: HEADER.size])
    if magic != MAGIC:
        raise RuntimeError("bad fast-solid oracle magic")
    payload = zstd.ZstdDecompressor().decompress(raw[HEADER.size :], max_output_size=int(usize))
    if len(payload) != int(usize) or hashlib.sha256(payload).digest() != expected_payload_sha:
        raise RuntimeError("fast-solid payload identity mismatch")

    unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
    unpacker.feed(payload)
    head = next(unpacker)
    if not isinstance(head, list):
        raise RuntimeError("bad fast-solid metadata")
    meta = msgpack.packb(head, use_bin_type=True)
    content = payload[len(meta) :]
    decoded = _decode_rows(head, content)

    dst.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for rel, member, _digest in decoded:
        if rel in seen:
            raise RuntimeError("duplicate fast-solid path")
        seen.add(rel)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(member)


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-fast-solid-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)

        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        candidates = []
        variant_stats = {}
        for variant in VARIANTS:
            pack_started = time.perf_counter()
            payload, logical_files, logical_bytes = _pack_source(stage, variant)
            pack_source_s = time.perf_counter() - pack_started
            variant_stats[variant] = {
                "payload_bytes_before_zstd": len(payload),
                "pack_source_s": pack_source_s,
            }
            for level in LEVELS:
                archive = root / f"{variant}-l{level}.bin"
                result = _write_candidate(payload, archive, level, variant)
                result["pack_source_s"] = pack_source_s
                result["create_s"] = pack_source_s + float(result["compression_and_write_s"])
                extracted = root / f"{variant}-l{level}-out"
                _extract_candidate(archive, extracted)
                B._verify_extracted(extracted, expected_tree, f"fast-solid-{variant}-l{level}")
                result["tree_verified"] = True
                result["beats_zip_size"] = result["archive_bytes"] < zip_result["archive_bytes"]
                result["beats_zstd19_size"] = result["archive_bytes"] < zstd_result["archive_bytes"]
                result["beats_zip_create"] = result["create_s"] < zip_result["create_s"]
                result["beats_zstd19_create"] = result["create_s"] < zstd_result["create_s"]
                result["viable"] = all(
                    result[key]
                    for key in (
                        "beats_zip_size",
                        "beats_zstd19_size",
                        "beats_zip_create",
                        "beats_zstd19_create",
                    )
                )
                candidates.append(result)

        viable = [row for row in candidates if row["viable"]]
        best = min(viable, key=lambda row: (row["archive_bytes"], row["create_s"], row["variant"], row["level"])) if viable else None
        closest = min(
            candidates,
            key=lambda row: (
                max(0, int(row["archive_bytes"]) - int(zstd_result["archive_bytes"])),
                max(0.0, float(row["create_s"]) - float(zip_result["create_s"])),
                row["archive_bytes"],
            ),
        )
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "logical_files": logical_files,
            "logical_bytes": logical_bytes,
            "variant_stats": variant_stats,
            "timing_boundary": "source-scan+metadata-pack+integrity-hash+zstd-compress+archive-write",
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
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_fast_solid_neutral"
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_fast_solid_hostile"
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_fast_solid_repair")
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
                raise RuntimeError(f"fast-solid source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            best = row["viable_candidate"]
            print(
                json.dumps(
                    {
                        "label": row["label"],
                        "zip": [row["zip"]["archive_bytes"], row["zip"]["create_s"]],
                        "zstd19": [row["tar_zstd19"]["archive_bytes"], row["tar_zstd19"]["create_s"]],
                        "viable": None if best is None else [best["variant"], best["level"], best["archive_bytes"], best["create_s"]],
                        "closest_zstd_gap": row["closest_zstd_size_gap_bytes"],
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )

    viable_rows = [row for row in rows if row["viable_candidate"] is not None]
    total_gap = sum(int(row["closest_zstd_size_gap_bytes"]) for row in rows)
    return {
        "schema": "cmpct-v030-fast-solid-oracle-v2",
        "claim_boundary": "research-only; not canonical r24/r25 and cannot authorize release",
        "timing_policy": "every candidate create_s includes its variant pack_source_s exactly once",
        "levels": list(LEVELS),
        "variants": list(VARIANTS),
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "viable_workloads": len(viable_rows),
            "all_workloads_viable": len(viable_rows) == len(rows),
            "viable_labels": [row["label"] for row in viable_rows],
            "aggregate_closest_zstd_gap_bytes": total_gap,
            "max_closest_zstd_gap_bytes": max(int(row["closest_zstd_size_gap_bytes"]) for row in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-fast-solid-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-fast-solid.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
