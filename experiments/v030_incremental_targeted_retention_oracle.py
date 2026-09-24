from __future__ import annotations

"""Test whether exact-stream retention can be limited to candidates that otherwise keep the r24 dictionary live."""
import hashlib, json, tempfile
from pathlib import Path
from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from cmpct.codec import BHDR, CODEC_ZSTDDICT
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_release_product as PROMOTED
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_r24_dead_dictionary as DEAD_DICT
from experiments import v030_incremental_parity_falsifier as P


def _zdict_user_hashes(path: Path) -> set[bytes]:
    users=set()
    with CMPCT(path) as r:
        for off,_usize,_csize,codec,_ml in r.blobs:
            if int(codec)!=CODEC_ZSTDDICT: continue
            pos=r.record_base+int(off)
            users.add(bytes(BHDR.unpack_from(r.mm,pos)[-1]))
    return users


class _TargetedRetentionBuilder(BASE.C.Builder):
    def __init__(self, root: Path, force_hashes: set[bytes]):
        super().__init__(root, deflate_reuse_min=65536)
        self.force_hashes=set(force_hashes)
        self.forced_applied=set()

    def _prepare_deflate_reuse(self):
        super()._prepare_deflate_reuse()
        for rh in sorted(self.force_hashes):
            cand=self.cands.get(rh)
            if cand is None or not cand.deflates: continue
            chosen_hash,_slot=max(cand.deflates.items(),key=lambda kv:(kv[1][1],-len(kv[1][0])))
            self.canonical_deflate[rh]=chosen_hash
            self.forced_applied.add(rh)


def _targeted_release(root: Path, out: Path, force_hashes: set[bytes]) -> dict:
    b=_TargetedRetentionBuilder(root,force_hashes); b.micro_pack_max_file=BASE.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular,largest=BASE._regular_user_shape(root)
    if largest>0:b.micro_pack_target=min(BASE.R24_RELEASE_PACK_CAP_BYTES,8*largest)
    pw=getattr(BASE._R24_CDC_POLICY,'wide_single_file',False); pm=getattr(BASE._R24_CDC_POLICY,'medium_binary_pack',False)
    BASE._R24_CDC_POLICY.wide_single_file=(regular==1 and largest>=BASE.R24_RELEASE_WIDE_CHUNK_BYTES); BASE._R24_CDC_POLICY.medium_binary_pack=True
    try: stats=dict(b.build(out))
    finally: BASE._R24_CDC_POLICY.wide_single_file=pw; BASE._R24_CDC_POLICY.medium_binary_pack=pm
    before=out.stat().st_size; elision=dict(DEAD_DICT.elide_dead_dictionary_in_place(out)); after=out.stat().st_size
    return {**stats,"forced_requested":len(force_hashes),"forced_applied":len(b.forced_applied),"dead_dictionary_elision":elision,"archive_bytes_before_elision":before,"archive_bytes":after,"format_revision":24}


def main():
    REPAIR.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-targeted-retention-') as raw:
        td=Path(raw); corpus=td/'corpus'; corpus.mkdir(); N.corpus_backups(corpus); root=corpus/'06_incremental_backups'; REPAIR.normalize_workload(root)
        ident=P._tree_identity(root)
        expected=(P.EXPECTED_TREE_SHA256,P.EXPECTED_FILES,P.EXPECTED_LOGICAL_BYTES)
        if ident!=expected: raise RuntimeError(f'substrate identity mismatch: {ident!r}')

        genuine=td/'genuine.cmpct'; P._genuine(root,genuine)
        if not PROMOTED.strong_verify(genuine).get('ok'): raise RuntimeError('genuine r24 failed verification')
        genuine_bytes=genuine.stat().st_size

        compact=td/'compact.cmpct'; compact_stats=P._release_policy(root,compact,65536,False)
        if not PROMOTED.strong_verify(compact).get('ok'): raise RuntimeError('compact control failed verification')
        force=_zdict_user_hashes(compact)

        targeted=td/'targeted.cmpct'; targeted_stats=_targeted_release(root,targeted,force)
        if not PROMOTED.strong_verify(targeted).get('ok'): raise RuntimeError('targeted candidate failed verification')
        locality=P._vzip_locality(targeted)
        target_bytes=targeted.stat().st_size
        byte_floor=target_bytes<=genuine_bytes; locality_green=bool(locality['within_8x'])
        decision=('TARGETED_RETENTION_EARNS_ONE_PRODUCT_ATTEMPT' if byte_floor and locality_green else 'TARGETED_RETENTION_RETIRED')
        print(json.dumps({
            "schema":"cmpct-v030-incremental-targeted-retention-v1",
            "source_tree":{"sha256":ident[0],"files":ident[1],"logical_bytes":ident[2]},
            "genuine_r24_bytes":genuine_bytes,
            "compact_control_bytes":compact.stat().st_size,
            "compact_zdict_user_hashes":len(force),
            "targeted_archive_bytes":target_bytes,
            "targeted_delta_vs_r24_bytes":target_bytes-genuine_bytes,
            "targeted_stats":targeted_stats,
            "vzip_locality":locality,
            "byte_floor_green":byte_floor,
            "locality_8x_green":locality_green,
            "decision":decision,
            "promotion_credit":False,
        },indent=2,sort_keys=True))

if __name__=='__main__':main()
