#!/usr/bin/env python3
"""Independent full-array oracle for O0 sparse logical Merkle research.

This standalone control deliberately materializes small complete files and
does not reuse the candidate's sparse leaf construction algorithm.
"""
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

candidate=Path(__file__).resolve().with_name('v031_sparse_merkle_proof_economics_o0.py')
spec=importlib.util.spec_from_file_location('sparse_commitment_candidate',candidate)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)
h=lambda x:hashlib.sha256(x).digest()

def reference_root(full,leaf):
    nodes=[h(b'L'+len(full[i:i+leaf]).to_bytes(4,'big')+bytes(full[i:i+leaf]))
           for i in range(0,len(full),leaf)] or [h(b'P:missing')]
    while len(nodes)>1:
        nodes=[h(b'N'+nodes[i]+(nodes[i+1] if i+1<len(nodes) else h(b'P:missing')))
               for i in range(0,len(nodes),2)]
    return h(b'F'+len(full).to_bytes(8,'big')+leaf.to_bytes(4,'big')+nodes[0])

def main():
    rng=random.Random(20261023)
    checks=0
    sizes=[0,1,2,127,128,4096,4097,65535,65536,65537,131071,131072,131073,200001]
    for trial in range(320):
        size=sizes[trial%len(sizes)] if trial<len(sizes)*4 else rng.randrange(0,250000)
        full=bytearray(size)
        extents=[]
        occupied=bytearray(size)
        for _ in range(rng.randrange(0,8)):
            if not size: break
            start=rng.randrange(0,size)
            length=min(size-start,rng.randrange(1,4000))
            if any(occupied[start:start+length]): continue
            payload=bytes(rng.randrange(1,256) for _ in range(length))
            full[start:start+length]=payload
            occupied[start:start+length]=b'\x01'*length
            extents.append(mod.Extent(start,payload))
        for leaf in (4096,65536):
            c=mod.sparse_commitment(size,extents,leaf)
            assert mod.original_flat_sha(size,extents)==hashlib.sha256(full).hexdigest()
            assert c.root==reference_root(full,leaf)
            assert mod.check_compact_index(c,c.nonzero_leaf_hashes,c.root)
            for j in ({0,len(c.levels[0])-1} if size else set()):
                raw=bytes(full[j*leaf:(j+1)*leaf])
                proof=mod.proof_for(c,j)
                assert mod.validate_leaf(c,j,raw,proof)
                altered=bytearray(raw)
                altered[-1]^=1
                assert not mod.validate_leaf(c,j,altered,proof)
                if proof:
                    bad=proof.copy()
                    bad[-1]=bytes(32)
                    assert not mod.validate_leaf(c,j,raw,bad)
            checks+=1
    print(json.dumps({'status':'PASS','case_count':320,
                      'leaf_configurations_per_case':2,
                      'reference_differentials':checks,
                      'scope':'independent full-array reference; not CMPCT product'}))

if __name__=='__main__':
    main()
