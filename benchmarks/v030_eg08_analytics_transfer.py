from __future__ import annotations

"""Focused Analytics transfer for the frozen EG08 adaptive-effort mechanism."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks.v030_eg08_neutral10_transfer import fresh_build
from benchmarks.v030_office_physical_economics_referee import frozen_v029
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

NAME = "04_analytics_and_database"


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--v029-checkout",type=Path,required=True); ap.add_argument("--out",type=Path,default=Path("eg08-analytics-transfer.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-analytics-") as td:
        work=Path(td); corpus=work/"corpus"; manifest=CORPUS.build(corpus); source=corpus/NAME
        item=next(x for x in manifest["corpora"] if x["name"]==NAME)
        b7=fresh_build("experiments.entropygraph_v030_federated_embedded_fs_candidate_v7",source,work/"eg07.cmpct")
        b8=fresh_build("experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8",source,work/"eg08.cmpct")
        v29=frozen_v029(source,work/"v029.cmpct",args.v029_checkout)
        l7=b7["result"]["locality"]; l8=b8["result"]["locality"]
        geometry_same=(l7["member_count"]==l8["member_count"] and l7["max_decode_unit_bytes"]==l8["max_decode_unit_bytes"] and l7["max_member_read_amplification"]==l8["max_member_read_amplification"])
        verify=EG08.strong_verify(work/"eg08.cmpct",expected_tree=EG08.EG07._treehash(source))
        corrupt=work/"eg08-corrupt.cmpct"; shutil.copyfile(work/"eg08.cmpct",corrupt); raw=bytearray(corrupt.read_bytes()); raw[EG08.EG07.EG06.EG05.V25.HDR.size]^=1; corrupt.write_bytes(raw); recovery=EG08.strong_verify(corrupt,expected_tree=EG08.EG07._treehash(source))["ok"]
        saved=int(b7["archive_bytes"])-int(b8["archive_bytes"]); cpu_ratio_v29=float(b8["create_cpu_s"])/max(float(v29["create_cpu_s"]),1e-9)
        conditions={
            "strong_verify":bool(verify.get("ok")),"tail_recovery":bool(recovery),"locality_geometry_unchanged":geometry_same,
            "strict_byte_win_vs_eg07":saved>0,"at_least_10x_faster_than_v029":cpu_ratio_v29<=0.10,
        }
        verdict="EG08_ANALYTICS_TRANSFER_PASSES" if all(conditions.values()) else "EG08_ANALYTICS_TRANSFER_BLOCKED"
        out={
            "schema":"v030-eg08-analytics-transfer-v1","verdict":verdict,"conditions":conditions,"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
            "eg07":b7,"eg08":b8,"frozen_v029":v29,"saved_vs_eg07_bytes":saved,"eg08_delta_vs_v029_bytes":int(b8["archive_bytes"])-int(v29["archive_bytes"]),"eg08_cpu_ratio_vs_v029":cpu_ratio_v29,"locality":l8,
        }
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
