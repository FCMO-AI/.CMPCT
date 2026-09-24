from __future__ import annotations
"""Charged exact-stream slab oracle derived from the proven v0.25 Office stream-pool mechanism.

Physical-only mode1 is fast but leaves ~9.45 MB of exact Deflate payload. v0.25 proved that exact stream
pools can be secondary-compressed, but its 512 KiB cold slabs are not automatically compatible with
#205's 4 KiB selective-read accounting. This oracle therefore tests the strongest immediately valid
32 KiB decode-unit control (<=8x for a 4 KiB request), plus larger diagnostic slabs with no product credit.
No ZIP member is inflated; exact stream bytes are only deduplicated, concatenated and Zstd-3 competed.
"""
import argparse,hashlib,io,json,os,shutil,statistics,struct,time,zipfile
from pathlib import Path
import zstandard as zstd
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission

REPS=3;LOCAL=30;SIG=b'PK\x03\x04';SLABS=(32*1024,64*1024,128*1024,512*1024);PH=struct.calcsize('<BQQI32s');REF_META=40;TARGET_RECOVERY=3_680_000

def _payload(raw,info):
    off=int(info.header_offset)
    if off<0 or off+LOCAL>len(raw) or raw[off:off+4]!=SIG:raise RuntimeError('local header')
    nl,xl=struct.unpack_from('<HH',raw,off+26);s=off+LOCAL+nl+xl;e=s+int(info.compress_size)
    if e>len(raw):raise RuntimeError('payload bounds')
    return raw[s:e]

def _collect(source,admitted):
    unique=[];seen={};total=0;aliases=0;read=0
    for rel in admitted:
        raw=(source/rel).read_bytes();read+=len(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in sorted((i for i in z.infolist() if not i.is_dir() and i.compress_type==zipfile.ZIP_DEFLATED),key=lambda i:i.header_offset):
                b=_payload(raw,info);total+=len(b);h=hashlib.sha256(b).digest()
                if h in seen and unique[seen[h]]==b:aliases+=1
                else:seen[h]=len(unique);unique.append(b)
    return unique,total,aliases,read

def _slabs(unique,limit):
    chunks=[];cur=bytearray()
    def flush():
        nonlocal cur
        if cur:chunks.append(bytes(cur));cur=bytearray()
    for stream in unique:
        if len(stream)>limit:
            flush();chunks.extend(stream[o:o+limit] for o in range(0,len(stream),limit));continue
        if cur and len(cur)+len(stream)>limit:flush()
        cur.extend(stream)
    flush();return chunks

def _represent(unique,aliases,limit):
    comp=zstd.ZstdCompressor(level=3,threads=0);slabs=_slabs(unique,limit);stored=0;compressed=0;t0=time.perf_counter()
    for raw in slabs:
        packed=comp.compress(raw)
        if len(packed)+8<len(raw):stored+=len(packed)+PH;compressed+=1
        else:stored+=len(raw)+PH
    wall=time.perf_counter()-t0;meta=REF_META*(len(unique)+aliases);direct=sum(len(x) for x in unique)+meta
    return {'slab_bytes':limit,'slabs':len(slabs),'compressed_slabs':compressed,'direct_unique_plus_meta_bytes':direct,'represented_charged_bytes':stored+meta,'recovered_bytes':direct-(stored+meta),'zstd3_wall_s':wall,'decode_unit_bytes':limit,'four_kib_amplification':limit/4096,'locality_green_for_4k':limit/4096<=8.0,'target_recovery_met':direct-(stored+meta)>=TARGET_RECOVERY}

def run(root):
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_stream_slab_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_stream_slab_r_{rep}');repair.install_generation_hooks(n);n.build(suite);repair.normalize_root(suite)
        source=suite/'02_office_workspace';tree=PRODUCT.treehash(source);admitted=[a.rel for a in observe_hidden_zip_admission(source).admitted];unique,total,aliases,read=_collect(source,admitted);variants=[_represent(unique,aliases,s) for s in SLABS]
        if PRODUCT.treehash(source)!=tree:raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'tree_sha256':tree,'admitted':admitted,'physical_payload_occurrence_bytes':total,'unique_stream_bytes':sum(map(len,unique)),'unique_streams':len(unique),'exact_aliases':aliases,'source_bytes_read':read,'variants':variants})
    summary=[]
    for i,limit in enumerate(SLABS):
        vs=[r['variants'][i] for r in rows];summary.append({'slab_bytes':limit,'represented_charged_bytes_median':statistics.median(v['represented_charged_bytes'] for v in vs),'recovered_bytes_median':statistics.median(v['recovered_bytes'] for v in vs),'zstd3_wall_s_median':statistics.median(v['zstd3_wall_s'] for v in vs),'four_kib_amplification':vs[0]['four_kib_amplification'],'locality_green_for_4k':vs[0]['locality_green_for_4k'],'target_recovery_met_all':all(v['target_recovery_met'] for v in vs)})
    return {'schema':'cmpct-v030-hidden-zip-stream-slab-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':summary,'contract':{'no_member_inflation':True,'exact_stream_dedup':True,'zstd_level':3,'all_slab_headers_and_reference_metadata_charged':True,'32k_variant_is_immediately_compatible_with_4k_le8x_decode_unit_bound':True,'larger_variants_diagnostic_only':True,'release_thresholds_unchanged':True},'rows':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-stream-slab-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-stream-slab.json'));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['summary'],indent=2))
if __name__=='__main__':main()
