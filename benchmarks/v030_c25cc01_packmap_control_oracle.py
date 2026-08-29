from __future__ import annotations

"""Research-only compact-control A/B for locality-safe S_PACK metadata.

A locality-safe encrypted-like source has 1,400 tiny logical members represented as S_PACK rows. The current
C25CC01 compact index repeats ``[S_PACK, blob_id, offset, length]`` per member. For a physical pack, slices are
contiguous, so the control plane can encode the pack once, list member file-table indices in physical order, store
logical sizes in a column, and derive every offset by cumulative sum. This oracle asks how many bytes that removes.

The candidate expands back to the *exact* ordinary r24 semantic index before any reader could consume it. It does
not change the physical data span, locality, integrity or recovery policy and grants no product/release credit.
"""

import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile

import msgpack

from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRAT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE
from experiments import entropygraph_v030_release_product as PRODUCT

LEVELS = CONTROL.LEVELS


def _compress(raw: bytes) -> tuple[int, bytes]:
    rows=[]
    for level in LEVELS:
        comp=R24.zc(raw, level); rows.append((len(comp), level, comp))
    _n, level, comp=min(rows, key=lambda x:(x[0],x[1]))
    return int(level), comp


def _packmap_compact(index: dict) -> dict:
    compact=CONTROL._compact_index(index)
    rows=copy.deepcopy(compact["f"])
    groups={}
    sizes=[]
    for fi,(src, enc) in enumerate(zip(index["files"], rows, strict=True)):
        storage=src[6]
        if src[1] != R24.K_FILE or not storage or int(storage[0]) != R24.S_PACK:
            continue
        blob=int(storage[1]); off=int(storage[2]); ln=int(storage[3])
        groups.setdefault(blob,[]).append((off,fi,ln))
        # The per-row storage tuple is replaced by a one-byte-ish repeated marker. Size is kept in a dense column.
        enc[3]=[R24.S_PACK]
        sizes.append([fi,ln])
    pack_rows=[]
    for blob,members in sorted(groups.items()):
        members.sort()
        expected=0; file_indices=[]
        for off,fi,ln in members:
            if off != expected:
                raise RuntimeError("S_PACK slices are not contiguous; implicit offset derivation would be invalid")
            file_indices.append(fi); expected += ln
        # Delta-code file table indices inside each physical pack.
        deltas=[]; prev=0
        for i,fi in enumerate(file_indices):
            deltas.append(fi if i==0 else fi-prev); prev=fi
        pack_rows.append([blob,deltas])
    return {**compact,"f":rows,"q":pack_rows,"s":sizes}


def _restore_standard(candidate: dict) -> dict:
    standard={k:copy.deepcopy(v) for k,v in candidate.items() if k not in {"q","s"}}
    size_by_file={int(fi):int(ln) for fi,ln in candidate["s"]}
    seen=set()
    for blob,deltas in candidate["q"]:
        prev=0; offset=0
        for i,delta in enumerate(deltas):
            fi=int(delta) if i==0 else prev+int(delta); prev=fi
            ln=size_by_file[fi]
            enc=standard["f"][fi]
            if enc[3] != [R24.S_PACK]: raise RuntimeError("pack-map row marker mismatch")
            enc[3]=[R24.S_PACK,int(blob),offset,ln]
            offset += ln; seen.add(fi)
    if seen != set(size_by_file): raise RuntimeError("pack-map membership is incomplete")
    return standard


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    roots=STRAT.SAFE._build_all(work_root/"corpus")
    name,source=STRAT.SAFE._find_suffix(roots, STRAT.SAFE.TARGET_SUFFIX)
    with tempfile.TemporaryDirectory(prefix="cmpct-packmap-", dir=work_root) as td:
        r24=Path(td)/"source.cmpct"
        with STRAT._patched("descending_greedy"):
            PRODUCT._locality_bounded_r24_build(source,r24)
        verified=PRODUCT.strong_verify(r24)
        if not verified.get("ok"): raise RuntimeError("locality-safe source failed strong verification")
        index,data,physical=PROFILE._source_r24_parts(r24)
        locality=PROFILE._audit_s_pack_locality(index)
        baseline_raw,_baseline_obj=PROFILE._compact_raw(index)
        blevel,bcomp=_compress(baseline_raw)
        candidate_obj=_packmap_compact(index)
        restored=_restore_standard(candidate_obj)
        expanded=CONTROL._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
        if expanded != index: raise RuntimeError("pack-map control does not expand to exact r24 semantic index")
        envelope={"x":list(index["features"]),"c":candidate_obj}
        candidate_raw=msgpack.packb(envelope,use_bin_type=True)
        clevel,ccomp=_compress(candidate_raw)
    framing=R24.HDR.size+R24.FTR.size
    baseline_projected=framing+2*len(bcomp)+len(data)
    candidate_projected=framing+2*len(ccomp)+len(data)
    saving=baseline_projected-candidate_projected
    pack_members=sum(1 for row in index["files"] if row[1]==R24.K_FILE and row[6] and row[6][0]==R24.S_PACK)
    return {
      "schema":"cmpct-v030-c25cc01-packmap-control-oracle-v1",
      "contract":{"release_credit":False,"production_change":False,"physical_data_span_changed":False,"locality_ceiling":8,"semantic_index_roundtrip_exact":True},
      "target":name,
      "tree_sha256":verified.get("tree_sha256"),
      "locality":locality,
      "s_pack_members":pack_members,
      "baseline":{"raw_control_bytes":len(baseline_raw),"compressed_control_bytes_per_copy":len(bcomp),"level":blevel,"projected_archive_bytes":baseline_projected},
      "packmap":{"raw_control_bytes":len(candidate_raw),"compressed_control_bytes_per_copy":len(ccomp),"level":clevel,"projected_archive_bytes":candidate_projected},
      "saving_vs_current_compact_control_bytes":saving,
      "gate":{"experiment_valid":expanded==index and candidate_projected < baseline_projected,"passed":expanded==index},
      "claim_boundary":"Research-only control representation estimate over the exact locality-safe physical payload. No reader/native/Android or release credit; positive savings require canonical grammar implementation and all authority gates."
    }


def main():
    p=argparse.ArgumentParser();p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-c25cc01-packmap-work"));p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-c25cc01-packmap.json"));a=p.parse_args()
    d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+"\n");print(json.dumps(d,indent=2),flush=True)
    if not d["gate"]["passed"]: raise SystemExit("pack-map compact-control oracle invalid")

if __name__=="__main__":main()
