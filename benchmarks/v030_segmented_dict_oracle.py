from __future__ import annotations

"""Shared-dictionary segmented-solid research oracle for CMPCT v0.30.

The existing segmented-solid oracle proved that strict <=8x member-read amplification and <=8 MiB decode units
can coexist with very fast creation, but several rows miss solid Zstd-19 by only a few KiB. This follow-up asks a
narrower question: can independently decodable segments recover cross-segment redundancy through one shared Zstd
dictionary without spending locality?

The dictionary is trained from the same bounded segments that are later compressed. Dictionary training time and
dictionary bytes are charged to every candidate. Each segment remains an independent frame, so reading a member
still decodes only its owning segment(s). Every candidate is fully extracted and exact-tree verified. This remains
research-only; a positive result does not become canonical r25 until reader/native/Android/integrity/product gates
are implemented and passed.
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
from benchmarks import v030_segmented_solid_oracle as BASE

MAGIC = b"C30SGD1\0"
HEADER = struct.Struct("<8sQ32s")
LEVELS = (1, 3, 6, 9)
DICT_SIZES = (8 * 1024, 16 * 1024)
VARIANTS = BASE.VARIANTS
WORKERS = 4


def _train(raw_segments: list[bytes], dict_size: int) -> tuple[bytes | None, float, str | None]:
    started = time.perf_counter()
    samples = [raw for raw in raw_segments if len(raw) >= 64]
    if len(samples) < 8 or sum(map(len, samples)) < max(32 * 1024, dict_size * 4):
        return None, time.perf_counter() - started, "insufficient-training-samples"
    size = min(dict_size, max(1024, sum(map(len, samples)) // 8))
    try:
        trained = zstd.train_dictionary(size, samples)
        raw = trained.as_bytes()
    except Exception as exc:
        return None, time.perf_counter() - started, f"train-failed:{type(exc).__name__}"
    return raw, time.perf_counter() - started, None


def _compress_one(raw: bytes, level: int, dictionary: bytes) -> bytes:
    zd = zstd.ZstdCompressionDict(dictionary)
    return zstd.ZstdCompressor(level=level, dict_data=zd, threads=0).compress(raw)


def _write_candidate(rows: list[dict], segments: list[dict], owners: list[list[int]], archive: Path, *,
                     variant: str, level: int, dictionary: bytes, train_s: float) -> dict:
    started = time.perf_counter()
    raw_segments = [segment["raw"] for segment in segments]
    if len(raw_segments) <= 1:
        compressed = [_compress_one(raw, level, dictionary) for raw in raw_segments]
    else:
        with ThreadPoolExecutor(max_workers=min(WORKERS, len(raw_segments)), thread_name_prefix="cmpct-segdict") as pool:
            compressed = list(pool.map(lambda raw: _compress_one(raw, level, dictionary), raw_segments))

    file_meta = []
    previous = ""
    for idx, row in enumerate(rows):
        rel = row["rel"]
        prefix = BASE._common_prefix(previous, rel)
        file_meta.append([prefix, rel[prefix:], len(row["raw"]), owners[idx]])
        previous = rel
    segment_meta = []
    for segment, blob in zip(segments, compressed, strict=True):
        segment_meta.append([[list(piece) for piece in segment["pieces"]], len(segment["raw"]), blob])
    body = msgpack.packb(["cmpct-segmented-dict-v1", variant, dictionary, file_meta, segment_meta], use_bin_type=True)
    digest = hashlib.sha256(body).digest()
    archive.write_bytes(HEADER.pack(MAGIC, len(body), digest) + body)
    encode_s = time.perf_counter() - started
    return {
        "variant": variant,
        "level": level,
        "dict_bytes": len(dictionary),
        "workers": min(WORKERS, max(1, len(raw_segments))),
        "archive_bytes": archive.stat().st_size,
        "dictionary_train_s": train_s,
        "compress_manifest_hash_write_s": encode_s,
    }


def _extract(archive: Path, dst: Path) -> None:
    raw = archive.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short segmented-dict archive")
    magic, body_size, digest = HEADER.unpack(raw[:HEADER.size])
    body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(body_size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("segmented-dict body identity mismatch")
    head = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(head, list) or len(head) != 5 or head[0] != "cmpct-segmented-dict-v1":
        raise RuntimeError("bad segmented-dict metadata")
    _profile, variant, dictionary, files, segment_rows = head
    if variant not in VARIANTS or not isinstance(dictionary, bytes):
        raise RuntimeError("bad segmented-dict profile")
    zd = zstd.ZstdCompressionDict(dictionary)
    decompressor = zstd.ZstdDecompressor(dict_data=zd)

    decoded_segments: list[bytes] = []
    piece_maps: list[list[list[int]]] = []
    for row in segment_rows:
        if not isinstance(row, list) or len(row) != 3:
            raise RuntimeError("bad segmented-dict segment")
        pieces, usize, blob = row
        usize = int(usize)
        if usize < 0 or usize > BASE.MAX_DECODE_UNIT or not isinstance(blob, bytes):
            raise RuntimeError("segmented-dict segment bounds")
        payload = decompressor.decompress(blob, max_output_size=usize)
        if len(payload) != usize:
            raise RuntimeError("segmented-dict segment length")
        decoded_segments.append(payload)
        piece_maps.append(pieces)

    assembled = [bytearray(int(row[2])) for row in files]
    coverage = [0 for _ in files]
    for payload, pieces in zip(decoded_segments, piece_maps, strict=True):
        cursor = 0
        for piece in pieces:
            if not isinstance(piece, list) or len(piece) != 3:
                raise RuntimeError("bad segmented-dict piece")
            file_idx, offset, length = map(int, piece)
            if file_idx < 0 or file_idx >= len(files) or length < 0 or cursor + length > len(payload):
                raise RuntimeError("segmented-dict piece bounds")
            end = offset + length
            if offset < 0 or end > len(assembled[file_idx]):
                raise RuntimeError("segmented-dict member bounds")
            assembled[file_idx][offset:end] = payload[cursor:cursor + length]
            coverage[file_idx] += length
            cursor += length
        if cursor != len(payload):
            raise RuntimeError("unowned segmented-dict segment bytes")

    dst.mkdir(parents=True, exist_ok=True)
    previous = ""
    seen: set[str] = set()
    for idx, row in enumerate(files):
        prefix, suffix, size, _segment_ids = row
        if not isinstance(prefix, int) or not isinstance(suffix, str) or prefix < 0 or prefix > len(previous):
            raise RuntimeError("bad segmented-dict path delta")
        rel = previous[:prefix] + suffix
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe segmented-dict path")
        if coverage[idx] != int(size):
            raise RuntimeError("segmented-dict member coverage")
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes(assembled[idx]))
        previous = rel
        seen.add(rel)


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = B._tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-segdict-", dir=work) as td:
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
            rows, logical_bytes = BASE._source(stage, variant)
            segments, owners, max_amp, max_unit = BASE._segment(rows)
            pack_source_s = time.perf_counter() - pack_started
            raw_segments = [segment["raw"] for segment in segments]
            logical_files = len(rows)
            variant_stats[variant] = {
                "segments": len(segments),
                "pack_source_s": pack_source_s,
                "max_member_read_amplification": max_amp,
                "max_decode_unit_bytes": max_unit,
            }
            for requested_dict_size in DICT_SIZES:
                dictionary, train_s, train_error = _train(raw_segments, requested_dict_size)
                if dictionary is None:
                    candidates.append({
                        "variant": variant,
                        "requested_dict_bytes": requested_dict_size,
                        "available": False,
                        "reason": train_error,
                        "dictionary_train_s": train_s,
                        "pack_source_s": pack_source_s,
                    })
                    continue
                for level in LEVELS:
                    archive = root / f"{variant}-d{requested_dict_size}-l{level}.bin"
                    result = _write_candidate(rows, segments, owners, archive, variant=variant, level=level,
                                              dictionary=dictionary, train_s=train_s)
                    result["requested_dict_bytes"] = requested_dict_size
                    result["available"] = True
                    result["pack_source_s"] = pack_source_s
                    result["create_s"] = pack_source_s + train_s + float(result["compress_manifest_hash_write_s"])
                    result["max_member_read_amplification"] = max_amp
                    result["max_decode_unit_bytes"] = max_unit
                    extracted = root / f"{variant}-d{requested_dict_size}-l{level}-out"
                    _extract(archive, extracted)
                    B._verify_extracted(extracted, expected_tree, f"segdict-{variant}-d{requested_dict_size}-l{level}")
                    result["tree_verified"] = True
                    result["beats_zip_size"] = result["archive_bytes"] < zip_result["archive_bytes"]
                    result["beats_zstd19_size"] = result["archive_bytes"] < zstd_result["archive_bytes"]
                    result["beats_zip_create"] = result["create_s"] < zip_result["create_s"]
                    result["beats_zstd19_create"] = result["create_s"] < zstd_result["create_s"]
                    result["locality_green"] = max_amp <= BASE.MAX_MEMBER_AMPLIFICATION and max_unit <= BASE.MAX_DECODE_UNIT
                    result["viable"] = result["locality_green"] and all(result[k] for k in (
                        "beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create"
                    ))
                    candidates.append(result)

        measured = [c for c in candidates if c.get("available")]
        viable = [c for c in measured if c["viable"]]
        best = min(viable, key=lambda c: (c["archive_bytes"], c["create_s"], c["dict_bytes"], c["level"])) if viable else None
        closest = min(measured, key=lambda c: (
            max(0, int(c["archive_bytes"]) - int(zstd_result["archive_bytes"])),
            max(0.0, float(c["create_s"]) - float(zip_result["create_s"])),
            c["archive_bytes"], c["create_s"]
        )) if measured else None
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "logical_files": logical_files,
            "logical_bytes": logical_bytes,
            "variant_stats": variant_stats,
            "timing_boundary": "source-scan+segment-plan+dictionary-train+zstd-segments+manifest+sha256+archive-write",
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidates": candidates,
            "viable_candidate": best,
            "closest_candidate": closest,
            "closest_zstd_size_gap_bytes": None if closest is None else max(0, int(closest["archive_bytes"]) - int(zstd_result["archive_bytes"])),
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_segdict_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_segdict_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_segdict_repair")
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
                raise RuntimeError(f"segmented-dict source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            best = row["viable_candidate"]
            print(json.dumps({
                "label": row["label"],
                "viable": None if best is None else [best["variant"], best["dict_bytes"], best["level"], best["archive_bytes"], best["create_s"]],
                "closest_zstd_gap": row["closest_zstd_size_gap_bytes"],
            }, separators=(",", ":")), flush=True)

    viable_rows = [row for row in rows if row["viable_candidate"] is not None]
    measured = [c for row in rows for c in row["candidates"] if c.get("available")]
    return {
        "schema": "cmpct-v030-segmented-dict-oracle-v1",
        "claim_boundary": "research-only; shared dictionary preserves independent locality-bounded segments but is not canonical r25",
        "max_member_read_amplification": BASE.MAX_MEMBER_AMPLIFICATION,
        "max_decode_unit_bytes": BASE.MAX_DECODE_UNIT,
        "levels": list(LEVELS),
        "dictionary_sizes": list(DICT_SIZES),
        "variants": list(VARIANTS),
        "rows": rows,
        "summary": {
            "workloads": len(rows),
            "viable_workloads": len(viable_rows),
            "viable_labels": [row["label"] for row in viable_rows],
            "all_measured_candidates_locality_green": all(c["locality_green"] for c in measured),
            "aggregate_closest_zstd_gap_bytes": sum(int(row["closest_zstd_size_gap_bytes"] or 0) for row in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-segmented-dict-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-segmented-dict.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
