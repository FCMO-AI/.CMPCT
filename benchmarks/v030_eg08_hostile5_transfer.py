from __future__ import annotations

"""Hostile-five transfer referee for EG08 adaptive physical effort."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08


def fresh_build(module: str, source: Path, archive: Path) -> dict:
    code = r'''
import importlib,json,resource,time,sys,traceback
from pathlib import Path
try:
    m=importlib.import_module(sys.argv[1]); source=Path(sys.argv[2]); out=Path(sys.argv[3])
    c0=time.process_time(); w0=time.perf_counter(); result=m.build(source,out); cpu=time.process_time()-c0; wall=time.perf_counter()-w0
    print(json.dumps({'module':sys.argv[1],'module_path':str(Path(m.__file__).resolve()),'archive_bytes':out.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall,'peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'result':result},default=str,sort_keys=True))
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


def recovery(archive: Path, source: Path, work: Path) -> bool:
    corrupt=work/(archive.stem+"-primary-corrupt.cmpct"); shutil.copyfile(archive,corrupt)
    raw=bytearray(corrupt.read_bytes()); raw[EG08.EG07.EG06.EG05.V25.HDR.size] ^= 1; corrupt.write_bytes(raw)
    try: return bool(EG08.strong_verify(corrupt,expected_tree=EG08.EG07._treehash(source))["ok"])
    finally: corrupt.unlink(missing_ok=True)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg08-hostile5-transfer.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-hostile5-") as td:
        work=Path(td); corpus=work/"corpus"; manifest=HOSTILE.build(corpus); rows=[]
        for item in manifest["workloads"]:
            name=item["name"]; source=corpus/name; w=work/name; w.mkdir()
            b7=fresh_build("experiments.entropygraph_v030_federated_embedded_fs_candidate_v7",source,w/"eg07.cmpct")
            b8=fresh_build("experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8",source,w/"eg08.cmpct")
            l7=b7["result"]["locality"]; l8=b8["result"]["locality"]
            same=(l7["member_count"]==l8["member_count"] and l7["max_decode_unit_bytes"]==l8["max_decode_unit_bytes"] and l7["max_member_read_amplification"]==l8["max_member_read_amplification"])
            saved=int(b7["archive_bytes"])-int(b8["archive_bytes"]); ratio=float(b8["create_cpu_s"])/max(float(b7["create_cpu_s"]),1e-9); rec=recovery(w/"eg08.cmpct",source,w); effort=b8["result"]["adaptive_effort"]
            rows.append({
              "name":name,"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
              "eg07_bytes":b7["archive_bytes"],"eg08_bytes":b8["archive_bytes"],"saved_bytes":saved,
              "eg07_cpu_s":b7["create_cpu_s"],"eg08_cpu_s":b8["create_cpu_s"],"cpu_ratio":ratio,"eg07_wall_s":b7["create_wall_s"],"eg08_wall_s":b8["create_wall_s"],
              "eg07_peak_rss_kib":b7["peak_rss_kib"],"eg08_peak_rss_kib":b8["peak_rss_kib"],"rss_delta_kib":int(b8["peak_rss_kib"])-int(b7["peak_rss_kib"]),
              "geometry_same":same,"tail_recovery":rec,"max_amp":l8["max_member_read_amplification"],"max_decode_unit_bytes":l8["max_decode_unit_bytes"],
              "changed_packs":effort["changed_packs"],"effort_attempts":effort["effort_attempts"],"early_stops":effort["early_stops"],"selected_levels":effort["selected_levels"],"repack_cpu_s":effort["repack_cpu_s"],
            })
        conditions={
          "five_workloads":len(rows)==5,
          "zero_stored_byte_regressions":all(r["saved_bytes"]>=0 for r in rows),
          "all_locality_geometry_unchanged":all(r["geometry_same"] for r in rows),
          "all_tail_recovery":all(r["tail_recovery"] for r in rows),
          "low_yield_cpu_export_cost_ok":all(not (r["saved_bytes"]<4096 and r["cpu_ratio"]>1.50) for r in rows),
        }
        verdict="EG08_HOSTILE5_PASSES" if all(conditions.values()) else "EG08_HOSTILE5_BLOCKED"
        out={"schema":"v030-eg08-hostile5-v1","verdict":verdict,"conditions":conditions,"workloads":rows,"aggregate_eg07_bytes":sum(int(r["eg07_bytes"]) for r in rows),"aggregate_eg08_bytes":sum(int(r["eg08_bytes"]) for r in rows),"aggregate_saved_bytes":sum(int(r["saved_bytes"]) for r in rows),"worst_cpu_ratio":max(float(r["cpu_ratio"]) for r in rows),"max_positive_rss_delta_kib":max(0,max(int(r["rss_delta_kib"]) for r in rows))}
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
