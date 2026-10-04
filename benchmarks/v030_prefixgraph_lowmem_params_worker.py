from __future__ import annotations

"""Fresh-process PrefixGraph compression-table Pareto worker.

Research only.  The direct Zstd-19 floor, anchor nomination, complete archive tournament, serializer, reader and
integrity law stay unchanged.  Candidate arms reduce only Zstd's prefix-compression match-table logs relative to
the level-19 defaults.  Bytes are allowed to differ in this oracle and receive zero release credit; the purpose is
to measure the exact size/speed/RSS Pareto frontier before any product proposal exists.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import zstandard as zstd

from experiments import entropygraph_v030_prefixgraph as BASE
from experiments import entropygraph_v030_prefixgraph_parallel as PG

ARMS: dict[str, tuple[int, int]] = {
    "baseline": (0, 0),
    "chain-m1": (-1, 0),
    "chain-m2": (-2, 0),
    "hash-m1": (0, -1),
    "chain-m1-hash-m1": (-1, -1),
    "chain-m2-hash-m1": (-2, -1),
}


def rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def install_arm(arm: str) -> dict:
    chain_delta, hash_delta = ARMS[arm]
    defaults = zstd.ZstdCompressionParameters.from_level(BASE.PAYLOAD_LEVEL)
    effective = {
        "window_log": int(defaults.window_log),
        "chain_log": max(6, int(defaults.chain_log) + chain_delta),
        "hash_log": max(6, int(defaults.hash_log) + hash_delta),
        "search_log": int(defaults.search_log),
        "min_match": int(defaults.min_match),
        "target_length": int(defaults.target_length),
        "strategy": int(defaults.strategy),
    }
    if arm == "baseline":
        return {"defaults": effective, "effective": effective, "patched": False}

    def lowmem_prefix_codec(prefix: bytes):
        dictionary = zstd.ZstdCompressionDict(prefix, dict_type=zstd.DICT_TYPE_RAWCONTENT)
        params = zstd.ZstdCompressionParameters.from_level(
            BASE.PAYLOAD_LEVEL,
            chain_log=effective["chain_log"],
            hash_log=effective["hash_log"],
        )
        compressor = zstd.ZstdCompressor(compression_params=params, dict_data=dictionary)
        return compressor, dictionary

    BASE._prefix_codec = lowmem_prefix_codec
    return {
        "defaults": {
            "window_log": int(defaults.window_log),
            "chain_log": int(defaults.chain_log),
            "hash_log": int(defaults.hash_log),
            "search_log": int(defaults.search_log),
            "min_match": int(defaults.min_match),
            "target_length": int(defaults.target_length),
            "strategy": int(defaults.strategy),
        },
        "effective": effective,
        "patched": True,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=tuple(ARMS), required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    args = p.parse_args()

    params = install_arm(args.arm)
    expected_tree = PG.treehash(args.source)
    baseline_peak = rss_kib()
    started = time.perf_counter()
    stats = PG.build(args.source, args.archive)
    build_s = time.perf_counter() - started
    build_peak = rss_kib()

    verify = BASE.strong_verify(args.archive)
    if not verify.get("ok") or verify.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{args.arm} failed exact tree verification: {verify!r}")

    print(json.dumps({
        "arm": args.arm,
        "params": params,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": sha256_file(args.archive),
        "tree_sha256": expected_tree,
        "prefix_records": int(stats.get("prefix_records", 0)),
        "anchor": stats.get("anchor"),
        "anchor_auditions": int(stats.get("anchor_auditions", 0)),
        "anchor_audition_workers": int(stats.get("anchor_audition_workers", 0)),
        "build_s": build_s,
        "baseline_peak_rss_kib": baseline_peak,
        "build_peak_rss_kib": build_peak,
        "incremental_build_peak_rss_kib": max(0, build_peak - baseline_peak),
        "strong_verify_ok": True,
        "release_credit": False,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
