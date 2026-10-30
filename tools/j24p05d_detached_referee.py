#!/usr/bin/env python3
"""Detached J24P05d PEP427 spread referee; never import or execute native CMPCT."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import zipfile
from j24p05_detached_artifact_referee import check_wheel, hard_check, digest

NATIVE="cmpct/cmpct_core.cpython-311-darwin.so"
DATA_NATIVE="cmpct-0.30.0.data/purelib/"+NATIVE
DATA_OTHER="cmpct-0.30.0.data/purelib/cmpct/UNRELATED.txt"
INERT=b"J24P05D_HOST_INERT_SPREAD_NO_CODE\n"
CASES={"original","disjoint","spread_before","spread_after"}

def verify(path:Path)->dict:
    raw=path.read_bytes()
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        hard_check(len(names)==len(set(names)), "duplicate provider ZIP member")
        court=json.loads(z.read("court.json"))
        hard_check(court["schema"]=="cmpct-j24p05d-data-spread-court-v1","wrong court")
        hard_check(set(court["cases"])==CASES,"wrong case set")
        source=court["source"]
        original_path=next(n for n in names if n.startswith("original/") and n.endswith(".whl"))
        original_members,_=check_wheel(z.read(original_path),"original")
        baseline=original_members[NATIVE]
        hard_check(digest(baseline)==source["native_original_sha256"],"native original source SHA")
        hard_check(digest(INERT)==source["inert_sha256"],"inert source SHA")
        cases={}
        for label in sorted(CASES):
            matches=[n for n in names if n.startswith(label+"/") and n.endswith(".whl")]
            hard_check(len(matches)==1,label+": source wheel absent")
            wheel=z.read(matches[0])
            members,paths=check_wheel(wheel,label)
            hard_check(members[NATIVE]==baseline,label+": native changed before install")
            hard_check(len(paths)==len(set(paths)),label+": distinct ZIP names not preserved")
            hard_check(all(n and not n.startswith("/") and all(p not in ("",".","..") for p in n.split("/")) for n in paths),label+": noncanonical ZIP input")
            if label.startswith("spread"):
                hard_check(members.get(DATA_NATIVE)==INERT,label+": PEP427 data source absent")
            else:
                hard_check(DATA_NATIVE not in members,label+": data unexpectedly present")
            if label=="disjoint":
                hard_check(DATA_OTHER in members,label+": missing disjoint control")
            row=court["cases"][label]
            hard_check(row["validator_pass"] is True,label+": inherited gate rejected input")
            hard_check(row["wheel_sha256"]==digest(wheel) and row["wheel_bytes"]==len(wheel),label+": wheel receipt mismatch")
            p="installed-native/"+label+".bin"
            hard_check(p in names,label+": missing physical post-pip bytes")
            actual=z.read(p)
            expected_inert=label.startswith("spread")
            hard_check(actual==(INERT if expected_inert else baseline),label+": installed bytes contradict spread hypothesis")
            reported=row["pip"]
            hard_check(reported["returncode"]==0 and reported["native_sha256"]==digest(actual)
                       and reported["native_length"]==len(actual)
                       and reported["spread_inert_won"] is expected_inert
                       and reported["original_retained"] is (not expected_inert),
                       label+": reporter does not match physical installed data")
            cases[label]={"wheel_sha256":digest(wheel),"record_sha256_verified":True,
                          "installed_sha256":digest(actual),"installed_bytes":len(actual),
                          "native_overwritten":expected_inert}
    return {"schema":"cmpct-j24p05d-detached-referee-v1",
            "provider_artifact_sha256":digest(raw),"host":court["host"],
            "cases":cases,"verified":True,"scope":"original wheel/RECORD and real installed file bytes, not executed native code"}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("raw_hosted_artifact",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    try:res=verify(args.raw_hosted_artifact)
    except (ValueError,KeyError,RuntimeError,OSError,zipfile.BadZipFile,StopIteration,TypeError) as exc:
        print(json.dumps({"pass":False,"error":str(exc)}));return 2
    s=json.dumps(res,sort_keys=True,indent=2)+"\n"
    if args.output:args.output.write_text(s)
    print(s)
    return 0

if __name__=="__main__":
    sys.exit(main())
