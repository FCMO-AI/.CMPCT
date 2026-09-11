from __future__ import annotations

"""Exact Office ZIP-stream federation density falsifier.

This research wrapper removes only byte-identical compressed member streams that occur in multiple
ZIP-family packages (DOCX/XLSX/PPTX), stores one authenticated shared copy, and stores exact package
literal segments plus references. It does not use semantic similarity, mode-2 regeneration, path-based
benchmark dispatch, or a new shipping opcode. Reconstruction must reproduce every original package
byte-for-byte and the complete Office tree hash.

The wrapper is deliberately simple so density economics are causal. Selective I/O/recovery/native
promotion is separate debt if the exact-federation seed is positive.
"""

import argparse, hashlib, json, os, shutil, struct, time, zipfile
from collections import defaultdict
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA='cmpct-v030-r4-office-exact-stream-federation-v1'
MAGIC=b'R4OSF1\0\0'
ZIP_SUFFIXES={'.docx','.xlsx','.pptx','.zip'}
LFH_FIXED=30
ACCEPTED_V029_OFFICE=5_954_026  # frozen accepted authority used by the current deficit map


def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def stream_range(blob:bytes, info:zipfile.ZipInfo)->tuple[int,int]:
    nl,xl=struct.unpack_from('<HH',blob,info.header_offset+26); s=info.header_offset+LFH_FIXED+nl+xl; return s,s+info.compress_size

def statrec(p:Path)->dict:
    st=p.stat(); return {'mode':int(st.st_mode&0o7777),'mtime_ns':int(st.st_mtime_ns)}

def discover(root:Path)->tuple[dict,dict]:
    occur=defaultdict(list); containers={}
    for p in sorted(q for q in root.rglob('*') if q.is_file() and q.suffix.lower() in ZIP_SUFFIXES):
        blob=p.read_bytes(); recs=[]
        with zipfile.ZipFile(p,'r') as zf:
            for info in zf.infolist():
                if info.is_dir(): continue
                s,e=stream_range(blob,info); st=blob[s:e]; h=sha(st); rec={'member':info.filename,'start':s,'end':e,'hash':h,'bytes':len(st)}; recs.append(rec); occur[h].append((p,rec,st))
        containers[p]={'blob':blob,'members':recs}
    shared={h:xs[0][2] for h,xs in occur.items() if len(xs)>=2 and len(xs[0][2])>0}
    return containers,shared

def encode_template(blob:bytes,recs:list[dict],shared:set[str])->dict:
    targets=sorted((r for r in recs if r['hash'] in shared),key=lambda r:r['start'])
    pieces=[]; pos=0
    for r in targets:
        if r['start']<pos: raise RuntimeError('overlapping ZIP stream ranges')
        if r['start']>pos: pieces.append({'literal':blob[pos:r['start']].hex()})
        pieces.append({'stream':r['hash']})
        pos=r['end']
    if pos<len(blob): pieces.append({'literal':blob[pos:].hex()})
    return {'size':len(blob),'pieces':pieces}

def decode_template(t:dict,shared:dict[str,bytes])->bytes:
    out=bytearray()
    for x in t['pieces']:
        if 'literal' in x: out.extend(bytes.fromhex(x['literal']))
        else: out.extend(shared[x['stream']])
    if len(out)!=t['size']: raise RuntimeError('template size mismatch')
    return bytes(out)

def build_candidate(root:Path,out:Path,work:Path)->dict:
    containers,shared=discover(root); ifiles=set(containers)
    if not shared: raise RuntimeError('no repeated exact streams')
    stripped=work/'stripped'; shutil.copytree(root,stripped)
    meta={}
    for p in ifiles:
        rel=p.relative_to(root); meta[rel.as_posix()]=statrec(p); (stripped/rel).unlink()
    base=work/'base.cmpct'; PRODUCT.build(stripped,base)
    templates={p.relative_to(root).as_posix():encode_template(v['blob'],v['members'],set(shared)) for p,v in containers.items()}
    pool=bytearray(); index={}
    for h,b in sorted(shared.items()): index[h]={'offset':len(pool),'bytes':len(b)}; pool.extend(b)
    manifest={'schema':'cmpct-v030-r4-office-stream-federation-bundle-v1','templates':templates,'stream_index':index,'metadata':meta}
    out.mkdir(parents=True,exist_ok=False); shutil.copy2(base,out/'base.cmpct'); (out/'streams.bin').write_bytes(pool)
    mraw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode(); (out/'manifest.json').write_bytes(mraw)
    auth=MAGIC+hashlib.sha256((out/'base.cmpct').read_bytes()).digest()+hashlib.sha256(bytes(pool)).digest()+hashlib.sha256(mraw).digest(); (out/'auth.bin').write_bytes(auth)
    sizes={p.name:p.stat().st_size for p in out.iterdir() if p.is_file()}
    duplicate_stream_bytes=sum(r['bytes'] for v in containers.values() for r in v['members'] if r['hash'] in shared)
    unique_shared_bytes=sum(len(b) for b in shared.values())
    return {'stored_bytes':sum(sizes.values()),'component_bytes':sizes,'shared_stream_count':len(shared),'shared_stream_bytes':unique_shared_bytes,'all_duplicate_occurrence_bytes':duplicate_stream_bytes,'raw_duplicate_stream_saving_before_metadata':duplicate_stream_bytes-unique_shared_bytes,'container_count':len(containers)}

def extract_candidate(bundle:Path,out:Path)->dict:
    mraw=(bundle/'manifest.json').read_bytes(); m=json.loads(mraw); pool=(bundle/'streams.bin').read_bytes(); base=(bundle/'base.cmpct').read_bytes()
    expected=MAGIC+hashlib.sha256(base).digest()+hashlib.sha256(pool).digest()+hashlib.sha256(mraw).digest()
    if (bundle/'auth.bin').read_bytes()!=expected: raise RuntimeError('auth mismatch')
    PRODUCT.extract(bundle/'base.cmpct',out); shared={h:pool[x['offset']:x['offset']+x['bytes']] for h,x in m['stream_index'].items()}
    for rel,t in m['templates'].items():
        b=decode_template(t,shared); p=out/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b); md=m['metadata'][rel]; os.chmod(p,int(md['mode'])); os.utime(p,ns=(int(md['mtime_ns']),int(md['mtime_ns'])))
    return {'tree_sha256':PRODUCT.treehash(out),'base_strong_verify':dict(PRODUCT.strong_verify(bundle/'base.cmpct'))}

def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_office_sf_neutral'); repair=V029._load(V029.REPAIR_PATH,'r4_office_sf_repair'); repair.install_generation_hooks(neutral)
    corpus=work/'neutral'; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/'02_office_workspace'; expected=PRODUCT.treehash(source)
    base=work/'baseline.cmpct'; w=time.perf_counter(); PRODUCT.build(source,base); base_wall=time.perf_counter()-w
    cand=work/'candidate'; w=time.perf_counter(); cs=build_candidate(source,cand,work/'cand-work'); cand_wall=time.perf_counter()-w
    v=extract_candidate(cand,work/'extract')
    if v['tree_sha256']!=expected: raise RuntimeError('tree mismatch')
    return {'schema':SCHEMA,'tree_sha256':expected,'baseline_v030_bytes':base.stat().st_size,'candidate_bytes':cs['stored_bytes'],'accepted_v029_office_bytes':ACCEPTED_V029_OFFICE,'saving_vs_v030_bytes':base.stat().st_size-cs['stored_bytes'],'margin_vs_v029_bytes':ACCEPTED_V029_OFFICE-cs['stored_bytes'],'baseline_create_wall_s':base_wall,'candidate_create_wall_s':cand_wall,'candidate':cs,'verify':v,'hypothesis':{'exact_stream_federation_beats_v030':cs['stored_bytes']<base.stat().st_size,'exact_stream_federation_beats_v029':cs['stored_bytes']<ACCEPTED_V029_OFFICE},'contract':{'diagnostic_only':True,'release_credit':False,'exact_compressed_stream_identity_only':True,'same_semantic_tree_verified':True,'no_mode2_regeneration':True,'no_locality_claim':True,'no_threshold_sweep':True},'next_if_supported':'add indexed physical selective-read and recovery accounting, then combine only evidence-backed Office and Analytics owners in a full matrix','next_if_falsified':'preserve exact-duplicate inventory; do not add resemblance search until the exact opportunity economics are understood'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-sf-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-sf.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps({k:d[k] for k in ('baseline_v030_bytes','candidate_bytes','accepted_v029_office_bytes','saving_vs_v030_bytes','margin_vs_v029_bytes','baseline_create_wall_s','candidate_create_wall_s','hypothesis')}|{'candidate_components':d['candidate']['component_bytes'],'shared_stream_count':d['candidate']['shared_stream_count'],'raw_duplicate_stream_saving_before_metadata':d['candidate']['raw_duplicate_stream_saving_before_metadata']},indent=2))
if __name__=='__main__': main()
