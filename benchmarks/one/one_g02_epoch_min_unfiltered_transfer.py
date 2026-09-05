"""ONE-G0.2 unfiltered epoch-min structural-transfer falsifier.

Referee freeze before result-bearing execution
==============================================
Epoch-min has preserved 35/35 targeted starvation hard rows, passed a strict native cost/state
gate, and captured 100% (532,480/532,480 B) of mature minimizer marginal opportunity on the
pre-existing MIY corpus. Those corpora are still small and partly inherited from the mechanism's
discovery history.

This experiment freezes a new candidate-independent temporal/versioned corpus generated only
from seed, base size and insertion length. No case is selected by anchor density, candidate
success, or mature-minimizer success.

Corpus:
- deterministic master RNG seed 0xC0DEC0DE;
- 8 independent bases for each size 8 KiB, 64 KiB and 256 KiB;
- insertion lengths 1, 8, 31 and 257 bytes, generated independently;
- each row is `basis + insertion + basis`, exposing an exact shifted second version while
  varying scale and displacement.

Frozen advancement gate:
- at least one mature positive-marginal row must exist at >=2 base sizes and >=2 insertion sizes;
- on every row where full minimizer beats the fixed observer, conservative candidate total
  `max(fixed, epoch)` must preserve >=100% of full-minimizer opportunity individually;
- total mature marginal capture must be 100%; aggregate extra opportunity cannot mask a loss;
- any positive-row loss scopes epoch-min away from complete minimizer substitution and is
  preserved as a structural negative, not tuned around.
Opportunity remains byte-verified discovery headroom, not stored-byte savings.
"""
from __future__ import annotations

import json,os,random

from benchmarks.one.one_g02_gear_replacement_ab import FIXED_MAX_INDEX_ENTRIES,MIN_RUN,WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_starvation_epoch_min_transfer import _epoch_observe
from experiments.one.observe import observe

MASTER_SEED=0xC0DEC0DE
BASE_SIZES=(8*1024,64*1024,256*1024)
INSERTION_SIZES=(1,8,31,257)
BASES_PER_SIZE=8


def _corpus():
    rng=random.Random(MASTER_SEED)
    rows=[]
    for size in BASE_SIZES:
        for bi in range(BASES_PER_SIZE):
            basis=rng.randbytes(size)
            for ins_size in INSERTION_SIZES:
                ins=rng.randbytes(ins_size)
                rows.append((size,bi,ins_size,basis+ins+basis))
    return rows


def run():
    rows=[];losses=[];positive=0;positive_sizes=set();positive_insertions=set()
    total_input=total_marginal=captured=extra=0
    for base_size,bi,ins_size,data in _corpus():
        fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
        full=_minimizer_observe(data);epoch=_epoch_observe(data)
        f=fixed.stats.reuse_opportunity_bytes;m=full.reuse_opportunity_bytes;e=epoch.reuse_opportunity_bytes
        candidate=max(f,e);marginal=max(0,m-f);cap=min(marginal,max(0,candidate-f));total_input+=len(data)
        if marginal:
            positive+=1;positive_sizes.add(base_size);positive_insertions.add(ins_size);total_marginal+=marginal;captured+=cap
            if candidate<m:losses.append(f"base={base_size}/i={bi}/insert={ins_size}")
        extra+=max(0,candidate-max(f,m))
        rows.append({"base_bytes":base_size,"base_index":bi,"insertion_bytes":ins_size,"input_bytes":len(data),
            "fixed_reuse_opportunity_bytes":f,"full_minimizer_reuse_opportunity_bytes":m,"epoch_min_reuse_opportunity_bytes":e,
            "mature_marginal_opportunity_bytes":marginal,"candidate_total_opportunity_bytes":candidate,
            "captured_mature_marginal_bytes":cap,"candidate_minus_mature_total_bytes":candidate-max(f,m),"epoch_pulses":epoch.pulses})
    frac=captured/total_marginal if total_marginal else None
    breadth=positive and len(positive_sizes)>=2 and len(positive_insertions)>=2
    decision=("advance_epoch_min_structural_transfer" if breadth and not losses and frac==1.0
              else "inconclusive_insufficient_positive_breadth" if not breadth
              else "scope_epoch_min_after_structural_transfer_loss")
    return {"schema":"cmpct-one-g02-epoch-min-unfiltered-transfer-v1","experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "corpus":{"master_seed":MASTER_SEED,"base_sizes":BASE_SIZES,"insertions":INSERTION_SIZES,"bases_per_size":BASES_PER_SIZE,"rows":len(rows)},
        "positive_marginal_rows":positive,"positive_base_sizes":sorted(positive_sizes),"positive_insertion_sizes":sorted(positive_insertions),
        "positive_loss_cases":losses,"total_input_bytes":total_input,"mature_marginal_opportunity_bytes":total_marginal,
        "captured_mature_marginal_bytes":captured,"mature_marginal_capture_fraction":frac,
        "mature_marginal_opportunity_per_input_byte":total_marginal/total_input if total_input else 0.0,
        "candidate_extra_exact_opportunity_bytes":extra,"decision":decision,
        "claim_boundary":"unfiltered structural encoder-discovery transfer only; no stored-byte/product/comparator/release authority","rows":rows}

if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
