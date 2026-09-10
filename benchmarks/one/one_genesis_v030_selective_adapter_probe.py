from __future__ import annotations

"""Pre-Genesis probe for the frozen v0.30 selective-read product surface.

This is comparator-preservation work, not v0.30 mechanism development.  It proves only
that the exact frozen v0.30 product can read executor-owned synthetic external inputs
selectively, reconstruct exact member bytes, and export internally coherent access stats.
It never touches the 15 Genesis workloads and performs no comparison or scoring.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.one.one_genesis_gate_executor_preflight import V030_SHA
from benchmarks.one.one_genesis_historical_adapter_probe import (
    _assert_frozen_repo,
    _block_historical_corpus_generators,
    _find_frozen_overlap,
    _import_product,
    _make_transfer_tree,
    _snapshot_tree,
)

MODULE = "experiments/entropygraph_v030_release_product.py"
REQUIRED_STATS = (
    "method",
    "compressed_bytes_touched",
    "uncompressed_bytes_decoded",
    "chunks_touched",
)


def validate_member_stats(*, member_bytes: bytes, archive_bytes: int, stats: Any) -> dict[str, Any]:
    if not isinstance(stats, dict):
        raise RuntimeError("v0.30 selective stats must be an object")
    missing = [field for field in REQUIRED_STATS if field not in stats]
    if missing:
        raise RuntimeError(f"v0.30 selective stats missing fields: {missing}")

    method = stats["method"]
    touched = stats["compressed_bytes_touched"]
    decoded = stats["uncompressed_bytes_decoded"]
    chunks = stats["chunks_touched"]
    if not isinstance(method, str) or not method:
        raise RuntimeError("v0.30 selective method must be a non-empty string")
    for name, value in (("compressed_bytes_touched", touched), ("uncompressed_bytes_decoded", decoded), ("chunks_touched", chunks)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RuntimeError(f"v0.30 selective {name} must be a non-negative integer")
    if len(member_bytes) > 0 and chunks < 1:
        raise RuntimeError("non-empty selective read must touch at least one chunk")
    if len(member_bytes) > 0 and touched < 1:
        raise RuntimeError("non-empty selective read must touch at least one compressed byte")
    if touched > archive_bytes:
        raise RuntimeError("selective compressed bytes touched cannot exceed complete archive bytes")
    if decoded < len(member_bytes):
        raise RuntimeError("selective uncompressed bytes decoded cannot be smaller than returned member bytes")

    return {
        "method": method,
        "compressed_bytes_touched": touched,
        "uncompressed_bytes_decoded": decoded,
        "chunks_touched": chunks,
    }


def probe(*, v030_repo: Path, work_root: Path) -> dict[str, Any]:
    _assert_frozen_repo(v030_repo, V030_SHA)
    overlap = _find_frozen_overlap(work_root)
    if overlap:
        raise RuntimeError(f"probe work root overlaps frozen Genesis identity: {overlap}")

    work_root.mkdir(parents=True, exist_ok=True)
    source = work_root / "external-transfer-tree"
    if source.exists():
        raise RuntimeError(f"refusing to reuse existing probe source tree: {source}")
    _make_transfer_tree(source)
    before = _snapshot_tree(source)

    with _block_historical_corpus_generators(v030_repo):
        product = _import_product(v030_repo, MODULE, "cmpct_genesis_v030_selective_product")
        archive = product.build(source)
        if not isinstance(archive, (bytes, bytearray)):
            raise RuntimeError("v0.30 build did not return archive bytes")
        archive = bytes(archive)
        if not product.strong_verify(archive):
            raise RuntimeError("v0.30 strong_verify rejected its own synthetic transfer archive")

        expected_members = sorted(before)
        listed = list(product.list_members(archive))
        if listed != expected_members:
            raise RuntimeError(f"v0.30 list_members mismatch: expected={expected_members!r} actual={listed!r}")

        rows: list[dict[str, Any]] = []
        for member in expected_members:
            expected = (source / member).read_bytes()
            plain = product.read_member(archive, member)
            with_stats, stats = product.read_member_with_stats(archive, member)
            if bytes(plain) != expected:
                raise RuntimeError(f"v0.30 read_member reconstructed wrong bytes for {member}")
            if bytes(with_stats) != expected:
                raise RuntimeError(f"v0.30 read_member_with_stats reconstructed wrong bytes for {member}")
            normalized = validate_member_stats(member_bytes=expected, archive_bytes=len(archive), stats=stats)
            rows.append({
                "path": member,
                "logical_bytes": len(expected),
                "stats": normalized,
            })

    after = _snapshot_tree(source)
    if after != before:
        raise RuntimeError("frozen v0.30 selective probe mutated executor-owned input tree")

    return {
        "schema": "cmpct-one-genesis-v030-selective-adapter-probe-v1",
        "claim_boundary": "frozen v0.30 selective API exactness and stat-shape on synthetic external input only; not Genesis performance evidence or scoring",
        "frozen_v030_sha": V030_SHA,
        "module": MODULE,
        "synthetic": True,
        "genesis_inputs_used": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
        "archive_bytes": len(archive),
        "members": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v030-repo", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(v030_repo=args.v030_repo, work_root=args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "archive_bytes": result["archive_bytes"],
        "members": len(result["members"]),
        "genesis_inputs_used": result["genesis_inputs_used"],
        "scoring_executed": result["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
