#!/usr/bin/env python3
"""Validate CMPCT's compact continuous-discovery state.

This checker deliberately validates shape and anti-Goodhart invariants only. It does not
score scientific ideas or become a second release gate.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA = "cmpct-discovery-state-v1"
ALLOWED = {"READY", "QUEUED", "RUNNING", "BLOCKED", "AMBIGUOUS", "RETIRED", "PRESERVED"}

def fail(msg: str) -> None:
    raise SystemExit(f"discovery-state: FAIL: {msg}")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="docs/discovery/STATE.json")
    ns = ap.parse_args()
    p = Path(ns.path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse {p}: {exc}")

    if data.get("schema") != SCHEMA:
        fail(f"schema must be {SCHEMA!r}")
    for key in ("authority", "active_product_bottleneck", "primary_question", "backup_question", "frontier_candidates",
                "saturated_families", "pending_jobs", "process_lessons", "next_action"):
        if key not in data:
            fail(f"missing {key}")

    primary = data["primary_question"]
    for key in ("id", "family", "hypothesis", "kill", "status"):
        if not primary.get(key):
            fail(f"primary_question missing {key}")
    if primary["status"] not in ALLOWED:
        fail(f"unknown primary status {primary['status']!r}")

    backup = data["backup_question"]
    for key in ("id", "family", "question", "kill", "status"):
        if not backup.get(key):
            fail(f"backup_question missing {key}")
    if backup["status"] not in ALLOWED:
        fail(f"unknown backup status {backup['status']!r}")
    if backup["id"] == primary["id"]:
        fail("backup_question must differ from primary_question")
    if backup["family"] == primary["family"]:
        fail("backup_question must use a dependency/solution family distinct from primary_question")

    frontier = data["frontier_candidates"]
    if not isinstance(frontier, list) or len(frontier) > 3:
        fail("frontier_candidates must contain at most three items")
    ids, families = set(), set()
    for item in frontier:
        for key in ("id", "family", "question", "status"):
            if not item.get(key):
                fail(f"frontier candidate missing {key}")
        if item["id"] in ids:
            fail(f"duplicate candidate id {item['id']!r}")
        ids.add(item["id"])
        families.add(item["family"])
        if item["status"] not in ALLOWED:
            fail(f"unknown candidate status {item['status']!r}")

    # Diversity is an explicit default. Two candidates may share a family only after the
    # state records a justification rather than silently collapsing search into one lane.
    if len(frontier) > 1 and len(families) < len(frontier) and not data.get("family_concentration_justification"):
        fail("duplicate frontier families require family_concentration_justification")

    forbidden = {"score", "rsi_score", "reward", "fitness"}
    def walk(x, where="root"):
        if isinstance(x, dict):
            for k, v in x.items():
                if k.lower() in forbidden:
                    fail(f"forbidden scalar optimization field {where}.{k}")
                walk(v, f"{where}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{where}[{i}]")
    walk(data)

    print(f"discovery-state: PASS: {p} | frontier={len(frontier)} families={len(families)}")

if __name__ == "__main__":
    main()
