from __future__ import annotations

"""Research-only A/B for an EOCD-indexed ZIP-factor parser.

The exact scan profiler shows ZIP parsing dominates the remaining source-scan cost. The first byte-neutral parser
A/B (precompiled Structs + startswith guards) preserved exact semantics but saved only ~16 us median, far below
its 100 us materiality bar. This follow-up changes the traversal rather than another micro-operation: locate and
validate EOCD first, walk the declared central directory once, and validate each owning local header directly from
the central local-offset. The returned structure remains byte-for-byte/equality identical to the mature parser.

The experiment has zero production/release credit. It is valid only if the parsed object, fused-scan fingerprint,
and exact 14,033-byte candidate/SHA remain unchanged across alternating timing rounds.
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
EOCD_SIG = b"PK\x05\x06"
LOCAL_HDR = struct.Struct("<IHHHHHIIIHH")
CENTRAL_HDR = struct.Struct("<IHHHHHHIIIHHHHHII")
EOCD_HDR = struct.Struct("<IHHHHIIH")
MAX_EOCD_SEARCH = 22 + 65535


def _candidate_parse_zip(raw: bytes) -> dict | None:
    nraw = len(raw)
    if nraw < EOCD_HDR.size:
        return None

    eocd_at = raw.rfind(EOCD_SIG, max(0, nraw - MAX_EOCD_SEARCH))
    if eocd_at < 0 or eocd_at + EOCD_HDR.size > nraw:
        return None
    sig, disk, disk_cd, entries_disk, entries_total, cd_size, cd_offset, comment_len = EOCD_HDR.unpack_from(raw, eocd_at)
    if sig != BASE.EOCD or entries_disk < 1 or entries_disk != entries_total:
        return None
    if eocd_at + EOCD_HDR.size + comment_len != nraw:
        return None
    if cd_offset < 0 or cd_size < 0 or cd_offset + cd_size != eocd_at:
        return None

    central_rows = []
    central_at = cd_offset
    for _ in range(entries_total):
        if central_at + CENTRAL_HDR.size > eocd_at:
            return None
        fields = CENTRAL_HDR.unpack_from(raw, central_at)
        (_sig, made, needed, flags, method, mtime, mdate, crc, csize, usize,
         name_len, extra_len, row_comment_len, row_disk, internal_attr, external_attr, local_offset) = fields
        if _sig != BASE.CENTRAL:
            return None
        body = central_at + CENTRAL_HDR.size
        end = body + name_len + extra_len + row_comment_len
        if end > eocd_at:
            return None
        central_rows.append({
            "made": made, "needed": needed, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize,
            "name": raw[body:body + name_len],
            "extra": raw[body + name_len:body + name_len + extra_len],
            "comment": raw[body + name_len + extra_len:end],
            "disk": row_disk, "internal_attr": internal_attr, "external_attr": external_attr,
            "local_offset": local_offset,
        })
        central_at = end
    if central_at != eocd_at:
        return None

    local_rows = []
    local_at = 0
    for central in central_rows:
        # Mature semantics require central/local rows to correspond in order, including exact local offsets.
        if central["local_offset"] != local_at or local_at + LOCAL_HDR.size > cd_offset:
            return None
        fields = LOCAL_HDR.unpack_from(raw, local_at)
        _sig, version, flags, method, mtime, mdate, crc, csize, usize, name_len, extra_len = fields
        if _sig != BASE.LOCAL or flags & 0x0001 or flags & 0x0008 or method not in (0, 8):
            return None
        frame_end = local_at + LOCAL_HDR.size + name_len + extra_len
        payload_end = frame_end + csize
        if payload_end > cd_offset:
            return None
        name = raw[local_at + LOCAL_HDR.size:local_at + LOCAL_HDR.size + name_len]
        extra = raw[local_at + LOCAL_HDR.size + name_len:frame_end]
        if (
            name != central["name"]
            or flags != central["flags"]
            or method != central["method"]
            or mtime != central["mtime"]
            or mdate != central["mdate"]
            or crc != central["crc"]
            or csize != central["csize"]
            or usize != central["usize"]
        ):
            return None
        local_rows.append({
            "version": version, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize,
            "name": name, "extra": extra, "payload": raw[frame_end:payload_end], "offset": local_at,
        })
        local_at = payload_end
    if local_at != cd_offset:
        return None

    return {
        "raw_size": nraw,
        "locals": local_rows,
        "centrals": central_rows,
        "eocd": {"disk": disk, "disk_cd": disk_cd, "comment": raw[eocd_at + EOCD_HDR.size:]},
    }


def _fingerprint(result) -> str:
    manifest, items, stats = result
    h = hashlib.sha256(manifest)
    for rel, parsed in items:
        h.update(rel.encode("utf-8"))
        h.update(repr(parsed).encode("utf-8"))
    h.update(json.dumps(stats, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-eocd-parser-", dir=work_root) as td_raw:
        stage = EXT._normalized_stage(source, Path(td_raw))
        baseline_parse = BASE._parse_zip
        baseline_result = FUSED._scan(stage)
        baseline_fp = _fingerprint(baseline_result)
        try:
            BASE._parse_zip = _candidate_parse_zip
            candidate_result = FUSED._scan(stage)
            candidate_fp = _fingerprint(candidate_result)
        finally:
            BASE._parse_zip = baseline_parse
        if candidate_result != baseline_result or candidate_fp != baseline_fp:
            raise RuntimeError("EOCD-indexed ZIP parser changed fused scan semantics")

        baseline_times: list[float] = []
        candidate_times: list[float] = []
        raw_rows = []
        try:
            for rep in range(ROUNDS):
                order = ("baseline", "candidate") if rep % 2 == 0 else ("candidate", "baseline")
                row = {}
                for kind in order:
                    BASE._parse_zip = baseline_parse if kind == "baseline" else _candidate_parse_zip
                    t0 = time.perf_counter_ns()
                    result = FUSED._scan(stage)
                    elapsed = (time.perf_counter_ns() - t0) / 1e9
                    if _fingerprint(result) != baseline_fp:
                        raise RuntimeError(f"{kind} scan fingerprint drifted on repetition {rep}")
                    row[kind] = elapsed
                baseline_times.append(row["baseline"])
                candidate_times.append(row["candidate"])
                raw_rows.append(row)
        finally:
            BASE._parse_zip = baseline_parse
        archive, _stats = BUILD.build_bytes(stage, level=3, group_size=7)

    archive_sha = hashlib.sha256(archive).hexdigest()
    base_med = statistics.median(baseline_times)
    cand_med = statistics.median(candidate_times)
    saving = base_med - cand_med
    exact = len(archive) == EXPECTED_BYTES and archive_sha == EXPECTED_SHA
    faster = saving >= MIN_MEDIAN_SAVING_S and cand_med < base_med
    valid = exact and candidate_fp == baseline_fp and len(baseline_times) == ROUNDS and len(candidate_times) == ROUNDS
    return {
        "schema": "cmpct-v030-zipfactor-eocd-indexed-parser-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "required_archive_bytes": EXPECTED_BYTES,
            "required_archive_sha256": EXPECTED_SHA,
            "minimum_median_saving_s": MIN_MEDIAN_SAVING_S,
            "candidate_change": "EOCD-first central index + direct local-offset validation; identical parsed object",
        },
        "candidate": {
            "archive_bytes": len(archive),
            "archive_sha256": archive_sha,
            "scan_fingerprint": candidate_fp,
        },
        "timing": {
            "rounds": ROUNDS,
            "baseline_median_scan_s": float(base_med),
            "candidate_median_scan_s": float(cand_med),
            "median_saving_s": float(saving),
            "candidate_over_baseline_ratio": float(cand_med / base_med if base_med else 1.0),
            "raw": raw_rows,
        },
        "gate": {"experiment_valid": valid, "materially_faster": faster, "passed": valid},
        "claim_boundary": (
            "Research A/B only. A material speed win still requires canonical implementation plus complete "
            "ZIP/Zstd/recovery/native/Android/final-authority evidence before promotion."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-parser-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-eocd-parser.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "timing": result["timing"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor EOCD-indexed parser oracle invalid")


if __name__ == "__main__":
    main()
