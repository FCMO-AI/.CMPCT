#!/usr/bin/env python3
"""Inspect local Discovery Engine state for concurrent-work collisions.

Dependency-free by design. This tool does not lock GitHub; it turns durable state into
an explicit collision check that scheduled activations can run before implementation.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

STATE = Path("docs/discovery/STATE.json")
LEDGER = Path("research/discovery_episodes.jsonl")

def norm(s: str) -> str:
    return " ".join(s.lower().replace("_"," ").replace("-"," ").split())

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_ledger(path: Path):
    rows=[]
    if not path.exists(): return rows
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if line.strip():
            try: rows.append(json.loads(line))
            except json.JSONDecodeError as e: raise SystemExit(f"{path}:{n}: {e}")
    return rows

def unresolved(rows):
    pred={r["id"]:r for r in rows if r.get("event")=="prediction" and r.get("id")}
    done={r["id"] for r in rows if r.get("event")=="outcome" and r.get("id")}
    return [p for eid,p in pred.items() if eid not in done]

def candidates(state, rows):
    out=[]
    p=state.get("primary_question") or {}
    if p: out.append({"source":"state:primary","id":p.get("id"),"family":p.get("family"),"text":p.get("hypothesis",""),"status":p.get("status")})
    for x in state.get("frontier_candidates",[]):
        out.append({"source":"state:frontier","id":x.get("id"),"family":x.get("family"),"text":x.get("question",""),"status":x.get("status")})
    for x in unresolved(rows):
        out.append({"source":"ledger:unresolved","id":x.get("id"),"family":x.get("family"),"text":x.get("problem","")+" "+x.get("hypothesis",""),"status":"UNRESOLVED"})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--state",type=Path,default=STATE)
    ap.add_argument("--ledger",type=Path,default=LEDGER)
    ap.add_argument("--family")
    ap.add_argument("--question",default="")
    ap.add_argument("--json",action="store_true")
    a=ap.parse_args()
    state=load_json(a.state); rows=load_ledger(a.ledger); cs=candidates(state,rows)
    if a.family:
        fam=norm(a.family); q=set(norm(a.question).split())
        hits=[]
        for x in cs:
            same_family=norm(str(x.get("family") or ""))==fam
            words=set(norm(str(x.get("text") or "")).split())
            overlap=(len(q & words)/max(1,len(q))) if q else 0.0
            if same_family or overlap>=0.5: hits.append({**x,"question_overlap":round(overlap,3)})
        result={"collision":bool(hits),"matches":hits}
    else:
        result={"active_surfaces":cs}
    if a.json: print(json.dumps(result,indent=2,ensure_ascii=False))
    else:
        if "collision" in result:
            print("COLLISION" if result["collision"] else "CLEAR")
            for x in result["matches"]: print(f"- {x['source']} {x.get('id')} [{x.get('family')}]: {x.get('text')}")
        else:
            for x in result["active_surfaces"]: print(f"- {x['source']} {x.get('id')} [{x.get('family')}]: {x.get('text')}")
if __name__=="__main__": main()
