#!/usr/bin/env python3
"""Independent J24G94 physical binary court: no cmpct product import."""
from __future__ import annotations
import hashlib,json,pathlib,sys
from j24g92_detached_referee import F,footer,chain,reconstruct,sha

def check(root,n,c):
    raw={k:(root/f"{n}-{k}.cmpct").read_bytes() for k in
         ("authentic","damaged-ancestor","after-writer","clean-control","damaged-final")}
    fields={"authentic":"original_sha256","damaged-ancestor":"damaged_ancestor_sha256",
            "after-writer":"after_writer_sha256","clean-control":"clean_control_sha256",
            "damaged-final":"damaged_final_sha256"}
    for k,b in raw.items():assert sha(b)==c[fields[k]]
    a=raw["authentic"];b=raw["damaged-ancestor"];w=raw["after-writer"]
    assert len(a)==len(b) and w.startswith(b)
    edits=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    assert edits==[c["changed_digest_byte_offset"]],edits
    original=chain(a)
    assert len(original)==4
    f0,f1,f2,f3=original
    assert [f["pos"] for f in original]==[c[f"authentic_f{i}"] for i in range(4)]
    try:footer(b,f2["pos"])
    except AssertionError:pass
    else:raise AssertionError("damaged F2 accepted")
    assert footer(b,f3["pos"])["payload_sha"]==f3["payload_sha"]
    assert footer(b,f3["pos"])["prev"]==f2["pos"]
    fresh=chain(w);control=chain(raw["clean-control"])
    assert len(fresh)==len(control)==3
    assert fresh[-1]["pos"]==c["new_writer_f4"]
    assert fresh[-1]["prev"]==f1["pos"] and fresh[-1]["prev"]!=f3["pos"]
    assert fresh[-1]["index"]["ops"]==[["del","f00003.dat"]]
    assert fresh[-1]["index"]["blobs"]==[]
    assert reconstruct(fresh)==reconstruct(control)
    assert len(reconstruct(original))==n-3
    assert len(reconstruct(fresh))==n-2
    assert len(reconstruct(fresh))==c["after_real_writer_members"]
    assert len(w)-len(b)==c["appended_writer_bytes"]
    try:footer(raw["damaged-final"],len(raw["damaged-final"])-F.size)
    except AssertionError:pass
    else:raise AssertionError("damaged newest SHA accepted")
    for key,expected,pos in [
        ("authentic",set(f"f{i:05d}.dat" for i in range(3,n)),f3["pos"]),
        ("damaged_ancestor",set(f"f{i:05d}.dat" for i in range(1,n)),f1["pos"]),
        ("after_writer",set(f"f{i:05d}.dat" for i in range(1,n)) - {"f00003.dat"},fresh[-1]["pos"]),
        ("clean_control",set(f"f{i:05d}.dat" for i in range(1,n)) - {"f00003.dat"},control[-1]["pos"]),
        ("damaged_final",set(f"f{i:05d}.dat" for i in range(1,n)),f1["pos"])]:
        x=c["answers"][key]
        assert x["reader"]["accepted"] and x["preflight"]["accepted"]
        assert set(x["reader"]["paths"])==expected
        assert x["reader"]["footer"]==x["preflight"]["result"]["latest_footer"]==pos
        assert x["preflight"]["result"]["files"]==len(expected)
        for path,digest in x["reader"]["sha256_by_path"].items():
            i=int(path[1:6])
            assert digest==sha(hashlib.sha256(f"j24g94-{n}-{i}".encode()).digest())
    return {"n":n,"modified_sha_bytes":len(edits),
            "physical_parent_proof":True,"after_original":n-3,
            "after_damaged_ancestor":n-1,"after_real_writer":n-2,
            "writer_footer":fresh[-1]["pos"],"writer_prev":fresh[-1]["prev"],
            "individual_f3_payload_digest_still_valid":True,
            "fourth_commit_bytes":len(w)-len(b),"distinct_whole_file_sha":sha(a)!=sha(b)}

def main():
    root=pathlib.Path(sys.argv[1])
    r=json.loads((root/"receipt.json").read_text())
    assert r["status"]=="PASS"
    assert r["source"]["reader_blob"]=="e716233403dabd0966863c45635e18fa5ac6afb8"
    assert r["source"]["writer_blob"]=="964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c"
    out={"schema":"j24g94-detached-binary-referee-v1",
         "status":"PASS","no_product_import":True,"source_head":r["source"]["head"],
         "cases":{str(n):check(root,n,r["cases"][str(n)]) for n in (16,128)}}
    (root/"detached-referee.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("J24G94_REFEREE",json.dumps({k:(v["after_original"],v["after_damaged_ancestor"],v["after_real_writer"]) for k,v in out["cases"].items()},sort_keys=True))
if __name__=="__main__":main()
