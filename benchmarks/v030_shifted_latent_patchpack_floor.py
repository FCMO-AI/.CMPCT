from __future__ import annotations

"""R4 Shifted capacity test: one latent basis plus one bounded patch context.

The prior latent-consensus oracle showed the shared basis itself is smaller than solid
Zstd-19, while 18 independently compressed patch programs erase that advantage. This
instrument keeps the same content-only latent derivation and exact depth-1 deltas, but
packs every tiny patch program into one <=8 MiB decoded context. It also prices an
identical independent-frame control so the experiment can distinguish "patch relation
entropy is too high" from "tiny frame/context fragmentation consumed the margin".

The control compression is timed separately from candidate construction. Causal evidence
must not make the candidate appear slower merely because the experiment also builds its
counterfactual. Research only: a size win advances construction/runtime work and grants
no release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks.resemblance_hostile_corpus_v1 import shifted_versions, tree_hash
from benchmarks import v030_shifted_latent_consensus_floor as LAT
from cmpct.resemblance import delta_decode, delta_encode

PATCH_LEVEL = 19


def _put_varint(out: bytearray, value: int) -> None:
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = tree_hash(source)
    rows = [(p.name, p.read_bytes()) for p in sorted(source.iterdir())]
    if len(rows) != 18:
        raise AssertionError("frozen Shifted file count drift")

    pivot_name, pivot = min(rows, key=lambda x: hashlib.sha256(x[1]).digest())
    others = [data for name, data in rows if name != pivot_name]

    candidate_started = time.perf_counter()
    phase_started = candidate_started
    latent, derivation = LAT._derive_latent(pivot, others)
    latent_derivation_s = time.perf_counter() - phase_started
    if not latent or len(latent) > LAT.MAX_DECODE:
        raise AssertionError("latent basis violates decode-unit bound")

    phase_started = time.perf_counter()
    base_cctx = zstd.ZstdCompressor(level=19, threads=0, write_checksum=True)
    latent_stored = base_cctx.compress(latent)
    latent_compress_s = time.perf_counter() - phase_started

    phase_started = time.perf_counter()
    raw_patches: list[tuple[str, int, bytes, bytes]] = []
    total_copy = 0
    total_literal = 0
    for name, target in rows:
        d = delta_encode(latent, target, block=LAT.DELTA_BLOCK, max_base_index=LAT.MAX_DECODE)
        raw_patches.append((name, len(target), d.payload, hashlib.sha256(target).digest()))
        total_copy += int(d.stats.copied_bytes)
        total_literal += int(d.stats.literal_bytes)
    delta_construction_s = time.perf_counter() - phase_started

    patch_raw = b"".join(payload for _, _, payload, _ in raw_patches)
    if len(patch_raw) > LAT.MAX_DECODE:
        raise AssertionError("shared patch context exceeds decode-unit bound")

    # Candidate path: one shared frame/context. Stop its construction clock only after
    # complete research framing below; verification and comparator construction are not
    # part of create time, matching the external comparator boundary.
    phase_started = time.perf_counter()
    patch_stored = zstd.ZstdCompressor(level=PATCH_LEVEL, threads=0, write_checksum=True).compress(patch_raw)
    shared_patch_compress_s = time.perf_counter() - phase_started

    artifact = bytearray(b"CMPNXLCP1")
    artifact.extend(hashlib.sha256(latent).digest())
    _put_varint(artifact, len(latent_stored)); artifact.extend(latent_stored)
    _put_varint(artifact, len(patch_stored)); artifact.extend(patch_stored)
    _put_varint(artifact, len(raw_patches))
    for name, logical_n, payload, digest in raw_patches:
        nb = name.encode()
        _put_varint(artifact, len(nb)); artifact.extend(nb)
        _put_varint(artifact, logical_n)
        _put_varint(artifact, len(payload))
        artifact.extend(digest)
    artifact.extend(bytes.fromhex(expected_tree))
    candidate_create_s = time.perf_counter() - candidate_started

    # Strongest simple control: the same exact raw delta programs, same level/checksum,
    # but each receives an independent Zstd frame/context. Build it *after* the candidate
    # timer stops so counterfactual instrumentation cannot contaminate candidate speed.
    control_started = time.perf_counter()
    individual_patch_stored = [
        zstd.ZstdCompressor(level=PATCH_LEVEL, threads=0, write_checksum=True).compress(payload)
        for _, _, payload, _ in raw_patches
    ]
    control_compress_s = time.perf_counter() - control_started
    individual_patch_stored_bytes = sum(map(len, individual_patch_stored))
    patch_context_saved_bytes = individual_patch_stored_bytes - len(patch_stored)
    if patch_context_saved_bytes < 0:
        raise AssertionError("shared patch context unexpectedly larger than identical independent-frame control")

    unpacked = zstd.ZstdDecompressor().decompress(patch_stored, max_output_size=LAT.MAX_DECODE)
    if unpacked != patch_raw:
        raise AssertionError("patch-pack round trip mismatch")
    verify = work_root / "verify"
    verify.mkdir()
    pos = 0
    for (name, logical_n, payload, _), (_, target) in zip(raw_patches, rows, strict=True):
        got_payload = unpacked[pos:pos + len(payload)]
        pos += len(payload)
        rebuilt = delta_decode(latent, got_payload, expected_size=logical_n, max_output=LAT.MAX_DECODE)
        if rebuilt != target:
            raise AssertionError("packed latent delta reconstruction mismatch")
        (verify / name).write_bytes(rebuilt)
    if pos != len(unpacked) or tree_hash(verify) != expected_tree:
        raise AssertionError("exact tree mismatch")

    zip_row = LAT.COMP._zip_deflate(source, work_root / "competitor.zip")
    zstd_row = LAT.COMP._solid_tar_zstd(source, work_root / "competitor.tar.zst")
    if not zip_row.get("available") or not zstd_row.get("available"):
        raise RuntimeError("required external comparator unavailable")

    payload_floor = len(latent_stored) + len(patch_stored)
    independent_payload_floor = len(latent_stored) + individual_patch_stored_bytes
    max_logical = max(len(data) for _, data in rows)
    max_amp = max((len(latent) + len(patch_raw) + len(data)) / max(1, len(data)) for _, data in rows)
    size_crosses_zstd = len(artifact) < int(zstd_row["bytes"])
    strict = (
        len(artifact) < int(zip_row["bytes"])
        and size_crosses_zstd
        and candidate_create_s < float(zip_row["create_s"])
        and candidate_create_s < float(zstd_row["create_s"])
    )
    terminal = "PROMOTE_NEXT_PREREQUISITE" if size_crosses_zstd else "RETIRE_FAMILY"

    return {
        "schema": "cmpct-v030-shifted-latent-patchpack-floor-v3",
        "source_commit": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local",
        "strict_target": "15/15: each workload strictly smaller and faster than ZIP/Deflate and solid Zstd-19; ties fail",
        "diagnosis": "D4",
        "radicality": "R4",
        "saturation_inherited": ["S1", "S3", "S4"],
        "rps": 99,
        "referee": {
            "causal_hypothesis": "the latent basis already beats Zstd; independent tiny patch frames, not relation entropy, consume the remaining size margin",
            "strongest_control": "same latent basis and exact delta programs compressed as eighteen independent level-19 checksum frames",
            "disproof": "one legal shared patch context plus complete research framing remains >= exact solid Zstd-19 bytes",
            "strongest_failure": "even a size crossing does not solve the inherited ~12 s latent derivation cost",
        },
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "pivot_selection": "minimum logical-content SHA-256",
            "max_chain_depth": 1,
            "single_shared_patch_context": True,
            "patch_context_level": PATCH_LEVEL,
            "candidate_create_excludes_counterfactual_control": True,
            "release_credit": False,
        },
        "workload": {"files": len(rows), "logical_bytes": sum(len(d) for _, d in rows), "tree_sha256": expected_tree},
        "derivation": derivation,
        "timing": {
            "latent_derivation_s": latent_derivation_s,
            "latent_compress_s": latent_compress_s,
            "delta_construction_s": delta_construction_s,
            "shared_patch_compress_s": shared_patch_compress_s,
            "candidate_create_s": candidate_create_s,
            "independent_frame_control_compress_s": control_compress_s,
        },
        "candidate": {
            "latent_logical_bytes": len(latent),
            "latent_stored_bytes": len(latent_stored),
            "patch_raw_bytes": len(patch_raw),
            "patch_stored_bytes": len(patch_stored),
            "independent_patch_stored_bytes": individual_patch_stored_bytes,
            "patch_context_saved_bytes": patch_context_saved_bytes,
            "patch_context_saved_fraction": patch_context_saved_bytes / max(1, individual_patch_stored_bytes),
            "independent_payload_floor_bytes": independent_payload_floor,
            "payload_floor_bytes": payload_floor,
            "archive_bytes": len(artifact),
            "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
            "create_seconds": candidate_create_s,
            "copied_bytes": total_copy,
            "literal_bytes": total_literal,
            "tree_verified": True,
            "max_chain_depth": 1,
            "max_decode_unit_bytes": max(len(latent), len(patch_raw), max_logical),
            "max_member_read_amplification": max_amp,
        },
        "comparators": {"zip_deflate9": zip_row, "tar_zstd19_solid": zstd_row},
        "hostile_reviewer": {
            "context_gain_is_exactly_attributed": True,
            "counterfactual_control_excluded_from_candidate_timing": True,
            "shared_context_exports_decode_work": "every member may require the bounded shared patch context; this is charged in max_member_read_amplification",
            "remaining_unpriced_debt": "final canonical/recovery/platform framing and implementation do not receive release credit from this capacity test",
        },
        "decision": {
            "payload_floor_zstd_gap_bytes": payload_floor - int(zstd_row["bytes"]),
            "archive_zstd_gap_bytes": len(artifact) - int(zstd_row["bytes"]),
            "context_gain_bytes_vs_identical_independent_frames": patch_context_saved_bytes,
            "size_crosses_zstd": size_crosses_zstd,
            "strict_four_way_win": strict,
            "terminal": terminal,
            "release_credit": False,
            "next_decisive_test": "replace quadratic Python latent derivation with a single-pass/native support collector while preserving exact candidate bytes" if size_crosses_zstd else "retire latent edit-program ownership and invent a non-delta single-context representation",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
