from __future__ import annotations

"""Hostile receipt for the research-only hidden-ZIP EOCD preflight."""

import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import zipfile

from experiments.v030_r4_zip_preflight import hidden_zip_preflight, MAX_TAIL, MAX_ENTRIES, MAX_CENTRAL_DIRECTORY


def _eocd(entries:int, cd_size:int, cd_off:int, *, disk:int=0, cd_disk:int=0, n_disk:int|None=None, comment:bytes=b'')->bytes:
    if n_disk is None:n_disk=entries
    return b'PK\x05\x06'+struct.pack('<HHHHIIH',disk,cd_disk,n_disk,entries,cd_size,cd_off,len(comment))+comment


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    cases={}
    # Genuine normal archive should pass.
    normal=work/'normal.bin'
    with zipfile.ZipFile(normal,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for i in range(12):z.writestr(f'member-{i}.txt',(f'row-{i}\n'*1024).encode())
    cases['normal']=hidden_zip_preflight(normal).to_dict()
    # Truncated PK-looking content: bounded reject.
    truncated=work/'truncated.bin';truncated.write_bytes(b'PK\x03\x04'+b'x'*1024)
    cases['truncated']=hidden_zip_preflight(truncated).to_dict()
    # ZIP64 sentinels on optional path: reject rather than delegate uncontrolled metadata work.
    z64=work/'zip64.bin';z64.write_bytes(b'PK\x03\x04'+b'x'*64+_eocd(0xFFFF,0xFFFFFFFF,0xFFFFFFFF))
    cases['zip64']=hidden_zip_preflight(z64).to_dict()
    # Entry budget attack.
    entries=work/'entries.bin';prefix=b'PK\x03\x04'+b'x'*128;entries.write_bytes(prefix+_eocd(MAX_ENTRIES+1,0,len(prefix)))
    cases['entry_budget']=hidden_zip_preflight(entries).to_dict()
    # CD byte budget attack.
    cdb=work/'cd-budget.bin';prefix=b'PK\x03\x04'+b'x'*128;cdb.write_bytes(prefix+_eocd(1,MAX_CENTRAL_DIRECTORY+1,0))
    cases['cd_budget']=hidden_zip_preflight(cdb).to_dict()
    # Out-of-bounds central directory.
    bounds=work/'bounds.bin';prefix=b'PK\x03\x04'+b'x'*128;bounds.write_bytes(prefix+_eocd(1,64,len(prefix)+1))
    cases['bounds']=hidden_zip_preflight(bounds).to_dict()
    # EOCD-looking bytes in comment must not be accepted unless comment length reaches physical EOF.
    comment=work/'comment-trap.bin'
    base=b'PK\x03\x04'+b'x'*128
    fake=_eocd(1,0,len(base))
    outer=_eocd(1,0,len(base),comment=b'noise'+fake+b'tail')
    comment.write_bytes(base+outer)
    cases['comment_trap']=hidden_zip_preflight(comment).to_dict()
    hyp={
        'normal_eligible':cases['normal']['eligible'],
        'truncated_rejected':not cases['truncated']['eligible'],
        'zip64_rejected':cases['zip64']['reason']=='zip64_optional_path_rejected',
        'entry_budget_rejected':cases['entry_budget']['reason']=='entry_budget',
        'cd_budget_rejected':cases['cd_budget']['reason']=='central_directory_budget',
        'bounds_rejected':cases['bounds']['reason']=='central_directory_bounds',
        'all_reads_bounded':all(c['tail_bytes_read']<=MAX_TAIL for c in cases.values()),
    }
    return {'schema':'cmpct-v030-r4-zip-preflight-hostile-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'cases':cases,'hypothesis':{**hyp,'passes':all(hyp.values())},
            'contract':{'diagnostic_only':True,'release_credit':False,'explicit_zip_behavior_changed':False,'reader_changed':False,'format_changed':False,
                        'rejection_means_ordinary_storage_not_data_loss':True},
            'next_if_supported':'compose this preflight ahead of hidden-content stdlib ZIP parsing, then verify Office eligibility and full-matrix byte identity before measuring parser CPU/RSS',
            'next_if_falsified':'fix the preflight structure/bounds logic; do not weaken budgets to make corpus rows pass'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-zip-preflight-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-zip-preflight.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'hypothesis':r['hypothesis'],'cases':{k:(v['eligible'],v['reason'],v['tail_bytes_read']) for k,v in r['cases'].items()}},indent=2))
if __name__=='__main__':main()
