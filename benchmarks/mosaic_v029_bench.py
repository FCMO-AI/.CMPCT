from __future__ import annotations

"""Measure bounded multi-root mosaic deltas against an optimistic v0.28-style single-base floor.

This is a **primitive research gate**, not an archive-format or v0.29 release benchmark.  Root storage is
identical on both sides and therefore cancels; the harness compares only the complete stored cost of each
target representation.  The baseline is intentionally stronger than current global central-base policy:
for every target it auditions *every* available direct root and keeps the smallest direct/single-base
representation.

Footnote: a mosaic win here means the additional source dimension contains measurable information.  It
does not yet prove that a full archive writer should promote the representation; that later step must
pay root packing, metadata, recovery, native-reader and direct-base release costs too.
"""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import statistics
import struct
import time

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import delta_decode, delta_encode, similarity_sketch
from mosaic_hostile_corpus_v1 import build as build_corpus

PH_SIZE = struct.calcsize("<BQQI32s")
SINGLE_METADATA = 24
MOSAIC_METADATA_BASE = 24
MOSAIC_METADATA_PER_ROOT = 8
MAX_MOSAIC_BASES = 4
MAX_READ_AMP = 8.0

_zstd = ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so")
_size_t = ctypes.c_size_t
_zstd.ZSTD_compressBound.argtypes = [_size_t]
_zstd.ZSTD_compressBound.restype = _size_t
_zstd.ZSTD_compress.argtypes = [ctypes.c_void_p, _size_t, ctypes.c_void_p, _size_t, ctypes.c_int]
_zstd.ZSTD_compress.restype = _size_t
_zstd.ZSTD_isError.argtypes = [_size_t]
_zstd.ZSTD_isError.restype = ctypes.c_uint


def _zc(data: bytes, level: int = 19) -> bytes:
    if not data:
        return b""
    source = ctypes.create_string_buffer(data)
    capacity = int(_zstd.ZSTD_compressBound(len(data)))
    dest = ctypes.create_string_buffer(capacity)
    size = int(_zstd.ZSTD_compress(dest, capacity, source, len(data), level))
    if _zstd.ZSTD_isError(size):
        raise RuntimeError("zstd compression failed")
    return dest.raw[:size]


def _physical_payload(data: bytes, level: int) -> bytes:
    compressed = _zc(data, level)
    return compressed if len(compressed) + 8 < len(data) else data


def _direct_cost(target: bytes) -> int:
    return PH_SIZE + len(_physical_payload(target, 19))


def _single_cost(base: bytes, target: bytes) -> tuple[int, int, int]:
    result = delta_encode(base, target, block=64, max_base_index=8 * 1024 * 1024)
    assert delta_decode(base, result.payload, expected_size=len(target)) == target
    payload = _physical_payload(result.payload, 12)
    return PH_SIZE + len(payload) + SINGLE_METADATA, result.stats.copied_bytes, len(result.payload)


def _shared_features(a, b) -> int:
    return sum(1 for left, right in zip(a.features, b.features) if left == right and left != 0)


def _rank_roots(roots: list[bytes], target: bytes) -> list[int]:
    """Rank a bounded root pool without treating sketch score as an admission decision."""
    if len(roots) <= MAX_MOSAIC_BASES:
        return list(range(len(roots)))
    target_sketch = similarity_sketch(target)
    rows = []
    for index, root in enumerate(roots):
        sketch = similarity_sketch(root)
        rows.append((-_shared_features(target_sketch, sketch), abs(len(root) - len(target)), index))
    # Footnote: a hostile all-tie population remains deterministic and bounded.  Final encoded bytes,
    # not this ranking, decide whether mosaic storage is selected.
    return [index for _, _, index in sorted(rows)[:MAX_MOSAIC_BASES]]


def _measure_target(roots: list[bytes], target: bytes) -> dict:
    direct = _direct_cost(target)
    single_trials = []
    for root_id, root in enumerate(roots):
        cost, copied, raw_delta = _single_cost(root, target)
        single_trials.append({"root": root_id, "bytes": cost, "copied": copied, "raw_delta": raw_delta})
    best_single = min(single_trials, key=lambda row: (row["bytes"], -row["copied"], row["root"])) if single_trials else None
    floor = min(direct, best_single["bytes"] if best_single else direct)
    floor_kind = "single" if best_single is not None and best_single["bytes"] < direct else "direct"

    ranked = _rank_roots(roots, target)
    mosaic_roots = [roots[index] for index in ranked]
    mosaic = mosaic_delta_encode(
        mosaic_roots,
        target,
        block=64,
        max_bases=MAX_MOSAIC_BASES,
        max_source_index=8 * 1024 * 1024,
        max_matches_per_key=16,
    )
    assert mosaic_delta_decode(
        mosaic_roots,
        mosaic.payload,
        expected_size=len(target),
        max_bases=MAX_MOSAIC_BASES,
        max_source_bytes=8 * 1024 * 1024,
    ) == target
    payload = _physical_payload(mosaic.payload, 12)
    used_slots = used_base_slots(mosaic.stats)
    used_root_ids = [ranked[slot] for slot in used_slots]
    mosaic_cost = (
        PH_SIZE
        + len(payload)
        + MOSAIC_METADATA_BASE
        + MOSAIC_METADATA_PER_ROOT * len(used_root_ids)
    )
    # Every referenced root is charged as an independently decoded node.  This is intentionally more
    # conservative than counting only copied ranges; a future pack-aware writer may prove a lower
    # physical cost, but the primitive does not get that assumption for free.
    decoded_source = sum(len(roots[root_id]) for root_id in used_root_ids)
    read_amp = (decoded_source + len(mosaic.payload)) / max(1, len(target))
    eligible = (
        len(used_root_ids) >= 2
        and read_amp <= MAX_READ_AMP
        and mosaic.stats.copied_bytes >= len(target) // 3
        and mosaic_cost + max(128, floor // 100) < floor
    )
    selected_cost = mosaic_cost if eligible else floor
    return {
        "logical_bytes": len(target),
        "direct_bytes": direct,
        "best_single_bytes": best_single["bytes"] if best_single else None,
        "best_single_root": best_single["root"] if best_single else None,
        "best_single_copied": best_single["copied"] if best_single else 0,
        "v028_optimistic_floor_bytes": floor,
        "floor_kind": floor_kind,
        "mosaic_bytes": mosaic_cost,
        "mosaic_raw_delta_bytes": len(mosaic.payload),
        "mosaic_copied_bytes": mosaic.stats.copied_bytes,
        "mosaic_literal_bytes": mosaic.stats.literal_bytes,
        "mosaic_copy_ops": mosaic.stats.copy_ops,
        "mosaic_used_roots": used_root_ids,
        "mosaic_indexed_source_bytes": mosaic.stats.indexed_source_bytes,
        "mosaic_read_amplification": read_amp,
        "selected": "mosaic" if eligible else f"v028-{floor_kind}-fallback",
        "selected_bytes": selected_cost,
        "saving_vs_floor_bytes": floor - selected_cost,
        "saving_vs_floor_pct": (floor - selected_cost) / floor * 100.0 if floor else 0.0,
        "single_trials": single_trials,
    }


def run(corpus_root: Path) -> dict:
    started = time.perf_counter()
    manifest = build_corpus(corpus_root)
    rows = []
    for workload_meta in manifest["workloads"]:
        path = corpus_root / workload_meta["name"]
        roots = [p.read_bytes() for p in sorted(path.glob("root-*.bin"))]
        targets = sorted(path.glob("target-*.bin"))
        measured = [_measure_target(roots, target.read_bytes()) for target in targets]
        floor = sum(row["v028_optimistic_floor_bytes"] for row in measured)
        selected = sum(row["selected_bytes"] for row in measured)
        rows.append(
            {
                **workload_meta,
                "targets_detail": measured,
                "v028_optimistic_floor_bytes": floor,
                "candidate_bytes": selected,
                "saving_vs_floor_bytes": floor - selected,
                "saving_vs_floor_pct": (floor - selected) / floor * 100.0 if floor else 0.0,
                "mosaic_selected": sum(row["selected"] == "mosaic" for row in measured),
                "max_read_amplification": max((row["mosaic_read_amplification"] for row in measured), default=0.0),
            }
        )

    floor_total = sum(row["v028_optimistic_floor_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    selected_count = sum(row["mosaic_selected"] for row in rows)
    target_count = sum(row["targets"] for row in rows)
    improved_workloads = sum(row["candidate_bytes"] < row["v028_optimistic_floor_bytes"] for row in rows)
    regressed_workloads = sum(row["candidate_bytes"] > row["v028_optimistic_floor_bytes"] for row in rows)
    max_amp = max((row["max_read_amplification"] for row in rows), default=0.0)
    return {
        "schema": "cmpct-mosaic-v029-primitive-v1",
        "claim_boundary": "multi-root target representation only; root storage cancels and canonical r24 is unchanged",
        "corpus": manifest,
        "rows": rows,
        "totals": {
            "targets": target_count,
            "v028_optimistic_floor_bytes": floor_total,
            "candidate_bytes": candidate_total,
            "smaller_than_floor_pct": (floor_total - candidate_total) / floor_total * 100.0 if floor_total else 0.0,
            "mosaic_selected": selected_count,
            "workloads_improved": improved_workloads,
            "workloads_regressed": regressed_workloads,
            "max_read_amplification": max_amp,
            "elapsed_s": time.perf_counter() - started,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", type=Path, default=Path("CMPCT_Mosaic_Hostile_v1"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.corpus_root)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
