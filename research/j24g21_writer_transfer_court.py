#!/usr/bin/env python3
"""J24G21: signed first-party Writer delta transfer court (RESEARCH ONLY).

Runs actual installed Builder/Writer and both real Reader classes; measures the
exact C-certified J24G19 research helper versus untouched MessagePack decode.
Product reader, codec, format, and release remain unchanged.
"""
from __future__ import annotations
import argparse, hashlib, json, os, random, shutil, statistics, subprocess, sys, tempfile, time
from pathlib import Path
import msgpack
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import FTR, FMAGIC, zd
from cmpct.transactions import append_rename, append_delete, append_update
from j24g19_signed_reader_court import ProjectedReader
from j24g19_certified_projection import certify, projected, direct

EXPECTED_READER_BLOB="f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PUBLISHED_READER_BLOB="e716233403dabd0966863c45635e18fa5ac6afb8"
PREREG="f918be061af16c1dbea8b6ad5888932676f2d53f"

def sha(x):return hashlib.sha256(x).hexdigest()
def delta_from_physical(path):
    data=path.read_bytes()
    magic,kind,codec,flags,res,cs,us,prev,ph=FTR.unpack_from(data,len(data)-FTR.size)
    assert magic==FMAGIC and kind==1 and flags==0 and res==0 and prev>0
    enc=data[-FTR.size-cs:-FTR.size]
    raw=enc if codec==0 else zd(enc,us)
    assert codec in (0,1) and len(raw)==us and sha(raw)==ph.hex()
    obj=msgpack.unpackb(raw,raw=False)
    assert isinstance(obj,dict) and set(obj)=={'ops','blobs'}, obj.keys()
    yes,_=certify(raw)
    assert projected(raw)==obj, ("semantic mismatch",path)
    return {'sha256':sha(raw),'encoded_bytes':cs,'decoded_bytes':us,'codec':codec,
            'certified':yes,'known_fields_exact':True,'ignored_fields':0,
            'physical_sha256':sha(data),'physical_bytes':len(data),
            'footer_position':len(data)-FTR.size,'prev_footer':prev}

def decode_worker(payload_path,arm,loops):
    b=Path(payload_path).read_bytes()
    f=direct if arm=='direct' else projected
    for _ in range(10):f(b)
    c0=time.process_time_ns();w0=time.perf_counter_ns()
    for _ in range(loops):f(b)
    return {'arm':arm,'loops':loops,'cpu_ns':time.process_time_ns()-c0,
            'wall_ns':time.perf_counter_ns()-w0,'input_sha256':sha(b)}
def read_worker(path,arm):
    cls=CMPCT if arm=='parent' else ProjectedReader
    t0=time.perf_counter_ns();c0=time.process_time_ns()
    with cls(Path(path)) as ar:
        members={n:sha(ar.read(n)) for n in sorted(ar.by) if ar.by[n][1]==0}
        for n in members:
            raw=ar.read(n)
            assert ar.read_range(n,0,min(len(raw),27))==raw[:27]
        verified=ar.verify()
        result={'status':'opened','footer':ar.latest_footer_pos,'depth':ar.delta_depth,
                'members':members,'verified':verified,'names':sorted(ar.by)}
    result.update(arm=arm,cpu_ns=time.process_time_ns()-c0,wall_ns=time.perf_counter_ns()-t0)
    return result
def run(out,repeats):
    out.mkdir(parents=True,exist_ok=True);physical=out/'physical';physical.mkdir(exist_ok=True)
    assert subprocess.check_output(['git','rev-parse','HEAD:src/cmpct/reader.py'],text=True).strip()==EXPECTED_READER_BLOB
    assert subprocess.check_output(['git','rev-parse','80c358f8824ec1b20d349c92ed94c898090969b0:src/cmpct/reader.py'],text=True).strip()==PUBLISHED_READER_BLOB
    assert subprocess.run(['git','merge-base','--is-ancestor',PREREG,'HEAD']).returncode==0
    # The actual signed archive, not a handmade signed delta, is the primary court.
    with tempfile.TemporaryDirectory(prefix='j24g21-writer-') as t:
        root=Path(t);tree=root/'tree';tree.mkdir()
        body=bytes((i*73+19)%256 for i in range(1024))
        (tree/'owner.bin').write_bytes(body)
        base=root/'base.cmpct';Builder(tree).build(base)
        pairs={}
        for name in ('rename','delete','update','rename_unicode','rename_long'):
            path=physical/(name+'.cmpct');shutil.copyfile(base,path)
            if name=='rename':append_rename(path,'owner.bin','renamed.bin')
            elif name=='delete':append_delete(path,'owner.bin')
            elif name=='update':
                src=root/'replacement.bin';src.write_bytes(bytes((i*37+5)%256 for i in range(3096)))
                append_update(path,'owner.bin',src)
            elif name=='rename_unicode':append_rename(path,'owner.bin','café.txt')
            else:append_rename(path,'owner.bin','owner-'+'A'*72+'.bin')
            pairs[name]=path
        # Original two-source control: first-party Builder-only checkpoint is not a delta.
        checkpoint=physical/'checkpoint.cmpct';shutil.copyfile(base,checkpoint)
    payloads={};rows={};raw_cpu={};reads={}
    rng=random.Random(2026102821)
    for name,path in pairs.items():
        delta=delta_from_physical(path)
        buf=path.read_bytes()
        enc=buf[-FTR.size-delta['encoded_bytes']:-FTR.size]
        raw=enc if delta['codec']==0 else zd(enc,delta['decoded_bytes'])
        payload_path=out/(name+'.mpk');payload_path.write_bytes(raw)
        payloads[name]=delta;records=[]
        loops=700 if len(raw)<1024 else (100 if len(raw)<50000 else 10)
        for block in range(repeats):
            order=['direct','projected','projected','direct']
            if rng.randrange(2):order.reverse()
            for arm in order:
                p=subprocess.run([sys.executable,__file__,'--decode-worker',str(payload_path),arm,str(loops)],
                                  text=True,capture_output=True)
                assert p.returncode==0,(name,arm,p.stdout,p.stderr)
                row=json.loads(p.stdout);row['block']=block;records.append(row)
        raw_cpu[name]=records
        observations={}
        for arm in ('parent','projected'):
            rr=[]
            for i in range(repeats):
                p=subprocess.run([sys.executable,__file__,'--read-worker',str(path),arm],
                                  text=True,capture_output=True)
                assert p.returncode==0,(name,arm,p.stdout,p.stderr)
                row=json.loads(p.stdout);row['repeat']=i;rr.append(row)
            observations[arm]=rr
        for a,b in zip(observations['parent'],observations['projected']):
            assert a['status']==b['status']=='opened' and a['footer']==b['footer']
            assert a['depth']==b['depth']==1 and a['members']==b['members']
            assert a['names']==b['names'] and a['verified']==b['verified']
        reads[name]=observations
        row={}
        for arm in ('direct','projected'):
            subset=[v for v in records if v['arm']==arm]
            row[arm+'_cpu_ns_per_decode']=statistics.median(x['cpu_ns']/x['loops'] for x in subset)
            row[arm+'_wall_ns_per_decode']=statistics.median(x['wall_ns']/x['loops'] for x in subset)
        row['cpu_ratio']=row['projected_cpu_ns_per_decode']/row['direct_cpu_ns_per_decode']
        rows[name]=row
    result={'schema':'cmpct-j24g21-first-party-writer-v1',
            'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'parent':'e24f9b1ed58ba6208b53bdd8d92aacb48e7442ed',
            'released_main':'80c358f8824ec1b20d349c92ed94c898090969b0',
            'reader_blob':EXPECTED_READER_BLOB,
            'published_reader_blob':PUBLISHED_READER_BLOB,
            'version':'0.30.0','format':24,'physical_payloads':payloads,
            'summary':rows,'raw_decode':raw_cpu,'raw_reader':reads,
            'all_first_party_ignored_fields_absent':True,
            'all_readers_semantics_equal':True,
            'no_product_source_changes':True,'release_credit':0}
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps({'result':'PASS','summary':rows,'physical_payloads':payloads},sort_keys=True,ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--decode-worker',nargs=3)
    ap.add_argument('--read-worker',nargs=2)
    ap.add_argument('--out',type=Path,default=Path('j24g21-artifacts'))
    ap.add_argument('--repeats',type=int,default=5)
    a=ap.parse_args()
    if a.decode_worker:print(json.dumps(decode_worker(a.decode_worker[0],a.decode_worker[1],int(a.decode_worker[2]))))
    elif a.read_worker:print(json.dumps(read_worker(*a.read_worker)))
    else:run(a.out,a.repeats)
