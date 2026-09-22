from __future__ import annotations

"""Counterfactual replay of EG08's observed effort traces with stop-on-tie."""

import argparse
import json
from pathlib import Path
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build

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


def replay(pack: dict) -> dict:
    incumbent=int(pack["current_payload_bytes"])
    attempts=0
    for row in pack.get("tried", []):
        attempts += 1
        size=int(row["storage_bytes"])
        if size < incumbent:
            incumbent=size
            continue
        # Counterfactual: ties and worse results terminate immediately.
        break
    actual=int(pack["selected_payload_bytes"])
    return {
        "index":int(pack["index"]),
        "actual_selected_bytes":actual,
        "stop_on_tie_selected_bytes":incumbent,
        "byte_loss":incumbent-actual,
        "actual_attempts":len(pack.get("tried", [])),
        "stop_on_tie_attempts":attempts,
        "attempts_avoided":len(pack.get("tried", []))-attempts,
    }


def one(family: str, source: Path, item: dict, work: Path) -> dict:
    build=fresh_build(EG08_MODULE,source,work/"eg08.cmpct")
    result=build["result"]
    if not bool((result.get("verified") or {}).get("ok")):
        raise RuntimeError(f"EG08 verify failed on {family}:{item['name']}")
    locality=result["locality"]
    if not bool(locality.get("within_release_bounds")):
        raise RuntimeError(f"EG08 locality failed on {family}:{item['name']}")
    traces=[replay(p) for p in result["adaptive_effort"]["packs"]]
    changed=[x for x in traces if x["byte_loss"]>0]
    return {
        "family":family,
        "name":item["name"],
        "tree_sha256":item["tree_sha256"],
        "logical_bytes":item["logical_bytes"],
        "files":item["files"],
        "eg08_archive_bytes":build["archive_bytes"],
        "eg08_physical_saved_bytes":result["adaptive_effort"]["physical_bytes_saved"],
        "actual_attempts":sum(x["actual_attempts"] for x in traces),
        "stop_on_tie_attempts":sum(x["stop_on_tie_attempts"] for x in traces),
        "attempts_avoided":sum(x["attempts_avoided"] for x in traces),
        "packs_requiring_tie_crossing":len(changed),
        "bytes_depending_on_tie_crossing":sum(x["byte_loss"] for x in traces),
        "counterexamples":changed,
        "max_amp":locality["max_member_read_amplification"],
        "max_decode_unit_bytes":locality["max_decode_unit_bytes"],
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg08-tie-attribution.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-tie-attribution-") as td:
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
        lost=sum(int(r["bytes_depending_on_tie_crossing"]) for r in rows)
        avoided=sum(int(r["attempts_avoided"]) for r in rows)
        counterpacks=sum(int(r["packs_requiring_tie_crossing"]) for r in rows)
        h0=(lost==0 and counterpacks==0 and avoided>0)
        verdict="EG08_TIE_CONTINUATION_REDUNDANT" if h0 else "EG08_TIE_CONTINUATION_CARRIES_DENSITY"
        out={
            "schema":"v030-eg08-tie-continuation-attribution-v1",
            "verdict":verdict,
            "h0_exact_same_selected_bytes":lost==0 and counterpacks==0,
            "aggregate_attempts_avoided":avoided,
            "aggregate_bytes_depending_on_tie_crossing":lost,
            "aggregate_packs_requiring_tie_crossing":counterpacks,
            "workloads":rows,
        }
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
