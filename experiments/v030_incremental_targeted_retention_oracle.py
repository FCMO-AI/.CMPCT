from __future__ import annotations

"""Prospectively retain exact streams only when compact policy would make their raw candidate use Zstd-dict."""
import json, tempfile
from pathlib import Path
from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from cmpct.codec import CODEC_ZSTDDICT
from experiments import entropygraph_v030_release_product as PROMOTED
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_r24_dead_dictionary as DEAD_DICT
from experiments import v030_incremental_parity_falsifier as P


class _TargetedRetentionBuilder(BASE.C.Builder):
    """Use facts available inside one ordinary build; no prior archive/result is consulted."""
    def __init__(self, root: Path):
        super().__init__(root, deflate_reuse_min=65536)
        self.targeted_retention_applied=set()

    def _train_dictionary(self):
        # Compact Deflate admission runs first in Builder.build(). After dictionary training, the encoder can
        # prospectively identify raw candidates that would keep the dictionary physically live. For those candidates
        # only, retain the already-known exact Deflate stream instead. This changes no reader grammar and does not
        # inspect paths, benchmark identity or a previously built archive.
        super()._train_dictionary()
        if not self.dictionary: return
        for rh,cand in sorted(self.cands.items()):
            if not cand.deflates or rh in self.canonical_deflate: continue
            codec,_comp,_meta=self._encode_candidate(rh,cand)
            if int(codec)!=CODEC_ZSTDDICT: continue
            chosen_hash,_slot=max(cand.deflates.items(),key=lambda kv:(kv[1][1],-len(kv[1][0])))
            self.canonical_deflate[rh]=chosen_hash
            self.targeted_retention_applied.add(rh)


def _targeted_release(root: Path, out: Path) -> dict:
    b=_TargetedRetentionBuilder(root); b.micro_pack_max_file=BASE.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular,largest=BASE._regular_user_shape(root)
    if largest>0:b.micro_pack_target=min(BASE.R24_RELEASE_PACK_CAP_BYTES,8*largest)
    pw=getattr(BASE._R24_CDC_POLICY,'wide_single_file',False); pm=getattr(BASE._R24_CDC_POLICY,'medium_binary_pack',False)
    BASE._R24_CDC_POLICY.wide_single_file=(regular==1 and largest>=BASE.R24_RELEASE_WIDE_CHUNK_BYTES); BASE._R24_CDC_POLICY.medium_binary_pack=True
    try: stats=dict(b.build(out))
    finally: BASE._R24_CDC_POLICY.wide_single_file=pw; BASE._R24_CDC_POLICY.medium_binary_pack=pm
    before=out.stat().st_size; elision=dict(DEAD_DICT.elide_dead_dictionary_in_place(out)); after=out.stat().st_size
    return {**stats,"targeted_retention_applied":len(b.targeted_retention_applied),"dead_dictionary_elision":elision,"archive_bytes_before_elision":before,"archive_bytes":after,"format_revision":24}


def main():
    REPAIR.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-targeted-retention-') as raw:
        td=Path(raw); corpus=td/'corpus'; corpus.mkdir(); N.corpus_backups(corpus); root=corpus/'06_incremental_backups'; REPAIR.normalize_workload(root)
        ident=P._tree_identity(root); expected=(P.EXPECTED_TREE_SHA256,P.EXPECTED_FILES,P.EXPECTED_LOGICAL_BYTES)
        if ident!=expected: raise RuntimeError(f'substrate identity mismatch: {ident!r}')

        genuine=td/'genuine.cmpct'; P._genuine(root,genuine)
        if not PROMOTED.strong_verify(genuine).get('ok'): raise RuntimeError('genuine r24 failed verification')
        genuine_bytes=genuine.stat().st_size

        compact=td/'compact.cmpct'; P._release_policy(root,compact,65536,True)
        if not PROMOTED.strong_verify(compact).get('ok'): raise RuntimeError('compact control failed verification')

        targeted=td/'targeted.cmpct'; targeted_stats=_targeted_release(root,targeted)
        if not PROMOTED.strong_verify(targeted).get('ok'): raise RuntimeError('targeted candidate failed verification')
        locality=P._vzip_locality(targeted); target_bytes=targeted.stat().st_size
        byte_floor=target_bytes<=genuine_bytes; locality_green=bool(locality['within_8x'])
        decision=('TARGETED_RETENTION_EARNS_ONE_PRODUCT_ATTEMPT' if byte_floor and locality_green else 'TARGETED_RETENTION_RETIRED')
        print(json.dumps({
            "schema":"cmpct-v030-incremental-targeted-retention-v2",
            "oracle_kind":"prospective-single-build-policy",
            "source_tree":{"sha256":ident[0],"files":ident[1],"logical_bytes":ident[2]},
            "genuine_r24_bytes":genuine_bytes,
            "compact_control_bytes":compact.stat().st_size,
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
