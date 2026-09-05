"""ONE-G0.2 automatic bounded translation-Law cone + Surprise admission.

Referee freeze before result-bearing execution
==============================================
O0 showed large headroom when an already byte-proven translation Law is allowed to persist
across explicit Surprise, but gifted the continuation decision and target-version extent.
This experiment removes that extent gift for a narrow but important temporal/versioned
shape: a previously proven positive translation delta defines a non-self-referential cone.

Automatic cone from one exact candidate seed
--------------------------------------------
For a successful exact relation with source start s and target start t, let delta=t-s>0.
The candidate Law is `target[x] = source[x-delta]`. Without knowing a version boundary, the
largest forward cone that cannot read from its own target is derived only from delta and the
input bounds: target interval [delta, min(2*delta, len(data))). Thus the source is
[0, cone_len). No target extent is gifted.

Within the cone every mismatch is explicit Surprise. Representation charge is the same as
O0: 32 B Law/control + ULEB Surprise count + ULEB position delta + one literal byte per
Surprise. Admission is pure MDL: admit only if charged Law+Surprise bytes < literal cone
bytes. Reconstruction must be exact.

Frozen positive corpus: the same 64 edited-version rows as O0.
Frozen hostile controls:
- 8 independent 64 KiB random-half pairs where a 16 KiB same-offset island is copied from
  first half into otherwise independent second-half bytes. The existing candidate must find
  a real exact seed, but a full translation Law should be rejected by MDL because most of
  the cone is Surprise.
- 8 fully independent random-half pairs, which must not produce an admitted Law.

Frozen advancement gates:
Positive edited rows:
- exact candidate seed exists and inferred delta equals the base size;
- automatic cone equals the complete second half solely as a consequence of delta/input bounds;
- MDL admits Law+Surprise;
- exact reconstruction;
- predicted exact bytes >= mature minimizer exact opportunity.
Hostile partial-copy rows:
- at least one exact candidate seed must exist, making the test meaningful;
- no translation Law may be admitted for the full automatic cone.
Independent rows:
- no admitted Law.
Any row failure rejects this automatic-cone rule. No threshold may be retuned post-result.

This is encoder discovery/representation evidence. Native execution, generic cone families,
wire encoding and product authority remain separate debt.
"""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_epoch_min_edited_loss_attribution import _candidate_trace
from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, MUTATION_COUNTS, _edited,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_translation_law_surprise_o0 import LAW_CONTROL_BYTES, _uleb_bytes

CONTROL_SEED = 0xA17C0E
CONTROL_HALF = 65_536
CONTROL_ISLAND = 16_384
CONTROL_ROWS = 8


def _seed(data: bytes, second_start: int | None = None):
    _, events, _ = _candidate_trace(data)
    successful = [e for e in events if e.get("gained_bytes", 0) > 0 and e.get("source") is not None]
    if second_start is not None:
        crossing = [e for e in successful if int(e["source"]) < second_start <= int(e["start"])]
        if crossing:
            e = crossing[0]
            return int(e["start"] - e["source"]), e
    if successful:
        e = successful[0]
        return int(e["start"] - e["source"]), e
    return None, None


def _cone(data: bytes, delta: int):
    if delta <= 0 or delta >= len(data):
        return None
    end = min(2 * delta, len(data))
    if end <= delta:
        return None
    source = data[: end - delta]
    target = data[delta:end]
    surprises = [i for i, (a, b) in enumerate(zip(source, target)) if a != b]
    charged = LAW_CONTROL_BYTES + _uleb_bytes(len(surprises))
    prev = 0
    for pos in surprises:
        charged += _uleb_bytes(pos - prev) + 1
        prev = pos
    rebuilt = bytearray(source)
    for pos in surprises:
        rebuilt[pos] = target[pos]
    return {
        "target_start": delta,
        "target_end": end,
        "literal_bytes": len(target),
        "surprises": len(surprises),
        "predicted_exact_bytes": len(target) - len(surprises),
        "charged_bytes": charged,
        "admit": charged < len(target),
        "exact": bytes(rebuilt) == target,
    }


def _positive_rows():
    master = random.Random(MASTER_SEED)
    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            for mutations in MUTATION_COUNTS:
                edited = _edited(base, random.Random(seed ^ (mutations << 32) ^ 0xA11CE5EED), mutations)
                yield size, base_index, mutations, base + edited


def _partial_controls():
    r = random.Random(CONTROL_SEED)
    for i in range(CONTROL_ROWS):
        left_seed = r.getrandbits(64); right_seed = r.getrandbits(64)
        left = random.Random(left_seed).randbytes(CONTROL_HALF)
        right = bytearray(random.Random(right_seed).randbytes(CONTROL_HALF))
        # Interior island; offset varies deterministically but remains far from boundaries.
        offset = 4096 + (i * 4093) % (CONTROL_HALF - CONTROL_ISLAND - 8192)
        right[offset:offset+CONTROL_ISLAND] = left[offset:offset+CONTROL_ISLAND]
        yield i, offset, left + bytes(right)


def _independent_controls():
    r = random.Random(CONTROL_SEED ^ 0x55AA55AA)
    for i in range(CONTROL_ROWS):
        left = random.Random(r.getrandbits(64)).randbytes(CONTROL_HALF)
        right = random.Random(r.getrandbits(64)).randbytes(CONTROL_HALF)
        yield i, left + right


def run():
    positives=[]; partial=[]; independent=[]; failures=[]
    total_literal=total_charged=total_predicted=total_mature=0

    for size, base_index, mutations, data in _positive_rows():
        delta,event=_seed(data,size)
        cone=_cone(data,delta) if delta is not None else None
        mature=_minimizer_observe(data)
        reasons=[]
        if delta!=size: reasons.append("seed_delta")
        if cone is None: reasons.append("no_cone")
        else:
            if cone["target_start"]!=size or cone["target_end"]!=len(data): reasons.append("cone_bounds")
            if not cone["admit"]: reasons.append("mdl_reject_positive")
            if not cone["exact"]: reasons.append("reconstruction")
            if cone["predicted_exact_bytes"] < mature.reuse_opportunity_bytes: reasons.append("mature_not_subsumed")
            total_literal += cone["literal_bytes"]; total_charged += cone["charged_bytes"]
            total_predicted += cone["predicted_exact_bytes"]; total_mature += mature.reuse_opportunity_bytes
        if reasons: failures.append({"kind":"positive","base_bytes":size,"base_index":base_index,"mutations":mutations,"reasons":reasons})
        positives.append({"base_bytes":size,"base_index":base_index,"mutation_count":mutations,
                          "seed_delta":delta,"seed_kind":event.get("kind") if event else None,
                          "mature_opportunity_bytes":mature.reuse_opportunity_bytes,"cone":cone,"failures":reasons})

    for i,offset,data in _partial_controls():
        delta,event=_seed(data,CONTROL_HALF)
        cone=_cone(data,delta) if delta is not None else None
        reasons=[]
        if delta is None: reasons.append("no_exact_seed_partial_control")
        if cone is not None and cone["admit"]: reasons.append("false_law_admitted")
        if cone is not None and not cone["exact"]: reasons.append("reconstruction")
        if reasons: failures.append({"kind":"partial_control","index":i,"reasons":reasons})
        partial.append({"index":i,"copied_island_offset":offset,"copied_island_bytes":CONTROL_ISLAND,
                        "seed_delta":delta,"seed_kind":event.get("kind") if event else None,"cone":cone,"failures":reasons})

    for i,data in _independent_controls():
        delta,event=_seed(data,CONTROL_HALF)
        cone=_cone(data,delta) if delta is not None else None
        reasons=[]
        if cone is not None and cone["admit"]: reasons.append("independent_law_admitted")
        if cone is not None and not cone["exact"]: reasons.append("reconstruction")
        if reasons: failures.append({"kind":"independent_control","index":i,"reasons":reasons})
        independent.append({"index":i,"seed_delta":delta,"seed_kind":event.get("kind") if event else None,
                            "cone":cone,"failures":reasons})

    return {
        "schema":"cmpct-one-g02-translation-law-surprise-autocone-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "oracle_tier":"automatic bounded cone; no target extent gift",
        "law_control_bytes":LAW_CONTROL_BYTES,
        "positive_rows":len(positives),
        "partial_copy_controls":len(partial),
        "independent_controls":len(independent),
        "gate_failures":failures,
        "total_positive_literal_bytes":total_literal,
        "total_positive_charged_bytes":total_charged,
        "positive_charged_fraction_of_literal": total_charged/total_literal if total_literal else None,
        "total_positive_predicted_exact_bytes":total_predicted,
        "total_mature_opportunity_bytes":total_mature,
        "decision":"advance_automatic_translation_law_surprise" if not failures else "reject_automatic_translation_cone_rule",
        "claim_boundary":"automatic bounded-cone/MDL encoder evidence only; no native-speed, generic-version-boundary, wire, comparator or release authority",
        "positives":positives,
        "partial_controls":partial,
        "independent":independent,
    }

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
