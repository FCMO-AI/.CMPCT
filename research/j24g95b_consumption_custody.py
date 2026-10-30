#!/usr/bin/env python3
"""J24G95b: physical controlled hash-to-Reader TOCTOU test; NOT a product patch.

No external inputs. This tests a named archive deliberately changed AFTER a
prior externally-trusted digest matches, but BEFORE a public Reader opens it.
"""
from __future__ import annotations
import hashlib,json,os,platform,shutil,subprocess,sys,tempfile
from pathlib import Path
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g95_anchor_court import sha_stream, source_receipt
from j24g92_footer_link_court import FOOTER,PREV_OFFSET,footer

PREREG='8b733845aef879ce7cb5eda8ff168e7116cd6286'
SIZES=(16,128,4096)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def case(original:Path, rewired:Path, root:Path,n:int):
    intact=original.read_bytes()
    redirected=rewired.read_bytes()
    assert len(intact)==len(redirected)
    pos=len(intact)-FOOTER.size+PREV_OFFSET
    assert intact[:pos]==redirected[:pos]
    assert intact[pos+8:]==redirected[pos+8:]
    assert footer(intact,len(intact)-FOOTER.size)['payload_sha']==footer(
        redirected,len(redirected)-FOOTER.size)['payload_sha']
    pin=sha(intact)
    target=root/f'{n}-verified-then-edited.cmpct'
    shutil.copyfile(original,target)
    prior_sha,nbytes=sha_stream(target)
    assert prior_sha==pin and nbytes==len(intact)
    before=target.stat()
    # Our deterministic injection is the interval between a *prior* correct
    # trust check and later independent pathname interpretation. It is not a
    # live scheduling race or bypass of a check on bytes actually consumed.
    with target.open('r+b') as f:
        f.seek(pos)
        assert f.write(redirected[pos:pos+8])==8
        f.flush()
        os.fsync(f.fileno())
    after=target.stat()
    raw=target.read_bytes()
    assert raw==redirected
    same=(before.st_dev==after.st_dev and before.st_ino==after.st_ino
          and before.st_size==after.st_size)
    assert same, 'test setup changed inode or file length unexpectedly'
    after_digest,after_bytes=sha_stream(target)
    assert after_digest!=pin and after_bytes==nbytes
    with CMPCT(target) as r:
        expected_count=n-2
        assert len(r.by)==expected_count
        assert r.verify()==expected_count
        assert 'f00001.dat' in r.by
        semantic={'count':expected_count,'resurrected':'f00001.dat',
                  'selected_footer':r.latest_footer_pos,'delta_depth':r.delta_depth,
                  'resurrected_sha256':sha(r.read('f00001.dat'))}
    preflight=preflight_archive(target)
    assert preflight['files']==expected_count
    shutil.copyfile(target, Path(os.environ.get('J24G95_EVIDENCE','evidence/j24g95'))/
                    f'{n}-consumption-edited.cmpct')
    changed=[i for i,(a,b) in enumerate(zip(intact,raw)) if a!=b]
    assert changed and all(pos<=i<pos+8 for i in changed)
    return {'case':n,'pin_established_prior_to_edit':True,
            'pin_externally_trusted_is_assumption':True,
            'intact_sha256':pin,'changed_sha256':after_digest,
            'full_hash_recheck_refuses':after_digest!=pin,
            'modified_byte_positions':changed,
            'inode_length_unchanged':same,
            'stat_before':{'dev':before.st_dev,'ino':before.st_ino,'size':before.st_size,
                           'mtime_ns':before.st_mtime_ns},
            'stat_after':{'dev':after.st_dev,'ino':after.st_ino,'size':after.st_size,
                          'mtime_ns':after.st_mtime_ns},
            'public_reader_post_edit':semantic,
            'public_preflight_post_edit_files':preflight['files'],
            'latest_payload_sha256_unchanged':True,
            'product_credit':0}

def main():
    root=Path(os.environ.get('J24G95_EVIDENCE','evidence/j24g95'))
    root.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','merge-base','--is-ancestor',PREREG,'HEAD'],check=True)
    receipt={'schema':'j24g95b-verification-consumption-custody-v1',
             'source':source_receipt(),'prereg':PREREG,'host':platform.platform(),
             'status':'STARTED','product_credit':0,'cases':{}}
    try:
        with tempfile.TemporaryDirectory(prefix='j24g95b-') as d:
            for n in SIZES:
                receipt['cases'][str(n)]=case(root/f'{n}-normal.cmpct',
                                             root/f'{n}-rewired.cmpct',Path(d),n)
        receipt['status']='PASS'
    except BaseException as e:
        receipt['status']='FAIL'
        receipt['fatal']={'type':type(e).__name__,'message':str(e)}
        raise
    finally:
        (root/'receipt-consumption.json').write_text(
            json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print('J24G95B',json.dumps({'status':receipt['status'],
                   'cases':{k:{'same_inode_size':x['inode_length_unchanged'],
                   'before_accepted':x['pin_established_prior_to_edit'],
                   'after_pin_refuses':x['full_hash_recheck_refuses'],
                   'reader_files':x['public_reader_post_edit']['count']}
                   for k,x in receipt['cases'].items()}},sort_keys=True))
if __name__=='__main__':main()
