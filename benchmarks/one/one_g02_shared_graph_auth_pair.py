"""ONE-G0.2 shared stored-graph authentication for edited version pairs.

Mission lock / Referee freeze before result-bearing execution
============================================================
The isolated reconstructed-root Merkle experiments showed that a generic integrity index can
miss a local <=3.5% index / <=1.20x 4 KiB access rectangle even though generic ONE range-cone
execution itself is bounded. ONE's representation, however, does not normally store two full
versions when a translation Law + sparse Surprise explains the second one.

Hypothesis: moving the authentication boundary to the *stored information graph* can afford a
much finer authenticated basis (and therefore a larger local index) while still producing a
strict complete-byte win over two independent literal roots, because the authenticated basis
is stored once and the derived root is only Law + Surprise.

This is not permission to ignore the prior 3.5% local-index negative. It asks a different,
global Pareto question and charges the large basis index honestly.

Frozen corpus: the existing 64 internally edited temporal/version rows: 64 KiB and 256 KiB
bases, 8 independent bases per size, mutation counts 1/4/16/64.
Frozen representation:
- first root stored literally once;
- second root is translation Law `target[i] = basis[i]` plus explicit Surprise mutations;
- deterministic Surprise wire: ULEB count, then ULEB position delta + one literal byte;
- generic graph manifest is fully stored and read on every selective request;
- graph root SHA-256 replaces an already-required archive/root digest and is not double charged;
- basis uses the existing domain-separated SHA-256 AuthTree; its base-tree root is stored in
  the graph manifest and all non-root tree hashes are charged;
- Surprise blob has a SHA-256 digest stored in the manifest and the complete small Surprise
  blob is read+verified on a selective read.

Frozen leaf grid: 48,64,80,96,112,128,160,192,256,384,512 bytes. Binary tree semantics are
unchanged. Selective 4 KiB starts sweep EVERY byte offset modulo the leaf. Every reconstructed
range is byte-exact verified.

Frozen advancement gate for a leaf size:
1. complete persisted candidate bytes (basis + all tree hashes + manifest + Surprise) are
   strictly less than two unauthenticated literal roots on EVERY row. This comparator gifts
   the literal pair its integrity metadata, making the density test conservative;
2. median authenticated bytes touched / 4096 <=1.20 on EVERY row;
3. every selective reconstruction is exact;
4. hostile corruption checks prove basis payload, Surprise blob and manifest mutations fail
   authentication.

The first passing leaf in the frozen grid is not automatically canonical. A pass only proves
that global ONE sharing can rehabilitate the isolated local-index tradeoff for this temporal
shape. Creation hashing CPU, larger version families, physical seek layout and generic graph
manifests remain debt.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import struct
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, MUTATION_COUNTS, _edited,
)
from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

REQUEST_BYTES = 4096
LEAF_GRID = (48,64,80,96,112,128,160,192,256,384,512)
MAX_MEDIAN_TOUCH_AMP = 1.20
LAW_CONTROL_BYTES = 32


def _uleb(n: int) -> bytes:
    if n < 0:
        raise ValueError("negative ULEB")
    out=bytearray()
    while True:
        b=n & 0x7f; n >>= 7
        if n: out.append(b|0x80)
        else:
            out.append(b); return bytes(out)


def _surprise_blob(base: bytes, edited: bytes) -> tuple[bytes, tuple[tuple[int,int],...]]:
    diffs=tuple((i,b) for i,(a,b) in enumerate(zip(base,edited)) if a!=b)
    out=bytearray(_uleb(len(diffs))); prev=0
    for pos,value in diffs:
        out.extend(_uleb(pos-prev)); out.append(value); prev=pos
    return bytes(out),diffs


def _manifest(total_len: int, leaf_bytes: int, base_root: bytes, surprise: bytes) -> bytes:
    # Explicit bytes; the graph root is SHA256(manifest) and replaces the ordinary root digest.
    law = b"ONE-TRANSLATION-LAW".ljust(LAW_CONTROL_BYTES,b"\0")
    return (
        b"ONE-GR1\0" + struct.pack("<QI",total_len,leaf_bytes) + base_root + law
        + struct.pack("<Q",len(surprise)) + hashlib.sha256(surprise).digest()
    )


def _verify_surprise(blob: bytes, manifest: bytes) -> bool:
    # Digest occupies the final 32 bytes by frozen manifest layout.
    return hashlib.sha256(blob).digest() == manifest[-32:]


def _apply_range(base_range: bytes, start: int, diffs: tuple[tuple[int,int],...]) -> bytes:
    out=bytearray(base_range); end=start+len(out)
    for pos,value in diffs:
        if start <= pos < end:
            out[pos-start]=value
    return bytes(out)


def run() -> dict[str,object]:
    master=random.Random(MASTER_SEED)
    rows=[]; exact_failures=[]; corruption_failures=[]
    groups={leaf:[] for leaf in LEAF_GRID}

    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed=master.getrandbits(64)
            base=random.Random(seed).randbytes(size)
            trees={leaf:build_auth_tree(base,leaf) for leaf in LEAF_GRID}
            for mutations in MUTATION_COUNTS:
                edited=_edited(base,random.Random(seed ^ (mutations<<32) ^ 0xA11CE5EED),mutations)
                surprise,diffs=_surprise_blob(base,edited)
                for leaf in LEAF_GRID:
                    tree=trees[leaf]
                    manifest=_manifest(size,leaf,tree.root,surprise)
                    graph_root=hashlib.sha256(b"ONE-GRAPH-ROOT\0"+manifest).digest()
                    # tree.stored_index_bytes includes a 4-byte leaf-size field. The manifest
                    # already stores leaf size, so charge every non-root hash but not duplicate metadata.
                    tree_hash_bytes=tree.stored_index_bytes-4
                    persisted=size+tree_hash_bytes+len(manifest)+len(surprise)
                    literal_pair=2*size
                    amps=[]; failures=[]
                    for mod in range(leaf):
                        center=(size-REQUEST_BYTES)//2
                        start=center-center%leaf+mod
                        if start+REQUEST_BYTES>size: start-=leaf
                        expected=edited[start:start+REQUEST_BYTES]
                        proof=prove_range(base,tree,start,REQUEST_BYTES)
                        try:
                            if hashlib.sha256(b"ONE-GRAPH-ROOT\0"+manifest).digest()!=graph_root:
                                raise ValueError("manifest root")
                            if not _verify_surprise(surprise,manifest):
                                raise ValueError("surprise digest")
                            basis_range=verify_range(proof,tree.root,start,REQUEST_BYTES)
                            got=_apply_range(basis_range,start,diffs)
                            if got!=expected:
                                raise ValueError("reconstruction")
                        except Exception as exc:
                            failures.append({"alignment":mod,"reason":type(exc).__name__})
                        touched=len(manifest)+len(surprise)+proof.touched_data_bytes+proof.touched_proof_bytes
                        amps.append(touched/REQUEST_BYTES)
                    if failures:
                        exact_failures.append({"base_bytes":size,"base_index":base_index,"mutations":mutations,"leaf":leaf,"failures":failures})

                    # One deterministic hostile corruption triplet per row/leaf.
                    hostile=[]
                    start=(size-REQUEST_BYTES)//2
                    proof=prove_range(base,tree,start,REQUEST_BYTES)
                    if proof.leaf_payloads:
                        damaged=list(proof.leaf_payloads)
                        first=bytearray(damaged[0]); first[0]^=1; damaged[0]=bytes(first)
                        from experiments.one.auth_tree import RangeProof
                        bad=RangeProof(proof.total_len,proof.leaf_bytes,proof.first_leaf,tuple(damaged),proof.siblings)
                        try:
                            verify_range(bad,tree.root,start,REQUEST_BYTES); hostile.append("basis_corruption_accepted")
                        except ValueError: pass
                    if surprise:
                        bads=bytearray(surprise); bads[-1]^=1
                        if _verify_surprise(bytes(bads),manifest): hostile.append("surprise_corruption_accepted")
                    badm=bytearray(manifest); badm[0]^=1
                    if hashlib.sha256(b"ONE-GRAPH-ROOT\0"+bytes(badm)).digest()==graph_root: hostile.append("manifest_corruption_accepted")
                    if hostile:
                        corruption_failures.append({"base_bytes":size,"base_index":base_index,"mutations":mutations,"leaf":leaf,"failures":hostile})

                    row={
                        "base_bytes":size,"base_index":base_index,"mutation_count":mutations,"leaf_bytes":leaf,
                        "surprise_bytes":len(surprise),"manifest_bytes":len(manifest),"basis_tree_hash_bytes":tree_hash_bytes,
                        "candidate_persisted_bytes":persisted,"literal_pair_bytes":literal_pair,
                        "candidate_fraction_of_literal_pair":persisted/literal_pair,
                        "median_authenticated_touch_amplification":median(amps),"max_authenticated_touch_amplification":max(amps),
                        "exact_failures":len(failures),
                    }
                    rows.append(row); groups[leaf].append(row)

    candidates=[]; summaries={}
    for leaf in LEAF_GRID:
        g=groups[leaf]
        s={
            "rows":len(g),
            "max_candidate_fraction_of_literal_pair":max(r["candidate_fraction_of_literal_pair"] for r in g),
            "median_candidate_fraction_of_literal_pair":median(r["candidate_fraction_of_literal_pair"] for r in g),
            "max_row_median_touch_amplification":max(r["median_authenticated_touch_amplification"] for r in g),
            "max_touch_amplification":max(r["max_authenticated_touch_amplification"] for r in g),
        }
        summaries[str(leaf)]=s
        if s["max_candidate_fraction_of_literal_pair"]<1.0 and s["max_row_median_touch_amplification"]<=MAX_MEDIAN_TOUCH_AMP:
            candidates.append(leaf)

    return {
        "schema":"cmpct-one-g02-shared-graph-auth-pair-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rows":len(rows),"leaf_grid":list(LEAF_GRID),"request_bytes":REQUEST_BYTES,
        "max_median_touch_amplification":MAX_MEDIAN_TOUCH_AMP,
        "exact_failures":exact_failures,"corruption_failures":corruption_failures,
        "target_candidates":candidates,"summaries":summaries,
        "decision":"advance_shared_stored_graph_auth_boundary" if candidates and not exact_failures and not corruption_failures else "shared_graph_auth_pair_not_yet_feasible",
        "remaining_debt":["creation hashing CPU/throughput","larger version-family amortization","physical wire seek/index integration","generic Law/Surprise manifest layout","failure blast radius and update invalidation"],
        "claim_boundary":"edited-version ONE representation/integrity research only; literal-pair comparator is not v0.29/v0.30 and grants no product/release authority",
        "results":rows,
    }


if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
