from __future__ import annotations

"""Transfer EG08 across the independently mapped EG07-valid nine surfaces."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build
from benchmarks.v030_office_physical_economics_referee import frozen_v029
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

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
ANALYTICS = "04_analytics_and_database"


def tail_recovery(archive: Path, source: Path, work: Path) -> bool:
    corrupt=work/(archive.stem+"-primary-corrupt.cmpct"); shutil.copyfile(archive,corrupt)
    raw=bytearray(corrupt.read_bytes()); raw[EG08.EG07.EG06.EG05.V25.HDR.size] ^= 1; corrupt.write_bytes(raw)
    try: return bool(EG08.strong_verify(corrupt,expected_tree=EG08.EG07._treehash(source))["ok"])
    finally: corrupt.unlink(missing_ok=True)


def one(family: str, source: Path, item: dict, work: Path, v029_checkout: Path | None) -> tuple[dict, dict | None]:
    b7=fresh_build("experiments.entropygraph_v030_federated_embedded_fs_candidate_v7",source,work/"eg07.cmpct")
    b8=fresh_build("experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8",source,work/"eg08.cmpct")
    l7=b7["result"]["locality"]; l8=b8["result"]["locality"]
    same=(l7["member_count"]==l8["member_count"] and l7["max_decode_unit_bytes"]==l8["max_decode_unit_bytes"] and l7["max_member_read_amplification"]==l8["max_member_read_amplification"])
    saved=int(b7["archive_bytes"])-int(b8["archive_bytes"]); cpu_ratio=float(b8["create_cpu_s"])/max(float(b7["create_cpu_s"]),1e-9)
    rec=tail_recovery(work/"eg08.cmpct",source,work); effort=b8["result"]["adaptive_effort"]
    row={
        "family":family,"name":item["name"],"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
        "eg07_bytes":b7["archive_bytes"],"eg08_bytes":b8["archive_bytes"],"saved_bytes":saved,
        "eg07_cpu_s":b7["create_cpu_s"],"eg08_cpu_s":b8["create_cpu_s"],"cpu_ratio":cpu_ratio,
        "eg07_wall_s":b7["create_wall_s"],"eg08_wall_s":b8["create_wall_s"],
        "eg07_peak_rss_kib":b7["peak_rss_kib"],"eg08_peak_rss_kib":b8["peak_rss_kib"],"rss_delta_kib":int(b8["peak_rss_kib"])-int(b7["peak_rss_kib"]),
        "geometry_same":same,"tail_recovery":rec,"max_amp":l8["max_member_read_amplification"],"max_decode_unit_bytes":l8["max_decode_unit_bytes"],"member_count":l8["member_count"],
        "changed_packs":effort["changed_packs"],"effort_attempts":effort["effort_attempts"],"early_stops":effort["early_stops"],"selected_levels":effort["selected_levels"],"repack_cpu_s":effort["repack_cpu_s"],
    }
    v29=None
    if item["name"]==ANALYTICS:
        assert v029_checkout is not None
        v29=frozen_v029(source,work/"v029.cmpct",v029_checkout)
        row["frozen_v029_bytes"]=v29["archive_bytes"]
        row["frozen_v029_cpu_s"]=v29["create_cpu_s"]
        row["eg08_cpu_ratio_vs_v029"]=float(b8["create_cpu_s"])/max(float(v29["create_cpu_s"]),1e-9)
        row["eg08_delta_vs_v029_bytes"]=int(b8["archive_bytes"])-int(v29["archive_bytes"])
    return row,v29


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--v029-checkout",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("eg08-eligible9-transfer.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-eligible9-") as td:
        work=Path(td); neutral=work/"neutral"; hostile=work/"hostile"; nm=CURRENT.build(neutral); hm=HOSTILE.build(hostile)
        rows=[]; analytics_v29=None
        surfaces=[]
        surfaces += [("neutral",neutral,x) for x in nm["corpora"] if x["name"] in NEUTRAL]
        surfaces += [("hostile",hostile,x) for x in hm["workloads"] if x["name"] in HOSTILE_NAMES]
        expected={f"neutral:{x}" for x in NEUTRAL}|{f"hostile:{x}" for x in HOSTILE_NAMES}
        actual={f"{f}:{x['name']}" for f,_r,x in surfaces}
        if actual!=expected: raise RuntimeError(f"eligible9 surface drift expected={sorted(expected)} actual={sorted(actual)}")
        for family,root,item in surfaces:
            w=work/f"{family}-{item['name']}"; w.mkdir(); row,v29=one(family,root/item["name"],item,w,args.v029_checkout); rows.append(row); analytics_v29=v29 or analytics_v29
        non_office_wins=sum(1 for r in rows if r["name"]!="02_office_workspace" and r["saved_bytes"]>0)
        analytics=next(r for r in rows if r["name"]==ANALYTICS)
        conditions={
            "nine_workloads":len(rows)==9,
            "zero_stored_byte_regressions":all(r["saved_bytes"]>=0 for r in rows),
            "all_locality_geometry_unchanged":all(r["geometry_same"] for r in rows),
            "all_tail_recovery":all(r["tail_recovery"] for r in rows),
            "at_least_two_non_office_strict_wins":non_office_wins>=2,
            "analytics_strict_eg07_byte_win":analytics["saved_bytes"]>0,
            "analytics_at_least_10x_faster_than_v029":analytics.get("eg08_cpu_ratio_vs_v029",999)<=0.10,
            "low_yield_cpu_export_cost_ok":all(not (r["saved_bytes"]<4096 and r["cpu_ratio"]>1.50) for r in rows),
        }
        verdict="EG08_ELIGIBLE9_TRANSFER_PASSES" if all(conditions.values()) else "EG08_ELIGIBLE9_TRANSFER_BLOCKED"
        out={
            "schema":"v030-eg08-eligible9-transfer-v1","verdict":verdict,"conditions":conditions,"workloads":rows,"non_office_strict_win_count":non_office_wins,
            "aggregate_eg07_bytes":sum(int(r["eg07_bytes"]) for r in rows),"aggregate_eg08_bytes":sum(int(r["eg08_bytes"]) for r in rows),"aggregate_saved_bytes":sum(int(r["saved_bytes"]) for r in rows),
            "worst_cpu_ratio":max(float(r["cpu_ratio"]) for r in rows),"max_positive_rss_delta_kib":max(0,max(int(r["rss_delta_kib"]) for r in rows)),"analytics_frozen_v029":analytics_v29,
        }
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
