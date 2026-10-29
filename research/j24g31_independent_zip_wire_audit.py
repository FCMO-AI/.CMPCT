#!/usr/bin/env python3
"""Independent, read-only ZIP wire auditor for J24G30 original Actions artifacts.

No CMPCT import, no product reader, and no stdlib ZIP parser for the inner
exports. The stdlib zipfile module is used solely for unpacking Actions' outer
transport archives. Exits nonzero on any structural/integrity discrepancy.

Usage: python research/j24g31_independent_zip_wire_audit.py --artifacts DIR [--json FILE]
"""
import argparse
import binascii
import datetime
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

LFH=struct.Struct('<IHHHHHIIIHH')
CDH=struct.Struct('<IHHHHHHIIIHHHHHII')
EOCD=struct.Struct('<IHHHHIIH')
SHA=lambda b:hashlib.sha256(b).hexdigest()

class Audit:
    def __init__(self): self.checks=0; self.per_host={}; self.negative=[]
    def yes(self, claim, desc):
        self.checks+=1
        if not claim:raise AssertionError(f'check {self.checks}: {desc}')
    def read_inner(self, raw, expected_payload_sha, ident, permit_invalid_date):
        self.yes(len(raw)>=EOCD.size+LFH.size+CDH.size, f'{ident}: ZIP total bound')
        e=EOCD.unpack_from(raw,len(raw)-EOCD.size)
        self.yes(e[0]==0x06054b50 and e[1:5]==(0,0,1,1) and e[-1]==0,f'{ident}: EOCD signature, single-disk, entry counts and no trailing comment')
        cd_size,cd_offset=e[5:7]
        self.yes(cd_offset+cd_size==len(raw)-EOCD.size,f'{ident}: central directory terminates before EOCD')
        self.yes(cd_size>=CDH.size,f'{ident}: central dir bound')
        c=CDH.unpack_from(raw,cd_offset)
        self.yes(c[0]==0x02014b50 and c[2]>=20,f'{ident}: central signature/version')
        # c: sig,made,need,flags,method,time,date,crc,cs,us,nlen,extra,comment,disk,iattr,eattr,lhofs
        self.yes(c[13]==0 and c[11]==0 and c[12]==0, f'{ident}: no extra, central comment or disk')
        self.yes(c[16]==0,f'{ident}: one entry starts at local offset 0')
        c_name=raw[cd_offset+CDH.size:cd_offset+CDH.size+c[10]]
        self.yes(cd_size==CDH.size+c[10],f'{ident}: complete central dir consumed')
        l=LFH.unpack_from(raw,0)
        self.yes(l[0]==0x04034b50, f'{ident}: local signature')
        self.yes(l[1]>=20 and l[10]==0,f'{ident}: version and no local extra')
        self.yes((l[2],l[3],l[4],l[5],l[6],l[7],l[8])==(c[3],c[4],c[5],c[6],c[7],c[8],c[9]), f'{ident}: local/central agreed flags, method, date, CRC and sizes')
        l_name=raw[LFH.size:LFH.size+l[9]]
        self.yes(l_name==c_name and l[9]==c[10] and len(l_name)>0, f'{ident}: matching name')
        off=LFH.size+l[9]
        self.yes(off+l[7]==cd_offset,f'{ident}: exact compressed span and no hidden intervening bytes')
        compressed=raw[off:cd_offset]
        self.yes(c[4] in (0,8), f'{ident}: supported method')
        if c[4]==8:
            decoder=zlib.decompressobj(-15)
            payload=decoder.decompress(compressed)+decoder.flush()
            self.yes(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail, f'{ident}: exact raw deflate terminates')
        else:payload=compressed
        self.yes(len(payload)==c[9],f'{ident}: uncompressed exact size')
        self.yes(binascii.crc32(payload)&0xffffffff==c[7],f'{ident}: physical ZIP CRC')
        self.yes(SHA(payload)==expected_payload_sha,f'{ident}: logical bytes match independently fingerprinted CMPCT creator payload')
        word_t,word_d=c[5],c[6]
        vals=(1980+(word_d>>9),(word_d>>5)&15,word_d&31,(word_t>>11)&31,(word_t>>5)&63,(word_t&31)*2)
        valid=True
        try:datetime.datetime(*vals)
        except ValueError:valid=False
        if not permit_invalid_date:self.yes(valid,f'{ident}: candidate DOS calendar is real Gregorian date')
        return {'date':list(vals),'valid_date':valid,'bytes':len(raw),'sha256':SHA(raw),'name':c_name.decode('utf-8'),'method':c[4]}

    def execute(self,root):
        src=root/'j30-physical-original.zip'
        hosts={k:root/f'j30-{k}-original.zip' for k in ('linux','mac','win')}
        expected_transport_sha={
            'j30-physical-original.zip':'856777ebf5dcc1c2a7e85a4bb7b0fd5e7a15b3dbcbf6f94ab8eb4ddf68a7082a',
            'j30-linux-original.zip':'9a25d1ed4cf94c01b575d9cb21d0e91bc7632d86ceee4ac779a7e7d5743c840e',
            'j30-mac-original.zip':'989b9cba84c1555d208a9864e63778ce5c47e08d8358025fc355a2b509767f8c',
            'j30-win-original.zip':'c13352d9f9c7e4ac88073888c40b20ce4cbb09770e07f2a3bc8a45771dbc84d0',
        }
        for p in [src,*hosts.values()]:
            self.yes(p.exists(),f'artifact exists: {p.name}')
            self.yes(SHA(p.read_bytes())==expected_transport_sha[p.name],f'original GitHub Actions artifact digest: {p.name}')
        with zipfile.ZipFile(src) as z:
            m=json.loads(z.read('manifest.json'))
            cases=m['cases']
            self.yes(len(cases)==7,'seven independently indexed physical scenarios')
            for name,v in cases.items():
                physical=z.read(v['archive'])
                self.yes(SHA(physical)==v['sha256'] and len(physical)==v['size'],f'{name}: original physical CMPCT archive SHA/size')
                self.yes(len(v['payload_sha256'])==64,f'{name}: payload SHA registered')
        all_outputs={}
        expected_dates={'negative_epoch':[1980,1,1,0,0,0],'zero_epoch':[1980,1,1,0,0,0],'pre_1980_1979':[1980,1,1,0,0,0],
                        'upper_2108_leap':[2107,12,31,23,59,58],'upper_2108_ordinary':[2107,12,31,23,59,58],
                        'ordinary_2020':[2020,1,1,12,0,0],'upper_2107_control':[2107,12,30,12,0,0]}
        for host,outer in hosts.items():
            per={'wire_parsed':0,'source_receipts':0,'negative_rejection':0,'candidate_dates':{},'zip_sha':{}}
            with zipfile.ZipFile(outer) as z:
                names=set(z.namelist())
                for mode,prefix in [('baseline','j30-old-out'),('candidate','j30-new-out')]:
                    records=[]
                    for repetition in (1,2):
                        filename=f'{prefix}/j24g28_{mode}_{repetition}.json'
                        self.yes(filename in names,f'{host}/{mode} original repeat {repetition} exists')
                        record=json.loads(z.read(filename))
                        self.yes(record['mode']==mode and record['repeat']==repetition,f'{host}/{mode} receipt identity and repetition')
                        self.yes(set(record['cases'])==set(cases),f'{host}/{mode} covers all seven cases')
                        expected_git='496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332' if mode=='baseline' else 'cd6a2971396d6fe02a1d7f460d850107b3dcc397'
                        self.yes(record['source']['git_blob']==expected_git, f'{host}/{mode} approved original Git blob')
                        for case,data in record['cases'].items():
                            self.yes(data['physical_sha256']==cases[case]['sha256'] and data['mtime_ns']==cases[case]['mtime_ns'],f'{host}/{mode}/{case}/{repetition}: same original physical input and metadata')
                            self.yes(data['read']=='PASS' and data['verify']=='PASS',f'{host}/{mode}/{case}/{repetition}: genuine read/verify logged')
                        per['source_receipts']+=1
                        records.append(record)
                    if host=='win' and mode=='baseline':
                        for r in records:
                            rec=r['cases']['negative_epoch']
                            self.yes(rec['zip']=='ERROR' and rec['error_type']=='OSError',f'{host}/{mode}: negative-time Windows expected error')
                            per['negative_rejection']+=1
                    for case in cases:
                        filename=f'{prefix}/{case}.zip'
                        if host=='win' and mode=='baseline' and case=='negative_epoch':
                            self.yes(filename not in names,f'{host}/{mode}/{case}: Windows old ZIP absent after exception')
                            continue
                        self.yes(filename in names,f'{host}/{mode}/{case}: original ZIP materialized')
                        raw=z.read(filename)
                        parsed=self.read_inner(raw,cases[case]['payload_sha256'],f'{host}/{mode}/{case}',mode=='baseline')
                        per['wire_parsed']+=1
                        for repetition,rec in enumerate(records,1):
                            item=rec['cases'][case]
                            self.yes(item['zip']=='SUCCESS' and item['zip_sha256']==parsed['sha256'] and item['zip_length']==len(raw),f'{host}/{mode}/{case}/{repetition}: independent wire bytes match receipt')
                            self.yes(item['dos_datetime']==parsed['date'] and item['gregorian_valid']==parsed['valid_date'],f'{host}/{mode}/{case}/{repetition}: independently parsed date matches receipt')
                        if mode=='candidate':
                            self.yes(parsed['date']==expected_dates[case],f'{host}: correct candidate signed/future/ordinary calendar: {case}')
                            per['candidate_dates'][case]=parsed['date']
                        per['zip_sha'][f'{mode}/{case}']=parsed['sha256']
                        all_outputs[(host,mode,case)]=parsed
                for case in ('ordinary_2020','upper_2107_control'):
                    self.yes(all_outputs[(host,'candidate',case)]['sha256']==all_outputs[(host,'baseline',case)]['sha256'],f'{host}: preserved normal ZIP bytes for {case}')
            self.per_host[host]=per
        for case in cases:
            hashes={all_outputs[(host,'candidate',case)]['sha256'] for host in hosts}
            self.yes(len(hashes)==1,f'{case}: candidate ZIP exact byte identity across all three hosts')
        return {'schema':'j24g31-independent-wire-audit-v1','checks':self.checks,'platforms':self.per_host,
                'candidate_zip_cross_host_identity_cases':len(cases),'actual_inner_zips_verified':sum(v['wire_parsed'] for v in self.per_host.values()),
                'scope':'Independent inner ZIP local+central+EOCD/Deflate/CRC/SHA/date/parser; archive provenance from immutable original physical input manifest. Does not independently parse CMPCT revision-24.',
                'source_head':'8581f1dee427e9ca7359e3c05bd514499471c357','workflow_run':40812726789,
                'artifact_ids':{'physical':12871265991,'linux':12871102381,'mac':12871166981,'win':12870519614}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--json',type=Path)
    a=p.parse_args();result=Audit().execute(a.artifacts)
    data=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if a.json:a.json.write_text(data)
    print(data)
if __name__=='__main__':main()
