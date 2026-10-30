#!/usr/bin/env python3
"""Independent byte-only J24G95b referee. Standard library; no CMPCT import."""
import hashlib,json,struct,sys
from pathlib import Path
FOOTER=struct.Struct('<8sBBBBQQQ32s')
PREV=struct.calcsize('<8sBBBBQQ')
def digest(v):return hashlib.sha256(v).hexdigest()
def main(root):
    receipt=json.loads((root/'receipt-consumption.json').read_text())
    assert receipt['status']=='PASS' and receipt['product_credit']==0
    summary={}
    for sn,case in receipt['cases'].items():
        n=int(sn)
        original=(root/f'{n}-normal.cmpct').read_bytes()
        edited=(root/f'{n}-consumption-edited.cmpct').read_bytes()
        alt=(root/f'{n}-rewired.cmpct').read_bytes()
        assert original!=edited and edited==alt and len(original)==len(edited)
        off=len(original)-FOOTER.size
        old=FOOTER.unpack_from(original,off);new=FOOTER.unpack_from(edited,off)
        assert old[0]==b'CMPTF24\0' and new[0]==old[0]
        assert old[-1]==new[-1] and old[-2]!=new[-2]
        assert old[:7]==new[:7]
        modified=[i for i,(x,y) in enumerate(zip(original,edited)) if x!=y]
        assert modified==case['modified_byte_positions']
        assert all(off+PREV<=i<off+PREV+8 for i in modified)
        assert digest(original)==case['intact_sha256']
        assert digest(edited)==case['changed_sha256']
        assert not case['full_hash_recheck_refuses']==False
        assert case['inode_length_unchanged']
        assert case['stat_before']['size']==len(original)==case['stat_after']['size']
        assert case['stat_before']['ino']==case['stat_after']['ino']
        assert case['stat_before']['dev']==case['stat_after']['dev']
        assert case['public_reader_post_edit']['count']==n-2
        assert case['public_preflight_post_edit_files']==n-2
        summary[sn]={'original_bytes':len(original),'modified_bytes':len(modified),
                     'same_inode_size':True,'intact_sha256':digest(original),
                     'modified_sha256':digest(edited)}
    answer={'status':'PASS','source':receipt['source']['head'],
            'cases':summary,'scope':'detached physical referee; installed semantics in original receipts'}
    (root/'detached-custody-audit.json').write_text(json.dumps(answer,sort_keys=True,indent=2)+'\n')
    print('J24G95B_DETACHED',json.dumps(answer,sort_keys=True))
if __name__=='__main__':main(Path(sys.argv[1]))
