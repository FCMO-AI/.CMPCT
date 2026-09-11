"""ONE-G0.2 structural validation of shared observer + unchanged cold phase fallback."""
from __future__ import annotations

import json
import os

from benchmarks.one.one_g02_relation_shared_observer_validation import (
    _build_safe,
    _cross_object_reuse_nominations,
    _safe_result,
)
from benchmarks.one.one_g02_bounded_shift_phase_certificate_validation import (
    _cases,
    _nominate,
    MODELED_STATE_BYTES,
)

SIZES=(4*1024,8*1024,16*1024,64*1024,256*1024)
SEEDS=(13,43,67)
MAX_FALLBACK_SAMPLE_FRACTION=0.19


def run():
    safe,td=_build_safe(); rows=[]; combined_misses=[]; random_false=[]; fallback_recovery_misses=[]
    max_fallback_fraction=0.0; shared_positive_hits=0; fallback_positive_recoveries=0; fallback_activations=0
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name,(source,target) in _cases(size,seed).items():
                    enabled,best_shift,proofs=_safe_result(safe,source,target)
                    cross_exact,cross_auditions,peak_queue=_cross_object_reuse_nominations(source,target)
                    shared=bool(cross_exact)
                    phase=False; ss=ts=compares=0; phase_id=None
                    if not shared:
                        fallback_activations += 1
                        phase,ss,ts,compares,phase_id=_nominate(source,target)
                        frac=(ss+ts)/len(source)
                        max_fallback_fraction=max(max_fallback_fraction,frac)
                    else:
                        frac=0.0
                    combined=shared or phase
                    if enabled and shared: shared_positive_hits += 1
                    if enabled and not shared and phase: fallback_positive_recoveries += 1
                    if enabled and not combined:
                        combined_misses.append((size,seed,name))
                        fallback_recovery_misses.append((size,seed,name))
                    if name=="independent_random" and combined:
                        random_false.append((size,seed,name,"shared" if shared else "phase"))
                    rows.append({
                        "relation_bytes":size,"seed":seed,"case":name,
                        "exact_relation_enabled":enabled,"best_shift":best_shift,"exact_proofs":proofs,
                        "shared_nominated":shared,"shared_cross_exact":cross_exact,"shared_cross_auditions":cross_auditions,"shared_peak_queue":peak_queue,
                        "phase_fallback_executed":not shared,"phase_fallback_nominated":phase,"phase_matching_source_phase":phase_id,
                        "fallback_source_word_samples":ss,"fallback_target_word_samples_until_decision":ts,"fallback_sampled_position_fraction":frac,"fallback_exact_word_compares":compares,
                        "combined_nominated":combined,
                    })
        passed=(not combined_misses and not random_false and max_fallback_fraction<=MAX_FALLBACK_SAMPLE_FRACTION and MODELED_STATE_BYTES==240)
        return {
            "schema":"cmpct-one-g02-shared-plus-phase-cold-fallback-v1",
            "experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes":list(SIZES),"frozen_seeds":list(SEEDS),
            "phase_fallback_state_bytes_transient":MODELED_STATE_BYTES,
            "fallback_activations":fallback_activations,
            "shared_positive_hits":shared_positive_hits,
            "fallback_positive_recoveries":fallback_positive_recoveries,
            "combined_positive_misses":combined_misses,
            "fallback_recovery_misses":fallback_recovery_misses,
            "independent_random_combined_false_nominations":random_false,
            "max_fallback_sampled_position_fraction":max_fallback_fraction,
            "decision":"advance_cold_fallback_cascade_to_native_cost" if passed else "reject_shared_plus_phase_cold_fallback",
            "claim_boundary":"structural complementarity only; no native speed, density, reader, format, or comparator claim",
            "rows":rows,
        }
    finally:
        td.cleanup()


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_cold_fallback_cascade_to_native_cost" else 1)
