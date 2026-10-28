#!/usr/bin/env python3
"""J24G19 authentic signed delta experiment; product Reader source remains untouched."""
from __future__ import annotations
import argparse, hashlib, json, resource, subprocess, sys, tempfile, time
from pathlib import Path
import msgpack
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_rename
from j24g18_native_reader_court import BODY, append_delta, exact_released_reader
from j24g19_certified_projection import projected, certify, selftest

PARENT = '804ccdc9576b860ff3b9d722c7b1e8ad0ac8176a'
READER_BLOB = 'f13c5492f5acfa1cfcfec97cdbe0da71e41e327b'
PUBLISHED_BLOB = 'e716233403dabd0966863c45635e18fa5ac6afb8'
def digest(b): return hashlib.sha256(b).hexdigest()

class ProjectedReader(CMPCT):
    def _index_from_footer(self, footer_pos):
        # Research override reproduces the inherited traversal exactly, except
        # for the kind-1 projection of ignored fields after signed payload SHA.
        chain=[];pos=footer_pos;depth=0;seen=set()
        while pos and pos not in seen:
            seen.add(pos);g=self._decode_generation_payload(pos)
            if g is None:return None
            kind,payload,prev=g
            if kind==0:
                idx=msgpack.unpackb(payload,raw=False)
                for delta in reversed(chain):
                    for b in delta.get('blobs',[]):idx['blobs'].append(b)
                    for op in delta.get('ops',[]):
                        if op[0]=='put':
                            row=op[1];done=False
                            for i,x in enumerate(idx['files']):
                                if x[0]==row[0]:idx['files'][i]=row;done=True;break
                            if not done:idx['files'].append(row)
                        elif op[0]=='del':idx['files']=[x for x in idx['files'] if x[0]!=op[1]]
                        elif op[0]=='ren':
                            for x in idx['files']:
                                if x[0]==op[1]:x[0]=op[2];break
                    idx['files'].sort(key=lambda x:x[0])
                return idx,depth
            if kind!=1:return None
            chain.append(projected(payload));depth+=1;pos=prev
        return None

READERS={'parent':CMPCT,'projected':ProjectedReader,'published':None}

def worker(path, arm):
    cls=exact_released_reader() if arm=='published' else READERS[arm]
    start_wall=time.perf_counter_ns();start_cpu=time.process_time_ns()
    result={'status':'error','error':None}
    try:
        with cls(Path(path)) as a:
            members={}
            for name in ('owner.bin','renamed.bin'):
                if name in a.by:
                    b=a.read(name)
                    assert b==BODY and a.read_range(name,1,17)==BODY[1:18]
                    members[name]=digest(b)
            a.verify()
            result={'status':'opened','footer':a.latest_footer_pos,
                    'depth':a.delta_depth,'members':members}
    except Exception as e:
        result={'status':'error','error':type(e).__name__}
    result.update(cpu_ns=time.process_time_ns()-start_cpu,
                  wall_ns=time.perf_counter_ns()-start_wall,
                  rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print(json.dumps(result,sort_keys=True))

def run(out,repeats):
    out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','merge-base','--is-ancestor',PARENT,'HEAD'],check=True)
    for ref,sha in [('HEAD',READER_BLOB),
                    ('80c358f8824ec1b20d349c92ed94c898090969b0',PUBLISHED_BLOB)]:
        assert subprocess.check_output(['git','rev-parse',ref+':src/cmpct/reader.py'],text=True).strip()==sha
    assert Path(__file__).read_bytes()==subprocess.check_output(
        ['git','show','HEAD:research/j24g19_signed_reader_court.py'])
    tests=selftest()
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);tree=root/'tree';tree.mkdir()
        (tree/'owner.bin').write_bytes(BODY)
        base=root/'base.cmpct';Builder(tree).build(base)
        with CMPCT(base) as a:
            checkpoint=a.latest_footer_pos
            assert checkpoint>0
        writer=root/'writer.cmpct';writer.write_bytes(base.read_bytes())
        append_rename(writer,'owner.bin','renamed.bin')
        ren=[['ren','owner.bin','renamed.bin']]
        large={'blobs':[],'ops':ren,'extension':[{'x':0} for _ in range(200000)]}
        unicode={'blobs':[],'ops':ren,'extension':[{'clé':0} for _ in range(1000)]}
        items={
            'linked-large':(msgpack.packb(large,use_bin_type=True),checkpoint),
            'orphan-large':(msgpack.packb(large,use_bin_type=True),0),
            'linked-unicode':(msgpack.packb(unicode,use_bin_type=True),checkpoint),
            'linked-small':(msgpack.packb({'blobs':[],'ops':ren,'extension':[{'x':0}]*50}),checkpoint),
            'malformed':(bytes.fromhex('81 a1 78 81 91 01 c0'),checkpoint)}
        p=msgpack.Packer(use_bin_type=True)
        items['linked-duplicate']=(b'\x83'+p.pack('blobs')+p.pack([])+
            p.pack('ops')+p.pack([])+p.pack('ops')+p.pack(ren),checkpoint)
        cases={'checkpoint':base,'writer':writer};signed={}
        for name,(payload,prev) in items.items():
            path=root/(name+'.cmpct')
            signed[name]=dict(append_delta(base,path,payload,prev),certified=certify(payload)[0])
            cases[name]=path
        raw={};files={}
        for case,source in cases.items():
            path=out/'physical'/(case+'.cmpct');path.parent.mkdir(exist_ok=True)
            path.write_bytes(source.read_bytes())
            files[case]={'relative':str(path.relative_to(out)),
                         'sha256':digest(path.read_bytes()),'bytes':path.stat().st_size,
                         'signed':signed.get(case)}
            raw[case]={}
            for arm in READERS:
                records=[]
                for i in range(repeats):
                    p=subprocess.run([sys.executable,__file__,'--worker',str(path),arm],
                                     capture_output=True,text=True)
                    assert p.returncode==0,(case,arm,p.stderr,p.stdout)
                    records.append(json.loads(p.stdout))
                raw[case][arm]=records
        for arm in READERS:
            for case,member,depth in [('checkpoint','owner.bin',0),('writer','renamed.bin',1),
                    ('linked-large','renamed.bin',1),('orphan-large','owner.bin',0),
                    ('linked-unicode','renamed.bin',1),('linked-small','renamed.bin',1),
                    ('linked-duplicate','renamed.bin',1)]:
                assert all(r['status']=='opened' and r['depth']==depth and
                    r['members'].get(member)==digest(BODY) for r in raw[case][arm]),(case,arm)
            assert all(r['status']=='error' for r in raw['malformed'][arm]),arm
            assert all(r['footer']>checkpoint for r in raw['linked-large'][arm])
            assert all(r['footer']==checkpoint for r in raw['orphan-large'][arm])
        assert signed['linked-large']['certified'] and not signed['linked-unicode']['certified']
        result={'schema':'cmpct-j24g19-signed-reader-court-v1',
                'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                'reader_blob':READER_BLOB,'published_blob':PUBLISHED_BLOB,
                'body_sha256':digest(BODY),'checkpoint':checkpoint,
                'selftest':tests,'files':files,'observations':raw,
                'product_changes':0,'release_credit':0}
        (out/'signed_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print('J24G19_SIGNED_READER_COURT=PASS cases='+str(len(cases))+' arms=3 repeats='+str(repeats))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--worker',nargs=2)
    ap.add_argument('--out',type=Path,default=Path('j24g19-artifacts'))
    ap.add_argument('--repeats',type=int,default=3)
    a=ap.parse_args()
    if a.worker:worker(*a.worker)
    else:run(a.out,a.repeats)
