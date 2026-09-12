from __future__ import annotations

"""Source-derived attribution of the frozen v0.25/v0.29 Office stream policy.

Mission Lock
------------
The frozen v0.29 Office winner (5,954,026 B) is the inherited v0.25 candidate, not the
v0.28 graph. Recent v0.30 experiments falsified several ways of making SFV4's exact-member
streams denser under strict locality, so the next causal question is whether the mature
control wins by a different *economic policy* rather than a stronger codec.

This referee reconstructs only v0.25 section 1/1b and stream physicalization from source:
  * ZIP-like containers are admitted only for local duplicate >=512 KiB, cross-container
    shared unique streams >=32 KiB, or loose-file exact reuse >=32 KiB;
  * admitted exact compressed streams are globally interned;
  * streams that back loose derived files are hot and stored raw in stream-aligned <=512 KiB
    slabs; cold container-only streams may share <=512 KiB slabs and compete with Zstd-3.

It compares that inventory to the current SFV4 all-member inventory on the exact same
Office tree. The hypothesis is falsifiable: if the mature control's stream-policy savings
on roots common to both plans are small relative to the current 549,285 B H-BMAX gap,
then hot/cold physical policy is not the missing mechanism and should not be copied into
v0.30. If large, the next experiment must reproduce the economics under the unchanged
<=8x product locality law rather than importing v0.25's 512 KiB access behavior.

Diagnostic only. This does not grant v0.25 locality, v0.30 selector admission or release
credit, and it does not waive storage of containers rejected by v0.25 virtualization.
"""

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import zipfile

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v025 as V025
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-v025-stream-policy-attribution-v1"
H_BMAX_GAP = 549_285
SHARED_MIN = 32 * 1024
LOCAL_DUP_MIN = 512 * 1024
TARGET = 512 * 1024


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _zip_probe(files: list[Path], raws: dict[Path, bytes]):
    probe = {}
    stream_containers: dict[bytes, set[Path]] = {}
    member_plain: dict[bytes, list[tuple[Path, bytes, int, int, int]]] = {}
    for p in files:
        raw = raws[p]
        if not raw.startswith(b"PK\x03\x04") or len(raw) < 4096:
            continue
        try:
            with zipfile.ZipFile(p) as ar:
                infos = sorted([i for i in ar.infolist() if not i.is_dir()], key=lambda x: x.header_offset)
                plain_by_offset = {i.header_offset: ar.read(i) for i in infos if i.compress_type in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED)}
            spans=[]; sids=[]; local={}; members=[]
            for zi in infos:
                v=struct.unpack_from("<IHHHHHIIIHH", raw, zi.header_offset)
                nl,xl=v[-2],v[-1]; s=zi.header_offset+30+nl+xl; e=s+zi.compress_size
                b=raw[s:e]; hh=_h(b)
                local.setdefault(hh,b); sids.append(hh); spans.append((s,e))
                stream_containers.setdefault(hh,set()).add(p)
                if zi.compress_type in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED):
                    pb=plain_by_offset[zi.header_offset]; ph=_h(pb)
                    member_plain.setdefault(ph,[]).append((p,hh,zi.compress_type,len(pb),len(b)))
                    members.append((ph,hh,zi.compress_type,len(pb),len(b)))
            local_dup=sum(e-s for s,e in spans)-sum(len(b) for b in local.values())
            probe[p]={"local":local,"local_dup":local_dup,"sids":sids,"members":members}
        except Exception:
            pass
    return probe, stream_containers, member_plain


def _v025_inventory(root: Path):
    files=sorted(p for p in root.rglob("*") if p.is_file())
    raws={p:p.read_bytes() for p in files}
    probe,stream_containers,member_plain=_zip_probe(files,raws)
    top_by_hash={}
    for p in files: top_by_hash.setdefault(_h(raws[p]),[]).append(p)

    special={}; stream_pool=bytearray(); stream_slot={}; stream_meta=[]
    for p,zp in probe.items():
        shared_unique=sum(len(b) for hh,b in zp["local"].items() if len(stream_containers.get(hh,()))>1)
        seen_plain=set(); external_match=0
        for ph,hh,method,usize,csize in zp["members"]:
            if ph in seen_plain: continue
            seen_plain.add(ph)
            if any(tp != p for tp in top_by_hash.get(ph,())):
                external_match += csize
        if zp["local_dup"] < LOCAL_DUP_MIN and shared_unique < SHARED_MIN and external_match < SHARED_MIN:
            continue
        for hh,b in zp["local"].items():
            if hh not in stream_slot:
                off=len(stream_pool); stream_pool += b; stream_slot[hh]=(off,len(b)); stream_meta.append((hh,off,len(b)))
        special[p]={"local_dup":zp["local_dup"],"shared_unique":shared_unique,"external_match":external_match,"sids":zp["sids"]}

    retained=set(stream_slot); derived={}
    for p in files:
        if p in special or len(raws[p]) < SHARED_MIN: continue
        opts=[]
        for cp,hh,method,usize,csize in member_plain.get(_h(raws[p]),[]):
            if cp in special and hh in retained and usize==len(raws[p]):
                opts.append((csize,hh,method,usize))
        if opts:
            csize,hh,method,usize=min(opts)
            derived[p]={"stream_hash":hh,"method":method,"usize":usize,"csize":csize}

    hot={d["stream_hash"] for d in derived.values()}
    entries=sorted((off,hh,n) for hh,off,n in stream_meta)
    physical=[]; cold=[]
    def emit(so: int, part: bytes, hot_flag: bool):
        if hot_flag:
            codec="raw"; payload=len(part)
        else:
            comp=V025.zc(part,3); codec="zstd3" if len(comp)+8 < len(part) else "raw"; payload=len(comp) if codec=="zstd3" else len(part)
        physical.append({"start":so,"logical":len(part),"payload":payload,"physical":payload+V025.PH.size,"codec":codec,"hot":hot_flag})
    def flush_cold():
        nonlocal cold
        if not cold: return
        so=cold[0][0]; end=cold[-1][0]+cold[-1][2]; raw=bytes(stream_pool[so:end])
        for o in range(0,len(raw),TARGET): emit(so+o,raw[o:o+TARGET],False)
        cold=[]
    for off,hh,n in entries:
        if hh in hot:
            flush_cold(); raw=bytes(stream_pool[off:off+n])
            for o in range(0,n,TARGET): emit(off+o,raw[o:o+TARGET],True)
        else:
            if cold and off+n-cold[0][0] > TARGET: flush_cold()
            cold.append((off,hh,n))
    flush_cold()

    # Attribute physical slabs back to roots by interval overlap. The actual v0.25 archive pays each
    # slab once; root-attributed bytes are diagnostic overlap weights, not an additional byte count.
    root_rows=[]
    for hh,off,n in stream_meta:
        overlaps=[]
        for fr in physical:
            a=max(off,fr["start"]); b=min(off+n,fr["start"]+fr["logical"])
            if a < b: overlaps.append({**fr,"overlap":b-a})
        # Fractional payload/header attribution is used only to compare common roots. Exact archive
        # physical total remains the integer sum below.
        attributed=sum(fr["physical"] * fr["overlap"] / fr["logical"] for fr in overlaps)
        root_rows.append({"hash":hh.hex(),"raw_bytes":n,"hot":hh in hot,"attributed_physical_bytes":attributed,"raw_minus_attributed":n-attributed})

    return {
        "candidate_containers":len(probe),"admitted_containers":len(special),
        "stream_roots":len(stream_meta),"stream_raw_bytes":len(stream_pool),
        "hot_roots":len(hot),"derived_loose_files":len(derived),
        "physical_frames":len(physical),"physical_stream_bytes":sum(x["physical"] for x in physical),
        "physical_payload_bytes":sum(x["payload"] for x in physical),
        "cold_zstd_frames":sum(x["codec"]=="zstd3" for x in physical),
        "hot_raw_frames":sum(x["hot"] for x in physical),
        "container_reasons":{
            "local_dup":sum(v["local_dup"]>=LOCAL_DUP_MIN for v in special.values()),
            "shared":sum(v["shared_unique"]>=SHARED_MIN for v in special.values()),
            "external":sum(v["external_match"]>=SHARED_MIN for v in special.values()),
        },
        "root_rows":root_rows,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_office_v025attrib_neutral")
    repair=V029._load(V029.REPAIR_PATH,"r4_office_v025attrib_repair")
    repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source=corpus/"02_office_workspace"
    sf=SFV4.build_candidate(source,work/"sfv4",work/"sfv4-work")
    old=_v025_inventory(source)

    sf_roots={h.hex():len(b) for h,b in sf["all_streams"].items()}
    old_rows={r["hash"]:r for r in old["root_rows"]}
    common=sorted(set(sf_roots)&set(old_rows))
    common_raw=sum(sf_roots[h] for h in common)
    common_v025_phys=sum(old_rows[h]["attributed_physical_bytes"] for h in common)
    common_policy_saving=common_raw-common_v025_phys
    sf_only=sorted(set(sf_roots)-set(old_rows)); old_only=sorted(set(old_rows)-set(sf_roots))

    return {
        "schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),
        "workload":"02_office_workspace","tree_sha256":PRODUCT.treehash(source),
        "sfv4":{
            "stored_bytes":int(sf["stored_bytes"]),"all_member_stream_roots":len(sf_roots),
            "all_member_stream_bytes":sum(sf_roots.values()),"derived_files":len(sf["derived_inventory"]),
        },
        "v025_stream_policy":{k:v for k,v in old.items() if k!="root_rows"},
        "common_root_attribution":{
            "common_roots":len(common),"common_raw_bytes":common_raw,
            "v025_fractionally_attributed_physical_bytes":common_v025_phys,
            "raw_minus_v025_physical_bytes":common_policy_saving,
            "h_bmax_gap_bytes":H_BMAX_GAP,
            "fraction_of_h_bmax_gap":common_policy_saving/H_BMAX_GAP,
            "sfv4_only_roots":len(sf_only),"sfv4_only_raw_bytes":sum(sf_roots[h] for h in sf_only),
            "v025_only_roots":len(old_only),"v025_only_raw_bytes":sum(old_rows[h]["raw_bytes"] for h in old_only),
        },
        "hypothesis":{
            "common_root_hot_cold_policy_can_explain_h_bmax_gap":common_policy_saving>=H_BMAX_GAP,
            "same_stream_root_universe":set(sf_roots)==set(old_rows),
        },
        "contract":{
            "diagnostic_only":True,"release_credit":False,"locality_credit":False,
            "v025_512k_locality_not_credited":True,"rejected_container_storage_not_waived":True,
            "root_fractional_attribution_is_diagnostic_not_archive_byte_count":True,
            "selector_changed":False,"production_format_changed":False,
            "next_if_positive":"reproduce hot/cold economics with <=8x bounded physical units and full candidate accounting",
            "next_if_negative":"retire hot/cold stream policy as primary explanation and inspect nonstream recipe/packing attribution",
        },
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-v025-policy-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-v025-policy.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps(d,indent=2))

if __name__=="__main__": main()
