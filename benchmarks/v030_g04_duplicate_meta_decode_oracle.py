"""Exact A/B oracle for eliminating duplicate authenticated G0-G4 metadata decode work.

A healthy canonical CMP25G4 archive stores the same compressed metadata at the primary header and recovery tail.
The shipping reader intentionally authenticates and bounded-decodes both copies. That is conservative but makes
the second zstd+MessagePack decode redundant when the compressed bytes, declared raw size and SHA-256 are identical
to the already-authenticated primary copy.

This oracle does *not* change product bytes or shipping reader semantics. It executes against the isolated canonical
r25 reader graph under the same operation-scoped profile context used by the product, then wraps its decoder for one
``_g04_open`` call at a time with a one-entry cache and proves:

* healthy archives perform one expensive decode instead of two;
* the complete opened semantic state is identical to baseline;
* primary corruption, tail corruption, and tail-authentication corruption all miss the cache and retain the
  baseline recovery result;
* the isolated open/preflight path improves materially under alternating repeated timing.

The candidate remains research-only until the same predicate is integrated canonically and full verify/extract,
recovery, locality, native and Android authorities pass on the exact product fingerprint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

C = PRODUCT.C
R = C.POLICY.R
G04 = R.G04
TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
REPETITIONS = 15
MIN_OPEN_SPEEDUP = 0.10


def _semantic_snapshot(opened: tuple) -> tuple:
    stream, meta, record_start, offsets, tree_sha, recovered = opened
    try:
        return (meta, record_start, tuple(offsets), tree_sha, recovered)
    finally:
        stream.close()


def _baseline_open_with_decode_count(archive: Path) -> tuple[tuple, int]:
    original_decode = R._decode_g04_meta
    count = 0

    def counted(comp: bytes, raw_size: int, expected_sha: bytes, expected_count: int | None):
        nonlocal count
        count += 1
        return original_decode(comp, raw_size, expected_sha, expected_count)

    R._decode_g04_meta = counted
    try:
        with C._revision25_profile_context():
            opened = R._g04_open(archive)
    finally:
        R._decode_g04_meta = original_decode
    return _semantic_snapshot(opened), count


def _candidate_open_with_decode_count(archive: Path) -> tuple[tuple, int]:
    """Model the proposed per-open exact-identity reuse without changing the shipping reader."""
    original_decode = R._decode_g04_meta
    cached_key: tuple[bytes, int, bytes] | None = None
    cached_meta: dict | None = None
    actual_decodes = 0

    def cached_decode(comp: bytes, raw_size: int, expected_sha: bytes, expected_count: int | None):
        nonlocal cached_key, cached_meta, actual_decodes
        key = (comp, int(raw_size), bytes(expected_sha))
        if cached_key == key and cached_meta is not None:
            leaves = cached_meta.get("record_leaf_sha256")
            if expected_count is None or (isinstance(leaves, list) and len(leaves) == expected_count):
                return cached_meta
        actual_decodes += 1
        meta = original_decode(comp, raw_size, expected_sha, expected_count)
        cached_key = key
        cached_meta = meta
        return meta

    R._decode_g04_meta = cached_decode
    try:
        with C._revision25_profile_context():
            opened = R._g04_open(archive)
    finally:
        R._decode_g04_meta = original_decode
    return _semantic_snapshot(opened), actual_decodes


def _copy_and_flip(path: Path, dst: Path, offset: int) -> Path:
    data = bytearray(path.read_bytes())
    if not 0 <= offset < len(data):
        raise RuntimeError(f"corruption offset outside archive: {offset} / {len(data)}")
    data[offset] ^= 0x01
    dst.write_bytes(data)
    return dst


def _layout(archive: Path) -> dict[str, int]:
    data = archive.read_bytes()
    if len(data) < G04.HDR.size + G04.FTR.size:
        raise RuntimeError("candidate archive too short for G0-G4")
    header = G04.HDR.unpack_from(data, 0)
    if header[0] != C.G04_MAGIC:
        raise RuntimeError(f"ML authority no longer emits canonical G0-G4: magic={header[0]!r}")
    primary_mcs = int(header[1])
    footer_offset = len(data) - G04.FTR.size
    footer = G04.FTR.unpack_from(data, footer_offset)
    if footer[0] != C.G04_TAIL:
        raise RuntimeError("canonical G0-G4 recovery footer missing")
    tail_mcs = int(footer[1])
    tail_meta_offset = footer_offset - tail_mcs
    return {
        "primary_meta_offset": G04.HDR.size,
        "primary_meta_bytes": primary_mcs,
        "tail_meta_offset": tail_meta_offset,
        "tail_meta_bytes": tail_mcs,
        "footer_offset": footer_offset,
    }


def _time_open(fn, archive: Path) -> float:
    started = time.perf_counter_ns()
    snapshot, _ = fn(archive)
    if not snapshot:
        raise RuntimeError("reader returned empty semantic snapshot")
    return (time.perf_counter_ns() - started) / 1e9


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    archive = work_root / "ml-v030.cmpct"
    packed = PERF._run_worker(
        "--engine", "v030", "--op", "pack", "--source", str(source), "--archive", str(archive)
    )
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    layout = _layout(archive)

    baseline_snapshot, baseline_decodes = _baseline_open_with_decode_count(archive)
    candidate_snapshot, candidate_decodes = _candidate_open_with_decode_count(archive)
    if baseline_snapshot != candidate_snapshot:
        raise RuntimeError("healthy candidate changed G0-G4 opened semantics")

    # Exercise both physical copies independently. A damaged copy must never inherit trust from the other one.
    primary_bad = _copy_and_flip(
        archive,
        work_root / "primary-corrupt.cmpct",
        layout["primary_meta_offset"] + max(0, layout["primary_meta_bytes"] // 2),
    )
    tail_bad = _copy_and_flip(
        archive,
        work_root / "tail-corrupt.cmpct",
        layout["tail_meta_offset"] + max(0, layout["tail_meta_bytes"] // 2),
    )
    # Flip one byte of the footer metadata SHA field. Struct prefix is magic + two uint64 declarations.
    footer_sha_offset = layout["footer_offset"] + 8 + 8 + 8
    tail_auth_bad = _copy_and_flip(archive, work_root / "tail-auth-corrupt.cmpct", footer_sha_offset)

    corruption_rows = []
    for label, damaged in (
        ("primary_metadata", primary_bad),
        ("tail_metadata", tail_bad),
        ("tail_authentication", tail_auth_bad),
    ):
        base, base_decodes = _baseline_open_with_decode_count(damaged)
        cand, cand_decodes = _candidate_open_with_decode_count(damaged)
        corruption_rows.append(
            {
                "case": label,
                "semantic_identity": base == cand,
                "baseline_decodes": base_decodes,
                "candidate_decodes": cand_decodes,
            }
        )
        if base != cand:
            raise RuntimeError(f"candidate changed recovery semantics under {label} corruption")
        if cand_decodes < base_decodes:
            raise RuntimeError(f"candidate improperly reused trust across {label} corruption")

    baseline_times: list[float] = []
    candidate_times: list[float] = []
    for rep in range(REPETITIONS):
        if rep % 2:
            candidate_times.append(_time_open(_candidate_open_with_decode_count, archive))
            baseline_times.append(_time_open(_baseline_open_with_decode_count, archive))
        else:
            baseline_times.append(_time_open(_baseline_open_with_decode_count, archive))
            candidate_times.append(_time_open(_candidate_open_with_decode_count, archive))

    baseline_median = statistics.median(baseline_times)
    candidate_median = statistics.median(candidate_times)
    ratio = candidate_median / max(baseline_median, 1e-12)
    gates = {
        "archive_bytes_unchanged": hashlib.sha256(archive.read_bytes()).hexdigest() == archive_sha,
        "healthy_semantic_identity": baseline_snapshot == candidate_snapshot,
        "healthy_baseline_decodes_two": baseline_decodes == 2,
        "healthy_candidate_decodes_one": candidate_decodes == 1,
        "corruption_semantics_identical": all(row["semantic_identity"] for row in corruption_rows),
        "corruption_never_reuses_invalid_copy": all(
            row["candidate_decodes"] >= row["baseline_decodes"] for row in corruption_rows
        ),
        "open_speedup_at_least_10pct": ratio <= 1.0 - MIN_OPEN_SPEEDUP,
    }
    gates["passed"] = all(gates.values())
    return {
        "schema": "cmpct-v030-g04-duplicate-meta-decode-oracle-v1",
        "research_only": True,
        "canonical_profile": "CMP25G4",
        "target": list(TARGET),
        "packed": packed,
        "archive_sha256": archive_sha,
        "layout": layout,
        "healthy": {
            "baseline_actual_metadata_decodes": baseline_decodes,
            "candidate_actual_metadata_decodes": candidate_decodes,
        },
        "corruption": corruption_rows,
        "timing": {
            "repetitions": REPETITIONS,
            "baseline_median_open_s": baseline_median,
            "candidate_median_open_s": candidate_median,
            "candidate_to_baseline_ratio": ratio,
            "speedup_fraction": 1.0 - ratio,
            "baseline_s": baseline_times,
            "candidate_s": candidate_times,
        },
        "gates": gates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-open-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-open.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"timing": result["timing"], "gates": result["gates"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit("G0-G4 duplicate metadata decode candidate did not cross the preregistered gate")


if __name__ == "__main__":
    main()
