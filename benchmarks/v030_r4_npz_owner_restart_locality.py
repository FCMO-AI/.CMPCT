from __future__ import annotations

"""Falsifier: exact NPZ owner + compact Deflate-inflation restart state.

The full dual-view experiment bought good locality by duplicating the exact NPZ, but spent 3.58 MB
above Mode2 and lost the v0.29 Analytics floor. This experiment moves ownership back to the exact NPZ
and asks whether the derived external NPY can be made locally readable with substantially smaller
inflater restart state. It is diagnostic only: no shipping format, selector, or release version changes.

Mission lock (fixed before hosted measurement): 27 KiB output spacing, 4 KiB probes, no parameter
sweep. Fully charge compressed checkpoint histories, deduplicated Huffman state, compact index, and a
conservative 1 KiB authenticated-index allowance per cold read. Advance only if the resulting bundle
stays below the accepted v0.29 Analytics floor AND both physical and reconstruction amplification are
<=8x with byte-exact restart reads.
"""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import time
from typing import Iterable
import zlib

import zstandard as zstd

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_npz_mode2_owner_inversion as MODE2
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-npz-owner-restart-locality-v1"
ACCEPTED_V029_ANALYTICS = 6_135_172
SPAN = 27 * 1024
RANGE = 4 * 1024
WINDOW = 32 * 1024
INDEX_AUTH_ALLOWANCE = 1024

LEN_BASE=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
LEN_EXTRA=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0]
DIST_BASE=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
DIST_EXTRA=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13]
CL_ORDER=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]


def _rev(v:int,n:int)->int:
    r=0
    for _ in range(n): r=(r<<1)|(v&1); v>>=1
    return r


class Bits:
    def __init__(self,data:bytes,bitpos:int=0): self.data=data; self.bitpos=bitpos
    def read(self,n:int)->int:
        if self.bitpos+n>len(self.data)*8: raise EOFError("truncated deflate")
        v=0
        for i in range(n):
            p=self.bitpos+i; v|=((self.data[p>>3]>>(p&7))&1)<<i
        self.bitpos+=n; return v
    def align(self)->None: self.bitpos=(self.bitpos+7)&~7


class Huff:
    def __init__(self,lengths:Iterable[int]):
        self.lengths=tuple(int(x) for x in lengths); counts={}
        for n in self.lengths:
            if n: counts[n]=counts.get(n,0)+1
        code=0; nxt={}
        for bits in range(1,max(counts,default=0)+1):
            code=(code+counts.get(bits-1,0))<<1; nxt[bits]=code
        self.map={}
        for sym,n in enumerate(self.lengths):
            if not n: continue
            c=nxt[n]; nxt[n]+=1; self.map[(n,_rev(c,n))]=sym
        self.maxbits=max(counts,default=0)
    def decode(self,br:Bits)->int:
        code=0
        for n in range(1,self.maxbits+1):
            code|=br.read(1)<<(n-1)
            sym=self.map.get((n,code))
            if sym is not None: return sym
        raise ValueError("invalid Huffman code")


def _fixed()->tuple[Huff,Huff]:
    ll=[0]*288
    for i in range(144): ll[i]=8
    for i in range(144,256): ll[i]=9
    for i in range(256,280): ll[i]=7
    for i in range(280,288): ll[i]=8
    return Huff(ll),Huff([5]*32)


def _dynamic(br:Bits)->tuple[Huff,Huff]:
    hlit=br.read(5)+257; hdist=br.read(5)+1; hclen=br.read(4)+4
    cl=[0]*19
    for i in range(hclen): cl[CL_ORDER[i]]=br.read(3)
    ch=Huff(cl); vals=[]
    while len(vals)<hlit+hdist:
        s=ch.decode(br)
        if s<=15: vals.append(s)
        elif s==16:
            if not vals: raise ValueError("repeat without predecessor")
            vals.extend([vals[-1]]*(br.read(2)+3))
        elif s==17: vals.extend([0]*(br.read(3)+3))
        elif s==18: vals.extend([0]*(br.read(7)+11))
        else: raise ValueError("bad code-length symbol")
    vals=vals[:hlit+hdist]
    return Huff(vals[:hlit]),Huff(vals[hlit:])


@dataclass
class CP:
    outpos:int
    bitpos:int
    ll:tuple[int,...]
    dd:tuple[int,...]
    block_final:bool
    required_history:int=0


def _parse(stream:bytes,expected:bytes)->tuple[list[CP],list[tuple[int,int,int]]]:
    br=Bits(stream); out=bytearray(); cps=[]; matches=[]; next_cp=SPAN; done=False
    while not done:
        block_final=bool(br.read(1)); typ=br.read(2)
        if typ==0:
            br.align(); ln=br.read(16); nln=br.read(16)
            if (ln^0xffff)!=nln: raise ValueError("stored block length mismatch")
            # This corpus is expected to use Huffman blocks for the feature stream. Refuse to mint
            # unsupported stored-block checkpoints rather than hiding a reader special case.
            for _ in range(ln): out.append(br.read(8))
            done=block_final; continue
        if typ==1: ll,dd=_fixed()
        elif typ==2: ll,dd=_dynamic(br)
        else: raise ValueError("reserved deflate block")
        while True:
            if len(out)>=next_cp:
                cps.append(CP(len(out),br.bitpos,ll.lengths,dd.lengths,block_final)); next_cp=len(out)+SPAN
            sym=ll.decode(br)
            if sym<256: out.append(sym); continue
            if sym==256: break
            if not 257<=sym<=285: raise ValueError("bad length symbol")
            i=sym-257; ln=LEN_BASE[i]+(br.read(LEN_EXTRA[i]) if LEN_EXTRA[i] else 0)
            ds=dd.decode(br)
            if ds>=len(DIST_BASE): raise ValueError("bad distance symbol")
            dist=DIST_BASE[ds]+(br.read(DIST_EXTRA[ds]) if DIST_EXTRA[ds] else 0)
            start=len(out); matches.append((start,ln,dist))
            if dist>len(out): raise ValueError("distance before start")
            for _ in range(ln): out.append(out[-dist])
        done=block_final
    if bytes(out)!=expected: raise RuntimeError("research Deflate parser output mismatch")
    # For any post-checkpoint match, only the portion of its backward distance that reaches before
    # the checkpoint must be persisted. Limit analysis to one locality window because later matches
    # can reference output already reconstructed after the checkpoint.
    for cp in cps:
        need=0
        for start,_ln,dist in matches:
            if start<cp.outpos: continue
            if start-cp.outpos>=WINDOW: break
            need=max(need,max(0,dist-(start-cp.outpos)))
        cp.required_history=min(WINDOW,need)
    return cps,matches


def _table_key(cp:CP)->bytes: return bytes(cp.ll)+b"\xff"+bytes(cp.dd)+bytes([1 if cp.block_final else 0])


def _state_cost(cps:list[CP],source:bytes)->dict:
    zc=zstd.ZstdCompressor(level=3); histories=[]; table_ids={}; table_blobs=[]; index_bytes=0; max_hist=0
    for cp in cps:
        hist=source[max(0,cp.outpos-cp.required_history):cp.outpos]
        blob=zc.compress(hist); histories.append(blob); max_hist=max(max_hist,len(hist))
        key=_table_key(cp)
        if key not in table_ids:
            table_ids[key]=len(table_blobs); table_blobs.append(zc.compress(key))
        # outpos, bitpos, history offset, history length, table id, raw history length, flags
        index_bytes+=8+8+8+4+4+4+1
    return {"history_raw_bytes":sum(cp.required_history for cp in cps),"history_zstd_bytes":sum(map(len,histories)),"history_frame_count":len(histories),"max_required_history_bytes":max_hist,"unique_huffman_states":len(table_blobs),"huffman_state_zstd_bytes":sum(map(len,table_blobs)),"index_bytes":index_bytes,"total_restart_bytes":sum(map(len,histories))+sum(map(len,table_blobs))+index_bytes,"history_blobs":histories}


def _next_block(br:Bits)->tuple[bool,Huff|None,Huff|None,int]:
    final=bool(br.read(1)); typ=br.read(2)
    if typ==0:
        br.align(); ln=br.read(16); nln=br.read(16)
        if (ln^0xffff)!=nln: raise ValueError("stored block mismatch")
        return final,None,None,ln
    if typ==1: ll,dd=_fixed(); return final,ll,dd,-1
    if typ==2: ll,dd=_dynamic(br); return final,ll,dd,-1
    raise ValueError("reserved block")


def _restart_decode(stream:bytes,cp:CP,history:bytes,want:int)->tuple[bytes,int]:
    br=Bits(stream,cp.bitpos); ll=Huff(cp.ll); dd=Huff(cp.dd); buf=bytearray(history); base=len(buf); block_final=cp.block_final
    while len(buf)-base<want:
        sym=ll.decode(br)
        if sym<256: buf.append(sym); continue
        if sym==256:
            if block_final: break
            block_final,ll2,dd2,stored=_next_block(br)
            if stored>=0:
                for _ in range(stored): buf.append(br.read(8))
                if block_final and len(buf)-base<want: break
                if not block_final:
                    block_final,ll2,dd2,stored2=_next_block(br)
                    if stored2>=0: raise ValueError("consecutive stored blocks unsupported by restart oracle")
            if ll2 is None or dd2 is None: break
            ll,dd=ll2,dd2; continue
        i=sym-257; ln=LEN_BASE[i]+(br.read(LEN_EXTRA[i]) if LEN_EXTRA[i] else 0)
        ds=dd.decode(br); dist=DIST_BASE[ds]+(br.read(DIST_EXTRA[ds]) if DIST_EXTRA[ds] else 0)
        if dist>len(buf): raise ValueError("restart history insufficient")
        for _ in range(ln): buf.append(buf[-dist])
    return bytes(buf[base:base+want]),(br.bitpos-cp.bitpos+7)//8


def _decode_prefix_incremental(stream:bytes,want:int)->tuple[bytes,int]:
    d=zlib.decompressobj(-15); out=bytearray(); pos=0; chunk=256
    while len(out)<want and pos<len(stream):
        part=stream[pos:pos+chunk]; pos+=len(part); out.extend(d.decompress(part,want-len(out)))
        if d.unconsumed_tail:
            pos-=len(d.unconsumed_tail)
        if d.eof: break
    return bytes(out[:want]),pos


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_restart_neutral")
    repair=V029._load(V029.REPAIR_PATH,"r4_restart_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source=corpus/"04_analytics_and_database"; expected_tree=PRODUCT.treehash(source)

    dual=work/"npz-owner"; t0=time.perf_counter(); dual_stats=DUAL._build_candidate(source,dual,work/"dual-work"); dual_wall=time.perf_counter()-t0
    verify=DUAL._extract_candidate(dual,work/"dual-extract")
    if verify["tree_sha256"]!=expected_tree: raise RuntimeError("NPZ-owner tree mismatch")

    rel=DUAL._npz_relation(source)["accepted"]
    fs=MODE2._feature_stream(source/rel["npz_path"],rel["member"]); npy=(source/rel["npy_path"]).read_bytes()
    cps,matches=_parse(fs["stream"],npy); cost=_state_cost(cps,npy)
    if not cps: raise RuntimeError("no restart checkpoints")

    probes=[]; starts=sorted(set([0,len(npy)//4,len(npy)//2,(3*len(npy))//4,max(0,len(npy)-RANGE)])); zdc=zstd.ZstdDecompressor()
    for target in starts:
        want=npy[target:target+RANGE]; eligible=[(i,cp) for i,cp in enumerate(cps) if cp.outpos<=target]
        if not eligible:
            got,consumed=_decode_prefix_incremental(fs["stream"],len(want)); hist_phys=hist_work=0; decoded_work=len(want)
        else:
            i,cp=eligible[-1]; hist=npy[cp.outpos-cp.required_history:cp.outpos]; hblob=cost["history_blobs"][i]; h2=zdc.decompress(hblob)
            if h2!=hist: raise RuntimeError("restart history compression mismatch")
            skip=target-cp.outpos; produced,consumed=_restart_decode(fs["stream"],cp,h2,skip+len(want)); got=produced[skip:skip+len(want)]
            hist_phys=len(hblob); hist_work=len(hist); decoded_work=len(hist)+skip+len(want)
        if got!=want: raise RuntimeError("restart selective read mismatch")
        physical=hist_phys+consumed+INDEX_AUTH_ALLOWANCE
        probes.append({"start":target,"requested_bytes":len(want),"history_physical_bytes":hist_phys,"compressed_stream_bytes_consumed":consumed,"authenticated_index_allowance_bytes":INDEX_AUTH_ALLOWANCE,"physical_bytes_touched":physical,"physical_amplification":physical/max(1,len(want)),"restart_history_work_bytes":hist_work,"decoded_work_bytes":decoded_work,"reconstruction_amplification":decoded_work/max(1,len(want))})

    restart_bytes=cost["total_restart_bytes"]+96
    candidate_bytes=dual_stats["stored_bytes"]+restart_bytes
    max_phys=max(x["physical_amplification"] for x in probes); max_recon=max(x["reconstruction_amplification"] for x in probes)
    supported=candidate_bytes<ACCEPTED_V029_ANALYTICS and max_phys<=8.0 and max_recon<=8.0
    return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"tree_sha256":expected_tree,"npz_owner_bytes":dual_stats["stored_bytes"],"restart_state_bytes":restart_bytes,"candidate_bytes":candidate_bytes,"accepted_v029_bytes":ACCEPTED_V029_ANALYTICS,"margin_vs_v029_bytes":ACCEPTED_V029_ANALYTICS-candidate_bytes,"npz_owner_build_wall_s":dual_wall,"feature_stream_bytes":len(fs["stream"]),"npy_bytes":len(npy),"checkpoint_span_bytes":SPAN,"checkpoint_count":len(cps),"match_count":len(matches),"restart_state":{k:cost[k] for k in ("history_raw_bytes","history_zstd_bytes","max_required_history_bytes","unique_huffman_states","huffman_state_zstd_bytes","index_bytes")},"selective_reads":probes,"max_physical_amplification":max_phys,"max_reconstruction_amplification":max_recon,"hypothesis":{"exact_npz_owner_tree":verify["tree_sha256"]==expected_tree,"restart_bundle_below_v029_analytics":candidate_bytes<ACCEPTED_V029_ANALYTICS,"cold_physical_amplification_le_8x":max_phys<=8.0,"cold_reconstruction_amplification_le_8x":max_recon<=8.0,"supported_for_product_prototype":supported},"contract":{"diagnostic_only":True,"release_credit":False,"production_format_changed":False,"production_selector_changed":False,"fixed_span_no_sweep":True,"actual_deflate_match_distances_measured":True,"huffman_states_deduplicated":True,"history_states_independently_compressed":True,"research_index_auth_allowance_not_final_physical_index":True,"same_semantic_tree_verified":True,"start_probe_uses_incremental_physical_stream_accounting":True,"final_block_state_persisted":True},"next_if_supported":"implement a file-backed authenticated restart index in a product-shaped prototype and replace the 1 KiB research allowance with measured proof/index I/O; then test portability/native decoder semantics","next_if_falsified":"preserve negative; do not weaken <=8x. Prefer another locally addressable density mechanism over duplicating a full NPY/NPZ view or serializing large compressor state."}


def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-npz-restart-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-npz-restart.json")); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+"\n"); print(json.dumps({k:d[k] for k in ("npz_owner_bytes","restart_state_bytes","candidate_bytes","accepted_v029_bytes","margin_vs_v029_bytes","feature_stream_bytes","npy_bytes","checkpoint_count","max_physical_amplification","max_reconstruction_amplification","hypothesis")}|{"restart_state":d["restart_state"]},indent=2))

if __name__=="__main__": main()
