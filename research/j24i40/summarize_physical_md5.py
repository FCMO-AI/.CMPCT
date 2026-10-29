#!/usr/bin/env python3
"""J24I40b evaluate actual physical archive Python/native verdicts without outcome gardening."""
import argparse
import hashlib
import json
import re
from pathlib import Path

PAT = re.compile(r"^archive=(valid|md5_flip) engine=(python|native) exit=(\d+)$")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case-dir",type=Path,required=True)
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    m=json.loads((a.case_dir/"physical-md5-manifest.json").read_text())
    assert m["schema"]=="j24i40b-physical-cma4-md5-v1"
    specimens={"valid":"md5-physical-valid.cmpct","md5_flip":"md5-physical-flip.cmpct"}
    assert hashlib.sha256((a.case_dir/specimens["valid"]).read_bytes()).hexdigest()==m["original_archive_sha256"]
    assert hashlib.sha256((a.case_dir/specimens["md5_flip"]).read_bytes()).hexdigest()==m["mutant_archive_sha256"]
    outcomes={}
    for line in a.raw.read_text().splitlines():
        mt=PAT.fullmatch(line)
        assert mt,f"unexpected observed result: {line!r}"
        name, engine, code=mt.groups()
        assert (name,engine) not in outcomes
        outcomes[(name,engine)]=int(code)
    assert set(outcomes)=={(v,e) for v in specimens for e in ("python","native")}
    assert outcomes[("valid","python")]==outcomes[("valid","native")]==0,"original controls must pass"
    ppass=outcomes[("md5_flip","python")]==0
    npass=outcomes[("md5_flip","native")]==0
    decision=("BOTH_ACCEPT_LOGICAL_SHA_INTACT" if ppass and npass
        else "BOTH_REJECT_CODEC_MD5" if not ppass and not npass
        else "PYTHON_ACCEPTS_NATIVE_REJECTS" if ppass else "NATIVE_ACCEPTS_PYTHON_REJECTS")
    result={
        "schema":"j24i40b-physical-reader-court-v1",
        "classification":decision,
        "physical_mutation":m,
        "exit_codes":{v:{e:outcomes[(v,e)] for e in ("python","native")} for v in specimens},
        "reference_flac_t":"Previously independently demonstrated to reject isolated FLAC MD5 flip; see J24I40 original hosted result",
        "conclusion_scope":"Only strong verify; not extraction, read_range, release, authentication, or product speed.",
    }
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
