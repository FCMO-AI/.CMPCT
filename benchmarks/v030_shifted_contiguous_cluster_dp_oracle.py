from __future__ import annotations

"""R4 Shifted capacity oracle: exact optimal contiguous locality-bounded solid clusters.

The existing greedy cluster-owned oracle asks whether jointly owned physical roots can recover the
cross-version redundancy that member-root PrefixGraph loses.  Greedy pair merging is not an exact
optimizer, so a negative there cannot retire the representation family.  This instrument closes that
loophole for the important content-agnostic case where members are kept in deterministic lexical order:
it compresses every admissible contiguous interval once and uses dynamic programming to find the exact
minimum total payload under the frozen <=8 MiB decode-unit and <=8x member-read amplification laws.

The experiment is deliberately a size-capacity oracle.  It prices all interval compression work and emits
an exact complete artifact/tree proof, but grants no creation-time or release credit.  If even this exact
optimum is not below solid Zstd-19, metadata shaving and search tuning cannot rescue contiguous
cluster-owned Zstd-19 roots; that scope is terminal negative evidence.  A size win advances only to a
bounded construction/admission timing prerequisite.
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

    # Compress every admissible lexical interval exactly once.  dp[j] is the minimum compressed
    # payload bytes for members [0:j].  Ties prefer fewer clusters, then the earlier predecessor,
    # making the complete artifact deterministic without benchmark identity.
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

    inf = 1 << 62
    dp: list[tuple[int, int, int] | None] = [None] * (n + 1)
    dp[0] = (0, 0, -1)  # payload bytes, cluster count, predecessor
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
        if best is None or best[0] >= inf:
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
        "members": member_rows,
        "max_cluster_raw_bytes": CLUSTER.MAX_CLUSTER_RAW,
        "max_read_amplification": CLUSTER.MAX_READ_AMPLIFICATION,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = zstd.ZstdCompressor(level=PG.META_LEVEL).compress(meta_raw)
    header = PG.HEADER.pack(MAGIC, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    footer = PG.FOOTER.pack(TAIL, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    artifact = header + meta_comp + b"".join(payloads) + meta_comp + footer

    # Independent reconstruction from the selected DP partition.
    decoded: list[bytes] = [b""] * n
    for cid, ((begin, end), payload) in enumerate(zip(clusters, payloads, strict=True)):
        expected_size = sum(len(raws[i]) for i in range(begin, end))
        cluster_raw = zstd.ZstdDecompressor().decompress(payload, max_output_size=expected_size)
        off = 0
        for i in range(begin, end):
            size = len(raws[i])
            raw = cluster_raw[off:off + size]
            if len(raw) != size or PG.H(raw) != PG.H(raws[i]):
                raise RuntimeError(f"DP cluster reconstruction failed for member {i}")
            decoded[i] = raw
            off += size
        if off != len(cluster_raw):
            raise RuntimeError(f"DP cluster {cid} has trailing decoded bytes")
    verified_tree = PG._treehash_parts(rels, decoded)
    if verified_tree != expected_tree:
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
        # Exact contiguous optimum improved shipping but still missed Zstd: contiguous cluster ownership
        # is exhausted, while non-contiguous content-derived grouping remains a distinct R4 family.
        decision = "ESCALATE_RADICALITY"

    return {
        "schema": "cmpct-v030-shifted-contiguous-cluster-dp-oracle-v1",
        "source_commit": _source_commit(),
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "files": n,
        "source_bytes": sum(map(len, raws)),
        "tree_sha256": expected_tree,
        "verified_tree_sha256": verified_tree,
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
        "claim_boundary": "R4 exact contiguous-partition capacity oracle only; all admissible interval compression work is priced, but no creation-time or release credit is claimed.",
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
