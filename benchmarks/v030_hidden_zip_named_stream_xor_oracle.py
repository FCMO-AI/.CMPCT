from __future__ import annotations
"""Strong inherited-prior-art control for #205: named exact-DEFLATE XOR groups.

Adapts the existing v030_raw_deflate_delta_oracle mechanism to the same five gifted Office winners.
No member is inflated. Corresponding ZIP member names form bounded groups; the first exact RFC-1951
payload is a base, later payloads are XOR-prefix residual + target tail, and the complete group is
Zstd-compressed. Every group competes against direct exact-stream storage, so a losing transform is
never credited. Research-only: this measures physical-stream headroom, not a product format.
"""
import argparse,io,json,os,shutil,statistics,struct,time,zipfile
from collections import defaultdict
from pathlib import Path
import zstandard as zstd
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission

REPS=3;LOCAL_HEADER_BYTES=30;LOCAL_SIG=b'PK\x03\x04';LEVEL=3;META_PER_STREAM=40;GROUP_META=32;MAX_DECODE=8*1024*1024;MAX_AMP=8.0;TARGET_RECOVERY=3_680_000

def _payload(raw,info):
    off=int(info.header_offset)
    if off<0 or off+LOCAL_HEADER_BYTES>len(raw) or raw[off:off+4]!=LOCAL_SIG:raise RuntimeError('local header')
    nl,xl=struct.unpack_from('<HH',raw,off+26);start=off+30+nl+xl;end=start+int(info.compress_size)
    if end>len(raw):raise RuntimeError('payload bounds')
    return raw[start:end]

def _xor(base,target):
    n=min(len(base),len(target));return bytes(a^b for a,b in zip(base[:n],target[:n])),target[n:]

def _serialize(streams):
    base=streams[0];out=io.BytesIO();out.write(struct.pack('<I',len(streams)));out.write(struct.pack('<I',len(base)));out.write(base)
    for target in streams[1:]:
        residual,tail=_xor(base,target);out.write(struct.pack('<III',len(target),len(residual),len(tail)));out.write(residual);out.write(tail)
    return out.getvalue()

def _collect(source,admitted):
    groups=defaultdict(list);source_bytes=0;physical=0;count=0
    for rel in admitted:
        raw=(source/rel).read_bytes();source_bytes+=len(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in z.infolist():
                if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED:continue
                stream=_payload(raw,info);groups[info.filename].append(stream);physical+=len(stream);count+=1
    return groups,source_bytes,physical,count

def _represent(groups):
    total_direct=total_charged=0;wins=0;max_decode=max_amp=0.0;rows=[]
    compressor=zstd.ZstdCompressor(level=LEVEL,threads=0)
    for name in sorted(groups):
        streams=groups[name];direct=sum(len(s) for s in streams);total_direct+=direct
        if len(streams)<2:
            charged=direct+META_PER_STREAM;chosen='direct';decode=direct;amp=1.0
        else:
            serialized=_serialize(streams);packed=compressor.compress(serialized);transformed=len(packed)+GROUP_META+META_PER_STREAM*len(streams)
            direct_charged=direct+META_PER_STREAM*len(streams)
            if transformed<direct_charged:
                charged=transformed;chosen='xor-zstd';wins+=1;decode=len(serialized);amp=max(len(serialized)/max(1,len(s)) for s in streams)
            else:
                charged=direct_charged;chosen='direct';decode=max(map(len,streams));amp=1.0
        total_charged+=charged;max_decode=max(max_decode,decode);max_amp=max(max_amp,amp);rows.append({'name':name,'streams':len(streams),'direct_bytes':direct,'charged_bytes':charged,'choice':chosen,'decode_unit_bytes':decode,'max_amp':amp})
    return {'direct_payload_bytes':total_direct,'represented_charged_bytes':total_charged,'recovered_bytes':total_direct-total_charged,'winning_groups':wins,'group_count':len(groups),'max_decode_unit_bytes':int(max_decode),'max_member_read_amplification':max_amp,'locality_green':max_decode<=MAX_DECODE and max_amp<=MAX_AMP,'target_recovery_met':total_direct-total_charged>=TARGET_RECOVERY,'groups':rows}

def run(root):
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_named_xor_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_named_xor_r_{rep}');repair.install_generation_hooks(n);n.build(suite);repair.normalize_root(suite)
        source=suite/'02_office_workspace';tree=PRODUCT.treehash(source);admitted=[a.rel for a in observe_hidden_zip_admission(source).admitted];t0=time.perf_counter();groups,read,physical,count=_collect(source,admitted);repn=_represent(groups);wall=time.perf_counter()-t0
        if PRODUCT.treehash(source)!=tree:raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'tree_sha256':tree,'admitted':admitted,'wall_s':wall,'source_bytes_read':read,'physical_payload_bytes':physical,'stream_count':count,**repn})
    med=lambda k:statistics.median(r[k] for r in rows)
    return {'schema':'cmpct-v030-hidden-zip-named-stream-xor-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':{'direct_payload_bytes_median':med('direct_payload_bytes'),'represented_charged_bytes_median':med('represented_charged_bytes'),'recovered_bytes_median':med('recovered_bytes'),'target_recovery_bytes':TARGET_RECOVERY,'target_recovery_met_all':all(r['target_recovery_met'] for r in rows),'locality_green_all':all(r['locality_green'] for r in rows),'max_decode_unit_bytes':max(r['max_decode_unit_bytes'] for r in rows),'max_member_read_amplification':max(r['max_member_read_amplification'] for r in rows),'winning_groups_median':med('winning_groups'),'wall_s_median':med('wall_s')},'contract':{'no_member_inflation':True,'exact_stream_bytes_only':True,'same_member_name_correspondence':True,'losing_groups_fallback_direct':True,'all_transformed_bytes_and_metadata_charged':True,'decode_unit_ceiling':MAX_DECODE,'read_amplification_ceiling':MAX_AMP,'release_thresholds_unchanged':True},'rows':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-named-xor-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-named-xor.json'));a=p.parse_args();result=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
