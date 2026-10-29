#!/usr/bin/env python3
"""J24I39b: classify binary results without changing any invalid-case expectation."""
import argparse, json, re
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case-dir",type=Path,required=True)
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    base=json.loads((a.case_dir/"tail-manifest.json").read_text())
    assert base["schema"]=="j24i39b-encoded-tail-v1"
    lines=a.raw.read_text().splitlines()
    rows={}
    for line in lines:
        m=re.fullmatch(r"variant=(valid|trailer|truncated|concatenated) reference_exit=(\d+) claxon_exit=(\d+)",line)
        assert m, line
        name,reference,claxon=m.groups()
        assert name not in rows
        rows[name]={"reference_accepts":int(reference)==0, "claxon_logical_digest_accepts":int(claxon)==0,
                    "reference_exit":int(reference),"claxon_exit":int(claxon),
                    **base["variants"][name]}
    assert len(rows)==4
    assert rows["valid"]["reference_accepts"] and rows["valid"]["claxon_logical_digest_accepts"], "valid control failed"
    result={
        "schema":"j24i39b-hostile-tail-classification-v1",
        "source_archive_sha256":base["source_archive_sha256"],
        "raw_observations":rows,
        "decision":(
            "CLAXON_LOGICAL_DIGEST_IS_NOT_FULL_ENCODED_VALIDATION"
            if rows["trailer"]["claxon_logical_digest_accepts"] and not rows["trailer"]["reference_accepts"]
            else "TRAILER_GAP_NOT_DEMONSTRATED"
        ),
        "scientific_only":True,
        "no_product_credit":True,
        "limitations":"source-exact split FLAC, not a re-signed physical CMPCT hostile archive; only four mutations",
    }
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
