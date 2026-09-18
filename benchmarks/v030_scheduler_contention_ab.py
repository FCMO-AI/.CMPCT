from __future__ import annotations

"""Balanced paired causal oracle for v0.30 release-candidate scheduler contention.

Research-only. It compares the exact shipping candidate builders under current co-scheduling
versus fresh-process isolation. Candidate hashes/tree identity must match. No product/release
credit is granted by this oracle. Worker failures retain stderr so infrastructure defects are causal.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF

ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/"benchmarks"/"v030_scheduler_contention_worker.py"
TARGETS=(
    ("neutral_hostile_v1","09_ml_artifacts","g04",0.101),
    ("resemblance_hostile_v1","01_shifted_versions","prefixgraph",0.036),
)
PAIR_ORDERS=(
    ("concurrent","solo"),
    ("solo","concurrent"),
    ("solo","concurrent"),
    ("concurrent","solo"),
)


def _worker(mode: str, source: Path, work: Path) -> dict:
    env=os.environ.copy()
    env["PYTHONPATH"]=str(ROOT)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cp=subprocess.run(
        [sys.executable,str(WORKER),"--mode",mode,"--source",str(source),"--work",str(work)],
        cwd=ROOT,env=env,check=False,capture_output=True,text=True,
    )
    if cp.returncode:
        raise RuntimeError(
            f"worker failed mode={mode!r} source={source} rc={cp.returncode}; "
            f"stdout={cp.stdout!r}; stderr={cp.stderr!r}"
        )
    lines=[x for x in cp.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError(f"worker emitted no JSON: {cp.stderr!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root,ignore_errors=True); work_root.mkdir(parents=True)
    corpora=PERF._build_corpora(work_root/"corpus")
    rows=[]
    for suite,name,selected_expected,product_gap_fraction in TARGETS:
        source=corpora[(suite,name)]
        pairs=[]
        for pair_index,order in enumerate(PAIR_ORDERS):
            arms={}
            for slot,arm in enumerate(order):
                mode="concurrent" if arm=="concurrent" else selected_expected
                arms[arm]=_worker(mode,source,work_root/"runs"/name/f"pair-{pair_index}-{slot}-{arm}")
            concurrent=arms["concurrent"]; solo=arms["solo"]
            if concurrent["selected"] != selected_expected:
                raise RuntimeError(f"{name}: selected candidate drift {concurrent['selected']} != {selected_expected}")
            if concurrent["selected_sha256"] != solo["physical_sha256"]:
                raise RuntimeError(f"{name}: isolated selected-candidate bytes differ from co-scheduled bytes")
            if int(concurrent["selected_bytes"]) != int(solo["archive_bytes"]):
                raise RuntimeError(f"{name}: isolated selected-candidate size differs")
            cwall=float(concurrent["selected_candidate_wall_s"]); swall=float(solo["candidate_wall_s"])
            pairs.append({
                "pair":pair_index,
                "order":list(order),
                "concurrent":concurrent,
                "solo":solo,
                "selected_candidate_contention_ratio":cwall/max(swall,1e-9),
                "selected_candidate_solo_saving_s":cwall-swall,
                "selected_candidate_solo_saving_fraction":1.0-swall/max(cwall,1e-9),
            })
        savings=[p["selected_candidate_solo_saving_fraction"] for p in pairs]
        abs_s=[p["selected_candidate_solo_saving_s"] for p in pairs]
        rows.append({
            "suite":suite,"name":name,"selected_candidate":selected_expected,
            "product_create_gap_fraction_context_only":product_gap_fraction,
            "pairs":pairs,
            "median_selected_candidate_solo_saving_fraction":float(statistics.median(savings)),
            "median_selected_candidate_solo_saving_s":float(statistics.median(abs_s)),
            "min_selected_candidate_solo_saving_fraction":float(min(savings)),
            "max_selected_candidate_solo_saving_fraction":float(max(savings)),
        })
    return {
        "schema":"cmpct-v030-scheduler-contention-oracle-v1",
        "release_credit":False,
        "pair_orders":[list(x) for x in PAIR_ORDERS],
        "rows":rows,
        "claim_boundary":"Paired mechanism evidence for selected-candidate slowdown under outer co-scheduling. It does not prove an implementable full-product speedup or unlock any release gate.",
        "preregistered_interpretation":"Material positive headroom requires a stable selected-candidate isolation advantage large enough to plausibly address the current product create gap; otherwise contention is secondary/negative and intrinsic/shared-work architecture remains primary.",
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
