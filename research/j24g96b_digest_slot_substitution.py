#!/usr/bin/env python3
"""J24G96b prospective O0: re-purpose existing 32-byte footer digest field.

This is a hypothetical FUTURE FORMAT, not an r24-compatible archive or Reader.
"""
import argparse,ctypes,hashlib,io,json,pathlib,struct,zipfile
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,sha,require,ZERO,LIB
DOMAIN=b'CMPCT-J24G96B-HYPOTHETICAL-FOOTER-DIGEST-SLOT-V2\0'
FTR=struct.Struct('<8sBBBBQQQ32s')

def expand(src,pos,codec,clen,ulen):
    compressed=src[pos-clen:pos]
    if codec==0:return compressed
    require(codec==1 and ulen<=32<<20,'future codec')
    dst=ctypes.create_string_buffer(ulen)
    inbound=ctypes.create_string_buffer(compressed)
    result=LIB.ZSTD_decompress(dst,ulen,inbound,clen)
    require(not LIB.ZSTD_isError(result) and result==ulen,'future payload decode')
    return dst.raw[:ulen]

def future_walk(raw):
    pos=len(raw)-FTR.size
    seen=set();descending=[]
    while pos:
        require(pos not in seen and pos>=1 and pos+FTR.size<=len(raw),'future cycle/bounds')
        seen.add(pos)
        magic,kind,codec,flags,reserved,clen,ulen,prev,stored=FTR.unpack_from(raw,pos)
        require(magic==b'CMPTF24\0' and kind in(0,1) and flags==reserved==0,'future fields')
        require(0<clen<=pos and 0<ulen<=32<<20 and 0<=prev<pos,'future sizes')
        descending.append((pos,kind,codec,clen,ulen,prev,stored))
        require(len(descending)<=128,'future depth')
        pos=prev
    require(descending[-1][1]==0 and all(row[1]==1 for row in descending[:-1]),'future root/kind')
    return descending[::-1]

def root_of_future(raw,validate=True):
    digest=ZERO
    for pos,kind,codec,clen,ulen,prev,stored in future_walk(raw):
        payload=expand(raw,pos,codec,clen,ulen)
        require(len(payload)==ulen,'future payload length')
        digest=sha(DOMAIN+digest+struct.pack('<Q',pos)+raw[pos:pos+36]+payload)
        if validate:require(digest==stored,'future slot digest failed')
    return digest

def build_future(raw):
    original=parse_chain(raw) # first authenticate original real r24 histories
    variant=bytearray(raw);old=ZERO
    for n in original:
        payload=expand(raw,n['pos'],n['codec'],n['clen'],n['ulen'])
        old=sha(DOMAIN+old+struct.pack('<Q',n['pos'])+raw[n['pos']:n['pos']+36]+payload)
        variant[n['pos']+36:n['pos']+68]=old
    return bytes(variant),old,original

def case(raw,label):
    future,pinned,nodes=build_future(raw)
    require(len(raw)==len(future),'changed archive size')
    require(root_of_future(future)==pinned,'future original verification failed')
    slots={i for n in nodes for i in range(n['pos']+36,n['pos']+68)}
    require(all(i in slots for i,(a,b) in enumerate(zip(raw,future)) if a!=b),'unexpected non-slot physical edit')
    # The released r24 SHA semantics are deliberately incompatible with this model.
    try:parse_chain(future)
    except ValueError:pass
    else:raise AssertionError('r24 interpreted hypothetical v2 footer digest')
    last,grandparent=nodes[-1],nodes[-3]
    variant=bytearray(future)
    struct.pack_into('<Q',variant,last['pos']+28,grandparent['pos'])
    try:root_of_future(bytes(variant),validate=True)
    except ValueError:pass
    else:raise AssertionError('unbound predecessor edit passed v2')
    # Attackers can recalculate unkeyed local hash, but not the independently trusted pin.
    fake_current=root_of_future(bytes(variant),validate=False)
    variant[last['pos']+36:last['pos']+68]=fake_current
    require(root_of_future(bytes(variant))==fake_current and fake_current!=pinned,
            'recomputed local root passed original external pin')
    # Two-link orphan camouflage, independently preregistered as a negative.
    double=bytearray(future)
    struct.pack_into('<Q',double,last['pos']+28,grandparent['pos'])
    struct.pack_into('<Q',double,nodes[-2]['pos']+28,0)
    try:root_of_future(bytes(double),validate=True)
    except ValueError:pass
    else:raise AssertionError('two-field parent camouflage accepted')
    local_double_root=root_of_future(bytes(double),validate=False)
    double[last['pos']+36:last['pos']+68]=local_double_root
    require(root_of_future(bytes(double))==local_double_root and local_double_root!=pinned,
            'double-rewire local rehash evades pinned head')
    broken=bytearray(future);broken[last['pos']-1]^=1
    try:root_of_future(bytes(broken),validate=True)
    except ValueError:pass
    else:raise AssertionError('footer payload mutation survived hypothetical cumulative digest')
    # Footer metadata is NOT a full archive integrity guarantee.
    marker=raw.index(b'CMA4')
    bm,bc,bf,br,us,cs,ml,crc,bs=struct.unpack_from('<4sBBHQQII32s',raw,marker)
    off=marker+64+ml
    require(bm==b'CMA4' and cs>0 and off+cs<=len(raw),'CMA4 geometry')
    physical=bytearray(future);physical[off]^=1
    require(root_of_future(bytes(physical))==pinned and sha(bytes(physical))!=sha(future),
            'physical-blob integrity negative')
    return {'case':label,'source_archive_bytes':len(raw),
            'hypothetical_archive_bytes':len(future),'additional_archive_bytes':0,
            'external_trusted_latest_head_bytes':32,'original_footer_count':len(nodes),
            'future_verified_root':pinned.hex(),
            'current_r24_semantics_incompatible':True,'single_rewire_fail_closed':True,'double_rewire_fail_closed':True,
            'malicious_rehash_requires_changed_trusted_root':True,
            'footer_payload_mutation_rejected':True,
            'physical_blob_mutation_invisible_to_footer_head':True,
            'decoded_footer_bytes_hashed':sum(n['ulen'] for n in nodes),
            'limitation':'FUTURE FORMAT O0 ONLY; no Reader product, issuer, atomic external root or full archive SHA'}

def main():
    p=argparse.ArgumentParser()
    for key in ZIP_CASES:p.add_argument('--'+key,required=True,type=pathlib.Path)
    p.add_argument('--output',required=True,type=pathlib.Path)
    args=p.parse_args();result={}
    for key,(expected,head,files) in ZIP_CASES.items():
        zipped=getattr(args,key.replace('-','_')).read_bytes()
        require(sha(zipped).hex()==expected,'provider ZIP mismatch '+key)
        with zipfile.ZipFile(io.BytesIO(zipped)) as z:
            require(z.read('checkout-head.txt').decode().strip()==head,'original checkout mismatch')
            for member in files:
                result[key+'/'+member]=case(z.read(member),key+'/'+member)
    require(len(result)==8,'expected eight cases')
    report={'schema':'cmpct-j24g96b-zero-extra-byte-footer-slot-O0-v1',
            'evidence_class':'hypothetical future-format O0; product and release credit zero',
            'results':result,
            'outcome':'ZERO_ARCHIVE_BYTES_O0_SURVIVES_ON_EIGHT_AUTHENTIC_HISTORIES',
            'caveat':'Streaming whole-file SHA has stronger coverage and may dominate this narrow benefit.'}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'cases':len(result),'new_archive_bytes_each':0,
                      'decoded_footer_bytes_hashed':sum(x['decoded_footer_bytes_hashed'] for x in result.values()),
                      'result_SHA256':sha(args.output.read_bytes()).hex()},sort_keys=True))
if __name__=='__main__':main()
