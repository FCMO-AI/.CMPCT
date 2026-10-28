#!/usr/bin/env python3
"""A16-O1: preregistered hostile overlapping co-owner classes, science only."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path
import a16_o0_sharing_run_court as m

SEEDS=(20261030,20261031)

def run(outdir: Path):
    outdir.mkdir(parents=True,exist_ok=True)
    cases=[]
    for seed in SEEDS:
        rng=random.Random(seed)
        source=[bytearray() for _ in range(m.N)]
        for position in range(m.CHUNKS):
            pool=[rng.randbytes(m.BLOCK) for _ in range(4)]
            # Every position's four blocks are assigned to EXACTLY eight
            # independently chosen member owners apiece. Shared chunk identity
            # does not imply shared adjacency or owner-set intersection.
            assignments=[id for id in range(4) for _ in range(8)]
            rng.shuffle(assignments)
            for member in range(m.N):
                source[member].extend(pool[assignments[member]])
        source=[bytes(s) for s in source]
        blobs={};owners={};units={}
        for arm in ('direct','chunkref','segref'):
            envelope,counts,nowners=m.encode(source,arm)
            if m.independent_parse(envelope)!=source:
                raise AssertionError('exact member reconstruction failed')
            blobs[arm]=len(envelope);owners[arm]=nowners;units[arm]=counts
        if any(len(parts)!=1 for parts in m.owners(source,True)):
            raise AssertionError('predeclared all-shared-class property failed')
        ratio=blobs['segref']/blobs['chunkref']
        result={'seed':seed,
                'source_sha256':hashlib.sha256(b''.join(source)).hexdigest(),
                'complete_envelope_bytes':blobs,
                'physical_owner_counts':owners,
                'decoder_units_per_member':{a:[min(v),max(v)] for a,v in units.items()},
                'segref_over_fixed_chunkref':ratio,
                'fivefold_falsifier_fired':ratio>=5.0,
                'independently_decoded_members':m.N}
        cases.append(result)
        print(json.dumps(result,sort_keys=True),flush=True)
    receipt={'schema':'a16-o1-coowner-intersection-hostile-v1',
             'preregistration_commit':'6c0a5602dc00fc499f092f4a3f1b89ba534b1b17',
             'criterion_met':all(x['fivefold_falsifier_fired'] for x in cases),
             'cases':cases,
             'claim_level':'scientific exact-reconstruction hostile only; not CMPCT product'}
    (outdir/'a16_o1_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'criterion_met':receipt['criterion_met'],'cases':len(cases)}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
