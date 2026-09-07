"""ONE-G0.2 packed one-shot SHA auth-tree A/B.

Frozen authority: docs/one/prereg/ONE_G02_AUTH_TREE_PACKED_ONESHOT_PREREG_2026-09-07.md
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from statistics import median

from experiments.one.auth_tree import build_auth_tree

ROOT_SIZES=(65_536,262_144)
LEAVES=(80,96,112,192)
REPS=31
BIN=Path("/tmp/one_g02_auth_tree_packed_oneshot")
SRC=Path("benchmarks/one/native/one_g02_auth_tree_packed_oneshot.c")
MAX_MEDIAN_RATIO=0.85
MAX_BALANCED_RATIO=0.90
MAX_ROW_RATIO=0.98


def _data(n:int)->bytes:
    return bytes((((i*131) ^ (i>>3) ^ (i>>11) ^ 0x5a)&255) for i in range(n))


def _nodes(total:int,leaf:int)->int:
    width=max(1,(total+leaf-1)//leaf); nodes=width
    while width>1:
        width=(width+1)//2; nodes+=width
    return nodes+1


def run()->dict[str,object]:
    subprocess.run([
        "cc","-std=c11","-O2","-Wall","-Wextra","-Werror","-Wno-deprecated-declarations",
        str(SRC),"-lcrypto","-o",str(BIN),
    ],check=True)
    rows=[]; mismatches=[]
    for root_bytes in ROOT_SIZES:
        data=_data(root_bytes)
        for leaf in LEAVES:
            expected=build_auth_tree(data,leaf).root.hex()
            p=subprocess.run([str(BIN),str(root_bytes),str(leaf),str(REPS)],check=True,text=True,capture_output=True)
            row=json.loads(p.stdout)
            problems=[]
            if row["baseline_root"]!=expected: problems.append("baseline_root")
            if row["candidate_root"]!=expected: problems.append("candidate_root")
            if row["baseline_root"]!=row["candidate_root"]: problems.append("cross_root")
            if row["node_count"]!=_nodes(root_bytes,leaf): problems.append("node_count")
            if problems:
                mismatches.append({"root_bytes":root_bytes,"leaf_bytes":leaf,"problems":problems,"expected":expected,"row":row})
            rows.append(row)
    ratios=[r["candidate_ratio"] for r in rows]
    balanced=[r["candidate_ratio"] for r in rows if r["leaf_bytes"]==112]
    med=median(ratios); worst=max(ratios)
    passed=(not mismatches and med<=MAX_MEDIAN_RATIO and max(balanced)<=MAX_BALANCED_RATIO and worst<=MAX_ROW_RATIO)
    return {
        "schema":"cmpct-one-g02-auth-tree-packed-oneshot-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions":REPS,
        "frozen_gate":{
            "max_median_ratio":MAX_MEDIAN_RATIO,
            "max_balanced_112_ratio":MAX_BALANCED_RATIO,
            "max_row_ratio":MAX_ROW_RATIO,
        },
        "root_or_geometry_mismatches":mismatches,
        "median_candidate_ratio":med,
        "max_balanced_112_ratio":max(balanced),
        "max_candidate_ratio":worst,
        "decision":"advance_packed_oneshot_auth_tree_hashing" if passed else "reject_packed_oneshot_auth_tree_hashing",
        "claim_boundary":"exact existing ONE research auth-tree native creation microprofile only; SHA-256/tree/proofs unchanged; no end-to-end ingest, authenticated-range, release or comparator authority",
        "rows":rows,
    }


if __name__=="__main__":
    result=run()
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"]=="advance_packed_oneshot_auth_tree_hashing" else 1)
