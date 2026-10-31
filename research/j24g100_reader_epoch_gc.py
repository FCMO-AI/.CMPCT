#!/usr/bin/env python3
"""J24G100: physical POSIX cooperative-reader epoch GC court, not CMPCT product code."""
from __future__ import annotations
import argparse,fcntl,hashlib,io,json,multiprocessing as mp,os,signal,tempfile,time,zipfile
from pathlib import Path
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,require

def digest(b): return hashlib.sha256(b).hexdigest()

def write_fsync(p,data):
    with open(p,'xb',buffering=0) as f:
        f.write(data);os.fsync(f.fileno())

def syncdir(root):
    fd=os.open(root,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try:os.fsync(fd)
    finally:os.close(fd)

def manifest_for(base,tail,g):
    return {'schema':'J24G100-EPOCH-O0','generation':g,
      'base':{'name':'base.bin','sha256':digest(base),'size':len(base)},
      'tail':{'name':f'tail-{g:03d}.bin','sha256':digest(tail),'size':len(tail)},
      'archive_sha256':digest(base+tail),'archive_size':len(base)+len(tail)}

def latest(root):
    m=json.loads((root/'HEAD').read_bytes())
    require(m['schema']=='J24G100-EPOCH-O0','manifest schema')
    return m

def publish(root,base,tail,g):
    # Single cooperative writer. The gate covers publication versus GC, NOT writer CAS.
    name=f'tail-{g:03d}.bin';write_fsync(root/name,tail);os.chmod(root/name,0o444)
    data=manifest_for(base,tail,g)
    body=(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n').encode()
    write_fsync(root/'HEAD.tmp',body)
    with open(root/'epoch.gate','rb',buffering=0) as gate:
        fcntl.flock(gate,fcntl.LOCK_EX)
        os.replace(root/'HEAD.tmp',root/'HEAD');syncdir(root)
        fcntl.flock(gate,fcntl.LOCK_UN)
    return len(body)

def retire(root,use_gate=True):
    t0=time.perf_counter_ns();removed=[];held=[]
    with open(root/'epoch.gate','rb',buffering=0) as gate:
        if use_gate:fcntl.flock(gate,fcntl.LOCK_EX)
        chosen=latest(root)['tail']['name']
        for path in sorted(root.glob('tail-*.bin')):
            if path.name==chosen:continue
            fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
            try:
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    held.append(path.name);continue
                os.unlink(path);removed.append(path.name)
            finally:os.close(fd)
        if removed:syncdir(root)
        if use_gate:fcntl.flock(gate,fcntl.LOCK_UN)
    return {'removed':removed,'held':held,'wall_ms':(time.perf_counter_ns()-t0)/1e6}

def read_selected(root,m,tailfd,raw):
    base=(root/m['base']['name']).read_bytes();tm=m['tail']
    tail=os.pread(tailfd,tm['size'],0)
    require(len(tail)==tm['size'] and digest(tail)==tm['sha256'],'tail corruption')
    require(digest(base)==m['base']['sha256'],'base corruption')
    both=base+tail
    require(len(both)==m['archive_size'] and digest(both)==m['archive_sha256'],'archive integrity')
    require(both==raw[:len(both)],'authentic CMPCT prefix mismatch')
    return len(both)

def child_reader(rootname,raw,pipe,mode):
    root=Path(rootname)
    try:
        with open(root/'epoch.gate','rb',buffering=0) as gate:
            if mode!='unsafe':fcntl.flock(gate,fcntl.LOCK_SH)
            m=latest(root);pipe.send({'stage':'read-head','gen':m['generation']})
            if mode in ('delayed','unsafe'):
                require(pipe.recv()=='continue','child start')
            try:fd=os.open(root/m['tail']['name'],os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
            except FileNotFoundError:
                if mode=='unsafe':pipe.send({'stage':'enoent'});return
                raise
            try:
                fcntl.flock(fd,fcntl.LOCK_SH)
                if mode!='unsafe':fcntl.flock(gate,fcntl.LOCK_UN)
                read_selected(root,m,fd,raw)
                pipe.send({'stage':'pinned','gen':m['generation']})
                require(pipe.recv()=='continue','child finish')
                read_selected(root,m,fd,raw);pipe.send({'stage':'done'})
            finally:os.close(fd)
    except Exception as exc:
        try:pipe.send({'stage':'error','reason':str(exc)})
        except Exception:pass
        raise

def spawn(ctx,root,raw,mode):
    parent,child=ctx.Pipe()
    proc=ctx.Process(target=child_reader,args=(str(root),raw,child,mode))
    proc.start();child.close();return proc,parent

def expect(pipe,stage):
    require(pipe.poll(8),f'missing {stage}')
    actual=pipe.recv()
    require(actual['stage']==stage,f'expected {stage}; received {actual}')
    return actual

def join(proc):
    proc.join(8)
    require(not proc.is_alive() and proc.exitcode==0,f'child failure {proc.exitcode}')

def setup(root,raw,ends):
    base=raw[:ends[0]];old=raw[ends[0]:ends[-2]];new=raw[ends[0]:ends[-1]]
    write_fsync(root/'epoch.gate',b'')
    write_fsync(root/'base.bin',base);os.chmod(root/'base.bin',0o444)
    publish(root,base,old,len(ends)-2)
    return base,new

def active(root):
    m=latest(root)
    paths=[root/'base.bin',root/m['tail']['name'],root/'HEAD']
    return {'allocated_bytes':sum(p.stat().st_blocks*512 for p in paths),
            'tail_count':len(list(root.glob('tail-*.bin'))),'generation':m['generation']}

def run_case(raw,name):
    nodes=parse_chain(raw)
    require(len(nodes)==64,'authentic 64-footer source required')
    ends=[n['pos']+68 for n in nodes]
    require(ends[-1]==len(raw),'source complete')
    ctx=mp.get_context('spawn')
    report={'name':name,'source_sha256':digest(raw),'source_bytes':len(raw),'footer_count':len(nodes),'cases':{}}
    # H1A: reader already holds a verified, pinned old-tail FD.
    with tempfile.TemporaryDirectory(prefix='j24g100-held-') as td:
        root=Path(td);base,new=setup(root,raw,ends)
        p,c=spawn(ctx,root,raw,'hold');expect(c,'read-head');expect(c,'pinned')
        publish(root,base,new,63);first=retire(root)
        require(first['held']==['tail-062.bin'] and not first['removed'],'GC removed held tail')
        c.send('continue');expect(c,'done');join(p)
        second=retire(root)
        require(second['removed']==['tail-062.bin'] and not second['held'],'GC failed after release')
        require((root/'base.bin').read_bytes()+(root/'tail-063.bin').read_bytes()==raw,'latest bytes')
        report['cases']['held_reader_gc']={'pass':True,'first':first,'second':second,'active':active(root)}
    # H1B: reader has selected old manifest but has not yet opened tail.
    with tempfile.TemporaryDirectory(prefix='j24g100-gate-') as td:
        root=Path(td);base,new=setup(root,raw,ends)
        p,c=spawn(ctx,root,raw,'delayed');expect(c,'read-head')
        with open(root/'epoch.gate','rb',buffering=0) as gate:
            blocked=False
            try:fcntl.flock(gate,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:blocked=True
            else:fcntl.flock(gate,fcntl.LOCK_UN)
        require(blocked,'writer/GC exclusive gate was not blocked')
        c.send('continue');expect(c,'pinned')
        publish(root,base,new,63);first=retire(root)
        require(first['held']==['tail-062.bin'],'delayed reader not protected')
        c.send('continue');expect(c,'done');join(p)
        second=retire(root)
        require(second['removed']==['tail-062.bin'],'delayed old tail not GCed')
        report['cases']['delayed_manifest_open']={'pass':True,'gate_exclusion':blocked,
            'first':first,'second':second,'active':active(root)}
    # H3 stronger negative: exact same prefix, but omit gate registration.
    with tempfile.TemporaryDirectory(prefix='j24g100-unsafe-') as td:
        root=Path(td);base,new=setup(root,raw,ends)
        p,c=spawn(ctx,root,raw,'unsafe');expect(c,'read-head')
        publish(root,base,new,63);first=retire(root,use_gate=False)
        require(first['removed']==['tail-062.bin'],'negative GC did not remove old tail')
        c.send('continue');expect(c,'enoent');join(p)
        report['cases']['no_gate_negative']={'pass':True,'confirmed_ENOENT':True,
            'removed':first['removed']}
    # H2: SIGKILL releases the shared advisory lock and GC can reclaim.
    with tempfile.TemporaryDirectory(prefix='j24g100-dead-') as td:
        root=Path(td);base,new=setup(root,raw,ends)
        p,c=spawn(ctx,root,raw,'hold');expect(c,'read-head');expect(c,'pinned')
        publish(root,base,new,63);first=retire(root)
        require(first['held']==['tail-062.bin'],'kill setup missing lock')
        os.kill(p.pid,signal.SIGKILL);p.join(8)
        require(not p.is_alive() and p.exitcode==-signal.SIGKILL,'child death not established')
        second=retire(root)
        require(second['removed']==['tail-062.bin'],'crashed reader lease not released')
        report['cases']['abnormal_exit']={'pass':True,'first':first,'second':second,'active':active(root)}
    return report

def main():
    ap=argparse.ArgumentParser()
    for k in ('deep-ubuntu','deep-windows'):ap.add_argument('--'+k,required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    report={'schema':'J24G100-POSIX-READER-EPOCH-O0-v1','host':os.uname().sysname,
      'cases':{},'limitations':['POSIX cooperative advisory locks; not Windows/macOS',
      'Single writer; no CAS/multiwriter protection or untrusted same-UID writers',
      'Not installed CMPCT Reader/Writer or real power failure',
      'SHA in same untrusted manifest does not authenticate file provenance',
      'GC must coordinate with EVERY reader and manifest publisher']}
    for k in ('deep-ubuntu','deep-windows'):
        data=getattr(args,k.replace('-','_')).read_bytes()
        expected,source_head,names=ZIP_CASES[k]
        require(digest(data)==expected,'original provider SHA')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(z.read('checkout-head.txt').decode().strip()==source_head,'source commit SHA')
            for name in names:report['cases'][k+'/'+name]=run_case(z.read(name),k+'/'+name)
    require(len(report['cases'])==4 and all(len(v['cases'])==4 and
      all(x['pass'] for x in v['cases'].values()) for v in report['cases'].values()),'incomplete cases')
    report['verdict']='POSIX_COOPERATIVE_READER_EPOCH_H1_H2_PASS_NO_GATE_RACE_CONFIRMED'
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'verdict':report['verdict'],'original_cases':len(report['cases']),
      'physical_scenarios':sum(len(x['cases']) for x in report['cases'].values()),
      'report_sha256':digest(args.output.read_bytes())},sort_keys=True))

if __name__=='__main__':main()
