"""Frozen ONE-G0.2 native authenticated-tree batching falsifier."""
from __future__ import annotations

import json
import os
import random
import time
from statistics import median

from experiments.one.auth_tree import build_auth_tree
from experiments.one.native_auth_tree import build_auth_tree_native

SIZES=(64 << 10, 256 << 10)
LEAVES=(80,96,112,192)
REPS=15
WARMUPS=2
DECISION_SIZE=256 << 10
LARGE_MAX=0.50
SMALL_MAX=0.75
SEED=0xA171BA7C


def _semantic(data: bytes, leaf: int) -> tuple[bool,int,int]:
    ref=build_auth_tree(data,leaf)
    got=build_auth_tree_native(data,leaf)
    ok=(got.root == ref.root and got.levels() == ref.levels and
        got.node_count == sum(len(x) for x in ref.levels) and
        got.stored_index_bytes == ref.stored_index_bytes)
    return ok,got.node_count,got.stored_index_bytes


def _paired(data: bytes, leaf: int) -> tuple[float,float,float,float]:
    # Compile/load before clocks and warm both arms.
    build_auth_tree_native(data,leaf)
    for _ in range(WARMUPS):
        build_auth_tree(data,leaf); build_auth_tree_native(data,leaf)
    ref_wall=[]; ref_cpu=[]; native_wall=[]; native_cpu=[]
    previous=None
    for rep in range(REPS):
        previous=None
        if rep & 1:
            order=("native","ref")
        else:
            order=("ref","native")
        for arm in order:
            previous=None
            c0=time.process_time_ns(); w0=time.perf_counter_ns()
            result=build_auth_tree_native(data,leaf) if arm == "native" else build_auth_tree(data,leaf)
            w1=time.perf_counter_ns(); c1=time.process_time_ns()
            if arm == "native":
                native_wall.append(w1-w0); native_cpu.append(c1-c0)
            else:
                ref_wall.append(w1-w0); ref_cpu.append(c1-c0)
            previous=result
    previous=None
    return median(ref_wall),median(ref_cpu),median(native_wall),median(native_cpu)


def _decide(rows: list[dict[str,object]]) -> str:
    if len(rows) != len(SIZES)*len(LEAVES) or not all(bool(r["semantic_ok"]) for r in rows):
        return "INVALIDATE_NATIVE_AUTH_TREE_BATCH"
    large=[r for r in rows if r["size"] == DECISION_SIZE]
    small=[r for r in rows if r["size"] != DECISION_SIZE]
    if (len(large) == len(LEAVES) and
        all(float(r["native_over_ref_wall"]) <= LARGE_MAX and float(r["native_over_ref_cpu"]) <= LARGE_MAX for r in large) and
        all(float(r["native_over_ref_wall"]) <= SMALL_MAX and float(r["native_over_ref_cpu"]) <= SMALL_MAX for r in small)):
        return "ADVANCE_NATIVE_AUTH_TREE_BATCH"
    return "HOLD_NATIVE_AUTH_TREE_BATCH"


def run() -> dict[str,object]:
    rows=[]
    for size in SIZES:
        data=random.Random(SEED ^ size).randbytes(size)
        for leaf in LEAVES:
            semantic_ok,node_count,index_bytes=_semantic(data,leaf)
            rw,rc,nw,nc=_paired(data,leaf)
            rows.append({
                "size":size,"leaf_bytes":leaf,"semantic_ok":semantic_ok,
                "node_count":node_count,"packed_node_bytes":node_count*32,
                "stored_index_bytes":index_bytes,
                "reference_wall_ns_median":rw,"reference_cpu_ns_median":rc,
                "native_wall_ns_median":nw,"native_cpu_ns_median":nc,
                "native_over_ref_wall":nw/rw,"native_over_ref_cpu":nc/rc,
            })
    decision=_decide(rows)
    return {
        "schema":"cmpct-one-g02-native-auth-tree-batch-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes":list(SIZES),"leaves":list(LEAVES),"repetitions":REPS,
        "decision_size":DECISION_SIZE,"large_ratio_max":LARGE_MAX,"small_ratio_max":SMALL_MAX,
        "semantic_gates_pass":all(bool(r["semantic_ok"]) for r in rows),
        "rows":rows,"decision":decision,
        "claim_boundary":"exact existing generic auth-tree grammar; candidate batches hashing in native libcrypto and emits packed node digests; compilation, proof verification, filesystem/product ingest, process RSS, and portability beyond the hosted research dependency are outside scope",
    }


if __name__ == "__main__":
    result=run()
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_NATIVE_AUTH_TREE_BATCH" else 2)
