from __future__ import annotations

"""Outcome attribution for path-blind dictionary auditions.

Mission lock
============
v7 shows that dictionary candidate encoding dominates the residual exact-portfolio
creation debt.  Before choosing between cheap admission and native/bulk acceleration,
measure whether successful dictionary substitutions are sparse or dense and where
candidate-level savings live.

Falsifiable hypothesis
----------------------
If only a small minority of path-blind auditions produce positive physical-byte
savings, a future content-derived admission proof may have leverage.  If winners are
common or savings are broadly distributed, skipping auditions is a poor target and
primitive-level acceleration should remain primary.  This referee does not change
which candidate wins: it records the exact normal and dictionary physical lengths
around the existing decision and preserves clean artifact identity as a hard gate.

Research-only.  No threshold, codec, dictionary, selector, corpus, locality rule,
format, canonical Builder, comparator, Genesis score, or release state changes.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

import msgpack

from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT, zcd
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import TimedFusedPathBlindDictionaryBuilder


class AuditedFusedDictionaryBuilder(TimedFusedPathBlindDictionaryBuilder):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self._auditions=[]

    def _encode_candidate(self,h,c):
        if self.dict_hash is not None and h==self.dict_hash:
            return CODEC_RAW,c.raw,b''
        normal=self._fused_normal_encode_cache.get(h)
        if normal is None:
            self._fused_misses+=1
            dictionary=self.dictionary; self.dictionary=b''
            try:
                normal=super(TimedFusedPathBlindDictionaryBuilder,self)._encode_candidate(h,c)
            finally:
                self.dictionary=dictionary
        else:
            self._fused_hits+=1
        if h in self.secondary_stream_hashes or h in self.canonical_deflate:
            return normal
        codec,comp,meta=normal
        dictionary=self.dictionary
        if dictionary and h in getattr(self,'_pathblind_dict_hashes',set()):
            c0=time.process_time();w0=time.perf_counter()
            dc=zcd(c.raw,dictionary,12)
            cpu=time.process_time()-c0;wall=time.perf_counter()-w0
            dm=msgpack.packb([12],use_bin_type=True)
            normal_bytes=len(comp)+len(meta);dict_bytes=len(dc)+len(dm)
            saving=normal_bytes-dict_bytes
            self._auditions.append({
                'raw_bytes':len(c.raw),'normal_bytes':normal_bytes,'dictionary_bytes':dict_bytes,
                'saving_bytes':saving,'winner':saving>0,'cpu_s':cpu,'wall_s':wall,
            })
            if saving>0:
                return CODEC_ZSTDDICT,dc,dm
        return codec,comp,meta


def _summarize(rows):
    n=len(rows);w=[r for r in rows if r['winner']]
    pos=sum(r['saving_bytes'] for r in w)
    neg=sum(-r['saving_bytes'] for r in rows if r['saving_bytes']<0)
    raw=sum(r['raw_bytes'] for r in rows)
    return {
        'auditions':n,'winners':len(w),'winner_fraction':len(w)/n if n else 0.0,
        'winner_savings_bytes':pos,'loser_excess_bytes':neg,
        'audition_raw_bytes':raw,'audition_cpu_s':sum(r['cpu_s'] for r in rows),
        'audition_wall_s':sum(r['wall_s'] for r in rows),
        'winner_raw_bytes':sum(r['raw_bytes'] for r in w),
        'winner_raw_fraction':sum(r['raw_bytes'] for r in w)/raw if raw else 0.0,
        'max_saving_bytes':max((r['saving_bytes'] for r in rows),default=0),
        'median_positive_saving_bytes': sorted([r['saving_bytes'] for r in w])[len(w)//2] if w else 0,
    }


def _one(source,root):
    root.mkdir(parents=True,exist_ok=True)
    clean_i=V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder,source),root/'clean-independent.cmpct')
    clean_d=V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder,source),root/'clean-dictionary.cmpct')
    seed=V1._new(V3.ScanSeedBuilder,source);seed.scan()
    rec=V3._clone_seed(seed,CanonicalRecordingIndependentBuilder,source)
    rec_build=V1._build_obj(rec,root/'fused-independent.cmpct')
    fused=V3._clone_seed(seed,AuditedFusedDictionaryBuilder,source)
    fused._fused_normal_encode_cache=rec._normal_encode_cache
    fused_build=V1._build_obj(fused,root/'fused-dictionary.cmpct')
    identity={
        'independent_exact':clean_i['sha256']==rec_build['sha256'] and clean_i['bytes']==rec_build['bytes'],
        'dictionary_exact':clean_d['sha256']==fused_build['sha256'] and clean_d['bytes']==fused_build['bytes'],
        'cache_miss_free':fused._fused_misses==0,
    }
    return {
        'clean_independent':clean_i,'clean_dictionary':clean_d,
        'artifact_delta_bytes':clean_d['bytes']-clean_i['bytes'],
        'identity':identity,'identity_pass':all(identity.values()),
        'outcomes':_summarize(fused._auditions),
    }


def run(work_root):
    shutil.rmtree(work_root,ignore_errors=True)
    paths,ids=V1.CUR._build(work_root/'corpus');fp=V1.CUR._fingerprint(ids)
    targets={
        'neutral_hostile_v1/01_developer_repository','neutral_hostile_v1/08_many_tiny_files',
        'neutral_hostile_v1/07_incompressible_and_encrypted_like','resemblance_hostile_v1/02_false_neighbors',
        'resemblance_hostile_v1/05_incompressible',
    }
    rows={k:_one(paths[k],work_root/'work'/k.replace('/','__')) for k in sorted(targets)}
    bad=[k for k,v in rows.items() if not v['identity_pass']]
    total_a=sum(v['outcomes']['auditions'] for v in rows.values())
    total_w=sum(v['outcomes']['winners'] for v in rows.values())
    agg={
        'auditions':total_a,'winners':total_w,'winner_fraction':total_w/total_a if total_a else 0.0,
        'winner_savings_bytes':sum(v['outcomes']['winner_savings_bytes'] for v in rows.values()),
        'audition_cpu_s':sum(v['outcomes']['audition_cpu_s'] for v in rows.values()),
        'audition_wall_s':sum(v['outcomes']['audition_wall_s'] for v in rows.values()),
        'winning_workloads':sum(v['artifact_delta_bytes']<0 for v in rows.values()),
        'losing_workloads':sum(v['artifact_delta_bytes']>0 for v in rows.values()),
    }
    return {
        'schema':'cmpct-v030-r24-pathdict-audition-outcome-v1','experiment_valid':not bad,
        'release_credit':False,'canonical_builder_changed':False,'genesis_rescore':False,
        'corpus_fingerprint':fp,'identity_failures':bad,'rows':rows,'aggregate':agg,
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-pathdict-outcome-work'));ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-pathdict-outcome.json'));a=ap.parse_args()
    d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'identity_failures':d['identity_failures'],'aggregate':d['aggregate'],'rows':{k:{'artifact_delta_bytes':v['artifact_delta_bytes'],'outcomes':v['outcomes']} for k,v in d['rows'].items()}},indent=2,sort_keys=True),flush=True)

if __name__=='__main__':main()
