#!/usr/bin/env python3
"""J24G78 independent public-Writer cost decomposition; research-only, no product edits."""
from __future__ import annotations
import hashlib, json, os, platform, shutil, statistics, subprocess, tempfile, time
from pathlib import Path
import msgpack
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from cmpct import transactions as tx

PARENT='6b68197c64b8de0654dd2f854a5185b45a00d2b9'
PREREG='1ba82c6e969f90e62ec67dd35e8a0de5a4c864ae'
WRITER_BLOB='71bbc8a989d1da79d0f0dbe44f7f5c39f3304854'
CASES=((8192,'middle'),(32768,'tail'))
def attest():
    repo=Path(__file__).resolve().parents[1]
    def git(*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
    head=git('rev-parse','HEAD')
    assert git('rev-parse','HEAD:src/cmpct/transactions.py')==WRITER_BLOB,'Writer changed'
    for ancestor in (PARENT,PREREG):
        subprocess.run(['git','merge-base','--is-ancestor',ancestor,head],cwd=repo,check=True)
    return dict(head=head,parent=PARENT,prereg=PREREG,writer_blob=WRITER_BLOB)

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def chosen(n,where):
    if where=='middle': a=range(n//2-31,n//2+32);extra=n//2+32
    else: a=range(n-63,n);extra=n-64
    return [f'f{i:05d}.dat' for i in a],f'f{extra:05d}.dat'

def instrumented_delete(archive,name,always_copy):
    """Inline source-exact append_delete/_append_generation with timing around its original stages."""
    t=time.perf_counter_ns
    start=t();cpu=time.process_time_ns()
    with tx.CMPCT(archive) as ar:
        opened=t()
        if name not in ar.by:raise KeyError(name)
        tx._reject_hardlink_owner_mutation(ar.index,name,'delete')
        guarded=t()
        prev=ar.latest_footer_pos;depth=ar.delta_depth
        # ONLY DIFFERENCE: no copy of private index for a pure one-op delta before checkpoint.
        idx=msgpack.unpackb(msgpack.packb(ar.index,use_bin_type=True),raw=False) if (always_copy or depth>=63) else None
        copied=t()
    op=['del',name]
    checkpoint=tx._index_after_op(idx,op) if depth>=63 else None
    checkpoint_end=t()
    if checkpoint is not None:
        payload=msgpack.packb(checkpoint,use_bin_type=True);kind=0
    else:
        payload=msgpack.packb({'blobs':[],'ops':[op]},use_bin_type=True);kind=1
    compressed=tx.zc(payload,3)
    if len(compressed)<len(payload):encoded=compressed;codec=1
    else:encoded=payload;codec=0
    footer=tx.FTR.pack(tx.FMAGIC,kind,codec,0,0,len(encoded),len(payload),prev,tx.sha(payload))
    encoded_end=t()
    with open(archive,'ab',buffering=0) as f:
        f.write(encoded);os.fsync(f.fileno());payload_sync=t()
        f.write(footer);os.fsync(f.fileno());footer_sync=t()
    return dict(wall_ns=t()-start,cpu_ns=time.process_time_ns()-cpu,depth_before=depth,
        footer_kind=kind,open_ns=opened-start,guard_ns=guarded-opened,
        copy_ns=copied-guarded,checkpoint_ns=checkpoint_end-copied,
        encode_ns=encoded_end-checkpoint_end,payload_sync_ns=payload_sync-encoded_end,
        footer_sync_ns=footer_sync-payload_sync)

def make_base(root,n,where):
    source=root/f'tree-{n}-{where}';source.mkdir()
    for i in range(n):
        (source/f'f{i:05d}.dat').write_bytes(hashlib.sha256(f'j24g78-{n}-{i}'.encode()).digest())
    archive=root/f'base-{n}-{where}.cmpct'
    s=time.perf_counter_ns();Builder(source,workers=1,reproducible=False).build(archive)
    build_wall=time.perf_counter_ns()-s
    with CMPCT(archive) as ar: assert len(ar.by)==n and ar.delta_depth==0
    return archive,build_wall

def run(root,base,n,where,label,trial,names,extra):
    path=root/f'{n}-{where}-{label}-{trial}.cmpct'
    shutil.copyfile(base,path)
    assert digest(path)==digest(base)
    samples=[];start=time.perf_counter_ns();cpu_start=time.process_time_ns()
    for name in names:
        if label=='public':
            a=time.perf_counter_ns();c=time.process_time_ns()
            tx.append_delete(path,name)
            samples.append(dict(wall_ns=time.perf_counter_ns()-a,cpu_ns=time.process_time_ns()-c))
        else:samples.append(instrumented_delete(path,name,label=='sham'))
    wall=time.perf_counter_ns()-start;cpu=time.process_time_ns()-cpu_start
    after63_bytes=path.stat().st_size;after63_sha=digest(path)
    with CMPCT(path) as ar:
        assert ar.delta_depth==63 and len(ar.by)==n-63
        index63=msgpack.packb(ar.index,use_bin_type=True)
        assert ar.verify()==n-63
        for name in (f'f00000.dat',f'f{n//4:05d}.dat'):
            if name in ar.by:
                i=int(name[1:6])
                assert ar.read(name)==hashlib.sha256(f'j24g78-{n}-{i}'.encode()).digest()
    p=preflight_archive(path)
    assert p['files']==n-63 and p['delta_depth']==63
    if label=='public':tx.append_delete(path,extra)
    else:instrumented_delete(path,extra,label=='sham')
    with CMPCT(path) as ar:
        assert ar.delta_depth==0 and len(ar.by)==n-64
        assert ar.verify()==n-64
        index64=msgpack.packb(ar.index,use_bin_type=True)
    assert preflight_archive(path)['files']==n-64
    after64_sha=digest(path)
    damaged=root/f'{n}-{where}-{label}-{trial}-damaged.cmpct'
    data=bytearray(path.read_bytes());data[-1]^=0xA5;damaged.write_bytes(data)
    with CMPCT(damaged) as ar:
        assert ar.delta_depth==63 and msgpack.packb(ar.index,use_bin_type=True)==index63
    return dict(label=label,trial=trial,wall_ns=wall,cpu_ns=cpu,
        after63_bytes=after63_bytes,after63_sha256=after63_sha,
        after63_index_sha256=hashlib.sha256(index63).hexdigest(),
        after64_sha256=after64_sha,
        after64_index_sha256=hashlib.sha256(index64).hexdigest(),
        checkpoint64=True,damaged_tail_recovery=True,stage_rows=samples)

def main():
    out=Path(os.getenv('J24G78_EVIDENCE_DIR','evidence'));out.mkdir(exist_ok=True,parents=True)
    receipt=dict(schema='j24g78-writer-copy-ownership-v1',source=attest(),
                 host=platform.platform(),product_credit=0,status='RUNNING',cases={})
    file=out/'j24g78-result.json'
    def save():file.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    save()
    with tempfile.TemporaryDirectory(prefix='cmpct-j24g78-') as t:
        root=Path(t)
        for n,where in CASES:
            base,build_wall=make_base(root,n,where)
            names,extra=chosen(n,where)
            # Balanced A/B/B/A + the phase-instrumented S control on the exact same base archive bytes.
            rows=[]
            for trial,label in enumerate(('public','elide','elide','public','sham')):
                row=run(root,base,n,where,label,trial,names,extra)
                rows.append(row)
                print(f'J24G78 n={n} trial={trial} {label} wall_s={row["wall_ns"]/1e9:.6f}',flush=True)
            for field in ('after63_bytes','after63_sha256','after63_index_sha256',
                          'after64_sha256','after64_index_sha256'):
                assert len({r[field] for r in rows})==1,(field,n)
            median={label:statistics.median(r['wall_ns'] for r in rows if r['label']==label)
                    for label in ('public','elide','sham')}
            stages={}
            for label in ('sham','elide'):
                s=[i for r in rows if r['label']==label for i in r['stage_rows']]
                stages[label]={field:statistics.mean(r[field] for r in s)
                    for field in ('open_ns','guard_ns','copy_ns','checkpoint_ns',
                        'encode_ns','payload_sync_ns','footer_sync_ns')}
            decisions=dict(elide_public_ratio=median['elide']/median['public'],
                sham_public_ratio=median['sham']/median['public'],
                sham_copy_fraction=stages['sham']['copy_ns']/(median['sham']/63),
                sham_open_fraction=stages['sham']['open_ns']/(median['sham']/63),
                h1_material=(median['elide']/median['public']<=.90 and
                             stages['sham']['copy_ns']/(median['sham']/63)>=.05),
                sham_valid=abs(median['sham']/median['public']-1)<=.10)
            receipt['cases'][f'{n}-{where}']=dict(initial_members=n,
                deletion_count=63,base_archive_sha256=digest(base),base_bytes=base.stat().st_size,
                build_wall_ns=build_wall,medians_ns=median,stages_mean_ns=stages,
                decisions=decisions,raw=rows)
            save()
    receipt['status']='COMPLETE';save()
    print('J24G78 full physical receipt:',str(file),flush=True)
if __name__=='__main__':main()
