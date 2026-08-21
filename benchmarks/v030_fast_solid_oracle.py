from __future__ import annotations

"""Fast solid-stream oracle for the v0.30 size+creation-speed contract.

This is deliberately research-only: it does not create canonical r24/r25 bytes and cannot satisfy a release gate.
Its job is to test a concrete architectural hypothesis suggested by current evidence: canonical r24 is already
fast, while most v0.30 wall-clock is spent searching research graphs. A compact whole-tree stream may recover
solid-compression gains without tar framing or subprocess overhead.

For each frozen regular-file workload, the oracle:
- normalizes the exact same source tree used by the external competitor matrix;
- encodes a deterministic compact stream of path/length/content records;
- compresses that stream in-process with python-zstandard at several levels;
- reconstructs and verifies the exact historical regular-file tree identity;
- compares complete candidate bytes and end-to-end creation wall-clock against deterministic ZIP/Deflate-9 and
  the existing tar+Zstd-19 competitor on the same normalized stage.

Candidate creation time includes the complete source scan, content hashing, metadata packing, compression and
archive write. The level sweep reuses the packed payload only as an experiment implementation detail; the measured
``create_s`` for every candidate adds the independently measured pack-source cost back in, so no candidate is
credited for work that a standalone encoder would have to perform.

No result is promoted automatically. A viable row requires one candidate level to be strictly smaller *and*
strictly faster to create than both ZIP and tar+Zstd-19. Equality is failure, matching the frozen v0.30 law.
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

MAGIC = b"C30SOL1\0"
HEADER = struct.Struct("<8sQ")
LEVELS = (1, 3, 6, 9, 12, 15, 19)


def _pack_source(stage: Path) -> tuple[bytes, list[list[object]]]:
    rows: list[list[object]] = []
    chunks: list[bytes] = []
    offset = 0
    for path in B._files(stage):
        raw = path.read_bytes()
        rel = path.relative_to(stage).as_posix()
        rows.append([rel, offset, len(raw), hashlib.sha256(raw).digest()])
        chunks.append(raw)
        offset += len(raw)
    meta = msgpack.packb(["cmpct-fast-solid-oracle-v1", rows], use_bin_type=True)
    return meta + b"".join(chunks), rows


def _write_candidate(payload: bytes, archive: Path, level: int) -> dict:
    started = time.perf_counter()
    compressed = zstd.ZstdCompressor(level=level, threads=0).compress(payload)
    archive.write_bytes(HEADER.pack(MAGIC, len(payload)) + compressed)
    return {
        "level": level,
        "archive_bytes": archive.stat().st_size,
        "compression_and_write_s": time.perf_counter() - started,
    }


def _extract_candidate(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short fast-solid oracle archive")
    magic, usize = HEADER.unpack(raw[: HEADER.size])
    if magic != MAGIC:
        raise RuntimeError("bad fast-solid oracle magic")
    payload = zstd.ZstdDecompressor().decompress(raw[HEADER.size :], max_output_size=int(usize))
    if len(payload) != int(usize):
        raise RuntimeError("fast-solid oracle payload length mismatch")
    unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
    unpacker.feed(payload)
    head = next(unpacker)
    if not isinstance(head, list) or len(head) != 2 or head[0] != "cmpct-fast-solid-oracle-v1":
        raise RuntimeError("bad fast-solid oracle metadata")
    meta = msgpack.packb(head, use_bin_type=True)
    content = payload[len(meta) :]
    dst.mkdir(parents=True, exist_ok=True)
    for row in head[1]:
        rel, offset, size, digest = row
        if not isinstance(rel, str) or rel.startswith("/") or ".." in Path(rel).parts:
            raise RuntimeError("unsafe fast-solid oracle path")
        start = int(offset)
        end = start + int(size)
        member = content[start:end]
        if len(member) != int(size) or hashlib.sha256(member).digest() != bytes(digest):
            raise RuntimeError("fast-solid oracle member identity mismatch")
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(member)


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-fast-solid-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)

        pack_started = time.perf_counter()
        payload, rows = _pack_source(stage)
        pack_source_s = time.perf_counter() - pack_started

        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        candidates = []
        for level in LEVELS:
            archive = root / f"solid-l{level}.bin"
            result = _write_candidate(payload, archive, level)
            result["pack_source_s"] = pack_source_s
            result["create_s"] = pack_source_s + float(result["compression_and_write_s"])
            extracted = root / f"solid-l{level}-out"
            _extract_candidate(archive, extracted)
            B._verify_extracted(extracted, expected_tree, f"fast-solid-l{level}")
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
        best = min(viable, key=lambda row: (row["archive_bytes"], row["create_s"], row["level"])) if viable else None
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "logical_files": len(rows),
            "logical_bytes": sum(int(row[2]) for row in rows),
            "payload_bytes_before_zstd": len(payload),
            "pack_source_s": pack_source_s,
            "timing_boundary": "source-scan+sha256+metadata-pack+zstd-compress+archive-write",
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidates": candidates,
            "viable_level": None if best is None else best["level"],
            "viable_candidate": best,
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
                        "pack_source_s": row["pack_source_s"],
                        "viable": None if best is None else [best["level"], best["archive_bytes"], best["create_s"]],
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )

    viable_rows = [row for row in rows if row["viable_candidate"] is not None]
    return {
        "schema": "cmpct-v030-fast-solid-oracle-v1",
        "claim_boundary": "research-only; not canonical r24/r25 and cannot authorize release",
        "timing_policy": "every candidate create_s includes pack_source_s exactly once",
        "levels": list(LEVELS),
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "viable_workloads": len(viable_rows),
            "all_workloads_viable": len(viable_rows) == len(rows),
            "viable_labels": [row["label"] for row in viable_rows],
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
