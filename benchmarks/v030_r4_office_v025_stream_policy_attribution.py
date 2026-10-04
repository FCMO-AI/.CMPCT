from __future__ import annotations

"""Attribute frozen v0.25/v0.29 Office advantage to compressed-stream policy.

Mission Lock: reconstruct v0.25 section 1/1b admission and stream physicalization from
source on the same deterministic Office tree, then compare roots common with current SFV4.
If mature hot/cold stream economics cannot explain the 549,285 B H-BMAX gap on common
roots, do not copy that policy into v0.30. If it can, the next test must reproduce the
mechanism under the unchanged <=8x locality law rather than importing 512 KiB locality.
Diagnostic only: rejected-container storage is never waived and fractional root attribution
is not archive-byte accounting.
"""

import argparse, hashlib, json, os, shutil, struct, zipfile
from pathlib import Path
from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v025 as V025
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA="cmpct-v030-r4-office-v025-stream-policy-attribution-v1"
GAP=549_285; MIN=32*1024; LOCAL=512*1024; TARGET=512*1024

def H(b): return hashlib.sha256(b).digest()
def keyhex(h): return h.hex() if isinstance(h,(bytes,bytearray)) else str(h)

def probe(files,raws):
    zp={}; containers={}; member_plain={}
    for p in files:
        raw=raws[p]
        if not raw.startswith(b"PK\x03\x04") or len(raw)<4096: continue
        try:
            with zipfile.ZipFile(p) as ar:
                infos=sorted([i for i in ar.infolist() if not i.is_dir()],key=lambda i:i.header_offset)
                plain={i.header_offset:ar.read(i) for i in infos if i.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED)}
            spans=[]; local={}; sids=[]; members=[]
            for zi in infos:
                v=struct.unpack_from("<IHHHHHIIIHH",raw,zi.header_offset); nl,xl=v[-2],v[-1]
                s=zi.header_offset+30+nl+xl; e=s+zi.compress_size; b=raw[s:e]; hh=H(b)
                spans.append((s,e)); local.setdefault(hh,b); sids.append(hh); containers.setdefault(hh,set()).add(p)
                if zi.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED):
                    pb=plain[zi.header_offset]; ph=H(pb); row=(p,hh,zi.compress_type,len(pb),len(b)); members.append((ph,*row[1:])); member_plain.setdefault(ph,[]).append(row)
            zp[p]={"local":local,"local_dup":sum(e-s for s,e in spans)-sum(map(len,local.values())),"sids":sids,"members":members}
        except Exception: pass
    return zp,containers,member_plain

def old_inventory(root):
    files=sorted(p for p in root.rglob("*") if p.is_file()); raws={p:p.read_bytes() for p in files}
    zp,containers,member_plain=probe(files,raws); top={}
    for p in files: top.setdefault(H(raws[p]),[]).append(p)
    special={}; pool=bytearray(); slot={}; meta=[]
    for p,z in zp.items():
        shared=sum(len(b) for hh,b in z["local"].items() if len(containers.get(hh,()))>1)
        seen=set(); external=0
        for ph,hh,method,usize,csize in z["members"]:
            if ph in seen: continue
            seen.add(ph)
            if any(tp!=p for tp in top.get(ph,())): external+=csize
        if z["local_dup"]<LOCAL and shared<MIN and external<MIN: continue
        for hh,b in z["local"].items():
            if hh not in slot:
                off=len(pool); pool+=b; slot[hh]=(off,len(b)); meta.append((hh,off,len(b)))
        special[p]={"local_dup":z["local_dup"],"shared":shared,"external":external}
    retained=set(slot); derived={}
    for p in files:
        if p in special or len(raws[p])<MIN: continue
        opts=[]
        for cp,hh,method,usize,csize in member_plain.get(H(raws[p]),[]):
            if cp in special and hh in retained and usize==len(raws[p]): opts.append((csize,hh,method,usize))
        if opts:
            csize,hh,method,usize=min(opts); derived[p]={"stream_hash":hh,"method":method,"usize":usize,"csize":csize}
    hot={d["stream_hash"] for d in derived.values()}; frames=[]; cold=[]
    def emit(start,part,is_hot):
        if is_hot: payload=len(part); codec="raw"
        else:
            c=V025.zc(part,3); codec="zstd3" if len(c)+8<len(part) else "raw"; payload=len(c) if codec=="zstd3" else len(part)
        frames.append({"start":start,"logical":len(part),"payload":payload,"physical":payload+V025.PH.size,"codec":codec,"hot":is_hot})
    def flush():
        nonlocal cold
        if not cold:return
        start=cold[0][0]; end=cold[-1][0]+cold[-1][2]; raw=bytes(pool[start:end])
        for o in range(0,len(raw),TARGET): emit(start+o,raw[o:o+TARGET],False)
        cold=[]
    for off,hh,n in sorted((off,hh,n) for hh,off,n in meta):
        if hh in hot:
            flush(); raw=bytes(pool[off:off+n])
            for o in range(0,n,TARGET): emit(off+o,raw[o:o+TARGET],True)
        else:
            if cold and off+n-cold[0][0]>TARGET: flush()
            cold.append((off,hh,n))
    flush()
    roots=[]
    for hh,off,n in meta:
        attr=0.0
        for f in frames:
            a=max(off,f["start"]); b=min(off+n,f["start"]+f["logical"])
            if a<b: attr+=f["physical"]*(b-a)/f["logical"]
        roots.append({"hash":hh.hex(),"raw_bytes":n,"hot":hh in hot,"attributed_physical":attr})
    return {"candidate_containers":len(zp),"admitted_containers":len(special),"stream_roots":len(meta),"stream_raw_bytes":len(pool),"hot_roots":len(hot),"derived_loose_files":len(derived),"physical_frames":len(frames),"physical_stream_bytes":sum(f["physical"] for f in frames),"physical_payload_bytes":sum(f["payload"] for f in frames),"cold_zstd_frames":sum(f["codec"]=="zstd3" for f in frames),"hot_raw_frames":sum(f["hot"] for f in frames),"reasons":{"local_dup":sum(x["local_dup"]>=LOCAL for x in special.values()),"shared":sum(x["shared"]>=MIN for x in special.values()),"external":sum(x["external"]>=MIN for x in special.values())},"roots":roots}

def run(work):
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_v025attr_neutral"); repair=V029._load(V029.REPAIR_PATH,"r4_v025attr_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"02_office_workspace"
    sf=SFV4.build_candidate(source,work/"sfv4",work/"sfv4-work"); old=old_inventory(source)
    sfr={keyhex(h):len(b) for h,b in sf["all_streams"].items()}; oldr={r["hash"]:r for r in old["roots"]}; common=sorted(set(sfr)&set(oldr))
    craw=sum(sfr[h] for h in common); cphys=sum(oldr[h]["attributed_physical"] for h in common); saving=craw-cphys
    sfonly=set(sfr)-set(oldr); oldonly=set(oldr)-set(sfr)
    return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"workload":"02_office_workspace","tree_sha256":PRODUCT.treehash(source),"sfv4":{"stored_bytes":int(sf["stored_bytes"]),"all_member_stream_roots":len(sfr),"all_member_stream_bytes":sum(sfr.values()),"derived_files":len(sf["derived_inventory"])},"v025_stream_policy":{k:v for k,v in old.items() if k!="roots"},"common_root_attribution":{"common_roots":len(common),"common_raw_bytes":craw,"v025_fractionally_attributed_physical_bytes":cphys,"raw_minus_v025_physical_bytes":saving,"h_bmax_gap_bytes":GAP,"fraction_of_h_bmax_gap":saving/GAP,"sfv4_only_roots":len(sfonly),"sfv4_only_raw_bytes":sum(sfr[h] for h in sfonly),"v025_only_roots":len(oldonly),"v025_only_raw_bytes":sum(oldr[h]["raw_bytes"] for h in oldonly)},"hypothesis":{"common_root_hot_cold_policy_can_explain_h_bmax_gap":saving>=GAP,"same_stream_root_universe":set(sfr)==set(oldr)},"contract":{"diagnostic_only":True,"release_credit":False,"locality_credit":False,"v025_512k_locality_not_credited":True,"rejected_container_storage_not_waived":True,"root_fractional_attribution_is_diagnostic_not_archive_byte_count":True,"selector_changed":False,"production_format_changed":False}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-v025-policy-work"));p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-v025-policy.json"));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+"\n");print(json.dumps(d,indent=2))
if __name__=="__main__":main()
