#!/usr/bin/env python3
from __future__ import annotations

"""Established-corpus, fresh-process benchmark for CMPCT and mature compressors.

Corpus acquisition and identity checks live in CI. This harness consumes one immutable manifest,
measures complete archive bytes, wall time and peak RSS, and rejects any byte-level round-trip mismatch.
It deliberately keeps size, latency and memory separate instead of manufacturing a weighted score.
"""

import argparse, hashlib, json, os, shlex, shutil, statistics, subprocess, tempfile
from pathlib import Path
from typing import Any, Callable

TIME_BIN='/usr/bin/time'
TIMEOUT=int(os.environ.get('CMPCT_EXTERNAL_TIMEOUT','3600'))
ADAPTER=Path(__file__).with_name('external_engine_adapter.py')

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def tree_manifest(root: Path) -> list[dict[str,Any]]:
    return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)}
            for p in sorted(x for x in root.rglob('*') if x.is_file())]

def tree_digest(rows: list[dict[str,Any]]) -> str:
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def timed(argv: list[str], *, cwd: Path|None=None, stdout_path: Path|None=None) -> dict[str,Any]:
    with tempfile.NamedTemporaryFile(prefix='cmpct-ext-time-',delete=False) as tf: stat=Path(tf.name)
    out=None
    try:
        if stdout_path:
            stdout_path.parent.mkdir(parents=True,exist_ok=True);out=stdout_path.open('wb')
        p=subprocess.run([TIME_BIN,'-f','%e %M','-o',str(stat),*argv],cwd=str(cwd) if cwd else None,
                         stdout=out if out else subprocess.PIPE,stderr=subprocess.PIPE,timeout=TIMEOUT)
        if out: out.close();out=None
        if p.returncode:
            raise RuntimeError(f"rc={p.returncode}: {shlex.join(argv)}\n{p.stderr.decode('utf-8','replace')[-4000:]}")
        vals=stat.read_text().strip().split()
        return {'wall_s':float(vals[0]),'peak_rss_kib':int(vals[1]),
                'stdout':p.stdout.decode('utf-8','replace') if p.stdout else '',
                'stderr_tail':p.stderr.decode('utf-8','replace')[-1000:] if p.stderr else ''}
    finally:
        if out: out.close()
        stat.unlink(missing_ok=True)

def shell(script: str) -> list[str]: return ['bash','-o','pipefail','-lc',script]

def tar_create(src: Path, compressor: str, out: Path) -> list[str]:
    qsrc,qout=shlex.quote(str(src)),shlex.quote(str(out))
    tar=f"tar --sort=name --mtime='@946684800' --owner=0 --group=0 --numeric-owner -C {qsrc} -cf - ."
    return shell(f'{tar} | {compressor} > {qout}')

def tar_extract(arc: Path, decompressor: str, dest: Path) -> list[str]:
    return shell(f"{decompressor} < {shlex.quote(str(arc))} | tar -C {shlex.quote(str(dest))} -xf -")

def one_file(src: Path) -> Path|None:
    fs=[p for p in src.rglob('*') if p.is_file()]
    return fs[0] if len(fs)==1 else None

def assert_roundtrip(src: Path,dst: Path,label: str) -> None:
    if tree_manifest(src)!=tree_manifest(dst): raise RuntimeError(f'lossless roundtrip mismatch for {label}')

def cmpct_shipping(src: Path, work: Path, py: str) -> dict[str,Any]:
    arc=work/'archive.cmpct';dest=work/'extract'
    c=timed([py,'-m','cmpct','create',str(src),str(arc),'--workers','1','--reproducible'])
    v=timed([py,'-m','cmpct','verify',str(arc)]);dest.mkdir()
    x=timed([py,'-m','cmpct','extract',str(arc),str(dest),'--no-metadata'])
    assert_roundtrip(src,dest,'cmpct-v0.29-shipping-r24')
    try: meta=json.loads(c['stdout'])
    except Exception: meta={}
    return {'bytes':arc.stat().st_size,'sha256':sha256_file(arc),'create':c,'extract':x,'verify':v,'engine':meta}

def cmpct_module(src: Path, work: Path, py: str, repo: str, engine: str) -> dict[str,Any]:
    arc=work/'archive.cmpct';dest=work/'extract';base=[py,str(ADAPTER),'--repo',repo,'--engine',engine]
    c=timed([*base,'--action','create','--source',str(src),'--archive',str(arc)])
    v=timed([*base,'--action','verify','--archive',str(arc)]);dest.mkdir()
    x=timed([*base,'--action','extract','--archive',str(arc),'--dest',str(dest)])
    assert_roundtrip(src,dest,engine)
    try: meta=json.loads(c['stdout'])
    except Exception: meta={}
    return {'bytes':arc.stat().st_size,'sha256':sha256_file(arc),'create':c,'extract':x,'verify':v,'engine':meta}

def zip9(src: Path, work: Path) -> dict[str,Any]:
    arc=work/'archive.zip';dest=work/'extract';c=timed(['zip','-q','-9','-X','-r',str(arc),'.'],cwd=src)
    dest.mkdir();x=timed(['unzip','-qq',str(arc),'-d',str(dest)]);assert_roundtrip(src,dest,'zip-deflate-9')
    return {'bytes':arc.stat().st_size,'sha256':sha256_file(arc),'create':c,'extract':x}

def seven(src: Path,work: Path) -> dict[str,Any]:
    arc=work/'archive.7z';dest=work/'extract'
    c=timed(['7z','a','-bd','-bso0','-bsp0','-t7z','-mx=9','-m0=lzma2','-ms=on',str(arc),'.'],cwd=src)
    dest.mkdir();x=timed(['7z','x','-bd','-bso0','-bsp0','-y',f'-o{dest}',str(arc)])
    assert_roundtrip(src,dest,'7z-lzma2-9');return {'bytes':arc.stat().st_size,'sha256':sha256_file(arc),'create':c,'extract':x}

STREAMS={
'zstd-3':(['zstd','-q','-3','-f','{input}','-o','{output}'],['zstd','-q','-d','-f','{input}','-o','{output}'],'zstd -q -3 -c','zstd -q -d -c','zst'),
'zstd-19':(['zstd','-q','-19','-f','{input}','-o','{output}'],['zstd','-q','-d','-f','{input}','-o','{output}'],'zstd -q -19 -c','zstd -q -d -c','zst'),
'xz-9e':(['xz','-9e','-c','{input}'],['xz','-d','-c','{input}'],'xz -9e -c','xz -d -c','xz'),
'gzip-9':(['gzip','-9','-n','-c','{input}'],['gzip','-d','-c','{input}'],'gzip -9 -n -c','gzip -d -c','gz'),
'bzip2-9':(['bzip2','-9','-c','{input}'],['bzip2','-d','-c','{input}'],'bzip2 -9 -c','bzip2 -d -c','bz2')}

def stream(name: str,src: Path,work: Path) -> dict[str,Any]:
    comp,dec,tcomp,tdec,ext=STREAMS[name];arc=work/f'archive.{ext}';dest=work/'extract';dest.mkdir();one=one_file(src)
    if one:
        ca=[x.format(input=str(one),output=str(arc)) for x in comp]
        c=timed(ca,stdout_path=arc) if name in {'xz-9e','gzip-9','bzip2-9'} else timed(ca)
        restored=dest/one.name;da=[x.format(input=str(arc),output=str(restored)) for x in dec]
        x=timed(da,stdout_path=restored) if name in {'xz-9e','gzip-9','bzip2-9'} else timed(da)
        semantics='raw-single-file'
    else:
        c=timed(tar_create(src,tcomp,arc));x=timed(tar_extract(arc,tdec,dest));semantics='deterministic-tar-stream'
    assert_roundtrip(src,dest,name)
    return {'bytes':arc.stat().st_size,'sha256':sha256_file(arc),'create':c,'extract':x,'stream_semantics':semantics}

def summarize(reps: list[dict[str,Any]],logical: int) -> dict[str,Any]:
    sizes={r['bytes'] for r in reps}
    if len(sizes)!=1: raise RuntimeError(f'nondeterministic archive sizes: {sorted(sizes)}')
    def stats(key: str)->dict[str,Any]:
        xs=[float(r[key]['wall_s']) for r in reps]
        return {'median_s':statistics.median(xs),'min_s':min(xs),'max_s':max(xs),'samples_s':xs}
    out={'bytes':reps[0]['bytes'],'ratio':reps[0]['bytes']/logical,'archive_sha256_first':reps[0]['sha256'],
         'repetitions':len(reps),'create':stats('create'),'extract':stats('extract'),
         'create_peak_rss_kib_samples':[r['create']['peak_rss_kib'] for r in reps],
         'extract_peak_rss_kib_samples':[r['extract']['peak_rss_kib'] for r in reps]}
    if 'verify' in reps[0]:
        xs=[float(r['verify']['wall_s']) for r in reps];out['verify']={'median_s':statistics.median(xs),'samples_s':xs};out['engine_first']=reps[0].get('engine',{})
    if 'stream_semantics' in reps[0]:out['stream_semantics']=reps[0]['stream_semantics']
    return out

def tool_versions()->dict[str,str]:
    queries={'zip':['zip','-v'],'7z':['7z'],'zstd':['zstd','--version'],'xz':['xz','--version'],'gzip':['gzip','--version'],'bzip2':['bzip2','--version']};out={}
    for k,v in queries.items():
        p=subprocess.run(v,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);out[k]=(p.stdout or '').splitlines()[0][:200] if p.stdout else ''
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('--out',required=True);a=ap.parse_args()
    spec=json.loads(Path(a.manifest).read_text());out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    py29=os.environ['CMPCT_V029_PYTHON'];repo29=os.environ['CMPCT_V029_REPO'];py30=os.environ['CMPCT_V030_PYTHON'];repo30=os.environ['CMPCT_V030_REPO']
    result={'schema':'cmpct-established-corpora-v2','purpose':'research evidence; not a release gate or website headline',
      'provenance':{'v029_release_sha':os.environ['CMPCT_V029_SHA'],'v030_snapshot_sha':os.environ['CMPCT_V030_SHA'],'benchmark_sha':os.environ.get('GITHUB_SHA'),'runner':os.environ.get('RUNNER_NAME'),'tool_versions':tool_versions()},
      'semantics':{'timing':'fresh-process GNU time; medians retained where repetitions>1','single_file_stream':'raw canonical file; archive formats retain native container overhead','multi_file_stream':'deterministic normalized tar piped to stream compressor','source_metadata':'regular-file mode and mtime normalized because corpus authorities specify bytes, not filesystem timestamps','roundtrip':'relative path + byte length + SHA-256 must match exactly','scores':'no weighted aggregate score'},'corpora':{}}
    runners:list[tuple[str,Callable[[Path,Path],dict[str,Any]]]]=[
      ('cmpct-v0.29-shipping-r24',lambda s,w:cmpct_shipping(s,w,py29)),
      ('cmpct-v0.29-research',lambda s,w:cmpct_module(s,w,py29,repo29,'v029-research')),
      ('cmpct-v0.30-canonical-snapshot',lambda s,w:cmpct_module(s,w,py30,repo30,'v030-canonical')),
      ('zip-deflate-9',zip9),('zstd-3',lambda s,w:stream('zstd-3',s,w)),('zstd-19',lambda s,w:stream('zstd-19',s,w)),
      ('7z-lzma2-9',seven),('xz-9e',lambda s,w:stream('xz-9e',s,w)),('gzip-9',lambda s,w:stream('gzip-9',s,w)),('bzip2-9',lambda s,w:stream('bzip2-9',s,w))]
    for item in spec['corpora']:
        name=item['name'];src=Path(item['path']);rows=tree_manifest(src);logical=sum(r['bytes'] for r in rows)
        if logical!=int(item['expected_logical_bytes']):raise RuntimeError(f'{name} logical mismatch')
        entry={'authority':item.get('authority'),'mode':item.get('mode'),'logical_bytes':logical,'files':len(rows),'tree_sha256':tree_digest(rows),'timing_repetitions':int(item.get('repetitions',1)),'results':{}}
        for label,fn in runners:
            reps=[]
            for i in range(entry['timing_repetitions']):
                work=out/'work'/name/label/f'rep-{i}';shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
                print(f'BENCH {name} :: {label} :: rep {i+1}',flush=True);reps.append(fn(src,work))
            entry['results'][label]=summarize(reps,logical);print(json.dumps({'corpus':name,'compressor':label,**entry['results'][label]},sort_keys=True),flush=True)
        result['corpora'][name]=entry;(out/'external-corpora.partial.json').write_text(json.dumps(result,indent=2))
    (out/'external-corpora.json').write_text(json.dumps(result,indent=2));print('RESULT_COMPLETE',flush=True)
if __name__=='__main__':main()
