from __future__ import annotations

"""Compact binary authenticated-owner oracle for reversible Analytics co-lifting.

The JSON-manifest owner proved density, integrity and bounded warm range reads, but all cold 4 KiB reads exceeded
the 8x stored-byte locality ceiling because verbose metadata had to be authenticated/opened first.  This oracle
changes only control-plane encoding: offsets are derived cumulatively and every row-group/column record uses fixed
binary fields.  Semantic column payloads and row-group partitioning are unchanged.
"""

import argparse, bisect, csv, hashlib, io, json, os, shutil, statistics, struct, time
from pathlib import Path
import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_tabular_owner_oracle as O
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET=O.TARGET
MAGIC=b"TCB2\0\0\0\0"
LEVEL=5
GROUPS=(2048,4096,8192)
REQUEST=4096
MAX_STORED_AMP=8.0
MAX_DECODE=8*1024*1024
REPS=2


def _manifest_bytes(fields:list[str], rows:list[dict], group_rows:int, compressed_groups:list[list[tuple[bytes,int]]]) -> bytes:
    chunks=[]
    group_count=(len(rows)+group_rows-1)//group_rows
    chunks.append(struct.pack('<IIIH',len(rows),group_rows,group_count,len(fields)))
    for f in fields:
        b=f.encode('utf-8'); chunks.append(struct.pack('<H',len(b))+b)
    for gi,start in enumerate(range(0,len(rows),group_rows)):
        chunk=rows[start:start+group_rows]
        csv_len=len(O._csv_bytes(fields,chunk,include_header=(gi==0)))
        json_len=len(O._jsonl_bytes(chunk))
        chunks.append(struct.pack('<IQQ',len(chunk),csv_len,json_len))
        for comp,logical_len in compressed_groups[gi]:
            chunks.append(struct.pack('<II32s',len(comp),logical_len,hashlib.sha256(comp).digest()))
    return b''.join(chunks)


def _encode(fields:list[str], rows:list[dict], group_rows:int)->tuple[bytes,dict]:
    cctx=zstd.ZstdCompressor(level=LEVEL); groups=[]; payload=bytearray()
    for start in range(0,len(rows),group_rows):
        chunk=rows[start:start+group_rows]; cols=[]
        for f in fields:
            raw=json.dumps([r[f] for r in chunk],separators=(',',':')).encode()
            comp=cctx.compress(raw); cols.append((comp,len(raw))); payload.extend(comp)
        groups.append(cols)
    manifest=_manifest_bytes(fields,rows,group_rows,groups)
    prefix=MAGIC+struct.pack('<I',len(manifest))+hashlib.sha256(manifest).digest()
    return prefix+manifest+bytes(payload),{'manifest_bytes':len(manifest),'prefix_bytes':len(prefix),'payload_bytes':len(payload),'group_count':len(groups)}


def _open(owner:bytes)->tuple[dict,int]:
    if len(owner)<44 or owner[:8]!=MAGIC: raise ValueError('bad binary owner header')
    n=struct.unpack('<I',owner[8:12])[0]; end=44+n
    if end>len(owner): raise ValueError('truncated binary owner manifest')
    raw=owner[44:end]
    if hashlib.sha256(raw).digest()!=owner[12:44]: raise ValueError('binary owner manifest authentication failed')
    at=0
    if len(raw)<14: raise ValueError('short binary owner manifest')
    row_count,group_rows,group_count,field_count=struct.unpack('<IIIH',raw[at:at+14]); at+=14
    fields=[]
    for _ in range(field_count):
        if at+2>len(raw): raise ValueError('truncated field name length')
        ln=struct.unpack('<H',raw[at:at+2])[0]; at+=2
        if at+ln>len(raw): raise ValueError('truncated field name')
        fields.append(raw[at:at+ln].decode()); at+=ln
    groups=[]; payload_offset=0
    for _ in range(group_count):
        if at+20>len(raw): raise ValueError('truncated group record')
        rows_n,csv_len,json_len=struct.unpack('<IQQ',raw[at:at+20]); at+=20
        cols=[]
        for field in fields:
            if at+40>len(raw): raise ValueError('truncated column record')
            stored,logical,digest=struct.unpack('<II32s',raw[at:at+40]); at+=40
            cols.append({'field':field,'offset':payload_offset,'stored_bytes':stored,'logical_column_bytes':logical,'sha256':digest})
            payload_offset+=stored
        groups.append({'row_count':rows_n,'csv_bytes':csv_len,'jsonl_bytes':json_len,'columns':cols})
    if at!=len(raw): raise ValueError('trailing binary manifest bytes')
    if end+payload_offset!=len(owner): raise ValueError('binary owner payload length mismatch')
    return {'row_count':row_count,'row_group_rows':group_rows,'fields':fields,'groups':groups},end


def _decode_group(owner:bytes,m:dict,base:int,gi:int)->list[dict]:
    g=m['groups'][gi]; columns=[]; dctx=zstd.ZstdDecompressor()
    for c in g['columns']:
        s=base+c['offset']; e=s+c['stored_bytes']; comp=owner[s:e]
        if hashlib.sha256(comp).digest()!=c['sha256']: raise ValueError('binary owner payload authentication failed')
        raw=dctx.decompress(comp)
        if len(raw)!=c['logical_column_bytes']: raise ValueError('binary owner column logical length mismatch')
        columns.append(json.loads(raw.decode()))
    n=g['row_count']
    if any(len(c)!=n for c in columns): raise ValueError('binary owner column row mismatch')
    return [{f:columns[j][i] for j,f in enumerate(m['fields'])} for i in range(n)]


def _full(owner:bytes)->tuple[list[str],list[dict]]:
    m,base=_open(owner); rows=[]
    for gi in range(len(m['groups'])): rows.extend(_decode_group(owner,m,base,gi))
    if len(rows)!=m['row_count']: raise ValueError('binary owner total row mismatch')
    return list(m['fields']),rows


def _prefix(m:dict,member:str)->list[int]:
    key='csv_bytes' if member=='csv' else 'jsonl_bytes'; out=[0]
    for g in m['groups']: out.append(out[-1]+g[key])
    return out


def _read_range(owner:bytes,member:str,start:int,length:int)->tuple[bytes,dict]:
    m,base=_open(owner); pref=_prefix(m,member); total=pref[-1]
    if start<0 or length<0 or start+length>total: raise ValueError('range outside member')
    if not length:return b'',{'groups_touched':0,'payload_bytes_touched':0,'decoded_member_segment_bytes':0,'metadata_bytes_touched_cold':base}
    first=max(0,bisect.bisect_right(pref,start)-1); last=max(first,bisect.bisect_left(pref,start+length)-1)
    pieces=[]; physical=decoded=0
    for gi in range(first,last+1):
        g=m['groups'][gi]; rows=_decode_group(owner,m,base,gi); physical+=sum(c['stored_bytes'] for c in g['columns'])
        seg=O._csv_bytes(m['fields'],rows,include_header=(gi==0)) if member=='csv' else O._jsonl_bytes(rows)
        expected=g['csv_bytes'] if member=='csv' else g['jsonl_bytes']
        if len(seg)!=expected: raise RuntimeError('binary lexical-length drift')
        pieces.append(seg); decoded+=len(seg)
    joined=b''.join(pieces); rel=start-pref[first]; ans=joined[rel:rel+length]
    if len(ans)!=length: raise RuntimeError('short binary-owner range')
    return ans,{'groups_touched':last-first+1,'payload_bytes_touched':physical,'decoded_member_segment_bytes':decoded,'metadata_bytes_touched_cold':base}


def _requests(n:int):
    l=min(REQUEST,n); return [(0,l),(max(0,n//2-l//2),l),(max(0,n-l),l)]


def _corruption(owner:bytes)->bool:
    m,base=_open(owner); damaged=bytearray(owner); damaged[base+m['groups'][0]['columns'][0]['offset']]^=1
    try:_decode_group(bytes(damaged),m,base,0)
    except ValueError as e:return 'authentication failed' in str(e)
    return False


def _baseline_pair(csv_raw:bytes,json_raw:bytes)->int:
    c=zstd.ZstdCompressor(level=15); return len(c.compress(csv_raw))+len(c.compress(json_raw))+48


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_binary_owner_neutral');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_binary_owner_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus);stage=EXT._normalized_stage(corpus/TARGET,work/'normalized');tree=PRODUCT.treehash(stage)
    csv_raw=(stage/'events.csv').read_bytes();json_raw=(stage/'events.jsonl').read_bytes();started=time.perf_counter();cf,cr=O._parse_csv(csv_raw);jf,jr=O._parse_jsonl(json_raw);parse_s=time.perf_counter()-started
    if cf!=jf or not O._semantic_equal(cf,cr,jr):raise RuntimeError('semantic pair gate failed')
    fixed_root=work/'fixed';profile,_=__import__('benchmarks.v030_r4_zstd_parameter_decomposition',fromlist=['_prepare'])._prepare(stage,fixed_root); archive=fixed_root/'candidate.cmpnx5'; ZD=__import__('benchmarks.v030_r4_zstd_parameter_decomposition',fromlist=['_scan','_verify']);ZD._scan(profile,archive);ZD._verify(profile,archive,fixed_root/'out',tree)
    fixed=archive.stat().st_size;accepted=int(GENERAL._accepted_v029_rows()[('neutral_hostile_v1',TARGET)]['accepted_v029_bytes']);pair=_baseline_pair(csv_raw,json_raw)
    variants=[]
    for gr in GROUPS:
        enc=[];dec=[];owners=[];stats=None
        for _ in range(REPS):
            t=time.perf_counter();owner,stats=_encode(cf,jr,gr);enc.append(time.perf_counter()-t);owners.append(owner)
            t=time.perf_counter();fields,rows=_full(owner);rebuilt_csv=O._csv_bytes(fields,rows);rebuilt_json=O._jsonl_bytes(rows);dec.append(time.perf_counter()-t)
            if rebuilt_csv!=csv_raw or rebuilt_json!=json_raw:raise RuntimeError('binary owner exact full reconstruction failed')
            if not _corruption(owner):raise RuntimeError('binary owner corruption control failed')
        if owners[0]!=owners[1]:raise RuntimeError('binary owner nondeterministic')
        owner=owners[0];req=[]
        for member,raw in (('csv',csv_raw),('jsonl',json_raw)):
            for start,length in _requests(len(raw)):
                got,diag=_read_range(owner,member,start,length)
                if got!=raw[start:start+length]:raise RuntimeError(f'binary exact range mismatch {member} {start}')
                warm=diag['payload_bytes_touched']/length;cold=(diag['payload_bytes_touched']+diag['metadata_bytes_touched_cold'])/length
                req.append({'member':member,'start':start,'length':length,**diag,'warm_stored_amplification':warm,'cold_stored_amplification':cold,'decoded_logical_amplification':diag['decoded_member_segment_bytes']/length})
        saving=pair-len(owner);projection=fixed-saving
        variants.append({'row_group_rows':gr,'stored_bytes':len(owner),'manifest_bytes':stats['manifest_bytes'],'payload_bytes':stats['payload_bytes'],'group_count':stats['group_count'],'median_encode_s':statistics.median(enc),'median_decode_and_reconstruct_both_s':statistics.median(dec),'charged_writer_s':parse_s+statistics.median(enc),'pair_saving_vs_independent_zstd15_bytes':saving,'optimistic_projected_whole_archive_bytes':projection,'optimistic_margin_vs_v029_bytes':accepted-projection,'requests':req,'max_warm_stored_amplification':max(r['warm_stored_amplification'] for r in req),'max_cold_stored_amplification':max(r['cold_stored_amplification'] for r in req),'max_decoded_logical_bytes':max(r['decoded_member_segment_bytes'] for r in req),'cold_locality_pass':max(r['cold_stored_amplification'] for r in req)<=MAX_STORED_AMP and max(r['decoded_member_segment_bytes'] for r in req)<=MAX_DECODE})
    supported=[v for v in variants if v['cold_locality_pass'] and v['charged_writer_s']<1.0 and v['optimistic_margin_vs_v029_bytes']>0]
    best=min(supported or variants,key=lambda v:(v['stored_bytes'],v['max_cold_stored_amplification']))
    return {'schema':'cmpct-v030-r4-tabular-binary-owner-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'workload':TARGET,'canonical_tree_sha256':tree,'row_count':len(jr),'fields':cf,'source_bytes':{'csv':len(csv_raw),'jsonl':len(json_raw),'total':len(csv_raw)+len(json_raw)},'parse_and_equivalence_s':parse_s,'independent_pair_zstd15_bytes':pair,'fixed_level15_archive_bytes':fixed,'accepted_v029_bytes':accepted,'variants':variants,'best_supported_variant':best if supported else None,'hypothesis':{'exact_full_reconstruction':True,'exact_4k_ranges_reconstructed':True,'payload_corruption_rejected':True,'deterministic_owner_bytes':True,'at_least_one_cold_owner_meets_8x_8mib_density_and_writer':bool(supported)},'contract':{'diagnostic_only':True,'release_credit':False,'production_format_changed':False,'production_selector_changed':False,'binary_manifest_authenticated':True,'payloads_authenticated':True,'offsets_derived_not_stored':True,'range_lengths_in_authenticated_manifest':True,'reader_discovery':False,'whole_archive_projection_is_optimistic_not_integrated_product_size':True},'next_if_supported':'advance selected binary owner to one research-only integrated product wrapper with actual complete archive ownership, content-driven admission, create/read/RSS/recovery and hostile false-positive controls','next_if_falsified':'binary metadata alone does not repair cold locality; redesign row-group physical partition/index before product integration'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-binary-owner-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-binary-owner.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'variants':[{k:v[k] for k in ('row_group_rows','stored_bytes','manifest_bytes','optimistic_margin_vs_v029_bytes','charged_writer_s','max_cold_stored_amplification','max_decoded_logical_bytes','cold_locality_pass')} for v in r['variants']],'hypothesis':r['hypothesis']},indent=2))

if __name__=='__main__':main()
