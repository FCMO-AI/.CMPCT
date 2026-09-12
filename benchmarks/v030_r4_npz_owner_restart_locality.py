from __future__ import annotations

"""Falsifier for the opposite Analytics ownership boundary: exact NPZ owner + compact restart state.

The full dual-view experiment proved that duplicating both exact NPZ and localized NPY buys good
locality but costs ~3.58 MB over Mode2 and loses the v0.29 Analytics floor. Mode2's single NPY owner
is dense but cannot reproduce arbitrary slices of the exact monolithic Deflate stream locally.

This experiment therefore moves ownership back to the exact NPZ (the earlier dual-owner seed) and
asks whether the *derived NPY* can be made locally readable with compact, independently authenticated
Deflate-inflation restart state. This direction is structurally cheaper because an inflater restart
needs only prior output history + Huffman/bit position; it does not need the much larger/nonportable
compressor search state required to recreate a monolithic Deflate stream from the middle.

The implementation uses a tiny research Deflate decoder to record symbol-boundary access points at a
fixed 27 KiB output span, computes the actually-required suffix of the 32 KiB history for each point,
compresses each history independently with zstd, deduplicates Huffman tables, and verifies cold 4 KiB
reads by restarting from the saved bit position/state. All restart bytes are charged on top of the
exact-NPZ-owner research bundle. No shipping format/selector/version change is implied.
"""

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import struct
import tempfile
import time
from typing import Iterable

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

LEN_BASE = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
LEN_EXTRA = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0]
DIST_BASE = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
DIST_EXTRA = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13]
CL_ORDER = [16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]


def _rev(v: int, n: int) -> int:
    r = 0
    for _ in range(n):
        r = (r << 1) | (v & 1); v >>= 1
    return r


class Bits:
    def __init__(self, data: bytes, bitpos: int = 0): self.data=data; self.bitpos=bitpos
    def read(self, n: int) -> int:
        if self.bitpos+n > len(self.data)*8: raise EOFError("truncated deflate")
        v=0
        for i in range(n):
            p=self.bitpos+i; v |= ((self.data[p>>3] >> (p&7)) & 1) << i
        self.bitpos += n; return v
    def align(self) -> None: self.bitpos=(self.bitpos+7)&~7


class Huff:
    def __init__(self, lengths: Iterable[int]):
        self.lengths=tuple(int(x) for x in lengths); counts={}
        for n in self.lengths:
            if n: counts[n]=counts.get(n,0)+1
        code=0; next_code={}
        for bits in range(1, max(counts,default=0)+1):
            code=(code+counts.get(bits-1,0))<<1; next_code[bits]=code
        self.map={}
        for sym,n in enumerate(self.lengths):
            if not n: continue
            c=next_code[n]; next_code[n]+=1; self.map[(n,_rev(c,n))]=sym
        self.maxbits=max(counts,default=0)
    def decode(self, br: Bits) -> int:
        code=0
        for n in range(1,self.maxbits+1):
            code |= br.read(1) << (n-1)
            s=self.map.get((n,code))
            if s is not None: return s
        raise ValueError("invalid Huffman code")


def _fixed() -> tuple[Huff,Huff]:
    ll=[0]*288
    for i in range(0,144): ll[i]=8
    for i in range(144,256): ll[i]=9
    for i in range(256,280): ll[i]=7
    for i in range(280,288): ll[i]=8
    return Huff(ll), Huff([5]*32)


def _dynamic(br: Bits) -> tuple[Huff,Huff]:
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
    return Huff(vals[:hlit]), Huff(vals[hlit:])


@dataclass
class CP:
    outpos: int
    bitpos: int
    ll: tuple[int,...]
    dd: tuple[int,...]
    required_history: int = 0


def _parse(stream: bytes, expected: bytes) -> tuple[list[CP], list[tuple[int,int,int]], bytes]:
    br=Bits(stream); out=bytearray(); cps=[]; matches=[]; next_cp=SPAN; final=False
    current: tuple[Huff,Huff] | None=None
    while not final:
        final=bool(br.read(1)); typ=br.read(2)
        if typ==0:
            br.align(); ln=br.read(16); nln=br.read(16)
            if (ln ^ 0xFFFF) != nln: raise ValueError("stored block length mismatch")
            for _ in range(ln):
                if len(out)>=next_cp:
                    # A byte-aligned stored block needs no history/table; encode empty tables.
                    cps.append(CP(len(out),br.bitpos,(),())); next_cp=len(out)+SPAN
                out.append(br.read(8))
            current=None; continue
        if typ==1: current=_fixed()
        elif typ==2: current=_dynamic(br)
        else: raise ValueError("reserved deflate block")
        ll,dd=current
        while True:
            if len(out)>=next_cp:
                cps.append(CP(len(out),br.bitpos,ll.lengths,dd.lengths)); next_cp=len(out)+SPAN
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
    if bytes(out)!=expected: raise RuntimeError("research Deflate parser output mismatch")
    # Required pre-checkpoint suffix: maximum portion of any post-checkpoint match that reaches before cp.
    for cp in cps:
        need=0
        for s,ln,dist in matches:
            if s<cp: continue
            if s-cp>=WINDOW: break
            need=max(need, max(0, dist-(s-cp)))
        cp.required_history=min(WINDOW,need)
    return cps,matches,bytes(out)


def _table_key(cp: CP) -> bytes: return bytes(cp.ll)+b"\xff"+bytes(cp.dd)


def _state_cost(cps: list[CP], source: bytes) -> dict:
    zc=zstd.ZstdCompressor(level=3)
    histories=[]; table_ids={}; table_blobs=[]; index_bytes=0
    max_hist=0
    for cp in cps:
        hist=source[max(0,cp.outpos-cp.required_history):cp.outpos]
        blob=zc.compress(hist); histories.append(blob); max_hist=max(max_hist,len(hist))
        key=_table_key(cp)
        if key not in table_ids:
            table_ids[key]=len(table_blobs); table_blobs.append(zc.compress(key))
        # outpos, bitpos, history offset/len, table id, required history len
        index_bytes += 8+8+8+4+4+4
    return {
        "history_raw_bytes":sum(cp.required_history for cp in cps),
        "history_zstd_bytes":sum(len(x) for x in histories),
        "history_frame_count":len(histories),
        "max_required_history_bytes":max_hist,
        "unique_huffman_states":len(table_blobs),
        "huffman_state_zstd_bytes":sum(len(x) for x in table_blobs),
        "index_bytes":index_bytes,
        "total_restart_bytes":sum(len(x) for x in histories)+sum(len(x) for x in table_blobs)+index_bytes,
        "history_blobs":histories,
        "table_ids":table_ids,
        "table_blobs":table_blobs,
    }


def _next_block(br: Bits) -> tuple[bool,Huff|None,Huff|None,int]:
    final=bool(br.read(1)); typ=br.read(2)
    if typ==0:
        br.align(); ln=br.read(16); nln=br.read(16)
        if (ln^0xffff)!=nln: raise ValueError("stored block mismatch")
        return final,None,None,ln
    if typ==1: ll,dd=_fixed(); return final,ll,dd,-1
    if typ==2: ll,dd=_dynamic(br); return final,ll,dd,-1
    raise ValueError("reserved block")


def _restart_decode(stream: bytes, cp: CP, history: bytes, want: int) -> tuple[bytes,int]:
    # Checkpoints are symbol boundaries inside Huffman blocks in this corpus. Empty-table checkpoints
    # (stored blocks) are deliberately rejected rather than silently overclaiming support.
    if not cp.ll: raise ValueError("stored-block checkpoint unsupported by this oracle")
    br=Bits(stream,cp.bitpos); ll=Huff(cp.ll); dd=Huff(cp.dd); buf=bytearray(history); start=len(buf); final=False
    while len(buf)-start < want:
        sym=ll.decode(br)
        if sym<256: buf.append(sym); continue
        if sym==256:
            if final: break
            final,ll,dd,stored=_next_block(br)
            if stored>=0:
                for _ in range(stored): buf.append(br.read(8))
            continue
        i=sym-257; ln=LEN_BASE[i]+(br.read(LEN_EXTRA[i]) if LEN_EXTRA[i] else 0); ds=dd.decode(br); dist=DIST_BASE[ds]+(br.read(DIST_EXTRA[ds]) if DIST_EXTRA[ds] else 0)
        if dist>len(buf): raise ValueError("restart history insufficient")
        for _ in range(ln): buf.append(buf[-dist])
    return bytes(buf[start:start+want]), (br.bitpos-cp.bitpos+7)//8


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_restart_neutral"); repair=V029._load(V029.REPAIR_PATH,"r4_restart_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"04_analytics_and_database"; expected_tree=PRODUCT.treehash(source)

    dual=work/"npz-owner"; t0=time.perf_counter(); dual_stats=DUAL._build_candidate(source,dual,work/"dual-work"); dual_wall=time.perf_counter()-t0
    verify=DUAL._extract_candidate(dual,work/"dual-extract")
    if verify["tree_sha256"]!=expected_tree: raise RuntimeError("NPZ-owner tree mismatch")

    rel=DUAL._npz_relation(source)["accepted"]; fs=MODE2._feature_stream(source/rel["npz_path"],rel["member"]); npy=(source/rel["npy_path"]).read_bytes()
    cps,matches,decoded=_parse(fs["stream"],npy); cost=_state_cost(cps,npy)
    if not cps: raise RuntimeError("no restart checkpoints")

    # Verify representative cold restarts and account physical + reconstruction work. We read the
    # independently-compressed history state plus exact compressed-stream bytes consumed. Root/index
    # authentication is conservatively charged as 1 KiB per cold request; final product must replace
    # this research allowance with measured authenticated index I/O.
    probes=[]
    starts=sorted(set([0,len(npy)//4,len(npy)//2,(3*len(npy))//4,max(0,len(npy)-RANGE)]))
    zdc=zstd.ZstdDecompressor()
    for target in starts:
        eligible=[(i,cp) for i,cp in enumerate(cps) if cp.outpos<=target]
        if eligible: i,cp=eligible[-1]
        else:
            # Start-of-stream is intrinsically local: decode from the stream beginning.
            cp=None
        if cp is None:
            # Use ordinary zlib only for the very first range; charge bytes conservatively by the
            # compressed prefix consumed estimate from full stream ratio.
            import zlib
            raw=zlib.decompress(fs["stream"],-15)[:RANGE]; got=raw; consumed=min(len(fs["stream"]),int(len(fs["stream"])*RANGE/max(1,len(npy)))+64); hist_phys=0; hist_work=0; decoded_work=RANGE
        else:
            hist=npy[cp.outpos-cp.required_history:cp.outpos]
            hblob=cost["history_blobs"][i]; h2=zdc.decompress(hblob)
            if h2!=hist: raise RuntimeError("restart history compression mismatch")
            skip=target-cp.outpos; produced,consumed=_restart_decode(fs["stream"],cp,h2,skip+RANGE); got=produced[skip:skip+RANGE]
            hist_phys=len(hblob); hist_work=len(hist); decoded_work=len(hist)+skip+RANGE
        want=npy[target:target+RANGE]
        if got[:len(want)]!=want: raise RuntimeError("restart selective read mismatch")
        requested=len(want); physical=hist_phys+consumed+1024
        probes.append({"start":target,"requested_bytes":requested,"history_physical_bytes":hist_phys,"compressed_stream_bytes_consumed":consumed,"authenticated_index_allowance_bytes":1024,"physical_bytes_touched":physical,"physical_amplification":physical/max(1,requested),"restart_history_work_bytes":hist_work,"decoded_work_bytes":decoded_work,"reconstruction_amplification":decoded_work/max(1,requested)})

    restart_bytes=cost["total_restart_bytes"]+96  # compact auth roots for three restart files
    candidate_bytes=dual_stats["stored_bytes"]+restart_bytes
    max_phys=max(x["physical_amplification"] for x in probes); max_recon=max(x["reconstruction_amplification"] for x in probes)
    supported=candidate_bytes<ACCEPTED_V029_ANALYTICS and max_phys<=8.0 and max_recon<=8.0
    return {
        "schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"tree_sha256":expected_tree,
        "npz_owner_bytes":dual_stats["stored_bytes"],"restart_state_bytes":restart_bytes,"candidate_bytes":candidate_bytes,"accepted_v029_bytes":ACCEPTED_V029_ANALYTICS,"margin_vs_v029_bytes":ACCEPTED_V029_ANALYTICS-candidate_bytes,
        "npz_owner_build_wall_s":dual_wall,"feature_stream_bytes":len(fs["stream"]),"npy_bytes":len(npy),"checkpoint_span_bytes":SPAN,"checkpoint_count":len(cps),"match_count":len(matches),
        "restart_state":{"history_raw_bytes":cost["history_raw_bytes"],"history_zstd_bytes":cost["history_zstd_bytes"],"max_required_history_bytes":cost["max_required_history_bytes"],"unique_huffman_states":cost["unique_huffman_states"],"huffman_state_zstd_bytes":cost["huffman_state_zstd_bytes"],"index_bytes":cost["index_bytes"]},
        "selective_reads":probes,"max_physical_amplification":max_phys,"max_reconstruction_amplification":max_recon,
        "hypothesis":{"exact_npz_owner_tree":verify["tree_sha256"]==expected_tree,"restart_bundle_below_v029_analytics":candidate_bytes<ACCEPTED_V029_ANALYTICS,"cold_physical_amplification_le_8x":max_phys<=8.0,"cold_reconstruction_amplification_le_8x":max_recon<=8.0,"supported_for_product_prototype":supported},
        "contract":{"diagnostic_only":True,"release_credit":False,"production_format_changed":False,"production_selector_changed":False,"fixed_span_no_sweep":True,"actual_deflate_match_distances_measured":True,"huffman_states_deduplicated":True,"history_states_independently_compressed":True,"research_index_auth_allowance_not_final_physical_index":True,"same_semantic_tree_verified":True},
        "next_if_supported":"implement file-backed authenticated restart index in a product-shaped prototype and replace the 1 KiB research auth allowance with measured proof/index I/O; then test portability/native decoder semantics",
        "next_if_falsified":"preserve negative; do not weaken <=8x. Prefer another locally addressable density mechanism over duplicating a full NPY/NPZ view or serializing large compressor state."
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-npz-restart-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-npz-restart.json")); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+"\n"); print(json.dumps({k:d[k] for k in ("npz_owner_bytes","restart_state_bytes","candidate_bytes","accepted_v029_bytes","margin_vs_v029_bytes","feature_stream_bytes","npy_bytes","checkpoint_count","max_physical_amplification","max_reconstruction_amplification","hypothesis")}|{"restart_state":d["restart_state"]},indent=2))

if __name__=="__main__": main()
