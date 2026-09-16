from __future__ import annotations

"""R4 capacity/payload floor for segmented relation-aware Shifted ownership.

The retired one-anchor joint edit stream proved that preserving long compression context is
useful but one global semantic decode unit cannot satisfy the <=8 MiB / <=8x laws.  This
oracle changes the ownership model rather than tuning that family: members are grouped by
exact content-relation cost around structurally chosen anchors, each group is independently
bounded by the release decode/locality laws, and each exact group transform is compressed
once at Zstd-19.

This is deliberately a necessary-condition oracle, not a product artifact.  It charges all
pairwise relation discovery, grouping, exact edit construction and payload compression to
creation time, but does not pretend projected framing is free.  If compressed payload alone
cannot beat the strict size floors, the family is terminal.  If it can, the next prerequisite
is a real framed reader/writer candidate with all framing and timing charged.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_shifted_joint_patch_stream_oracle as JOINT
from experiments import entropygraph_v030_authoritative as CMPCT

MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_LOCALITY = 8.0
LEVEL = 19


def _digest(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _segment_rows(rows: list[tuple[str, bytes]]) -> tuple[list[list[int]], dict]:
    remaining = set(range(len(rows)))
    segments: list[list[int]] = []
    pair_patch_bytes = 0
    pair_evaluations = 0

    while remaining:
        ordered_remaining = sorted(remaining)
        local = [rows[i] for i in ordered_remaining]
        local_anchor = JOINT._anchor(local)
        anchor_index = ordered_remaining[local_anchor]
        anchor = rows[anchor_index][1]

        candidates: list[tuple[float, int, bytes, int]] = []
        for idx in ordered_remaining:
            if idx == anchor_index:
                continue
            patch = JOINT._patch(anchor, rows[idx][1])
            pair_evaluations += 1
            pair_patch_bytes += len(patch)
            candidates.append((len(patch) / max(1, len(rows[idx][1])), len(patch), _digest(rows[idx][1]), idx))
        candidates.sort()

        chosen = [anchor_index]
        singleton, _stats = JOINT._transform([rows[anchor_index]], 0)
        singleton_limit = min(MAX_DECODE_UNIT, int(MAX_LOCALITY * max(1, len(anchor))))
        if len(singleton) > singleton_limit:
            # A member that cannot fit as its own semantic unit needs intra-member chunking,
            # which is a different representation family.
            return [], {
                "pair_evaluations": pair_evaluations,
                "pair_patch_bytes": pair_patch_bytes,
                "terminal_member_index": anchor_index,
                "terminal_singleton_bytes": len(singleton),
                "terminal_singleton_limit": singleton_limit,
            }

        for _ratio, _patch_len, _digest_key, idx in candidates:
            trial_indices = chosen + [idx]
            trial_rows = [rows[i] for i in trial_indices]
            transform, _ = JOINT._transform(trial_rows, 0)
            min_member = min(len(raw) for _name, raw in trial_rows)
            limit = min(MAX_DECODE_UNIT, int(MAX_LOCALITY * max(1, min_member)))
            if len(transform) <= limit:
                chosen.append(idx)

        for idx in chosen:
            remaining.remove(idx)
        segments.append(chosen)

    return segments, {
        "pair_evaluations": pair_evaluations,
        "pair_patch_bytes": pair_patch_bytes,
    }


def run(work_root: Path) -> dict:
    started = time.perf_counter()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    HOSTILE.shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = HOSTILE.tree_hash(source)
    accepted = GENERAL._accepted_v029_rows()[("resemblance_hostile_v1", "01_shifted_versions")]
    if expected_tree != accepted["tree_sha256"]:
        raise RuntimeError("Shifted corpus tree drift")

    normalized_parent = work_root / "normalized"
    normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")

    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zw = work_root / "solid-zstd-work"
    zw.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zw)
    if not zstd_result.get("available"):
        raise RuntimeError("solid Zstd-19 comparator unavailable")

    rows = [(p.relative_to(stage).as_posix(), p.read_bytes()) for p in JOINT._files(stage)]
    segments, relation_stats = _segment_rows(rows)
    if not segments:
        return {
            "schema": "cmpct-v030-shifted-segmented-relation-payload-floor-v1",
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "target": "resemblance_hostile_v1/01_shifted_versions",
            "contract": {
                "benchmark_identity_used_in_representation": False,
                "research_only": True,
                "release_credit": False,
                "framing_not_claimed": True,
                "relation_discovery_inside_create_time": True,
            },
            "representation_admissible": False,
            "relation_stats": relation_stats,
            "create_s": time.perf_counter() - started,
            "domination_audit": {
                "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
                "diagnosis": "D4",
                "radicality": "R4",
                "saturation_triggers": ["S1", "S2", "S3", "S4"],
                "research_priority_score": 99,
                "pre_mortem": "Segmenting the one-anchor transform may still fail if even one member cannot form a lawful semantic decode unit.",
                "builder": "Partition by exact content-relation cost while enforcing the release decode-unit and locality laws before compression.",
                "hostile_review": "No compressor or framing trick can repair an intrinsically oversized singleton semantic unit under this ownership model.",
                "measured_gap_change_bytes": None,
                "terminal_decision": "RETIRE_FAMILY",
                "next_decisive_test": "Escalate to intra-member relation/chunk ownership rather than retrying segment parameters.",
            },
        }

    segment_rows = []
    payload_total = 0
    raw_transform_total = 0
    for ordinal, indices in enumerate(segments):
        selected = [rows[i] for i in indices]
        transform, stats = JOINT._transform(selected, 0)
        min_member = min(len(raw) for _name, raw in selected)
        locality = len(transform) / max(1, min_member)
        if len(transform) > MAX_DECODE_UNIT or locality > MAX_LOCALITY:
            raise RuntimeError("segmentation admitted an unlawful semantic unit")
        segment_work = work_root / f"segment-{ordinal:03d}"
        segment_work.mkdir()
        blob = JOINT._zstd_blob(shutil.which("zstd") or "", transform, LEVEL, segment_work)
        payload_total += len(blob)
        raw_transform_total += len(transform)
        segment_rows.append({
            "ordinal": ordinal,
            "member_count": len(indices),
            "member_indices": indices,
            "anchor_member_index": indices[0],
            "transform_raw_bytes": len(transform),
            "zstd19_payload_bytes": len(blob),
            "max_locality_amplification": locality,
            "decode_unit_le_8mib": len(transform) <= MAX_DECODE_UNIT,
            "locality_le_8x": locality <= MAX_LOCALITY,
            **stats,
        })

    accepted_bytes = int(accepted["accepted_v029_bytes"])
    zip_bytes = int(zip_result["archive_bytes"])
    zstd_bytes = int(zstd_result["archive_bytes"])
    payload_feasible = payload_total < min(accepted_bytes, zip_bytes, zstd_bytes)
    elapsed = time.perf_counter() - started
    decision = "PROMOTE_NEXT_PREREQUISITE" if payload_feasible else "RETIRE_FAMILY"

    return {
        "schema": "cmpct-v030-shifted-segmented-relation-payload-floor-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "tree_sha256": expected_tree,
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "research_only": True,
            "release_credit": False,
            "framing_not_claimed": True,
            "relation_discovery_inside_create_time": True,
            "grouping_uses_content_relation_only": True,
            "payload_floor_is_necessary_not_sufficient": True,
        },
        "representation_admissible": True,
        "member_count": len(rows),
        "segment_count": len(segments),
        "segments": segment_rows,
        "relation_stats": relation_stats,
        "raw_transform_total_bytes": raw_transform_total,
        "compressed_payload_total_bytes": payload_total,
        "accepted_v029_bytes": accepted_bytes,
        "zip_bytes": zip_bytes,
        "solid_zstd19_bytes": zstd_bytes,
        "payload_beats_v029": payload_total < accepted_bytes,
        "payload_beats_zip": payload_total < zip_bytes,
        "payload_beats_zstd19": payload_total < zstd_bytes,
        "payload_capacity_positive": payload_feasible,
        "create_s_including_comparators": elapsed,
        "comparators": {"zip_deflate9": zip_result, "tar_zstd19_solid": zstd_result},
        "release_credit": False,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "saturation_triggers": ["S1", "S2", "S3", "S4"],
            "research_priority_score": 99,
            "pre_mortem": (
                "Segmentation can cure the one-unit locality/decode violation yet still leave so much transformed payload "
                "that complete framing can never cross the accepted-v0.29 or solid-Zstd floor."
            ),
            "builder": (
                "Use exact bounded edit cost to group members around structural anchors, enforce <=8 MiB and <=8x per "
                "semantic unit, then compress every exact unit once at Zstd-19 with discovery inside timing."
            ),
            "hostile_review": (
                "Compressed payload is only a necessary size floor: paths, ownership tables, hashes, framing, reader, "
                "recovery and publication remain unpriced, and this run cannot claim a strict creation-time win."
            ),
            "measured_gap_change_bytes": zstd_bytes - payload_total,
            "terminal_decision": decision,
            "next_decisive_test": (
                "If payload-positive, build one exact framed segmented reader/writer and price all metadata, hashing, "
                "verification and publication in a single-pass ZIP/Zstd A/B; otherwise retire segmented edit ownership."
            ),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = {
        "representation_admissible": result["representation_admissible"],
        "segment_count": result.get("segment_count"),
        "compressed_payload_total_bytes": result.get("compressed_payload_total_bytes"),
        "solid_zstd19_bytes": result.get("solid_zstd19_bytes"),
        "payload_capacity_positive": result.get("payload_capacity_positive", False),
        "terminal_decision": result["domination_audit"]["terminal_decision"],
    }
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
