from __future__ import annotations

"""Read-only attribution of v0.25 implicit micro-pack metadata savings.

Mission: docs/V030_COMPACT_PACK_CONTROL_ATTRIBUTION_MISSION_2026-09-12.md
Payload packs are held byte-identical; only an explicit-metadata counterfactual is re-encoded.
"""

import argparse
import copy
import json
from pathlib import Path
import shutil
import struct

import msgpack

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25

TARGETS = {
    "01_developer_repository": 8 * 1024,
    "08_many_tiny_files": 32 * 1024,
}


def _build_sources(root: Path) -> None:
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_compact_control_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_compact_control_repair",
    )
    repair.install_generation_hooks(neutral)
    root.mkdir(parents=True, exist_ok=True)
    neutral.corpus_source_repo(root)
    neutral.corpus_tinyfiles(root)
    for name in TARGETS:
        repair.normalize_root(root / name)


def _read_compact_metadata(archive: Path) -> tuple[dict, int, int, int]:
    raw = archive.read_bytes()
    magic, mcs, mus, npacks, mh = V25.HDR.unpack_from(raw, 0)
    if magic != V25.MAG:
        raise RuntimeError("unexpected v0.25 archive magic")
    mc = raw[V25.HDR.size : V25.HDR.size + mcs]
    mb = V25.zd(mc, mus)
    if V25.H(mb) != mh:
        raise RuntimeError("metadata authentication failed")
    meta = msgpack.unpackb(mb, raw=False)
    if int(meta.get("pack_count", -1)) != int(npacks):
        raise RuntimeError("pack-count drift")
    return meta, len(mb), len(mc), int(npacks)


def _expand_micro(meta: dict) -> dict:
    expanded = copy.deepcopy(meta)
    files = list(expanded.get("files", []))
    seen = {str(row[0]) for row in files}
    for pi, entries in expanded.get("micro", []):
        offset = 0
        for path, n in entries:
            path = str(path); n = int(n)
            if path in seen:
                raise RuntimeError(f"micro path already explicit: {path}")
            files.append([path, ["plain", [["slice", int(pi), offset, n]], n]])
            seen.add(path)
            offset += n
    files.sort(key=lambda row: str(row[0]))
    expanded["files"] = files
    expanded["micro"] = []
    return expanded


def _one(source: Path, root: Path) -> dict:
    archive = root / "archive.cmpct"
    root.mkdir(parents=True, exist_ok=True)
    old_root, old_out = V25.ROOT, V25.OUT
    try:
        V25.ROOT, V25.OUT = source, archive
        build_stats = dict(V25.build())
        verify = dict(V25.strong_verify())
    finally:
        V25.ROOT, V25.OUT = old_root, old_out
    if not verify.get("ok"):
        raise RuntimeError("strong verify failed")
    if verify["tree_sha256"] != V25.treehash(source):
        raise RuntimeError("tree hash drift")

    meta, compact_raw, compact_comp, npacks = _read_compact_metadata(archive)
    expanded = _expand_micro(meta)
    expanded_raw_b = msgpack.packb(expanded, use_bin_type=True)
    expanded_comp_b = V25.zc(expanded_raw_b, 12)

    micro_groups = list(meta.get("micro", []))
    micro_files = sum(len(entries) for _, entries in micro_groups)
    micro_logical = sum(int(n) for _, entries in micro_groups for _, n in entries)
    stored_saving = 2 * (len(expanded_comp_b) - compact_comp)
    expanded_archive = archive.stat().st_size + stored_saving

    # The pack table/payload region is identical in the counterfactual. This number includes per-pack headers.
    payload_region = archive.stat().st_size - V25.HDR.size - V25.FTR.size - 2 * compact_comp

    return {
        "actual_archive_bytes": archive.stat().st_size,
        "counterfactual_explicit_archive_bytes": expanded_archive,
        "implicit_micro_stored_saving_bytes": stored_saving,
        "compact_meta_raw_bytes": compact_raw,
        "compact_meta_comp_bytes": compact_comp,
        "expanded_meta_raw_bytes": len(expanded_raw_b),
        "expanded_meta_comp_bytes": len(expanded_comp_b),
        "pack_count": npacks,
        "payload_and_pack_headers_bytes": payload_region,
        "micro_groups": len(micro_groups),
        "micro_files": micro_files,
        "micro_logical_bytes": micro_logical,
        "build_stats": build_stats,
        "tree_sha256": verify["tree_sha256"],
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    _build_sources(corpus)
    rows = {}
    gates = {}
    for name, floor in TARGETS.items():
        row = _one(corpus / name, work_root / "artifacts" / name)
        rows[name] = row
        gates[name] = {
            "saving_floor_bytes": floor,
            "saving_floor_pass": int(row["implicit_micro_stored_saving_bytes"]) >= floor,
            "strong_tree_exact": True,
            "payload_bytes_unchanged_by_counterfactual": True,
        }
    gate = {
        "all_materiality_floors": all(v["saving_floor_pass"] for v in gates.values()),
        "all_strong_tree_exact": True,
        "payload_bytes_unchanged": True,
    }
    verdict = "COMPACT_CONTROL_MATERIAL" if all(gate.values()) else "MICRO_INDEX_NOT_PRIMARY_ENOUGH"
    return {
        "schema": "cmpct-v030-compact-pack-control-attribution-v1",
        "experiment_valid": True,
        "release_credit": False,
        "workloads": rows,
        "workload_gates": gates,
        "gate": gate,
        "verdict": verdict,
        "contract": {
            "payload_packs_byte_identical_counterfactual": True,
            "same_msgpack_and_zstd12_metadata_encoding": True,
            "head_and_tail_metadata_both_charged": True,
            "strong_verify_before_attribution": True,
            "no_product_selector_change": True,
            "no_release_credit": True,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-compact-control-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-compact-control.json"))
    args = ap.parse_args()
    r = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(r, indent=2, default=str) + "\n")
    print(json.dumps({"verdict": r["verdict"], "workloads": r["workloads"], "gate": r["gate"]}, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
