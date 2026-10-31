#!/usr/bin/env python3
"""POSTHOC J24G96 control, not preregistered and not product evidence.

A retained streaming hashlib state may cover *all archive bytes* incrementally
without adding 32 bytes per footer. This is only a mathematical replay of
immutable original prefix bytes; a hashlib state is not crash-durable here.
"""
import argparse
import hashlib
import io
import json
import pathlib
import struct
import zipfile

SOURCES={
    'small-ubuntu':['16-normal.cmpct','128-normal.cmpct'],
    'small-windows':['16-normal.cmpct','128-normal.cmpct'],
    'deep-ubuntu':['4096-A.cmpct','8192-A.cmpct'],
    'deep-windows':['4096-A.cmpct','8192-A.cmpct'],
}
SHA={
    'small-ubuntu':'d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d',
    'small-windows':'f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e',
    'deep-ubuntu':'19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b',
    'deep-windows':'c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab',
}
HEAD={
    'small-ubuntu':'f29561c5e2d36a8f47aa35f61191911c0611be6b',
    'small-windows':'f29561c5e2d36a8f47aa35f61191911c0611be6b',
    'deep-ubuntu':'129edec976efe8bb604584517de39553487fec34',
    'deep-windows':'129edec976efe8bb604584517de39553487fec34',
}
def digest(b):
    return hashlib.sha256(b).hexdigest()
def footer_ends(raw):
    pos=len(raw)-68
    seen=set()
    out=[]
    while pos:
        if pos in seen or pos<1 or pos+68>len(raw) or len(out)>128:
            raise AssertionError('footer cycle/bounds')
        seen.add(pos)
        magic,kind,codec,flags,reserved,clen,ulen,prev,ph=struct.unpack_from('<8sBBBBQQQ32s',raw,pos)
        if magic!=b'CMPTF24\0' or prev>=pos or kind not in (0,1) or flags or reserved:
            raise AssertionError('footer grammar')
        out.append(pos+68)
        pos=prev
    return out[::-1]
def compute(raw):
    ends=footer_ends(raw)
    state=hashlib.sha256()
    prev=0
    stateless_bytes=0
    largest_append=0
    for end in ends:
        delta=raw[prev:end]
        largest_append=max(largest_append,len(delta))
        state.update(delta)
        if state.copy().hexdigest()!=digest(raw[:end]):
            raise AssertionError('incremental whole-file SHA mismatch')
        stateless_bytes+=end
        prev=end
    if prev!=len(raw) or state.hexdigest()!=digest(raw):
        raise AssertionError('final whole-file SHA mismatch')
    # This stronger checksum covers the complete final archive, not just its
    # footer chain. Its update assumptions remain unrealized in production.
    return {'footers':len(ends),'archive_bytes':len(raw),
            'full_file_rehash_each_generation_input_bytes':stateless_bytes,
            'retained_state_total_stream_input_bytes':len(raw),
            'stateless_over_retained_work_ratio':stateless_bytes/len(raw),
            'largest_append_bytes':largest_append,'final_file_SHA256':digest(raw),
            'retained_midstate_durable':False,
            'externally_authenticated_head_protocol':False}
def main():
    p=argparse.ArgumentParser()
    for k in SOURCES:p.add_argument('--'+k,required=True,type=pathlib.Path)
    p.add_argument('--output',required=True,type=pathlib.Path)
    a=p.parse_args()
    cases={}
    for k,names in SOURCES.items():
        blob=getattr(a,k.replace('-','_')).read_bytes()
        if digest(blob)!=SHA[k]:
            raise AssertionError('original provider SHA mismatch: '+k)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            if z.read('checkout-head.txt').decode().strip()!=HEAD[k]:
                raise AssertionError('original checkout mismatch: '+k)
            for name in names:
                cases[k+'/'+name]=compute(z.read(name))
    doc={'schema':'cmpct-j24g96-posthoc-incremental-whole-file-sha-v1',
         'evidence_class':'POSTHOC O0 mathematical prefix replay; not independent prospective product evidence',
         'limitations':['No serializable crash-safe SHA256 state; no trusted external issuance/revocation',
                        'No concurrent writer/source-byte immutability guarantee',
                        'No complete product CPU/wall/RSS or I/O measurement'],
         'cases':cases}
    a.output.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'cases':len(cases),'stream_v_stateless_read_proxy':{
        k:round(v['stateless_over_retained_work_ratio'],2) for k,v in cases.items()}},sort_keys=True))
if __name__=='__main__':main()
