from __future__ import annotations

"""Bounded authenticated owner oracle for reversible tabular co-lifting.

This diagnostic follows the positive CSV<->JSONL co-lift feasibility receipt.  It is deliberately not a
shipping-format change.  It asks whether the same semantic table can be represented once in bounded row
groups while paying concrete integrity, framing, deterministic decode and failure-blast-radius costs.

Every accepted pair must independently parse equal rows and reconstruct both source byte streams exactly.
The owner authenticates its manifest and every compressed column payload.  Row groups bound corruption and
reconstruction cones; no reader-side discovery is performed.
"""

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import struct
import time

import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_zstd_parameter_decomposition as ZD
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
MAGIC = b"TCOL1\0\0\0"
LEVEL = 5
ROW_GROUPS = (2048, 4096, 8192, 16384)
REPS = 2


def _parse_csv(raw: bytes) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline="")))
    if not rows:
        raise ValueError("empty CSV")
    return list(rows[0]), [list(r) for r in rows[1:]]


def _parse_jsonl(raw: bytes) -> tuple[list[str], list[dict]]:
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    if not rows or not isinstance(rows[0], dict):
        raise ValueError("empty/non-object JSONL")
    fields = list(rows[0].keys())
    if any(list(r.keys()) != fields for r in rows):
        raise ValueError("JSONL field order drift")
    return fields, rows


def _semantic_equal(fields: list[str], csv_rows: list[list[str]], json_rows: list[dict]) -> bool:
    if len(csv_rows) != len(json_rows):
        return False
    for crow, jrow in zip(csv_rows, json_rows):
        expected = [str(jrow[f]) if not isinstance(jrow[f], bool) else ("True" if jrow[f] else "False") for f in fields]
        if crow != expected:
            return False
    return True


def _csv_bytes(fields: list[str], rows: list[dict], *, include_header: bool = True) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    if include_header:
        writer.writerow(fields)
    for row in rows:
        writer.writerow([row[f] for f in fields])
    return out.getvalue().encode("utf-8")


def _jsonl_bytes(rows: list[dict]) -> bytes:
    return ("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _encode_owner(fields: list[str], rows: list[dict], row_group_rows: int) -> tuple[bytes, dict]:
    cctx = zstd.ZstdCompressor(level=LEVEL)
    payload = bytearray()
    groups = []
    for start in range(0, len(rows), row_group_rows):
        chunk = rows[start : start + row_group_rows]
        columns = []
        for field in fields:
            raw = json.dumps([r[field] for r in chunk], separators=(",", ":")).encode("utf-8")
            compressed = cctx.compress(raw)
            offset = len(payload)
            payload.extend(compressed)
            columns.append({
                "field": field,
                "offset": offset,
                "stored_bytes": len(compressed),
                "logical_column_bytes": len(raw),
                "sha256": _sha(compressed),
            })
        groups.append({"row_start": start, "row_count": len(chunk), "columns": columns})

    manifest = {
        "schema": "cmpct-tabular-owner-v1",
        "fields": fields,
        "row_count": len(rows),
        "row_group_rows": row_group_rows,
        "compression": {"codec": "zstd", "level": LEVEL},
        "groups": groups,
    }
    manifest_raw = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf-8")
    prefix = MAGIC + struct.pack("<I", len(manifest_raw)) + hashlib.sha256(manifest_raw).digest()
    owner = prefix + manifest_raw + bytes(payload)
    stats = {
        "manifest_bytes": len(manifest_raw),
        "prefix_bytes": len(prefix),
        "payload_bytes": len(payload),
        "group_count": len(groups),
        "max_group_payload_bytes": max(sum(c["stored_bytes"] for c in g["columns"]) for g in groups),
        "max_group_logical_column_bytes": max(sum(c["logical_column_bytes"] for c in g["columns"]) for g in groups),
    }
    return owner, stats


def _open_owner(owner: bytes) -> tuple[dict, int]:
    if len(owner) < 44 or owner[:8] != MAGIC:
        raise ValueError("bad tabular owner header")
    manifest_len = struct.unpack("<I", owner[8:12])[0]
    end = 44 + manifest_len
    if end > len(owner):
        raise ValueError("truncated tabular owner manifest")
    expected = owner[12:44]
    manifest_raw = owner[44:end]
    if hashlib.sha256(manifest_raw).digest() != expected:
        raise ValueError("tabular owner manifest authentication failed")
    manifest = json.loads(manifest_raw)
    return manifest, end


def _decode_group(owner: bytes, manifest: dict, payload_base: int, group_index: int) -> list[dict]:
    group = manifest["groups"][group_index]
    cols = []
    dctx = zstd.ZstdDecompressor()
    for col in group["columns"]:
        start = payload_base + int(col["offset"])
        end = start + int(col["stored_bytes"])
        if start < payload_base or end > len(owner):
            raise ValueError("tabular owner payload bounds violation")
        compressed = owner[start:end]
        if _sha(compressed) != col["sha256"]:
            raise ValueError("tabular owner payload authentication failed")
        cols.append(json.loads(dctx.decompress(compressed).decode("utf-8")))
    n = int(group["row_count"])
    if any(len(c) != n for c in cols):
        raise ValueError("tabular owner column length mismatch")
    fields = list(manifest["fields"])
    return [{field: cols[j][i] for j, field in enumerate(fields)} for i in range(n)]


def _decode_all(owner: bytes) -> tuple[list[str], list[dict], dict]:
    manifest, payload_base = _open_owner(owner)
    rows = []
    for gi in range(len(manifest["groups"])):
        rows.extend(_decode_group(owner, manifest, payload_base, gi))
    if len(rows) != int(manifest["row_count"]):
        raise ValueError("tabular owner total row count mismatch")
    return list(manifest["fields"]), rows, manifest


def _corruption_must_fail(owner: bytes) -> bool:
    manifest, payload_base = _open_owner(owner)
    first = manifest["groups"][0]["columns"][0]
    at = payload_base + int(first["offset"])
    damaged = bytearray(owner)
    damaged[at] ^= 0x01
    try:
        _decode_group(bytes(damaged), manifest, payload_base, 0)
    except ValueError as exc:
        return "authentication failed" in str(exc)
    return False


def _baseline_pair(raw_csv: bytes, raw_json: bytes) -> int:
    cctx = zstd.ZstdCompressor(level=15)
    return len(cctx.compress(raw_csv)) + len(cctx.compress(raw_json)) + 48


def _measure_variant(fields: list[str], rows: list[dict], raw_csv: bytes, raw_json: bytes, group_rows: int) -> dict:
    encode_samples = []
    decode_samples = []
    owners = []
    stats = None
    for _ in range(REPS):
        started = time.perf_counter()
        owner, stats = _encode_owner(fields, rows, group_rows)
        encode_samples.append(time.perf_counter() - started)
        owners.append(owner)

        started = time.perf_counter()
        got_fields, decoded, manifest = _decode_all(owner)
        rebuilt_csv = _csv_bytes(got_fields, decoded)
        rebuilt_json = _jsonl_bytes(decoded)
        decode_samples.append(time.perf_counter() - started)
        if rebuilt_csv != raw_csv or rebuilt_json != raw_json:
            raise RuntimeError("authenticated owner did not reconstruct exact source bytes")
        if not _corruption_must_fail(owner):
            raise RuntimeError("corruption hostile control was not rejected")

    if owners[0] != owners[1]:
        raise RuntimeError("nondeterministic tabular owner bytes")
    assert stats is not None
    owner = owners[0]
    manifest, payload_base = _open_owner(owner)

    group_physical = []
    group_logical_output = []
    fields2 = list(manifest["fields"])
    for gi, group in enumerate(manifest["groups"]):
        decoded = _decode_group(owner, manifest, payload_base, gi)
        physical = sum(int(c["stored_bytes"]) for c in group["columns"])
        logical = len(_csv_bytes(fields2, decoded, include_header=(gi == 0))) + len(_jsonl_bytes(decoded))
        group_physical.append(physical)
        group_logical_output.append(logical)

    return {
        "row_group_rows": group_rows,
        "stored_bytes": len(owner),
        "median_encode_s": statistics.median(encode_samples),
        "median_decode_and_reconstruct_both_s": statistics.median(decode_samples),
        "manifest_bytes": stats["manifest_bytes"],
        "payload_bytes": stats["payload_bytes"],
        "group_count": stats["group_count"],
        "max_group_payload_bytes": max(group_physical),
        "max_group_logical_blast_radius_bytes": max(group_logical_output),
        "max_group_physical_to_logical_ratio": max(p / max(1, l) for p, l in zip(group_physical, group_logical_output)),
        "member_dependency_fanout": 2,
        "random_member_byte_range_supported": False,
        "repetitions": REPS,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_owner_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_owner_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work / "normalized")
    expected_tree = PRODUCT.treehash(stage)

    raw_csv = (stage / "events.csv").read_bytes()
    raw_json = (stage / "events.jsonl").read_bytes()
    parse_started = time.perf_counter()
    csv_fields, csv_rows = _parse_csv(raw_csv)
    json_fields, json_rows = _parse_jsonl(raw_json)
    parse_s = time.perf_counter() - parse_started
    if csv_fields != json_fields or not _semantic_equal(csv_fields, csv_rows, json_rows):
        raise RuntimeError("semantic pair gate failed")
    if _csv_bytes(csv_fields, json_rows) != raw_csv or _jsonl_bytes(json_rows) != raw_json:
        raise RuntimeError("exact lexical reconstruction gate failed")
    rotated = json_rows[1:] + json_rows[:1]
    if _semantic_equal(csv_fields, csv_rows, rotated):
        raise RuntimeError("rotated-row hostile control accepted")

    profile, _ = ZD._prepare(stage, work / "fixed-l15")
    archive = work / "fixed-l15" / "candidate.cmpnx5"
    _, _, _ = ZD._scan(profile, archive)
    ZD._verify(profile, archive, work / "fixed-l15" / "out", expected_tree)
    l15_archive = archive.stat().st_size
    accepted = int(GENERAL._accepted_v029_rows()[("neutral_hostile_v1", TARGET)]["accepted_v029_bytes"])
    pair_baseline = _baseline_pair(raw_csv, raw_json)

    variants = [_measure_variant(csv_fields, json_rows, raw_csv, raw_json, g) for g in ROW_GROUPS]
    for v in variants:
        v["pair_saving_vs_independent_zstd15_bytes"] = pair_baseline - v["stored_bytes"]
        v["optimistic_projected_whole_archive_bytes"] = l15_archive - v["pair_saving_vs_independent_zstd15_bytes"]
        v["optimistic_margin_vs_v029_bytes"] = accepted - v["optimistic_projected_whole_archive_bytes"]
        v["charged_writer_s"] = parse_s + v["median_encode_s"]

    promotable = [v for v in variants if v["optimistic_margin_vs_v029_bytes"] > 0 and v["charged_writer_s"] < 1.0]
    best = min(promotable or variants, key=lambda v: (v["stored_bytes"], v["max_group_logical_blast_radius_bytes"]))
    return {
        "schema": "cmpct-v030-r4-tabular-owner-oracle-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": TARGET,
        "canonical_tree_sha256": expected_tree,
        "row_count": len(json_rows),
        "fields": csv_fields,
        "source_bytes": {"csv": len(raw_csv), "jsonl": len(raw_json), "total": len(raw_csv) + len(raw_json)},
        "parse_and_equivalence_s": parse_s,
        "independent_pair_zstd15_bytes": pair_baseline,
        "fixed_level15_archive_bytes": l15_archive,
        "accepted_v029_bytes": accepted,
        "variants": variants,
        "best_variant": best,
        "hypothesis": {
            "exact_two_format_reconstruction": True,
            "rotated_rows_rejected": True,
            "payload_corruption_rejected_before_decode": True,
            "bounded_row_group_owner_exists": True,
            "optimistic_whole_archive_beats_v029": best["optimistic_margin_vs_v029_bytes"] > 0,
            "charged_writer_under_one_second": best["charged_writer_s"] < 1.0,
            "supported_for_integrated_owner_prototype": best["optimistic_margin_vs_v029_bytes"] > 0 and best["charged_writer_s"] < 1.0,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "manifest_authenticated": True,
            "payloads_authenticated": True,
            "row_group_failure_cones_bounded": True,
            "member_dependency_fanout_measured": True,
            "random_member_byte_range_supported": False,
            "whole_archive_projection_is_optimistic_not_integrated_product_size": True,
        },
        "next_if_supported": "prototype one research-only authenticated owner inside the v0.30 product wrapper, then measure actual archive bytes, complete create/read/RSS, member/range locality, recovery and hostile false-positive controls before any format proposal",
        "next_if_falsified": "retire bounded tabular co-lift ownership as the primary Analytics R4 and move to a different reversible structural primitive",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-tabular-owner-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-tabular-owner.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best_variant": result["best_variant"], "hypothesis": result["hypothesis"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
