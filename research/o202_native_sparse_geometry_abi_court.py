#!/usr/bin/env python3
"""O202: independent native C ABI vs Python on immutable O198 r24 sparse wires.

O202 prereg: docs/v031-research/2026-10-26-o202-native-python-sparse-prereg.md
Research-only: never redefines a Reader/native baseline or emits product safety credit.
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

from o198_sparse_extent_range_court import REL, PAYLOAD, installed_custody, invoke, wire_archive


def run_native(lib, path: Path) -> dict:
    handle=ctypes.c_void_p()
    start=time.perf_counter_ns()
    code=int(lib.cmpct_open(os.fsencode(path),ctypes.byref(handle)))
    result={"open_status":code,"handle_nonnull":bool(handle.value),
            "open_ns":time.perf_counter_ns()-start}
    if code!=0 or not handle.value:
        # Native must never return a non-null handle on failure.
        return result
    try:
        result["revision"]=int(lib.cmpct_revision(handle))
        result["entry_count"]=int(lib.cmpct_entry_count(handle))
        if result["entry_count"]!=1:
            result["unexpected_count"]=True
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


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--native-library",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    root=Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    assert head==os.environ["EVIDENCE_HEAD"],("source drift",head,os.environ["EVIDENCE_HEAD"])
    assert args.native_library.is_file(),f"missing genuine compiled native library: {args.native_library}"
    lib=ctypes.CDLL(str(args.native_library.resolve()))
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

    src=installed_custody()
    git_sha=lambda p:subprocess.check_output(["git","rev-parse",f"HEAD:{p}"],cwd=root,text=True).strip()
    data={
        "question":"NATIVE_R24_SPARSE_GEOMETRY_ADMISSION_VS_PYTHON_O198",
        "host":{"system":platform.platform(),"python":platform.python_version()},
        "source":{"head":head,"installed_python":src,
            "native_lib_rs_blob":git_sha("native/cmpct-core/src/lib.rs"),
            "native_cargo_lock_blob":git_sha("native/cmpct-core/Cargo.lock"),
            "native_library_sha256":hashlib.sha256(args.native_library.read_bytes()).hexdigest(),
            "o198_wire_court_blob":git_sha("research/o198_sparse_extent_range_court.py"),
            "o202_court_blob":git_sha("research/o202_native_sparse_geometry_abi_court.py")},
        "cases":[]
    }
    with tempfile.TemporaryDirectory(prefix="o202-sparse-wire-") as d:
        work=Path(d)
        for length in (4,1,2,5):
            archive_bytes, wire=wire_archive(length)
            p=work/f"extent-{length}.cmpct"
            p.write_bytes(archive_bytes)
            assert hashlib.sha256(p.read_bytes()).hexdigest()==wire["archive_sha256"]
            python_result=invoke(p,work/f"py-extract-{length}")
            native_result=run_native(lib,p)
            data["cases"].append({
                "declared_extent_length":length,"wire":wire,
                "python":python_result,"native":native_result})
    good=data["cases"][0]
    positive=(
        good["python"]["verify"]=={"ok":True,"value":1}
        and good["python"]["full_read"]=={"ok":True,"value":PAYLOAD.hex()}
        and good["python"]["late_range"]=={"ok":True,"value":PAYLOAD[2:].hex()}
        and good["native"]["open_status"]==0
        and good["native"]["handle_nonnull"]
        and good["native"].get("revision")==24
        and good["native"].get("entry_count")==1
        and good["native"].get("entry_path")==REL
        and good["native"].get("entry_path_probe_status")==0
        and good["native"].get("entry_path_status")==0
        and good["native"].get("late_range_status")==0
        and good["native"].get("late_range_bytes")==2
        and good["native"].get("late_range_hex")==PAYLOAD[2:].hex())
    bad=data["cases"][1:]
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
    data["positive_control_pass"]=bool(positive)
    data["historical_python_acceptance_reproduced"]=bool(python_accepts)
    data["historical_late_range_mismatch_reproduced"]=bool(python_wrong)
    data["native_schema_rejection"]=bool(native_rejects)
    if not positive:
        decision="INCONCLUSIVE_VALID_CONTROL_FAIL"
    elif python_accepts and python_wrong and native_rejects:
        decision="NATIVE_PYTHON_SPARSE_GEOMETRY_ADMISSION_SPLIT_CONFIRMED"
    else:
        decision="UNEXPECTED_OR_CONTRADICTORY_DIFFERENTIAL_REQUIRES_REVIEW"
    data["decision"]=decision
    data["product_changed"]=False
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("O202_DECISION="+decision)
    print("O202_MATRIX="+json.dumps([{
        "declared":x["declared_extent_length"],
        "python_late":x["python"]["late_range"],
        "native_open":x["native"]["open_status"],
        "native_late":x["native"].get("late_range_hex")
    } for x in data["cases"]],sort_keys=True))
    return 1 if not positive else 0


if __name__=="__main__":
    raise SystemExit(main())
