from __future__ import annotations

"""Hostile reviewer for EG08 exported read/verification cost.

Preregistered by docs/V030_EG08_READ_COST_MISSION_LOCK_2026-09-13.md.
No compression decision is changed here.
"""

import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build

EG07_MODULE = "experiments.entropygraph_v030_federated_embedded_fs_candidate_v7"
EG08_MODULE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8"
NEUTRAL = {
    "02_office_workspace",
    "04_analytics_and_database",
    "05_logs_and_telemetry",
    "09_ml_artifacts",
    "10_large_mixed_binary",
}
HOSTILE_NAMES = {
    "01_shifted_versions",
    "02_false_neighbors",
    "03_boundary_churn",
    "05_incompressible",
}
REPS = 3
REL = 0.05
ABS_S = 0.003

_OP = r'''
import importlib,json,os,resource,sys,tempfile,time
from pathlib import Path
module,op,archive,source=sys.argv[1:5]
m=importlib.import_module(module)
archive=Path(archive); source=Path(source)
tree_owner=m if hasattr(m,"_treehash") else getattr(m,"EG07",None)
if tree_owner is None or not hasattr(tree_owner,"_treehash"):
    raise RuntimeError(f"{module} exposes no authoritative tree hash owner")
expected=tree_owner._treehash(source)
c0=time.process_time(); w0=time.perf_counter()
if op == "extract":
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-read-extract-") as td:
        dest=Path(td)/"out"
        m.extract(archive,dest)
        observed=tree_owner._treehash(dest)
        ok=observed==expected
elif op == "verify":
    result=m.strong_verify(archive,expected_tree=expected)
    observed=str(result.get("canonical_user_tree_sha256", expected))
    ok=bool(result.get("ok")) and observed==expected
else:
    raise SystemExit("bad op")
cpu=time.process_time()-c0; wall=time.perf_counter()-w0
print(json.dumps({"ok":ok,"expected_tree":expected,"observed_tree":observed,"cpu_s":cpu,"wall_s":wall,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"module_path":str(Path(m.__file__).resolve()),"tree_owner_path":str(Path(tree_owner.__file__).resolve())},sort_keys=True))
'''


def _expected_module_path(module: str) -> Path:
    return (Path.cwd() / Path(*module.split("."))).with_suffix(".py").resolve()


def fresh_op(module: str, op: str, archive: Path, source: Path) -> dict:
    cp=subprocess.run(
        [sys.executable,"-c",_OP,module,op,str(archive.resolve()),str(source.resolve())],
        text=True,capture_output=True,check=False,env=dict(os.environ, PYTHONPATH=str(Path.cwd().resolve())),
    )
    if cp.returncode:
        raise RuntimeError(f"{module} {op} failed rc={cp.returncode}: {cp.stderr[-4000:]}")
    lines=[x for x in cp.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError(f"{module} {op} emitted no receipt")
    out=json.loads(lines[-1])
    if Path(out["module_path"]).resolve()!=_expected_module_path(module):
        raise RuntimeError(f"source leak {module}: {out['module_path']}")
    if Path(out["tree_owner_path"]).resolve()!=_expected_module_path(EG07_MODULE):
        raise RuntimeError(f"tree authority leak {module}: {out['tree_owner_path']}")
    if not out["ok"]:
        raise RuntimeError(f"{module} {op} semantic failure")
    return out


def med_ops(module: str, op: str, archive: Path, source: Path) -> dict:
    rows=[fresh_op(module,op,archive,source) for _ in range(REPS)]
    return {
        "repetitions":REPS,
        "cpu_s_median":statistics.median(float(x["cpu_s"]) for x in rows),
        "wall_s_median":statistics.median(float(x["wall_s"]) for x in rows),
        "peak_rss_kib_max":max(int(x["peak_rss_kib"]) for x in rows),
        "expected_tree":rows[0]["expected_tree"],
        "all_tree_identity":all(x["expected_tree"]==x["observed_tree"] for x in rows),
        "module_path":rows[0]["module_path"],
        "tree_owner_path":rows[0]["tree_owner_path"],
    }


def confirmed_reg(base: float, cand: float) -> bool:
    return cand > base*(1.0+REL) and cand > base+ABS_S


def one(family: str, source: Path, item: dict, work: Path) -> dict:
    a7=work/"eg07.cmpct"; a8=work/"eg08.cmpct"
    b7=fresh_build(EG07_MODULE,source,a7); b8=fresh_build(EG08_MODULE,source,a8)
    v7=bool((b7["result"].get("verified") or {}).get("ok")); v8=bool((b8["result"].get("verified") or {}).get("ok"))
    l7=b7["result"]["locality"]; l8=b8["result"]["locality"]
    geometry=(l7["member_count"]==l8["member_count"] and l7["max_decode_unit_bytes"]==l8["max_decode_unit_bytes"] and l7["max_member_read_amplification"]==l8["max_member_read_amplification"])
    ops={}
    for op in ("extract","verify"):
        r7=med_ops(EG07_MODULE,op,a7,source); r8=med_ops(EG08_MODULE,op,a8,source)
        ops[op]={
            "eg07":r7,"eg08":r8,
            "cpu_ratio":r8["cpu_s_median"]/max(r7["cpu_s_median"],1e-12),
            "wall_ratio":r8["wall_s_median"]/max(r7["wall_s_median"],1e-12),
            "rss_delta_kib":r8["peak_rss_kib_max"]-r7["peak_rss_kib_max"],
            "confirmed_cpu_regression":confirmed_reg(r7["cpu_s_median"],r8["cpu_s_median"]),
            "confirmed_wall_regression":confirmed_reg(r7["wall_s_median"],r8["wall_s_median"]),
        }
    return {
        "family":family,"name":item["name"],"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
        "eg07_bytes":b7["archive_bytes"],"eg08_bytes":b8["archive_bytes"],"saved_bytes":int(b7["archive_bytes"])-int(b8["archive_bytes"]),
        "build_strong_verify_eg07":v7,"build_strong_verify_eg08":v8,"geometry_same":geometry,
        "member_count":l8["member_count"],"max_amp":l8["max_member_read_amplification"],"max_decode_unit_bytes":l8["max_decode_unit_bytes"],
        "operations":ops,
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg08-read-cost.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-read-cost-") as td:
        work=Path(td); neutral=work/"neutral"; hostile=work/"hostile"; nm=CURRENT.build(neutral); hm=HOSTILE.build(hostile)
        surfaces=[]
        surfaces += [("neutral",neutral,x) for x in nm["corpora"] if x["name"] in NEUTRAL]
        surfaces += [("hostile",hostile,x) for x in hm["workloads"] if x["name"] in HOSTILE_NAMES]
        expected={f"neutral:{x}" for x in NEUTRAL}|{f"hostile:{x}" for x in HOSTILE_NAMES}
        actual={f"{f}:{x['name']}" for f,_r,x in surfaces}
        if actual!=expected: raise RuntimeError(f"surface drift expected={sorted(expected)} actual={sorted(actual)}")
        rows=[]
        for family,root,item in surfaces:
            w=work/f"{family}-{item['name']}"; w.mkdir(); rows.append(one(family,root/item["name"],item,w))
        conditions={
            "nine_workloads":len(rows)==9,
            "all_build_strong_verify":all(r["build_strong_verify_eg07"] and r["build_strong_verify_eg08"] for r in rows),
            "all_geometry_same":all(r["geometry_same"] for r in rows),
            "all_extract_tree_identity":all(r["operations"]["extract"]["eg07"]["all_tree_identity"] and r["operations"]["extract"]["eg08"]["all_tree_identity"] for r in rows),
            "zero_confirmed_extract_cpu_regressions":not any(r["operations"]["extract"]["confirmed_cpu_regression"] for r in rows),
            "zero_confirmed_extract_wall_regressions":not any(r["operations"]["extract"]["confirmed_wall_regression"] for r in rows),
            "zero_confirmed_verify_cpu_regressions":not any(r["operations"]["verify"]["confirmed_cpu_regression"] for r in rows),
            "zero_confirmed_verify_wall_regressions":not any(r["operations"]["verify"]["confirmed_wall_regression"] for r in rows),
        }
        verdict="EG08_READ_COST_SURVIVES" if all(conditions.values()) else "EG08_READ_COST_DEBT"
        out={
            "schema":"v030-eg08-read-cost-v2","verdict":verdict,"conditions":conditions,"timing_rule":{"relative":REL,"absolute_s":ABS_S,"repetitions":REPS},"workloads":rows,
            "aggregate_saved_bytes":sum(int(r["saved_bytes"]) for r in rows),
            "worst_extract_cpu_ratio":max(float(r["operations"]["extract"]["cpu_ratio"]) for r in rows),
            "worst_extract_wall_ratio":max(float(r["operations"]["extract"]["wall_ratio"]) for r in rows),
            "worst_verify_cpu_ratio":max(float(r["operations"]["verify"]["cpu_ratio"]) for r in rows),
            "worst_verify_wall_ratio":max(float(r["operations"]["verify"]["wall_ratio"]) for r in rows),
            "max_positive_reader_rss_delta_kib":max(0,max(max(int(r["operations"][op]["rss_delta_kib"]) for op in ("extract","verify")) for r in rows)),
        }
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
