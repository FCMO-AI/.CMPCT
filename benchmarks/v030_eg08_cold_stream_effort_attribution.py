from __future__ import annotations

"""Attribute EG08 selected-byte savings to cold stream packs on eligible-nine."""

import argparse
import json
from pathlib import Path
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build

EG08_MODULE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8"
NEUTRAL = {"02_office_workspace","04_analytics_and_database","05_logs_and_telemetry","09_ml_artifacts","10_large_mixed_binary"}
HOSTILE_NAMES = {"01_shifted_versions","02_false_neighbors","03_boundary_churn","05_incompressible"}


def one(family: str, source: Path, item: dict, work: Path) -> dict:
    build=fresh_build(EG08_MODULE,source,work/"eg08.cmpct")
    result=build["result"]
    if not bool((result.get("verified") or {}).get("ok")):
        raise RuntimeError(f"EG08 verify failed on {family}:{item['name']}")
    loc=result["locality"]
    if not bool(loc.get("within_release_bounds")):
        raise RuntimeError(f"EG08 locality failed on {family}:{item['name']}")
    packs=[p for p in result["adaptive_effort"]["packs"] if p.get("stream_pack") and not p.get("hot_stream_root")]
    changed=[p for p in packs if int(p.get("saved_bytes",0))>0]
    levels={}
    for p in changed:
        level=str(p.get("selected_level","current")); levels[level]=levels.get(level,0)+1
    return {
        "family":family,"name":item["name"],"tree_sha256":item["tree_sha256"],
        "cold_stream_pack_count":len(packs),"changed_cold_stream_pack_count":len(changed),
        "cold_stream_saved_bytes":sum(int(p.get("saved_bytes",0)) for p in changed),
        "selected_levels":levels,
        "counterexamples":[{"index":int(p["index"]),"saved_bytes":int(p["saved_bytes"]),"selected_level":p["selected_level"],"current_payload_bytes":int(p["current_payload_bytes"]),"selected_payload_bytes":int(p["selected_payload_bytes"])} for p in changed],
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg08-cold-stream-attribution.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-cold-stream-") as td:
        work=Path(td); neutral=work/"neutral"; hostile=work/"hostile"; nm=CURRENT.build(neutral); hm=HOSTILE.build(hostile)
        surfaces=[*(('neutral',neutral,x) for x in nm['corpora'] if x['name'] in NEUTRAL),*(('hostile',hostile,x) for x in hm['workloads'] if x['name'] in HOSTILE_NAMES)]
        expected={f"neutral:{x}" for x in NEUTRAL}|{f"hostile:{x}" for x in HOSTILE_NAMES}; actual={f"{f}:{x['name']}" for f,_r,x in surfaces}
        if actual!=expected: raise RuntimeError(f"surface drift expected={sorted(expected)} actual={sorted(actual)}")
        rows=[]
        for family,root,item in surfaces:
            w=work/f"{family}-{item['name']}"; w.mkdir(); rows.append(one(family,root/item['name'],item,w))
        changed=sum(int(r["changed_cold_stream_pack_count"]) for r in rows); saved=sum(int(r["cold_stream_saved_bytes"]) for r in rows)
        verdict="EG08_COLD_STREAM_EFFORT_UNUSED" if changed==0 and saved==0 else "EG08_COLD_STREAM_EFFORT_CARRIES_DENSITY"
        out={"schema":"v030-eg08-cold-stream-attribution-v1","verdict":verdict,"aggregate_cold_stream_pack_count":sum(int(r['cold_stream_pack_count']) for r in rows),"aggregate_changed_cold_stream_pack_count":changed,"aggregate_cold_stream_saved_bytes":saved,"workloads":rows}
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
