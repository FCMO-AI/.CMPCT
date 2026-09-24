from __future__ import annotations

"""Localize the incremental-backups parity failure and charge the compact-retention counterfactual."""
import hashlib, json, tempfile, zipfile
from pathlib import Path
from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP
from experiments import entropygraph_v030_release_product as PROMOTED
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_r24_dead_dictionary as DEAD_DICT

EXPECTED_TREE_SHA256="a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"; EXPECTED_FILES=769; EXPECTED_LOGICAL_BYTES=14_006_619

def _tree_identity(root):
    h=hashlib.sha256(); files=logical=0
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        rel=p.relative_to(root).as_posix().encode(); raw=p.read_bytes(); h.update(len(rel).to_bytes(4,'little'));h.update(rel);h.update(len(raw).to_bytes(8,'little'));h.update(raw);files+=1;logical+=len(raw)
    return h.hexdigest(),files,logical

def _genuine(root,out): return {**dict(Builder(root).build(out)),"selected":"canonical-r24","format_revision":24}

def _release_policy(root,out,deflate_min,elide_dead_dictionary=False):
    b=BASE.C.Builder(root,deflate_reuse_min=deflate_min); b.micro_pack_max_file=BASE.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular,largest=BASE._regular_user_shape(root)
    if largest>0:b.micro_pack_target=min(BASE.R24_RELEASE_PACK_CAP_BYTES,8*largest)
    pw=getattr(BASE._R24_CDC_POLICY,'wide_single_file',False); pm=getattr(BASE._R24_CDC_POLICY,'medium_binary_pack',False)
    BASE._R24_CDC_POLICY.wide_single_file=(regular==1 and largest>=BASE.R24_RELEASE_WIDE_CHUNK_BYTES); BASE._R24_CDC_POLICY.medium_binary_pack=True
    try: stats=dict(b.build(out))
    finally: BASE._R24_CDC_POLICY.wide_single_file=pw; BASE._R24_CDC_POLICY.medium_binary_pack=pm
    elision={"reason":"not-requested","saving_bytes":0}
    if elide_dead_dictionary:
        before=out.stat().st_size; elision=dict(DEAD_DICT.elide_dead_dictionary_in_place(out)); after=out.stat().st_size
        if int(elision.get("saving_bytes",before-after)) != before-after: raise RuntimeError(f'dead-dictionary accounting mismatch: {elision!r}, before={before}, after={after}')
    return {**stats,"selected":f"release-r24-deflate-min-{deflate_min}"+("-dead-dict-elided" if elide_dead_dictionary else ""),"format_revision":24,"dead_dictionary_elision":elision}

def _vzip_locality(path):
    """Conservatively charge every blob materialized to reconstruct one selected virtual ZIP.

    Mode 0 reads an already-retained exact Deflate payload directly from its physical record and therefore adds no
    logical blob materialization. Modes 1/2 and STORED members call the reader's blob path; charge each referenced
    blob's full logical usize once, even when its physical codec is RAW. Skeleton materialization is charged too.
    This intentionally overcharges decoded context rather than granting locality from cache assumptions.
    """
    rows=[]
    with CMPCT(path) as r:
        for file_row in r.files:
            storage=file_row[6]
            if not storage or storage[0]!=S_VZIP: continue
            rid=int(storage[1]); recipe=r.recipes[rid]; skref,lens,payloads,_sha,vsize,_crc=recipe
            refs={int(skref)}
            modes={"mode0":0,"mode1":0,"mode2":0,"stored":0}
            for rawref,method,stream_mode,streamref,_csize,_level in payloads:
                if int(method)==zipfile.ZIP_STORED:
                    refs.add(int(rawref)); modes["stored"]+=1
                elif int(stream_mode)==0: modes["mode0"]+=1
                elif int(stream_mode)==1: refs.add(int(streamref)); modes["mode1"]+=1
                else: refs.add(int(rawref)); modes["mode2"]+=1
            decoded=sum(int(r.blobs[idx][1]) for idx in refs)
            rows.append({"path":file_row[0],"selected_bytes":int(vsize),"charged_blob_refs":len(refs),"charged_decoded_context_bytes":decoded,"decoded_context_amplification":decoded/max(1,int(vsize)),"payload_modes":modes})
    worst=max((x["decoded_context_amplification"] for x in rows),default=0.0)
    return {"contract":"conservative-full-materialized-blob-usize-v1","vzip_count":len(rows),"max_decoded_context_amplification":worst,"within_8x":worst<=8.0+1e-12,"rows":rows}

def _row(name,builder,root,out):
    s=dict(builder(root,out)); v=dict(PROMOTED.strong_verify(out))
    if not v.get('ok'): raise RuntimeError(f'{name} failed strong verification: {v!r}')
    return {"name":name,"archive_bytes":out.stat().st_size,"archive_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"selected":s.get('selected'),"format_revision":s.get('format_revision'),"r24_product_bytes":s.get('r24_product_bytes'),"r25_product_bytes":s.get('r25_product_bytes'),"dead_dictionary_elision":s.get('dead_dictionary_elision'),"vzip_locality":_vzip_locality(out)}

def main():
    REPAIR.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-inc-parity-') as raw:
        td=Path(raw); corpus=td/'corpus';corpus.mkdir();N.corpus_backups(corpus);root=corpus/'06_incremental_backups';REPAIR.normalize_workload(root)
        ident=_tree_identity(root)
        if ident!=(EXPECTED_TREE_SHA256,EXPECTED_FILES,EXPECTED_LOGICAL_BYTES):raise RuntimeError(f'substrate identity mismatch: {ident!r}')
        rows=[
            _row('promoted_frontdoor',PROMOTED.build,root,td/'promoted.cmpct'),
            _row('mature_base_frontdoor',BASE.build,root,td/'base.cmpct'),
            _row('genuine_r24',_genuine,root,td/'genuine.cmpct'),
            _row('release_policy_deflate_65536',lambda r,o:_release_policy(r,o,65536),root,td/'release-65536.cmpct'),
            _row('release_policy_deflate_65536_dead_dict_elided',lambda r,o:_release_policy(r,o,65536,True),root,td/'release-65536-elided.cmpct'),
            _row('release_policy_deflate_0',lambda r,o:_release_policy(r,o,0),root,td/'release-0.cmpct'),
            _row('deflate0_only',lambda r,o:{**dict(Builder(r,deflate_reuse_min=0).build(o)),"format_revision":24},root,td/'deflate0-only.cmpct'),
        ]
        genuine=next(x for x in rows if x['name']=='genuine_r24')['archive_bytes']
        for x in rows:x['delta_vs_r24_bytes']=x['archive_bytes']-genuine
        by_name={x['name']:x for x in rows}; compact=by_name['release_policy_deflate_65536_dead_dict_elided']; promoted=by_name['promoted_frontdoor']['delta_vs_r24_bytes']; base=by_name['mature_base_frontdoor']['delta_vs_r24_bytes']; release65536=by_name['release_policy_deflate_65536']['delta_vs_r24_bytes']; release0=by_name['release_policy_deflate_0']['delta_vs_r24_bytes']; deflate0=by_name['deflate0_only']['delta_vs_r24_bytes']
        byte_floor=compact['delta_vs_r24_bytes']<=0; locality=bool(compact['vzip_locality']['within_8x'])
        if byte_floor and locality: decision='COMPACT_RETENTION_RECOVERS_R24_FLOOR_AND_LOCALITY_ONE_PRODUCT_ATTEMPT_EARNED'
        elif byte_floor: decision='COMPACT_RETENTION_RECOVERS_R24_BYTE_FLOOR_BUT_FAILS_LOCALITY'
        elif promoted>0 and base>0 and release0==promoted:
            if release65536==0: decision='DEFLATE_RETENTION_POLICY_CAUSAL'
            elif deflate0==promoted: decision='DEFLATE_RETENTION_DOMINANT_CAUSAL'
            else: decision='RELEASE_R24_POLICY_COMPOSITE_CAUSAL'
        else: decision='RECONCILE_POLICY_DECOMPOSITION'
        print(json.dumps({"schema":"cmpct-v030-incremental-parity-falsifier-v5","source_tree":{"sha256":ident[0],"files":ident[1],"logical_bytes":ident[2]},"comparator_contract":"v030_release_ablation_canonical::_product_row ordinary Builder(root).build","rows":rows,"compact_retention":{"byte_floor_green":byte_floor,"locality_8x_green":locality},"decision":decision,"promotion_credit":False,"remaining_gate":("one product-path attempt with full release timing/selective evidence" if byte_floor and locality else "retire or redesign compact retention; do not change product policy")},indent=2,sort_keys=True))
if __name__=='__main__':main()
