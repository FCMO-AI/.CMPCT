"""ONE-G0.2 creation-cost audit for passing shared-graph authentication leaves.

Referee freeze before result-bearing execution
==============================================
The shared stored-graph experiment advanced 80/96/112/192-byte leaves on complete density +
authenticated selective access. This audit asks what encoder cost that win exported.

Frozen cases: deterministic random 64 KiB and 256 KiB roots. Passing leaves only, with the
existing exact AuthTree implementation. Baseline is one whole-root SHA-256 over identical
bytes. Two warmups and 15 timed repetitions; medians reported.

In addition to hosted Python elapsed (diagnostic, not native authority), charge an
implementation-independent work model from the exact hash grammar:
- one SHA-256 per leaf over domain + index/total metadata + payload;
- one SHA-256 per binary parent over domain + level + two 32-byte children;
- one root-commit SHA-256.
Report hash invocation count and total bytes presented to SHA-256 relative to the input.

Falsifiable hypothesis: the globally feasible fine leaves export a material creation bill:
>10x hosted elapsed vs whole-root SHA on both large roots OR >1.50x hash-input traffic. A
failure to meet that condition would falsify 'creation hashing is material debt'. No result
changes the preceding density/access win; this instrument only decides whether creation-side
rehabilitation is mandatory before promotion.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import time
from statistics import median

from experiments.one.auth_tree import build_auth_tree

ROOT_SIZES=(65_536,262_144)
LEAVES=(80,96,112,192)
REPS=15
WARMUPS=2
SEED=0xA171C057


def _work(root_bytes:int,leaf:int)->dict[str,float|int]:
    leaves=math.ceil(root_bytes/leaf)
    widths=[leaves]
    while widths[-1]>1:
        widths.append(math.ceil(widths[-1]/2))
    parents=sum(widths[1:])
    # _leaf_hash: b"ONE-L\0" (6) + <QQ> (16) + payload.
    leaf_input=root_bytes + leaves*22
    # _parent_hash: b"ONE-P\0" (6) + <I> (4) + two 32-byte children.
    parent_input=parents*74
    # _root_commit: b"ONE-R\0" (6) + <QI> (12) + 32-byte tree root.
    root_input=50
    hashed=leaf_input+parent_input+root_input
    return {
        "leaf_hashes":leaves,"parent_hashes":parents,"root_commit_hashes":1,
        "sha256_invocations":leaves+parents+1,
        "sha256_input_bytes":hashed,"sha256_input_bytes_per_source_byte":hashed/root_bytes,
    }


def _median_ns(fn):
    for _ in range(WARMUPS): fn()
    samples=[]
    for _ in range(REPS):
        t=time.perf_counter_ns(); fn(); samples.append(time.perf_counter_ns()-t)
    return median(samples),samples


def run()->dict[str,object]:
    rows=[]; material=[]
    for root_bytes in ROOT_SIZES:
        data=random.Random(SEED ^ root_bytes).randbytes(root_bytes)
        base_ns,base_samples=_median_ns(lambda: hashlib.sha256(data).digest())
        for leaf in LEAVES:
            tree_ns,tree_samples=_median_ns(lambda leaf=leaf: build_auth_tree(data,leaf))
            work=_work(root_bytes,leaf)
            ratio=tree_ns/base_ns
            row={
                "root_bytes":root_bytes,"leaf_bytes":leaf,"repetitions":REPS,
                "whole_sha256_median_ns":base_ns,"auth_tree_median_ns":tree_ns,
                "elapsed_ratio_vs_whole_sha256":ratio,
                "whole_sha256_samples_ns":base_samples,"auth_tree_samples_ns":tree_samples,
                **work,
            }
            rows.append(row)
            if ratio>10.0 or work["sha256_input_bytes_per_source_byte"]>1.50:
                material.append({"root_bytes":root_bytes,"leaf_bytes":leaf})
    expected=len(ROOT_SIZES)*len(LEAVES)
    return {
        "schema":"cmpct-one-g02-shared-graph-auth-create-cost-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rows":rows,"material_debt_rows":material,
        "decision":"creation_hashing_rehabilitation_required" if len(material)==expected else "creation_hashing_materiality_hypothesis_partly_or_fully_falsified",
        "claim_boundary":"hosted Python elapsed + exact hash-work accounting; no native/product-speed authority",
        "next_if_material":"test level-batched/fused native hashing while preserving exact roots and the shared-graph density/access gain",
    }


if __name__=='__main__': print(json.dumps(run(),indent=2,sort_keys=True))
