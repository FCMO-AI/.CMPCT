#!/usr/bin/env python3
"""Read-only stronger control: canonical r24 versus exact frozen BDC sibling on identical trees.

Research evidence only: this is NOT a CMPCT product benchmark or promotion gate.
Source, tree, independent sibling receipt, complete bytes, and filesystem
semantics are checked before claiming any difference.
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

# Exact hosted physical receipts: frozen run 39925132930 / artifact 12489775120.
FROZEN_RECEIPT = {
    "01_shifted_versions": (1687989, "6f15c582a4c448524f112e5a74d832401004895c30a3e53723684d3d921b2b30"),
    "03_boundary_churn": (72841, "da20e529c5acd391e1ea26ab3101e1d6a1960c8216f5438e998cbc27489c78ae"),
}


def court_one(root: Path, name: str) -> dict:
    expected = FROZEN.TARGETS[name]
    source = FROZEN._build_source(root, name)
    tree_before = HOSTILE.tree_hash(source)
    if tree_before != expected["tree_sha256"]:
        raise RuntimeError("frozen source tree identity changed: " + name)
    manifest, regular, manifest_stats = FROZEN._capture(source)
    sibling, sibling_info = FROZEN._encode_sibling(manifest, regular)
    size, digest = FROZEN_RECEIPT[name]
    if len(sibling) != size or hashlib.sha256(sibling).hexdigest() != digest:
        raise RuntimeError("frozen source-independent sibling receipt not reproducible: " + name)
    _control, _blob, restored_manifest = FROZEN._parse_sibling(sibling)
    if restored_manifest != manifest:
        raise RuntimeError("frozen sibling manifest not equal to source manifest")

    candidate = root / "canonical-r24.cmpct"
    wall0 = time.perf_counter()
    cpu0 = time.process_time()
    build_stats = Builder(source, workers=1, reproducible=False).build(candidate)
    create_cpu = time.process_time() - cpu0
    create_wall = time.perf_counter() - wall0
    canonical_bytes = candidate.stat().st_size
    canonical_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    restored = root / "canonical-extracted"
    with CMPCT(candidate) as reader:
        verified_files = reader.verify()
        reader.extractall(restored, metadata=True)
    tree_after = HOSTILE.tree_hash(restored)
    final_manifest, _regular, _stats = FROZEN._capture(restored)
    equal_manifest = final_manifest == manifest
    equal_tree = tree_after == tree_before
    return {
        "name": name,
        "original_tree_sha256": tree_before,
        "restored_tree_sha256": tree_after,
        "exact_tree": equal_tree,
        "exact_filesystem_manifest": equal_manifest,
        "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "restored_manifest_sha256": hashlib.sha256(final_manifest).hexdigest(),
        "canonical_r24": {
            "archive_bytes": canonical_bytes,
            "physical_sha256": canonical_sha,
            "create_wall_s": create_wall,
            "create_cpu_s": create_cpu,
            "verified_files": verified_files,
            "build_stats": build_stats,
        },
        "noncanonical_bdc": {"archive_bytes": len(sibling), "physical_sha256": digest, "receipt_match": True},
        "pinned_zstd19_bytes": expected["historical_zstd19_bytes"],
        "canonical_minus_sibling_bytes": canonical_bytes - len(sibling),
        "sibling_external_margin_bytes": expected["historical_zstd19_bytes"] - len(sibling),
        "strict_sibling_size_win_vs_canonical": len(sibling) < canonical_bytes,
        "metadata_source_stats": manifest_stats,
        "claim_boundary": "research-only canonical r24 stronger control; BDC sibling is not integrated or a shipping grammar",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = {
        "schema": "cmpct-v031-bdc-canonical-control-v1",
        "frozen_scientific_run": 39925132930,
        "frozen_scientific_artifact": 12489775120,
        "baseline": "canonical r24 Builder + CMPCT Reader from frozen BDC owner source",
        "status": "INCOMPLETE",
        "rows": [],
        "product_credit": False,
        "release_credit": False,
    }
    try:
        for name in FROZEN.TARGETS:
            with tempfile.TemporaryDirectory(prefix="bd-canonical-" + name + "-") as td:
                result["rows"].append(court_one(Path(td), name))
        good = all(r["exact_tree"] and r["exact_filesystem_manifest"] for r in result["rows"])
        result["status"] = "CONTROL_EQUIVALENT" if good else "CONTROL_SEMANTICS_MISMATCH"
    except Exception:
        result["status"] = "UNMEASURED_OR_INCOMPLETE"
        result["error"] = traceback.format_exc()
    result["process_peak_rss_kib_upper_bound"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    if result["status"] != "CONTROL_EQUIVALENT":
        raise SystemExit("canonical control not proven semantically equivalent; size comparisons not promotable")


if __name__ == "__main__":
    main()
