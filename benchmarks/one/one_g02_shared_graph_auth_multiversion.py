"""ONE-G0.2 shared stored-graph authentication multi-version transfer.

Referee freeze before result-bearing execution
==============================================
The edited-pair experiment showed that authenticating one stored basis plus Law+Surprise can
retain SHA-256 integrity, bounded 4 KiB access and a complete-byte win even with a locally
large fine-leaf index. This transfer grows the family while preserving that representation.

Frozen family:
- bases 64 KiB and 256 KiB, four deterministic independent bases each;
- eight independently edited children with mutation counts 1,2,4,8,16,32,48,64;
- prefixes of 1,2,4,8 derived versions are tested;
- leaf grid 32,48,64,80,96,112,128,160,192 bytes;
- graph manifest stores base-tree root + one 72-byte descriptor per derived version
  (32 B Law control, 8 B Surprise length, 32 B SHA-256 Surprise digest);
- the current simple reader authenticates/reads the COMPLETE graph manifest for each range,
  plus only the selected version's complete Surprise blob and the required basis proof;
- starts sweep every byte offset modulo leaf and reconstruction must be exact.

Frozen transfer gate: a leaf transfers only if for EVERY tested family prefix/target row,
(1) complete persisted bytes are strictly below an unauthenticated independent-literal family
of equal semantics and (2) median authenticated 4 KiB traffic <=1.20x. Literal baselines are
gifted all integrity metadata. No post-result manifest paging or threshold change is allowed.

If pair-feasible leaves lose as version count rises, identify whether complete-manifest bytes
own the loss. The correct next Builder would then make the generic Law/Surprise manifest
selectively authenticated/addressable rather than weakening data authentication or discarding
shared Law.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import struct
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob, _apply_range
from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

ROOT_SIZES=(65_536,262_144)
BASES_PER_SIZE=4
MUTATIONS=(1,2,4,8,16,32,48,64)
VERSION_COUNTS=(1,2,4,8)
LEAF_GRID=(32,48,64,80,96,112,128,160,192)
REQUEST_BYTES=4096
MAX_MEDIAN_TOUCH_AMP=1.20
LAW_CONTROL_BYTES=32


def _manifest(total:int,leaf:int,base_root:bytes,surprises:list[bytes])->bytes:
    out=bytearray(b"ONE-GMV1")
    out.extend(struct.pack("<QII",total,leaf,len(surprises)))
    out.extend(base_root)
    for i,blob in enumerate(surprises):
        law=(f"ONE-TRANSLATION-{i}".encode()).ljust(LAW_CONTROL_BYTES,b"\0")[:LAW_CONTROL_BYTES]
        out.extend(law); out.extend(struct.pack("<Q",len(blob))); out.extend(hashlib.sha256(blob).digest())
    return bytes(out)


def run()->dict[str,object]:
    master=random.Random(MASTER_SEED ^ 0xA071FA11)
    rows=[]; exact_failures=[]
    for size in ROOT_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed=master.getrandbits(64); base=random.Random(seed).randbytes(size)
            edited=[]; blobs=[]; diffs=[]
            for m in MUTATIONS:
                e=_edited(base,random.Random(seed ^ (m<<32) ^ 0xA11CE5EED),m)
                b,d=_surprise_blob(base,e); edited.append(e); blobs.append(b); diffs.append(d)
            trees={leaf:build_auth_tree(base,leaf) for leaf in LEAF_GRID}
            for count in VERSION_COUNTS:
                chosen_blobs=blobs[:count]
                for leaf in LEAF_GRID:
                    tree=trees[leaf]; manifest=_manifest(size,leaf,tree.root,chosen_blobs)
                    graph_root=hashlib.sha256(b"ONE-GMV-ROOT\0"+manifest).digest()
                    tree_hash_bytes=tree.stored_index_bytes-4
                    persisted=size+tree_hash_bytes+len(manifest)+sum(len(b) for b in chosen_blobs)
                    literal_family=(count+1)*size
                    for version in range(count):
                        amps=[]; failures=[]
                        for mod in range(leaf):
                            center=(size-REQUEST_BYTES)//2
                            start=center-center%leaf+mod
                            if start+REQUEST_BYTES>size: start-=leaf
                            proof=prove_range(base,tree,start,REQUEST_BYTES)
                            try:
                                if hashlib.sha256(b"ONE-GMV-ROOT\0"+manifest).digest()!=graph_root:
                                    raise ValueError("manifest")
                                # Descriptor digest is at a deterministic offset in the fully authenticated manifest.
                                desc0=8+16+32 + version*72
                                digest=manifest[desc0+40:desc0+72]
                                if hashlib.sha256(chosen_blobs[version]).digest()!=digest:
                                    raise ValueError("surprise")
                                basis=verify_range(proof,tree.root,start,REQUEST_BYTES)
                                got=_apply_range(basis,start,diffs[version])
                                if got!=edited[version][start:start+REQUEST_BYTES]:
                                    raise ValueError("reconstruction")
                            except Exception as exc:
                                failures.append({"alignment":mod,"reason":type(exc).__name__})
                            touched=len(manifest)+len(chosen_blobs[version])+proof.touched_data_bytes+proof.touched_proof_bytes
                            amps.append(touched/REQUEST_BYTES)
                        if failures:
                            exact_failures.append({"root_bytes":size,"base_index":base_index,"version_count":count,"version":version,"leaf":leaf,"failures":failures})
                        rows.append({
                            "root_bytes":size,"base_index":base_index,"version_count":count,"version":version,"mutation_count":MUTATIONS[version],"leaf_bytes":leaf,
                            "manifest_bytes":len(manifest),"target_surprise_bytes":len(chosen_blobs[version]),"basis_tree_hash_bytes":tree_hash_bytes,
                            "candidate_persisted_bytes":persisted,"literal_family_bytes":literal_family,
                            "candidate_fraction_of_literal_family":persisted/literal_family,
                            "median_authenticated_touch_amplification":median(amps),"max_authenticated_touch_amplification":max(amps),
                        })
    summaries={}; candidates=[]
    for leaf in LEAF_GRID:
        g=[r for r in rows if r["leaf_bytes"]==leaf]
        s={
            "rows":len(g),
            "max_candidate_fraction_of_literal_family":max(r["candidate_fraction_of_literal_family"] for r in g),
            "max_row_median_touch_amplification":max(r["median_authenticated_touch_amplification"] for r in g),
            "max_touch_amplification":max(r["max_authenticated_touch_amplification"] for r in g),
        }
        # expose growth owner at the largest family
        g8=[r for r in g if r["version_count"]==8]
        s["v8_max_manifest_bytes"]=max(r["manifest_bytes"] for r in g8)
        s["v8_max_row_median_touch_amplification"]=max(r["median_authenticated_touch_amplification"] for r in g8)
        summaries[str(leaf)]=s
        if s["max_candidate_fraction_of_literal_family"]<1.0 and s["max_row_median_touch_amplification"]<=MAX_MEDIAN_TOUCH_AMP:
            candidates.append(leaf)
    return {
        "schema":"cmpct-one-g02-shared-graph-auth-multiversion-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "version_counts":list(VERSION_COUNTS),"mutation_counts":list(MUTATIONS),"leaf_grid":list(LEAF_GRID),
        "exact_failures":exact_failures,"target_candidates":candidates,"summaries":summaries,
        "decision":"shared_graph_auth_transfers_to_multiversion" if candidates and not exact_failures else "complete_manifest_addressability_blocks_multiversion_transfer",
        "claim_boundary":"multi-version structural transfer only; no v0.29/v0.30, native-speed, canonical-wire or release authority",
        "results":rows,
    }


if __name__=='__main__': print(json.dumps(run(),indent=2,sort_keys=True))
