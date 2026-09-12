from __future__ import annotations

"""Transfer the bounded local-window bit source to the frozen Office v7 candidate.

Mission lock
============
The synthetic exact-head referee showed that a page-local contiguous compressed window preserves the
same guarded physical reads while removing most Python segmented-source dispatch debt without an
archive-sized buffer.  This transfer keeps the accepted Office v7 representation/economics frozen at
5,952,805 B, the 644 B metadata grouping, 360 B locator/root charge, 4 KiB request and 8x limit.
It first re-runs the exact Office pread8 prerequisite, then replaces only the runtime bit source with
bounded page-local windows.  Both inherited fixed probes and every adjacent-page sufficient-condition
probe are charged actual unique pread bytes + the same whole metadata groups + locator/root.

Disproof
========
Any byte mismatch, uncovered logical compressed interval, window >32,768 B, or charged fixed/pair read
>32,768 B falsifies transfer.  Do not change the 8x law or representation to make this pass.
"""

import argparse,hashlib,json,os,time,zlib
from pathlib import Path
from benchmarks import v030_r4_bounded_token_guard_pread_referee as G
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from benchmarks import v030_r4_office_sparse_superframe_economic_referee as SUPER
from benchmarks import v030_r4_office_gated_seed_superframe_economic_referee as SEEDGROUP
from benchmarks import v030_r4_office_group_charge_locality_referee as GROUP
from benchmarks import v030_r4_office_payload_pread8_referee as PREAD8
from benchmarks import v030_r4_pread_bit_source_referee as SRC
from benchmarks import v030_r4_window_guard_dispatch_referee as WINDOW

SCHEMA='cmpct-v030-r4-office-window-guard-transfer-v1';PAGE=4096;LIMIT=8*PAGE

class WindowSeedReader(SEED.SeedReader):
    def _decode_page(self,page:int,depth:int)->bytes:
        cached=self.page_cache.get(page)
        if cached is not None:return cached
        anchor=self.anchors[page];self.anchor_frames.add(page);page_base=page*PAGE;page_end=min(page_base+PAGE,self.output_bytes)
        out_start=anchor['token_start'];out_pos=out_start;local=bytearray();bid=anchor['block_id'];base,window=self.comp.ensure_page(page)
        br=WINDOW.AbsoluteWindowBitReader(window,base,anchor['bit_start']);segment_start=br.bit;tables=self._tables(bid)
        def finish_segment():
            nonlocal segment_start
            a=segment_start//8;b=(br.bit+7)//8
            if b>a:self.payload_ranges.append((a,b))
            segment_start=br.bit
        while out_pos<page_end:
            if self.symbols_decoded>SEED.MAX_DECODE_SYMBOLS:raise RuntimeError('decode symbol resource bound exceeded')
            block=self.blocks[bid]
            if out_pos>=block['out_end']:
                finish_segment();bid+=1
                if bid>=len(self.blocks):raise RuntimeError('ran beyond final DEFLATE block')
                block=self.blocks[bid];br.bit=block['first_token_bit'];segment_start=br.bit;tables=self._tables(bid)
            token_start=out_pos
            if block['type']==0:
                sym=br.read(8);self.symbols_decoded+=1;token=bytes([sym])
            else:
                ll,dd=tables;sym=CONE._decode(br,ll);self.symbols_decoded+=1
                if sym<256:token=bytes([sym])
                elif sym==256:
                    if out_pos!=block['out_end']:raise RuntimeError('early EOB relative to persisted block state')
                    continue
                elif 257<=sym<=285:
                    li=sym-257;length=CONE.LEN_BASE[li]+br.read(CONE.LEN_EXTRA[li]);ds=CONE._decode(br,dd)
                    if ds>=len(CONE.DIST_BASE):raise RuntimeError('invalid distance symbol')
                    distance=CONE.DIST_BASE[ds]+br.read(CONE.DIST_EXTRA[ds])
                    if distance>out_pos:raise RuntimeError('distance beyond output')
                    seed_len=min(distance,length);src0=out_pos-distance;src1=src0+seed_len;seed=bytearray()
                    if src0<out_start:
                        prior_end=min(src1,out_start);seed+=self._seed_read(page,src0,prior_end);src0=prior_end
                    if src0<src1:
                        lo=src0-out_start;hi=src1-out_start
                        if lo<0 or hi>len(local):raise RuntimeError('local LZ77 history unavailable')
                        seed+=local[lo:hi]
                    if len(seed)!=seed_len or not seed:raise RuntimeError('failed to reconstruct LZ77 seed')
                    token=bytes((seed*((length+len(seed)-1)//len(seed)))[:length])
                else:raise RuntimeError('reserved literal/length symbol')
            local+=token;out_pos=token_start+len(token)
        finish_segment();begin=page_base-out_start
        if begin<0 or page_end-out_start>len(local):raise RuntimeError('page reconstruction bounds mismatch')
        page_bytes=bytes(local[begin:page_end-out_start])
        if len(page_bytes)!=page_end-page_base:raise RuntimeError('short page reconstruction')
        self.page_cache[page]=page_bytes;return page_bytes

def _prepare(parsed,raw,anchors,blocks,si):
    seeds,_all,_logical=SEED._build_seeds(parsed,anchors,raw);brecs,arecs=SUPER._encoded_records(parsed)
    bmap,bcost,btotal=PREAD8._pack644([(int(r['key']),r['encoded']) for r in brecs],f's{si}:b')
    amap,acost,atotal=PREAD8._pack644([(int(r['key']),r['encoded']) for r in arecs],f's{si}:a')
    pages=len(anchors);unsafe=set();selected=set()
    for p in range(pages):
        a=p*PAGE;b=min(len(raw),min(pages,p+2)*PAGE);r=COLD.ColdReader(raw if False else parsed.get('_never',b''),anchors,blocks,len(raw))
        # classifier must use the real compressed stream; caller overwrites below.
    return seeds,bmap,bcost,btotal,amap,acost,atotal

def run(work:Path,v029_checkout:Path,worker:Path)->dict:
    t0=time.perf_counter();base=PREAD8.run(work,v029_checkout,worker)
    if not base['hypothesis']['eight_byte_exact_start_pread_refill_preserves_office_8x']:raise RuntimeError('frozen Office pread8 prerequisite no longer supported')
    if base['frozen_v7']['candidate_bytes']!=5_952_805 or base['frozen_v7']['grouped_metadata_bytes']!=48_787:raise RuntimeError('frozen v7 economics drift')
    manifest=json.loads((work/'current'/'manifest.json').read_text());pool=(work/'current'/'streams.bin').read_bytes();hashes=sorted({r['stream_hash'] for r in manifest['derived'].values()})
    fixed=pair=exact_fail=locality_fail=pair_fail=cover_fail=0;worst=None;worst_pair=None;max_window=0;physical_total=logical_total=0
    for si,h in enumerate(hashes):
        s=manifest['stream_index'][h];comp=pool[s['o']:s['o']+s['n']];parsed=DEP.parse_tokens(comp);raw=zlib.decompress(comp,-15);anchors,blocks,_=COLD._build_metadata(parsed)
        seeds,_all,_logical=SEED._build_seeds(parsed,anchors,raw);brecs,arecs=SUPER._encoded_records(parsed)
        bmap,bcost,_=PREAD8._pack644([(int(r['key']),r['encoded']) for r in brecs],f's{si}:b');amap,acost,_=PREAD8._pack644([(int(r['key']),r['encoded']) for r in arecs],f's{si}:a')
        pages=len(anchors);unsafe=set();selected=set()
        for p in range(pages):
            a=p*PAGE;b=min(len(raw),min(pages,p+2)*PAGE);r=COLD.ColdReader(comp,anchors,blocks,len(raw))
            if r.read(a,b)!=raw[a:b]:raise RuntimeError('classifier exactness drift')
            if r.metadata_bytes()+r.payload_bytes()>LIMIT:
                unsafe.add(p);selected.add(p)
                if p+1<pages:selected.add(p+1)
        gated=[None]*pages;seed_records=[]
        for p in sorted(selected):
            if seeds[p] is None:continue
            enc=GROUP._seed_enc(p,anchors[p],parsed,raw)
            if enc is None or hashlib.sha256(enc).hexdigest()!=seeds[p]['frame_sha256']:raise RuntimeError('seed parity drift')
            gated[p]=seeds[p];seed_records.append((p,enc))
        smap,scost,_=PREAD8._pack644(seed_records,f's{si}:s');costs={**bcost,**acost,**scost}
        path=work/f'window-stream-{si}.deflate';path.write_bytes(comp);fd=os.open(path,os.O_RDONLY)
        try:
            def probe(a,b,seed_mode):
                src=WINDOW.WindowGuardedSource(fd,len(comp),anchors);cls=WindowSeedReader if seed_mode else WINDOW.WindowGuardedReader
                r=cls(src,anchors,blocks,gated,len(raw)) if seed_mode else cls(src,anchors,blocks,len(raw));got=r.read(a,b)
                physical=SRC._bytes(src.physical_ranges());meta=GROUP._charge_groups(r,amap,bmap,smap,costs);combined=physical+meta+PREAD8.LOCATOR_ROOT_CHARGE
                return got,r,src,physical,meta,combined,SRC._covers(src.ranges,r.payload_ranges)
            for p in range(pages):
                a=p*PAGE;b=min(len(raw),min(pages,p+2)*PAGE);got,r,src,physical,meta,combined,covered=probe(a,b,p in unsafe);pair+=1;logical_total+=r.payload_bytes();physical_total+=physical;max_window=max(max_window,src.max_live_window_bytes)
                if got!=raw[a:b] or combined>LIMIT or not covered:pair_fail+=1
                q={'stream_sha256':h,'pair_start_page':p,'logical_payload_bytes':r.payload_bytes(),'physical_payload_bytes':physical,'metadata_bytes':meta,'combined_bytes':combined,'slack_bytes':LIMIT-combined,'calls':src.calls,'max_live_window_bytes':src.max_live_window_bytes,'covered':covered}
                if worst_pair is None or combined>worst_pair['combined_bytes']:worst_pair=q
            for start in TRANSFER._starts(len(raw)):
                end=min(start+PAGE,len(raw));p0=start//PAGE;p1=(end-1)//PAGE;seed_mode=(p0 in unsafe) if p1!=p0 else (p0 in unsafe or (p0>0 and (p0-1) in unsafe))
                got,r,src,physical,meta,combined,covered=probe(start,end,seed_mode);fixed+=1;logical_total+=r.payload_bytes();physical_total+=physical;max_window=max(max_window,src.max_live_window_bytes)
                if got!=raw[start:end]:exact_fail+=1
                if combined>LIMIT:locality_fail+=1
                if not covered:cover_fail+=1
                q={'stream_sha256':h,'start':start,'end':end,'logical_payload_bytes':r.payload_bytes(),'physical_payload_bytes':physical,'metadata_bytes':meta,'combined_bytes':combined,'slack_bytes':LIMIT-combined,'calls':src.calls,'max_live_window_bytes':src.max_live_window_bytes,'covered':covered}
                if worst is None or combined>worst['combined_bytes']:worst=q
        finally:os.close(fd)
    supported=exact_fail==0 and locality_fail==0 and pair_fail==0 and cover_fail==0 and max_window<=LIMIT
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'frozen_v7':base['frozen_v7'],'baseline_pread8':{'total_logical_payload_bytes':base['physical_refill']['total_logical_payload_bytes'],'total_physical_payload_bytes':base['physical_refill']['total_pread_payload_bytes'],'total_pread_calls':base['physical_refill']['total_pread_calls'],'worst_fixed_probe':base['physical_refill']['worst_fixed_probe'],'worst_page_pair':base['physical_refill']['worst_page_pair']},'window_transfer':{'fixed_requests':fixed,'pair_requests':pair,'exact_failures':exact_fail,'locality_failures':locality_fail,'pair_failures':pair_fail,'coverage_failures':cover_fail,'total_logical_payload_bytes':logical_total,'total_physical_payload_bytes':physical_total,'physical_minus_logical_bytes':physical_total-logical_total,'max_live_window_bytes':max_window,'worst_fixed_probe':worst,'worst_page_pair':worst_pair},'profile':{'wall_s_including_pread8_prerequisite':time.perf_counter()-t0},'hypothesis':{'bounded_window_dispatch_transfers_to_frozen_office_v7_under_8x':supported},'contract':{'diagnostic_only':True,'release_credit':False,'candidate_bytes_unchanged':True,'same_644b_metadata_groups':True,'same_locator_root_charge':True,'same_8x_limit':True,'same_seed_selector':True,'actual_os_pread_drives_bit_decoder':True,'no_archive_sized_compressed_buffer':True,'no_threshold_sweep':True,'remaining_debt':'if supported: isolate throughput/RSS then integrate serialized auth/root/recovery/native; if false: preserve exact guard overfetch and redesign range ownership without moving 8x'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-window-work'));p.add_argument('--v029-checkout',type=Path,required=True);p.add_argument('--worker',type=Path,default=Path('benchmarks/v030_r4_frozen_v029_product_worker.py'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-window-guard-transfer.json'));a=p.parse_args();d=run(a.work_root,a.v029_checkout,a.worker);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'window_transfer':d['window_transfer'],'hypothesis':d['hypothesis'],'profile':d['profile']},sort_keys=True))
if __name__=='__main__':main()
