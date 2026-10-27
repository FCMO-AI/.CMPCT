#!/usr/bin/env python3
"""Independent receipt-level referee for J24B03 source-exact paired court.

Checks result shape/identity and requires a real vulnerable baseline; deliberately
does not import CMPCT, call the Builder, or implement any Reader function.
"""
import hashlib
import json
import sys
from pathlib import Path

def check(baseline_path, fixed_path):
    old=json.loads(Path(baseline_path).read_text())
    new=json.loads(Path(fixed_path).read_text())
    assert old["mode"]=="vulnerable" and new["mode"]=="repaired"
    assert old["case_count"]==new["case_count"]==24
    assert old["empty_owners_verified"]==new["empty_owners_verified"]==2
    assert old["frozen_vectors"]==new["frozen_vectors"]
    assert len(old["frozen_vectors"])==3
    assert all(v["result"]=="PASS" for v in old["frozen_vectors"])
    assert len(old["raw_header_controls"])==len(new["raw_header_controls"])==2
    for x,y in zip(old["raw_header_controls"],new["raw_header_controls"]):
        assert x["kind"]==y["kind"] and x["archive_sha256"]==y["archive_sha256"]
        assert x["preflight"]==y["preflight"]=="REJECT"
        assert x["selected"]=="ACCEPT" and y["selected"]=="REJECT"
    positives=negatives=historical_spills=0
    for a,b in zip(old["cases"],new["cases"]):
        invariant=("codec","kind","declared","physical","archive_sha256","frame_sha256","tail_prefix")
        assert tuple(a[x] for x in invariant)==tuple(b[x] for x in invariant)
        assert a["physical"]==128
        assert len(a["archive_sha256"])==len(a["frame_sha256"])==64
        if a["declared"]==128:
            positives+=1
            for op in ("preflight","read","verify","zero","early","eof"):
                assert a[op]["status"]==b[op]["status"]=="ACCEPT",(op,a,b)
            assert a["spill"]["status"]==b["spill"]["status"]=="REJECT"
            assert a["read"]["sha256"]==b["read"]["sha256"]
        else:
            negatives+=1
            assert a["preflight"]["status"]=="ACCEPT" and b["preflight"]["status"]=="REJECT"
            for op in ("read","verify","zero","early","eof","spill"):
                assert b[op]["status"]=="REJECT",(op,b)
            if a["codec"]==0 and a["declared"]==136:
                historical_spills+=1
                assert a["spill"]["hex"]==a["tail_prefix"]
    assert positives==6 and negatives==18 and historical_spills==2
    report={"decision":"J24B03_SIGNED_DIRECT_BLOB_SIZE_GUARD_CONFIRMED_IN_COURT",
            "cases":24,"positive":positives,"negative":negatives,
            "original_tail_spills":historical_spills,"frozen_vectors":3,
            "raw_header_controls":2,"referee":"PASS"}
    print(json.dumps(report,sort_keys=True))
    return report

if __name__=="__main__":
    check(sys.argv[1],sys.argv[2])
