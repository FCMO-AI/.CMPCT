#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def load(repo: Path, engine: str):
    sys.path.insert(0, str(repo))
    if engine == "v029-research":
        from experiments import entropygraph_v029_release as mod
    elif engine == "v030-canonical":
        from experiments import entropygraph_v030_canonical as mod
    else:
        raise SystemExit(f"unsupported engine {engine}")
    return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--engine", required=True, choices=["v029-research","v030-canonical"])
    ap.add_argument("--action", required=True, choices=["create","verify","extract"])
    ap.add_argument("--source")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--dest")
    a=ap.parse_args()
    mod=load(Path(a.repo), a.engine)
    archive=Path(a.archive)
    if a.action=="create":
        if not a.source: raise SystemExit("--source required")
        result=mod.build(Path(a.source), archive)
        print(json.dumps(result, sort_keys=True, default=str))
    elif a.action=="verify":
        result=mod.strong_verify(archive)
        print(json.dumps(result, sort_keys=True, default=str))
    else:
        if not a.dest: raise SystemExit("--dest required")
        dest=Path(a.dest); dest.mkdir(parents=True, exist_ok=True)
        mod.extract(archive, dest)

if __name__=="__main__":
    main()
