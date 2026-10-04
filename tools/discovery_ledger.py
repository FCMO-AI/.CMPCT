#!/usr/bin/env python3
"""Dependency-free validator/summarizer for CMPCT recursive-discovery episodes."""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT = Path("research/discovery_episodes.jsonl")
REQUIRED = {"id","event","timestamp","family"}
START_REQUIRED = {"start_commit","problem","hypothesis","control","alternative","prediction","kill_condition","decision_unlocked"}
OUTCOME_REQUIRED = {"disposition","decisive","classification","observation","next_action"}
VALID_EVENTS={"prediction","outcome","correction","lesson"}

def load(path: Path):
    rows=[]
    if not path.exists(): return rows
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: row=json.loads(line)
        except json.JSONDecodeError as e: raise SystemExit(f"{path}:{n}: invalid JSON: {e}")
        miss=REQUIRED-set(row)
        if miss: raise SystemExit(f"{path}:{n}: missing {sorted(miss)}")
        if row["event"] not in VALID_EVENTS: raise SystemExit(f"{path}:{n}: invalid event {row['event']!r}")
        if row["event"]=="prediction":
            miss=START_REQUIRED-set(row)
            if miss: raise SystemExit(f"{path}:{n}: prediction missing {sorted(miss)}")
        if row["event"]=="outcome":
            miss=OUTCOME_REQUIRED-set(row)
            if miss: raise SystemExit(f"{path}:{n}: outcome missing {sorted(miss)}")
        rows.append(row)
    return rows

def audit(rows):
    predictions={}; outcomes=defaultdict(list); lessons=[]
    for r in rows:
        if r["event"]=="prediction":
            if r["id"] in predictions: raise SystemExit(f"duplicate prediction id: {r['id']}")
            predictions[r["id"]]=r
        elif r["event"]=="outcome": outcomes[r["id"]].append(r)
        elif r["event"]=="lesson": lessons.append(r)
    orphan=sorted(set(outcomes)-set(predictions))
    unresolved=sorted(set(predictions)-set(outcomes))
    if orphan: raise SystemExit("outcomes without prediction: "+", ".join(orphan))
    return predictions,outcomes,lessons,unresolved

def summary(rows):
    p,o,l,u=audit(rows)
    dispositions=Counter(x["disposition"] for xs in o.values() for x in xs)
    families=Counter(x["family"] for x in p.values())
    decisive=sum(bool(x.get("decisive")) for xs in o.values() for x in xs)
    print(json.dumps({"episodes":len(p),"outcomes":sum(map(len,o.values())),"decisive_outcomes":decisive,
      "unresolved":u,"lessons":len(l),"families":families,"dispositions":dispositions},indent=2,default=dict))

def replay(rows):
    p,o,_,_=audit(rows)
    for eid,pred in p.items():
        if eid not in o: continue
        last=o[eid][-1]
        cf=last.get("counterfactual_discriminator")
        if cf:
            print(json.dumps({"id":eid,"family":pred["family"],"original_decision":pred["decision_unlocked"],
              "counterfactual_discriminator":cf,"reusable_lesson":last.get("discovery_lesson")},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["validate","summary","replay"])
    ap.add_argument("--ledger",type=Path,default=DEFAULT)
    a=ap.parse_args(); rows=load(a.ledger)
    if a.command=="validate": audit(rows); print(f"OK: {len(rows)} events")
    elif a.command=="summary": summary(rows)
    else: replay(rows)
if __name__=="__main__": main()
