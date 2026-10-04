from __future__ import annotations

"""Fused-encode rehabilitation for the exact independent/pathdict portfolio.

The shared-scan referee showed that removing repeated filesystem discovery recovers
only ~1% of the two-build creation cost and leaves confirmed creation debt on every
first-gate workload.  The dominant duplicated work is therefore ordinary candidate
encoding.

Hypothesis: while building the exact independent contender, cache each candidate's
best non-dictionary physical encoding.  The path-blind dictionary contender can
reuse that exact evidence and pay only its dictionary audition plus its own metadata
publication.  One scanned candidate graph is reused.  The fused pathdict artifact
must be byte-identical to a clean PathBlindDictionaryBuilder artifact.  No codec
level, threshold, format, locality law, path signal, comparator, or Genesis score is
changed.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import time
import types

import msgpack

from cmpct.builder import Candidate
from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT, zcd
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks import v030_r24_micropack_content_selective_read_referee as SEL
from benchmarks.v030_r24_pathblind_dictionary_referee import PathBlindDictionaryBuilder


class RecordingIndependentBuilder(SAME.NoMicroPackBuilder):
    """Exact ordinary independent builder that also retains reusable no-dict encodes."""
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self._normal_encode_cache={}

    def _encode_candidate(self,h,c):
        # Compute the dictionary-independent candidate once.  This is the expensive
        # evidence the second contender currently recomputes.
        dictionary=self.dictionary
        self.dictionary=b''
        try:
            normal=super()._encode_candidate(h,c)
        finally:
            self.dictionary=dictionary
        self._normal_encode_cache[h]=normal
        if self.dict_hash is not None and h==self.dict_hash:
            return CODEC_RAW,c.raw,b''
        # Reproduce the inherited Builder's mature extension-hinted dictionary
        # audition exactly so this contender stays byte-identical to independent.
        codec,comp,meta=normal
        if dictionary and any(hint.lower().endswith(BASE.BUILDER.TEXT_EXT) for hint in c.hints):
            dc=zcd(c.raw,dictionary,12); dm=msgpack.packb([12],use_bin_type=True)
            if len(dc)+len(dm)<len(comp)+len(meta):
                return CODEC_ZSTDDICT,dc,dm
        return codec,comp,meta


class FusedPathBlindDictionaryBuilder(PathBlindDictionaryBuilder):
    def __init__(self,*a,normal_encode_cache=None,**kw):
        super().__init__(*a,**kw)
        self._fused_normal_encode_cache=normal_encode_cache or {}
        self._fused_hits=0; self._fused_misses=0

    def _encode_candidate(self,h,c):
        if self.dict_hash is not None and h==self.dict_hash:
            return CODEC_RAW,c.raw,b''
        normal=self._fused_normal_encode_cache.get(h)
        if normal is None:
            self._fused_misses+=1
            dictionary=self.dictionary; self.dictionary=b''
            try: normal=super(PathBlindDictionaryBuilder,self)._encode_candidate(h,c)
            finally: self.dictionary=dictionary
        else:
            self._fused_hits+=1
        codec,comp,meta=normal
        if self.dictionary and h in getattr(self,'_pathblind_dict_hashes',set()):
            dc=zcd(c.raw,self.dictionary,12); dm=msgpack.packb([12],use_bin_type=True)
            if len(dc)+len(dm)<len(comp)+len(meta):
                return CODEC_ZSTDDICT,dc,dm
        return codec,comp,meta


def _snapshot(seed):
    return {
        'cands':{h:Candidate(c.raw,set(c.hints),{sh:[slot[0],slot[1]] for sh,slot in c.deflates.items()}) for h,c in seed.cands.items()},
        'files':copy.deepcopy(seed.files),'recipes':copy.deepcopy(seed.recipes),
        'dictionary':b'','dict_hash':None,'canonical_deflate':dict(seed.canonical_deflate),
        'secondary_stream_hashes':set(seed.secondary_stream_hashes),'inode_first':dict(seed.inode_first),
        'meta_by_rel':copy.deepcopy(seed.meta_by_rel),
    }


def _build_obj(b,out):
    out.parent.mkdir(parents=True,exist_ok=True)
    c0=time.process_time();w0=time.perf_counter();b.build(out);cpu=time.process_time()-c0;wall=time.perf_counter()-w0
    v=BASE.PRODUCT.strong_verify(out)
    if not v.get('ok'):raise RuntimeError('strong verify failed')
    return {'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'cpu_s':cpu,'wall_s':wall}


def _new(cls,source):
    b=cls(source,deflate_reuse_min=0,workers=1);b.micro_pack_max_file=int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES);return b


def _one(source,root):
    root.mkdir(parents=True,exist_ok=True)
    # Clean controls.
    clean_i=_build_obj(_new(SAME.NoMicroPackBuilder,source),root/'clean-independent.cmpct')
    clean_d=_build_obj(_new(PathBlindDictionaryBuilder,source),root/'clean-dictionary.cmpct')

    # Fused route. One scan is charged explicitly, then the independent build skips
    # scan and records ordinary encodes. The pathdict build reuses both graph+encodes.
    rec=_new(RecordingIndependentBuilder,source)
    c0=time.process_time();w0=time.perf_counter();rec.scan();scan_cpu=time.process_time()-c0;scan_wall=time.perf_counter()-w0
    rec.scan=types.MethodType(lambda self:None,rec)
    rec_build=_build_obj(rec,root/'fused-independent.cmpct')

    c0=time.process_time();w0=time.perf_counter();state=_snapshot(rec);clone_cpu=time.process_time()-c0;clone_wall=time.perf_counter()-w0
    fused=_new(FusedPathBlindDictionaryBuilder,source)
    for k,v in state.items():setattr(fused,k,v)
    fused._fused_normal_encode_cache=rec._normal_encode_cache
    fused.scan=types.MethodType(lambda self:None,fused)
    fused_build=_build_obj(fused,root/'fused-dictionary.cmpct')

    fused_cpu=scan_cpu+rec_build['cpu_s']+clone_cpu+fused_build['cpu_s']
    fused_wall=scan_wall+rec_build['wall_s']+clone_wall+fused_build['wall_s']
    clean_port_cpu=clean_i['cpu_s']+clean_d['cpu_s'];clean_port_wall=clean_i['wall_s']+clean_d['wall_s']
    identity={
        'independent_exact':clean_i['sha256']==rec_build['sha256'] and clean_i['bytes']==rec_build['bytes'],
        'dictionary_exact':clean_d['sha256']==fused_build['sha256'] and clean_d['bytes']==fused_build['bytes'],
    }
    return {
        'clean':{'independent':clean_i,'dictionary':clean_d,'portfolio_cpu_s':clean_port_cpu,'portfolio_wall_s':clean_port_wall},
        'fused':{'scan_cpu_s':scan_cpu,'scan_wall_s':scan_wall,'independent':rec_build,'clone_cpu_s':clone_cpu,'clone_wall_s':clone_wall,'dictionary':fused_build,'portfolio_cpu_s':fused_cpu,'portfolio_wall_s':fused_wall,'cache_hits':fused._fused_hits,'cache_misses':fused._fused_misses,'cache_entries':len(rec._normal_encode_cache)},
        'identity':identity,'identity_pass':all(identity.values()),
        'cpu_ratio_vs_clean_portfolio':fused_cpu/clean_port_cpu if clean_port_cpu else None,
        'wall_ratio_vs_clean_portfolio':fused_wall/clean_port_wall if clean_port_wall else None,
        'cpu_ratio_vs_single_independent':fused_cpu/clean_i['cpu_s'] if clean_i['cpu_s'] else None,
        'wall_ratio_vs_single_independent':fused_wall/clean_i['wall_s'] if clean_i['wall_s'] else None,
        'remaining_cpu_debt':SEL._confirmed_regression({'median_read_wall_s':fused_cpu},{'median_read_wall_s':clean_i['cpu_s']}),
        'remaining_wall_debt':SEL._confirmed_regression({'median_read_wall_s':fused_wall},{'median_read_wall_s':clean_i['wall_s']}),
    }


def run(work_root):
    shutil.rmtree(work_root,ignore_errors=True)
    paths,ids=CUR._build(work_root/'corpus');fp=CUR._fingerprint(ids)
    targets={'neutral_hostile_v1/01_developer_repository','neutral_hostile_v1/08_many_tiny_files','neutral_hostile_v1/07_incompressible_and_encrypted_like','resemblance_hostile_v1/02_false_neighbors','resemblance_hostile_v1/05_incompressible'}
    rows={k:_one(paths[k],work_root/'work'/k.replace('/','__')) for k in sorted(targets)}
    bad=[k for k,r in rows.items() if not r['identity_pass']]
    cpu_debt=[k for k,r in rows.items() if r['remaining_cpu_debt']['confirmed_regression']]
    wall_debt=[k for k,r in rows.items() if r['remaining_wall_debt']['confirmed_regression']]
    agg={q:sum(r['fused'][q] if q in r['fused'] else 0 for r in rows.values()) for q in ['scan_cpu_s','scan_wall_s','clone_cpu_s','clone_wall_s','cache_hits','cache_misses']}
    agg.update({
        'clean_portfolio_cpu_s':sum(r['clean']['portfolio_cpu_s'] for r in rows.values()),
        'clean_portfolio_wall_s':sum(r['clean']['portfolio_wall_s'] for r in rows.values()),
        'fused_portfolio_cpu_s':sum(r['fused']['portfolio_cpu_s'] for r in rows.values()),
        'fused_portfolio_wall_s':sum(r['fused']['portfolio_wall_s'] for r in rows.values()),
        'single_independent_cpu_s':sum(r['clean']['independent']['cpu_s'] for r in rows.values()),
        'single_independent_wall_s':sum(r['clean']['independent']['wall_s'] for r in rows.values()),
    })
    agg['cpu_ratio_vs_clean_portfolio']=agg['fused_portfolio_cpu_s']/agg['clean_portfolio_cpu_s'];agg['wall_ratio_vs_clean_portfolio']=agg['fused_portfolio_wall_s']/agg['clean_portfolio_wall_s']
    agg['cpu_ratio_vs_single_independent']=agg['fused_portfolio_cpu_s']/agg['single_independent_cpu_s'];agg['wall_ratio_vs_single_independent']=agg['fused_portfolio_wall_s']/agg['single_independent_wall_s']
    if bad:verdict='FUSED_ENCODE_INVALID'
    elif cpu_debt or wall_debt:verdict='FUSED_ENCODE_HELPS_BUT_CREATION_DEBT_REMAINS'
    else:verdict='FUSED_ENCODE_CLOSES_CREATION_DEBT'
    return {'schema':'cmpct-v030-r24-pathdict-fused-encode-v1','experiment_valid':not bad,'release_credit':False,'canonical_builder_changed':False,'genesis_rescore':False,'corpus_fingerprint':fp,'rows':rows,'identity_failures':bad,'remaining_cpu_debts':cpu_debt,'remaining_wall_debts':wall_debt,'aggregate':agg,'verdict':verdict}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-pathdict-fused-work'));ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-pathdict-fused.json'));a=ap.parse_args()
    d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':d['verdict'],'fingerprint':d['corpus_fingerprint'],'identity_failures':d['identity_failures'],'remaining_cpu':d['remaining_cpu_debts'],'remaining_wall':d['remaining_wall_debts'],'aggregate':d['aggregate'],'rows':{k:{'cpu_port_ratio':v['cpu_ratio_vs_clean_portfolio'],'wall_port_ratio':v['wall_ratio_vs_clean_portfolio'],'cpu_single_ratio':v['cpu_ratio_vs_single_independent'],'wall_single_ratio':v['wall_ratio_vs_single_independent'],'hits':v['fused']['cache_hits'],'misses':v['fused']['cache_misses']} for k,v in d['rows'].items()}},indent=2,sort_keys=True),flush=True)

if __name__=='__main__':main()
