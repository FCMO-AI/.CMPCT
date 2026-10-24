#!/usr/bin/env python3
"""O16: fully charge one genuine CMPCT r24 envelope around exact frozen BDC bytes.

Research oracle ONLY. The r24 archive contains one opaque file, not an exposed
reconstruction of the original source tree. A negative verdict kills only the
naive opaque-envelope external-strict-win route, not direct integration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import tempfile
import time
import traceback
from pathlib import Path

from benchmarks import v031_bounded_drift_coordered_court as FROZEN
from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from cmpct.builder import Builder
from cmpct.reader import CMPCT

FROZEN_RECEIPTS = {
    "01_shifted_versions": {
        "sibling_bytes": 1687989,
        "sibling_sha256": "6f15c582a4c448524f112e5a74d832401004895c30a3e53723684d3d921b2b30",
        "zstd19_bytes": 1694674,
    },
    "03_boundary_churn": {
        "sibling_bytes": 72841,
        "sibling_sha256": "da20e529c5acd391e1ea26ab3101e1d6a1960c8216f5438e998cbc27489c78ae",
        "zstd19_bytes": 73097,
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def court_one(work: Path, name: str) -> dict:
    frozen = FROZEN_RECEIPTS[name]
    source = FROZEN._build_source(work, name)
    tree = HOSTILE.tree_hash(source)
    if tree != FROZEN.TARGETS[name]["tree_sha256"]:
        raise RuntimeError(f"{name}: frozen input tree SHA drift ({tree})")
    start = time.perf_counter()
    cpu0 = time.process_time()
    manifest, regular, _stats = FROZEN._capture(source)
    sibling, _sib_meta = FROZEN._encode_sibling(manifest, regular)
    sib_build_wall = time.perf_counter() - start
    sib_build_cpu = time.process_time() - cpu0
    if len(sibling) != frozen["sibling_bytes"] or digest(sibling) != frozen["sibling_sha256"]:
        raise RuntimeError(f"{name}: frozen physical BDC SHA/length drift")
    _raw, _bdc, recovered_manifest = FROZEN._parse_sibling(sibling)
    if recovered_manifest != manifest:
        raise RuntimeError(f"{name}: BDC decoded manifest drift")

    outer_input = work / "opaque-envelope-input"
    outer_input.mkdir()
    inner_path = outer_input / "coordered-sibling.bin"
    outer_build_start = time.perf_counter()
    outer_cpu_start = time.process_time()
    inner_path.write_bytes(sibling)
    archive = work / "outer-r24.cmpct"
    builder_stats = Builder(outer_input, workers=1, reproducible=False).build(archive)
    outer_build_wall = time.perf_counter() - outer_build_start
    outer_build_cpu = time.process_time() - outer_cpu_start
    outer_bytes = archive.stat().st_size
    outer_sha = digest(archive.read_bytes())
    extracted = work / "outer-verified-extract"
    with CMPCT(archive) as reader:
        verified = reader.verify()
        reader.extractall(extracted, metadata=True)
    restored = (extracted / "coordered-sibling.bin").read_bytes()
    if restored != sibling or digest(restored) != frozen["sibling_sha256"]:
        raise RuntimeError(f"{name}: actual r24 envelope corrupts/replaces inner bytes")
    _raw2, _bdc2, post_manifest = FROZEN._parse_sibling(restored)
    if post_manifest != manifest:
        raise RuntimeError(f"{name}: nested BDC manifest changed across r24 envelope")
    net = outer_bytes - len(sibling)
    margin = frozen["zstd19_bytes"] - outer_bytes
    return {
        "name": name,
        "tree_sha256": tree,
        "sibling_original": {"bytes": len(sibling), "sha256": digest(sibling)},
        "r24_real_opaque_envelope": {
            "archive_bytes": outer_bytes,
            "archive_sha256": outer_sha,
            "net_physical_carry_bytes": net,
            "builder_stats": builder_stats,
            "verified_members": verified,
            "inner_byte_identical": True,
            "decoded_original_manifest_identical": True,
        },
        "pinned_original_zstd19_bytes": frozen["zstd19_bytes"],
        "original_external_slack_bytes": frozen["zstd19_bytes"] - len(sibling),
        "remaining_external_slack_bytes": margin,
        "strict_size_win_vs_pinned_zstd19": margin > 0,
        "timings_single_process_diagnostic_only": {
            "sibling_construct_wall_s": sib_build_wall,
            "sibling_construct_cpu_s": sib_build_cpu,
            "copy_plus_r24_builder_wall_s": outer_build_wall,
            "copy_plus_r24_builder_cpu_s": outer_build_cpu,
            "combined_wall_s": sib_build_wall + outer_build_wall,
            "combined_cpu_s": sib_build_cpu + outer_build_cpu,
        },
        "claim_boundary": "research-only opaque carrier; original filesystem NOT directly exposed by r24",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = {
        "schema": "cmpct-v031-bdc-r24-opaque-envelope-o16-v1",
        "prereg": "docs/v031-research/2026-10-24-bdc-r24-envelope-o16-prereg.md",
        "status": "UNMEASURED",
        "rows": [],
        "product_credit": False,
        "release_credit": False,
        "format_change": False,
        "original_filesystem_exposed_in_r24": False,
    }
    try:
        for name in FROZEN_RECEIPTS:
            with tempfile.TemporaryDirectory(prefix=f"cmpct-bdc-envelope-{name}-") as tmp:
                result["rows"].append(court_one(Path(tmp), name))
        passes = all(row["strict_size_win_vs_pinned_zstd19"] for row in result["rows"])
        result["status"] = "CORRECT_OPAQUE_ENVELOPE"
        result["decision"] = ("OPAQUE_ENVELOPE_PASSES_SIZE_ONLY_RESEARCH_RUNG" if passes
                              else "RETIRE_OPAQUE_ENVELOPE_STRICT_EXTERNAL_WIN_ROUTE")
    except Exception:
        result["status"] = "UNMEASURED_OR_CORRUPT"
        result["error"] = traceback.format_exc()
    result["process_peak_rss_kib_upper_bound"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    if result["status"] != "CORRECT_OPAQUE_ENVELOPE":
        raise SystemExit("O16: cannot decide size without exact physical and semantic custody")


if __name__ == "__main__":
    main()
