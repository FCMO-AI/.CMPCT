#!/usr/bin/env python3
"""J24C09 independent judge; invalid receipts are not science-negative product data."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import statistics

PROFILES = ((4096, 1), (65536, 1), (65536, 256), (262144, 1))
SOURCE = {
    "reader": "9bca5d1047f9c78984b945d7ca90e3149fe429ab",
    "admission": "432e86f73f3f1751c04ccbb0e45858c18531da1d",
}
PHASES = ("open", "list", "ranges", "full_verify", "close")


def evaluate(raw: dict) -> dict:
    assert raw["schema"] == "cmpct-j24c09-installed-selective-session-v1"
    assert raw["preregistered"] == {
        "large_one_owner_wall_ratio_min": 1.5,
        "rss_growth_max_bytes": 8388608,
        "cycles": 3, "repeats": 3,
    }
    assert len(raw["raw_workers"]) == 48
    source = raw["source"]
    for name, value in SOURCE.items():
        assert source[name + "_git_blob"] == value
    assert len(source["reader_sha256"]) == len(source["admission_sha256"]) == 64
    manifest = {(f["count"], f["owners"]): f for f in raw["fixtures"]}
    assert set(manifest) == set(PROFILES)
    for f in manifest.values():
        assert f["archive_bytes"] > 0 and f["logical_bytes"] == 4*f["count"]
        assert len(bytes.fromhex(f["archive_sha256"])) == 32
        assert len(bytes.fromhex(f["logical_sha256"])) == 32
        assert len(f["ranges"]) == 6
        assert all(0 <= pos <= f["logical_bytes"]-16 and len(bytes.fromhex(hx))==16
                   for pos,hx in f["ranges"])
    ids = set()
    arms = Counter()
    for row in raw["raw_workers"]:
        profile = (row["count"], row["owners"])
        assert profile in manifest and row["mode"] in ("strict", "native")
        f = manifest[profile]
        assert row["archive_sha256"] == f["archive_sha256"]
        assert row["source"] == source
        assert row["native_engagement_probe_calls"] == (1 if row["mode"]=="native" else 0)
        assert row["native_timed"] is (row["mode"] == "native")
        assert row["cycle"] in (0, 1, 2) and row["slot"] in (0, 1, 2, 3)
        expected_mode = ("strict","native","native","strict") if row["cycle"]%2==0 else (
            "native","strict","strict","native")
        assert row["mode"] == expected_mode[row["slot"]]
        key = (*profile, row["cycle"], row["slot"])
        assert key not in ids
        ids.add(key)
        arms[(*profile, row["mode"])] += 1
        assert row["process_wall_ns"] > 0 and len(row["samples"]) == 3
        expected_digest = hashlib.sha256(
            b"".join(bytes.fromhex(hx) for _,hx in f["ranges"])
        ).hexdigest()
        for sample in row["samples"]:
            assert sample["range_digest"] == expected_digest
            for phase in PHASES:
                assert sample[phase+"_wall_ns"] >= 0
                assert sample[phase+"_cpu_ns"] >= 0
            assert sample["session_wall_ns"] == sum(
                sample[phase+"_wall_ns"] for phase in PHASES)
            assert sample["session_cpu_ns"] == sum(
                sample[phase+"_cpu_ns"] for phase in PHASES)
            assert sample["session_wall_ns"] > 0
    assert len(ids) == 48
    assert arms == Counter({
        (n,o,mode): 6 for n,o in PROFILES for mode in ("strict","native")
    })
    summary=[]
    positive=True
    rss_unknown=False
    for n,o in PROFILES:
        by={}
        for mode in ("strict","native"):
            matches=[row for row in raw["raw_workers"] if
                     (row["count"],row["owners"],row["mode"])==(n,o,mode)]
            medians={}
            for measure in ("session_wall_ns","session_cpu_ns","open_wall_ns",
                            "ranges_wall_ns","full_verify_wall_ns"):
                medians[measure.replace("_ns","_ms")] = statistics.median(
                    statistics.median(s[measure] for s in row["samples"])
                    for row in matches
                ) / 1e6
            values=[row["rss_highwater_bytes"] for row in matches]
            medians["rss_highwater_bytes"]=max(values) if all(
                x is not None for x in values) else None
            by[mode]=medians
        ratio=by["strict"]["session_wall_ms"]/by["native"]["session_wall_ms"]
        rss_a=by["strict"]["rss_highwater_bytes"]
        rss_b=by["native"]["rss_highwater_bytes"]
        rss_growth=None if rss_a is None or rss_b is None else rss_b-rss_a
        if o==1 and n in (65536,262144):
            if ratio<1.5 or (rss_growth is not None and rss_growth>8388608):
                positive=False
            if rss_growth is None:
                rss_unknown=True
        summary.append({
            "count":n, "owners":o, "strict":by["strict"], "native":by["native"],
            "complete_session_wall_ratio":ratio, "rss_growth_bytes":rss_growth,
        })
    decision=("SELECTIVE_SESSION_PRODUCT_HEADROOM_CONFIRMED" if positive else
              "SELECTIVE_SESSION_GAIN_BELOW_PREREGISTERED_FLOOR")
    if positive and rss_unknown:
        decision="SELECTIVE_SESSION_WALL_GAIN_RSS_UNMEASURED"
    return {
        "decision":decision,
        "evidence_head":raw["evidence_head"],
        "source":source,
        "platform":raw["platform"],
        "python":raw["python"],
        "workers":len(ids),
        "summary":summary,
        "limits":"signed Builder-free fixed RAW S_CHUNKS only; no full-release claim",
        "source_and_answer_custody":"PASS",
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raw=json.loads(args.input.read_text())
    verdict=evaluate(raw)
    for mutation in ("missing-worker", "false-native-engagement", "wrong-answer",
                     "wrong-source"):
        forged=copy.deepcopy(raw)
        if mutation=="missing-worker":
            forged["raw_workers"].pop()
        elif mutation=="false-native-engagement":
            row=next(x for x in forged["raw_workers"] if x["mode"]=="native")
            row["native_engagement_probe_calls"]=0
        elif mutation=="wrong-answer":
            forged["raw_workers"][0]["samples"][0]["range_digest"]="00"*32
        else:
            forged["raw_workers"][0]["source"]["reader_git_blob"]="11"*20
        try:
            evaluate(forged)
        except (AssertionError,ValueError,KeyError):
            pass
        else:
            raise AssertionError("referee accepted falsified "+mutation)
    args.output.write_text(json.dumps(verdict,sort_keys=True,indent=2)+"\n")
    print("J24C09_AUDITOR_PASS workers="+str(verdict["workers"]))
    print("J24C09_DECISION="+verdict["decision"])
    for x in verdict["summary"]:
        print("J24C09_PROFILE "+str((x["count"],x["owners"]))+" ratio="+
              str(round(x["complete_session_wall_ratio"],4))+
              " rss_growth="+str(x["rss_growth_bytes"]))


if __name__=="__main__":
    main()
