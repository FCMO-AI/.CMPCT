"""ONE-G0.2 integrated authenticated-range descriptor A/B.

Referee freeze before result-bearing execution
==============================================
The generic range cone has already shown 2.0x source-size-invariant reconstruction work, but
explicitly without hard selective authentication.  The shared-graph authentication line then
found a structural knee at an 80-byte basis AuthTree leaf, and q4 descriptor authentication plus
packed proofs reduced persisted descriptor hashes without adding authenticated information.

This experiment combines those already-evidenced pieces for one narrow carrying-cost question:
with the SAME 80-byte basis tree, Surprise bytes, 40-byte Law descriptor control and 4 KiB
request, does packed q4 descriptor authentication retain its byte advantage without making the
complete authenticated selective read slower than binary descriptor authentication?

It is intentionally NOT a new representation search.  The basis tree, corpus/version families,
request geometry and translation reconstruction are frozen from the existing shared-graph
experiments.  Binary and q4 read the same basis proof and same Surprise.  Only descriptor-tree
shape/proof representation differs.

Frozen V=8 gate:
- every binary and q4 read must authenticate and reconstruct exact requested bytes;
- deterministic descriptor-proof corruption must reject for q4;
- q4 complete persisted bytes must be strictly below binary on every V=8 row;
- q4 authenticated bytes touched must be <= binary + 32 bytes on every V=8 row (the known
  q4 descriptor-proof traffic delta);
- median end-to-end reference read ratio q4/binary across V=8 rows <=1.03x;
- no V=8 row may exceed 1.08x.
Failure preserves the q4 structural result but records exported integrated read debt.  Timing is
CPython/hashlib research evidence only; native/product claims require native execution.
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
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob, _apply_range
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, BASES_PER_SIZE, MUTATIONS, REQUEST_BYTES
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import (
    DESC_CONTROL_BYTES, HEADER_BYTES, HASH_BYTES, _build_desc_tree, _desc_control, _desc_proof,
    _header, _verify_desc,
)
from benchmarks.one.one_g02_descriptor_auth_quaternary_ab import _build as _build_q
from benchmarks.one.one_g02_descriptor_auth_packed_proof_ab import _packed_proof, _verify_packed
from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

LEAF = 80
COUNT = 8
REPETITIONS = 13
INNER = 80
MAX_MEDIAN_RATIO = 1.03
MAX_ROW_RATIO = 1.08


def _time(fn) -> int:
    t = time.perf_counter_ns()
    for _ in range(INNER): fn()
    return time.perf_counter_ns() - t


def _measure(binary_fn, q_fn):
    for _ in range(3): binary_fn(); q_fn()
    b=[]; q=[]; enabled=gc.isenabled(); gc.disable()
    try:
        for r in range(REPETITIONS):
            if r & 1:
                q.append(_time(q_fn)); b.append(_time(binary_fn))
            else:
                b.append(_time(binary_fn)); q.append(_time(q_fn))
    finally:
        if enabled: gc.enable()
    return median(b), median(q)


def run() -> dict[str, object]:
    master=random.Random(MASTER_SEED ^ 0xA071FA11)
    rows=[]; failures=[]; corruption_failures=[]
    for size in ROOT_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed=master.getrandbits(64); base=random.Random(seed).randbytes(size)
            edited=[]; blobs=[]; diffs=[]
            for m in MUTATIONS[:COUNT]:
                e=_edited(base,random.Random(seed^(m<<32)^0xA11CE5EED),m)
                blob,diff=_surprise_blob(base,e); edited.append(e); blobs.append(blob); diffs.append(diff)
            controls=[_desc_control(i,blobs[i]) for i in range(COUNT)]
            bt=_build_desc_tree(controls,blobs); qt=_build_q(controls,blobs)
            basis=build_auth_tree(base,LEAF)
            basis_hash_bytes=basis.stored_index_bytes-4
            b_persist=(size+basis_hash_bytes+HEADER_BYTES+DESC_CONTROL_BYTES*COUNT+
                       bt.stored_nonroot_hash_bytes+sum(map(len,blobs)))
            q_persist=(size+basis_hash_bytes+HEADER_BYTES+DESC_CONTROL_BYTES*COUNT+
                       qt.stored_nonroot_hash_bytes+sum(map(len,blobs)))
            for version in range(COUNT):
                bp=_desc_proof(bt,version); qp=_packed_proof(qt,version)
                center=(size-REQUEST_BYTES)//2
                start=center-center%LEAF+(version*17)%LEAF
                if start+REQUEST_BYTES>size: start-=LEAF
                basis_proof=prove_range(base,basis,start,REQUEST_BYTES)

                def bread():
                    _verify_desc(index=version,count=COUNT,control=controls[version],surprise=blobs[version],proof=bp,expected_root=bt.root)
                    got_basis=verify_range(basis_proof,basis.root,start,REQUEST_BYTES)
                    got=_apply_range(got_basis,start,diffs[version])
                    if got!=edited[version][start:start+REQUEST_BYTES]: raise AssertionError("binary reconstruction")

                def qread():
                    _verify_packed(version,COUNT,controls[version],blobs[version],qp,qt.root)
                    got_basis=verify_range(basis_proof,basis.root,start,REQUEST_BYTES)
                    got=_apply_range(got_basis,start,diffs[version])
                    if got!=edited[version][start:start+REQUEST_BYTES]: raise AssertionError("q4 reconstruction")

                try: bread(); qread()
                except Exception as exc:
                    failures.append({"root":size,"base":base_index,"version":version,"reason":type(exc).__name__})
                if qp and qp[0]:
                    bad=list(qp); x=bytearray(bad[0]); x[0]^=1; bad[0]=bytes(x)
                    try:
                        _verify_packed(version,COUNT,controls[version],blobs[version],tuple(bad),qt.root)
                        corruption_failures.append({"root":size,"base":base_index,"version":version})
                    except ValueError: pass

                bm,qm=_measure(bread,qread)
                basis_touch=basis_proof.touched_data_bytes+basis_proof.touched_proof_bytes
                b_desc_proof=HASH_BYTES*len(bp); q_desc_proof=sum(len(x) for x in qp)
                common_touch=HEADER_BYTES+DESC_CONTROL_BYTES+len(blobs[version])+basis_touch
                rows.append({
                    "root_bytes":size,"base_index":base_index,"version":version,
                    "binary_persisted_bytes":b_persist,"q4_persisted_bytes":q_persist,
                    "persisted_delta_bytes":q_persist-b_persist,
                    "binary_authenticated_touch_bytes":common_touch+b_desc_proof,
                    "q4_authenticated_touch_bytes":common_touch+q_desc_proof,
                    "authenticated_touch_delta_bytes":q_desc_proof-b_desc_proof,
                    "binary_read_median_ns":bm,"q4_read_median_ns":qm,"read_ratio":qm/bm,
                })

    ratios=[r["read_ratio"] for r in rows]
    persisted_ok=all(r["q4_persisted_bytes"]<r["binary_persisted_bytes"] for r in rows)
    touch_ok=all(r["authenticated_touch_delta_bytes"]<=32 for r in rows)
    timing_ok=median(ratios)<=MAX_MEDIAN_RATIO and max(ratios)<=MAX_ROW_RATIO
    passed=not failures and not corruption_failures and persisted_ok and touch_ok and timing_ok
    return {
        "schema":"cmpct-one-g02-authenticated-range-integrated-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "basis_leaf_bytes":LEAF,"version_count":COUNT,"request_bytes":REQUEST_BYTES,
        "frozen_gate":{"max_median_read_ratio":MAX_MEDIAN_RATIO,"max_row_read_ratio":MAX_ROW_RATIO},
        "exact_failures":failures,"corruption_failures":corruption_failures,
        "median_read_ratio":median(ratios),"max_read_ratio":max(ratios),
        "persisted_delta_bytes":sorted(set(r["persisted_delta_bytes"] for r in rows)),
        "touch_delta_bytes":sorted(set(r["authenticated_touch_delta_bytes"] for r in rows)),
        "decision":"advance_integrated_q4_authenticated_range" if passed else "integrated_q4_read_debt",
        "claim_boundary":"generic shared-basis authenticated-range carrying-cost profile; translation reconstruction helper; CPython/hashlib only; no canonical wire/native/product/comparator/release authority",
        "rows":rows,
    }

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
