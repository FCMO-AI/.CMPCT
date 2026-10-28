from __future__ import annotations

"""Research oracle: compact inline solid framing for the v0.30 strict external contract.

The v2 fast-solid sweep reached 6/15 workloads that were simultaneously smaller and faster to create than both
ZIP/Deflate-9 and solid tar+Zstd-19.  Several remaining rows missed Zstd by only a few KiB.  v2 placed all compact
metadata before all file contents, while tar naturally interleaves each pathname header with its payload.  That
layout difference can change Zstd's local context enough to matter when the deficit is measured in hundreds or
thousands of bytes.

This oracle therefore tests two reversible compact-inline layouts:

``inline-path``
    Frozen path order.  Each row stores prefix-delta path + raw member bytes together.
``inline-ext``
    The same framing after deterministic extension grouping.

For levels 12/15/19 the oracle also tries four Zstd worker threads.  Worker startup and all compression time are
inside ``create_s``.  Every candidate additionally pays for source scan, compact metadata construction, payload
SHA-256 and archive publication, and every result is fully decoded and exact-tree verified.  Ties lose.

These bytes are deliberately research-only and cannot satisfy a release receipt.  A successful shape would still
need a bounded canonical r25 grammar, <=8x selective-read locality, strong/member integrity and native/Android
parity before promotion.
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

MAGIC = b"C30INL3\0"
HEADER = struct.Struct("<8sQ32s")
LEVELS = (1, 3, 6, 9, 12, 15, 19)
VARIANTS = ("inline-path", "inline-ext")
THREADED_LEVELS = frozenset((12, 15, 19))
THREAD_OPTIONS = (0, 4)


def _common_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


def _ordered_files(stage: Path, variant: str) -> list[Path]:
    files = B._files(stage)
    if variant == "inline-path":
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
    previous = ""
    logical_bytes = 0
    for path in _ordered_files(stage, variant):
        raw = path.read_bytes()
        rel = path.relative_to(stage).as_posix()
        prefix = _common_prefix(previous, rel)
        # Keeping each member beside its compact path metadata is the entire experiment.  The raw member is a
        # MessagePack bin value so parsing stays deterministic and bounded by the already-frozen corpus envelope.
        rows.append([prefix, rel[prefix:], raw])
        previous = rel
        logical_bytes += len(raw)
    payload = msgpack.packb(["cmpct-fast-solid-inline-v3", variant, rows], use_bin_type=True)
    return payload, len(rows), logical_bytes


def _write_candidate(payload: bytes, archive: Path, level: int, variant: str, threads: int) -> dict:
    started = time.perf_counter()
    digest = hashlib.sha256(payload).digest()
    compressed = zstd.ZstdCompressor(level=level, threads=threads).compress(payload)
    archive.write_bytes(HEADER.pack(MAGIC, len(payload), digest) + compressed)
    return {
        "variant": variant,
        "level": level,
        "threads": threads,
        "archive_bytes": archive.stat().st_size,
        "compression_hash_write_s": time.perf_counter() - started,
    }


def _extract_candidate(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short inline-solid oracle archive")
    magic, usize, expected_sha = HEADER.unpack(raw[: HEADER.size])
    if magic != MAGIC:
        raise RuntimeError("bad inline-solid oracle magic")
    payload = zstd.ZstdDecompressor().decompress(raw[HEADER.size :], max_output_size=int(usize))
    if len(payload) != int(usize) or hashlib.sha256(payload).digest() != expected_sha:
        raise RuntimeError("inline-solid payload identity mismatch")
    head = msgpack.unpackb(payload, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 3 or head[0] != "cmpct-fast-solid-inline-v3":
        raise RuntimeError("bad inline-solid metadata")
    variant, rows = head[1], head[2]
    if variant not in VARIANTS or not isinstance(rows, list):
        raise RuntimeError("bad inline-solid profile")

    dst.mkdir(parents=True, exist_ok=True)
    previous = ""
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, list) or len(row) != 3:
            raise RuntimeError("bad inline-solid row")
        prefix, suffix, member = row
        if not isinstance(prefix, int) or not isinstance(suffix, str) or not isinstance(member, bytes):
            raise RuntimeError("bad inline-solid row types")
        if prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad inline-solid path prefix")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe/duplicate inline-solid path")
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(member)
        previous = rel
        seen.add(rel)


def _thread_choices(level: int) -> tuple[int, ...]:
    return THREAD_OPTIONS if level in THREADED_LEVELS else (0,)


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-inline-solid-", dir=work) as td:
        root = Path(td)
        stage = B._normalized_stage(source, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        candidates: list[dict] = []
        variant_stats: dict[str, dict] = {}
        logical_files = logical_bytes = 0
        for variant in VARIANTS:
            pack_started = time.perf_counter()
            payload, logical_files, logical_bytes = _pack_source(stage, variant)
            pack_source_s = time.perf_counter() - pack_started
            variant_stats[variant] = {
                "payload_bytes_before_zstd": len(payload),
                "pack_source_s": pack_source_s,
            }
            for level in LEVELS:
                for threads in _thread_choices(level):
                    archive = root / f"{variant}-l{level}-t{threads}.bin"
                    result = _write_candidate(payload, archive, level, variant, threads)
                    result["pack_source_s"] = pack_source_s
                    result["create_s"] = pack_source_s + float(result["compression_hash_write_s"])
                    extracted = root / f"{variant}-l{level}-t{threads}-out"
                    _extract_candidate(archive, extracted)
                    B._verify_extracted(extracted, expected_tree, f"inline-solid-{variant}-l{level}-t{threads}")
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
        best = min(
            viable,
            key=lambda row: (row["archive_bytes"], row["create_s"], row["variant"], row["level"], row["threads"]),
        ) if viable else None
        closest = min(
            candidates,
            key=lambda row: (
                max(0, int(row["archive_bytes"]) - int(zstd_result["archive_bytes"])),
                max(0.0, float(row["create_s"]) - float(zip_result["create_s"])),
                row["archive_bytes"],
                row["create_s"],
            ),
        )
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "logical_files": logical_files,
            "logical_bytes": logical_bytes,
            "variant_stats": variant_stats,
            "timing_boundary": "source-scan+inline-metadata-pack+payload-sha256+zstd-compress+archive-write",
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidates": candidates,
            "viable_candidate": best,
            "closest_candidate": closest,
            "closest_zstd_size_gap_bytes": max(0, int(closest["archive_bytes"]) - int(zstd_result["archive_bytes"])),
            "closest_zip_create_gap_s": max(0.0, float(closest["create_s"]) - float(zip_result["create_s"])),
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_inline_solid_neutral"
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_inline_solid_hostile"
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_inline_solid_repair")
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
                raise RuntimeError(f"inline-solid source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            best = row["viable_candidate"]
            print(json.dumps({
                "label": row["label"],
                "zip": [row["zip"]["archive_bytes"], row["zip"]["create_s"]],
                "zstd19": [row["tar_zstd19"]["archive_bytes"], row["tar_zstd19"]["create_s"]],
                "viable": None if best is None else [best["variant"], best["level"], best["threads"], best["archive_bytes"], best["create_s"]],
                "closest_zstd_gap": row["closest_zstd_size_gap_bytes"],
                "closest_zip_create_gap_s": row["closest_zip_create_gap_s"],
            }, separators=(",", ":")), flush=True)

    viable_rows = [row for row in rows if row["viable_candidate"] is not None]
    return {
        "schema": "cmpct-v030-fast-solid-inline-oracle-v3",
        "claim_boundary": "research-only; not canonical r24/r25 and cannot authorize release",
        "timing_policy": "every candidate create_s includes inline pack_source_s plus payload hash/compress/write exactly once",
        "levels": list(LEVELS),
        "variants": list(VARIANTS),
        "thread_options": list(THREAD_OPTIONS),
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "viable_workloads": len(viable_rows),
            "all_workloads_viable": len(viable_rows) == len(rows),
            "viable_labels": [row["label"] for row in viable_rows],
            "aggregate_closest_zstd_gap_bytes": sum(int(row["closest_zstd_size_gap_bytes"]) for row in rows),
            "max_closest_zstd_gap_bytes": max(int(row["closest_zstd_size_gap_bytes"]) for row in rows),
            "aggregate_closest_zip_create_gap_s": sum(float(row["closest_zip_create_gap_s"]) for row in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-inline-solid-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-inline-solid.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
