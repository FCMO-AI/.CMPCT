#!/usr/bin/env python3
"""J24G80: sequential private Writer-state oracle. NOT a public concurrent Writer."""
from __future__ import annotations
import hashlib, json, os, platform, shutil, statistics, subprocess, tempfile, time
from pathlib import Path
import msgpack
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from cmpct import transactions as tx

PARENT='42d60372fb71e574e1271f14402b5ca325ed1147'
PREREG='85210966da6046b69ecfa4685c71af3ae693087b'
WRITER_BLOB='71bbc8a989d1da79d0f0dbe44f7f5c39f3304854'
CASES=((8192,'middle'),(32768,'tail'))

def attest():
    repo=Path(__file__).resolve().parents[1]
    def git(*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
    head=git('rev-parse','HEAD')
    assert git('rev-parse','HEAD:src/cmpct/transactions.py')==WRITER_BLOB
    for sha in (PARENT,PREREG):
        subprocess.run(['git','merge-base','--is-ancestor',sha,head],cwd=repo,check=True)
    return dict(head=head,parent=PARENT,prereg=PREREG,writer_blob=WRITER_BLOB)

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def select(n,where):
    ix=range(n//2-31,n//2+32) if where=='middle' else range(n-63,n)
    extra=n//2+32 if where=='middle' else n-64
    names=[f'f{i:05d}.dat' for i in ix]+[f'f{extra:05d}.dat']
    assert len(names)==64 and len(set(names))==64
    return names

def make_base(root,n,where):
    src=root/f'source-{n}-{where}';src.mkdir()
    for i in range(n):
        (src/f'f{i:05d}.dat').write_bytes(hashlib.sha256(f'j24g80-{n}-{i}'.encode()).digest())
    archive=root/f'base-{n}-{where}.cmpct'
    s=time.perf_counter_ns()
    Builder(src,workers=1,reproducible=False).build(archive)
    created=time.perf_counter_ns()-s
    with CMPCT(archive) as ar:
        assert len(ar.by)==n and ar.delta_depth==0 and ar.latest_footer_pos is not None
    return archive,created

def trial(root,base,n,where,names,variant,trial_no):
    path=root/f'{n}-{where}-{variant}-{trial_no}.cmpct'
    shutil.copyfile(base,path)
    assert sha_file(path)==sha_file(base)
    initial_wall=initial_cpu=0
    if variant=='owned':
        w=time.perf_counter_ns();c=time.process_time_ns()
        with CMPCT(path) as ar:
            idx=msgpack.unpackb(msgpack.packb(ar.index,use_bin_type=True),raw=False)
            prev=ar.latest_footer_pos;depth=ar.delta_depth
        initial_wall=time.perf_counter_ns()-w;initial_cpu=time.process_time_ns()-c
        live={row[0] for row in idx['files']}
        assert len(live)==n
    per=[];physical=[]
    for gen,name in enumerate(names,1):
        w=time.perf_counter_ns();c=time.process_time_ns()
        if variant=='public':
            tx.append_delete(path,name)
        else:
            assert name in live
            tx._reject_hardlink_owner_mutation(idx,name,'delete')
            op=['del',name]
            tx._index_after_op(idx,op)
            checkpoint=idx if depth>=63 else None
            prev,_=tx._append_generation(path,{'blobs':[],'ops':[op]},prev,checkpoint)
            depth=0 if checkpoint is not None else depth+1
            live.remove(name)
        wall=time.perf_counter_ns()-w;cpu=time.process_time_ns()-c
        per.append(dict(generation=gen,wall_ns=wall,cpu_ns=cpu))
        # Physical SHA and size are charged equally and strictly OUTSIDE the timed mutation.
        physical.append(dict(generation=gen,sha256=sha_file(path),bytes=path.stat().st_size))
    with CMPCT(path) as ar:
        assert ar.delta_depth==0 and len(ar.by)==n-64
        assert ar.verify()==n-64
        final=msgpack.packb(ar.index,use_bin_type=True)
        expected={f'f{i:05d}.dat' for i in range(n)}-set(names)
        assert set(ar.by)==expected
        for name in (f'f00000.dat',f'f{n//4:05d}.dat'):
            if name in expected:
                i=int(name[1:6])
                assert ar.read(name)==hashlib.sha256(f'j24g80-{n}-{i}'.encode()).digest()
    p=preflight_archive(path)
    assert p['files']==n-64 and p['delta_depth']==0
    corrupt=root/f'corrupt-{n}-{variant}-{trial_no}.cmpct'
    data=bytearray(path.read_bytes());data[-1]^=0xA5;corrupt.write_bytes(data)
    with CMPCT(corrupt) as ar:
        assert ar.delta_depth==63 and len(ar.by)==n-63
        assert names[-1] in ar.by and ar.verify()==n-63
    # Retain authentic wire bytes for a separate no-CMPCT referee. All export
    # work occurs AFTER every timed mutation and every product verification.
    if trial_no in (0,1):
        export=Path(os.environ.get('J24G80_EVIDENCE_DIR','evidence'))
        export.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,export/f'j24g80-{n}-{where}-{variant}-valid.cmpct')
        if variant=='owned':
            shutil.copyfile(corrupt,export/f'j24g80-{n}-{where}-{variant}-corrupt-tail.cmpct')
    return dict(variant=variant,trial=trial_no,per_generation=per,physical=physical,
                init_wall_ns=initial_wall,init_cpu_ns=initial_cpu,
                final_index_sha256=hashlib.sha256(final).hexdigest(),
                checkpoint64=True,corrupt_tail_recovery=True)

def main():
    out=Path(os.getenv('J24G80_EVIDENCE_DIR','evidence'));out.mkdir(parents=True,exist_ok=True)
    dest=out/'j24g80-result.json'
    receipt=dict(schema='cmpct-j24g80-owned-writer-oracle-v1',source=attest(),
                 host=platform.platform(),product_credit=0,status='RUNNING',cases={})
    def save():dest.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    save()
    try:
        with tempfile.TemporaryDirectory(prefix='cmpct-j24g80-') as td:
            root=Path(td)
            for n,where in CASES:
                base,created=make_base(root,n,where)
                names=select(n,where);rows=[]
                for i,v in enumerate(('public','owned','owned','public')):
                    row=trial(root,base,n,where,names,v,i);rows.append(row)
                    print('J24G80',n,where,v,i,
                          '63_writer_s',sum(x['wall_ns'] for x in row['per_generation'][:63])/1e9,
                          flush=True)
                    receipt['cases'][f'{n}-{where}']=dict(status='PARTIAL',base_sha256=sha_file(base),
                        base_bytes=base.stat().st_size,build_wall_ns=created,rows=rows)
                    save()
                assert all(row['physical']==rows[0]['physical'] for row in rows), 'physical SHA/byte parity'
                assert len({row['final_index_sha256'] for row in rows})==1,'index parity'
                med={v:statistics.median(sum(x['wall_ns'] for x in row['per_generation'][:63])
                                         +row['init_wall_ns'] for row in rows if row['variant']==v)
                     for v in ('public','owned')}
                ratio=med['owned']/med['public']
                receipt['cases'][f'{n}-{where}'].update(
                    status='COMPLETE',medians_63_ns=med,owned_over_public=ratio,
                    h1_4x=ratio<=.25,physical_sha_parity_64_of_64=True,
                    decision='H1_MECHANISM_PASS' if ratio<=.25 else 'H1_BELOW_FROZEN_HEADROOM')
                save()
        receipt['status']='COMPLETE'
        receipt['decision']='H1_SURVIVES_BOTH_FAMILIES' if all(
            c['h1_4x'] for c in receipt['cases'].values()) else 'H1_BELOW_HEADROOM_IN_AT_LEAST_ONE_FAMILY'
        save()
    except BaseException as exc:
        receipt['status']='FAILED';receipt['error']=repr(exc);save();raise
    print('J24G80 final',receipt['decision'],flush=True)

if __name__=='__main__':main()
