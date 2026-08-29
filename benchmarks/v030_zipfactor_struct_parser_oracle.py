from __future__ import annotations

"""Research-only A/B for the measured ZIP-factor parser hot path.

The exact scan profiler attributed the dominant source-scan CPU cost to the mature BASE._parse_zip implementation.
cProfile also showed thousands of struct.unpack_from calls, including a separate 4-byte signature unpack before each
full local/central header unpack. This oracle keeps the already-falsified micro-optimization as durable negative
evidence: bytes.startswith signature guards plus precompiled Struct objects.

The candidate must return an exactly identical parsed structure, produce an exactly identical fused scan
fingerprint, and reproduce the exact 14,033-byte ZIP-factor archive/SHA. Parser selection is injected through the
fused scanner's explicit test seam; this oracle never mutates process-global parser state. Timing is research-only
and grants no production or release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import struct
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as BUILD
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_profile as BASE

ROUNDS = 61
MIN_MEDIAN_SAVING_S = 0.00010
EXPECTED_BYTES = 14033
EXPECTED_SHA = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"
LOCAL_SIG = b"PK\x03\x04"
CENTRAL_SIG = b"PK\x01\x02"
LOCAL_HDR = struct.Struct("<IHHHHHIIIHH")
CENTRAL_HDR = struct.Struct("<IHHHHHHIIIHHHHHII")
EOCD_HDR = struct.Struct("<IHHHHIIH")


def _candidate_parse_zip(raw: bytes) -> dict | None:
    at = 0
    nraw = len(raw)
    local_rows = []
    while at + 4 <= nraw and raw.startswith(LOCAL_SIG, at):
        if at + LOCAL_HDR.size > nraw:
            return None
        fields = LOCAL_HDR.unpack_from(raw, at)
        _sig, version, flags, method, mtime, mdate, crc, csize, usize, name_len, extra_len = fields
        if flags & 0x0001 or flags & 0x0008 or method not in (0, 8):
            return None
        frame_end = at + LOCAL_HDR.size + name_len + extra_len
        payload_end = frame_end + csize
        if payload_end > nraw:
            return None
        local_rows.append({
            "version": version, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize,
            "name": raw[at + LOCAL_HDR.size:at + LOCAL_HDR.size + name_len],
            "extra": raw[at + LOCAL_HDR.size + name_len:frame_end],
            "payload": raw[frame_end:payload_end], "offset": at,
        })
        at = payload_end
    if not local_rows:
        return None

    central_rows = []
    central_start = at
    while at + 4 <= nraw and raw.startswith(CENTRAL_SIG, at):
        if at + CENTRAL_HDR.size > nraw:
            return None
        fields = CENTRAL_HDR.unpack_from(raw, at)
        (_sig, made, needed, flags, method, mtime, mdate, crc, csize, usize,
         name_len, extra_len, comment_len, disk, internal_attr, external_attr, local_offset) = fields
        body = at + CENTRAL_HDR.size
        end = body + name_len + extra_len + comment_len
        if end > nraw:
            return None
        central_rows.append({
            "made": made, "needed": needed, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize,
            "name": raw[body:body + name_len],
            "extra": raw[body + name_len:body + name_len + extra_len],
            "comment": raw[body + name_len + extra_len:end],
            "disk": disk, "internal_attr": internal_attr, "external_attr": external_attr,
            "local_offset": local_offset,
        })
        at = end

    if len(central_rows) != len(local_rows) or at + EOCD_HDR.size > nraw:
        return None
    sig, disk, disk_cd, entries_disk, entries_total, cd_size, cd_offset, comment_len = EOCD_HDR.unpack_from(raw, at)
    if sig != BASE.EOCD or entries_disk != len(local_rows) or entries_total != len(local_rows):
        return None
    if cd_offset != central_start or cd_size != at - central_start or at + EOCD_HDR.size + comment_len != nraw:
        return None
    for local, central in zip(local_rows, central_rows, strict=True):
        if any((
            local["name"] != central["name"], local["flags"] != central["flags"],
            local["method"] != central["method"], local["mtime"] != central["mtime"],
            local["mdate"] != central["mdate"], local["crc"] != central["crc"],
            local["csize"] != central["csize"], local["usize"] != central["usize"],
            local["offset"] != central["local_offset"],
        )):
            return None
    return {"raw_size": nraw, "locals": local_rows, "centrals": central_rows,
            "eocd": {"disk": disk, "disk_cd": disk_cd, "comment": raw[at + EOCD_HDR.size:]}}


def _fingerprint(result) -> str:
    manifest, items, stats = result
    h = hashlib.sha256(manifest)
    for rel, parsed in items:
        h.update(rel.encode("utf-8")); h.update(repr(parsed).encode("utf-8"))
    h.update(json.dumps(stats, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-struct-parser-", dir=work_root) as td_raw:
        stage = EXT._normalized_stage(source, Path(td_raw))
        baseline_parse = BASE._parse_zip
        baseline_result = FUSED._scan(stage, parse_zip=baseline_parse)
        baseline_fp = _fingerprint(baseline_result)
        candidate_result = FUSED._scan(stage, parse_zip=_candidate_parse_zip)
        candidate_fp = _fingerprint(candidate_result)
        if candidate_result != baseline_result or candidate_fp != baseline_fp:
            raise RuntimeError("candidate ZIP parser changed fused scan semantics")

        baseline_times = []
        candidate_times = []
        raw_rows = []
        for rep in range(ROUNDS):
            order = ("baseline", "candidate") if rep % 2 == 0 else ("candidate", "baseline")
            row = {}
            for kind in order:
                parser = baseline_parse if kind == "baseline" else _candidate_parse_zip
                t0 = time.perf_counter_ns()
                result = FUSED._scan(stage, parse_zip=parser)
                elapsed = (time.perf_counter_ns() - t0) / 1e9
                if _fingerprint(result) != baseline_fp:
                    raise RuntimeError(f"{kind} scan fingerprint drifted on repetition {rep}")
                row[kind] = elapsed
            baseline_times.append(row["baseline"])
            candidate_times.append(row["candidate"])
            raw_rows.append(row)
        archive, _stats = BUILD.build_bytes(stage, level=3, group_size=7)

    archive_sha = hashlib.sha256(archive).hexdigest()
    base_med = statistics.median(baseline_times)
    cand_med = statistics.median(candidate_times)
    saving = base_med - cand_med
    exact = len(archive) == EXPECTED_BYTES and archive_sha == EXPECTED_SHA
    faster = saving >= MIN_MEDIAN_SAVING_S and cand_med < base_med
    valid = exact and candidate_fp == baseline_fp and len(baseline_times) == ROUNDS and len(candidate_times) == ROUNDS
    return {
        "schema": "cmpct-v030-zipfactor-struct-parser-oracle-v2",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "process_global_mutation": False,
            "required_archive_bytes": EXPECTED_BYTES,
            "required_archive_sha256": EXPECTED_SHA,
            "minimum_median_saving_s": MIN_MEDIAN_SAVING_S,
            "candidate_change": "bytes.startswith signature guards + precompiled Struct full-header decode",
        },
        "candidate": {"archive_bytes": len(archive), "archive_sha256": archive_sha, "scan_fingerprint": candidate_fp},
        "timing": {
            "rounds": ROUNDS,
            "baseline_median_scan_s": float(base_med),
            "candidate_median_scan_s": float(cand_med),
            "median_saving_s": float(saving),
            "candidate_over_baseline_ratio": float(cand_med / base_med if base_med else 1.0),
            "raw": raw_rows,
        },
        "gate": {"experiment_valid": valid, "materially_faster": faster, "passed": valid},
        "claim_boundary": "Durable negative research A/B. The candidate is not the shipping parser and receives no production/release credit.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-struct-parser-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-struct-parser.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "timing": result["timing"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor struct-parser oracle invalid")


if __name__ == "__main__":
    main()
