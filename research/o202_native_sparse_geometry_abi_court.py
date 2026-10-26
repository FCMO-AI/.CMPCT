#!/usr/bin/env python3
"""O202a/O202b independent native vs Python sparse geometry admission court.

O202a prereg: docs/v031-research/2026-10-26-o202-native-python-sparse-prereg.md
O202b prereg: docs/v031-research/2026-10-26-o202b-root-schema-prereg.md
Original O198 wires are immutable and explicitly preserved; normalized index wires
are DISTINCT authenticated archives with an additional root "v":24 field.
"""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import msgpack
from cmpct.codec import (MAGIC, VERSION, FMAGIC, HDR, FTR, zc, zd, sha)
from cmpct.validation import preflight_archive
from o198_sparse_extent_range_court import REL, PAYLOAD, installed_custody, invoke, wire_archive


def with_version_root(original: bytes) -> tuple[bytes, dict]:
    magic,version,flags,cs,us,ds,ih=HDR.unpack(original[:HDR.size])
    assert magic==MAGIC and version==VERSION
    primary=original[HDR.size:HDR.size+cs]
    plain=zd(primary,us)
    assert sha(plain)==ih
    idx=msgpack.unpackb(plain,raw=False)
    assert "v" not in idx, "O198 original root unexpectedly has revision"
    record=original[HDR.size+cs:HDR.size+cs+ds]
    assert len(record)==ds
    # Preserve the original complete physical blob record byte-for-byte.
    # Exactly one additional authenticated index field; do not alter extents.
    corrected={"v":VERSION,**idx}
    new_plain=msgpack.packb(corrected,use_bin_type=True)
    new_comp=zc(new_plain,12)
    new_hash=sha(new_plain)
    footer=FTR.pack(FMAGIC,0,1,0,0,len(new_comp),len(new_plain),0,new_hash)
    result=(HDR.pack(MAGIC,VERSION,flags,len(new_comp),len(new_plain),len(record),new_hash)
            +new_comp+record+new_comp+footer)
    assert msgpack.unpackb(zd(new_comp,len(new_plain)),raw=False)==corrected
    assert result[HDR.size+len(new_comp):HDR.size+len(new_comp)+ds]==record
    return result,{
        "archive_sha256":hashlib.sha256(result).hexdigest(),
        "archive_bytes":len(result),
        "added_index_field":"v",
        "new_index_sha256":new_hash.hex(),
        "physical_record_sha256":hashlib.sha256(record).hexdigest(),
        "old_index_sha256":ih.hex(),
        "root_revision":VERSION,
    }


def run_native(lib, path: Path) -> dict:
    handle=ctypes.c_void_p()
    start=time.perf_counter_ns()
    code=int(lib.cmpct_open(os.fsencode(path),ctypes.byref(handle)))
    result={"open_status":code,"handle_nonnull":bool(handle.value),
            "open_ns":time.perf_counter_ns()-start}
    if code!=0 or not handle.value:
        return result
    try:
        result["revision"]=int(lib.cmpct_revision(handle))
        result["entry_count"]=int(lib.cmpct_entry_count(handle))
        if result["entry_count"]!=1:
            return result
        path_size=ctypes.c_size_t()
        pstatus=int(lib.cmpct_entry_path(handle,0,None,0,ctypes.byref(path_size)))
        path_buf=ctypes.create_string_buffer(path_size.value+1)
        got_status=int(lib.cmpct_entry_path(handle,0,path_buf,len(path_buf),ctypes.byref(path_size)))
        result["entry_path_probe_status"]=pstatus
        result["entry_path_status"]=got_status
        result["entry_path"]=path_buf.value.decode("utf-8")
        out=ctypes.create_string_buffer(2)
        copied=ctypes.c_size_t(0)
        status=int(lib.cmpct_entry_read_range(handle,0,2,out,2,ctypes.byref(copied)))
        result["late_range_status"]=status
        result["late_range_bytes"]=int(copied.value)
        result["late_range_hex"]=out.raw[:copied.value].hex()
        return result
    finally:
        lib.cmpct_close(handle)


def run_preflight(path:Path)->dict:
    try:
        v=preflight_archive(path,verify_blob_headers=True)
        return {"ok":True,"version":v.get("version"),"files":v.get("files")}
    except Exception as exc:
        return {"ok":False,"error_type":type(exc).__name__,"error":str(exc)}


def configure_abi(lib):
    lib.cmpct_open.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype=ctypes.c_int32
    lib.cmpct_close.argtypes=[ctypes.c_void_p]
    lib.cmpct_close.restype=None
    lib.cmpct_revision.argtypes=[ctypes.c_void_p]
    lib.cmpct_revision.restype=ctypes.c_uint16
    lib.cmpct_entry_count.argtypes=[ctypes.c_void_p]
    lib.cmpct_entry_count.restype=ctypes.c_size_t
    lib.cmpct_entry_path.argtypes=[
        ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_entry_path.restype=ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes=[
        ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_entry_read_range.restype=ctypes.c_int32


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--native-library",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    root=Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    assert head==os.environ["EVIDENCE_HEAD"],("source drift",head,os.environ["EVIDENCE_HEAD"])
    assert args.native_library.is_file(),f"missing compiled native library: {args.native_library}"
    lib=ctypes.CDLL(str(args.native_library.resolve()))
    configure_abi(lib)
    src=installed_custody()
    git_sha=lambda p:subprocess.check_output(["git","rev-parse",f"HEAD:{p}"],cwd=root,text=True).strip()
    data={
        "question":"ROOT_VERSION_CONTROLLED_NATIVE_PYTHON_SPARSE_GEOMETRY_DIFFERENTIAL",
        "host":{"system":platform.platform(),"python":platform.python_version()},
        "source":{"head":head,"installed_python":src,
            "native_lib_rs_blob":git_sha("native/cmpct-core/src/lib.rs"),
            "native_cargo_lock_blob":git_sha("native/cmpct-core/Cargo.lock"),
            "native_library_sha256":hashlib.sha256(args.native_library.read_bytes()).hexdigest(),
            "original_o198_court_blob":git_sha("research/o198_sparse_extent_range_court.py"),
            "o202_court_blob":git_sha("research/o202_native_sparse_geometry_abi_court.py"),
            "first_prereg_blob":git_sha("docs/v031-research/2026-10-26-o202-native-python-sparse-prereg.md"),
            "superseding_prereg_blob":git_sha("docs/v031-research/2026-10-26-o202b-root-schema-prereg.md")},
        "original_o198_cases":[],
        "revision_normalized_cases":[]
    }
    with tempfile.TemporaryDirectory(prefix="o202-sparse-wire-") as d:
        work=Path(d)
        for length in (4,1,2,5):
            raw,wire=wire_archive(length)
            p=work/f"original-extent-{length}.cmpct"
            p.write_bytes(raw)
            assert hashlib.sha256(p.read_bytes()).hexdigest()==wire["archive_sha256"]
            data["original_o198_cases"].append({
                "length":length,"original_wire":wire,
                "python":invoke(p,work/f"py-original-extract-{length}"),
                "preflight":run_preflight(p),"native":run_native(lib,p)})
            canonical,canonical_meta=with_version_root(raw)
            p=work/f"revision24-extent-{length}.cmpct"
            p.write_bytes(canonical)
            assert hashlib.sha256(p.read_bytes()).hexdigest()==canonical_meta["archive_sha256"]
            data["revision_normalized_cases"].append({
                "length":length,
                "original_archive_sha256":wire["archive_sha256"],
                "normalized_wire":canonical_meta,
                "python":invoke(p,work/f"py-normalized-extract-{length}"),
                "preflight":run_preflight(p),"native":run_native(lib,p)})
    good=data["revision_normalized_cases"][0]
    positive=(
        good["python"]["verify"]=={"ok":True,"value":1}
        and good["python"]["full_read"]=={"ok":True,"value":PAYLOAD.hex()}
        and good["python"]["late_range"]=={"ok":True,"value":PAYLOAD[2:].hex()}
        and good["preflight"]=={"ok":True,"version":VERSION,"files":1}
        and good["native"]["open_status"]==0
        and good["native"]["handle_nonnull"]
        and good["native"].get("revision")==VERSION
        and good["native"].get("entry_count")==1
        and good["native"].get("entry_path")==REL
        and good["native"].get("entry_path_probe_status")==0
        and good["native"].get("entry_path_status")==0
        and good["native"].get("late_range_status")==0
        and good["native"].get("late_range_bytes")==2
        and good["native"].get("late_range_hex")==PAYLOAD[2:].hex())
    bad=data["revision_normalized_cases"][1:]
    python_accepts=all(
        x["python"]["verify"]=={"ok":True,"value":1}
        and x["python"]["full_read"]=={"ok":True,"value":PAYLOAD.hex()}
        for x in bad)
    python_wrong=all(
        x["python"]["late_range"]=={"ok":True,"value":"0000"}
        for x in bad[:2])
    native_rejects=all(
        x["native"]["open_status"]==-3 and not x["native"]["handle_nonnull"]
        for x in bad)
    strict_rejects=(
        all(
            not x["preflight"]["ok"]
            and x["preflight"].get("error_type")=="ValidationError"
            and "length mismatch" in x["preflight"].get("error","")
            for x in bad[:2])
        and not bad[2]["preflight"]["ok"]
        and bad[2]["preflight"].get("error_type")=="ValidationError"
        and "overlaps or exceeds file" in bad[2]["preflight"].get("error","")
    )
    orig_missing_version=all(
        not x["preflight"]["ok"]
        and "index revision" in x["preflight"].get("error","")
        and x["native"]["open_status"]==-3
        for x in data["original_o198_cases"])
    data["positive_control_pass"]=bool(positive)
    data["normalized_python_acceptance"]=bool(python_accepts)
    data["normalized_python_wrong_late_bytes"]=bool(python_wrong)
    data["normalized_native_schema_rejection"]=bool(native_rejects)
    data["normalized_preflight_geometry_rejection"]=bool(strict_rejects)
    data["original_o198_missing_revision_confounder_confirmed"]=bool(orig_missing_version)
    if not positive:
        decision="INCONCLUSIVE_NORMALIZED_VALID_CONTROL_FAILED"
    elif python_accepts and python_wrong and native_rejects and strict_rejects:
        decision="EXISTING_STRICT_VALIDATORS_REJECT_GEOMETRY_ORDINARY_READER_GAP"
    else:
        decision="UNEXPECTED_OR_CONTRADICTORY_DIFFERENTIAL_REQUIRES_REVIEW"
    data["decision"]=decision
    data["product_changed"]=False
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("O202_DECISION="+decision)
    print("O202_ORIGINAL_ROOT_VERSION_CONFOUNDER="+str(orig_missing_version))
    print("O202_MATRIX="+json.dumps([{
        "length":x["length"],
        "python_late":x["python"]["late_range"],
        "strict_preflight":x["preflight"],
        "native_open":x["native"]["open_status"],
        "native_late":x["native"].get("late_range_hex")
    } for x in data["revision_normalized_cases"]],sort_keys=True))
    return 1 if not positive else 0


if __name__=="__main__":
    raise SystemExit(main())
