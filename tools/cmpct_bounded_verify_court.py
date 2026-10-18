"""Optional revision-24 >4-GiB strong-verification resource court (not a release gate).

Run from the repository root on Linux:
    python tools/cmpct_bounded_verify_court.py --kind chunks --count 4097
The fixture uses one physical MiB, but SHA-256 is computed over every logical byte.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def _worker(path, limit_mib):
    resource.setrlimit(resource.RLIMIT_AS, (limit_mib << 20, limit_mib << 20))
    from cmpct.reader import CMPCT
    start = time.perf_counter()
    cpu = time.process_time()
    with CMPCT(path) as archive:
        verified = archive.verify()
    return dict(verified=verified, wall_s=time.perf_counter()-start,
                cpu_s=time.process_time()-cpu,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', choices=('chunks', 'cdc'), default='chunks')
    parser.add_argument('--count', type=int, default=4097)
    parser.add_argument('--limit-mib', type=int, default=512)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--archive', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.platform != 'linux':
        parser.error('This RLIMIT_AS/RSS court is Linux-only')
    if args.count < 1 or args.count > 10000 or args.limit_mib < 128:
        parser.error('out-of-range count or memory limit')
    if args.worker:
        print(json.dumps(_worker(args.archive, args.limit_mib)))
        return
    sys.path.insert(0, str(ROOT/'tests'))
    from make_map_archive import make
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'large.cmpct'
        expected = make(path, args.kind, args.count)
        cmd = [sys.executable, str(Path(__file__).resolve()), '--worker',
               '--archive', str(path), '--kind', args.kind, '--count',
               str(args.count), '--limit-mib', str(args.limit_mib)]
        env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))
        run = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        if run.returncode:
            raise RuntimeError('worker failed: '+run.stderr[-1200:])
        measured = json.loads(run.stdout)
        if measured['verified'] != 1:
            raise AssertionError('expected exactly one authenticated logical file')
        source = (ROOT/'src/cmpct/reader.py').read_bytes()
        git_blob = hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()
        print(json.dumps(dict(schema='cmpct-r24-bounded-verification-court-v1',
                              reader_git_blob=git_blob, fixture=expected,
                              limit_as_mib=args.limit_mib, measured=measured), indent=2))


if __name__ == '__main__':
    main()
