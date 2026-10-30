#!/usr/bin/env python3
"""J24G95: trusted out-of-band snapshot-hash baseline, research only.

External trusted anchor is a PRECONDITION. A stored hash beside attacker-controlled
archive bytes is NOT authentication. No product source/format modifications.
"""
from __future__ import annotations
import hashlib, json, os, platform, shutil, statistics, struct, subprocess, sys, tempfile, time, tracemalloc
from pathlib import Path
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from j24g92_footer_link_court import one_case, lineage, FOOTER, PREV_OFFSET

PREREG = '5691dc1fcf448ab43b203624fc52e64447c4b7ce'
PARENT = 'f29561c5e2d36a8f47aa35f61191911c0611be6b'
READER_BLOB = 'e716233403dabd0966863c45635e18fa5ac6afb8'
SIZES = (16, 128, 4096)
SAMPLES = 35

def source_receipt():
    def git(*a): return subprocess.check_output(['git', *a], text=True).strip()
    head = git('rev-parse','HEAD')
    for ref in (PREREG, PARENT):
        subprocess.run(['git','merge-base','--is-ancestor',ref,'HEAD'], check=True)
    assert git('rev-parse','HEAD:src/cmpct/reader.py') == READER_BLOB
    return {'head':head, 'prereg':PREREG,'parent':PARENT,'reader_blob':READER_BLOB}

def sha_raw(data): return hashlib.sha256(data).hexdigest()

def sha_stream(path):
    sha = hashlib.sha256()
    count = 0
    with path.open('rb', buffering=0) as f:
        while True:
            buf = f.read(1024 * 1024)
            if not buf: break
            sha.update(buf); count += len(buf)
    return sha.hexdigest(), count

def timed(path, operation):
    # Amortized samples prevent Windows process_time_ns from rounding to zero.
    batch = 64 if sys.platform == 'win32' else 1
    start = time.perf_counter_ns(); cpu = time.process_time_ns()
    for _ in range(batch):
        if operation == 'hash':
            result, n = sha_stream(path)
            assert n == path.stat().st_size and len(result) == 64
        else:
            with CMPCT(path) as r:
                assert len(r.by) > 0
    return {'wall_ns':(time.perf_counter_ns()-start)/batch,
            'cpu_ns':(time.process_time_ns()-cpu)/batch,'batch':batch}

def pair_benchmark(path):
    for o in ('hash','reader'):
        for _ in range(3): timed(path,o)
    raw = []
    for i in range(SAMPLES):
        for o in (('hash','reader') if i%2==0 else ('reader','hash')):
            raw.append({'round':i,'operation':o,**timed(path,o)})
    med = {m:{o:statistics.median(s[m] for s in raw if s['operation']==o)
              for o in ('hash','reader')} for m in ('wall_ns','cpu_ns')}
    peaks = {}
    for o in ('hash','reader'):
        readings=[]
        for _ in range(3):
            tracemalloc.start()
            timed(path,o)
            readings.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        peaks[o]=readings
    return {'raw':raw,'medians':med,'python_traced_peak':peaks,
            'hash_to_reader_wall_ratio':med['wall_ns']['hash']/med['wall_ns']['reader']}

def case(root, out, n):
    # Reuse the installed-Reader mutation court, not new r24 interpretations.
    prior = one_case(root, n, out)
    normal = (out / f'{n}-normal.cmpct')
    trusted = sha_stream(normal)[0]
    nbytes = normal.stat().st_size
    chain = lineage(normal.read_bytes())
    assert len(chain)==4
    # Two-link camouflage: F3 -> F1 while F2 -> zero.
    double = bytearray((out / f'{n}-rewired.cmpct').read_bytes())
    f2 = chain[-2]
    struct.pack_into('<Q',double,f2['pos']+PREV_OFFSET,0)
    double_file = out / f'{n}-double.cmpct'; double_file.write_bytes(double)
    assert double_file.stat().st_size == nbytes
    changed = bytearray(normal.read_bytes()); changed[0] ^= 0x01
    body_file = out / f'{n}-body_changed.cmpct'; body_file.write_bytes(changed)
    # Legitimate public Writer change invalidates the old pin until reauthorized.
    updated = out / f'{n}-authorized_append.cmpct'
    shutil.copyfile(normal,updated)
    append_delete(updated,'f00003.dat')
    with CMPCT(updated) as reader:
        assert reader.verify()==n-4
    names=['normal','rewired','double','bad_digest','out_of_bounds','body_changed','authorized_append']
    paths={v:out / f'{n}-{v}.cmpct' for v in names}
    records={}
    for label,p in paths.items():
        dig,count=sha_stream(p)
        records[label]={'sha256':dig,'bytes':count,'pinned_sha_accept':dig==trusted}
        assert records[label]['pinned_sha_accept']==(label=='normal'),label
    for label in ('normal','rewired','double','bad_digest','out_of_bounds','body_changed'):
        assert records[label]['bytes']==nbytes
    for label in ('normal','rewired','double','authorized_append'):
        with CMPCT(paths[label]) as r:
            count=len(r.by)
            assert r.verify()==count
            records[label]['reader_files']=count
    assert records['normal']['reader_files']==n-3
    assert records['rewired']['reader_files']==n-2
    assert records['double']['reader_files']==n-2
    assert records['authorized_append']['reader_files']==n-4
    benchmark=pair_benchmark(normal)
    return {'n':n,'trusted_snapshot_anchor_sha256':trusted,
            'anchor_is_externally_trusted_in_this_model':True,
            'records':records,'same_input_open_economics':benchmark,
            'physical_snapshot_source_sha256':prior['answers']['normal']['whole_file_sha256'],
            'sidecar_raw_digest_bytes':32,'product_credit':0}

def main():
    out=Path(os.environ.get('J24G95_EVIDENCE','evidence/j24g95'));out.mkdir(parents=True,exist_ok=True)
    receipt={'schema':'j24g95-trusted-external-snapshot-anchor-o0-v1','source':source_receipt(),
             'host':platform.platform(),'python':sys.version,'status':'STARTED',
             'trust_model':'external trusted exact whole-file SHA; no in-band authentication',
             'cases':{},'product_credit':0}
    try:
        with tempfile.TemporaryDirectory(prefix='cmpct-j24g95-') as d:
            root=Path(d)
            for n in SIZES: receipt['cases'][str(n)]=case(root,out,n)
        receipt['status']='PASS'
    except BaseException as e:
        receipt['status']='FAIL';receipt['fatal']={'type':type(e).__name__,'message':str(e)}
        raise
    finally:
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print('J24G95',json.dumps({'status':receipt['status'],'cases':{
            k:{'bytes':v['records']['normal']['bytes'],
               'ratio':v['same_input_open_economics']['hash_to_reader_wall_ratio'],
               'wall':v['same_input_open_economics']['medians']['wall_ns']}
            for k,v in receipt['cases'].items()}},sort_keys=True))
if __name__=='__main__':main()
