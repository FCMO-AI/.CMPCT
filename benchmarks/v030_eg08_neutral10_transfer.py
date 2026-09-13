from __future__ import annotations

"""Fresh-process neutral10 transfer referee for EG08 adaptive physical effort."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks.v030_office_physical_economics_referee import frozen_v029
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

ANALYTICS = "04_analytics_and_database"


def fresh_build(module: str, source: Path, archive: Path) -> dict:
    code = r'''
import importlib,json,resource,time,sys,traceback
from pathlib import Path
try:
    m=importlib.import_module(sys.argv[1]); source=Path(sys.argv[2]); out=Path(sys.argv[3])
    c0=time.process_time(); w0=time.perf_counter(); result=m.build(source,out); cpu=time.process_time()-c0; wall=time.perf_counter()-w0
    print(json.dumps({
      'module':sys.argv[1], 'module_path':str(Path(m.__file__).resolve()),
      'archive_bytes':out.stat().st_size, 'create_cpu_s':cpu, 'create_wall_s':wall,
      'peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), 'result':result,
    },default=str,sort_keys=True))
except Exception:
    traceback.print_exc()
    raise
'''
    env=dict(os.environ); env["PYTHONNOUSERSITE"]="1"
    p=subprocess.run([sys.executable,"-c",code,module,str(source),str(archive)],capture_output=True,text=True,env=env)
    if p.returncode != 0:
        raise RuntimeError(
            f"fresh-build failure module={module} source={source.name} rc={p.returncode}\n"
            f"--- child stdout ---\n{p.stdout}\n--- child stderr ---\n{p.stderr}"
        )
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:
        raise RuntimeError(
            f"fresh-build emitted no parseable receipt module={module} source={source.name}\n"
            f"--- child stdout ---\n{p.stdout}\n--- child stderr ---\n{p.stderr}"
        ) from exc


def tail_recovery(archive: Path, source: Path, work: Path) -> bool:
    corrupt=work/(archive.stem+"-primary-corrupt.cmpct"); shutil.copyfile(archive,corrupt)
    raw=bytearray(corrupt.read_bytes()); raw[EG08.EG07.EG06.EG05.V25.HDR.size] ^= 1; corrupt.write_bytes(raw)
    try:
        return bool(EG08.strong_verify(corrupt, expected_tree=EG08.EG07._treehash(source))["ok"])
    finally:
        corrupt.unlink(missing_ok=True)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--v029-checkout",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("eg08-neutral10-transfer.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-neutral10-") as td:
        work=Path(td); corpus=work/"corpus"; manifest=CORPUS.build(corpus)
        rows=[]; analytics_v029=None
        for item in manifest["corpora"]:
            name=item["name"]; source=corpus/name; w=work/name; w.mkdir()
            b7=fresh_build("experiments.entropygraph_v030_federated_embedded_fs_candidate_v7",source,w/"eg07.cmpct")
            b8=fresh_build("experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8",source,w/"eg08.cmpct")
            loc7=b7["result"]["locality"]; loc8=b8["result"]["locality"]
            geometry_same=(loc7["member_count"]==loc8["member_count"] and loc7["max_decode_unit_bytes"]==loc8["max_decode_unit_bytes"] and loc7["max_member_read_amplification"]==loc8["max_member_read_amplification"])
            recovery=tail_recovery(w/"eg08.cmpct",source,w)
            saved=int(b7["archive_bytes"])-int(b8["archive_bytes"])
            cpu_ratio=float(b8["create_cpu_s"])/max(float(b7["create_cpu_s"]),1e-9)
            rss_delta=int(b8["peak_rss_kib"])-int(b7["peak_rss_kib"])
            effort=b8["result"]["adaptive_effort"]
            row={
                "name":name,"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
                "eg07_bytes":b7["archive_bytes"],"eg08_bytes":b8["archive_bytes"],"saved_bytes":saved,
                "eg07_cpu_s":b7["create_cpu_s"],"eg08_cpu_s":b8["create_cpu_s"],"cpu_ratio":cpu_ratio,
                "eg07_wall_s":b7["create_wall_s"],"eg08_wall_s":b8["create_wall_s"],
                "eg07_peak_rss_kib":b7["peak_rss_kib"],"eg08_peak_rss_kib":b8["peak_rss_kib"],"rss_delta_kib":rss_delta,
                "geometry_same":geometry_same,"tail_recovery":recovery,
                "max_amp":loc8["max_member_read_amplification"],"max_decode_unit_bytes":loc8["max_decode_unit_bytes"],"member_count":loc8["member_count"],
                "effort_attempts":effort["effort_attempts"],"early_stops":effort["early_stops"],"selected_levels":effort["selected_levels"],"changed_packs":effort["changed_packs"],"repack_cpu_s":effort["repack_cpu_s"],
            }
            if name==ANALYTICS:
                analytics_v029=frozen_v029(source,w/"v029.cmpct",args.v029_checkout)
                row["frozen_v029_bytes"]=analytics_v029["archive_bytes"]
                row["frozen_v029_cpu_s"]=analytics_v029["create_cpu_s"]
                row["eg08_cpu_ratio_vs_v029"]=float(b8["create_cpu_s"])/max(float(analytics_v029["create_cpu_s"]),1e-9)
                row["eg08_delta_vs_v029_bytes"]=int(b8["archive_bytes"])-int(analytics_v029["archive_bytes"])
            rows.append(row)

        zero_regressions=all(r["saved_bytes"]>=0 for r in rows)
        all_geometry=all(r["geometry_same"] for r in rows)
        all_recovery=all(r["tail_recovery"] for r in rows)
        analytics=next(r for r in rows if r["name"]==ANALYTICS)
        low_yield_cpu_ok=all(not (r["saved_bytes"]<4096 and r["cpu_ratio"]>1.50) for r in rows)
        conditions={
            "ten_workloads":len(rows)==10,
            "zero_stored_byte_regressions":zero_regressions,
            "all_locality_geometry_unchanged":all_geometry,
            "all_tail_recovery":all_recovery,
            "analytics_strict_eg07_byte_win":analytics["saved_bytes"]>0,
            "analytics_at_least_10x_faster_than_v029":analytics.get("eg08_cpu_ratio_vs_v029",999)<=0.10,
            "low_yield_cpu_export_cost_ok":low_yield_cpu_ok,
        }
        verdict="EG08_NEUTRAL10_TRANSFER_PASSES" if all(conditions.values()) else "EG08_NEUTRAL10_TRANSFER_BLOCKED"
        out={
            "schema":"v030-eg08-neutral10-transfer-v1","verdict":verdict,"conditions":conditions,"workloads":rows,
            "aggregate_eg07_bytes":sum(int(r["eg07_bytes"]) for r in rows),"aggregate_eg08_bytes":sum(int(r["eg08_bytes"]) for r in rows),
            "aggregate_saved_bytes":sum(int(r["saved_bytes"]) for r in rows),
            "worst_cpu_ratio":max(float(r["cpu_ratio"]) for r in rows),"max_positive_rss_delta_kib":max(0,max(int(r["rss_delta_kib"]) for r in rows)),
            "analytics_frozen_v029":analytics_v029,
        }
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
