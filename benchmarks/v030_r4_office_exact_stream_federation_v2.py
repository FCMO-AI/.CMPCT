from __future__ import annotations

"""Compact/indexed exact Office ZIP-stream federation falsifier.

V1 intentionally used a transparent JSON-hex package template so every byte of the causal mechanism
was inspectable. This V2 changes only the wrapper representation: literal ZIP framing/nonshared
regions are concatenated into a binary literal pool and templates store bounded offset/length
segments. Repeated byte-identical compressed member streams remain in one shared stream pool.

That gives a direct range map for every package byte: a selected range is composed only from slices of
literal.bin and/or streams.bin, with no inflate/regeneration discovery in the reader. The diagnostic
charges all authenticated wrapper bytes, verifies byte-exact package reconstruction and reports an
ideal indexed 4 KiB pool-touch amplification. It is still research packaging, not release authority.
"""

import argparse, hashlib, json, os, shutil, struct, time, zipfile
from collections import defaultdict
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA='cmpct-v030-r4-office-exact-stream-federation-v2'
MAGIC=b'R4OSF2\0\0'
ZIP_SUFFIXES={'.docx','.xlsx','.pptx','.zip'}
LFH_FIXED=30
ACCEPTED_V029_OFFICE=5_954_026
REQUEST=4096
MAX_POOL_TOUCH_AMP=8.0


def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def statrec(p:Path)->dict:
    st=p.stat(); return {'mode':int(st.st_mode&0o7777),'mtime_ns':int(st.st_mtime_ns)}
def stream_range(blob:bytes, info:zipfile.ZipInfo)->tuple[int,int]:
    nl,xl=struct.unpack_from('<HH',blob,info.header_offset+26); s=info.header_offset+LFH_FIXED+nl+xl; return s,s+info.compress_size

def discover(root:Path):
    occur=defaultdict(list); containers={}
    for p in sorted(q for q in root.rglob('*') if q.is_file() and q.suffix.lower() in ZIP_SUFFIXES):
        blob=p.read_bytes(); recs=[]
        with zipfile.ZipFile(p,'r') as zf:
            for info in zf.infolist():
                if info.is_dir(): continue
                s,e=stream_range(blob,info); st=blob[s:e]; h=sha(st); rec={'start':s,'end':e,'hash':h,'bytes':len(st),'member':info.filename}; recs.append(rec); occur[h].append((p,rec,st))
        containers[p]={'blob':blob,'members':recs}
    shared={h:xs[0][2] for h,xs in occur.items() if len(xs)>=2 and len(xs[0][2])>0}
    return containers,shared

def build_layout(containers:dict,shared:dict[str,bytes]):
    literal=bytearray(); templates={}
    for p,v in containers.items():
        blob=v['blob']; pos=0; segs=[]
        targets=sorted((r for r in v['members'] if r['hash'] in shared),key=lambda r:r['start'])
        for r in targets:
            if r['start']<pos: raise RuntimeError('overlap')
            if r['start']>pos:
                off=len(literal); literal.extend(blob[pos:r['start']]); segs.append({'k':'l','o':off,'n':r['start']-pos})
            segs.append({'k':'s','h':r['hash'],'n':r['end']-r['start']}); pos=r['end']
        if pos<len(blob):
            off=len(literal); literal.extend(blob[pos:]); segs.append({'k':'l','o':off,'n':len(blob)-pos})
        templates[p]={'size':len(blob),'segments':segs}
    stream_pool=bytearray(); sidx={}
    for h,b in sorted(shared.items()): sidx[h]={'o':len(stream_pool),'n':len(b)}; stream_pool.extend(b)
    return bytes(literal),bytes(stream_pool),sidx,templates

def reconstruct(t:dict,literal:bytes,streams:bytes,sidx:dict)->bytes:
    out=bytearray()
    for x in t['segments']:
        if x['k']=='l': out.extend(literal[x['o']:x['o']+x['n']])
        else:
            s=sidx[x['h']]; out.extend(streams[s['o']:s['o']+s['n']])
    if len(out)!=t['size']: raise RuntimeError('size mismatch')
    return bytes(out)
def pool_touch_for_range(t:dict,start:int,length:int)->int:
    end=min(t['size'],start+length); logical=0; touched=0
    for seg in t['segments']:
        ss=logical; se=logical+seg['n']; logical=se
        ov=max(0,min(end,se)-max(start,ss))
        if ov: touched+=ov
    return touched

def build_candidate(root:Path,out:Path,work:Path)->dict:
    containers,shared=discover(root)
    if not shared: raise RuntimeError('no exact shared streams')
    stripped=work/'stripped'; shutil.copytree(root,stripped); meta={}
    for p in containers:
        rel=p.relative_to(root); meta[rel.as_posix()]=statrec(p); (stripped/rel).unlink()
    base=work/'base.cmpct'; PRODUCT.build(stripped,base)
    literal,streams,sidx,templates_abs=build_layout(containers,shared)
    templates={p.relative_to(root).as_posix():t for p,t in templates_abs.items()}
    manifest={'schema':'cmpct-v030-r4-office-stream-federation-v2-bundle','templates':templates,'stream_index':sidx,'metadata':meta}
    out.mkdir(parents=True,exist_ok=False); shutil.copy2(base,out/'base.cmpct'); (out/'literal.bin').write_bytes(literal); (out/'streams.bin').write_bytes(streams)
    mraw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode(); (out/'manifest.json').write_bytes(mraw)
    pieces=[(out/'base.cmpct').read_bytes(),literal,streams,mraw]; (out/'auth.bin').write_bytes(MAGIC+b''.join(hashlib.sha256(x).digest() for x in pieces))
    sizes={p.name:p.stat().st_size for p in out.iterdir() if p.is_file()}
    req=[]
    for rel,t in templates.items():
        n=min(REQUEST,t['size'])
        for start in sorted({0,max(0,t['size']//2-n//2),max(0,t['size']-n)}):
            touch=pool_touch_for_range(t,start,n); req.append({'path':rel,'start':start,'length':n,'pool_payload_bytes_touched':touch,'pool_touch_amplification':touch/max(1,n)})
    occ=sum(r['bytes'] for v in containers.values() for r in v['members'] if r['hash'] in shared)
    return {'stored_bytes':sum(sizes.values()),'component_bytes':sizes,'shared_stream_count':len(shared),'shared_stream_bytes':len(streams),'literal_pool_bytes':len(literal),'all_duplicate_occurrence_bytes':occ,'raw_duplicate_stream_saving_before_metadata':occ-len(streams),'selective_requests':req,'max_ideal_pool_touch_amplification':max(r['pool_touch_amplification'] for r in req) if req else 0.0}
def extract_candidate(bundle:Path,out:Path)->dict:
    mraw=(bundle/'manifest.json').read_bytes(); m=json.loads(mraw); literal=(bundle/'literal.bin').read_bytes(); streams=(bundle/'streams.bin').read_bytes(); base=(bundle/'base.cmpct').read_bytes(); pieces=[base,literal,streams,mraw]
    if (bundle/'auth.bin').read_bytes()!=MAGIC+b''.join(hashlib.sha256(x).digest() for x in pieces): raise RuntimeError('auth mismatch')
    PRODUCT.extract(bundle/'base.cmpct',out)
    for rel,t in m['templates'].items():
        b=reconstruct(t,literal,streams,m['stream_index']); p=out/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b); md=m['metadata'][rel]; os.chmod(p,int(md['mode'])); os.utime(p,ns=(int(md['mtime_ns']),int(md['mtime_ns'])))
    return {'tree_sha256':PRODUCT.treehash(out),'base_strong_verify':dict(PRODUCT.strong_verify(bundle/'base.cmpct'))}
def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_office_sfv2_neutral'); repair=V029._load(V029.REPAIR_PATH,'r4_office_sfv2_repair'); repair.install_generation_hooks(neutral)
    corpus=work/'neutral'; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/'02_office_workspace'; expected=PRODUCT.treehash(source)
    base=work/'baseline.cmpct'; w=time.perf_counter(); PRODUCT.build(source,base); bw=time.perf_counter()-w
    cand=work/'candidate'; w=time.perf_counter(); cs=build_candidate(source,cand,work/'cand-work'); cw=time.perf_counter()-w; v=extract_candidate(cand,work/'extract')
    if v['tree_sha256']!=expected: raise RuntimeError('tree mismatch')
    return {'schema':SCHEMA,'tree_sha256':expected,'baseline_v030_bytes':base.stat().st_size,'candidate_bytes':cs['stored_bytes'],'accepted_v029_office_bytes':ACCEPTED_V029_OFFICE,'saving_vs_v030_bytes':base.stat().st_size-cs['stored_bytes'],'margin_vs_v029_bytes':ACCEPTED_V029_OFFICE-cs['stored_bytes'],'baseline_create_wall_s':bw,'candidate_create_wall_s':cw,'candidate':cs,'verify':v,'hypothesis':{'compact_exact_federation_beats_v030':cs['stored_bytes']<base.stat().st_size,'compact_exact_federation_beats_v029':cs['stored_bytes']<ACCEPTED_V029_OFFICE,'ideal_pool_touch_meets_8x':cs['max_ideal_pool_touch_amplification']<=MAX_POOL_TOUCH_AMP},'contract':{'diagnostic_only':True,'release_credit':False,'exact_compressed_stream_identity_only':True,'same_semantic_tree_verified':True,'indexed_binary_literal_pool':True,'ideal_pool_touch_not_physical_io':True,'no_mode2_regeneration':True,'no_threshold_sweep':True},'next_if_supported':'instrument actual file-backed range reads plus auth proof/recovery/native overhead, then combine with evidence-backed Analytics mechanism in full matrix','next_if_falsified':'retain exact relationship inventory and attribute whether residual gap is nonshared streams, framing, or base representation before resemblance search'}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-sfv2-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-sfv2.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps({k:d[k] for k in ('baseline_v030_bytes','candidate_bytes','accepted_v029_office_bytes','saving_vs_v030_bytes','margin_vs_v029_bytes','baseline_create_wall_s','candidate_create_wall_s','hypothesis')}|{'components':d['candidate']['component_bytes'],'shared_stream_count':d['candidate']['shared_stream_count'],'raw_duplicate_stream_saving_before_metadata':d['candidate']['raw_duplicate_stream_saving_before_metadata'],'max_ideal_pool_touch_amplification':d['candidate']['max_ideal_pool_touch_amplification']},indent=2))
if __name__=='__main__': main()
