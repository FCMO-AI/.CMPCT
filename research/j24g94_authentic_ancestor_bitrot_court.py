#!/usr/bin/env python3
"""J24G94 installed public Writer after one-byte corruption of a real ancestor.

A real Writer emitted F1/F2/F3 before F2's footer SHA is manually damaged.
Research only; disk failure and power loss are NOT simulated.
"""
from __future__ import annotations
import hashlib, json, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path
from cmpct.builder import Builder
from cmpct.transactions import append_delete
from j24g92_footer_link_court import FOOTER, footer, lineage, sha, inspect_reader, inspect_preflight
from j24g93_orphan_writer_court import check_reader

PARENT = "5f765553a62a57ecd1ca4ac2b15bf713b8496867"
PREREG = "afbc896291a0061ee0a6dfdaa6147fcdee719799"
READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"
WRITER_BLOB = "964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c"

def attest():
    def git(*args):return subprocess.check_output(["git", *args], text=True).strip()
    head=git("rev-parse","HEAD")
    for ancestor in (PARENT,PREREG):
        subprocess.run(["git","merge-base","--is-ancestor",ancestor,"HEAD"],check=True)
    assert git("rev-parse","HEAD:src/cmpct/reader.py")==READER_BLOB
    assert git("rev-parse","HEAD:src/cmpct/transactions.py")==WRITER_BLOB
    return {"head":head,"parent":PARENT,"prereg":PREREG,
            "reader_blob":READER_BLOB,"writer_blob":WRITER_BLOB}

def case(root:Path, evidence:Path, n:int):
    source=root/f"source_{n}";source.mkdir()
    hashes={}
    for i in range(n):
        name=f"f{i:05d}.dat"
        raw=hashlib.sha256(f"j24g94-{n}-{i}".encode()).digest()
        (source/name).write_bytes(raw);hashes[name]=sha(raw)
    p=root/f"{n}-authentic.cmpct"
    Builder(source,workers=1,reproducible=False).build(p)
    for i in range(3):append_delete(p,f"f{i:05d}.dat")
    original=p.read_bytes()
    history=lineage(original)
    assert len(history)==4
    f0,f1,f2,f3=history
    expected_original=set(hashes)-{"f00000.dat","f00001.dat","f00002.dat"}
    observed={"authentic":check_reader(p,expected_original,hashes,f3["pos"])}
    shutil.copyfile(p,evidence/f"{n}-authentic.cmpct")

    # Only the original F2 SHA field is modified. F3 payload and digest stay valid,
    # but the chain from F3 no longer reaches F1+F0.
    corrupt=bytearray(original)
    digest_byte=f2["pos"]+FOOTER.size-32
    corrupt[digest_byte]^=0xA5
    corrupt=bytes(corrupt)
    assert sum(a!=b for a,b in zip(original,corrupt))==1
    assert len(original)==len(corrupt) and sha(original)!=sha(corrupt)
    try:footer(corrupt,f2["pos"])
    except AssertionError:pass
    else:raise AssertionError("tampered F2 SHA incorrectly valid")
    assert footer(corrupt,f3["pos"])["payload_sha"]==f3["payload_sha"]
    p.write_bytes(corrupt)
    expected_recovered=set(hashes)-{"f00000.dat"}
    observed["damaged_ancestor"]=check_reader(p,expected_recovered,hashes,f1["pos"])
    shutil.copyfile(p,evidence/f"{n}-damaged-ancestor.cmpct")

    # CRITICAL: actual public Writer operation, not a synthetically encoded footer.
    append_delete(p,"f00003.dat")
    written=p.read_bytes()
    assert written.startswith(corrupt)
    new_chain=lineage(written)
    assert len(new_chain)==3
    new_footer=new_chain[-1]
    assert new_footer["prev"]==f1["pos"]!=f3["pos"]
    assert new_footer["payload"]["ops"]==[["del","f00003.dat"]]
    expected_after=expected_recovered-{"f00003.dat"}
    observed["after_writer"]=check_reader(p,expected_after,hashes,new_footer["pos"])
    shutil.copyfile(p,evidence/f"{n}-after-writer.cmpct")

    # Strong simplest control: actual same source F0+F1 physical prefix (no
    # damaged F2 nor unrooted F3), then public Writer performs identical DELETE.
    clean=root/f"{n}-clean.cmpct"
    clean.write_bytes(original[:f1["pos"]+FOOTER.size])
    append_delete(clean,"f00003.dat")
    cc=lineage(clean.read_bytes())
    observed["clean_control"]=check_reader(clean,expected_after,hashes,cc[-1]["pos"])
    assert observed["clean_control"]["reader"]["sha256_by_path"]==observed["after_writer"]["reader"]["sha256_by_path"]
    shutil.copyfile(clean,evidence/f"{n}-clean-control.cmpct")

    # A torn newest F4 must recover F1, not the individually SHA-valid F3.
    bad=bytearray(written);bad[-1]^=0x5A
    tail=root/f"{n}-damaged-final.cmpct";tail.write_bytes(bad)
    observed["damaged_final"]=check_reader(tail,expected_recovered,hashes,f1["pos"])
    shutil.copyfile(tail,evidence/f"{n}-damaged-final.cmpct")

    return {"n":n,"original_sha256":sha(original),
            "damaged_ancestor_sha256":sha(corrupt),
            "after_writer_sha256":sha(written),
            "clean_control_sha256":sha(clean.read_bytes()),
            "damaged_final_sha256":sha(bytes(bad)),
            "changed_digest_byte_offset":digest_byte,
            "authentic_f0":f0["pos"],"authentic_f1":f1["pos"],
            "authentic_f2":f2["pos"],"authentic_f3":f3["pos"],
            "new_writer_f4":new_footer["pos"],"new_writer_parent":new_footer["prev"],
            "before_damage_members":len(expected_original),
            "after_digest_damage_members":len(expected_recovered),
            "after_real_writer_members":len(expected_after),
            "appended_writer_bytes":len(written)-len(corrupt),
            "f3_payload_sha_still_valid":True,
            "only_one_real_f2_digest_byte_changed":True,"answers":observed}

def main():
    evidence=Path(os.environ.get("J24G94_EVIDENCE","evidence/j24g94"));evidence.mkdir(parents=True,exist_ok=True)
    report={"schema":"j24g94-authentic-ancestor-digest-damage-writer-v1",
            "source":attest(),"host":platform.platform(),"python":sys.version,
            "product_source_modified":False,"release_credit":0,
            "scope":"single manual authentic F2 digest corruption, not power-loss",
            "status":"STARTED","cases":{}}
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g94-") as d:
            for n in (16,128):report["cases"][str(n)]=case(Path(d),evidence,n)
        assert all(c["new_writer_parent"]==c["authentic_f1"] and
                   c["new_writer_parent"]!=c["authentic_f3"] for c in report["cases"].values())
        report["status"]="PASS"
        report["decision"]="ACTUAL_WRITER_SKIPS_SHA_VALID_F3_AFTER_F2_DIGEST_DAMAGE"
    except BaseException as exc:
        report["status"]="FAIL";report["fatal"]={"type":type(exc).__name__,"detail":str(exc)}
        raise
    finally:
        (evidence/"receipt.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
        print("J24G94_REPORT",json.dumps({
            "status":report["status"],"decision":report.get("decision"),
            "cases":{k:{"before":v["before_damage_members"],
                        "recovered":v["after_digest_damage_members"],
                        "writer":v["after_real_writer_members"],
                        "prev":v["new_writer_parent"],
                        "skipped_f3":v["authentic_f3"]} for k,v in report["cases"].items()}
        },sort_keys=True))

if __name__=="__main__":main()
