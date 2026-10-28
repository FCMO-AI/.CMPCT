from __future__ import annotations

"""R4 diagnostic for reversible cross-format tabular co-lifting.

The Analytics neutral workload intentionally contains CSV and JSONL views of the same 90k logical rows.
Independent pack compression has a proven expensive density floor.  This diagnostic asks whether a generic,
fail-closed structural lift can store the shared table once and reconstruct both source byte streams exactly.

This is not a format proposal.  It accepts a pair only when independently parsed CSV/JSONL rows are equal
and deterministic re-serialization reproduces both original byte streams byte-for-byte.  It charges schema /
dialect metadata, column framing, parse+encode time, and measures reader reconstruction time.  The isolated
pair saving is compared to the exact fixed-level15 whole-archive gap only as an optimistic feasibility bound;
whole-archive ownership/locality/integrity evidence is required before any product credit.
"""

import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import time

import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_zstd_parameter_decomposition as ZD
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
LEVELS = (3, 5, 9)
REPS = 2
COLUMN_HEADER_BYTES = 24
FIXED_OWNER_METADATA_BYTES = 512


def _parse_csv(raw: bytes) -> tuple[list[str], list[list[str]]]:
    text = raw.decode("utf-8")
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows:
        raise ValueError("empty CSV")
    return list(rows[0]), [list(r) for r in rows[1:]]


def _parse_jsonl(raw: bytes) -> tuple[list[str], list[dict]]:
    lines = raw.decode("utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line]
    if not rows or not isinstance(rows[0], dict):
        raise ValueError("empty/non-object JSONL")
    fields = list(rows[0].keys())
    if any(list(r.keys()) != fields for r in rows):
        raise ValueError("JSONL field order drift")
    return fields, rows


def _csv_from_json_rows(fields: list[str], rows: list[dict]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(fields)
    for row in rows:
        writer.writerow([row[f] for f in fields])
    return out.getvalue().encode("utf-8")


def _jsonl_bytes(rows: list[dict]) -> bytes:
    return ("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)).encode("utf-8")


def _semantic_equal(fields: list[str], csv_rows: list[list[str]], json_rows: list[dict]) -> bool:
    if len(csv_rows) != len(json_rows):
        return False
    # Compare against exact CSV lexicalization of each JSON value.  The round-trip byte gates below remain
    # authoritative; this equality gate merely rejects unrelated pairs cheaply before encoding.
    for crow, jrow in zip(csv_rows, json_rows):
        if len(crow) != len(fields):
            return False
        expected = [str(jrow[f]) if not isinstance(jrow[f], bool) else ("True" if jrow[f] else "False") for f in fields]
        if crow != expected:
            return False
    return True


def _encode_columns(fields: list[str], rows: list[dict], level: int) -> tuple[list[bytes], int]:
    cctx = zstd.ZstdCompressor(level=level)
    blobs = []
    logical = 0
    for field in fields:
        raw = json.dumps([r[field] for r in rows], separators=(",", ":")).encode("utf-8")
        logical += len(raw)
        blobs.append(cctx.compress(raw))
    return blobs, logical


def _decode_columns(fields: list[str], blobs: list[bytes]) -> list[dict]:
    dctx = zstd.ZstdDecompressor()
    cols = [json.loads(dctx.decompress(blob).decode("utf-8")) for blob in blobs]
    if not cols:
        return []
    n = len(cols[0])
    if any(len(c) != n for c in cols):
        raise RuntimeError("column length mismatch")
    return [{field: cols[j][i] for j, field in enumerate(fields)} for i in range(n)]


def _baseline_pair(raw_csv: bytes, raw_json: bytes) -> int:
    cctx = zstd.ZstdCompressor(level=15)
    return len(cctx.compress(raw_csv)) + len(cctx.compress(raw_json)) + 2 * COLUMN_HEADER_BYTES


def _variant(fields: list[str], rows: list[dict], raw_csv: bytes, raw_json: bytes, level: int) -> dict:
    create_samples = []
    decode_samples = []
    stored_sizes = set()
    logical_column_bytes = set()
    for _ in range(REPS):
        started = time.perf_counter()
        blobs, logical = _encode_columns(fields, rows, level)
        metadata = json.dumps({"fields": fields, "csv_dialect": "excel", "json_separators": [",", ":"]}, separators=(",", ":")).encode("utf-8")
        stored = sum(map(len, blobs)) + len(metadata) + FIXED_OWNER_METADATA_BYTES + len(blobs) * COLUMN_HEADER_BYTES
        create_samples.append(time.perf_counter() - started)
        stored_sizes.add(stored)
        logical_column_bytes.add(logical)

        started = time.perf_counter()
        decoded = _decode_columns(fields, blobs)
        rebuilt_csv = _csv_from_json_rows(fields, decoded)
        rebuilt_json = _jsonl_bytes(decoded)
        decode_samples.append(time.perf_counter() - started)
        if rebuilt_csv != raw_csv or rebuilt_json != raw_json:
            raise RuntimeError("structural lift did not reconstruct source bytes exactly")
    if len(stored_sizes) != 1 or len(logical_column_bytes) != 1:
        raise RuntimeError("nondeterministic structural lift")
    return {
        "level": level,
        "stored_bytes": next(iter(stored_sizes)),
        "logical_column_encoding_bytes_before_zstd": next(iter(logical_column_bytes)),
        "median_encode_s": statistics.median(create_samples),
        "median_decode_and_reconstruct_s": statistics.median(decode_samples),
        "repetitions": REPS,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_colift_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_colift_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work / "normalized")
    expected_tree = PRODUCT.treehash(stage)

    csv_path = stage / "events.csv"
    json_path = stage / "events.jsonl"
    raw_csv = csv_path.read_bytes()
    raw_json = json_path.read_bytes()

    parse_started = time.perf_counter()
    csv_fields, csv_rows = _parse_csv(raw_csv)
    json_fields, json_rows = _parse_jsonl(raw_json)
    parse_s = time.perf_counter() - parse_started
    if csv_fields != json_fields or not _semantic_equal(csv_fields, csv_rows, json_rows):
        raise RuntimeError("CSV/JSONL semantic equivalence gate failed")
    if _csv_from_json_rows(csv_fields, json_rows) != raw_csv or _jsonl_bytes(json_rows) != raw_json:
        raise RuntimeError("fail-closed exact source round-trip gate failed")

    # Hostile disproof: a one-row rotation must no longer be accepted as the same semantic table.
    rotated = json_rows[1:] + json_rows[:1]
    if _semantic_equal(csv_fields, csv_rows, rotated):
        raise RuntimeError("hostile mismatch control was incorrectly accepted")

    baseline_pair = _baseline_pair(raw_csv, raw_json)
    variants = [_variant(csv_fields, json_rows, raw_csv, raw_json, level) for level in LEVELS]
    accepted = int(GENERAL._accepted_v029_rows()[("neutral_hostile_v1", TARGET)]["accepted_v029_bytes"])

    # Reproduce the fixed-L15 whole-archive authority rather than hard-coding the prior receipt.
    profile, _ = ZD._prepare(stage, work / "fixed-l15")
    archive = work / "fixed-l15" / "candidate.cmpnx5"
    _, _, _ = ZD._scan(profile, archive)
    ZD._verify(profile, archive, work / "fixed-l15" / "out", expected_tree)
    l15_archive = archive.stat().st_size
    required = l15_archive - accepted + 1

    for v in variants:
        v["pair_saving_vs_independent_zstd15_bytes"] = baseline_pair - v["stored_bytes"]
        v["optimistic_fraction_of_whole_archive_gap"] = v["pair_saving_vs_independent_zstd15_bytes"] / max(1, required)
        v["charged_writer_s"] = parse_s + v["median_encode_s"]

    best = min(variants, key=lambda r: (r["stored_bytes"], r["charged_writer_s"]))
    return {
        "schema": "cmpct-v030-r4-tabular-colift-oracle-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": TARGET,
        "canonical_tree_sha256": expected_tree,
        "row_count": len(json_rows),
        "fields": csv_fields,
        "source_bytes": {"csv": len(raw_csv), "jsonl": len(raw_json), "total": len(raw_csv) + len(raw_json)},
        "parse_and_equivalence_s": parse_s,
        "independent_pair_zstd15_bytes": baseline_pair,
        "fixed_level15_archive_bytes": l15_archive,
        "accepted_v029_bytes": accepted,
        "strict_whole_archive_saving_required_to_beat_v029": required,
        "variants": variants,
        "best_variant": best,
        "hypothesis": {
            "exact_two_format_reconstruction": True,
            "hostile_rotated_rows_rejected": True,
            "best_pair_saving_exceeds_whole_archive_gap": best["pair_saving_vs_independent_zstd15_bytes"] >= required,
            "best_writer_under_one_second": best["charged_writer_s"] < 1.0,
            "supported_as_structural_feasibility_oracle": best["pair_saving_vs_independent_zstd15_bytes"] >= required and best["charged_writer_s"] < 1.0,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "exact_source_bytes_required": True,
            "whole_archive_saving_is_optimistic_pair_delta_not_integrated_product_size": True,
            "reader_reconstruction_time_measured": True,
        },
        "next_if_supported": "build a bounded authenticated tabular owner with exact member reconstruction, selective-row/member dependency accounting, all-15 hostile controls and full create/read/RSS measurement",
        "next_if_falsified": "retire CSV/JSONL semantic co-lifting as the primary Analytics R4 and move to a different structural primitive",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-tabular-colift-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-tabular-colift.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best_variant": result["best_variant"], "hypothesis": result["hypothesis"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
