from __future__ import annotations

"""Trace pre-encode state for the deflate-family zero-group side effect."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import resemblance_hostile_corpus_v1 as RESEMBLANCE
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from cmpct import builder as BUILDER
from experiments import entropygraph_v030_release_product as PRODUCT


def snapshot(builder: BUILDER.Builder) -> dict:
    candidates=[]
    for h,c in sorted(builder.cands.items()):
        candidates.append({
            "sha256": bytes(h).hex(),
            "raw_bytes": len(c.raw),
            "hints": sorted(str(x) for x in c.hints),
            "deflates": len(c.deflates),
        })
    storages={}
    for row in builder.files:
        tag="none" if not row[6] else str(int(row[6][0]))
        storages[tag]=storages.get(tag,0)+1
    return {"candidate_count":len(candidates),"candidates":candidates,"storage_counts":storages}


def one(source:Path, derived:bool)->dict:
    cls=BASE.LocalityDerivedBuilder if derived else BUILDER.Builder
    b=cls(source,deflate_reuse_min=0,workers=1)
    b.micro_pack_max_file=PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES if derived else 0
    b.scan(); before=snapshot(b)
    b._build_micro_packs(); after=snapshot(b)
    return {
        "before":before,"after":after,
        "candidate_table_changed":before["candidates"]!=after["candidates"],
        "storage_counts_changed":before["storage_counts"]!=after["storage_counts"],
        "derived_groups":list(getattr(b,"_locality_derived_groups",[])),
    }


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-zero-group-probe-work")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-zero-group-probe.json")); args=ap.parse_args()
    shutil.rmtree(args.work_root,ignore_errors=True); root=args.work_root/"corpus"; manifest=RESEMBLANCE.build(root); source=root/"04_deflate_family"
    result={"schema":"cmpct-v030-r24-zero-group-candidate-probe-v1","identity":next(x for x in manifest["workloads"] if x["name"]=="04_deflate_family"),"independent":one(source,False),"derived":one(source,True),"release_credit":False}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
