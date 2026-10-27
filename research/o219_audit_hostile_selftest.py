#!/usr/bin/env python3
"""Hostile negative controls for O219 independent scientific-receipt auditor."""
import argparse
import copy
import json
import tempfile
from pathlib import Path

from o219_independent_receipt_audit import audit

def mutate(d, label):
    if label == "drop_sample": d["samples"].pop()
    elif label == "duplicate_repeat":
        # Randomized order puts different methods in adjacent rows; mutate
        # inside one SAME (profile, method) bucket to guarantee a real duplicate.
        first=d["samples"][0]
        later=next(row for row in d["samples"] if
                   (row["n"],row["unique"],row["method"]) ==
                   (first["n"],first["unique"],first["method"]) and
                   row["repeat"] != first["repeat"])
        first["repeat"]=later["repeat"]
    elif label == "forge_clock": d["samples"][0]["total_wall_ns"] += 42
    elif label == "forge_cpu": d["samples"][0]["total_cpu_ns"] += 42
    elif label == "forge_median": d["summary"][0]["methods"]["native"]["total_wall_ns"] *= 0.1
    elif label == "flip_decision": d["decision"] = "WHOLE_INDEX_ORACLE_AT_LEAST_2X"
    elif label == "unknown_arm": d["samples"][0]["method"] = "magic"
    elif label == "bad_wire_digest": d["cases"][0]["wire_sha256"] = "not-a-digest"
    elif label == "fake_product": d["product_credit"] = True
    elif label == "false_prereg": d["prereg_commit"] = "0"*40
    elif label == "valid_shape_wrong_wire": d["cases"][0]["wire_sha256"] = "0"*64
    elif label == "wrong_logical_size": d["cases"][0]["declared"] += 1
    else: raise ValueError(label)

def run(source):
    baseline=audit(source)
    original=json.loads(Path(source).read_text())
    labels=["drop_sample","duplicate_repeat","forge_clock","forge_cpu",
            "forge_median","flip_decision","unknown_arm","bad_wire_digest",
            "fake_product","false_prereg","valid_shape_wrong_wire","wrong_logical_size"]
    with tempfile.TemporaryDirectory(prefix="o219-audit-negative-") as td:
        for label in labels:
            candidate=copy.deepcopy(original)
            mutate(candidate,label)
            path=Path(td)/(label+".json")
            path.write_text(json.dumps(candidate,sort_keys=True))
            try:
                audit(path)
            except (AssertionError,ValueError,KeyError,IndexError,ZeroDivisionError):
                continue
            raise AssertionError("malicious receipt accepted: "+label)
    print(json.dumps({"negative_controls_rejected":len(labels),
                      "baseline_checks":baseline["checks"],"decision":baseline["decision"]},
                     sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source")
    args=p.parse_args()
    run(args.source)
