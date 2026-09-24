from __future__ import annotations
"""Decompose the residual release-r24 byte debt after compact Deflate retention."""
import hashlib,json,tempfile
from pathlib import Path
from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from experiments import entropygraph_v030_release_product as PROMOTED
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_r24_dead_dictionary as DEAD_DICT
from experiments import v030_incremental_parity_falsifier as P

def _build(root:Path,out:Path,*,micro_max:int,medium_binary:bool,micro_target:int|None=None)->dict:
    b=BASE.C.Builder(root,deflate_reuse_min=65536); b.micro_pack_max_file=micro_max
    regular,largest=BASE._regular_user_shape(root)
    if micro_target is not None:b.micro_pack_target=micro_target
    elif largest>0:b.micro_pack_target=min(BASE.R24_RELEASE_PACK_CAP_BYTES,8*largest)
    pw=getattr(BASE._R24_CDC_POLICY,'wide_single_file',False);pm=getattr(BASE._R24_CDC_POLICY,'medium_binary_pack',False)
    BASE._R24_CDC_POLICY.wide_single_file=(regular==1 and largest>=BASE.R24_RELEASE_WIDE_CHUNK_BYTES);BASE._R24_CDC_POLICY.medium_binary_pack=medium_binary
    try:stats=dict(b.build(out))
    finally:BASE._R24_CDC_POLICY.wide_single_file=pw;BASE._R24_CDC_POLICY.medium_binary_pack=pm
    before=out.stat().st_size;elision=dict(DEAD_DICT.elide_dead_dictionary_in_place(out));after=out.stat().st_size
    return {**stats,"archive_bytes_before_elision":before,"archive_bytes":after,"dead_dictionary_elision":elision,"micro_pack_max_file":micro_max,"micro_pack_target":b.micro_pack_target,"medium_binary_pack":medium_binary}

def _row(name,root,out,**kw):
    stats=_build(root,out,**kw)
    if not PROMOTED.strong_verify(out).get('ok'):raise RuntimeError(f'{name} verification failed')
    return {"name":name,"archive_bytes":out.stat().st_size,"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"stats":stats,"vzip_locality":P._vzip_locality(out)}

def main():
    REPAIR.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-release-policy-decomp-') as raw:
        td=Path(raw);corpus=td/'corpus';corpus.mkdir();N.corpus_backups(corpus);root=corpus/'06_incremental_backups';REPAIR.normalize_workload(root)
        ident=P._tree_identity(root);expected=(P.EXPECTED_TREE_SHA256,P.EXPECTED_FILES,P.EXPECTED_LOGICAL_BYTES)
        if ident!=expected:raise RuntimeError(f'substrate identity mismatch: {ident!r}')
        genuine=td/'genuine.cmpct';P._genuine(root,genuine)
        if not PROMOTED.strong_verify(genuine).get('ok'):raise RuntimeError('genuine verification failed')
        floor=genuine.stat().st_size
        rows=[
            _row('release_compact',root,td/'release.cmpct',micro_max=256*1024,medium_binary=True),
            _row('default_micro_max_only',root,td/'micro-default.cmpct',micro_max=32*1024,medium_binary=True),
            _row('disable_medium_binary_only',root,td/'medium-off.cmpct',micro_max=256*1024,medium_binary=False),
            _row('mature_micro_and_medium_defaults',root,td/'both-default.cmpct',micro_max=32*1024,medium_binary=False),
            _row('all_mature_pack_defaults',root,td/'all-default.cmpct',micro_max=32*1024,medium_binary=False,micro_target=256*1024),
        ]
        for r in rows:r['delta_vs_r24_bytes']=r['archive_bytes']-floor
        best=min(rows,key=lambda r:r['archive_bytes'])
        print(json.dumps({"schema":"cmpct-v030-release-policy-decomposition-v2","source_tree":{"sha256":ident[0],"files":ident[1],"logical_bytes":ident[2]},"genuine_r24_bytes":floor,"rows":rows,"best_arm":best['name'],"best_delta_vs_r24_bytes":best['delta_vs_r24_bytes'],"decision":"RESIDUAL_POLICY_OWNER_LOCALIZED" if best['delta_vs_r24_bytes']<=0 else "RESIDUAL_POLICY_DEBT_REMAINS_COMPOSITE","promotion_credit":False},indent=2,sort_keys=True))
if __name__=='__main__':main()
