#!/usr/bin/env python3
"""O201: actual r24 cdc descriptor-length/read_range discrepancy.
Preregistered independently in docs/v031-research/2026-10-26-o201-cdc-chunk-range-prereg.md.
"""
from __future__ import annotations
import argparse
import binascii
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import traceback
import msgpack
from cmpct.codec import (MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
                         CODEC_RAW, K_FILE, S_CDC, zc, zd, sha)
from cmpct.reader import CMPCT

PAYLOAD = b'ABCD'
REL = 'cdc.bin'

def wire_archive(chunk_length: int) -> tuple[bytes, dict]:
    """Construct complete checksum-consistent head/index/RAW record/tail/index/footer."""
    index = {
        'files': [[REL, K_FILE, 0o644, 946684800000000000, 4, sha(PAYLOAD),
                   [S_CDC, [[chunk_length, 0]]]]],
        'blobs': [[0, 4, 4, CODEC_RAW, 0]],
        'recipes': [], 'dict_blob': None, 'fsmeta': {},
    }
    ib = msgpack.packb(index, use_bin_type=True)
    ic = zc(ib, 12)
    ih = hashlib.sha256(ib).digest()
    record = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, 4, 4, 0,
                       binascii.crc32(PAYLOAD) & 0xffffffff, sha(PAYLOAD)) + PAYLOAD
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(ic), len(ib), 0, ih)
    binary = HDR.pack(MAGIC, VERSION, 0, len(ic), len(ib), len(record), ih) + ic + record + ic + footer
    assert len(binary) == HDR.size + 2 * len(ic) + len(record) + FTR.size
    assert hashlib.sha256(zd(ic, len(ib))).digest() == ih
    assert msgpack.unpackb(zd(ic, len(ib)), raw=False) == index
    assert binary[-FTR.size:] == footer
    assert binary[HDR.size:HDR.size + len(ic)] == binary[-FTR.size-len(ic):-FTR.size]
    return binary, {'index_sha256': ih.hex(), 'archive_sha256': hashlib.sha256(binary).hexdigest(),
                    'archive_bytes': len(binary),
                    'physical_raw_crc32': binascii.crc32(PAYLOAD) & 0xffffffff}

def installed_custody() -> dict:
    root = Path(os.environ['GITHUB_WORKSPACE']).resolve()
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    if head != os.environ['EVIDENCE_HEAD']:
        raise AssertionError(('exact-head mismatch',head,os.environ['EVIDENCE_HEAD']))
    import cmpct.reader as reader_module
    import cmpct.codec as codec_module
    installed_shas = {}
    for name, module in [('reader', reader_module), ('codec', codec_module)]:
        actual = Path(inspect.getfile(module)).resolve()
        repo = (root/'src'/'cmpct'/(name+'.py')).resolve()
        if actual == repo:
            raise AssertionError(('expected independently installed package',name))
        norm = lambda b: b.replace(b'\r\n',b'\n')
        if norm(actual.read_bytes()) != norm(repo.read_bytes()):
            raise AssertionError(('installed package differs from exact checked out source',name))
        installed_shas[name] = hashlib.sha256(norm(actual.read_bytes())).hexdigest()
    return {'git_head':head,'installed_source_sha256':installed_shas}

def invoke(path:Path, dest:Path) -> dict:
    out = {}
    with CMPCT(path) as reader:
        out['loaded_declared_chunk_length'] = reader.by[REL][6][1][0][0]
        for label, fn in (
            ('verify',lambda:reader.verify()),
            ('full_read',lambda:reader.read(REL).hex()),
            ('full_range',lambda:reader.read_range(REL,0,4).hex()),
            ('late_range',lambda:reader.read_range(REL,2,2).hex())):
            try:
                out[label] = {'ok':True,'value':fn()}
            except Exception as e:
                out[label] = {'ok':False,'error':type(e).__name__+': '+str(e)}
        try:
            reader.extractall(dest,metadata=False)
            data = (dest/REL).read_bytes()
            out['extract'] = {'ok':True,'sha256':hashlib.sha256(data).hexdigest(),
                              'hex':data.hex(),'bytes':len(data)}
        except Exception as e:
            out['extract'] = {'ok':False,'error':type(e).__name__+': '+str(e)}
    return out

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    record = {'question':'CDC_DECLARED_CHUNK_LENGTH_VS_RANGE_EXACTNESS',
              'host':{'platform':platform.platform(),'python':platform.python_version(),'os':os.name},
              'source':installed_custody(),'cases':[]}
    with tempfile.TemporaryDirectory(prefix='o201-r24-wire-') as d:
        root=Path(d)
        for ln in (4,1,2,5):
            raw, meta = wire_archive(ln)
            archive=root/f'chunk-{ln}.cmpct'
            archive.write_bytes(raw)
            assert hashlib.sha256(archive.read_bytes()).hexdigest() == meta['archive_sha256']
            trial=invoke(archive,root/f'extracted-{ln}')
            record['cases'].append({'declared_chunk_length':ln,'archive':meta,'reader':trial})
    valid=record['cases'][0]['reader']
    correct_sha=hashlib.sha256(PAYLOAD).hexdigest()
    baseline=(valid['verify']=={'ok':True,'value':1} and
              valid['full_read']=={'ok':True,'value':PAYLOAD.hex()} and
              valid['full_range']=={'ok':True,'value':PAYLOAD.hex()} and
              valid['late_range']=={'ok':True,'value':PAYLOAD[2:].hex()} and
              valid['extract'].get('sha256')==correct_sha)
    bad=record['cases'][1]['reader']
    mismatch=(bad['verify']=={'ok':True,'value':1} and
              bad['full_read']=={'ok':True,'value':PAYLOAD.hex()} and
              bad['extract'].get('ok') is False and 'chunk length failure' in bad['extract'].get('error','') and
              bad['late_range']=={'ok':True,'value':bytes(2).hex()})
    record['positive_control_pass']=bool(baseline)
    record['hostile_mismatch_observed']=bool(mismatch)
    record['decision']=('INCONCLUSIVE_POSITIVE_CONTROL_FAILED' if not baseline else
                        'REPRODUCED_AUTHENTIC_CDC_RANGE_SEMANTIC_GAP' if mismatch else
                        'HOSTILE_CHUNK_REJECTED_OR_NO_MISMATCH')
    record['product_change']=False
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('O201_DECISION='+record['decision'])
    print('O201_RESULT='+json.dumps({k:record[k] for k in
                                    ('decision','positive_control_pass','hostile_mismatch_observed')},
                                    sort_keys=True))
    return 1 if not baseline else 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
