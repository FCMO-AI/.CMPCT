#!/usr/bin/env python3
"""J24G96 independent stdlib-only source/receipt referee.

Never imports the producer, CMPCT, msgpack or libzstd; independently tests
footer geometry and chain commitment. Producer checks decoded payload SHA.
"""
import argparse
import hashlib
import io
import json
import pathlib
import struct
import zipfile

DOMAIN=b'CMPCT-J24G96-HYPOTHETICAL-PINNED-ANCESTRY-V1\0'
SOURCE={
'small-ubuntu':('d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d','f29561c5e2d36a8f47aa35f61191911c0611be6b'),
'small-windows':('f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e','f29561c5e2d36a8f47aa35f61191911c0611be6b'),
'deep-ubuntu':('19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b','129edec976efe8bb604584517de39553487fec34'),
'deep-windows':('c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab','129edec976efe8bb604584517de39553487fec34'),
}

def digest(b):return hashlib.sha256(b).hexdigest()
def need(b,label):
    if not b:raise AssertionError(label)

def raw_chain(data):
    out=[]; pos=len(data)-68; seen=set()
    while pos:
        need(0<pos and pos+68<=len(data) and pos not in seen and len(out)<128,'chain bounds')
        seen.add(pos)
        magic,kind,codec,flags,reserved,cs,us,prev,stored_sha=struct.unpack_from('<8sBBBBQQQ32s',data,pos)
        need(magic==b'CMPTF24\0' and flags==0 and reserved==0 and kind in(0,1),'header')
        need(0<cs<=pos and 0<us<=32<<20 and 0<=prev<pos,'payload bounds')
        out.append((pos,kind,codec,cs,us,prev,stored_sha))
        pos=prev
    need(out[-1][1]==0 and all(n[1]==1 for n in out[:-1]),'kinds')
    return out[::-1]

def cumulative(data, chain):
    current=bytes(32)
    for pos,_,_,_,_,_,sha in chain:
        body=DOMAIN+current+pos.to_bytes(8,'little')+data[pos:pos+36]+sha
        current=bytes.fromhex(digest(body))
    return current.hex()

def analyse(data):
    chain=raw_chain(data)
    last=chain[-1]; old=chain[-3]
    new=bytearray(data);new[last[0]+28:last[0]+36]=old[0].to_bytes(8,'little')
    rewired=bytes(new)
    altered=raw_chain(rewired)
    need(len(altered)==len(chain)-1,'skipped exactly one')
    need(rewired[last[0]+36:last[0]+68]==data[last[0]+36:last[0]+68],'payload digest preserved')
    return {'count':len(chain), 'source_root':cumulative(data,chain), 'altered_root':cumulative(rewired,altered),
            'sha':digest(data),'fullhash_work':sum(x[0]+68 for x in chain),
            'metadata_work':len(chain)*(len(DOMAIN)+32+8+36+32),
            'compressed_footer_bytes':sum(x[3] for x in chain)}

def verify(inputs,result):
    data=json.loads(pathlib.Path(result).read_text())
    need(data['schema']=='cmpct-j24g96-externally-pinned-ancestry-O0-v1','schema')
    need(len(data['cases'])==8,'case count')
    for key,source_path in inputs.items():
        blob=source_path.read_bytes(); required_sha,head=SOURCE[key]
        need(digest(blob)==required_sha,'original provider SHA')
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            need(archive.read('checkout-head.txt').decode().strip()==head,'checkout source')
            prefix='small' if key.startswith('small') else 'deep'
            names=['16-normal.cmpct','128-normal.cmpct'] if prefix=='small' else ['4096-A.cmpct','8192-A.cmpct']
            for filename in names:
                obj=data['cases'][key+'/'+filename]
                raw=archive.read(filename)
                check=analyse(raw)
                for lhs,rhs in [('physical_archive_bytes',len(raw)),('archive_SHA256',check['sha']),('trusted_head_SHA256',check['source_root']),
                    ('parent_rewire_new_head',check['altered_root']),('footers',check['count']),
                    ('candidate_archive_extra_bytes_lower_bound',32*check['count']),
                    ('full_SHA_historical_cumulative_input_byte_proxy',check['fullhash_work']),
                    ('chain_metadata_cumulative_hash_input_byte_proxy',check['metadata_work']),
                    ('hashed_payload_compressed_bytes_for_offline_r24_authentication',check['compressed_footer_bytes'])]:
                    need(obj[lhs]==rhs, f'{key}/{filename} mismatch {lhs}')
                need(check['source_root']!=check['altered_root'],'head collision')
                need(abs(obj['candidate_archive_extra_percent_lower_bound']-100*32*check['count']/len(raw))<1e-10,'percent')
                need(obj['local_rehash_with_replaced_untrusted_head_admitted'] is True,'untrusted-root negative')
    return {'result':'PASS','validated_cases':len(data['cases']),'original_provider_ZIPs':len(inputs)}

def hostile_tests(inputs,report):
    doc=json.loads(pathlib.Path(report).read_text());cases=doc['cases']
    a=next(iter(cases)); orig=cases[a]
    wrong=[('trusted_head_SHA256','0'*64),('physical_archive_bytes',orig['physical_archive_bytes']+1),
           ('parent_rewire_new_head',orig['trusted_head_SHA256']),('candidate_archive_extra_bytes_lower_bound',0),
           ('footers',99),('full_SHA_historical_cumulative_input_byte_proxy',0)]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td)/'mutant.json'
        for field,val in wrong:
            mutate=json.loads(json.dumps(doc));mutate['cases'][a][field]=val;p.write_text(json.dumps(mutate))
            try:verify(inputs,p)
            except AssertionError:pass
            else:raise AssertionError('forged receipt accepted: '+field)
    return len(wrong)

def main():
    parser=argparse.ArgumentParser()
    for name in SOURCE:parser.add_argument('--'+name,required=True,type=pathlib.Path)
    parser.add_argument('--result',required=True,type=pathlib.Path)
    args=parser.parse_args()
    paths={n:getattr(args,n.replace('-','_')) for n in SOURCE}
    checked=verify(paths,args.result)
    checked['hostile_receipts_rejected']=hostile_tests(paths,args.result)
    print(json.dumps(checked,sort_keys=True))

if __name__=='__main__':main()
