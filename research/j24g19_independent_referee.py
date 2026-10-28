#!/usr/bin/env python3
"""J24G19 independent physical SHA/footer and observed-result audit.

No cmpct imports, no Reader, no semantic MessagePack unpacking. Asserts
physical receipts and cross-arm outcomes only. Not a complete independent
CMPCT reader. Tampering a record must fail.
"""
from __future__ import annotations
import copy, hashlib, json, pathlib, struct, sys

FTR=struct.Struct('<8sBBBBQQQ32s')
FMAGIC=b'CMPTF24\0'
MAGIC=b'CMPCT24\0'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(cond,what):
    if not cond:raise AssertionError(what)

def audit(root,record):
    n=0
    def check(x,why):
        nonlocal n
        require(x,why);n+=1
    check(record['schema']=='cmpct-j24g19-signed-reader-court-v1','schema')
    check(record['product_changes']==0 and record['release_credit']==0,'no release credit')
    check(record['reader_blob']=='f13c5492f5acfa1cfcfec97cdbe0da71e41e327b','reader')
    check(record['published_blob']=='e716233403dabd0966863c45635e18fa5ac6afb8','released')
    check(record['selftest']['valid_cases']>=2600 and record['selftest']['hostile_mutants']>=2000,'fuzz')
    check(record['selftest']['certified_invalid']==0 and record['selftest']['wrong_known_field_values']==0,'fuzz no mismatch')
    files=record['files']; observations=record['observations']
    base=(root/files['checkpoint']['relative']).read_bytes()
    check(base.startswith(MAGIC),'base magic')
    for case,entry in files.items():
        name=entry['relative'];b=(root/name).read_bytes()
        check(sha(b)==entry['sha256'],case+' file digest')
        check(len(b)==entry['bytes'],case+' file length')
        check(b.startswith(MAGIC),case+' archive magic')
        if case not in ('checkpoint','writer'):
            signed=entry['signed'];footer=signed['footer'];p=signed['prev']
            check(b.startswith(base),case+' same builder checkpoint')
            check(footer+FTR.size==len(b),case+' last physical footer')
            magic,kind,codec,flags,res,cs,us,prev,ph=FTR.unpack_from(b,footer)
            check(magic==FMAGIC and kind==1 and codec==0,case+' signed kind')
            check(flags==0 and res==0 and cs==us,case+' signed exact uncompressed')
            check(prev==p,case+' physical parent pointer')
            payload=b[footer-cs:footer]
            check(len(payload)==cs,case+' payload framing')
            check(sha(payload)==signed['payload_sha256'],case+' payload SHA')
            check(sha(payload)==ph.hex(),case+' signed payload hash')
            check(sha(b[footer:])==signed['footer_sha256'],case+' footer hash')
            check((p==0)==(case=='orphan-large'),case+' orphan-only null parent')
        for arm,rows in observations[case].items():
            check(len(rows)>=2,case+arm+' repetitions')
            for r in rows:
                if case=='malformed':
                    check(r['status']=='error' and r['error'],case+arm+' malformed refused')
                else:
                    expected='owner.bin' if case in ('checkpoint','orphan-large') else 'renamed.bin'
                    depth=0 if case in ('checkpoint','orphan-large') else 1
                    check(r['status']=='opened' and r['depth']==depth,case+arm+' selection')
                    check(r['members'].get(expected)==record['body_sha256'],case+arm+' exact member')
                    check((r['footer']==record['checkpoint'])==(depth==0),case+arm+' footer pointer')
                check(r['cpu_ns']>=0 and r['wall_ns']>=0 and r['rss_kib']>0,case+arm+' telemetry')
    check(files['linked-large']['signed']['certified'],'large fast path')
    check(not files['linked-unicode']['signed']['certified'],'unicode fallback')
    return n

def run(root:pathlib.Path):
    record=json.loads((root/'signed_result.json').read_text())
    checks=audit(root,record)
    changes=[('wrong_member',lambda x:x['observations']['linked-large']['projected'][0]['members'].update({'renamed.bin':'bad'})),
             ('wrong_footer',lambda x:x['observations']['orphan-large']['parent'][0].update({'footer':-1})),
             ('false_source',lambda x:x.update({'published_blob':'x'*40})),
             ('fake_payload',lambda x:x['files']['linked-large']['signed'].update({'payload_sha256':'0'*64}))]
    blocked=0
    for label,mutate in changes:
        obj=copy.deepcopy(record);mutate(obj)
        try:audit(root,obj)
        except AssertionError:blocked+=1
        else:raise AssertionError('referee accepted tampered '+label)
    result={'independent_checks':checks,'tampered_records_rejected':blocked,
            'source':'standard-library physical SHA/footer and outcome referee',
            'not_a_second_reader':True}
    (root/'independent_referee.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
    assert blocked==len(changes)

if __name__=='__main__':run(pathlib.Path(sys.argv[1]))
