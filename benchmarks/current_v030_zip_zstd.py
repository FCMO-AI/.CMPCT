from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as V030
from experiments import entropygraph_v030_release as TREE


def tree(root: Path) -> str:
    return TREE.treehash(root)


def v030(stage: Path, archive: Path, extracted: Path) -> dict:
    started=time.perf_counter(); stats=V030.build(stage,archive); create_s=time.perf_counter()-started
    verified=V030.strong_verify(archive)
    if not verified.get('ok'): raise RuntimeError(f'v0.30 verify failed: {verified!r}')
    started=time.perf_counter(); V030.extract(archive,extracted); extract_s=time.perf_counter()-started
    return {'archive_bytes':archive.stat().st_size,'create_s':create_s,'extract_s':extract_s,'selected':stats.get('selected'),'available':True}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root,ignore_errors=True); work_root.mkdir(parents=True)
    accepted=GENERAL._accepted_v029_rows()
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_now_ext_neutral')
    hostile=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_now_ext_hostile')
    repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_now_ext_repair'); repair.install_generation_hooks(neutral)
    roots=(('neutral_hostile_v1',neutral,work_root/'neutral'),('resemblance_hostile_v1',hostile,work_root/'resemblance'))
    rows=[]
    for suite,builder,root in roots:
        builder.build(root)
        if suite=='neutral_hostile_v1': repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            if tree(source)!=accepted[(suite,source.name)]['tree_sha256']: raise RuntimeError(f'source drift {suite}/{source.name}')
            with tempfile.TemporaryDirectory(prefix='cmpct-now-ext-',dir=work_root) as td0:
                td=Path(td0); stage=EXT._normalized_stage(source,td); expected=tree(stage)
                outputs=td/'outputs'; outputs.mkdir()
                c=v030(stage,outputs/'candidate.cmpct',outputs/'cmpct-out')
                z=EXT._zip(stage,outputs/'archive.zip',outputs/'zip-out')
                s=EXT._tar_zstd(stage,outputs/'archive.tar.zst',outputs/'zstd-out',outputs)
                for name,item,dst in [('v030',c,outputs/'cmpct-out'),('zip_deflate9',z,outputs/'zip-out'),('tar_zstd19_solid',s,outputs/'zstd-out')]:
                    if tree(dst)!=expected: raise RuntimeError(f'{name} tree mismatch {suite}/{source.name}')
                    item['tree_verified']=True
                row={'label':f'{suite}/{source.name}','suite':suite,'name':source.name,'tree_sha256':expected,'formats':{'v030':c,'zip_deflate9':z,'tar_zstd19_solid':s}}
                rows.append(row); print(json.dumps(row,separators=(',',':')),flush=True)
    def agg(name: str):
        vals=[r['formats'][name] for r in rows]
        return {'archive_bytes':sum(int(x['archive_bytes']) for x in vals),'create_s':sum(float(x['create_s']) for x in vals),'extract_s':sum(float(x['extract_s']) for x in vals)}
    a={n:agg(n) for n in ('v030','zip_deflate9','tar_zstd19_solid')}; c=a['v030']
    ratios={n:{k:c[k]/a[n][k] for k in ('archive_bytes','create_s','extract_s')} for n in ('zip_deflate9','tar_zstd19_solid')}
    wins={n:{'size':sum(r['formats']['v030']['archive_bytes']<r['formats'][n]['archive_bytes'] for r in rows),'create':sum(r['formats']['v030']['create_s']<r['formats'][n]['create_s'] for r in rows),'extract':sum(r['formats']['v030']['extract_s']<r['formats'][n]['extract_s'] for r in rows)} for n in ('zip_deflate9','tar_zstd19_solid')}
    return {'schema':'cmpct-current-v030-zip-zstd19-v1','workload_count':len(rows),'rows':rows,'aggregates':a,'ratios_v030_over_competitor':ratios,'wins_v030':wins,'exact_all':all(item['tree_verified'] for r in rows for item in r['formats'].values())}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--work-root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)

if __name__=='__main__': main()
