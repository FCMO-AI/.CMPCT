from __future__ import annotations

"""Counterfactual stopping-oracle referee for the frozen EG08 effort ladder."""

import argparse
import binascii
import hashlib
import json
from pathlib import Path
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EG07_MODULE = "experiments.entropygraph_v030_federated_embedded_fs_candidate_v7"
EG08_MODULE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8"
NEUTRAL = {"02_office_workspace", "04_analytics_and_database", "05_logs_and_telemetry", "09_ml_artifacts", "10_large_mixed_binary"}
HOSTILE_NAMES = {"01_shifted_versions", "02_false_neighbors", "03_boundary_churn", "05_incompressible"}
PREDICATES = (
    "P1_stop_after_level3_no_strict_win",
    "P2_stop_after_3_6_no_strict_win",
    "P3_stop_after_two_consecutive_storage_ties",
    "P4_stop_after_3_6_same_candidate_size",
    "P5_jump_3_to_19_on_level3_no_strict_win",
)


def H(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_packs(archive: Path) -> tuple[list[dict], dict]:
    owner = EG07.EG06.EG05; V25 = owner.V25
    packs=[]
    with EG07._engine(archive.resolve()):
        stream, meta, offsets = V25.open_ar()
        try:
            for pi,(offset,codec,usize,csize,crc,expected_sha) in enumerate(offsets):
                stream.seek(offset); payload=stream.read(csize)
                raw=V25.zd(payload,usize) if int(codec)==1 else payload
                if len(raw)!=int(usize) or (binascii.crc32(raw)&0xffffffff)!=int(crc) or V25.H(raw)!=expected_sha:
                    raise RuntimeError(f"pack integrity mismatch {pi}")
                packs.append({"index":pi,"codec":int(codec),"raw":raw,"payload":payload,"csize":int(csize)})
        finally: stream.close()
    return packs,dict(meta)


def trace_pack(row: dict) -> list[dict]:
    V25=EG07.EG06.EG05.V25; raw=row["raw"]
    calls=[]
    for level in EG08.EFFORT_LADDER:
        c0=time.process_time_ns(); w0=time.perf_counter_ns(); comp=V25.zc(raw,level); cpu=time.process_time_ns()-c0; wall=time.perf_counter_ns()-w0
        admitted=len(comp)+8 < len(raw)
        payload=comp if admitted else raw
        calls.append({"level":int(level),"codec":1 if admitted else 0,"payload":payload,"size":len(payload),"cpu_ns":int(cpu),"wall_ns":int(wall)})
    return calls


def apply_full(row: dict,calls:list[dict]) -> tuple[int,bytes,int|None]:
    best_codec=int(row["codec"]); best=row["payload"]; best_size=len(best); best_level=None
    for c in calls:
        if c["size"]<=best_size:
            if c["size"]<best_size:
                best_codec=c["codec"]; best=c["payload"]; best_size=c["size"]; best_level=c["level"]
            continue
        break
    return best_codec,best,best_level


def simulate(name:str,row:dict,calls:list[dict]) -> tuple[int,bytes,set[int]]:
    best_codec=int(row["codec"]); best=row["payload"]; best_size=len(best)
    executed=set(); strict_levels=[]; consecutive_ties=0
    for idx,c in enumerate(calls):
        level=c["level"]
        if name=="P5_jump_3_to_19_on_level3_no_strict_win" and idx in (1,2) and not strict_levels:
            continue
        executed.add(idx)
        before=best_size
        strict=c["size"]<best_size
        tie=c["size"]==best_size
        if c["size"]<=best_size:
            if strict:
                best_codec=c["codec"]; best=c["payload"]; best_size=c["size"]; strict_levels.append(level); consecutive_ties=0
            elif tie:
                consecutive_ties += 1
        else:
            break
        if name=="P1_stop_after_level3_no_strict_win" and level==3 and not strict_levels:
            break
        if name=="P2_stop_after_3_6_no_strict_win" and level==6 and not strict_levels:
            break
        if name=="P3_stop_after_two_consecutive_storage_ties" and consecutive_ties>=2:
            break
        if name=="P4_stop_after_3_6_same_candidate_size" and level==6 and len(calls)>=2 and calls[0]["size"]==calls[1]["size"]:
            break
    return best_codec,best,executed


def one(family:str,source:Path,item:dict,work:Path)->dict:
    a7=work/"eg07.cmpct"; a8=work/"eg08.cmpct"
    b7=fresh_build(EG07_MODULE,source,a7); b8=fresh_build(EG08_MODULE,source,a8)
    base,meta=load_packs(a7); actual,meta8=load_packs(a8)
    if len(base)!=len(actual): raise RuntimeError("pack-count drift")
    streams,hot=EG08._stream_roles(meta,len(base)); streams8,hot8=EG08._stream_roles(meta8,len(actual))
    if streams!=streams8 or hot!=hot8: raise RuntimeError("stream-role drift")
    stats={p:{"mismatches":0,"byte_penalty":0,"avoided_calls":0,"avoided_cpu_ns":0,"avoided_wall_ns":0,"office_raw_promotion_preserved":True,"examples":[]} for p in PREDICATES}
    full_mismatch=[]; total_calls=0; total_cpu=0; total_wall=0; office_raw_promotions=0
    for row,act in zip(base,actual):
        pi=int(row["index"])
        if pi in hot:
            if row["codec"]!=act["codec"] or row["payload"]!=act["payload"]: full_mismatch.append({"pack":pi,"reason":"hot-drift"})
            continue
        calls=trace_pack(row); total_calls+=len(calls); total_cpu+=sum(c["cpu_ns"] for c in calls); total_wall+=sum(c["wall_ns"] for c in calls)
        fc,fp,fl=apply_full(row,calls)
        if fc!=act["codec"] or fp!=act["payload"]:
            full_mismatch.append({"pack":pi,"reason":"full-replay-mismatch"}); continue
        raw_promotion = int(row["codec"])==0 and (int(act["codec"])!=0 or act["payload"]!=row["payload"])
        if raw_promotion: office_raw_promotions += 1
        for p in PREDICATES:
            pc,pp,executed=simulate(p,row,calls)
            omitted=[i for i in range(len(calls)) if i not in executed]
            s=stats[p]; s["avoided_calls"]+=len(omitted); s["avoided_cpu_ns"]+=sum(calls[i]["cpu_ns"] for i in omitted); s["avoided_wall_ns"]+=sum(calls[i]["wall_ns"] for i in omitted)
            ok=pc==act["codec"] and pp==act["payload"]
            if not ok:
                s["mismatches"]+=1; s["byte_penalty"]+=len(pp)-len(act["payload"])
                if len(s["examples"])<8: s["examples"].append({"pack":pi,"incumbent_codec":row["codec"],"actual_codec":act["codec"],"actual_size":len(act["payload"]),"counterfactual_size":len(pp),"full_selected_level":fl,"raw_promotion":raw_promotion})
                if raw_promotion: s["office_raw_promotion_preserved"]=False
    l7=b7["result"]["locality"]; l8=b8["result"]["locality"]
    geometry=l7["member_count"]==l8["member_count"] and l7["max_decode_unit_bytes"]==l8["max_decode_unit_bytes"] and l7["max_member_read_amplification"]==l8["max_member_read_amplification"]
    for p,s in stats.items():
        s["avoided_call_share"]=s["avoided_calls"]/max(total_calls,1); s["avoided_cpu_share"]=s["avoided_cpu_ns"]/max(total_cpu,1); s["avoided_wall_share"]=s["avoided_wall_ns"]/max(total_wall,1); s["status"]="EXACT" if s["mismatches"]==0 else "FALSIFIED"
    return {"family":family,"name":item["name"],"tree_sha256":item["tree_sha256"],"eg07_bytes":b7["archive_bytes"],"eg08_bytes":b8["archive_bytes"],"saved_bytes":int(b7["archive_bytes"])-int(b8["archive_bytes"]),"strong_verify_eg07":bool((b7["result"].get("verified") or {}).get("ok")),"strong_verify_eg08":bool((b8["result"].get("verified") or {}).get("ok")),"geometry_same":geometry,"full_replay_mismatches":full_mismatch,"total_calls":total_calls,"total_cpu_s":total_cpu/1e9,"total_wall_s":total_wall/1e9,"raw_incumbent_promotions":office_raw_promotions,"predicates":stats}


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg08-ladder-stopping-oracle.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-stop-") as td:
        work=Path(td); neutral=work/"neutral"; hostile=work/"hostile"; nm=CURRENT.build(neutral); hm=HOSTILE.build(hostile)
        surfaces=[*(("neutral",neutral,x) for x in nm["corpora"] if x["name"] in NEUTRAL),*(("hostile",hostile,x) for x in hm["workloads"] if x["name"] in HOSTILE_NAMES)]
        rows=[]
        for family,root,item in surfaces:
            w=work/f"{family}-{item['name']}"; w.mkdir(); rows.append(one(family,root/item["name"],item,w))
        valid=len(rows)==9 and all(r["strong_verify_eg07"] and r["strong_verify_eg08"] and r["geometry_same"] and not r["full_replay_mismatches"] for r in rows)
        aggregate={}
        for p in PREDICATES:
            mm=sum(r["predicates"][p]["mismatches"] for r in rows); penalty=sum(r["predicates"][p]["byte_penalty"] for r in rows); avoided=sum(r["predicates"][p]["avoided_calls"] for r in rows); calls=sum(r["total_calls"] for r in rows); acpu=sum(r["predicates"][p]["avoided_cpu_ns"] for r in rows); tcpu=sum(r["total_cpu_s"]*1e9 for r in rows)
            aggregate[p]={"status":"EXACT" if valid and mm==0 else "FALSIFIED","mismatches":mm,"byte_penalty":penalty,"avoided_calls":avoided,"avoided_call_share":avoided/max(calls,1),"avoided_cpu_s":acpu/1e9,"avoided_cpu_share":acpu/max(tcpu,1),"office_raw_promotion_preserved":next(r for r in rows if r["name"]=="02_office_workspace")["predicates"][p]["office_raw_promotion_preserved"]}
        out={"schema":"v030-eg08-ladder-stopping-oracle-v1","valid":valid,"workloads":rows,"aggregate_predicates":aggregate,"total_effort_calls":sum(r["total_calls"] for r in rows),"aggregate_saved_bytes":sum(r["saved_bytes"] for r in rows)}
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
