#!/usr/bin/env python3
"""Independent, strict audit of a J24P03 kernel-court JSON receipt.

No source/oracle imports and no reliance on the oracle's prose decision label.
Not an independent syscall replay: checks what its authentic kernel run recorded.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(content):
    return hashlib.sha256(content).hexdigest()


def inode(val):
    assert isinstance(val,list) and len(val)==2
    assert all(type(x) is int and x>0 for x in val)
    return tuple(val)


def audit(doc):
    assert doc['schema']=='j24p03-linux-existing-replace-v1'
    source=doc['source']
    assert source['euid']>0 and source['platform'].startswith('Linux-')
    assert source['git_head'] is None or re.fullmatch(r'[0-9a-f]{40}',source['git_head'])
    expected={
      'good': digest(b'J24P03-authenticated-good-'*113),
      'bad': digest(b'J24P03-unverified-foreign-'*107),
      'old': digest(b'J24P03-existing-old-target-'*101),
    }
    assert len(set(expected.values()))==3 and doc['payload_sha256']==expected
    trials=doc['trials'];assert len(trials)==7
    seen=set()
    for x in trials[:4]:
        method=x['method'];hostile=x['hostile']
        assert type(hostile) is bool and method in ('os.replace','renameat2_exchange')
        assert (method,hostile) not in seen;seen.add((method,hostile))
        src=inode(x['source_inode']);pub=inode(x['published_inode'])
        assert x['original_fd_sha256']==expected['good']
        assert x['original_target_sha256']==expected['old']
        assert x['stage_link_mode'] in ('AT_EMPTY_PATH','PROC_SELF_FD_FOLLOW')
        if hostile:
            assert x['published_sha256']==expected['bad'] and pub!=src
            assert pub==inode(x['attacker_inode'])
            actor=x['actor'];assert actor['actor_pid']>0
            assert actor['uid']==source['euid']
            assert src==inode(actor['quarantine_inode'])
            assert pub==inode(actor['foreign_inode'])
        else:
            assert x['actor'] is None and x['attacker_inode'] is None
            assert x['published_sha256']==expected['good'] and pub==src
    assert len(seen)==4
    positive,occupied=trials[4:6]
    assert positive['occupied'] is False
    assert positive['target_sha256']==expected['good']
    inode(positive['target_inode'])
    assert positive['decision']=='AUTHENTIC_NO_CLOBBER'
    assert occupied['occupied'] is True
    assert occupied['target_sha256']==expected['old']
    inode(occupied['target_inode'])
    assert occupied['decision']=='EEXIST_PRESERVED'
    direct=trials[6]
    assert direct['decision'] in ('DIRECT_PROC_RENAME_REJECTED','DIRECT_PROC_RENAME_SUCCEEDED')
    if direct['decision']=='DIRECT_PROC_RENAME_REJECTED':
        assert type(direct['errno']) is int and direct['errno']>0
    else:
        assert type(direct['published_is_authenticated_inode']) is bool
    assert all(not x['published_is_authenticated_inode'] for x in trials[:4] if x['hostile'])
    assert all(x['published_is_authenticated_inode'] for x in trials[:4] if not x['hostile'])
    assert doc['decision']=='RETIRE_VISIBLE_STAGE_PLUS_RENAME_EXISTING_TARGET_UNDER_HOSTILE_SAME_UID_WRITER'
    return {'decision':'INDEPENDENT_RECEIPT_CONSISTENCY_PASS','cases':7,
            'hostile_foreign_published':2,'uncontended_authenticated':2,
            'direct_procfd_result':direct['decision'],
            'boundary':'Linux same-UID actor, visible stage plus pathname replacement only'}


def main():
    p=argparse.ArgumentParser();p.add_argument('receipt',type=Path);args=p.parse_args()
    raw=args.receipt.read_text(encoding='utf-8')
    def reject(pairs):
        obj={}
        for k,v in pairs:
            if k in obj: raise ValueError('duplicate JSON key '+k)
            obj[k]=v
        return obj
    doc=json.loads(raw,object_pairs_hook=reject,parse_constant=lambda s: (_ for _ in ()).throw(ValueError('nonfinite '+s)))
    print('J24P03_AUDIT='+json.dumps(audit(doc),sort_keys=True))


if __name__=='__main__':main()
