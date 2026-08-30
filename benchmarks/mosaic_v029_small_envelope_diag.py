from __future__ import annotations

"""Diagnose why the valid 2 KiB multi-root mosaic loses as a complete research artifact.

This is a causal probe, not an acceptance benchmark. It builds the exact small-metadata workload under
three independently useful envelopes:

- inherited EntropyGraph v0.25 / CMPNX5;
- raw EntropyGraph II v0.28 graph / CMPNX8;
- Mosaic Placement Compiler attempt #4 / CMPNX10.

It separates fixed framing, duplicated compressed metadata, and physical-record bytes. Besides the existing
compact-metadata oracle it now computes exact lower bounds for the entire metadata-only optimization family.
Those lower bounds are deliberately more optimistic than a shippable recovery design: they include a zero-
metadata floor and a compact single-copy floor. If even those lose, metadata-only work is terminal and the
next design must also reduce record/framing bytes.
"""

import argparse
import importlib.util
import json
import msgpack
from pathlib import Path
import shutil
import sys

from mosaic_stress_corpus_v2 import small_metadata_control

ROOT = Path(__file__).resolve().parents[1]
V028_PATH = ROOT / "experiments" / "entropygraph_v028.py"
PLACEMENT_PATH = ROOT / "experiments" / "entropygraph_v029_mosaic_strict.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V028 = _load(V028_PATH, "cmpct_small_envelope_v028")
PLACEMENT = _load(PLACEMENT_PATH, "cmpct_small_envelope_placement")
V025 = V028.BASE


def _parse(path: Path, module) -> dict:
    raw = path.read_bytes()
    magic = raw[:8]
    if magic != module.MAG:
        raise RuntimeError(f"unexpected magic {magic!r} for {path.name}")
    header = module.HDR.unpack(raw[: module.HDR.size])
    mcs = int(header[1]); mus = int(header[2]); count = int(header[3])
    meta_start = module.HDR.size
    meta_comp = raw[meta_start : meta_start + mcs]
    meta_raw = module.zd(meta_comp, mus)
    meta = msgpack.unpackb(meta_raw, raw=False, strict_map_key=False)
    cursor = meta_start + mcs
    record_payload_bytes = 0
    record_header_bytes = 0
    record_rows = []
    for record_id in range(count):
        ph = module.PH.unpack(raw[cursor : cursor + module.PH.size])
        csize = int(ph[2])
        record_rows.append({"record_id": record_id, "codec": int(ph[0]), "logical_bytes": int(ph[1]), "stored_payload_bytes": csize})
        cursor += module.PH.size + csize
        record_header_bytes += module.PH.size
        record_payload_bytes += csize
    tail_meta_start = len(raw) - module.FTR.size - mcs
    if tail_meta_start != cursor:
        raise RuntimeError(f"record/tail boundary mismatch for {path.name}: {cursor} != {tail_meta_start}")
    return {
        "magic": magic.decode("latin1"),
        "total_bytes": len(raw),
        "header_bytes": module.HDR.size,
        "footer_bytes": module.FTR.size,
        "metadata_raw_bytes": len(meta_raw),
        "metadata_compressed_one_copy_bytes": mcs,
        "metadata_compressed_two_copies_bytes": 2 * mcs,
        "record_count": count,
        "record_header_bytes": record_header_bytes,
        "record_payload_bytes": record_payload_bytes,
        "record_area_bytes": record_header_bytes + record_payload_bytes,
        "meta": meta,
        "records": record_rows,
    }


def _compact_meta(meta: dict) -> dict:
    omit = {
        "engine", "max_decode_unit", "max_decoder_memory", "max_dependency_depth",
        "max_mosaic_bases", "max_mosaic_source_index", "pack_limit", "pack_read_amplification",
        "max_mosaic_read_amplification", "preflate_required", "preflate_bridge_contract",
    }
    tag = {"direct": 0, "delta": 1, "mosaic": 2, "pack_mosaic": 3, "preflate": 4, "nodes": 5}
    top_key = {
        "v": 0, "files": 1, "nodes": 2, "record_rel_offsets": 3,
        "record_leaf_sha256": 4, "tree_sha256": 5,
    }

    def convert(value):
        if isinstance(value, list):
            out = [convert(item) for item in value]
            if out and isinstance(out[0], str) and out[0] in tag:
                out[0] = tag[out[0]]
            return out
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        return value

    return {
        top_key[key]: convert(value)
        for key, value in meta.items()
        if key not in omit and key in top_key
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    suite = work_root / "suite"
    small_metadata_control(suite)
    source = suite / "10_small_metadata_control"
    out_dir = work_root / "archives"
    out_dir.mkdir(parents=True)

    v025_path = out_dir / "v025.cmpct"
    v028_graph_path = out_dir / "v028-graph.cmpct"
    v028_portfolio_path = out_dir / "v028-portfolio.cmpct"
    placement_path = out_dir / "placement.cmpct"
    placement_portfolio_path = out_dir / "placement-portfolio.cmpct"

    V025.ROOT = source; V025.OUT = v025_path
    V025.build()
    V028._build_graph(source, v028_graph_path)
    v028_portfolio_stats = V028.build(source, v028_portfolio_path)
    placement_stats = PLACEMENT.build_graph(source, placement_path)
    placement_portfolio_stats = PLACEMENT.build(source, placement_portfolio_path)

    v025 = _parse(v025_path, V025)
    v028_graph = _parse(v028_graph_path, V028)
    placement = _parse(placement_path, PLACEMENT.IMPL)

    compact = _compact_meta(placement["meta"])
    compact_raw = msgpack.packb(compact, use_bin_type=True)
    compact_comp = PLACEMENT.IMPL.zc(compact_raw, 12)
    fixed_framing = placement["header_bytes"] + placement["footer_bytes"]
    baseline_bytes = int(v028_portfolio_stats["archive_bytes"])
    compact_total = fixed_framing + placement["record_area_bytes"] + 2 * len(compact_comp)

    # These are proof-oriented lower bounds, not format proposals. A recoverable grammar cannot literally
    # use zero metadata, and a single metadata copy is intentionally optimistic. Therefore a loss here is a
    # strict terminal result for metadata-only work under the current record/framing representation.
    zero_metadata_floor = fixed_framing + placement["record_area_bytes"]
    current_single_copy_floor = zero_metadata_floor + placement["metadata_compressed_one_copy_bytes"]
    compact_single_copy_floor = zero_metadata_floor + len(compact_comp)
    required_nonmetadata_reduction = max(0, compact_single_copy_floor - baseline_bytes + 1)

    return {
        "schema": "cmpct-mosaic-v029-small-envelope-diagnostic-v2",
        "claim_boundary": "diagnostic only; compact/single-copy/zero-metadata values are non-emitted lower-bound oracles",
        "tree_sha256": V028.treehash(source),
        "v025": {key: value for key, value in v025.items() if key != "meta"},
        "v028_graph": {key: value for key, value in v028_graph.items() if key != "meta"},
        "placement": {key: value for key, value in placement.items() if key != "meta"},
        "portfolio": {
            "v028_selected": v028_portfolio_stats["selected"],
            "v028_archive_bytes": baseline_bytes,
            "v028_legacy_bytes": v028_portfolio_stats["legacy_bytes"],
            "v028_graph_bytes": v028_portfolio_stats["graph_bytes"],
            "placement_selected": placement_portfolio_stats["selected"],
            "placement_archive_bytes": placement_portfolio_stats["archive_bytes"],
            "placement_graph_bytes": placement_portfolio_stats["mosaic_graph_bytes"],
        },
        "placement_mechanism": placement_stats,
        "compact_metadata_oracle": {
            "metadata_raw_bytes": len(compact_raw),
            "metadata_compressed_one_copy_bytes": len(compact_comp),
            "hypothetical_total_bytes": compact_total,
            "saving_vs_current_placement_bytes": placement["total_bytes"] - compact_total,
            "saving_vs_v028_portfolio_bytes": baseline_bytes - compact_total,
            "would_beat_v028_portfolio": compact_total < baseline_bytes,
        },
        "metadata_only_terminal_floor": {
            "fixed_framing_bytes": fixed_framing,
            "record_area_bytes": placement["record_area_bytes"],
            "zero_metadata_floor_bytes": zero_metadata_floor,
            "zero_metadata_headroom_vs_v028_bytes": baseline_bytes - zero_metadata_floor,
            "current_single_copy_floor_bytes": current_single_copy_floor,
            "current_single_copy_delta_vs_v028_bytes": current_single_copy_floor - baseline_bytes,
            "compact_single_copy_floor_bytes": compact_single_copy_floor,
            "compact_single_copy_delta_vs_v028_bytes": compact_single_copy_floor - baseline_bytes,
            "minimum_additional_nonmetadata_reduction_for_strict_win_bytes": required_nonmetadata_reduction,
            "metadata_only_family_terminal": compact_single_copy_floor >= baseline_bytes,
            "recovery_note": "single-copy and zero-metadata floors are optimistic non-emitted bounds; shipping recovery may require more bytes",
        },
        "comparisons": {
            "v025_vs_v028_graph_bytes": v028_graph["total_bytes"] - v025["total_bytes"],
            "placement_vs_v025_bytes": placement["total_bytes"] - v025["total_bytes"],
            "placement_vs_v028_graph_bytes": placement["total_bytes"] - v028_graph["total_bytes"],
            "placement_record_area_vs_v025_bytes": placement["record_area_bytes"] - v025["record_area_bytes"],
            "placement_record_area_vs_v028_graph_bytes": placement["record_area_bytes"] - v028_graph["record_area_bytes"],
            "placement_two_metadata_copies_vs_v025_bytes": placement["metadata_compressed_two_copies_bytes"] - v025["metadata_compressed_two_copies_bytes"],
            "placement_two_metadata_copies_vs_v028_graph_bytes": placement["metadata_compressed_two_copies_bytes"] - v028_graph["metadata_compressed_two_copies_bytes"],
            "placement_fixed_header_footer_vs_v025_bytes": fixed_framing - (v025["header_bytes"] + v025["footer_bytes"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Mosaic_Small_Envelope_Diagnostic"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2, default=str)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
