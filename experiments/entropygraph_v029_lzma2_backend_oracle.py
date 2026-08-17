"""CMPCT v0.29 detached oracle — bounded LZMA2 physical-record backend.

Both preregistered Zstd cross-record-context mechanisms failed: the stored shared dictionary bought only
6,340 net bytes and one-hop reference context found zero admissible profitable targets. This oracle
therefore changes the model of the problem instead of relaxing those gates. It asks whether the large
independent physical-record pool itself is using the wrong backend.

The exact accepted attempt-5 archive is built first. Eligible direct/root records are decoded through the
existing authenticated reader, independently recompressed as bounded raw LZMA2 frames, immediately
decoded and byte-compared, and charged a conservative per-record transition cost. Record boundaries,
logical dependency depth and selective-read topology do not change in this ceiling measurement.

This is not a format implementation. A PASS only authorizes a reader-visible experiment with independent
vectors, malformed/resource tests, native parity, recovery/export semantics and fresh competitor evidence.
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
SOURCE_PATH = HERE / "entropygraph_v029_shared_dictionary_oracle.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SRC = _load(SOURCE_PATH, "cmpct_v029_lzma2_source")
ENGINE = SRC.ENGINE
CODEC_PREFLATE = SRC.CODEC_PREFLATE

# Frozen before measurement. Keeping dictionary memory <=8 MiB is deliberate: the point is to test a
# practical independently-decodable backend, not to recreate a giant solid 7z stream inside CMPCT.
DICT_SIZES = (1 << 20, 4 << 20, 8 << 20)
TRANSITION_METADATA_CHARGE = 16
MIN_NET_SAVING = 128 * 1024
MIN_IMPROVED_RECORDS = 4
MAX_DICT_BYTES = 8 << 20


def _compress_verify(raw: bytes, dict_size: int) -> tuple[bytes, float, float]:
    filters = [{"id": lzma.FILTER_LZMA2, "dict_size": dict_size, "preset": 6}]
    started = time.perf_counter()
    payload = lzma.compress(raw, format=lzma.FORMAT_RAW, filters=filters)
    encode_s = time.perf_counter() - started
    started = time.perf_counter()
    restored = lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=filters)
    decode_s = time.perf_counter() - started
    if restored != raw:
        raise RuntimeError("LZMA2 oracle round-trip changed physical logical record bytes")
    return payload, encode_s, decode_s


def measure(root: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    archive = work_root / "attempt5.cmpct"
    wall_started = time.perf_counter()
    built = ENGINE.build(root, archive)
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != ENGINE.BASE.treehash(root):
        raise RuntimeError("attempt-5 source archive failed verification before LZMA2 backend oracle")

    meta, records = SRC._read_records(archive)
    direct_ids = SRC._direct_record_ids(meta)
    candidates = [
        row for row in records
        if row["record_id"] in direct_ids and row["codec"] != CODEC_PREFLATE
    ]
    baseline_payload = sum(int(row["payload_bytes"]) for row in candidates)
    results = []

    for dict_size in DICT_SIZES:
        rows = []
        encode_s = 0.0
        decode_s = 0.0
        for row in candidates:
            payload, enc, dec = _compress_verify(row["raw"], dict_size)
            encode_s += enc
            decode_s += dec
            saving = int(row["payload_bytes"]) - len(payload) - TRANSITION_METADATA_CHARGE
            if saving <= 0:
                continue
            rows.append({
                "record_id": int(row["record_id"]),
                "logical_bytes": int(row["logical_bytes"]),
                "baseline_payload_bytes": int(row["payload_bytes"]),
                "lzma2_payload_bytes": len(payload),
                "transition_charge_bytes": TRANSITION_METADATA_CHARGE,
                "net_saving_bytes": saving,
            })
        rows.sort(key=lambda item: (-item["net_saving_bytes"], item["record_id"]))
        net = sum(item["net_saving_bytes"] for item in rows)
        results.append({
            "dictionary_bytes": dict_size,
            "profitable_records": len(rows),
            "net_saving_bytes": net,
            "baseline_candidate_payload_bytes": baseline_payload,
            "selected_payload_fraction": (
                sum(item["baseline_payload_bytes"] for item in rows) / max(1, baseline_payload)
            ),
            "recompress_verify_encode_s": encode_s,
            "recompress_verify_decode_s": decode_s,
            "top_record_savings": rows[:24],
        })

    best = max(results, key=lambda row: (row["net_saving_bytes"], -row["dictionary_bytes"]))
    gate = bool(
        best["net_saving_bytes"] >= MIN_NET_SAVING
        and best["profitable_records"] >= MIN_IMPROVED_RECORDS
        and best["dictionary_bytes"] <= MAX_DICT_BYTES
    )
    return {
        "schema": "cmpct-v029-lzma2-backend-oracle-v1",
        "claim_boundary": "detached physical-backend ceiling only; emitted archive remains exact attempt-5 bytes",
        "source_archive": {
            "bytes": archive.stat().st_size,
            "selected": built.get("selected"),
            "records": len(records),
            "direct_records": len(direct_ids),
            "candidate_records": len(candidates),
            "candidate_payload_bytes": baseline_payload,
        },
        "policy": {
            "dictionary_sizes_bytes": list(DICT_SIZES),
            "max_decoder_dictionary_bytes": MAX_DICT_BYTES,
            "transition_metadata_charge_per_record": TRANSITION_METADATA_CHARGE,
            "min_net_saving_bytes": MIN_NET_SAVING,
            "min_improved_records": MIN_IMPROVED_RECORDS,
            "record_boundaries_unchanged": True,
            "dependency_depth_unchanged": True,
            "roundtrip_verified_per_candidate": True,
            "thresholds_frozen_before_measurement": True,
        },
        "best": best,
        "research_gate_pass": gate,
        "results": results,
        "oracle_wall_s": time.perf_counter() - wall_started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT detached bounded LZMA2 physical-record backend oracle")
    parser.add_argument("source", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_LZMA2_Backend_Oracle"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.source, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best": result["best"], "research_gate_pass": result["research_gate_pass"]}, indent=2))


if __name__ == "__main__":
    main()
