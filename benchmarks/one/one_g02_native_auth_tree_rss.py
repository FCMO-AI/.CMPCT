"""Frozen ONE-G0.2 native AuthTree packed-state RSS transfer falsifier."""
from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys
from statistics import median

from experiments.one.auth_tree import build_auth_tree
from experiments.one.native_auth_tree import build_auth_tree_native

SIZES=(4 << 20,16 << 20)
LEAVES=(80,112,192)
REPS=7
DECISION_SIZE=16 << 20
LARGE_HARD_MAX=1.05
LARGE_GOOD_MAX=0.90
LARGE_GOOD_REQUIRED=2
SMALL_MAX=1.10
_DATA_BLOCK=bytes(((i*131) ^ (i>>3) ^ 0x5A) & 0xFF for i in range(4096))


def _data(size:int)->bytes:
    """Construct the source without a source-sized temporary integer/container.

    The root sizes are exact multiples of the frozen 4 KiB block, so multiplication
    creates the one retained source object directly.  This keeps the pre-tree RSS
    high-water mark from being polluted by Random.randbytes/getrandbits temporaries.
    """
    if size % len(_DATA_BLOCK):
        raise ValueError("frozen RSS sizes must be 4 KiB aligned")
    return _DATA_BLOCK * (size // len(_DATA_BLOCK))


def _rss_kib()->int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _child(mode:str,size:int,leaf:int)->dict[str,object]:
    data=_data(size)
    before=_rss_kib()
    if mode == "reference":
        tree=build_auth_tree(data,leaf)
        root=tree.root
        nodes=sum(len(level) for level in tree.levels)
        stored=tree.stored_index_bytes
        packed=None
    elif mode == "native":
        tree=build_auth_tree_native(data,leaf)
        root=tree.root
        nodes=tree.node_count
        stored=tree.stored_index_bytes
        packed=len(tree.packed_nodes)
    else:
        raise ValueError(mode)
    after=_rss_kib()
    return {
        "mode":mode,"size":size,"leaf_bytes":leaf,"root":root.hex(),
        "node_count":nodes,"stored_index_bytes":stored,"packed_nodes_bytes":packed,
        "rss_before_kib":before,"rss_after_kib":after,
        "incremental_peak_kib":max(0,after-before),
    }


def _spawn(mode:str,size:int,leaf:int)->dict[str,object]:
    p=subprocess.run(
        [sys.executable,"-m","benchmarks.one.one_g02_native_auth_tree_rss","--child",mode,
         "--size",str(size),"--leaf",str(leaf)],
        check=True,text=True,capture_output=True,
    )
    return json.loads(p.stdout)


def _decide(rows:list[dict[str,object]])->str:
    if len(rows) != len(SIZES)*len(LEAVES):
        return "INVALIDATE_NATIVE_AUTH_TREE_RSS"
    for r in rows:
        if not bool(r["semantic_ok"]) or float(r["reference_incremental_peak_kib_median"]) <= 0 or float(r["candidate_incremental_peak_kib_median"]) <= 0:
            return "INVALIDATE_NATIVE_AUTH_TREE_RSS"
    large=[r for r in rows if int(r["size"]) == DECISION_SIZE]
    small=[r for r in rows if int(r["size"]) != DECISION_SIZE]
    if len(large) != len(LEAVES) or len(small) != len(LEAVES):
        return "INVALIDATE_NATIVE_AUTH_TREE_RSS"
    large_hard=all(float(r["candidate_over_reference_incremental_rss"]) <= LARGE_HARD_MAX for r in large)
    large_good=sum(1 for r in large if float(r["candidate_over_reference_incremental_rss"]) <= LARGE_GOOD_MAX)
    small_ok=all(float(r["candidate_over_reference_incremental_rss"]) <= SMALL_MAX for r in small)
    return "ADVANCE_NATIVE_AUTH_TREE_RSS" if large_hard and large_good >= LARGE_GOOD_REQUIRED and small_ok else "HOLD_NATIVE_AUTH_TREE_RSS"


def run()->dict[str,object]:
    rows=[]
    for size in SIZES:
        for leaf in LEAVES:
            ref=[]; cand=[]
            for rep in range(REPS):
                order=("native","reference") if rep & 1 else ("reference","native")
                pair={arm:_spawn(arm,size,leaf) for arm in order}
                ref.append(pair["reference"]); cand.append(pair["native"])
            semantic_ok=all(
                a["root"] == b["root"] and a["node_count"] == b["node_count"] and
                a["stored_index_bytes"] == b["stored_index_bytes"]
                for a,b in zip(ref,cand)
            ) and len({x["root"] for x in ref+cand}) == 1
            rm=median(int(x["incremental_peak_kib"]) for x in ref)
            cm=median(int(x["incremental_peak_kib"]) for x in cand)
            rows.append({
                "size":size,"leaf_bytes":leaf,"semantic_ok":semantic_ok,
                "root":ref[0]["root"],"node_count":ref[0]["node_count"],
                "stored_index_bytes":ref[0]["stored_index_bytes"],
                "native_packed_nodes_bytes":cand[0]["packed_nodes_bytes"],
                "reference_incremental_peak_kib_median":rm,
                "candidate_incremental_peak_kib_median":cm,
                "candidate_over_reference_incremental_rss":cm/rm if rm else None,
                "reference_samples_kib":[x["incremental_peak_kib"] for x in ref],
                "candidate_samples_kib":[x["incremental_peak_kib"] for x in cand],
            })
    decision=_decide(rows)
    return {
        "schema":"cmpct-one-g02-native-auth-tree-rss-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes":list(SIZES),"leaves":list(LEAVES),"cold_process_repetitions":REPS,
        "decision_size":DECISION_SIZE,"large_hard_max":LARGE_HARD_MAX,
        "large_good_max":LARGE_GOOD_MAX,"large_good_required":LARGE_GOOD_REQUIRED,"small_max":SMALL_MAX,
        "rows":rows,"decision":decision,
        "claim_boundary":"fresh-process Linux ru_maxrss incremental peak during in-memory AuthTree construction; no product ingest, portable allocator, proof throughput or canonical on-disk authority",
    }


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--child",choices=("reference","native")); ap.add_argument("--size",type=int); ap.add_argument("--leaf",type=int)
    args=ap.parse_args()
    if args.child:
        if args.size is None or args.leaf is None: ap.error("--child requires --size and --leaf")
        print(json.dumps(_child(args.child,args.size,args.leaf),sort_keys=True)); return 0
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_NATIVE_AUTH_TREE_RSS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
