"""CMPCT v0.29 detached oracle — bounded solid LZMA2 record clusters.

Independent per-record LZMA2 failed decisively: only 152 net bytes on one record. That result says the
problem is not simply choosing a stronger codec for the same independent decode units. This oracle tests
a different mechanism class: whether a *small, explicitly bounded solid cluster* of already-adjacent
attempt-5 direct/root records can expose cross-record redundancy that independent Zstd/LZMA2 missed.

The experiment keeps logical dependency depth unchanged. It may enlarge a physical decode unit, but only
under a frozen <=8x per-member materialization bound and <=2 MiB raw cluster ceiling. Every selected
cluster is raw-LZMA2 round-tripped byte-exactly, every framing byte is charged, and attempt-5 archive bytes
remain untouched. A PASS only authorizes a reader-visible research implementation; it is not a format
claim.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import lzma
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "entropygraph_v029_lzma2_backend_oracle.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SRC = _load(SOURCE_PATH, "cmpct_v029_bounded_solid_source")
BASE = SRC.SRC
ENGINE = SRC.ENGINE
CODEC_PREFLATE = SRC.CODEC_PREFLATE

# Frozen before measurement. Physical adjacency is deliberate: attempt-5 already has a locality-aware
# physical order, so this asks whether bounded solidity can exploit redundancy without introducing a new
# similarity search or arbitrary dependency graph.
CLUSTER_LIMITS = (512 << 10, 1 << 20, 2 << 20)
DICT_SIZES = (1 << 20, 4 << 20, 8 << 20)
MAX_MEMBER_AMPLIFICATION = 8.0
GROUP_METADATA_CHARGE = 32
MEMBER_METADATA_CHARGE = 8
MIN_NET_SAVING = 128 * 1024
MIN_PROFITABLE_GROUPS = 4


def _pack_adjacent(rows: list[dict], limit: int) -> list[list[dict]]:
    groups: list[list[dict]] = []
    current: list[dict] = []
    current_raw = 0

    def admissible(candidate: list[dict], total: int) -> bool:
        if len(candidate) < 2:
            return True
        return all(total / max(1, int(row["logical_bytes"])) <= MAX_MEMBER_AMPLIFICATION for row in candidate)

    for row in rows:
        size = int(row["logical_bytes"])
        if current and (current_raw + size > limit or not admissible(current + [row], current_raw + size)):
            if len(current) >= 2:
                groups.append(current)
            current = []
            current_raw = 0
        current.append(row)
        current_raw += size
        if current_raw >= limit:
            if len(current) >= 2 and admissible(current, current_raw):
                groups.append(current)
            current = []
            current_raw = 0
    if len(current) >= 2 and admissible(current, current_raw):
        groups.append(current)
    return groups


def _compress_verify(raw: bytes, dict_size: int) -> tuple[bytes, float, float]:
    filters = [{"id": lzma.FILTER_LZMA2, "dict_size": dict_size, "preset": 6}]
    started = time.perf_counter()
    payload = lzma.compress(raw, format=lzma.FORMAT_RAW, filters=filters)
    encode_s = time.perf_counter() - started
    started = time.perf_counter()
    restored = lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=filters)
    decode_s = time.perf_counter() - started
    if restored != raw:
        raise RuntimeError("bounded-solid LZMA2 round-trip changed concatenated physical logical bytes")
    return payload, encode_s, decode_s


def measure(root: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    archive = work_root / "attempt5.cmpct"
    wall_started = time.perf_counter()
    built = ENGINE.build(root, archive)
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != ENGINE.BASE.treehash(root):
        raise RuntimeError("attempt-5 source archive failed verification before bounded-solid oracle")

    meta, records = BASE._read_records(archive)
    direct_ids = BASE._direct_record_ids(meta)
    candidates = [
        row for row in records
        if row["record_id"] in direct_ids and row["codec"] != CODEC_PREFLATE
    ]
    baseline_payload = sum(int(row["payload_bytes"]) for row in candidates)
    results = []

    for cluster_limit in CLUSTER_LIMITS:
        groups = _pack_adjacent(candidates, cluster_limit)
        for dict_size in DICT_SIZES:
            selected = []
            encode_s = 0.0
            decode_s = 0.0
            for group in groups:
                raw = b"".join(row["raw"] for row in group)
                payload, enc, dec = _compress_verify(raw, dict_size)
                encode_s += enc
                decode_s += dec
                baseline = sum(int(row["payload_bytes"]) for row in group)
                metadata = GROUP_METADATA_CHARGE + MEMBER_METADATA_CHARGE * len(group)
                saving = baseline - len(payload) - metadata
                if saving <= 0:
                    continue
                amps = [len(raw) / max(1, int(row["logical_bytes"])) for row in group]
                if max(amps) > MAX_MEMBER_AMPLIFICATION:
                    raise RuntimeError("selected bounded-solid group violated frozen member amplification")
                selected.append({
                    "record_ids": [int(row["record_id"]) for row in group],
                    "members": len(group),
                    "logical_bytes": len(raw),
                    "baseline_payload_bytes": baseline,
                    "lzma2_payload_bytes": len(payload),
                    "metadata_charge_bytes": metadata,
                    "net_saving_bytes": saving,
                    "max_member_amplification": max(amps),
                })
            selected.sort(key=lambda item: (-item["net_saving_bytes"], item["record_ids"]))
            net = sum(item["net_saving_bytes"] for item in selected)
            weighted_amp_num = sum(
                item["logical_bytes"] * item["baseline_payload_bytes"] for item in selected
            )
            weighted_amp_den = sum(item["baseline_payload_bytes"] for item in selected)
            results.append({
                "cluster_limit_bytes": cluster_limit,
                "dictionary_bytes": dict_size,
                "candidate_groups": len(groups),
                "profitable_groups": len(selected),
                "net_saving_bytes": net,
                "baseline_candidate_payload_bytes": baseline_payload,
                "weighted_group_logical_bytes": weighted_amp_num / max(1, weighted_amp_den),
                "max_member_amplification": max(
                    (item["max_member_amplification"] for item in selected), default=0.0
                ),
                "recompress_verify_encode_s": encode_s,
                "recompress_verify_decode_s": decode_s,
                "top_group_savings": selected[:24],
            })

    best = max(
        results,
        key=lambda row: (row["net_saving_bytes"], -row["cluster_limit_bytes"], -row["dictionary_bytes"]),
    )
    gate = bool(
        best["net_saving_bytes"] >= MIN_NET_SAVING
        and best["profitable_groups"] >= MIN_PROFITABLE_GROUPS
        and best["max_member_amplification"] <= MAX_MEMBER_AMPLIFICATION
    )
    return {
        "schema": "cmpct-v029-bounded-solid-lzma2-oracle-v1",
        "claim_boundary": "detached bounded-solid ceiling only; emitted archive remains exact attempt-5 bytes",
        "source_archive": {
            "bytes": archive.stat().st_size,
            "selected": built.get("selected"),
            "records": len(records),
            "direct_records": len(direct_ids),
            "candidate_records": len(candidates),
            "candidate_payload_bytes": baseline_payload,
        },
        "policy": {
            "cluster_limits_bytes": list(CLUSTER_LIMITS),
            "dictionary_sizes_bytes": list(DICT_SIZES),
            "max_member_materialization_amplification": MAX_MEMBER_AMPLIFICATION,
            "group_metadata_charge_bytes": GROUP_METADATA_CHARGE,
            "member_metadata_charge_bytes": MEMBER_METADATA_CHARGE,
            "min_net_saving_bytes": MIN_NET_SAVING,
            "min_profitable_groups": MIN_PROFITABLE_GROUPS,
            "physical_order_frozen": True,
            "logical_dependency_depth_unchanged": True,
            "roundtrip_verified_per_group": True,
            "thresholds_frozen_before_measurement": True,
        },
        "best": best,
        "research_gate_pass": gate,
        "results": results,
        "oracle_wall_s": time.perf_counter() - wall_started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT detached bounded-solid LZMA2 cluster oracle")
    parser.add_argument("source", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Bounded_Solid_LZMA2"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.source, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best": result["best"], "research_gate_pass": result["research_gate_pass"]}, indent=2))


if __name__ == "__main__":
    main()
