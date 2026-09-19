from __future__ import annotations

"""Research-only oracle: can exact repeated compression reuse accelerate both co-critical ML children?"""
import argparse, hashlib, json, shutil, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v028 as V028
from experiments import entropygraph_v029_residual_fast as A5


def _sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def _run(label: str, build, source: Path, work: Path, compress_owner) -> dict:
    base=work/f'{label}-base.cmpct'; cand=work/f'{label}-memo.cmpct'
    t=time.perf_counter(); build(source, base); base_s=time.perf_counter()-t
    original=compress_owner._compress_record; cache={}; hits=misses=0; retained_raw=0; retained_comp=0
    def memo(raw: bytes, level: int=19):
        nonlocal hits,misses,retained_raw,retained_comp
        key=(int(level), raw)
        value=cache.get(key)
        if value is not None:
            hits += 1; return value
        misses += 1; value=original(raw, level); cache[key]=value
        retained_raw += len(raw); retained_comp += len(value[1])
        return value
    compress_owner._compress_record=memo
    try:
        t=time.perf_counter(); build(source, cand); memo_s=time.perf_counter()-t
    finally:
        compress_owner._compress_record=original
    if _sha(base)!=_sha(cand): raise RuntimeError(f'{label} memoization changed archive bytes')
    return {"label":label,"baseline_s":base_s,"memo_s":memo_s,
            "improvement_pct":(base_s-memo_s)/base_s*100.0,"archive_sha256":_sha(base),
            "cache_hits":hits,"cache_misses":misses,"cache_entries":len(cache),
            "retained_raw_bytes":retained_raw,"retained_compressed_bytes":retained_comp}


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    source=PERF._build_corpora(work/'corpus')[("neutral_hostile_v1","09_ml_artifacts")]
    tree=V028.treehash(source)
    v028=_run('v028', lambda s,o: V028.build(s,o), source, work, V028)
    owner=A5.BASE.P; old=owner._position_independent_candidates
    owner._position_independent_candidates=lambda _s,_n: []
    # Mosaic loads v0.28 under its own module identity; patch the actual delegated compression owner.
    attempt5_compress_owner=owner.PARENT.V028
    try:
        a5=_run('attempt5-neutral', lambda s,o: A5.build_graph(s,o), source, work, attempt5_compress_owner)
    finally:
        owner._position_independent_candidates=old
    return {"schema":"cmpct-v030-ml-compress-memo-oracle-v1","release_credit":False,
            "source_tree_sha256":tree,"v028":v028,"attempt5":a5,
            "claim_boundary":"One paired research oracle per child. Exact archive SHA is mandatory. Cache memory is fully reported and receives no product credit; fresh-process balanced whole-product evidence is required before promotion."}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
