from __future__ import annotations

"""SFV4 deterministic-build referee.

Two exact-head hosted receipts on the same repaired Office tree reported 6,506,050 B and
6,506,052 B before locality metadata.  `streams.bin` was identical at 5,658,164 B, so
the 2-byte drift is in the non-stream/control side.  This referee does not change any
representation.  It builds SFV4 twice from one normalized source tree into independent
work directories and compares every emitted component by size and SHA-256.

H-REPRO: same tree + same source + same process contract => byte-identical SFV4 bundle.
Any component mismatch is a harness/product-research determinism defect and must not be
misreported as compression noise.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA="cmpct-v030-r4-office-sfv4-reproducibility-referee-v1"


def _inventory(root: Path) -> dict:
    out={}
    for p in sorted(q for q in root.iterdir() if q.is_file()):
        b=p.read_bytes(); out[p.name]={"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
    return out


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_office_sfv4_repro_neutral")
    repair=V029._load(V029.REPAIR_PATH,"r4_office_sfv4_repro_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"02_office_workspace"
    expected=PRODUCT.treehash(source)
    a=SFV4.build_candidate(source,work/"a",work/"a-work")
    b=SFV4.build_candidate(source,work/"b",work/"b-work")
    ia=_inventory(work/"a"); ib=_inventory(work/"b")
    names=sorted(set(ia)|set(ib)); mismatch={n:{"a":ia.get(n),"b":ib.get(n)} for n in names if ia.get(n)!=ib.get(n)}
    return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"tree_sha256":expected,
            "build_a_bytes":int(a["stored_bytes"]),"build_b_bytes":int(b["stored_bytes"]),"inventory_a":ia,"inventory_b":ib,
            "component_mismatches":mismatch,"hypothesis":{"byte_identical_rebuild":not mismatch and a["stored_bytes"]==b["stored_bytes"]},
            "contract":{"diagnostic_only":True,"release_credit":False,"format_changed":False,"selector_changed":False,"thresholds_changed":False,
                        "note":"Any mismatch is determinism debt, not benchmark noise."}}


def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-sfv4-repro-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-sfv4-repro.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"build_a_bytes":d["build_a_bytes"],"build_b_bytes":d["build_b_bytes"],"component_mismatches":d["component_mismatches"],"hypothesis":d["hypothesis"]},indent=2))

if __name__=="__main__":main()
