from __future__ import annotations

"""R4 Shifted capacity oracle: exact optimal contiguous locality-bounded solid clusters.

The existing greedy cluster-owned oracle asks whether jointly owned physical roots can recover the
cross-version redundancy that member-root PrefixGraph loses. Greedy pair merging is not an exact optimizer,
so a negative there cannot retire the representation family. This instrument closes that loophole for the
important content-agnostic case where members are kept in deterministic lexical order: it compresses every
admissible contiguous interval once and uses dynamic programming to find the exact minimum total payload
under the frozen <=8 MiB decode-unit and <=8x member-read amplification laws.

The experiment is deliberately a size-capacity oracle. It prices all interval compression work and emits a
self-describing complete artifact whose authenticated metadata includes every payload boundary. Verification
reparses only those artifact bytes and reconstructs the logical tree independently. It grants no creation-time
or release credit. If even this exact optimum is not below solid Zstd-19, metadata shaving and search tuning
cannot rescue contiguous cluster-owned Zstd-19 roots; that scope is terminal negative evidence.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time

import msgpack
import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_shifted_cluster_owned_pack_oracle as CLUSTER
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

MAGIC = b"CMPNXDP\0"
TAIL = b"CMPNXDPT"
TARGET = CLUSTER.TARGET


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _verify_artifact(artifact: bytes) -> tuple[list[str], list[bytes], dict]:
    """Parse and reconstruct only from emitted bytes; no builder-side payload list is trusted."""
    if len(artifact) < PG.HEADER.size + PG.FOOTER.size:
        raise RuntimeError("truncated DP cluster artifact")
    magic, meta_comp_len, meta_raw_len, meta_sha = PG.HEADER.unpack_from(artifact, 0)
    if magic != MAGIC or meta_raw_len > PG.MAX_META_BYTES:
        raise RuntimeError("invalid DP cluster header")
    meta_start = PG.HEADER.size
    meta_end = meta_start + meta_comp_len
    if meta_end > len(artifact) - PG.FOOTER.size:
        raise RuntimeError("truncated DP cluster metadata")
    meta_comp = artifact[meta_start:meta_end]
    meta_raw = zstd.ZstdDecompressor().decompress(meta_comp, max_output_size=meta_raw_len)
    if len(meta_raw) != meta_raw_len or PG.H(meta_raw) != meta_sha:
        raise RuntimeError("DP cluster metadata authentication failed")
    meta = msgpack.unpackb(meta_raw, raw=False)
    if meta.get("v") != 1 or meta.get("engine") != "contiguous-cluster-zstd19-dp-v1":
        raise RuntimeError("unsupported DP cluster metadata")
    rels = meta.get("files")
    clusters = meta.get("clusters")
    members = meta.get("members")
    payload_sizes = meta.get("payload_sizes")
    if not isinstance(rels, list) or not isinstance(clusters, list) or not isinstance(members, list):
        raise RuntimeError("invalid DP cluster metadata tables")
    if not isinstance(payload_sizes, list) or len(payload_sizes) != len(clusters):
        raise RuntimeError("invalid DP cluster payload boundary table")

    tail_meta_start = len(artifact) - PG.FOOTER.size - meta_comp_len
    if tail_meta_start < meta_end:
        raise RuntimeError("overlapping DP cluster payload/metadata regions")
    tail_magic, tail_comp_len, tail_raw_len, tail_sha = PG.FOOTER.unpack_from(artifact, len(artifact) - PG.FOOTER.size)
    if tail_magic != TAIL or tail_comp_len != meta_comp_len or tail_raw_len != meta_raw_len or tail_sha != meta_sha:
        raise RuntimeError("DP cluster footer authentication mismatch")
    if artifact[tail_meta_start:tail_meta_start + meta_comp_len] != meta_comp:
        raise RuntimeError("DP cluster redundant metadata mismatch")

    payload_region = memoryview(artifact)[meta_end:tail_meta_start]
    payloads: list[bytes] = []
    off = 0
    for raw_size in payload_sizes:
        size = int(raw_size)
        if size <= 0 or off + size > len(payload_region):
            raise RuntimeError("invalid DP cluster payload boundary")
        payloads.append(bytes(payload_region[off:off + size]))
        off += size
    if off != len(payload_region):
        raise RuntimeError("trailing DP cluster payload bytes")

    decoded_clusters: list[bytes] = []
    for cid, (bounds, payload) in enumerate(zip(clusters, payloads, strict=True)):
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise RuntimeError("invalid DP cluster bounds")
        begin, end = map(int, bounds)
        if not (0 <= begin < end <= len(rels)):
            raise RuntimeError("out-of-range DP cluster bounds")
        expected_size = 0
        for row in members:
            if int(row[1]) == cid:
                expected_size = max(expected_size, int(row[2]) + int(row[3]))
        if expected_size > CLUSTER.MAX_CLUSTER_RAW:
            raise RuntimeError("DP cluster exceeds decode-unit ceiling")
        decoded_clusters.append(zstd.ZstdDecompressor().decompress(payload, max_output_size=expected_size))
        if len(decoded_clusters[-1]) != expected_size:
            raise RuntimeError("DP cluster decoded-size mismatch")

    decoded: list[bytes | None] = [None] * len(rels)
    for row in members:
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("invalid DP member row")
        i, cid, offset, size = map(int, row[:4])
        digest = bytes(row[4])
        if not (0 <= i < len(rels) and 0 <= cid < len(decoded_clusters) and size >= 0 and offset >= 0):
            raise RuntimeError("invalid DP member coordinates")
        cluster_raw = decoded_clusters[cid]
        raw = cluster_raw[offset:offset + size]
        if len(raw) != size or PG.H(raw) != digest:
            raise RuntimeError(f"DP cluster member integrity failed: {i}")
        if decoded[i] is not None:
            raise RuntimeError("duplicate DP member identity")
        decoded[i] = raw
    if any(raw is None for raw in decoded):
        raise RuntimeError("missing DP cluster member")
    return [str(rel) for rel in rels], [bytes(raw) for raw in decoded if raw is not None], meta


def run(work_root: Path) -> dict:
    started = time.perf_counter()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    staged = work_root / "r25-stage"
    CANON._prepare_profile_tree(source, staged)
    files = sorted(path for path in staged.rglob("*") if path.is_file())
    rels = [path.relative_to(staged).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if not raws:
        raise RuntimeError("Shifted DP oracle requires regular files")
    if any(len(raw) > CLUSTER.MAX_CLUSTER_RAW for raw in raws):
        raise RuntimeError("member exceeds frozen decode-unit ceiling")
    expected_tree = PG._treehash_parts(rels, raws)

    interval_payloads: dict[tuple[int, int], bytes] = {}
    compression_calls = 0
    trial_raw_bytes = 0
    compression_seconds = 0.0
    n = len(raws)
    for i in range(n):
        indices: list[int] = []
        for j in range(i, n):
            indices.append(j)
            key = tuple(indices)
            if not CLUSTER._admissible(key, raws):
                break
            raw = CLUSTER._cluster_raw(key, raws)
            t0 = time.perf_counter()
            payload = zstd.ZstdCompressor(level=19).compress(raw)
            compression_seconds += time.perf_counter() - t0
            interval_payloads[(i, j + 1)] = payload
            compression_calls += 1
            trial_raw_bytes += len(raw)

    dp: list[tuple[int, int, int] | None] = [None] * (n + 1)
    dp[0] = (0, 0, -1)
    for end in range(1, n + 1):
        best: tuple[int, int, int] | None = None
        for begin in range(end):
            payload = interval_payloads.get((begin, end))
            prev = dp[begin]
            if payload is None or prev is None:
                continue
            candidate = (prev[0] + len(payload), prev[1] + 1, begin)
            if best is None or candidate < best:
                best = candidate
        if best is None:
            raise RuntimeError(f"no admissible contiguous partition reaches member {end}")
        dp[end] = best

    clusters_rev: list[tuple[int, int]] = []
    cursor = n
    while cursor:
        row = dp[cursor]
        if row is None or row[2] < 0:
            raise RuntimeError("broken DP predecessor chain")
        begin = row[2]
        clusters_rev.append((begin, cursor))
        cursor = begin
    clusters = list(reversed(clusters_rev))
    payloads = [interval_payloads[c] for c in clusters]

    member_rows = []
    max_amp = 0.0
    max_cluster_raw = 0
    for cid, (begin, end) in enumerate(clusters):
        cluster_raw = sum(len(raws[i]) for i in range(begin, end))
        max_cluster_raw = max(max_cluster_raw, cluster_raw)
        offset = 0
        for i in range(begin, end):
            amp = cluster_raw / max(1, len(raws[i]))
            max_amp = max(max_amp, amp)
            member_rows.append([i, cid, offset, len(raws[i]), PG.H(raws[i])])
            offset += len(raws[i])

    meta = {
        "v": 1,
        "engine": "contiguous-cluster-zstd19-dp-v1",
        "tree_sha256": expected_tree,
        "files": rels,
        "clusters": [[begin, end] for begin, end in clusters],
        "payload_sizes": [len(payload) for payload in payloads],
        "members": member_rows,
        "max_cluster_raw_bytes": CLUSTER.MAX_CLUSTER_RAW,
        "max_read_amplification": CLUSTER.MAX_READ_AMPLIFICATION,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > PG.MAX_META_BYTES:
        raise RuntimeError("DP cluster metadata exceeds decode-unit ceiling")
    meta_comp = zstd.ZstdCompressor(level=PG.META_LEVEL).compress(meta_raw)
    header = PG.HEADER.pack(MAGIC, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    footer = PG.FOOTER.pack(TAIL, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    artifact = header + meta_comp + b"".join(payloads) + meta_comp + footer

    verified_rels, verified_raws, parsed_meta = _verify_artifact(artifact)
    if verified_rels != rels:
        raise RuntimeError("DP artifact path table changed during parse")
    verified_tree = PG._treehash_parts(verified_rels, verified_raws)
    if verified_tree != expected_tree or bytes(parsed_meta["tree_sha256"]) != expected_tree:
        raise RuntimeError("DP cluster artifact changed logical tree")

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)
    ext_parent = work_root / "external"; ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-out")
    zstd_work = work_root / "zstd-work"; zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(normalized, work_root / "shifted.tar.zst", work_root / "zstd-out", zstd_work)
    if not zstd_row.get("available"):
        raise RuntimeError("solid Zstd-19 comparator unavailable")
    zstd_bytes = int(zstd_row["archive_bytes"])
    zip_bytes = int(zip_row["archive_bytes"])
    shipping_bytes = shipping.stat().st_size
    archive_bytes = len(artifact)
    strict_size_win = archive_bytes < zstd_bytes and archive_bytes < zip_bytes
    gap_before = shipping_bytes - zstd_bytes
    gap_after = archive_bytes - zstd_bytes
    gap_change = shipping_bytes - archive_bytes
    if strict_size_win:
        decision = "PROMOTE_NEXT_PREREQUISITE"
    elif gap_after >= gap_before:
        decision = "RETIRE_FAMILY"
    else:
        decision = "ESCALATE_RADICALITY"

    return {
        "schema": "cmpct-v030-shifted-contiguous-cluster-dp-oracle-v2",
        "source_commit": _source_commit(),
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "files": n,
        "source_bytes": sum(map(len, raws)),
        "tree_sha256": expected_tree,
        "verified_tree_sha256": verified_tree,
        "artifact_reparsed_from_bytes": True,
        "payload_boundaries_authenticated": True,
        "intervals_compressed": compression_calls,
        "trial_raw_bytes": trial_raw_bytes,
        "search_work_amplification_vs_source": trial_raw_bytes / max(1, sum(map(len, raws))),
        "zstd19_compression_seconds": compression_seconds,
        "cluster_count": len(clusters),
        "clusters": [[begin, end] for begin, end in clusters],
        "max_cluster_raw_bytes": max_cluster_raw,
        "max_decoded_context_amplification": max_amp,
        "within_decode_unit": max_cluster_raw <= CLUSTER.MAX_CLUSTER_RAW,
        "within_locality_amplification": max_amp <= CLUSTER.MAX_READ_AMPLIFICATION,
        "payload_bytes": sum(map(len, payloads)),
        "meta_raw_bytes": len(meta_raw),
        "meta_comp_bytes": len(meta_comp),
        "archive_bytes": archive_bytes,
        "archive_sha256": hashlib.sha256(artifact).hexdigest(),
        "shipping_prefixgraph_bytes": shipping_bytes,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "gap_before_vs_zstd19_bytes": gap_before,
        "gap_after_vs_zstd19_bytes": gap_after,
        "measured_gap_change_bytes": gap_change,
        "strict_size_win_vs_zip_and_zstd19": strict_size_win,
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "product_create_time_claim": False,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster to create than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "active_saturation": ["S2", "S3", "S4"],
            "research_priority_score": 97,
            "measured_gap_change_bytes": gap_change,
            "strongest_self_critique": "Lexical contiguity is content-agnostic and exact within its scope, but it may separate structurally related members that a bounded content-derived clustering law would place together; failure retires contiguous cluster ownership, not every possible jointly owned representation.",
            "terminal_decision": decision,
            "next_decisive_test": ("replace the exact DP capacity search with bounded structural admission and measure complete creation time" if strict_size_win else "if size still misses, use the exact gap to decide whether non-contiguous content-derived ownership has enough plausible headroom before another R4 build"),
        },
        "decision": decision,
        "claim_boundary": "R4 exact contiguous-partition capacity oracle only; every admissible interval is compressed and the emitted artifact is reparsed independently, but no creation-time or release credit is claimed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
