#!/usr/bin/env python3
"""J24G101 independent POSIX O0: root rebasing vs selected older Reader identity.

No CMPCT Reader/Writer import or format/ABI mutation. Genuine revision-24 bytes
are verified against original provider ZIP SHA and exact preceding footer.
"""
from __future__ import annotations
import argparse,fcntl,hashlib,io,json,multiprocessing as mp,os,tempfile,time,zipfile
from pathlib import Path
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,require

def sha(b): return hashlib.sha256(b).hexdigest()
def write(p,b):
    with open(p,'xb',buffering=0) as f:
        f.write(b);os.fsync(f.fileno())
def dirsync(d):
    fd=os.open(d,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try:os.fsync(fd)
    finally:os.close(fd)
def fread(fd,n):
    b=os.pread(fd,n,0);require(len(b)==n,'short file descriptor read');return b
def blocks(p):return p.stat().st_blocks*512
def manifest(bname,b,tname,t,g):
    return {'schema':'J24G101-REBASE-O0','generation':g,
            'base':{'name':bname,'size':len(b),'sha256':sha(b)},
            'tail':{'name':tname,'size':len(t),'sha256':sha(t)},
            'archive_sha256':sha(b+t),'archive_size':len(b)+len(t)}
def encode(x):return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def init(d,base,tail,bname):
    write(d/'epoch.gate',b'');write(d/bname,base);write(d/'tail-062.bin',tail)
    write(d/'HEAD',encode(manifest(bname,base,'tail-062.bin',tail,62)));dirsync(d)
def child(d,expected,pipe,mode):
    bf=None;tf=None
    try:
        with open(d/'epoch.gate','rb',buffering=0) as gate:
            fcntl.flock(gate,fcntl.LOCK_SH)
            m=json.loads((d/'HEAD').read_bytes())
            tf=os.open(d/m['tail']['name'],os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
            fcntl.flock(tf,fcntl.LOCK_SH)
            if mode=='owned':
                bf=os.open(d/m['base']['name'],os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
                fcntl.flock(bf,fcntl.LOCK_SH)
            fcntl.flock(gate,fcntl.LOCK_UN)
        pipe.send({'stage':'pinned','generation':m['generation'],
                   'owned_base_allocated':os.fstat(bf).st_blocks*512 if bf is not None else 0})
        require(pipe.recv()=='continue','child release')
        b=fread(bf,m['base']['size']) if bf is not None else (d/m['base']['name']).read_bytes()
        t=fread(tf,m['tail']['size'])
        good=(len(b)==m['base']['size'] and sha(b)==m['base']['sha256']
              and sha(t)==m['tail']['sha256'] and b+t==expected
              and sha(b+t)==m['archive_sha256'])
        pipe.send({'stage':'read','correct':good,
                   'base_sha_matches':sha(b)==m['base']['sha256'],
                   'tail_sha_matches':sha(t)==m['tail']['sha256'],
                   'consumed_sha256':sha(b+t),'consumed_bytes':len(b+t),
                   'expected_sha256':sha(expected)})
        require(pipe.recv()=='finish','child finish')
    except BaseException as e:
        try:pipe.send({'stage':'error','reason':str(e)})
        except Exception:pass
        raise
    finally:
        if bf is not None:os.close(bf)
        if tf is not None:os.close(tf)
        pipe.close()
def recv(p,stage):
    require(p.poll(15),'child stage timeout '+stage)
    x=p.recv();require(x['stage']==stage,'unexpected child stage '+str(x));return x
def rebase(d,base,tail,mode):
    name='base.bin' if mode!='versioned' else 'base-063.bin'
    write(d/'next-base.tmp',base);write(d/'tail-063.bin',tail)
    write(d/'next-head.tmp',encode(manifest(name,base,'tail-063.bin',tail,63)))
    with open(d/'epoch.gate','rb',buffering=0) as gate:
        fcntl.flock(gate,fcntl.LOCK_EX)
        os.replace(d/'next-base.tmp',d/name)
        os.replace(d/'next-head.tmp',d/'HEAD')
        dirsync(d);fcntl.flock(gate,fcntl.LOCK_UN)
def one(raw,key,mode):
    chain=parse_chain(raw)
    require(len(chain)==64,'authentic 64 footers')
    ends=[f['pos']+68 for f in chain]
    require(ends[-1]==len(raw),'source tail at EOF')
    root=raw[:ends[0]];old=raw[ends[0]:ends[-2]]
    previous=raw[:ends[-2]];newbase=previous;newtail=raw[ends[-2]:]
    ctx=mp.get_context('spawn')
    with tempfile.TemporaryDirectory(prefix='j24g101-') as name:
        d=Path(name);bname='base-000.bin' if mode=='versioned' else 'base.bin'
        init(d,root,old,bname);original_base_blocks=blocks(d/bname)
        a,b=ctx.Pipe();proc=ctx.Process(target=child,args=(d,previous,b,mode))
        proc.start();b.close()
        pinned=recv(a,'pinned')
        require(pinned['generation']==62,'reader selected wrong historical generation')
        t0=time.perf_counter_ns();rebase(d,newbase,newtail,mode)
        wall_ms=(time.perf_counter_ns()-t0)/1e6
        m=json.loads((d/'HEAD').read_text())
        latest=(d/m['base']['name']).read_bytes()+(d/m['tail']['name']).read_bytes()
        require(latest==raw,'newly published archive not actual source')
        current=sum(blocks(d/f) for f in (m['base']['name'],m['tail']['name'],'HEAD'))
        oldtail_blocks=blocks(d/'tail-062.bin')
        retained_base=(original_base_blocks if mode=='versioned'
                       else pinned['owned_base_allocated'])
        if mode in ('owned','versioned'):
            require(retained_base==original_base_blocks,'old base not retained')
        with open(d/'tail-062.bin','rb',buffering=0) as old_fd:
            try:fcntl.flock(old_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:held=True
            else:
                held=False;fcntl.flock(old_fd,fcntl.LOCK_UN)
        require(held,'reader tail not locked')
        a.send('continue');reading=recv(a,'read')
        require(reading['correct']==(mode!='pathname'),'unexpected old prefix result')
        if mode=='pathname':require(not reading['base_sha_matches'],'pathname rebase failed to change base')
        else:require(reading['consumed_sha256']==sha(previous),'owned reader wrong previous source')
        a.send('finish');proc.join(15)
        require(proc.exitcode==0,'reader process failure')
        a.close()
        with open(d/'tail-062.bin','rb',buffering=0) as old_fd:
            fcntl.flock(old_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        (d/'tail-062.bin').unlink()
        if mode=='versioned':(d/'base-000.bin').unlink()
        dirsync(d)
        return {'mode':mode,'source_sha256':sha(raw),'archive_bytes':len(raw),
                'old_archive_bytes':len(previous),'old_base_bytes':len(root),
                'new_tail_bytes':len(newtail),'latest_sha256':sha(latest),
                'reader':reading,'correct_old_snapshot':reading['correct'],
                'tail_lease_confirmed':held,'old_tail_reclaimed':not (d/'tail-062.bin').exists(),
                'old_base_original_allocated':original_base_blocks,
                'old_base_retained_allocated':retained_base,
                'old_tail_retained_allocated':oldtail_blocks,
                'current_allocated':current,
                'retained_peak_ratio':(current+retained_base+oldtail_blocks)/max(1,current),
                'publish_wall_ms':wall_ms}
def hostile(raw):
    nodes=parse_chain(raw);b=raw[:nodes[0]['pos']+68]
    with tempfile.TemporaryDirectory(prefix='j24g101-adversary-') as dn:
        p=Path(dn)/'root.bin';write(p,b)
        fd=os.open(p,os.O_RDONLY);fcntl.flock(fd,fcntl.LOCK_SH)
        st=os.fstat(fd)
        with open(p,'r+b',buffering=0) as w:
            w.write(bytes([b[0]^1]));os.fsync(w.fileno())
        changed=fread(fd,len(b));now=os.fstat(fd)
        require(changed!=b and sha(changed)!=sha(b),'FD incorrectly assumed immutable')
        require((st.st_dev,st.st_ino,st.st_size)==(now.st_dev,now.st_ino,now.st_size),'not same inode control')
        with open(p,'r+b',buffering=0) as w:w.write(b[:1]);os.fsync(w.fileno())
        require(fread(fd,len(b))==b,'restore mutated source')
        os.close(fd)
        return {'same_inode_and_size':True,'digest_detects_mutation':True,
                'shared_advisory_lock_does_not_block_noncooperative_writer':True}
def main():
    p=argparse.ArgumentParser()
    for key in ('deep-ubuntu','deep-windows'):p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();out={'schema':'J24G101-REBASE-BASE-OWNERSHIP-O0-v1',
        'host':'Linux','cases':{},'hostile':{},
        'limitations':['Linux POSIX cooperative 1-writer O0 only','not installed CMPCT API',
        'no power-fail atomicity or multiwriter CAS','base and tail mutable by noncooperative same-UID actor',
        'directory/inode metadata and cross-platform costs not measured']}
    for key in ('deep-ubuntu','deep-windows'):
        zipped=getattr(args,key.replace('-','_')).read_bytes()
        expect,source,filenames=ZIP_CASES[key]
        require(sha(zipped)==expect,'provider SHA')
        with zipfile.ZipFile(io.BytesIO(zipped)) as archive:
            require(archive.read('checkout-head.txt').decode().strip()==source,'source commit identity')
            for filename in filenames:
                if not filename.endswith('-A.cmpct'):continue
                name=key+'/'+filename;raw=archive.read(filename)
                out['cases'][name]={mode:one(raw,name,mode) for mode in ('pathname','owned','versioned')}
                out['hostile'][name]=hostile(raw)
    require(len(out['cases'])==4,'four original Writer A histories required')
    require(all(not v['pathname']['correct_old_snapshot'] and
                v['owned']['correct_old_snapshot'] and v['versioned']['correct_old_snapshot']
                for v in out['cases'].values()),'scope decision changed')
    out['verdict']='LOCAL_ROOT_REBASE_PATHNAME_FAIL_OWNED_AND_VERSIONED_PASS'
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'verdict':out['verdict'],'scenarios':len(out['cases'])*3,
                      'same_inode_hostiles':len(out['hostile']),
                      'report_sha256':sha(args.output.read_bytes())},sort_keys=True))
if __name__=='__main__':main()
