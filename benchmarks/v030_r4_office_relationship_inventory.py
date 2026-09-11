from __future__ import annotations

"""Cheap causal inventory for the dominant unresolved v0.30 Office density deficit.

This does not compress the corpus or propose a shipping opcode. It inventories exact relationships
already present between ordinary files and ZIP-family members (DOCX/XLSX/PPTX), and asks which
DEFLATE streams are reproducible under the existing r24 stream-mode-2 semantic. The point is to
quantify structural opportunity before paying expensive synthesis or importing v0.25 machinery.
"""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from cmpct.codec import deflate_level_for

SCHEMA="cmpct-v030-r4-office-relationship-inventory-v1"
LFH_FIXED=30
ZIP_SUFFIXES={'.docx','.xlsx','.pptx','.zip'}


def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()


def raw_stream(blob:bytes, info:zipfile.ZipInfo)->bytes:
    nl,xl=struct.unpack_from('<HH',blob,info.header_offset+26)
    s=info.header_offset+LFH_FIXED+nl+xl
    return blob[s:s+info.compress_size]


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    NEUTRAL.corpus_office(work)
    root=work/'02_office_workspace'
    ordinary={}
    for p in sorted(q for q in root.rglob('*') if q.is_file() and q.suffix.lower() not in ZIP_SUFFIXES):
        b=p.read_bytes(); ordinary.setdefault(sha(b),[]).append({'path':p.relative_to(root).as_posix(),'bytes':len(b)})

    payload_groups=defaultdict(list); stream_groups=defaultdict(list)
    members=[]; mode2_count=mode2_payload=mode2_stream=0
    for zp in sorted(q for q in root.rglob('*') if q.is_file() and q.suffix.lower() in ZIP_SUFFIXES):
        blob=zp.read_bytes()
        with zipfile.ZipFile(zp,'r') as zf:
            for info in zf.infolist():
                if info.is_dir(): continue
                raw=zf.read(info.filename); st=raw_stream(blob,info)
                level=None
                if info.compress_type==zipfile.ZIP_DEFLATED:
                    level=deflate_level_for(raw,st)
                    if level is not None:
                        mode2_count+=1; mode2_payload+=len(raw); mode2_stream+=len(st)
                rec={'container':zp.relative_to(root).as_posix(),'member':info.filename,'raw_bytes':len(raw),'compressed_bytes':len(st),'method':int(info.compress_type),'mode2_level':level,'raw_sha256':sha(raw),'stream_sha256':sha(st)}
                members.append(rec); payload_groups[rec['raw_sha256']].append(rec); stream_groups[rec['stream_sha256']].append(rec)

    cross=[]; exact_member_dups=[]; exact_stream_dups=[]
    for h,rs in payload_groups.items():
        if h in ordinary:
            cross.append({'sha256':h,'ordinary':ordinary[h],'members':[{'container':r['container'],'member':r['member'],'raw_bytes':r['raw_bytes'],'compressed_bytes':r['compressed_bytes'],'mode2_level':r['mode2_level']} for r in rs]})
        if len(rs)>1:
            exact_member_dups.append({'sha256':h,'count':len(rs),'raw_bytes_each':rs[0]['raw_bytes'],'avoidable_raw_duplicates':(len(rs)-1)*rs[0]['raw_bytes'],'members':[f"{r['container']}::{r['member']}" for r in rs]})
    for h,rs in stream_groups.items():
        if len(rs)>1:
            exact_stream_dups.append({'sha256':h,'count':len(rs),'compressed_bytes_each':rs[0]['compressed_bytes'],'avoidable_stream_duplicates':(len(rs)-1)*rs[0]['compressed_bytes'],'members':[f"{r['container']}::{r['member']}" for r in rs]})

    cross_raw=sum(sum(o['bytes'] for o in x['ordinary'])+sum(m['raw_bytes'] for m in x['members']) for x in cross)
    cross_avoidable=sum((len(x['ordinary'])+len(x['members'])-1)*(x['ordinary'][0]['bytes'] if x['ordinary'] else x['members'][0]['raw_bytes']) for x in cross)
    return {'schema':SCHEMA,'office_root_bytes':sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),'zip_member_count':len(members),'zip_member_raw_bytes':sum(r['raw_bytes'] for r in members),'zip_member_compressed_bytes':sum(r['compressed_bytes'] for r in members),'mode2_reproducible_member_count':mode2_count,'mode2_reproducible_raw_bytes':mode2_payload,'mode2_reproducible_stream_bytes':mode2_stream,'external_member_identity_group_count':len(cross),'external_member_identity_total_participating_raw_bytes':cross_raw,'external_member_identity_avoidable_raw_duplicate_bytes':cross_avoidable,'exact_member_duplicate_group_count':len(exact_member_dups),'exact_member_duplicate_avoidable_raw_bytes':sum(x['avoidable_raw_duplicates'] for x in exact_member_dups),'exact_stream_duplicate_group_count':len(exact_stream_dups),'exact_stream_duplicate_avoidable_bytes':sum(x['avoidable_stream_duplicates'] for x in exact_stream_dups),'top_external_member_identities':sorted(cross,key=lambda x:sum(o['bytes'] for o in x['ordinary'])+sum(m['raw_bytes'] for m in x['members']),reverse=True)[:20],'top_member_duplicate_groups':sorted(exact_member_dups,key=lambda x:x['avoidable_raw_duplicates'],reverse=True)[:20],'top_stream_duplicate_groups':sorted(exact_stream_dups,key=lambda x:x['avoidable_stream_duplicates'],reverse=True)[:20],'contract':{'diagnostic_only':True,'release_credit':False,'cheap_exact_relationships_only':True,'no_semantic_similarity_claim':True,'no_locality_credit':True,'no_threshold_sweep':True},'next':'Use this inventory to decide whether Office warrants exact federation/mode2 experiments before any expensive resemblance synthesis; preserve locality as a first-class cost.'}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-inventory-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-inventory.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps({k:d[k] for k in ('office_root_bytes','zip_member_count','zip_member_raw_bytes','zip_member_compressed_bytes','mode2_reproducible_member_count','mode2_reproducible_raw_bytes','mode2_reproducible_stream_bytes','external_member_identity_group_count','external_member_identity_avoidable_raw_duplicate_bytes','exact_member_duplicate_group_count','exact_member_duplicate_avoidable_raw_bytes','exact_stream_duplicate_group_count','exact_stream_duplicate_avoidable_bytes')},indent=2))
if __name__=='__main__': main()
