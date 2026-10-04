from __future__ import annotations

"""Selective-range falsifier for the bounded tabular co-lift owner.

The positive bounded-owner receipt leaves locality as its largest explicit debt.  This oracle does not change the
owner representation.  It constructs a tiny authenticated lexical-length index for the existing row groups and
asks whether exact byte ranges in either reconstructed CSV or JSONL view can be served by decoding only intersecting
row groups.  It reports both cold-read amplification (owner manifest + range index + touched payload) and warm-read
amplification (touched payload after authenticated metadata is already open), so metadata overhead cannot disappear
from the evidence.
"""

import argparse
import bisect
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = OWNER.TARGET
REQUEST_BYTES = 4096
MAX_STEADY_STORED_AMPLIFICATION = 8.0
MAX_DECODED_LOGICAL_BYTES = 8 * 1024 * 1024
INDEX_MAGIC = b"TCIX1\0\0\0"


def _segments(fields: list[str], rows: list[dict], group_rows: int, member: str) -> list[bytes]:
    out = []
    for gi, start in enumerate(range(0, len(rows), group_rows)):
        chunk = rows[start : start + group_rows]
        if member == "csv":
            out.append(OWNER._csv_bytes(fields, chunk, include_header=(gi == 0)))
        elif member == "jsonl":
            out.append(OWNER._jsonl_bytes(chunk))
        else:
            raise ValueError(member)
    return out


def _range_index(csv_segments: list[bytes], json_segments: list[bytes]) -> bytes:
    if len(csv_segments) != len(json_segments):
        raise ValueError("segment-count mismatch")
    body = bytearray()
    body.extend(struct.pack("<I", len(csv_segments)))
    for c, j in zip(csv_segments, json_segments):
        body.extend(struct.pack("<QQ", len(c), len(j)))
    digest = hashlib.sha256(body).digest()
    return INDEX_MAGIC + digest + bytes(body)


def _parse_index(raw: bytes) -> tuple[list[int], list[int]]:
    if len(raw) < 44 or raw[:8] != INDEX_MAGIC:
        raise ValueError("bad lexical range index")
    body = raw[40:]
    if hashlib.sha256(body).digest() != raw[8:40]:
        raise ValueError("lexical range index authentication failed")
    if len(body) < 4:
        raise ValueError("truncated lexical range index")
    n = struct.unpack("<I", body[:4])[0]
    if len(body) != 4 + n * 16:
        raise ValueError("lexical range index length mismatch")
    csv_lengths, json_lengths = [], []
    at = 4
    for _ in range(n):
        c, j = struct.unpack("<QQ", body[at : at + 16])
        csv_lengths.append(int(c)); json_lengths.append(int(j)); at += 16
    return csv_lengths, json_lengths


def _prefix(lengths: list[int]) -> list[int]:
    out = [0]
    for n in lengths:
        out.append(out[-1] + n)
    return out


def _read_range(owner: bytes, index: bytes, member: str, start: int, length: int) -> tuple[bytes, dict]:
    manifest, payload_base = OWNER._open_owner(owner)
    csv_lengths, json_lengths = _parse_index(index)
    lengths = csv_lengths if member == "csv" else json_lengths
    prefix = _prefix(lengths)
    total = prefix[-1]
    if start < 0 or length < 0 or start + length > total:
        raise ValueError("range outside logical member")
    if length == 0:
        return b"", {"groups_touched": 0, "payload_bytes_touched": 0, "decoded_member_segment_bytes": 0}
    first = max(0, bisect.bisect_right(prefix, start) - 1)
    last = max(first, bisect.bisect_left(prefix, start + length) - 1)
    pieces = []
    payload_bytes = 0
    decoded_segment_bytes = 0
    for gi in range(first, last + 1):
        group = manifest["groups"][gi]
        rows = OWNER._decode_group(owner, manifest, payload_base, gi)
        payload_bytes += sum(int(c["stored_bytes"]) for c in group["columns"])
        if member == "csv":
            segment = OWNER._csv_bytes(list(manifest["fields"]), rows, include_header=(gi == 0))
        else:
            segment = OWNER._jsonl_bytes(rows)
        if len(segment) != lengths[gi]:
            raise RuntimeError("lexical range index drift")
        pieces.append(segment)
        decoded_segment_bytes += len(segment)
    joined = b"".join(pieces)
    relative = start - prefix[first]
    answer = joined[relative : relative + length]
    if len(answer) != length:
        raise RuntimeError("short reconstructed range")
    return answer, {
        "groups_touched": last - first + 1,
        "payload_bytes_touched": payload_bytes,
        "decoded_member_segment_bytes": decoded_segment_bytes,
        "metadata_bytes_touched_cold": payload_base + len(index),
    }


def _requests(n: int) -> list[tuple[int, int]]:
    length = min(REQUEST_BYTES, n)
    return [(0, length), (max(0, n // 2 - length // 2), length), (max(0, n - length), length)]


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_owner_range_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_owner_range_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work / "normalized")
    expected_tree = PRODUCT.treehash(stage)
    raw_csv = (stage / "events.csv").read_bytes(); raw_json = (stage / "events.jsonl").read_bytes()
    csv_fields, csv_rows = OWNER._parse_csv(raw_csv); json_fields, json_rows = OWNER._parse_jsonl(raw_json)
    if csv_fields != json_fields or not OWNER._semantic_equal(csv_fields, csv_rows, json_rows):
        raise RuntimeError("semantic pair gate failed")

    variants = []
    for group_rows in OWNER.ROW_GROUPS:
        owner, stats = OWNER._encode_owner(csv_fields, json_rows, group_rows)
        csv_segments = _segments(csv_fields, json_rows, group_rows, "csv")
        json_segments = _segments(csv_fields, json_rows, group_rows, "jsonl")
        index = _range_index(csv_segments, json_segments)
        if _parse_index(index) != ([len(x) for x in csv_segments], [len(x) for x in json_segments]):
            raise RuntimeError("range-index round trip failed")
        rows = []
        for member, raw in (("csv", raw_csv), ("jsonl", raw_json)):
            for start, length in _requests(len(raw)):
                got, diag = _read_range(owner, index, member, start, length)
                if got != raw[start : start + length]:
                    raise RuntimeError(f"exact {member} byte-range mismatch at {start}+{length}")
                warm_amp = diag["payload_bytes_touched"] / max(1, length)
                cold_bytes = diag["payload_bytes_touched"] + diag["metadata_bytes_touched_cold"]
                cold_amp = cold_bytes / max(1, length)
                decoded_amp = diag["decoded_member_segment_bytes"] / max(1, length)
                rows.append({
                    "member": member,
                    "start": start,
                    "length": length,
                    **diag,
                    "warm_stored_amplification": warm_amp,
                    "cold_stored_amplification": cold_amp,
                    "decoded_logical_amplification": decoded_amp,
                })
        variants.append({
            "row_group_rows": group_rows,
            "owner_bytes": len(owner),
            "owner_manifest_bytes": stats["manifest_bytes"],
            "range_index_bytes": len(index),
            "requests": rows,
            "max_warm_stored_amplification": max(r["warm_stored_amplification"] for r in rows),
            "max_cold_stored_amplification": max(r["cold_stored_amplification"] for r in rows),
            "max_decoded_logical_bytes": max(r["decoded_member_segment_bytes"] for r in rows),
            "max_decoded_logical_amplification": max(r["decoded_logical_amplification"] for r in rows),
            "warm_locality_pass": max(r["warm_stored_amplification"] for r in rows) <= MAX_STEADY_STORED_AMPLIFICATION and max(r["decoded_member_segment_bytes"] for r in rows) <= MAX_DECODED_LOGICAL_BYTES,
            "cold_locality_pass": max(r["cold_stored_amplification"] for r in rows) <= MAX_STEADY_STORED_AMPLIFICATION and max(r["decoded_member_segment_bytes"] for r in rows) <= MAX_DECODED_LOGICAL_BYTES,
        })

    warm = [v for v in variants if v["warm_locality_pass"]]
    return {
        "schema": "cmpct-v030-r4-tabular-owner-range-oracle-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": TARGET,
        "canonical_tree_sha256": expected_tree,
        "request_bytes": REQUEST_BYTES,
        "variants": variants,
        "hypothesis": {
            "exact_ranges_reconstructed": True,
            "authenticated_length_index_round_trips": True,
            "at_least_one_warm_owner_meets_8x_and_8mib": bool(warm),
            "at_least_one_cold_owner_meets_8x_and_8mib": any(v["cold_locality_pass"] for v in variants),
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "metadata_cost_reported_separately_for_cold_and_warm_reads": True,
            "reader_discovery": False,
        },
        "next_if_warm_only": "compact/authenticate owner metadata and lexical offsets as a bounded binary index before integrated-product publication; do not relax the locality threshold",
        "next_if_cold_passes": "advance the smallest-debt owner to an integrated research product wrapper and measure actual archive/create/read/RSS/recovery costs",
        "next_if_no_warm_pass": "retire current row-group layout and redesign the owner partitioning before any product integration",
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-tabular-owner-range-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-tabular-owner-range.json")); a=p.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"variants":[{k:v[k] for k in ("row_group_rows","max_warm_stored_amplification","max_cold_stored_amplification","max_decoded_logical_bytes","warm_locality_pass","cold_locality_pass")} for v in result["variants"]],"hypothesis":result["hypothesis"]}, indent=2))

if __name__ == "__main__": main()
