#!/usr/bin/env python3
"""J24I68 independent research referee hostile controls. Reads only frozen hosted ZIPs."""
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("j24i68",ROOT/"research"/"j24i68_zip_proxy_referee.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def rewrite_member(raw, member, mutate):
    src=zipfile.ZipFile(io.BytesIO(raw))
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as dst:
        for item in src.infolist():
            b=src.read(item)
            if item.filename==member:
                obj=json.loads(b)
                mutate(obj)
                b=(json.dumps(obj,sort_keys=True)+"\n").encode()
            dst.writestr(item,b)
    return out.getvalue()

def refuse(raw,name):
    try:
        m.source_rows(raw,name)
    except ValueError:
        return
    raise AssertionError("referee accepted an adversarial artifact")

def main():
    m.selftest()
    bundle=os.environ.get("J24I68_BUNDLE")
    if not bundle:
        print("J24I68_BUNDLE not supplied; pure arithmetic selftest passed")
        return
    report=m.analyze(bundle)
    assert list(report["results"])==list(m.EXPECTED)
    assert [len(r["all_rows"]) for r in report["results"].values()]==[32,32,32]
    assert [len(r["verdict"]["official_cmpct_reds"]) for r in report["results"].values()]==[2,5,0]
    assert [r["verdict"]["preregistered_h1_survives"] for r in report["results"].values()]==[False,True,False]
    assert report["all_three_h1_survive"] is False
    with zipfile.ZipFile(bundle) as z:
        n=next(iter(m.EXPECTED))
        original=z.read(n)
        assert hashlib.sha256(original).hexdigest()==m.EXPECTED[n][0]
        refuse(original+b"tampering",n)
        for member,mutator in (
            ("corpus.json",lambda x:x.__setitem__("tree_sha256","0"*64)),
            ("candidate.json",lambda x:x.__setitem__("source_commit","0"*40)),
            ("base-native.json",lambda x:x.__setitem__("source_commit","0"*40)),
        ):
            forged=rewrite_member(original,member,mutator)
            refuse(forged,n)
            previous=m.EXPECTED[n]
            m.EXPECTED[n]=(hashlib.sha256(forged).hexdigest(),previous[1],previous[2])
            try:refuse(forged,n)
            finally:m.EXPECTED[n]=previous
        # A malicious swapped timestamp need not alter the source identity: it should
        # be refused at the original provider ZIP digest boundary.
        forged=rewrite_member(original,"base-a.json",lambda x:x["corpora"]["binary"]["library"]["cmpct"].__setitem__("create_s_median",1.0))
        refuse(forged,n)
        # These two controls MUST fail even after adjusting the outer ZIP digest,
        # because the source-identical surrogate cannot compare changed archive shape.
        for engine in ("zip","cmpct"):
            def alter_size(x):
                cell=x["corpora"]["binary"]["library"][engine]
                cell["bytes"]=int(cell["bytes"])+1
            forged=rewrite_member(original,"base-a.json",alter_size)
            previous=m.EXPECTED[n]
            m.EXPECTED[n]=(hashlib.sha256(forged).hexdigest(),previous[1],previous[2])
            try:refuse(forged,n)
            finally:m.EXPECTED[n]=previous
    print("J24I68 PASS: 3 source-identical provider ZIPs, 96 CMPCT/ZIP paired cells, 2/5/0 inherited reds; 10 hostile refusal paths")

if __name__=="__main__":
    main()
