from __future__ import annotations

"""Fresh-process PrefixGraph RSS phase worker.

Research-only: compare the immutable direct-payload floor with the complete shipping PrefixGraph builder. The floor
uses the same sorted files, raw bytes, direct Zstd payloads, tree identity and historical all-direct serializer as
the product. It changes no selector or production path and exists only to identify which phase owns Shifted RSS.

RSS is sampled immediately after construction and before strong verification. Verification remains mandatory, but
its allocations are reported separately so reader/materialization cost cannot be mistaken for builder peak RSS.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

from experiments import entropygraph_v030_prefixgraph as BASE
from experiments import entropygraph_v030_prefixgraph_parallel as PG


def rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def direct_floor(root: Path, out: Path) -> dict:
    files = sorted(path for path in root.rglob('*') if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    expected_tree = BASE._treehash_parts(rels, raws)
    direct_payloads = [BASE._compress(raw) for raw in raws]
    blob, stats = BASE._serialize_candidate(rels, raws, direct_payloads, expected_tree, None)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    return {
        'tree_sha256': expected_tree,
        'archive_bytes': len(blob),
        'archive_sha256': sha256_file(out),
        'files': len(files),
        'logical_bytes': sum(map(len, raws)),
        'prefix_records': int(stats.get('prefix_records', 0)),
    }


def full(root: Path, out: Path) -> dict:
    expected_tree = PG.treehash(root)
    stats = PG.build(root, out)
    return {
        'tree_sha256': expected_tree,
        'archive_bytes': out.stat().st_size,
        'archive_sha256': sha256_file(out),
        'files': int(stats['files']),
        'logical_bytes': int(stats['logical_bytes']),
        'prefix_records': int(stats.get('prefix_records', 0)),
        'anchor_auditions': int(stats.get('anchor_auditions', 0)),
        'anchor_audition_workers': int(stats.get('anchor_audition_workers', 0)),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=('direct-floor', 'full'), required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    args = p.parse_args()

    baseline_peak = rss_kib()
    build_started = time.perf_counter()
    result = direct_floor(args.source, args.archive) if args.mode == 'direct-floor' else full(args.source, args.archive)
    build_wall = time.perf_counter() - build_started
    build_peak = rss_kib()

    verify_started = time.perf_counter()
    verify = BASE.strong_verify(args.archive)
    verify_wall = time.perf_counter() - verify_started
    if not verify.get('ok') or verify.get('tree_sha256') != result['tree_sha256']:
        raise RuntimeError(f'{args.mode} failed exact post-measurement verification: {verify!r}')
    post_verify_peak = rss_kib()
    incremental_build_peak = max(0, build_peak - baseline_peak)

    print(json.dumps({
        'mode': args.mode,
        **result,
        'baseline_peak_rss_kib': baseline_peak,
        'build_peak_rss_kib': build_peak,
        'incremental_build_peak_rss_kib': incremental_build_peak,
        'build_wall_s': build_wall,
        'post_verify_peak_rss_kib': post_verify_peak,
        'verify_wall_s': verify_wall,
        'strong_verify_ok': True,
        'rss_measurement_boundary': 'build-before-strong-verify-v2',
        # Compatibility aliases for the first oracle revision. These intentionally mean build-only metrics now.
        'peak_rss_kib': build_peak,
        'incremental_peak_rss_kib': incremental_build_peak,
        'wall_s': build_wall,
    }, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
