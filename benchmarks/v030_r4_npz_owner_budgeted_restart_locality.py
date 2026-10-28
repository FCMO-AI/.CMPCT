from __future__ import annotations

"""Falsifier for budget-driven, rather than fixed-span, NPZ-owner restart placement.

The fixed 27 KiB restart experiment missed all three relevant laws narrowly: +71,549 B over the v0.29
Analytics floor, 8.627x physical, 9.053x reconstruction. Its receipt showed the failure is heterogeneous:
four of five probes already satisfy locality, while the middle probe carries ~20.6 KiB history plus
~12.35 KiB skip. Restart storage is dominated by independently stored histories.

This experiment does NOT sweep checkpoint spacing. Candidate restart points are sampled on a 4 KiB
output lattice because 4 KiB is the frozen selective request unit. A greedy interval-cover algorithm
then chooses only points required to keep the reconstruction cone under the inherited 8x law. Selection
uses only raw reconstruction geometry (required history + forward skip + request), never stored-size or
v0.29 outcomes. After selection, all chosen histories/Huffman/index bytes are charged and exact cold
reads at every region boundary measure both physical and reconstruction amplification.

Advance requires: exact tree, candidate < accepted v0.29 Analytics 6,135,172 B, every measured region
boundary <=8x physical and <=8x reconstruction. No post-result span tuning is allowed.

An infeasible interval cover is itself a scientific negative, not a harness failure. In that case this
falsifier emits a complete negative receipt identifying the exact coverage frontier instead of raising
before evidence persistence. That changes only evidence handling; candidate selection and the 8x budget
remain frozen.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import zlib

import zstandard as zstd

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_npz_mode2_owner_inversion as MODE2
from benchmarks import v030_r4_npz_owner_restart_locality as FIXED
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-npz-owner-budgeted-restart-locality-v1"
REQUEST = 4096
BUDGET = 8 * REQUEST
LATTICE = REQUEST
ACCEPTED_V029_ANALYTICS = 6_135_172
INDEX_AUTH_ALLOWANCE = 1024


def _candidates(stream: bytes, npy: bytes):
    old = FIXED.SPAN
    FIXED.SPAN = LATTICE
    try:
        cps, matches = FIXED._parse(stream, npy)
    finally:
        FIXED.SPAN = old
    return cps, matches


def _reach(cp) -> int:
    # A cold request starting at cp may reconstruct at most BUDGET total bytes. History initialization
    # is reconstruction work too; the remaining forward distance is therefore fixed by the product law.
    return cp.outpos + max(0, BUDGET - REQUEST - cp.required_history)


def _select(cps, logical_size: int):
    # The start-of-stream is an implicit checkpoint with zero history and BUDGET-REQUEST forward reach.
    chosen=[]; covered=BUDGET-REQUEST; cursor=0
    while covered < logical_size - REQUEST:
        eligible=[]
        while cursor < len(cps) and cps[cursor].outpos <= covered:
            cp=cps[cursor]; cursor+=1
            if _reach(cp) > covered:
                eligible.append(cp)
        # Cursor has consumed older candidates, so keep a reservoir of all points in the current overlap
        # by scanning cps directly. This is small (~1k points) and makes the interval-cover rule obvious.
        eligible=[cp for cp in cps if cp.outpos <= covered and _reach(cp) > covered and cp not in chosen]
        if not eligible:
            return chosen, covered, {
                'feasible': False,
                'failure_reason': f'reconstruction budget cannot cover output beyond {covered}',
                'failure_covered_output_bytes': covered,
            }
        best=max(eligible,key=lambda cp:(_reach(cp),-cp.required_history,cp.outpos))
        chosen.append(best); new=_reach(best)
        if new <= covered:
            return chosen, covered, {
                'feasible': False,
                'failure_reason': 'restart cover did not advance',
                'failure_covered_output_bytes': covered,
            }
        covered=new
    return chosen, covered, {
        'feasible': True,
        'failure_reason': None,
        'failure_covered_output_bytes': None,
    }


def _decode_prefix(stream: bytes, want: int):
    d=zlib.decompressobj(-15); out=bytearray(); pos=0
    while len(out)<want and pos<len(stream):
        part=stream[pos:pos+256]; pos+=len(part); out.extend(d.decompress(part,want-len(out)))
        if d.unconsumed_tail: pos-=len(d.unconsumed_tail)
        if d.eof: break
    return bytes(out[:want]),pos


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_budget_restart_neutral'); repair=V029._load(V029.REPAIR_PATH,'r4_budget_restart_repair'); repair.install_generation_hooks(neutral)
    corpus=work/'neutral'; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/'04_analytics_and_database'; expected=PRODUCT.treehash(source)

    bundle=work/'npz-owner'; owner=DUAL._build_candidate(source,bundle,work/'owner-work'); verify=DUAL._extract_candidate(bundle,work/'extract')
    if verify['tree_sha256']!=expected: raise RuntimeError('NPZ-owner semantic tree mismatch')
    rel=DUAL._npz_relation(source)['accepted']; fs=MODE2._feature_stream(source/rel['npz_path'],rel['member']); npy=(source/rel['npy_path']).read_bytes()
    candidates,matches=_candidates(fs['stream'],npy); chosen,covered,selection=_select(candidates,len(npy)); state=FIXED._state_cost(chosen,npy)

    if not selection['feasible']:
        # There is no complete representation satisfying the frozen 8x reconstruction geometry. Charge
        # every state selected before the impossibility frontier so this negative cannot hide prefix cost,
        # but do not report a synthetic candidate size or locality maximum for a layout that cannot exist.
        partial_restart_bytes=state['total_restart_bytes']+96
        return {
            'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'tree_sha256':expected,
            'npz_owner_bytes':owner['stored_bytes'],'candidate_lattice_bytes':LATTICE,
            'candidate_restart_points':len(candidates),'selected_restart_points':len(chosen),
            'coverage_end':covered,'logical_npy_bytes':len(npy),'match_count':len(matches),
            'selection_feasible':False,'selection_failure_reason':selection['failure_reason'],
            'restart_state_bytes':partial_restart_bytes,'candidate_bytes':None,
            'accepted_v029_bytes':ACCEPTED_V029_ANALYTICS,'margin_vs_v029_bytes':None,
            'restart_state':{k:state[k] for k in ('history_raw_bytes','history_zstd_bytes','max_required_history_bytes','unique_huffman_states','huffman_state_zstd_bytes','index_bytes')},
            'selective_region_boundary_reads':[], 'max_physical_amplification':None,
            'max_reconstruction_amplification':None,
            'hypothesis':{
                'exact_npz_owner_tree':verify['tree_sha256']==expected,
                'reconstruction_budget_covers_stream':False,
                'budgeted_restart_bundle_below_v029':False,
                'all_region_boundaries_physical_le_8x':False,
                'all_region_boundaries_reconstruction_le_8x':False,
                'supported_for_product_prototype':False,
            },
            'contract':{
                'diagnostic_only':True,'release_credit':False,'production_format_changed':False,
                'production_selector_changed':False,'no_span_sweep':True,
                'candidate_lattice_equals_request_size':True,
                'placement_uses_locality_budget_not_size_outcome':True,
                'all_selected_histories_fully_charged':True,
                'every_service_region_endpoint_verified':False,
                'infeasible_selection_is_scientific_negative':True,
                'research_index_auth_allowance_not_final_product_proof':True,
            },
            'next_if_supported':'implement authenticated shared-history/file-backed restart index and validate held-out Deflate streams before product integration',
            'next_if_falsified':'preserve negative and retire independent-history restart placement unless a separately motivated shared-history mechanism demonstrates causal savings without weakening locality',
        }

    # Define disjoint service regions: start-of-stream serves until first chosen checkpoint; each chosen
    # checkpoint serves until the next one (or EOF). Probe the end of every region, where forward work is
    # maximal; correctness at each endpoint exercises every selected restart state.
    boundaries=[cp.outpos for cp in chosen]+[len(npy)]
    probes=[]; zdc=zstd.ZstdDecompressor()
    first_end=boundaries[0] if boundaries else len(npy)
    target=max(0,min(first_end-REQUEST,BUDGET-REQUEST))
    want=npy[target:target+REQUEST]; got,consumed=_decode_prefix(fs['stream'],target+len(want)); got=got[target:target+len(want)]
    if got!=want: raise RuntimeError('start-region selective mismatch')
    probes.append({'checkpoint':'start','target':target,'requested_bytes':len(want),'required_history_bytes':0,'skip_bytes':target,'history_physical_bytes':0,'compressed_stream_bytes_consumed':consumed,'physical_bytes_touched':consumed+INDEX_AUTH_ALLOWANCE,'physical_amplification':(consumed+INDEX_AUTH_ALLOWANCE)/max(1,len(want)),'reconstruction_bytes':target+len(want),'reconstruction_amplification':(target+len(want))/max(1,len(want))})

    for i,cp in enumerate(chosen):
        region_end=boundaries[i+1]; target=max(cp.outpos,min(region_end-REQUEST,_reach(cp)-REQUEST)); target=max(cp.outpos,target)
        want=npy[target:target+REQUEST]; hist=npy[cp.outpos-cp.required_history:cp.outpos]; hblob=state['history_blobs'][i]; h2=zdc.decompress(hblob)
        if h2!=hist: raise RuntimeError('history frame mismatch')
        skip=target-cp.outpos; produced,consumed=FIXED._restart_decode(fs['stream'],cp,h2,skip+len(want)); got=produced[skip:skip+len(want)]
        if got!=want: raise RuntimeError('budgeted restart selective mismatch')
        physical=len(hblob)+consumed+INDEX_AUTH_ALLOWANCE; recon=len(hist)+skip+len(want)
        probes.append({'checkpoint':i,'checkpoint_outpos':cp.outpos,'target':target,'requested_bytes':len(want),'required_history_bytes':len(hist),'skip_bytes':skip,'history_physical_bytes':len(hblob),'compressed_stream_bytes_consumed':consumed,'physical_bytes_touched':physical,'physical_amplification':physical/max(1,len(want)),'reconstruction_bytes':recon,'reconstruction_amplification':recon/max(1,len(want))})

    restart_bytes=state['total_restart_bytes']+96; candidate=owner['stored_bytes']+restart_bytes; max_phys=max(x['physical_amplification'] for x in probes); max_recon=max(x['reconstruction_amplification'] for x in probes)
    supported=candidate<ACCEPTED_V029_ANALYTICS and max_phys<=8.0 and max_recon<=8.0
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'tree_sha256':expected,'npz_owner_bytes':owner['stored_bytes'],'candidate_lattice_bytes':LATTICE,'candidate_restart_points':len(candidates),'selected_restart_points':len(chosen),'coverage_end':covered,'logical_npy_bytes':len(npy),'match_count':len(matches),'selection_feasible':True,'selection_failure_reason':None,'restart_state_bytes':restart_bytes,'candidate_bytes':candidate,'accepted_v029_bytes':ACCEPTED_V029_ANALYTICS,'margin_vs_v029_bytes':ACCEPTED_V029_ANALYTICS-candidate,'restart_state':{k:state[k] for k in ('history_raw_bytes','history_zstd_bytes','max_required_history_bytes','unique_huffman_states','huffman_state_zstd_bytes','index_bytes')},'selective_region_boundary_reads':probes,'max_physical_amplification':max_phys,'max_reconstruction_amplification':max_recon,'hypothesis':{'exact_npz_owner_tree':verify['tree_sha256']==expected,'reconstruction_budget_covers_stream':True,'budgeted_restart_bundle_below_v029':candidate<ACCEPTED_V029_ANALYTICS,'all_region_boundaries_physical_le_8x':max_phys<=8.0,'all_region_boundaries_reconstruction_le_8x':max_recon<=8.0,'supported_for_product_prototype':supported},'contract':{'diagnostic_only':True,'release_credit':False,'production_format_changed':False,'production_selector_changed':False,'no_span_sweep':True,'candidate_lattice_equals_request_size':True,'placement_uses_locality_budget_not_size_outcome':True,'all_selected_histories_fully_charged':True,'every_service_region_endpoint_verified':True,'infeasible_selection_is_scientific_negative':True,'research_index_auth_allowance_not_final_product_proof':True},'next_if_supported':'implement authenticated shared-history/file-backed restart index and validate held-out Deflate streams before product integration','next_if_falsified':'preserve negative and retire independent-history restart placement unless a separately motivated shared-history mechanism demonstrates causal savings without weakening locality'}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-budgeted-restart-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-budgeted-restart.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+'\n'); print(json.dumps({k:d[k] for k in ('npz_owner_bytes','candidate_restart_points','selected_restart_points','coverage_end','selection_feasible','selection_failure_reason','restart_state_bytes','candidate_bytes','accepted_v029_bytes','margin_vs_v029_bytes','max_physical_amplification','max_reconstruction_amplification','hypothesis')}|{'restart_state':d['restart_state']},indent=2))

if __name__=='__main__': main()
