#!/usr/bin/env python3
"""J24I21: independent oracle that demonstrates proof reuse's mutable-source debt.

Research only: never modifies CMPCT or weakens its installed tests.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import tempfile
import time

READER_BLOB = 'f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f'
SIZES = [(2 << 20, 1), (64 << 20, 32)]


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for piece in iter(lambda:f.read(1 << 20),b''):h.update(piece)
    return h.hexdigest()


def reader_identity():
    import cmpct.reader as rm
    path=Path(rm.__file__).resolve()
    raw=path.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
    assert blob==READER_BLOB,('installed Reader provenance mismatch',path,blob)
    return {'path':str(path),'git_blob':blob}


def first_blob_payload(reader,owner):
    from cmpct.codec import BHDR, S_SPARSE
    assert owner[6][0]==S_SPARSE and owner[6][1]
    extent=owner[6][1][0]
    assert extent[2]
    idx=extent[2][0]
    pos=reader.record_base+reader.blobs[idx][0]
    hdr=BHDR.unpack_from(reader.mm,pos)
    meta_len=hdr[-3]  # BHDR: magic, codec, flags, reserved, us, cs, ml, crc, sha
    physical=pos+BHDR.size+meta_len
    assert 0 <= physical < reader.mm.size()
    return physical,idx


def run_child(path,mode,race):
    from cmpct.reader import CMPCT
    from cmpct.codec import K_DIR,K_FILE,K_HARDLINK,S_SPARSE
    who=reader_identity()
    before=digest(path)
    count=0
    touched=[]
    verified_names=0
    t0=time.perf_counter_ns()
    c0=time.process_time_ns()
    with CMPCT(path) as reader:
        owner=reader.by['a-owner.bin']
        assert owner[1]==K_FILE and owner[6][0]==S_SPARSE
        assert sum(row[1]==K_HARDLINK for row in reader.files)>=1
        unmodified=reader._verify_sparse_streamed
        done=set()
        def probe(row):
            nonlocal count
            if mode=='cache-oracle' and row[0] in done:
                return
            result=unmodified(row)
            count+=1
            if mode=='cache-oracle':done.add(row[0])
            if race and count==1:
                offset,idx=first_blob_payload(reader,owner)
                with path.open('r+b') as f:
                    f.seek(offset)
                    original=f.read(1)
                    assert len(original)==1
                    f.seek(offset)
                    f.write(bytes([original[0]^1]))
                    f.flush()
                    os.fsync(f.fileno())
                touched.append({'offset':offset,'blob_index':idx,
                                'from':original.hex(),'to':f'{original[0]^1:02x}'})
            return result
        reader._verify_sparse_streamed=probe
        error=None
        try: verified_names=reader.verify()
        except (IOError,ValueError,EOFError,RuntimeError) as exc:
            error=type(exc).__name__+': '+str(exc)
        member_count=sum(row[1]!=K_DIR for row in reader.files)
    wall=time.perf_counter_ns()-t0
    cpu=time.process_time_ns()-c0
    after=digest(path)
    return {'mode':mode,'race':race,'reader':who,'logical_size':owner[4],
            'member_count':member_count,'verified_names':verified_names,
            'streamed_sha_calls':count,'error':error,'accepted':error is None,
            'source_sha_before':before,'source_sha_after':after,
            'tamper':touched,'wall_ns':wall,'cpu_ns':cpu,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def make_archive(root,size,alias_count):
    from cmpct.builder import Builder
    from cmpct.codec import K_HARDLINK,K_FILE,S_SPARSE
    from cmpct.reader import CMPCT
    tree=root/'tree';tree.mkdir()
    owner=tree/'a-owner.bin'
    with owner.open('wb') as f:
        f.write(b'A'*4096)
        f.seek(size-4096)
        f.write(b'Z'*4096)
    physical_allocation=owner.stat().st_blocks*512
    assert physical_allocation < size//4,('host filesystem did not create sparse file',physical_allocation)
    for i in range(alias_count):os.link(owner,tree/f'z-link-{i:05d}.bin')
    source=root/'source.cmpct'
    Builder(tree,workers=1,reproducible=True).build(source)
    with CMPCT(source) as r:
        assert len(r.files)==alias_count+1
        assert r.by['a-owner.bin'][1]==K_FILE
        assert r.by['a-owner.bin'][6][0]==S_SPARSE
        assert sum(row[1]==K_HARDLINK for row in r.files)==alias_count
        assert all(row[4]==size for row in r.files)
    return source,physical_allocation


def call(script,path,mode,race):
    proc=subprocess.run([sys.executable,str(script),'--child',str(path),mode,str(int(race))],
        capture_output=True,text=True,cwd=path.parent,timeout=120)
    if proc.returncode:raise RuntimeError(f'child mode={mode} race={race} rc={proc.returncode}: {proc.stderr[-3000:]}')
    return json.loads(proc.stdout)


def main():
    if sys.platform!='linux':raise RuntimeError('Linux-only physically sparse controlled-mutation court')
    reader_identity()
    evidence=Path(os.environ.get('J24I21_EVIDENCE_DIR',tempfile.mkdtemp(prefix='j24i21-artifacts-')))
    evidence.mkdir(parents=True,exist_ok=True)
    observations=[]
    script=Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix='j24i21-source-') as name:
        work=Path(name)
        for size,aliases in SIZES:
            case=work/f'{size}-{aliases}';case.mkdir()
            source,physical=make_archive(case,size,aliases)
            source_sha=digest(source)
            archive_target=evidence/f'source-{size}-{aliases}.cmpct'
            shutil.copyfile(source,archive_target)
            trials=[]
            for index,mode in enumerate(['baseline','cache-oracle','cache-oracle','baseline']):
                record=call(script,source,mode,False)
                assert record['reader']['git_blob']==READER_BLOB
                assert record['source_sha_before']==record['source_sha_after']==source_sha
                assert record['accepted'] and record['verified_names']==aliases+1
                assert record['streamed_sha_calls']==(aliases+1 if mode=='baseline' else 1),record
                record['trial']=index;trials.append(record)
            observations.append({'size':size,'aliases':aliases,'host_allocation_bytes':physical,
                'stored_bytes':source.stat().st_size,'source_sha256':source_sha,'trials':trials})
        # Race comparison on identical independent copies of one original authenticated archive.
        large=observations[-1]
        original=evidence/f"source-{large['size']}-{large['aliases']}.cmpct"
        race=[]
        for mode in ['baseline','cache-oracle']:
            destination=work/f'race-{mode}.cmpct'
            shutil.copyfile(original,destination)
            pre=digest(destination)
            result=call(script,destination,mode,True)
            assert result['source_sha_before']==pre==large['source_sha256']
            assert result['source_sha_after']!=pre
            assert result['tamper'] and result['tamper'][0]['offset']>0
            result['copy_sha256_after']=digest(destination)
            race.append(result)
            shutil.copyfile(destination,evidence/f'race-{mode}-tampered.cmpct')
    decision=('NAIVE_CACHE_MUTABLE_CUSTODY_FALSIFIED'
        if not race[0]['accepted'] and race[1]['accepted']
        else 'PREDICTION_NOT_ESTABLISHED')
    report={'schema':'J24I21-sparse-proof-ownership-oracle-v1','source_head':os.environ.get('J24I21_SOURCE_HEAD'),
        'reader_blob':READER_BLOB,'host':platform.platform(),'cases':observations,
        'mutation':race,'decision':decision,'product_credit':False,
        'safety_scope':'controlled same-process interposition; actor permitted to edit archive file',
        'unmeasured':['immutable source snapshot ownership','Windows/macOS','full product benchmark',
                      'adversary without file-write permission','crash recovery']}
    (evidence/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'case_summary':[
        {'size':x['size'],'aliases':x['aliases'],'stored_bytes':x['stored_bytes'],
        'wall_ms':[round(t['wall_ns']/1e6,3) for t in x['trials']],
        'sha_calls':[t['streamed_sha_calls'] for t in x['trials']]}
        for x in observations],'mutated_baseline_error':race[0]['error'],
        'mutated_cache_accepted':race[1]['accepted']},indent=2))
    assert decision=='NAIVE_CACHE_MUTABLE_CUSTODY_FALSIFIED',report['mutation']


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        print(json.dumps(run_child(Path(sys.argv[2]),sys.argv[3],bool(int(sys.argv[4]))),sort_keys=True))
    else:main()
