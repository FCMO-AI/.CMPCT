#!/usr/bin/env python3
"""Exact-source r24 sparse extraction SHA-cost attribution, not a release benchmark.

The only dynamic instrumentation is a module-local hashlib shim that forwards
EVERY update to the real OpenSSL SHA-256 implementation without byte changes.
Only constructed synthetic fixtures are read/written, under TemporaryDirectory.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import resource
import statistics
import tempfile
import time
import types

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_SPARSE
from cmpct import sparse_extract

MIB = 1024 * 1024
SEED = 0xC0DEC7


def digest_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb', buffering=0) as stream:
        while True:
            b = stream.read(2 * MIB)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def make_input(path: Path, logical_mib: int, offsets_mib: tuple[int, ...]):
    rng = random.Random(SEED + logical_mib + sum(offsets_mib))
    with path.open('wb') as f:
        f.truncate(logical_mib * MIB)
        for offset_mib in offsets_mib:
            f.seek(offset_mib * MIB)
            f.write(rng.randbytes(MIB))
    s = path.stat()
    return {"logical_bytes": s.st_size, "physical_bytes_st_blocks": s.st_blocks * 512}


class TimedDigest:
    def __init__(self, original_factory, slab):
        self.real = original_factory()
        self.slab = slab
        self.stats = {
            "hole": {"calls": 0, "bytes": 0, "wall_ns": 0, "cpu_ns": 0},
            "data": {"calls": 0, "bytes": 0, "wall_ns": 0, "cpu_ns": 0},
        }

    def update(self, b):
        # A pointer-identity test, NOT a test for zero byte *values*:
        # genuine stored extents may themselves happen to contain zeros.
        hole = isinstance(b, memoryview) and b.obj is self.slab
        kind = 'hole' if hole else 'data'
        start_wall = time.perf_counter_ns()
        start_cpu = time.process_time_ns()
        self.real.update(b)
        dt_cpu = time.process_time_ns() - start_cpu
        dt_wall = time.perf_counter_ns() - start_wall
        st = self.stats[kind]
        st['calls'] += 1
        st['bytes'] += len(b)
        st['cpu_ns'] += dt_cpu
        st['wall_ns'] += dt_wall

    def digest(self):
        return self.real.digest()


def measure(archive: Path, expected_sha: str, output: Path, instrumentation: bool):
    output.mkdir()
    row_name = 'disk.img'
    with CMPCT(archive) as reader:
        row = reader.by[row_name]
        assert row[6][0] == S_SPARSE, f'not genuine S_SPARSE: {row[6][0]}'
        assert row[4] > 0 and row[5].hex() == expected_sha
        data_bytes = sum(int(ext[1]) for ext in row[6][1])
        expected_holes = row[4] - data_bytes
        assert data_bytes >= MIB and expected_holes > 0

        real_hashlib = sparse_extract.hashlib
        meter = None
        if instrumentation:
            meter = TimedDigest(real_hashlib.sha256, sparse_extract._ZERO)
            # Keep the shim confined to the sparse_extract module. Replacing the
            # global hashlib.sha256 would pollute unrelated Reader hashing.
            sparse_extract.hashlib = types.SimpleNamespace(sha256=lambda: meter)
        try:
            start_wall = time.perf_counter_ns()
            start_cpu = time.process_time_ns()
            reader.extractall(output, metadata=False)
            duration_cpu_ns = time.process_time_ns() - start_cpu
            duration_wall_ns = time.perf_counter_ns() - start_wall
        finally:
            sparse_extract.hashlib = real_hashlib

    restored = output / row_name
    assert restored.stat().st_size == row[4]
    assert digest_path(restored) == expected_sha, 'independent full output SHA mismatch'
    assert not list(output.glob('.cmpct-part-*')), 'stale temporary stage'
    output_s = restored.stat()
    assert output_s.st_blocks * 512 < row[4] // 2, 'physical sparse-hole property lost'

    report = {
        "instrumented": instrumentation,
        "total_wall_ns": duration_wall_ns,
        "total_cpu_ns": duration_cpu_ns,
        "logical_bytes": row[4],
        "expected_hole_bytes": expected_holes,
        "expected_data_bytes": data_bytes,
        "restored_physical_bytes_st_blocks": output_s.st_blocks * 512,
    }
    if meter is not None:
        st = meter.stats
        assert st['hole']['bytes'] == expected_holes, (st['hole']['bytes'], expected_holes)
        assert st['data']['bytes'] == data_bytes, (st['data']['bytes'], data_bytes)
        assert sum(v['bytes'] for v in st.values()) == row[4]
        assert meter.digest() == bytes(row[5])
        report['sha_update'] = st
        report['hole_wall_share'] = st['hole']['wall_ns'] / duration_wall_ns
        report['hole_cpu_share'] = st['hole']['cpu_ns'] / duration_cpu_ns
        report['all_sha_wall_share'] = sum(v['wall_ns'] for v in st.values()) / duration_wall_ns
        report['all_sha_cpu_share'] = sum(v['cpu_ns'] for v in st.values()) / duration_cpu_ns
    return report


def one_case(root: Path, name: str, logical_mib: int, offsets_mib: tuple[int, ...]):
    case = root / name
    src = case / 'src'
    src.mkdir(parents=True)
    inp = src / 'disk.img'
    input_stat = make_input(inp, logical_mib, offsets_mib)
    expected_sha = digest_path(inp)
    arc = case / 'source.cmpct'
    Builder(src).build(arc)
    with CMPCT(arc) as reader:
        assert reader.by['disk.img'][6][0] == S_SPARSE
        assert reader.by['disk.img'][5].hex() == expected_sha
        counts = {'sparse_extents': len(reader.by['disk.img'][6][1])}
    # Run uninstrumented and instrumented interleaved. Each extraction opens an
    # independent authentic Reader and writes a new previously nonexistent path.
    runs = []
    for j in range(8):
        runs.append(measure(arc, expected_sha, case / f'out{j}', instrumentation=bool(j % 2)))
    observed = [v for v in runs if v['instrumented']]
    controls = [v for v in runs if not v['instrumented']]
    mids = lambda vals: int(statistics.median(vals))
    summarize = {
        'control_wall_ns_median': mids([v['total_wall_ns'] for v in controls]),
        'instrumented_wall_ns_median': mids([v['total_wall_ns'] for v in observed]),
        'control_cpu_ns_median': mids([v['total_cpu_ns'] for v in controls]),
        'instrumented_cpu_ns_median': mids([v['total_cpu_ns'] for v in observed]),
        'hole_hash_wall_ns_median': mids([v['sha_update']['hole']['wall_ns'] for v in observed]),
        'hole_hash_cpu_ns_median': mids([v['sha_update']['hole']['cpu_ns'] for v in observed]),
        'data_hash_wall_ns_median': mids([v['sha_update']['data']['wall_ns'] for v in observed]),
        'data_hash_cpu_ns_median': mids([v['sha_update']['data']['cpu_ns'] for v in observed]),
        'hole_wall_share_median': statistics.median(v['hole_wall_share'] for v in observed),
        'hole_cpu_share_median': statistics.median(v['hole_cpu_share'] for v in observed),
        'measurement_overhead_wall_ns_median': mids([v['total_wall_ns'] for v in observed]) - mids([v['total_wall_ns'] for v in controls]),
    }
    return {'case': name, 'logical_mib': logical_mib, 'data_offsets_mib': offsets_mib,
            'archive_bytes': arc.stat().st_size, 'source_sha256': expected_sha,
            'input': input_stat, 'counts': counts, 'raw_interleaved': runs, 'summary': summarize}


def main():
    start = time.time()
    with tempfile.TemporaryDirectory(prefix='cmpct-sparse-sha-court-') as work:
        root = Path(work)
        cases = [
            one_case(root, 'small16', 16, (0, 3, 8, 12)),
            one_case(root, 'parity_shape128', 128, (0, 31, 64, 120)),
            one_case(root, 'shifted_shape128', 128, (7, 45, 77, 119)),
        ]
    out = {
        'schema': 'cmpct-v031-sparse-sha-attribution-v1',
        'evidence_tier': 'scientific/product-instrumentation, not promotion',
        'candidate_head': os.environ.get('CMPCT_COURT_HEAD', 'UNSET'),
        'source': 'authentic Builder/CMPCT/sha256/sparse_extract; unchanged product source',
        'peak_rss_kib_process': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'wall_elapsed_s_all_cases': time.time() - start,
        'cases': cases,
    }
    dest = Path(os.environ.get('CMPCT_COURT_OUTPUT', 'sparse-sha-attribution.json'))
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'result': 'COURT_PASS', 'output': str(dest),
                      'summary': {c['case']: c['summary'] for c in cases}}, indent=2))


if __name__ == '__main__':
    main()
