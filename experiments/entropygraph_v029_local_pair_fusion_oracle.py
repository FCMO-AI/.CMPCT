"""CMPCT v0.29 detached oracle — locality-bounded pair fusion.

The first bounded-solid LZMA2 oracle rejected its exact greedy adjacency policy with zero candidate
groups. That algorithm can discard a compatible nearby pair merely because a size-imbalanced record sits
between them. This successor changes the grouping rule, not the safety budget: each direct/root record
may pair with one of the next eight eligible physical records, the fused raw unit is <=2 MiB, and reading
either member must materialize <=8x that member's logical bytes. Records are used at most once.

Every candidate pair is encoded independently as raw LZMA2 and round-tripped byte-exactly. Selection is
greedy by measured net saving after fixed framing charges. A PASS is only a research signal; canonical
revision-24 bytes remain untouched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "entropygraph_v029_bounded_solid_lzma2_oracle.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SRC = _load(SOURCE_PATH, "cmpct_v029_pair_fusion_source")
BASE = SRC.BASE
ENGINE = SRC.ENGINE
CODEC_PREFLATE = SRC.CODEC_PREFLATE

LOOKAHEAD_RECORDS = 8
MAX_FUSED_RAW_BYTES = 2 << 20
MAX_MEMBER_AMPLIFICATION = 8.0
DICT_SIZES = (1 << 20, 4 << 20, 8 << 20)
GROUP_METADATA_CHARGE = 32
MEMBER_METADATA_CHARGE = 8
MIN_NET_SAVING = 128 * 1024
MIN_PROFITABLE_PAIRS = 4


def _pair_admissible(a: dict, b: dict) -> bool:
    total = int(a["logical_bytes"]) + int(b["logical_bytes"])
    if total > MAX_FUSED_RAW_BYTES:
        return False
    return all(
        total / max(1, int(row["logical_bytes"])) <= MAX_MEMBER_AMPLIFICATION
        for row in (a, b)
    )


def _candidate_pairs(rows: list[dict]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for i, left in enumerate(rows):
        for j in range(i + 1, min(len(rows), i + 1 + LOOKAHEAD_RECORDS)):
            if _pair_admissible(left, rows[j]):
                pairs.append((i, j))
    return pairs


def measure(root: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    archive = work_root / "attempt5.cmpct"
    started = time.perf_counter()
    built = ENGINE.build(root, archive)
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != ENGINE.BASE.treehash(root):
        raise RuntimeError("attempt-5 source archive failed verification before pair-fusion oracle")

    meta, records = BASE._read_records(archive)
    direct_ids = BASE._direct_record_ids(meta)
    candidates = [
        row for row in records
        if row["record_id"] in direct_ids and row["codec"] != CODEC_PREFLATE
    ]
    pair_indices = _candidate_pairs(candidates)
    results = []
    for dict_size in DICT_SIZES:
        scored = []
        encode_s = 0.0
        decode_s = 0.0
        for i, j in pair_indices:
            group = (candidates[i], candidates[j])
            raw = group[0]["raw"] + group[1]["raw"]
            payload, enc, dec = SRC._compress_verify(raw, dict_size)
            encode_s += enc
            decode_s += dec
            baseline = sum(int(row["payload_bytes"]) for row in group)
            metadata = GROUP_METADATA_CHARGE + 2 * MEMBER_METADATA_CHARGE
            saving = baseline - len(payload) - metadata
            if saving <= 0:
                continue
            amp = max(len(raw) / max(1, int(row["logical_bytes"])) for row in group)
            scored.append({
                "indices": [i, j],
                "record_ids": [int(row["record_id"]) for row in group],
                "physical_candidate_distance": j - i,
                "logical_bytes": len(raw),
                "baseline_payload_bytes": baseline,
                "lzma2_payload_bytes": len(payload),
                "metadata_charge_bytes": metadata,
                "net_saving_bytes": saving,
                "max_member_amplification": amp,
            })
        scored.sort(key=lambda item: (-item["net_saving_bytes"], item["record_ids"]))
        used: set[int] = set()
        selected = []
        for item in scored:
            i, j = item["indices"]
            if i in used or j in used:
                continue
            used.update((i, j))
            selected.append(item)
        net = sum(item["net_saving_bytes"] for item in selected)
        results.append({
            "dictionary_bytes": dict_size,
            "candidate_pairs": len(pair_indices),
            "profitable_candidate_pairs": len(scored),
            "selected_disjoint_pairs": len(selected),
            "net_saving_bytes": net,
            "max_member_amplification": max((x["max_member_amplification"] for x in selected), default=0.0),
            "encode_s": encode_s,
            "decode_s": decode_s,
            "top_pairs": selected[:24],
        })

    best = max(results, key=lambda r: (r["net_saving_bytes"], -r["dictionary_bytes"]))
    gate = bool(
        best["net_saving_bytes"] >= MIN_NET_SAVING
        and best["selected_disjoint_pairs"] >= MIN_PROFITABLE_PAIRS
        and best["max_member_amplification"] <= MAX_MEMBER_AMPLIFICATION
    )
    return {
        "schema": "cmpct-v029-local-pair-fusion-oracle-v1",
        "claim_boundary": "detached ceiling only; emitted archive remains exact attempt-5 bytes",
        "source_archive": {"bytes": archive.stat().st_size, "selected": built.get("selected")},
        "policy": {
            "lookahead_records": LOOKAHEAD_RECORDS,
            "max_fused_raw_bytes": MAX_FUSED_RAW_BYTES,
            "max_member_materialization_amplification": MAX_MEMBER_AMPLIFICATION,
            "dictionary_sizes_bytes": list(DICT_SIZES),
            "group_metadata_charge_bytes": GROUP_METADATA_CHARGE,
            "member_metadata_charge_bytes": MEMBER_METADATA_CHARGE,
            "min_net_saving_bytes": MIN_NET_SAVING,
            "min_profitable_pairs": MIN_PROFITABLE_PAIRS,
            "records_used_at_most_once": True,
            "roundtrip_verified_per_pair": True,
            "thresholds_frozen_before_measurement": True
        },
        "candidate_records": len(candidates),
        "best": best,
        "research_gate_pass": gate,
        "results": results,
        "oracle_wall_s": time.perf_counter() - started
    }


def main() -> None:
    p = argparse.ArgumentParser(description="CMPCT locality-bounded pair-fusion oracle")
    p.add_argument("source", type=Path)
    p.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Local_Pair_Fusion"))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = measure(args.source, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_records": result["candidate_records"], "best": result["best"], "research_gate_pass": result["research_gate_pass"]}, indent=2))


if __name__ == "__main__":
    main()
