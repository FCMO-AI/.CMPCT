"""ONE-G0.2 epoch-min transfer onto the mature minimizer marginal-yield corpus.

Referee freeze before result-bearing execution
==============================================
The scalar epoch-min seed has two independent facts: 35/35 targeted generator-distinct hard
starvation rows retained the full minimizer opportunity, and native cost/state beat the current
promoted selector by large margins. The strongest surviving criticism is structural transfer.

This test reuses the existing *pre-candidate* minimizer marginal-information-yield corpus,
including its independent ordinary/random/compressed/repeated/exact/shifted cases and the two
explicit anchor-starvation falsifiers. The candidate does not influence corpus selection.

For each row, mature marginal opportunity is `max(0, full_minimizer - fixed_observer)`.
Candidate total opportunity is conservatively `max(fixed_observer, epoch_min)`; overlap is not
summed. All opportunity is still byte-verified by the existing observers and remains headroom,
not stored-byte savings.

Frozen advancement gate:
- the corpus must contain at least one mature positive-marginal row;
- epoch-min must preserve >=100% of mature full-minimizer opportunity on *every* mature
  positive-marginal row (no aggregate averaging away a structural loss);
- candidate capture of total mature marginal opportunity must therefore be 100%;
- any mature-positive row loss rejects epoch-min as a complete minimizer substitute and forces
  a scoped hybrid/causal follow-up rather than threshold tuning.
Extra exact candidate opportunity is reported but cannot compensate for a lost required row.
"""
from __future__ import annotations

import json,os,random

from benchmarks.one.one_g02_gear_replacement_ab import _cases,FIXED_MAX_INDEX_ENTRIES,MIN_RUN,WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_starvation_epoch_min_transfer import _epoch_observe
from experiments.one.observe import observe


def run():
    cases=_cases()
    starved=random.Random(4876).randbytes(8*1024)
    cases["starved_repeat_basis_8k_16k"]=starved*2
    cases["starved_shifted_basis_8k_insert1"]=starved+b"X"+starved
    rows=[];positive=[];losses=[];mature_marginal_total=0;captured_total=0;candidate_extra_total=0
    for name,data in cases.items():
        fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
        full=_minimizer_observe(data);epoch=_epoch_observe(data)
        f=fixed.stats.reuse_opportunity_bytes;m=full.reuse_opportunity_bytes;e=epoch.reuse_opportunity_bytes
        mature_marginal=max(0,m-f);candidate_total=max(f,e);candidate_marginal=max(0,candidate_total-f)
        captured=min(mature_marginal,candidate_marginal)
        if mature_marginal:
            positive.append(name);mature_marginal_total+=mature_marginal;captured_total+=captured
            if candidate_total<m:losses.append(name)
        candidate_extra_total+=max(0,candidate_total-max(f,m))
        rows.append({"case":name,"input_bytes":len(data),"fixed_reuse_opportunity_bytes":f,
            "full_minimizer_reuse_opportunity_bytes":m,"epoch_min_reuse_opportunity_bytes":e,
            "mature_marginal_opportunity_bytes":mature_marginal,"candidate_total_opportunity_bytes":candidate_total,
            "candidate_marginal_opportunity_bytes":candidate_marginal,"captured_mature_marginal_bytes":captured,
            "candidate_minus_mature_total_opportunity_bytes":candidate_total-max(f,m),"epoch_pulses":epoch.pulses,
            "epoch_verification_read_bytes":epoch.verification_read_bytes,"epoch_extension_read_bytes":epoch.extension_read_bytes})
    capture=(captured_total/mature_marginal_total if mature_marginal_total else None)
    decision=("advance_epoch_min_to_unfiltered_structural_transfer" if positive and not losses and capture==1.0
              else "inconclusive_no_mature_marginal_rows" if not positive
              else "reject_epoch_min_as_complete_minimizer_substitute_on_miy_corpus")
    return {"schema":"cmpct-one-g02-epoch-min-miy-transfer-v1","experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "corpus_contract":"existing one_g02_minimizer_miy case family + frozen Random(4876) starvation pair",
        "mature_positive_marginal_cases":positive,"mature_positive_marginal_loss_cases":losses,
        "mature_marginal_opportunity_bytes":mature_marginal_total,"captured_mature_marginal_bytes":captured_total,
        "mature_marginal_capture_fraction":capture,"candidate_extra_exact_opportunity_bytes":candidate_extra_total,
        "decision":decision,"interpretation":"opportunity bytes are exact discovery headroom, not stored-byte savings",
        "claim_boundary":"structural encoder-discovery transfer only; no reader/product/comparator/release authority","rows":rows}

if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
