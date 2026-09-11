"""ONE-G0.2 multi-buffer SHA resource/crossover falsifier.

Frozen authority:
docs/one/prereg/ONE_G02_AUTH_TREE_MULTIBUFFER_RESOURCE_CROSSOVER_PREREG_2026-09-07.md
"""
from __future__ import annotations

import json
import os
import subprocess
from math import isfinite
from pathlib import Path
from statistics import median

from experiments.one.auth_tree import build_auth_tree

DISCOVERY=(1_024,2_048,4_096,8_192,16_384,32_768,65_536,131_072,262_144)
HOLDOUT=(6_144,12_288,24_576,49_152,98_304,196_608)
LEAF=112
REPS=31
BIN=Path("/tmp/one_g02_auth_tree_multibuffer_resource")
SRC=Path("benchmarks/one/native/one_g02_auth_tree_multibuffer_sha.c")


def _data(n:int)->bytes:
    return bytes((((i*131) ^ (i>>3) ^ (i>>11) ^ 0x5a)&255) for i in range(n))


def _run_row(root_bytes:int)->dict[str,object]:
    expected=build_auth_tree(_data(root_bytes),LEAF).root.hex()
    p=subprocess.run([str(BIN),str(root_bytes),str(LEAF),str(REPS)],check=True,text=True,capture_output=True)
    row=json.loads(p.stdout)
    problems=[]
    if row["baseline_root"]!=expected: problems.append("baseline_root")
    if row["candidate_root"]!=expected: problems.append("candidate_root")
    if row["baseline_root"]!=row["candidate_root"]: problems.append("cross_root")
    expected_staged=root_bytes + row["leaf_count"]*22 + row["parent_count"]*74 + 50
    if row["candidate_staged_bytes"]!=expected_staged: problems.append("staged_accounting")
    if row["candidate_total_explicit_workspace_bytes"] != row["baseline_explicit_workspace_bytes"] + row["candidate_extra_explicit_workspace_bytes"]:
        problems.append("workspace_accounting")
    for key in ("candidate_ratio","candidate_cpu_ratio","candidate_staged_over_source_ratio"):
        value=float(row[key])
        if not isfinite(value) or value < 0.0:
            problems.append(f"nonfinite_or_negative_{key}")
    row["problems"]=problems
    return row


def _learn_threshold(rows:list[dict[str,object]])->int|None:
    ordered=sorted(rows,key=lambda r:int(r["node_count"]))
    # A deployed threshold dispatches *every* row whose node_count is >= the
    # threshold.  Therefore a threshold may only start at the first row of a
    # node-count equivalence class.  Starting in the middle of a tie can make
    # the learner ignore a bad observation that deployment would still route
    # to the multi-buffer path.
    candidate_starts=[]
    previous_node_count=None
    for i,row in enumerate(ordered):
        node_count=int(row["node_count"])
        if node_count!=previous_node_count:
            candidate_starts.append(i)
            previous_node_count=node_count
    for i in candidate_starts:
        row=ordered[i]
        suffix=ordered[i:]
        wall=[float(r["candidate_ratio"]) for r in suffix]
        cpu=[float(r["candidate_cpu_ratio"]) for r in suffix]
        if not all(isfinite(x) and x >= 0.0 for x in wall+cpu): continue
        if wall[0]>0.95: continue
        if any(x>0.95 for x in wall): continue
        if median(cpu)>0.90: continue
        return int(row["node_count"])
    return None


def run()->dict[str,object]:
    include=os.environ.get("IMB_INCLUDE","/tmp/imb/include")
    lib=os.environ.get("IMB_LIB","/tmp/imb/lib")
    subprocess.run([
        "cc","-std=c11","-O2","-Wall","-Wextra","-Werror","-Wno-deprecated-declarations",
        f"-I{include}",str(SRC),f"-L{lib}",f"-Wl,-rpath,{lib}","-lIPSec_MB","-lcrypto","-o",str(BIN),
    ],check=True)

    discovery=[_run_row(n) for n in DISCOVERY]
    holdout=[_run_row(n) for n in HOLDOUT]
    all_rows=discovery+holdout
    mismatches=[{"root_bytes":r["root_bytes"],"problems":r["problems"]} for r in all_rows if r["problems"]]
    threshold=_learn_threshold(discovery) if not mismatches else None

    selected=[]
    dispatch_rows=[]
    for row in holdout:
        use_mb=threshold is not None and int(row["node_count"])>=threshold
        dispatched_wall=float(row["candidate_ratio"]) if use_mb else 1.0
        dispatched_cpu=float(row["candidate_cpu_ratio"]) if use_mb else 1.0
        d={"root_bytes":row["root_bytes"],"node_count":row["node_count"],"use_multibuffer":use_mb,
           "raw_candidate_wall_ratio":row["candidate_ratio"],"raw_candidate_cpu_ratio":row["candidate_cpu_ratio"],
           "dispatched_wall_ratio":dispatched_wall,"dispatched_cpu_ratio":dispatched_cpu}
        dispatch_rows.append(d)
        if use_mb: selected.append(row)

    extra_workspace={int(r["candidate_extra_explicit_workspace_bytes"]) for r in all_rows}
    holdout_ok=(
        threshold is not None and not mismatches and len(extra_workspace)==1
        and all(float(r["dispatched_wall_ratio"])<=1.00 for r in dispatch_rows)
        and all(float(r["raw_candidate_wall_ratio"])<=0.97 for r in dispatch_rows if r["use_multibuffer"])
        and bool(selected)
        and median(float(r["candidate_cpu_ratio"]) for r in selected)<=0.92
    )

    return {
        "schema":"cmpct-one-g02-auth-tree-multibuffer-resource-crossover-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "external_prototype_commit":"4f808234a91e87147a4f26167df40f3fd7c7f0c6",
        "leaf_bytes":LEAF,
        "repetitions":REPS,
        "discovery_root_bytes":list(DISCOVERY),
        "holdout_root_bytes":list(HOLDOUT),
        "learned_node_threshold":threshold,
        "candidate_extra_explicit_workspace_bytes":next(iter(extra_workspace)) if len(extra_workspace)==1 else None,
        "root_or_accounting_mismatches":mismatches,
        "selected_holdout_cpu_median_ratio":median(float(r["candidate_cpu_ratio"]) for r in selected) if selected else None,
        "max_selected_holdout_wall_ratio":max((float(r["candidate_ratio"]) for r in selected),default=None),
        "decision":"advance_node_count_multibuffer_dispatch_principle" if holdout_ok else "reject_node_count_multibuffer_dispatch_principle",
        "claim_boundary":"writer-side exact SHA-256 implementation dispatch only; external kernel remains research prototype; no reader/format/security/storage/access/portability/end-to-end authority",
        "discovery_rows":discovery,
        "holdout_rows":holdout,
        "holdout_dispatch":dispatch_rows,
    }


if __name__=="__main__":
    result=run()
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"]=="advance_node_count_multibuffer_dispatch_principle" else 1)
