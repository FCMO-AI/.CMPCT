from __future__ import annotations

"""Exact capacity floor for the Shifted one-anchor joint edit-stream family.

This is deliberately cheaper than the full compression oracle.  It constructs the exact
structural anchor + edit transform once, charges the complete transform bytes, and decides
whether the family can even satisfy the <=8 MiB decode-unit and <=8x locality laws.  A
capacity failure is terminal for this one-joint-unit representation and must be preserved
as negative evidence rather than retried as a compression-level sweep.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_shifted_joint_patch_stream_oracle as JOINT
from experiments import entropygraph_v030_authoritative as CMPCT


def run(work_root: Path) -> dict:
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

    rows = [(p.relative_to(stage).as_posix(), p.read_bytes()) for p in JOINT._files(stage)]
    anchor_i = JOINT._anchor(rows)
    transform, stats = JOINT._transform(rows, anchor_i)
    min_member = min(len(raw) for _, raw in rows)
    decode_unit_bytes = len(transform)
    locality = decode_unit_bytes / max(1, min_member)
    decode_ok = decode_unit_bytes <= JOINT.MAX_DECODE_UNIT
    locality_ok = locality <= JOINT.MAX_LOCALITY
    admissible = decode_ok and locality_ok

    return {
        "schema": "cmpct-v030-shifted-joint-edit-capacity-floor-v1",
        "source_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "target": "resemblance_hostile_v1/01_shifted_versions",
        "tree_sha256": expected_tree,
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "research_only": True,
            "release_credit": False,
            "exact_transform_constructed_once": True,
            "compression_level_sweep_skipped_when_capacity_impossible": True,
        },
        "anchor_index": anchor_i,
        "member_count": len(rows),
        **stats,
        "decode_unit_bytes": decode_unit_bytes,
        "decode_unit_limit_bytes": JOINT.MAX_DECODE_UNIT,
        "decode_unit_excess_bytes": max(0, decode_unit_bytes - JOINT.MAX_DECODE_UNIT),
        "max_locality_amplification": locality,
        "max_locality_limit": JOINT.MAX_LOCALITY,
        "decode_unit_le_8mib": decode_ok,
        "locality_le_8x": locality_ok,
        "representation_admissible": admissible,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "saturation_triggers": ["S2", "S3", "S4"],
            "research_priority_score": 98,
            "pre_mortem": "A single joint edit stream may preserve compression context yet still exceed the fixed decode-unit or locality law before compression can matter.",
            "builder": "Construct the exact structurally selected anchor plus every exact edit program once and measure the uncompressed semantic decode unit.",
            "hostile_review": "Compression cannot rescue an oversized semantic decode unit because the reader must reconstruct the whole transform under this representation; splitting it would be a different ownership family and needs a new oracle.",
            "measured_gap_change_bytes": JOINT.MAX_DECODE_UNIT - decode_unit_bytes,
            "terminal_decision": "PROMOTE_NEXT_PREREQUISITE" if admissible else "RETIRE_FAMILY",
            "next_decisive_test": (
                "Run the full joint compression oracle only if capacity-admissible; otherwise test a genuinely segmented relation-aware ownership representation rather than another compression-level sweep."
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
    print(json.dumps({
        "decode_unit_bytes": result["decode_unit_bytes"],
        "decode_unit_excess_bytes": result["decode_unit_excess_bytes"],
        "max_locality_amplification": result["max_locality_amplification"],
        "representation_admissible": result["representation_admissible"],
        "terminal_decision": result["domination_audit"]["terminal_decision"],
    }, indent=2))


if __name__ == "__main__":
    main()
