"""ONE-G0.2 shared-authentication family creation amortization A/B.

Referee freeze before result-bearing execution
==============================================
Prior native evidence showed an 80-byte basis AuthTree costs about 4.85-5.07x ONE whole-file
SHA when compared to ONE root.  That denominator is useful for finding work, but the structural
win being rehabilitated is a shared temporal family: one basis plus eight edited roots.  The
independent-literal comparator must authenticate all nine roots to provide the same whole-root
integrity semantics.

This experiment isolates AUTHENTICATION SETUP cost after representation discovery is complete.
It therefore receives the basis, edited roots and already-derived Surprise blobs.  It compares:
A) nine independent whole-root SHA-256 commitments; versus
B) one 80-byte fine-grained basis AuthTree plus one packed-q4-compatible descriptor tree for the
   eight derived roots.  The q4 build includes Surprise hashing and descriptor leaf/parent hashes.
No discovery, wire encoding or compression search time is included in either candidate.

Frozen V=8 gate on 64 KiB and 256 KiB, three independent families each:
- all independent root digests and shared basis/q4 roots must be deterministic;
- hosted shared-auth setup median elapsed <=0.80x independent nine-root hashing on every row;
- deterministic bytes presented to SHA by the shared authentication grammar <=0.40x the bytes
  hashed by nine independent literal roots on every row.
If hosted timing fails while deterministic SHA bytes pass, retain amortization as structural
compute evidence but keep implementation debt explicit.  Thresholds/corpus/leaf may not change.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import random
import time
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, MUTATIONS
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import _desc_control
from benchmarks.one.one_g02_descriptor_auth_quaternary_ab import _build as _build_q
from experiments.one.auth_tree import build_auth_tree

LEAF=80
COUNT=8
FAMILIES_PER_ROOT=3
REPETITIONS=15
INNER=18
MAX_ELAPSED_RATIO=0.80
MAX_SHA_INPUT_RATIO=0.40

# Exact domain lengths from experiments/one/auth_tree.py and q4 descriptor grammar are measured
# by deterministic formulas below; this is causal accounting, not a wall-clock surrogate.
LEAF_DOMAIN_LEN=len(b"ONE-AUTH-LEAF\0")
PARENT_DOMAIN_LEN=len(b"ONE-AUTH-PARENT\0")
ROOT_DOMAIN_LEN=len(b"ONE-AUTH-ROOT\0")
DESC_LEAF_DOMAIN_LEN=len(b"ONE-GDESC-L\0")
DESC_PARENT_DOMAIN_LEN=len(b"ONE-GDESC-QP\0")


def _families():
    master=random.Random(MASTER_SEED^0xA071FA11)
    for size in ROOT_SIZES:
        for base_index in range(FAMILIES_PER_ROOT):
            seed=master.getrandbits(64); base=random.Random(seed).randbytes(size)
            edited=[]; blobs=[]
            for m in MUTATIONS[:COUNT]:
                e=_edited(base,random.Random(seed^(m<<32)^0xA11CE5EED),m)
                blob,_=_surprise_blob(base,e); edited.append(e); blobs.append(blob)
            yield size,base_index,base,edited,blobs


def _basis_sha_input_bytes(size:int)->int:
    # build_auth_tree leaf grammar: domain + <Q offset> + complete leaf bytes.
    leaves=(size+LEAF-1)//LEAF
    total=leaves*(LEAF_DOMAIN_LEN+8)+size
    width=leaves; level=1
    while width>1:
        parents=(width+1)//2
        # binary parent hashes domain + u32 level + two child digests; odd duplicates left.
        total+=parents*(PARENT_DOMAIN_LEN+4+64)
        width=parents; level+=1
    # final root commitment domain + u64 total + u32 leaf + top digest.
    total+=ROOT_DOMAIN_LEN+8+4+32
    return total


def _q_descriptor_sha_input_bytes(blobs:list[bytes])->int:
    count=len(blobs)
    # Each Surprise digest hashes complete Surprise bytes, then descriptor leaf.
    total=sum(map(len,blobs)) + count*(DESC_LEAF_DOMAIN_LEN+4+40+32)
    width=count
    while width>1:
        next_width=0
        for start in range(0,width,4):
            cc=min(4,width-start)
            total+=DESC_PARENT_DOMAIN_LEN+8+32*cc
            next_width+=1
        width=next_width
    return total


def _time(fn)->int:
    t=time.perf_counter_ns()
    for _ in range(INNER): fn()
    return time.perf_counter_ns()-t


def _measure(independent,shared):
    for _ in range(3): independent(); shared()
    i=[]; s=[]; enabled=gc.isenabled(); gc.disable()
    try:
        for r in range(REPETITIONS):
            if r&1:
                s.append(_time(shared)); i.append(_time(independent))
            else:
                i.append(_time(independent)); s.append(_time(shared))
    finally:
        if enabled: gc.enable()
    return median(i),median(s)


def run():
    rows=[]; failures=[]
    for size,base_index,base,edited,blobs in _families():
        controls=[_desc_control(i,blobs[i]) for i in range(COUNT)]
        def independent():
            roots=[hashlib.sha256(base).digest()]
            roots.extend(hashlib.sha256(x).digest() for x in edited)
            return roots
        def shared():
            basis=build_auth_tree(base,LEAF)
            q=_build_q(controls,blobs)
            return basis.root,q.root
        iroots=independent(); sroots=shared()
        # Determinism and nontrivial root checks.
        if iroots!=independent() or sroots!=shared() or len(set(iroots))!=len(iroots):
            failures.append({"root":size,"base":base_index,"reason":"root_determinism"})
        im,sm=_measure(independent,shared)
        independent_sha_bytes=(COUNT+1)*size
        shared_sha_bytes=_basis_sha_input_bytes(size)+_q_descriptor_sha_input_bytes(blobs)
        rows.append({"root_bytes":size,"base_index":base_index,
                     "independent_roots":COUNT+1,"basis_leaf_bytes":LEAF,
                     "surprise_bytes":sum(map(len,blobs)),
                     "independent_median_ns":im,"shared_median_ns":sm,"elapsed_ratio":sm/im,
                     "independent_sha_input_bytes":independent_sha_bytes,
                     "shared_sha_input_bytes":shared_sha_bytes,
                     "sha_input_ratio":shared_sha_bytes/independent_sha_bytes})
    elapsed_ok=all(r["elapsed_ratio"]<=MAX_ELAPSED_RATIO for r in rows)
    sha_ok=all(r["sha_input_ratio"]<=MAX_SHA_INPUT_RATIO for r in rows)
    passed=not failures and elapsed_ok and sha_ok
    return {"schema":"cmpct-one-g02-shared-auth-family-creation-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_gate":{"max_elapsed_ratio":MAX_ELAPSED_RATIO,"max_sha_input_ratio":MAX_SHA_INPUT_RATIO},
            "failures":failures,
            "median_elapsed_ratio":median(r["elapsed_ratio"] for r in rows),
            "max_elapsed_ratio":max(r["elapsed_ratio"] for r in rows),
            "median_sha_input_ratio":median(r["sha_input_ratio"] for r in rows),
            "max_sha_input_ratio":max(r["sha_input_ratio"] for r in rows),
            "decision":"shared_auth_creation_amortizes_across_v8_family" if passed else "shared_auth_family_creation_debt",
            "claim_boundary":"authentication-setup carrying cost after discovery; shared V8 family semantics; CPython/hashlib timing + deterministic SHA input accounting; no encoder discovery/wire/native/product/comparator/release authority",
            "rows":rows}

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
