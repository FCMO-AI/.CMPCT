from __future__ import annotations

"""Fresh-process A/B for bounded pack-plan cache through the real two-child parallel portfolio shape.

Evidence only: this reproduces the accepted scheduler's independent-child topology and exact smaller-artifact
tournament while changing only each child's pack-plan pricing implementation. It grants no release credit.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v029_residual_fast as A5
from experiments import entropygraph_v030_pack_plan_cache as CACHE


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def _worker(kind: str, candidate: bool, source: str, out: str, q) -> None:
    owner = A5.BASE.P.PARENT.V028 if kind == 'attempt5' else A5.V028
    old_choose = owner._choose_pack_plan
    old_position = None
    try:
        if candidate:
            def cached_choose(nodes, sketches, roots):
                chosen, trials, _ = CACHE.choose_pack_plan_cached(
                    nodes, sketches, roots, compress_record=owner._compress_record)
                return chosen, trials
            owner._choose_pack_plan = cached_choose
        if kind == 'attempt5':
            position_owner = A5.BASE.P
            old_position = position_owner._position_independent_candidates
            position_owner._position_independent_candidates = lambda _s, _n: []
            stats = A5.build_graph(Path(source), Path(out))
        elif kind == 'v028':
            stats = A5.V028.build(Path(source), Path(out))
        else:
            raise ValueError(kind)
        q.put({'kind': kind, 'ok': True, 'selected': stats.get('selected') if isinstance(stats, dict) else None})
    except BaseException as exc:
        q.put({'kind': kind, 'ok': False, 'error': repr(exc)})
    finally:
        owner._choose_pack_plan = old_choose
        if old_position is not None:
            A5.BASE.P._position_independent_candidates = old_position


def _portfolio(candidate: bool, source: Path, out: Path) -> dict:
    started_cpu = time.process_time()
    started = time.perf_counter()
    ctx = mp.get_context('spawn')
    with tempfile.TemporaryDirectory(prefix='cmpct-cache-parallel-', dir=out.parent) as td:
        td = Path(td)
        paths = {'v028': td/'v028.cmpct', 'attempt5': td/'attempt5.cmpct'}
        q = ctx.Queue()
        ps = [ctx.Process(target=_worker, args=(k, candidate, str(source), str(paths[k]), q))
              for k in ('v028','attempt5')]
        for p in ps: p.start()
        rows = [q.get(timeout=1800) for _ in ps]
        for p in ps: p.join(30)
        if any(not r.get('ok') for r in rows) or any(p.exitcode != 0 for p in ps):
            raise RuntimeError(f'child failure rows={rows!r} exitcodes={[p.exitcode for p in ps]!r}')
        # Match the accepted scheduler exactly: attempt-5 must be strictly smaller; ties fall back to v0.28.
        winner = paths['attempt5'] if paths['attempt5'].stat().st_size < paths['v028'].stat().st_size else paths['v028']
        shutil.copyfile(winner, out)
    return {'candidate': candidate, 'wall_s': time.perf_counter()-started,
            'parent_cpu_s': time.process_time()-started_cpu,
            'maxrss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'archive_bytes': out.stat().st_size, 'archive_sha256': _sha(out)}


def _invoke(candidate: bool, source: Path, out: Path) -> dict:
    cmd=[sys.executable, str(Path(__file__).resolve()), '--child', '--source', str(source), '--archive', str(out)]
    if candidate: cmd.append('--candidate')
    p=subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                     env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])})
    return json.loads(p.stdout.strip().splitlines()[-1])


def run(work: Path, pairs: int) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    source=PERF._build_corpora(work/'corpus')[('neutral_hostile_v1','09_ml_artifacts')]
    rows=[]
    for i in range(pairs):
        arms=(False,True) if i%2==0 else (True,False)
        got=[]
        for cand in arms:
            got.append(_invoke(cand, source, work/f"{i}-{'candidate' if cand else 'control'}.cmpct"))
        c=next(x for x in got if not x['candidate']); n=next(x for x in got if x['candidate'])
        if c['archive_sha256'] != n['archive_sha256'] or c['archive_bytes'] != n['archive_bytes']:
            raise RuntimeError('candidate changed whole-portfolio archive identity')
        rows.append({'control':c,'candidate':n,'wall_improvement_pct':(c['wall_s']-n['wall_s'])/c['wall_s']*100})
    vals=sorted(x['wall_improvement_pct'] for x in rows)
    return {'schema':'cmpct-v030-pack-cache-parallel-product-v1','release_credit':False,'pairs':pairs,'rows':rows,
            'median_wall_improvement_pct':vals[len(vals)//2],
            'claim_boundary':'Whole parallel-portfolio topology A/B on ML corpus; exact bytes mandatory; authoritative release runtime remains unpaid.'}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--child',action='store_true'); p.add_argument('--candidate',action='store_true')
    p.add_argument('--source',type=Path); p.add_argument('--archive',type=Path); p.add_argument('--work-root',type=Path)
    p.add_argument('--output',type=Path); p.add_argument('--pairs',type=int,default=3); a=p.parse_args()
    if a.child:
        print(json.dumps(_portfolio(a.candidate,a.source,a.archive),separators=(',',':'))); return
    d=run(a.work_root,a.pairs); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps(d,indent=2))

if __name__ == '__main__': main()
