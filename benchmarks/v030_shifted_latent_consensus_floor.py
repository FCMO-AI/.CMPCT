from __future__ import annotations

"""R4 Shifted oracle: derive one latent consensus basis, then exact deltas.

This is intentionally different from the existing stored-member resemblance graph.
The physical basis is not required to equal any logical member: it is synthesized
from cross-member agreement, stored once, and each logical file is reconstructed
from a bounded depth-1 COPY/LITERAL program against that latent basis.

Research only.  No benchmark identity is available to base selection or relation
construction; names appear only in complete research framing and tree verification.
"""

import argparse
from array import array
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

import zstandard as zstd

from benchmarks.resemblance_hostile_corpus_v1 import shifted_versions, tree_hash
from cmpct.resemblance import delta_decode, delta_encode

ROOT = Path(__file__).resolve().parents[1]
MIN_SUPPORT = 8
DELTA_BLOCK = 64
MAX_DECODE = 8 * 1024 * 1024


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


COMP = _load(ROOT / "benchmarks" / "entropygraph_v028_bench.py", "cmpct_v030_latent_competitors")


def _get_varint(payload: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(10):
        if pos >= len(payload):
            raise ValueError("truncated varint")
        b = payload[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not b & 0x80:
            return value, pos
        shift += 7
    raise ValueError("oversized varint")


def _copy_spans(payload: bytes) -> list[tuple[int, int]]:
    spans = []
    p = 0
    while p < len(payload):
        tag = payload[p]
        p += 1
        if tag == 0:
            n, p = _get_varint(payload, p)
            if p + n > len(payload):
                raise ValueError("truncated literal")
            p += n
        elif tag == 1:
            off, p = _get_varint(payload, p)
            n, p = _get_varint(payload, p)
            spans.append((off, n))
        else:
            raise ValueError("unknown delta opcode")
    return spans


def _put_varint(out: bytearray, value: int) -> None:
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def _derive_latent(pivot: bytes, others: list[bytes]) -> tuple[bytes, dict]:
    """Delete pivot-only spans using exact cross-member COPY support.

    A byte survives only when at least MIN_SUPPORT other logical members copy it
    exactly from the pivot under the existing bounded rolling-delta relation.
    This specifically removes pivot-private insertions/mutations instead of
    forcing them into the one shared physical basis.
    """
    diff = array("b", [0]) * (len(pivot) + 1)
    audition_raw = 0
    copied_total = 0
    for target in others:
        d = delta_encode(pivot, target, block=DELTA_BLOCK, max_base_index=MAX_DECODE)
        audition_raw += len(d.payload)
        copied_total += d.stats.copied_bytes
        for off, n in _copy_spans(d.payload):
            if off < 0 or n < 0 or off + n > len(pivot):
                raise AssertionError("delta emitted invalid pivot span")
            diff[off] += 1
            diff[off + n] -= 1

    coverage = 0
    latent = bytearray()
    kept = 0
    low = 0
    support_hist: dict[int, int] = {}
    for i, b in enumerate(pivot):
        coverage += diff[i]
        support_hist[coverage] = support_hist.get(coverage, 0) + 1
        if coverage >= MIN_SUPPORT:
            latent.append(b)
            kept += 1
        else:
            low += 1
    return bytes(latent), {
        "pivot_bytes": len(pivot),
        "latent_bytes": kept,
        "removed_low_support_bytes": low,
        "first_pass_delta_payload_bytes": audition_raw,
        "first_pass_copied_bytes": copied_total,
        "support_histogram": {str(k): v for k, v in sorted(support_hist.items())},
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    shifted_versions(work_root)
    source = work_root / "01_shifted_versions"
    expected_tree = tree_hash(source)
    rows = [(p.name, p.read_bytes()) for p in sorted(source.iterdir())]
    if len(rows) != 18:
        raise AssertionError("frozen Shifted file count drift")

    # Content-only pivot identity. Paths are unavailable to the mechanism.
    pivot_name, pivot = min(rows, key=lambda x: hashlib.sha256(x[1]).digest())
    others = [data for name, data in rows if name != pivot_name]

    started = time.perf_counter()
    latent, derivation = _derive_latent(pivot, others)
    if not latent or len(latent) > MAX_DECODE:
        raise AssertionError("latent basis violates decode-unit bound")

    base_cctx = zstd.ZstdCompressor(level=19, threads=0, write_checksum=True)
    patch_cctx = zstd.ZstdCompressor(level=1, threads=0, write_checksum=True)
    patch_dctx = zstd.ZstdDecompressor()
    latent_stored = base_cctx.compress(latent)

    patches = []
    restored = {}
    total_raw_patch = 0
    total_stored_patch = 0
    total_copy = 0
    total_literal = 0
    for name, target in rows:
        d = delta_encode(latent, target, block=DELTA_BLOCK, max_base_index=MAX_DECODE)
        packed = patch_cctx.compress(d.payload)
        raw = patch_dctx.decompress(packed)
        rebuilt = delta_decode(latent, raw, expected_size=len(target), max_output=MAX_DECODE)
        if rebuilt != target:
            raise AssertionError("latent delta reconstruction mismatch")
        restored[name] = rebuilt
        patches.append((name, len(target), packed, hashlib.sha256(target).digest()))
        total_raw_patch += len(d.payload)
        total_stored_patch += len(packed)
        total_copy += int(d.stats.copied_bytes)
        total_literal += int(d.stats.literal_bytes)
    create_s = time.perf_counter() - started

    verify = work_root / "verify"
    verify.mkdir()
    for name, data in restored.items():
        (verify / name).write_bytes(data)
    if tree_hash(verify) != expected_tree:
        raise AssertionError("exact tree mismatch")

    # Complete framing. The optimistic floor deliberately excludes all names,
    # per-file hashes, table bytes and final tree hash; if that floor loses,
    # serializer work cannot rescue this representation.
    artifact = bytearray(b"CMPNXLC1")
    artifact.extend(bytes.fromhex(hashlib.sha256(latent).hexdigest()))
    _put_varint(artifact, len(latent_stored)); artifact.extend(latent_stored)
    _put_varint(artifact, len(patches))
    for name, logical_n, packed, digest in patches:
        nb = name.encode()
        _put_varint(artifact, len(nb)); artifact.extend(nb)
        _put_varint(artifact, logical_n)
        _put_varint(artifact, len(packed)); artifact.extend(packed)
        artifact.extend(digest)
    artifact.extend(bytes.fromhex(expected_tree))

    zip_row = COMP._zip_deflate(source, work_root / "competitor.zip")
    zstd_row = COMP._solid_tar_zstd(source, work_root / "competitor.tar.zst")
    if not zip_row.get("available") or not zstd_row.get("available"):
        raise RuntimeError("required external comparator unavailable")

    payload_floor = len(latent_stored) + total_stored_patch
    max_logical = max(len(d) for _, d in rows)
    max_amp = max((len(latent) + len(d)) / max(1, len(d)) for _, d in rows)
    strict = (
        len(artifact) < int(zip_row["bytes"])
        and len(artifact) < int(zstd_row["bytes"])
        and create_s < float(zip_row["create_s"])
        and create_s < float(zstd_row["create_s"])
    )

    return {
        "schema": "cmpct-v030-shifted-latent-consensus-floor-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local",
        "diagnosis": "D4",
        "radicality": "R4",
        "saturation_inherited": ["S1", "S3", "S4"],
        "rps": 96,
        "strict_target": "15/15: each workload strictly smaller and faster than ZIP/Deflate and solid Zstd-19; ties fail",
        "referee": {
            "simplest_control": "stored-member depth-1 rolling delta (already represented in the v0.28/v0.29 lineage)",
            "causal_hypothesis": "private edits in every stored logical base waste the shared physical basis; a latent consensus can remove that tax",
            "strongest_failure": "solid Zstd already approximates the common latent source closely enough that explicit edit programs add more bytes/work than they save",
            "disproof": "optimistic latent+patch payload floor is >= exact solid Zstd-19 bytes",
        },
        "contract": {
            "benchmark_identity_used_in_representation": False,
            "pivot_selection": "minimum logical-content SHA-256",
            "latent_selection": f"pivot bytes copied by at least {MIN_SUPPORT} other members",
            "delta_primitive": "existing bounded cmpct.resemblance rolling COPY/LITERAL",
            "max_chain_depth": 1,
            "creation_prices_consensus_derivation_and_second_pass_patches": True,
            "release_credit": False,
        },
        "workload": {"files": len(rows), "tree_sha256": expected_tree, "logical_bytes": sum(len(d) for _, d in rows)},
        "derivation": derivation,
        "candidate": {
            "latent_logical_bytes": len(latent),
            "latent_stored_bytes": len(latent_stored),
            "patch_raw_bytes": total_raw_patch,
            "patch_stored_bytes": total_stored_patch,
            "payload_floor_bytes": payload_floor,
            "archive_bytes": len(artifact),
            "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
            "create_seconds": create_s,
            "copied_bytes": total_copy,
            "literal_bytes": total_literal,
            "tree_verified": True,
            "max_chain_depth": 1,
            "max_decode_unit_bytes": max(len(latent), max_logical),
            "max_member_read_amplification": max_amp,
        },
        "comparators": {"zip_deflate9": zip_row, "tar_zstd19_solid": zstd_row},
        "decision": {
            "payload_floor_zstd_gap_bytes": payload_floor - int(zstd_row["bytes"]),
            "archive_zstd_gap_bytes": len(artifact) - int(zstd_row["bytes"]),
            "strict_four_way_win": strict,
            "terminal": "PROMOTE_NEXT_PREREQUISITE" if strict else ("ESCALATE_RADICALITY" if payload_floor < int(zstd_row["bytes"]) else "RETIRE_FAMILY"),
            "release_credit": False,
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
