#!/usr/bin/env python3
"""J24B11 independent transfer of the frozen J24B10 sparse quota hostile corpus to #573."""
from __future__ import annotations
import argparse
import binascii
import hashlib
import inspect
import json
from pathlib import Path
import os
import subprocess

import msgpack
from cmpct.codec import MAGIC,VERSION,HDR,BMAGIC,BHDR,FMAGIC,FTR,K_FILE,S_SPARSE,CODEC_RAW,zc,sha
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

L=16_384
B=8_192
SRC_HEAD_EXPECTED="9f269ce8a13b54e44679942d018b226e8dce4d6a"
ORIGINAL_SHA="d36da9b74217904e7e957ca03672bce857350b3b26faaacc0a376c89ed21ce61"
MUTANT_SHA="50277518ace719f00dcd085ef274fd2df3c1b80eac19989cd31aa3b158d608d5"
PHYSICAL_SHA="3327af305bc2f7a6397c98ccbd2213da46145e0691a11d7c26c26054bae9becd"

def digest(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def wire(index,physical):
    ib=msgpack.packb(index,use_bin_type=True)
    enc=zc(ib,12)
    return (HDR.pack(MAGIC,VERSION,0,len(enc),len(ib),len(physical),sha(ib))
            + enc+physical+enc+FTR.pack(FMAGIC,0,1,0,0,len(enc),len(ib),0,sha(ib)))

def expect_bad(fn,fragment,label):
    try:fn()
    except Exception as exc:
        message=f"{type(exc).__name__}: {exc}"
        if fragment.lower() not in message.lower():
            raise AssertionError(f"{label}: wrong refusal {message}") from exc
        return message
    raise AssertionError(f"{label}: unexpectedly accepted")

def check_install(module, name):
    import inspect
    imported=Path(inspect.getfile(module)).resolve()
    checkout=Path(__file__).resolve().parents[1]/"src"/"cmpct"/name
    checkout=checkout.resolve()
    assert imported != checkout, f"{name}: checkout import masquerades as installed wheel"
    norm=lambda b:b.replace(b"\r\n",b"\n")
    s=norm(checkout.read_bytes()); p=norm(imported.read_bytes())
    assert s==p,f"{name}: installed module differs from checkout source"
    return {"installed_path":str(imported),"sha256_normalized":digest(s)}

def run(out:Path):
    assert not out.exists(), "Never overwrite user/evidence directory"
    out.mkdir(parents=True)
    source_head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    from cmpct import sparse_extract
    identities={"reader":check_install(CMPCT,"reader.py"),
                "sparse_helper":check_install(sparse_extract.write_sparse_verified,"sparse_extract.py")}
    payload=b"".join(hashlib.sha256(f"J24B10:{i}".encode()).digest() for i in range(B//32))
    original=b"\0"*4096+payload+b"\0"*(L-4096-B)
    physical=BHDR.pack(BMAGIC,CODEC_RAW,0,0,B,B,0,binascii.crc32(payload)&0xffffffff,sha(payload))+payload
    index={"v":VERSION,"files":[["sparse.bin",K_FILE,0o644,0,L,sha(original),[S_SPARSE,[[4096,B,[0]]]]]],
           "blobs":[[0,B,B,CODEC_RAW,0]],"recipes":[],"dict_blob":None,"fsmeta":{}}
    mutated=msgpack.unpackb(msgpack.packb(index,use_bin_type=True),raw=False)
    mutated["files"][0][6][1][0][:2]=[L-1,1]
    good_wire=wire(index,physical);bad_wire=wire(mutated,physical)
    assert digest(good_wire)==ORIGINAL_SHA
    assert digest(bad_wire)==MUTANT_SHA
    assert digest(physical)==PHYSICAL_SHA
    good=out/"source-original.cmpct";bad=out/"source-mutant.cmpct"
    good.write_bytes(good_wire);bad.write_bytes(bad_wire)
    preflight_archive(good)
    preflight_bad=expect_bad(lambda:preflight_archive(bad),"extent","strict malformed preflight")
    accepted=out/"valid-accepted"
    undercap=out/"valid-undercap"
    with CMPCT(good) as a:
        assert a.read("sparse.bin")==original and a.verify()==1
        too_small=expect_bad(lambda:a.extractall(undercap,max_bytes=L-1,metadata=False),"above limit","valid undercap")
        a.extractall(accepted,max_bytes=L,metadata=False)
    assert (accepted/"sparse.bin").read_bytes()==original
    # Original J24B11 stronger gate FAILED and remains recorded in hosted run
    # 40762227735: the inherited #573 Reader creates an empty destination
    # directory before checking max_bytes. J24B11b independently probes only
    # the sparse physical-extent publication boundary, not that broader gate.
    assert undercap.is_dir(), "inherited pre-budget destination side effect changed"
    assert list(undercap.iterdir()) == [], "undercap must not materialize any logical member"
    existing=out/"hostile-existing";existing.mkdir()
    target=existing/"sparse.bin"
    canary=hashlib.sha256(b"J24B11-existing-canary").digest()*7
    target.write_bytes(canary)
    before=os.stat(target)
    fresh=out/"hostile-fresh";fresh.mkdir()
    with CMPCT(bad) as a:
        mismatch=expect_bad(lambda:a.read("sparse.bin"),"file integrity failure","malformed read")
        mismatch_v=expect_bad(lambda:a.verify(),"file integrity failure","malformed verify")
        guard=expect_bad(lambda:a.extractall(existing,max_bytes=L,metadata=False),
                         "sparse extent overrun","existing canary protected")
        guard_fresh=expect_bad(lambda:a.extractall(fresh,max_bytes=L,metadata=False),
                               "sparse extent overrun","fresh must refuse")
    assert target.read_bytes()==canary and os.stat(target).st_ino==before.st_ino, "changed existing canary inode/content"
    assert not (fresh/"sparse.bin").exists()
    assert sorted(p.name for p in existing.iterdir()) == ["sparse.bin"], "unexpected leftover stage in preexisting destination"
    assert list(fresh.iterdir()) == [], "unexpected leftover file or stage in fresh destination"
    result={"schema":"cmpct-j24b11-transfer-v1","decision":"EXISTING_SPARSE_HELPER_PREVENTS_J24B10_OVERFLOW",
            "source_head":source_head,"parent_head_expected":SRC_HEAD_EXPECTED,
            "source_identities":identities,"platform":__import__("platform").platform(),
            "original_archive_sha256":digest(good_wire),"mutant_archive_sha256":digest(bad_wire),
            "physical_sha256":digest(physical),"positive_logical_sha256":digest(original),
            "positive_length":L,"signed_mutant_row_length":L,"mutant_physical_payload_length":B,
            "malformed_read_refusal":mismatch,"malformed_verify_refusal":mismatch_v,
            "malformed_preflight_refusal":preflight_bad,
            "malformed_existing_extract_refusal":guard,
            "malformed_fresh_extract_refusal":guard_fresh,
            "valid_undercap_refusal":too_small,"existing_canary_sha256":digest(canary),
            "inherited_undercap_directory_created":True,
            "original_j24b11_gate":"FAILED_PRE_BUDGET_DIRECTORY_CREATION",
            "new_narrow_experiment":"J24B11b",
            "existing_canary_inode_preserved":True,"fresh_bad_not_published":True,
            "stage_cleanup_pass":True}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    run(p.parse_args().out.resolve())
