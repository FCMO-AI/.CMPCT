from __future__ import annotations

"""Fresh-process hidden-cost gate for transient LOC1 checkpoints.

Mission Lock / Hostile Reviewer
===============================
The supported checkpoint candidate is frozen at stride 256 and five packed u64 arrays per family.
The earlier lookup receipt reported packed payload bytes, not Python/container overhead. This gate uses
the exact same deterministic near-ceiling locator and measures a fresh process before/after building the
candidate, including Python allocation peak and current/peak RSS. Archive representation bytes, auth,
locality and the parser's 1 MiB raw ceiling are unchanged.

Hypothesis
----------
The candidate's hidden runtime state remains bounded enough to be plausible as a reader optimization:
parse/build Python allocation peak <= 2x raw locator bytes and current RSS increase over retaining the
raw locator <= 4096 KiB. Exact record cardinality and packed checkpoint <=128 KiB must remain true.

Disproof
--------
Any cardinality drift, checkpoint bound breach, >2x raw Python peak, or >4 MiB incremental current RSS
falsifies the Python candidate as a general reader implementation. A PASS still grants no product speed,
Office, native or release credit; a native implementation must account independently.
"""

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tracemalloc

from benchmarks import v030_r4_compact_locator_checkpoint_lookup as CP

SCHEMA = "cmpct-v030-r4-compact-locator-checkpoint-rss-v1"
RSS_LIMIT_KIB = 4096


def _rss_kib() -> int:
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmRSS:'):
                return int(line.split()[1])
    except OSError:
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def worker(raw_path: Path) -> dict:
    raw = raw_path.read_bytes()
    gc.collect()
    before = _rss_kib()
    before_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    tracemalloc.start()
    candidate = CP.CheckpointLocator(raw)
    _cur, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()
    after = _rss_kib()
    after_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Keep candidate live through measurement.
    return {
        'raw_bytes': len(raw),
        'records': candidate.record_count,
        'packed_checkpoint_bytes': candidate.packed_checkpoint_bytes,
        'python_peak_bytes': int(py_peak),
        'current_rss_before_kib': before,
        'current_rss_after_kib': after,
        'current_rss_delta_kib': after-before,
        'peak_rss_before_kib': before_peak,
        'peak_rss_after_kib': after_peak,
    }


def run(work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    raw, expected_records = CP._increasing_locator()
    raw_path = work/'near-ceiling.loc1'
    raw_path.write_bytes(raw)
    cp = subprocess.run([sys.executable, __file__, '--worker', str(raw_path)], check=True, capture_output=True, text=True)
    m = json.loads(cp.stdout.strip().splitlines()[-1])
    py_limit = 2*len(raw)
    supported = (
        m['records']==expected_records
        and m['packed_checkpoint_bytes'] <= CP.MAX_CHECKPOINT_BYTES
        and m['python_peak_bytes'] <= py_limit
        and m['current_rss_delta_kib'] <= RSS_LIMIT_KIB
    )
    return {
        'schema': SCHEMA,
        'source_commit': os.environ.get('EVIDENCE_HEAD'),
        'measurement': m,
        'limits': {
            'python_peak_bytes': py_limit,
            'current_rss_delta_kib': RSS_LIMIT_KIB,
            'packed_checkpoint_bytes': CP.MAX_CHECKPOINT_BYTES,
        },
        'hypothesis': {'checkpoint_python_hidden_cost_is_bounded': supported},
        'contract': {
            'candidate_and_stride_frozen': True,
            'fresh_process': True,
            'representation_bytes_unchanged': True,
            'auth_and_locality_unchanged': True,
            'diagnostic_only': True,
            'release_credit': False,
        },
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--worker', type=Path)
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-r4-checkpoint-rss-work'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-r4-compact-locator-checkpoint-rss.json'))
    a=p.parse_args()
    if a.worker:
        print(json.dumps(worker(a.worker), sort_keys=True)); return
    d=run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps(d,sort_keys=True))


if __name__=='__main__':
    main()
