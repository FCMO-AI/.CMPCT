from __future__ import annotations

"""Fresh-process Office Builder gate for C25EG08 adaptive physical effort."""

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

OFFICE_TREE = "ba72464747d4e3c129d91077c30f0c17c97fcb9bf5fc997cfe7001e234998934"
ORACLE_SAVING = 484_719


def fresh_build(module: str, source: Path, archive: Path) -> dict:
    code = r'''
import importlib,json,resource,time,sys
from pathlib import Path
name=sys.argv[1]; source=Path(sys.argv[2]); out=Path(sys.argv[3])
m=importlib.import_module(name)
c0=time.process_time(); w0=time.perf_counter(); result=m.build(source,out); cpu=time.process_time()-c0; wall=time.perf_counter()-w0
print(json.dumps({
  'module':name,
  'module_path':str(Path(m.__file__).resolve()),
  'archive_bytes':out.stat().st_size,
  'create_cpu_s':cpu,
  'create_wall_s':wall,
  'peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
  'result':result,
},default=str,sort_keys=True))
'''
    env = dict(os.environ); env["PYTHONNOUSERSITE"] = "1"
    p = subprocess.run(
        [sys.executable, "-c", code, module, str(source), str(archive)],
        check=True, capture_output=True, text=True, env=env,
    )
    return json.loads(p.stdout.strip().splitlines()[-1])


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--v029-checkout",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("office-adaptive-effort-builder.json"))
    args=ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="cmpct-office-eg08-") as td:
        work=Path(td); corpus=work/"corpus"; manifest=CORPUS.build(corpus)
        source=corpus/"02_office_workspace"
        office=next(x for x in manifest["corpora"] if x["name"]==source.name)
        if office["tree_sha256"] != OFFICE_TREE:
            raise RuntimeError("EG08 mission-lock Office tree changed; rerun attribution before Builder")

        eg07_path=work/"eg07.cmpct"; eg08_path=work/"eg08.cmpct"; v029_path=work/"v029.cmpct"
        eg07=fresh_build("experiments.entropygraph_v030_federated_embedded_fs_candidate_v7",source,eg07_path)
        eg08=fresh_build("experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8",source,eg08_path)
        v029=frozen_v029(source,v029_path,args.v029_checkout)

        verify=EG08.strong_verify(eg08_path, expected_tree=EG08.EG07._treehash(source))
        locality=EG08.locality_report(eg08_path)
        base_loc=eg07["result"]["locality"]
        locality_same=(
            locality["max_decode_unit_bytes"]==base_loc["max_decode_unit_bytes"]
            and locality["max_member_read_amplification"]==base_loc["max_member_read_amplification"]
            and locality["member_count"]==base_loc["member_count"]
        )

        corrupt=work/"eg08-primary-corrupt.cmpct"; shutil.copyfile(eg08_path,corrupt)
        raw=bytearray(corrupt.read_bytes()); raw[EG08.EG07.EG06.EG05.V25.HDR.size] ^= 1; corrupt.write_bytes(raw)
        recovery=EG08.strong_verify(corrupt, expected_tree=EG08.EG07._treehash(source))["ok"]

        recovered=int(eg07["archive_bytes"])-int(eg08["archive_bytes"])
        realization=recovered/ORACLE_SAVING
        cpu_ratio=float(eg08["create_cpu_s"])/max(float(v029["create_cpu_s"]),1e-9)
        conditions={
            "strong_verify": bool(verify.get("ok")),
            "tail_recovery": bool(recovery),
            "locality_geometry_unchanged": bool(locality_same),
            "oracle_realization_ge_80pct": realization >= 0.80,
            "strictly_smaller_than_frozen_v029": int(eg08["archive_bytes"]) < int(v029["archive_bytes"]),
            "at_least_10x_faster_cpu_than_v029": cpu_ratio <= 0.10,
        }
        verdict="EG08_OFFICE_BUILDER_PASSES" if all(conditions.values()) else "EG08_OFFICE_BUILDER_REJECTED"
        out={
            "schema":"v030-office-adaptive-effort-builder-v1",
            "verdict":verdict,
            "office_tree_sha256":office["tree_sha256"],
            "logical_bytes":office["logical_bytes"],
            "oracle_saving_bytes":ORACLE_SAVING,
            "eg07":eg07,
            "eg08":eg08,
            "frozen_v029":v029,
            "actual_recovered_vs_eg07_bytes":recovered,
            "oracle_realization_fraction":realization,
            "eg08_cpu_ratio_vs_v029":cpu_ratio,
            "locality":locality,
            "tail_recovery":recovery,
            "conditions":conditions,
        }
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
        print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
