from __future__ import annotations

"""Exact 15-workload falsifier for the existing-mode-2 R4 owner inversion.

Reuses the already-audited full-matrix harness, replacing only the admitted Analytics candidate
builder/extractor with the mode-2 owner inversion. Non-admitted workloads still use byte-identical
ordinary v0.30 fallback. Diagnostic only; no shipping selector/format/version change.
"""
import argparse, json
from pathlib import Path
from benchmarks import v030_r4_dual_owner_full_matrix as MATRIX
from benchmarks import v030_r4_npz_mode2_owner_inversion as M2

SCHEMA="cmpct-v030-r4-mode2-full-matrix-v1"

# The matrix harness deliberately calls the candidate through this module's worker process. Patch only
# the admitted candidate implementation; discovery, baselines, corpus generation, verification gates,
# process-tree accounting and exact fallback stay identical to the raw dual-owner matrix.
MATRIX.DUAL._build_candidate=M2._build
MATRIX.DUAL._extract_candidate=M2._extract


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-mode2-matrix-work"))
    p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-mode2-matrix.json"))
    p.add_argument("--worker",choices=["baseline","candidate"])
    p.add_argument("--source",type=Path); p.add_argument("--archive",type=Path); p.add_argument("--worker-result",type=Path)
    a=p.parse_args()
    if a.worker:
        if not (a.source and a.archive and a.worker_result): raise SystemExit("worker mode requires source/archive/result")
        MATRIX._worker(a.worker,a.source,a.archive,a.work_root,a.worker_result)
        return
    d=MATRIX.run(a.work_root)
    d["schema"]=SCHEMA
    d["contract"].update({"candidate":"existing-r24-mode2-owner-inversion","existing_mode2_semantics_only":True,"npz_inverse_view_locality_not_yet_promoted":True})
    d["next_if_supported"]="preserve matrix win; rehabilitate physical selective locality of reconstructed NPZ, recovery/native parity, then attack Office"
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+"\n")
    print(json.dumps({"aggregate":d["aggregate"],"analytics":d["analytics"],"hypothesis":d["hypothesis"],"admitted":d["admitted"],"regressions":d["regressions"]},indent=2))

if __name__=="__main__": main()
