#!/usr/bin/env python3
"""Independent J24G101 receipt proof. Does not import producer or CMPCT."""
from __future__ import annotations
import argparse,copy,hashlib,io,json,struct,zipfile
from pathlib import Path

PINS={
 'deep-ubuntu':('19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b','129edec976efe8bb604584517de39553487fec34'),
 'deep-windows':('c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab','129edec976efe8bb604584517de39553487fec34')
}
FORMAT='<8sBBBBQQQ32s';LEN=struct.calcsize(FORMAT)
def sha(b):return hashlib.sha256(b).hexdigest()
def require(cond,reason):
    if not cond:raise ValueError(reason)
def original_zips(paths):
    out={}
    for key,p in paths.items():
        b=p.read_bytes();expected,head=PINS[key]
        require(sha(b)==expected,'source provider checksum')
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            require(z.read('checkout-head.txt').decode().strip()==head,'original checkout identity')
            for name in ('4096-A.cmpct','8192-A.cmpct'):out[key+'/'+name]=z.read(name)
    return out
def footer_bounds(raw):
    pos=len(raw)-LEN;chain=[];seen=set()
    while True:
        require(pos>=0 and pos+LEN<=len(raw) and pos not in seen,'footer bounds/cycle')
        seen.add(pos)
        magic,kind,codec,flags,unused,clen,ulen,prev,digest=struct.unpack_from(FORMAT,raw,pos)
        require(magic==b'CMPTF24\x00' and 0<clen<=pos,'footer framing')
        if kind==1:
            require(codec==0 and clen==ulen,'delta physical encoding')
            require(hashlib.sha256(raw[pos-clen:pos]).digest()==digest,'delta SHA')
        else:require(kind==0,'unexpected footer kind')
        chain.append((pos,kind))
        if prev==0:break
        require(0<prev<pos and prev not in seen,'ancestor pointer')
        pos=prev
    require(len(chain)==64 and chain[-1][1]==0 and all(kind==1 for _,kind in chain[:-1]),
            'authentic 63 deletes plus checkpoint')
    return chain[-1][0]+LEN,chain[1][0]+LEN
def check(r,orig):
    require(r['schema']=='J24G101-REBASE-BASE-OWNERSHIP-O0-v1','schema')
    require(r['host']=='Linux' and r['verdict']=='LOCAL_ROOT_REBASE_PATHNAME_FAIL_OWNED_AND_VERSIONED_PASS','verdict')
    require(set(r['cases'])==set(r['hostile'])==set(orig),'original case inventory')
    for key,raw in orig.items():
        oldbase,older=footer_bounds(raw)
        modes=r['cases'][key]
        require(set(modes)=={'pathname','owned','versioned'},'mode inventory')
        for mode,x in modes.items():
            require(x['mode']==mode and x['source_sha256']==sha(raw),'source identity')
            require(x['archive_bytes']==len(raw) and x['old_archive_bytes']==older,'historic identity')
            require(x['old_base_bytes']==oldbase and x['new_tail_bytes']==len(raw)-older==97,'tail composition')
            require(x['latest_sha256']==sha(raw),'latest replay not exact')
            require(x['tail_lease_confirmed'] is True and x['old_tail_reclaimed'] is True,'tail lifetime')
            require(x['old_base_original_allocated']>=oldbase,'root allocation')
            require(x['old_tail_retained_allocated']>0 and x['current_allocated']>0,'data blocks')
            require(0<=x['publish_wall_ms']<120000,'publication timing')
            result=x['reader']
            require(result['tail_sha_matches'] is True,'tail hash')
            require(result['expected_sha256']==sha(raw[:older]),'prior source SHA')
            if mode=='pathname':
                require(x['correct_old_snapshot'] is False and result['correct'] is False,'missing expected negative')
                require(result['base_sha_matches'] is False,'root replacement did not occur')
                require(result['consumed_sha256']!=sha(raw[:older]),'wrong old source received')
                require(x['old_base_retained_allocated']==0,'unowned base counted as retained')
            else:
                require(x['correct_old_snapshot'] is True and result['correct'] is True,'owned old Reader lost snapshot')
                require(result['base_sha_matches'] is True,'owned root hash')
                require(result['consumed_sha256']==sha(raw[:older]) and result['consumed_bytes']==older,
                        'previous signed physical archive mismatch')
                require(x['old_base_retained_allocated']==x['old_base_original_allocated'],'hidden old root blocks')
                require(x['retained_peak_ratio']>=1.7,'overlapping root carrying cost')
        h=r['hostile'][key]
        require(all(h[k] is True for k in ('same_inode_and_size','digest_detects_mutation',
                'shared_advisory_lock_does_not_block_noncooperative_writer')),'adversarial same-inode omission')
    return True
def main():
    a=argparse.ArgumentParser()
    a.add_argument('--deep-ubuntu',type=Path,required=True)
    a.add_argument('--deep-windows',type=Path,required=True)
    a.add_argument('--result',type=Path,required=True)
    z=a.parse_args();orig=original_zips({'deep-ubuntu':z.deep_ubuntu,'deep-windows':z.deep_windows})
    r=json.loads(z.result.read_bytes());check(r,orig)
    forgeries=[
      ('fake_unowned_pass',lambda x:x['cases']['deep-ubuntu/4096-A.cmpct']['pathname'].__setitem__('correct_old_snapshot',True)),
      ('fake_owned_pass',lambda x:x['cases']['deep-ubuntu/8192-A.cmpct']['owned']['reader'].__setitem__('consumed_sha256','0'*64)),
      ('hide_root_blocks',lambda x:x['cases']['deep-windows/4096-A.cmpct']['owned'].__setitem__('old_base_retained_allocated',0)),
      ('changed_original',lambda x:x['cases']['deep-windows/8192-A.cmpct']['versioned'].__setitem__('source_sha256','1'*64)),
      ('fake_tail_lock',lambda x:x['cases']['deep-windows/8192-A.cmpct']['owned'].__setitem__('tail_lease_confirmed',False)),
      ('fake_adversary',lambda x:x['hostile']['deep-ubuntu/4096-A.cmpct'].__setitem__('digest_detects_mutation',False)),
      ('missing_case',lambda x:x['cases'].pop('deep-windows/8192-A.cmpct'))
    ]
    rejected=[]
    for label,change in forgeries:
        altered=copy.deepcopy(r);change(altered)
        try:check(altered,orig)
        except (ValueError,KeyError,TypeError,AssertionError):rejected.append(label)
    require(len(rejected)==len(forgeries),'forged receipt accepted')
    print(json.dumps({'verdict':'DETACHED_J24G101_REFEREE_PASS','physical_sources':len(orig),
                      'scenarios':len(orig)*3,'same_inode_hostiles':len(orig),
                      'forgeries_rejected':rejected,'receipt_sha256':sha(z.result.read_bytes())},sort_keys=True))
if __name__=='__main__':main()
