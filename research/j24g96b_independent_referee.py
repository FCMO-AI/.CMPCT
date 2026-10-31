#!/usr/bin/env python3
"""Independent v2 hypothetical digest-slot referee; no producer imports."""
import argparse,ctypes,hashlib,io,json,pathlib,struct,tempfile,zipfile
DOMAIN=b'CMPCT-J24G96B-HYPOTHETICAL-FOOTER-DIGEST-SLOT-V2\0'
SOURCES={
'small-ubuntu':('d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d','f29561c5e2d36a8f47aa35f61191911c0611be6b',['16-normal.cmpct','128-normal.cmpct']),
'small-windows':('f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e','f29561c5e2d36a8f47aa35f61191911c0611be6b',['16-normal.cmpct','128-normal.cmpct']),
'deep-ubuntu':('19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b','129edec976efe8bb604584517de39553487fec34',['4096-A.cmpct','8192-A.cmpct']),
'deep-windows':('c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab','129edec976efe8bb604584517de39553487fec34',['4096-A.cmpct','8192-A.cmpct'])}
LIB=ctypes.CDLL('libzstd.so.1')
LIB.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
LIB.ZSTD_decompress.restype=ctypes.c_size_t
LIB.ZSTD_isError.argtypes=[ctypes.c_size_t];LIB.ZSTD_isError.restype=ctypes.c_uint

def check(v,msg):
    if not v:raise AssertionError(msg)
def sha(v):return hashlib.sha256(v).digest()
def inspect(raw):
    p=len(raw)-68;seen=set();rows=[]
    while p:
        check(0<p and p+68<=len(raw) and p not in seen and len(rows)<128,'physical footer path')
        seen.add(p)
        magic,kind,codec,flags,reserved,clen,ulen,prev,stored=struct.unpack_from('<8sBBBBQQQ32s',raw,p)
        check(magic==b'CMPTF24\0' and kind in(0,1) and flags==reserved==0,'footer flags')
        check(0<clen<=p and 0<ulen<=32<<20 and prev<p,'footer bounds')
        compressed=raw[p-clen:p]
        if codec==0:content=compressed
        elif codec==1:
            inp=ctypes.create_string_buffer(compressed);out=ctypes.create_string_buffer(ulen)
            result=LIB.ZSTD_decompress(out,ulen,inp,clen)
            check(not LIB.ZSTD_isError(result) and result==ulen,'independent zstd')
            content=out.raw[:ulen]
        else:raise AssertionError('unexpected codec')
        check(len(content)==ulen and sha(content)==stored,'original r24 SHA')
        rows.append((p,kind,content));p=prev
    check(rows[-1][1]==0 and all(row[1]==1 for row in rows[:-1]),'root and kind')
    accumulator=bytes(32)
    for p,kind,content in rows[::-1]:
        accumulator=sha(DOMAIN+accumulator+struct.pack('<Q',p)+raw[p:p+36]+content)
    return {'root':accumulator.hex(),'footers':len(rows),
            'decoded':sum(len(x[2]) for x in rows),'archive_bytes':len(raw)}

def verify(args,receipt):
    data=json.loads(pathlib.Path(receipt).read_text())
    check(data['schema']=='cmpct-j24g96b-zero-extra-byte-footer-slot-O0-v1','schema')
    check(len(data['results'])==8,'result cardinality')
    for key,(zsha,head,files) in SOURCES.items():
        provider=getattr(args,key.replace('-','_')).read_bytes()
        check(sha(provider).hex()==zsha,'source zip digest')
        with zipfile.ZipFile(io.BytesIO(provider)) as z:
            check(z.read('checkout-head.txt').decode().strip()==head,'original checkout SHA')
            for filename in files:
                original=z.read(filename);calculated=inspect(original)
                target=data['results'][key+'/'+filename]
                for field,want in [('source_archive_bytes',calculated['archive_bytes']),
                    ('hypothetical_archive_bytes',calculated['archive_bytes']),
                    ('additional_archive_bytes',0),('external_trusted_latest_head_bytes',32),
                    ('original_footer_count',calculated['footers']),
                    ('future_verified_root',calculated['root']),
                    ('decoded_footer_bytes_hashed',calculated['decoded'])]:
                    check(target[field]==want,key+'/'+filename+'/'+field)
                for field in ('current_r24_semantics_incompatible','single_rewire_fail_closed',
                    'malicious_rehash_requires_changed_trusted_root',
                    'footer_payload_mutation_rejected','physical_blob_mutation_invisible_to_footer_head'):
                    check(target[field] is True,'negative flag '+field)
    return data

def forged(args,receipt):
    original=json.loads(pathlib.Path(receipt).read_text());key=next(iter(original['results']))
    cases=[('future_verified_root','0'*64),('additional_archive_bytes',1),
           ('decoded_footer_bytes_hashed',0),('physical_blob_mutation_invisible_to_footer_head',False)]
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td)/'bad.json'
        for field,value in cases:
            bad=json.loads(json.dumps(original));bad['results'][key][field]=value;p.write_text(json.dumps(bad))
            try:verify(args,p)
            except AssertionError:pass
            else:raise AssertionError('forged v2 receipt accepted: '+field)
    return len(cases)

def main():
    p=argparse.ArgumentParser()
    for key in SOURCES:p.add_argument('--'+key,required=True,type=pathlib.Path)
    p.add_argument('--result',required=True,type=pathlib.Path)
    args=p.parse_args()
    validated=verify(args,args.result)
    print(json.dumps({'result':'PASS','cases':len(validated['results']),
                      'forged_receipts_refused':forged(args,args.result)},sort_keys=True))
if __name__=='__main__':main()
