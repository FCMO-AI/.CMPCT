from __future__ import annotations

"""R4 Shifted oracle: locality-bounded cluster-owned solid packs.

Member-to-member raw-prefix forests have now exposed the root-cost problem directly:
cheap pairwise edges exist, but acyclicity forces expensive full-member roots. This
oracle changes the physical owner. A bounded cluster is one independently compressed
Zstd-19 payload containing the raw bytes of several members; metadata owns exact
member offsets, sizes and hashes. Reading one member decodes only its cluster.

Clusters are built by a content-agnostic greedy merge tournament. At every step we
measure every admissible pair of current clusters and commit the merge with the
largest exact compressed-payload saving. A merge is admissible only when the decoded
cluster is <=8 MiB and its decoded-context amplification is <=8x for every member.
The tournament stops when no merge saves payload bytes. This is an R4 capacity oracle,
not a production selector; construction cost is diagnostic and grants no release
credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import msgpack
import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_prefixgraph_two_anchor_representation_oracle as BASE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

TARGET = BASE.TARGET
MAX_CLUSTER_RAW = 8 * 1024 * 1024
MAX_READ_AMPLIFICATION = 8.0
MAGIC = b"CMPNXCP\0"
TAIL = b"CMPNXCPT"


def _cluster_raw(indices: tuple[int, ...], raws: list[bytes]) -> bytes:
    return b"".join(raws[i] for i in indices)


def _admissible(indices: tuple[int, ...], raws: list[bytes]) -> bool:
    total = sum(len(raws[i]) for i in indices)
    if total > MAX_CLUSTER_RAW:
        return False
    return all(total / max(1, len(raws[i])) <= MAX_READ_AMPLIFICATION for i in indices)


def _compress(indices: tuple[int, ...], raws: list[bytes]) -> bytes:
    return zstd.ZstdCompressor(level=19).compress(_cluster_raw(indices, raws))


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
    if not raws or any(len(raw) > MAX_CLUSTER_RAW for raw in raws):
        raise RuntimeError("Shifted stage is outside cluster-pack decode-unit envelope")
    expected_tree = PG._treehash_parts(rels, raws)

    clusters: list[tuple[int, ...]] = [(i,) for i in range(len(raws))]
    payloads: dict[tuple[int, ...], bytes] = {c: _compress(c, raws) for c in clusters}
    evaluated_merges = 0
    committed_merges = []
    while True:
        best = None
        for li, left in enumerate(clusters):
            for right in clusters[li + 1:]:
                merged = tuple(sorted(left + right))
                if not _admissible(merged, raws):
                    continue
                payload = payloads.get(merged)
                if payload is None:
                    payload = _compress(merged, raws)
                    payloads[merged] = payload
                evaluated_merges += 1
                saving = len(payloads[left]) + len(payloads[right]) - len(payload)
                key = (saving, tuple(-i for i in merged))
                if saving > 0 and (best is None or key > best[0]):
                    best = (key, left, right, merged, payload)
        if best is None:
            break
        _key, left, right, merged, payload = best
        clusters.remove(left); clusters.remove(right); clusters.append(merged); clusters.sort()
        payloads[merged] = payload
        committed_merges.append({"left": list(left), "right": list(right), "merged": list(merged), "payload_saving_bytes": int(_key[0])})

    cluster_payloads = [payloads[c] for c in clusters]
    member_rows = []
    max_amp = 0.0
    for cid, cluster in enumerate(clusters):
        offset = 0
        cluster_raw_bytes = sum(len(raws[i]) for i in cluster)
        for i in cluster:
            amp = cluster_raw_bytes / max(1, len(raws[i]))
            max_amp = max(max_amp, amp)
            member_rows.append([i, cid, offset, len(raws[i]), PG.H(raws[i])])
            offset += len(raws[i])
    member_rows.sort(key=lambda row: row[0])
    meta = {
        "v": 1,
        "engine": "cluster-owned-zstd19-v1",
        "tree_sha256": expected_tree,
        "files": rels,
        "clusters": [list(c) for c in clusters],
        "members": member_rows,
        "max_cluster_raw_bytes": MAX_CLUSTER_RAW,
        "max_read_amplification": MAX_READ_AMPLIFICATION,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > PG.MAX_META_BYTES:
        raise RuntimeError("cluster-pack metadata exceeds decode-unit ceiling")
    meta_comp = zstd.ZstdCompressor(level=PG.META_LEVEL).compress(meta_raw)
    header = PG.HEADER.pack(MAGIC, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    footer = PG.FOOTER.pack(TAIL, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    blob = header + meta_comp + b"".join(cluster_payloads) + meta_comp + footer

    # Independent reconstruction from cluster payloads and metadata.
    decoded_clusters = []
    for cluster, payload in zip(clusters, cluster_payloads, strict=True):
        expected_size = sum(len(raws[i]) for i in cluster)
        decoded_clusters.append(zstd.ZstdDecompressor().decompress(payload, max_output_size=expected_size))
    verified_raws = []
    for i, cid, offset, size, digest in member_rows:
        raw = decoded_clusters[cid][offset:offset + size]
        if len(raw) != size or PG.H(raw) != bytes(digest):
            raise RuntimeError("cluster-pack member reconstruction failed")
        verified_raws.append(raw)
    if PG._treehash_parts(rels, verified_raws) != expected_tree:
        raise RuntimeError("cluster-pack changed logical tree")

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)
    ext_parent = work_root / "external"; ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-extracted")
    zstd_work = work_root / "zstd-work"; zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(normalized, work_root / "shifted.tar.zst", work_root / "zstd-extracted", zstd_work)
    source_tree = EXT._tree(normalized)
    EXT._verify_extracted(work_root / "zip-extracted", source_tree, "ZIP")
    if not zstd_row.get("available"):
        raise RuntimeError("Zstd-19 comparator unavailable")
    EXT._verify_extracted(work_root / "zstd-extracted", source_tree, "Zstd-19")
    zstd_bytes = int(zstd_row["archive_bytes"])
    strict_size_win = len(blob) < int(zip_row["archive_bytes"]) and len(blob) < zstd_bytes
    gap_before = shipping.stat().st_size - zstd_bytes
    gap_after = len(blob) - zstd_bytes
    gap_closure = (gap_before - max(gap_after, 0)) / max(gap_before, 1)
    decision = "PROMOTE_NEXT_PREREQUISITE" if strict_size_win else ("ITERATE_SAME_FAMILY" if gap_closure >= 0.25 else "ESCALATE_RADICALITY")

    return {
        "schema": "cmpct-v030-shifted-cluster-owned-pack-oracle-v1",
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "files": len(raws),
        "cluster_count": len(clusters),
        "clusters": [list(c) for c in clusters],
        "committed_merges": committed_merges,
        "evaluated_merges": evaluated_merges,
        "max_cluster_raw_bytes": max(sum(len(raws[i]) for i in c) for c in clusters),
        "max_decoded_context_amplification": max_amp,
        "within_decode_unit": all(sum(len(raws[i]) for i in c) <= MAX_CLUSTER_RAW for c in clusters),
        "within_locality_amplification": max_amp <= MAX_READ_AMPLIFICATION,
        "shipping_prefixgraph_bytes": shipping.stat().st_size,
        "shipping_prefixgraph_sha256": hashlib.sha256(shipping.read_bytes()).hexdigest(),
        "cluster_pack_bytes": len(blob),
        "cluster_pack_sha256": hashlib.sha256(blob).hexdigest(),
        "payload_bytes": sum(map(len, cluster_payloads)),
        "meta_raw_bytes": len(meta_raw),
        "meta_comp_bytes": len(meta_comp),
        "saving_vs_shipping_prefixgraph_bytes": shipping.stat().st_size - len(blob),
        "zip_bytes": int(zip_row["archive_bytes"]),
        "zstd19_bytes": zstd_bytes,
        "margin_vs_zstd19_bytes": zstd_bytes - len(blob),
        "strict_size_win_vs_zip_and_zstd19": strict_size_win,
        "gap_closure_fraction": gap_closure,
        "tree_sha256": expected_tree,
        "verified_tree_sha256": PG._treehash_parts(rels, verified_raws),
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "product_create_time_claim": False,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "active_saturation": ["S2", "S3", "S4"],
            "research_priority_score": 95,
            "measured_gap_change_bytes": shipping.stat().st_size - len(blob),
            "strongest_self_critique": "Solid cluster ownership may recover cyclic resemblance but can export creation cost and selective-read decode work; the <=8 MiB/<=8x bounds must survive a fast generic selector before promotion.",
            "terminal_decision": decision,
            "next_decisive_test": ("build a bounded single-pass structural cluster admission and measure full creation time" if strict_size_win else "change the physical owner again if bounded cluster packs fail to close a material fraction of the Zstd gap"),
        },
        "decision": decision,
        "claim_boundary": "R4 representation-capacity oracle only; greedy merge search is diagnostic and grants zero release credit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shifted-cluster-owned-pack-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shifted-cluster-owned-pack.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
