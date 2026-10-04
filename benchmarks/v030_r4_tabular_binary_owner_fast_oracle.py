from __future__ import annotations

"""Compute-efficient writer variant of the authenticated binary tabular owner.

The first binary-owner oracle repaired cold locality but recomputed full CSV and JSONL byte strings per row group
solely to derive segment lengths, making the diagnostic writer ~0.66 s slower.  This variant leaves the physical
owner grammar unchanged and derives exact group lexical lengths directly from the already-present canonical source
bytes.  It fails closed unless each semantic row occupies exactly one newline-terminated physical line, so embedded
newline CSVs or other dialects remain ordinary fallback rather than being normalized.
"""

import argparse, hashlib, json, os, shutil, statistics, struct, time
from pathlib import Path
import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_tabular_owner_oracle as O
from benchmarks import v030_r4_tabular_binary_owner_oracle as B
from benchmarks import v030_r4_zstd_parameter_decomposition as ZD
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET=O.TARGET
GROUPS=(2048,4096,8192)
REPS=3
REQUEST=4096
MAX_STORED_AMP=8.0
MAX_DECODE=8*1024*1024


def _line_lengths(raw:bytes, rows:int, group_rows:int, *, header:bool)->list[int]:
    # Narrow, exact admission: one physical LF-terminated line per row (+ one CSV header).  No normalization.
    if not raw.endswith(b'\n'):
        raise ValueError('tabular fast-owner requires terminal LF')
    lines=raw.splitlines(keepends=True)
    expected=rows+(1 if header else 0)
    if len(lines)!=expected or any(not line.endswith(b'\n') for line in lines):
        raise ValueError('tabular fast-owner rejects multiline/noncanonical lexical rows')
    data=lines[1:] if header else lines
    out=[]
    for gi,start in enumerate(range(0,rows,group_rows)):
        chunk=data[start:start+group_rows]
        n=sum(map(len,chunk))
        if header and gi==0:n+=len(lines[0])
        out.append(n)
    return out


def _manifest(fields:list[str], rows:list[dict], group_rows:int, groups:list[list[tuple[bytes,int]]], csv_lengths:list[int], json_lengths:list[int])->bytes:
    chunks=[struct.pack('<IIIH',len(rows),group_rows,len(groups),len(fields))]
    for f in fields:
        b=f.encode();chunks.append(struct.pack('<H',len(b))+b)
    for gi,start in enumerate(range(0,len(rows),group_rows)):
        chunk=rows[start:start+group_rows]
        chunks.append(struct.pack('<IQQ',len(chunk),csv_lengths[gi],json_lengths[gi]))
        for comp,logical in groups[gi]:chunks.append(struct.pack('<II32s',len(comp),logical,hashlib.sha256(comp).digest()))
    return b''.join(chunks)


def _encode(fields:list[str],rows:list[dict],group_rows:int,csv_lengths:list[int],json_lengths:list[int])->tuple[bytes,dict]:
    cctx=zstd.ZstdCompressor(level=B.LEVEL);groups=[];payload=bytearray()
    for start in range(0,len(rows),group_rows):
        chunk=rows[start:start+group_rows];cols=[]
        for f in fields:
            raw=json.dumps([r[f] for r in chunk],separators=(',',':')).encode();comp=cctx.compress(raw);cols.append((comp,len(raw)));payload.extend(comp)
        groups.append(cols)
    manifest=_manifest(fields,rows,group_rows,groups,csv_lengths,json_lengths)
    prefix=B.MAGIC+struct.pack('<I',len(manifest))+hashlib.sha256(manifest).digest()
    return prefix+manifest+bytes(payload),{'manifest_bytes':len(manifest),'payload_bytes':len(payload),'group_count':len(groups)}


def _requests(n:int):
    l=min(REQUEST,n);return [(0,l),(max(0,n//2-l//2),l),(max(0,n-l),l)]


def _baseline_pair(csv_raw:bytes,json_raw:bytes)->int:
    c=zstd.ZstdCompressor(level=15);return len(c.compress(csv_raw))+len(c.compress(json_raw))+48


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_fast_owner_neutral');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_fast_owner_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus);stage=EXT._normalized_stage(corpus/TARGET,work/'normalized');tree=PRODUCT.treehash(stage)
    csv_raw=(stage/'events.csv').read_bytes();json_raw=(stage/'events.jsonl').read_bytes()
    t=time.process_time();cf,cr=O._parse_csv(csv_raw);jf,jr=O._parse_jsonl(json_raw);parse_cpu=time.process_time()-t
    if cf!=jf or not O._semantic_equal(cf,cr,jr):raise RuntimeError('semantic pair gate failed')
    fixed_root=work/'fixed';profile,_=ZD._prepare(stage,fixed_root);archive=fixed_root/'candidate.cmpnx5';ZD._scan(profile,archive);ZD._verify(profile,archive,fixed_root/'out',tree);fixed=archive.stat().st_size
    accepted=int(GENERAL._accepted_v029_rows()[('neutral_hostile_v1',TARGET)]['accepted_v029_bytes']);pair=_baseline_pair(csv_raw,json_raw)
    variants=[]
    for gr in GROUPS:
        t=time.process_time();csv_lengths=_line_lengths(csv_raw,len(jr),gr,header=True);json_lengths=_line_lengths(json_raw,len(jr),gr,header=False);length_index_cpu=time.process_time()-t
        enc=[];owners=[];stats=None
        for _ in range(REPS):
            t=time.process_time();owner,stats=_encode(cf,jr,gr,csv_lengths,json_lengths);enc.append(time.process_time()-t);owners.append(owner)
        if len(set(owners))!=1:raise RuntimeError('fast owner nondeterministic')
        owner=owners[0];fields,rows=B._full(owner)
        if O._csv_bytes(fields,rows)!=csv_raw or O._jsonl_bytes(rows)!=json_raw:raise RuntimeError('fast owner exact reconstruction failed')
        if not B._corruption(owner):raise RuntimeError('fast owner corruption reject failed')
        req=[]
        for member,raw in (('csv',csv_raw),('jsonl',json_raw)):
            for start,length in _requests(len(raw)):
                got,diag=B._read_range(owner,member,start,length)
                if got!=raw[start:start+length]:raise RuntimeError('fast owner exact range mismatch')
                cold=(diag['payload_bytes_touched']+diag['metadata_bytes_touched_cold'])/length
                req.append({'member':member,'start':start,'length':length,**diag,'cold_stored_amplification':cold})
        saving=pair-len(owner);projection=fixed-saving;charged=parse_cpu+length_index_cpu+statistics.median(enc)
        variants.append({'row_group_rows':gr,'stored_bytes':len(owner),'manifest_bytes':stats['manifest_bytes'],'payload_bytes':stats['payload_bytes'],'parse_cpu_s':parse_cpu,'lexical_length_index_cpu_s':length_index_cpu,'median_encode_cpu_s':statistics.median(enc),'charged_writer_cpu_s':charged,'optimistic_margin_vs_v029_bytes':accepted-projection,'requests':req,'max_cold_stored_amplification':max(r['cold_stored_amplification'] for r in req),'max_decoded_logical_bytes':max(r['decoded_member_segment_bytes'] for r in req),'cold_locality_pass':max(r['cold_stored_amplification'] for r in req)<=MAX_STORED_AMP and max(r['decoded_member_segment_bytes'] for r in req)<=MAX_DECODE})
    supported=[v for v in variants if v['cold_locality_pass'] and v['charged_writer_cpu_s']<1.0 and v['optimistic_margin_vs_v029_bytes']>0]
    return {'schema':'cmpct-v030-r4-tabular-binary-owner-fast-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'workload':TARGET,'canonical_tree_sha256':tree,'row_count':len(jr),'variants':variants,'hypothesis':{'exact_owner_and_ranges':True,'noncanonical_multiline_forms_fail_closed':True,'at_least_one_variant_cold_8x_density_and_under_1s_cpu':bool(supported)},'best_supported_variant':min(supported,key=lambda v:(v['stored_bytes'],v['charged_writer_cpu_s'])) if supported else None,'contract':{'diagnostic_only':True,'release_credit':False,'physical_owner_grammar_changed_from_binary_v1':False,'lexical_lengths_derived_from_exact_source_bytes':True,'multiline_csv_generalization_claimed':False,'production_format_changed':False,'production_selector_changed':False},'next_if_supported':'combine sparse content-driven admission with the fast binary owner in one integrated research archive wrapper; then charge actual complete create/read/RSS/recovery and all hostile fallbacks','next_if_falsified':'writer cost remains too high after eliminating duplicate serialization; profile semantic parsing/column materialization before integration'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-binary-owner-fast-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-binary-owner-fast.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'variants':[{k:v[k] for k in ('row_group_rows','stored_bytes','manifest_bytes','charged_writer_cpu_s','optimistic_margin_vs_v029_bytes','max_cold_stored_amplification','max_decoded_logical_bytes','cold_locality_pass')} for v in r['variants']],'hypothesis':r['hypothesis']},indent=2))

if __name__=='__main__':main()
