from __future__ import annotations

"""Optimistic byte floors for the encrypted-like C25 locality-safe family.

The first floor gives semantic co-location every byte advantage a real grammar cannot: local
semantic payloads pay zero framing/authentication/descriptor bytes and their pack id is free
through physical co-location. The mirrored global root retains only non-S_PACK file rows.

The second, even more optimistic floor also deletes every existing 64-byte r24 blob-record
header while leaving payload bytes unchanged. This is intentionally impossible as a shipping
format because those headers currently carry codec, sizes and SHA-256 salvage identity. Its
purpose is disproof: if even zero-cost semantics plus zero blob headers still lose Zstd-19,
header compaction cannot be the next architecture; compressed payload bytes themselves must fall.
"""

import argparse
import json
import os
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_distributed_file_table_oracle as DISTR
from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRATEGY
from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

STRATEGY_NAME = "descending_greedy"


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    target_name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)

    candidate = work_root / "cmpct" / "locality-safe-r24.cmpct"
    row = STRATEGY._build(source, candidate, STRATEGY_NAME)
    if not row.get("eligible"):
        raise RuntimeError("locality-safe strategy unexpectedly ineligible")

    index, _data, physical = PROFILE._source_r24_parts(candidate)
    compact = CONTROL._compact_index(index)
    residual, groups = DISTR._split_file_rows(compact)
    if DISTR._restore_file_rows(len(compact["f"]), residual, groups) != compact["f"]:
        raise RuntimeError("co-located semantic floor lost exact file-row reconstruction")

    local_payloads = []
    for pack_index in sorted(groups):
        comp, raw_bytes, level = DISTR._compress(groups[pack_index])
        local_payloads.append({
            "pack_index": int(pack_index),
            "rows": len(groups[pack_index]),
            "raw_bytes": int(raw_bytes),
            "compressed_bytes": len(comp),
            "compression_level": int(level),
        })

    optimistic_root = dict(compact)
    optimistic_root["f"] = residual
    root_envelope = {"x": list(index["features"]), "c": optimistic_root}
    root_comp, root_raw_bytes, root_level = DISTR._compress(root_envelope)

    physical_data_bytes = int(physical["data_bytes"])
    fixed_header_footer_bytes = int(R24.HDR.size + R24.FTR.size)
    local_semantic_bytes = sum(int(x["compressed_bytes"]) for x in local_payloads)
    optimistic_bytes = physical_data_bytes + fixed_header_footer_bytes + local_semantic_bytes + 2 * len(root_comp)

    blobs = index.get("blobs")
    if not isinstance(blobs, list) or not blobs:
        raise RuntimeError("locality-safe source has no physical blob table")
    blob_record_count = len(blobs)
    blob_header_bytes = int(R24.BHDR.size) * blob_record_count
    if blob_header_bytes > physical_data_bytes:
        raise RuntimeError("blob-header accounting exceeds physical data span")
    zero_blob_header_floor = optimistic_bytes - blob_header_bytes

    baseline_raw = msgpack.packb({"x": list(index["features"]), "c": compact}, use_bin_type=True)
    _baseline_level, baseline_comp = PROFILE._compress_control(baseline_raw)
    baseline_bytes = physical_data_bytes + fixed_header_footer_bytes + 2 * len(baseline_comp)
    if baseline_bytes != int(row["wrapped_bytes"]):
        raise RuntimeError("baseline accounting drift")

    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    zstd = EXT._tar_zstd(source, work_root / "competitor.tar.zst", work_root / "zstd-out", zstd_work)
    zstd_bytes = int(zstd["archive_bytes"])
    required_physical_shrink = max(0, optimistic_bytes - (zstd_bytes - 1))
    required_payload_shrink_after_zero_headers = max(0, zero_blob_header_floor - (zstd_bytes - 1))

    return {
        "schema": "cmpct-v030-c25cc01-colocated-semantic-floor-v2",
        "candidate_head": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "target": target_name,
        "strategy": STRATEGY_NAME,
        "tree_sha256": row["tree_sha256"],
        "locality": row["locality"],
        "exact_compact_file_row_reconstruction": True,
        "baseline": {
            "wrapped_bytes": baseline_bytes,
            "physical_data_bytes": physical_data_bytes,
            "fixed_header_footer_bytes": fixed_header_footer_bytes,
            "control_bytes_per_copy": len(baseline_comp),
            "blob_record_count": blob_record_count,
            "blob_header_bytes_each": int(R24.BHDR.size),
            "all_blob_header_bytes": blob_header_bytes,
        },
        "optimistic_colocated_floor": {
            "pack_tables": len(local_payloads),
            "moved_pack_rows": sum(int(x["rows"]) for x in local_payloads),
            "residual_global_rows": len(residual),
            "local_semantic_compressed_bytes": local_semantic_bytes,
            "local_framing_bytes_charged": 0,
            "local_descriptor_bytes_charged": 0,
            "mirrored_residual_root_raw_bytes_per_copy": root_raw_bytes,
            "mirrored_residual_root_bytes_per_copy": len(root_comp),
            "mirrored_residual_root_level": root_level,
            "projected_total_bytes": optimistic_bytes,
        },
        "impossible_zero_blob_header_floor": {
            "blob_headers_charged_bytes": 0,
            "blob_header_bytes_removed": blob_header_bytes,
            "projected_total_bytes": zero_blob_header_floor,
            "margin_below_zstd19_bytes": zstd_bytes - zero_blob_header_floor,
            "minimum_additional_payload_shrink_for_strict_zstd_win_bytes": required_payload_shrink_after_zero_headers,
        },
        "zstd19_bytes": zstd_bytes,
        "optimistic_margin_below_zstd19_bytes": zstd_bytes - optimistic_bytes,
        "minimum_additional_physical_shrink_for_strict_zstd_win_bytes": required_physical_shrink,
        "gate": {
            "exact_baseline_accounting": baseline_bytes == int(row["wrapped_bytes"]),
            "exact_file_semantic_reconstruction": True,
            "current_locality_within_8x": float(row["locality"]["max_member_read_amplification"]) <= 8.0,
            "optimistic_metadata_relocation_alone_can_beat_zstd19": optimistic_bytes < zstd_bytes,
            "impossible_zero_blob_headers_can_beat_zstd19": zero_blob_header_floor < zstd_bytes,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Research-only optimistic lower bounds. Local semantic framing/authentication/discovery/descriptors are "
            "priced at zero. The second floor additionally prices every existing r24 blob header at zero even though "
            "shipping recovery requires self-description and authentication. Positive shrink requirements therefore "
            "prove what the next grammar must save beyond metadata/header relocation; no reader, recovery, selector "
            "or release credit is implied."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-colocated-floor-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-colocated-floor.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("co-located semantic floor oracle invalid")


if __name__ == "__main__":
    main()
