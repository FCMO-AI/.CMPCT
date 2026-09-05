"""ONE-G0.2 causal attribution for the frozen edited-version loss.

Referee freeze before result-bearing execution
==============================================
The 64-row internally edited-version transfer found exactly one mature-positive row where
scalar epoch-min failed the strict replacement gate: 262,144-byte base #1 with 16 internal
byte substitutions. Mature adds 1,008 exact bytes beyond fixed; epoch-min adds none.

This diagnostic reproduces that row *without changing any parameter* and instruments the
existing mature rolling-minimizer and candidate sparse/epoch observers. It records successful
exact-reuse regions, nomination kind/position/signal/source, mutation coordinates and nearby
candidate epoch/sparse nominations. It is attribution only: it may not promote a repair.

A useful outcome localizes the mature-only relationship to concrete source/target intervals
and describes which candidate nomination boundary missed it. If the discrepancy cannot be
localized exactly, the result is `mechanism_ambiguous` and no repair should be attempted.
"""
from __future__ import annotations

from collections import OrderedDict, deque
import json
import os
import random

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, _edited,
)
from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, ANCHOR_MASK, WINDOW, MIN_RUN, GEAR_MAX_INDEX_ENTRIES,
    _extend_left, _extend_right,
)
from benchmarks.one.one_g02_minimizer_gear_ab import MINIMIZER_SPAN, LOCAL_ENTRIES

TARGET_SIZE = 262_144
TARGET_BASE_INDEX = 1
TARGET_MUTATIONS = 16


def _target():
    master = random.Random(MASTER_SEED)
    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            if size == TARGET_SIZE and base_index == TARGET_BASE_INDEX:
                edit_rng = random.Random(seed ^ (TARGET_MUTATIONS << 32) ^ 0xA11CE5EED)
                # Duplicate the frozen editor while retaining mutation positions.
                positions = sorted(edit_rng.sample(range(WINDOW, len(base) - WINDOW), TARGET_MUTATIONS))
                edited = bytearray(base)
                replacements = []
                for pos in positions:
                    old = edited[pos]
                    delta = edit_rng.randrange(1, 256)
                    new = (old + delta) & 0xFF
                    edited[pos] = new
                    replacements.append({"offset_in_second_version": pos, "old": old, "new": new})
                frozen = _edited(base, random.Random(seed ^ (TARGET_MUTATIONS << 32) ^ 0xA11CE5EED), TARGET_MUTATIONS)
                assert bytes(edited) == frozen
                return seed, base + bytes(edited), replacements
    raise AssertionError("frozen target row not found")


def _audition(data, start, source, covered, kind, signal, nomination_position, events):
    if source is None or start < covered:
        return covered, 0
    if data[source:source+WINDOW] != data[start:start+WINDOW]:
        events.append({"kind": kind, "nomination_position": nomination_position, "start": start,
                       "source": source, "signal": signal, "exact_window": False})
        return covered, 0
    left, _ = _extend_left(data, source, start, covered)
    right, _ = _extend_right(data, source, start)
    a = max(start-left, covered)
    b = start+right
    gained = max(0, b-a)
    events.append({"kind": kind, "nomination_position": nomination_position, "start": start,
                   "source": source, "signal": signal, "exact_window": True,
                   "left_extension": left, "right_extension": right,
                   "accepted_start": a, "accepted_end": b, "gained_bytes": gained})
    return (b if gained else covered), gained


def _mature_trace(data: bytes):
    global_index = {}
    local_index = OrderedDict()
    minima = deque()
    h = 0
    run_value = data[0]
    run_length = 0
    covered = 0
    last_emitted = -1
    events = []
    emitted = []
    reuse = 0
    for position, value in enumerate(data):
        if not run_length: run_value,run_length=value,1
        elif value == run_value: run_length += 1
        else: run_value,run_length=value,1
        h=((h<<1)+_GEAR[value])&_U64_MASK
        if position+1<WINDOW: continue
        start=position+1-WINDOW
        rd=run_length>=max(MIN_RUN,WINDOW)
        run_start=position-run_length+1
        if not rd and (position+1)%WINDOW==0:
            source=local_index.get(h)
            covered,gain=_audition(data,start,source,covered,"local",h,position,events); reuse+=gain
            if source is None:
                local_index[h]=start; local_index.move_to_end(h)
                if len(local_index)>LOCAL_ENTRIES: local_index.popitem(last=False)
        while minima and minima[-1][0]>=h: minima.pop()
        minima.append((h,position))
        first_valid=position-MINIMIZER_SPAN+1
        while minima and minima[0][1]<first_valid: minima.popleft()
        if first_valid<WINDOW-1: continue
        signal,anchor=minima[0]; anchor_start=anchor+1-WINDOW
        if rd and anchor_start>=run_start: continue
        if anchor==last_emitted: continue
        last_emitted=anchor
        emitted.append({"position":anchor,"start":anchor_start,"signal":signal,"scan_position":position})
        source=global_index.get(signal)
        covered,gain=_audition(data,anchor_start,source,covered,"global_minimizer",signal,anchor,events); reuse+=gain
        if source is None and len(global_index)<GEAR_MAX_INDEX_ENTRIES: global_index[signal]=anchor_start
    return reuse, events, emitted


def _candidate_trace(data: bytes):
    sparse_index={}; rescue_index={}; h=0; last_sparse=None; active=False
    min_signal=(1<<64)-1; min_pos=-1; epoch_count=0; covered=0; reuse=0
    events=[]; nominations=[]; run_value=data[0]; run_length=0
    def reset():
        nonlocal min_signal,min_pos,epoch_count
        min_signal=(1<<64)-1; min_pos=-1; epoch_count=0
    def audition(start,signal,index,kind,position):
        nonlocal covered,reuse
        source=index.get(signal)
        if source is None:
            if len(index)<GEAR_MAX_INDEX_ENTRIES:index[signal]=start
            events.append({"kind":kind,"nomination_position":position,"start":start,"source":None,
                           "signal":signal,"index_insert":True})
            return
        covered,gain=_audition(data,start,source,covered,kind,signal,position,events);reuse+=gain
    def pulse(reason,scan_position):
        if min_pos<0:return
        nominations.append({"kind":"epoch","position":min_pos,"start":min_pos+1-WINDOW,
                            "signal":min_signal,"pulse_reason":reason,"scan_position":scan_position})
        audition(min_pos+1-WINDOW,min_signal,rescue_index,"epoch",min_pos); reset()
    for position,value in enumerate(data):
        if not run_length:run_value=value;run_length=1
        elif value==run_value:run_length+=1
        else:run_value=value;run_length=1
        h=((h<<1)+_GEAR[value])&_U64_MASK
        if position+1<WINDOW:continue
        rd=run_length>=max(MIN_RUN,WINDOW); sparse=not(h&ANCHOR_MASK) and not rd
        if sparse:
            if active:pulse("sparse_boundary",position)
            nominations.append({"kind":"sparse","position":position,"start":position+1-WINDOW,"signal":h})
            audition(position+1-WINDOW,h,sparse_index,"sparse",position)
            last_sparse=position;active=False;reset();continue
        if rd:continue
        epoch_count+=1
        if h<=min_signal:min_signal=h;min_pos=position
        gap=position-last_sparse if last_sparse is not None else position+1-WINDOW
        if not active and gap>=MINIMIZER_SPAN:pulse("activation",position);active=True
        elif active and epoch_count>=MINIMIZER_SPAN:pulse("span",position)
    if active:pulse("eof",len(data)-1)
    return reuse, events, nominations


def run():
    seed,data,mutations=_target()
    mature_reuse,mature_events,mature_nom=_mature_trace(data)
    cand_reuse,cand_events,cand_nom=_candidate_trace(data)
    mature_success=[e for e in mature_events if e.get("gained_bytes",0)>0]
    cand_success=[e for e in cand_events if e.get("gained_bytes",0)>0]
    cand_intervals={(e["accepted_start"],e["accepted_end"]) for e in cand_success}
    mature_only=[e for e in mature_success if (e["accepted_start"],e["accepted_end"]) not in cand_intervals]
    if not mature_only:
        decision="mechanism_ambiguous"
        focus=None
        nearby=[]
    else:
        # The frozen row has exactly one 1,008-byte marginal loss. Focus on the mature
        # success intersecting that missing mass and expose nearest candidate nominations.
        focus=min(mature_only,key=lambda e: abs(e.get("gained_bytes",0)-1008))
        target=focus["nomination_position"]
        nearby=sorted(cand_nom,key=lambda n:abs(n["position"]-target))[:12]
        decision="missing_mature_nomination_localized"
    second_version_start=TARGET_SIZE
    mutation_absolute=[dict(m,absolute_offset=second_version_start+m["offset_in_second_version"]) for m in mutations]
    return {
        "schema":"cmpct-one-g02-epoch-min-edited-loss-attribution-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "target":{"seed":seed,"base_bytes":TARGET_SIZE,"base_index":TARGET_BASE_INDEX,
                  "mutation_count":TARGET_MUTATIONS,"input_bytes":len(data)},
        "mutations":mutation_absolute,
        "mature_reuse_bytes":mature_reuse,
        "candidate_reuse_bytes":cand_reuse,
        "mature_successful_regions":mature_success,
        "candidate_successful_regions":cand_success,
        "mature_only_successful_regions":mature_only,
        "focused_missing_region":focus,
        "nearest_candidate_nominations":nearby,
        "decision":decision,
        "claim_boundary":"causal attribution of one frozen structural-transfer loss only; no repair/promotion authority",
    }

if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
