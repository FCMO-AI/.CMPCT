#!/usr/bin/env python3
"""J24F11: authentic r24 extracted-file publication, fresh inode versus late leaf.

Scope: Linux O_TMPFILE/linkat create-only branch. Existing-leaf overwrite and
unsupported filesystems are explicitly NOT authenticated against issue #528.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

from j24f04_raw_chunk_immutable_transfer import independent_revision24, blob_sha


def sha(data): return hashlib.sha256(data).hexdigest()


def run_case(root:Path, storage:int, scenario:str):
    from cmpct.reader import CMPCT
    chunks=[hashlib.shake_256(("j24f11-"+str(storage)+"-"+str(i)).encode()).digest(98317+i*239)
            for i in range(3)]
    original=b"".join(chunks)
    name,archive,payload_off=independent_revision24(chunks,storage)
    src=root/"source.cmpct"
    src.write_bytes(archive)
    out=root/"output"
    out.mkdir()
    leaf=out/name
    sentinel=b"external existing inode - must not overwrite"
    if scenario=="existing":
        leaf.write_bytes(sentinel)
    if scenario=="corrupt":
        with open(src,"r+b") as handle:
            handle.seek(payload_off)
            handle.write(bytes([chunks[0][0]^0xff]))
    stage=[]
    original_write=os.write

    def spy_write(fd,data):
        if not stage:
            observed=os.fstat(fd)
            visible=[x.name for x in out.iterdir() if ".cmpct-part-" in x.name]
            stage.append({"inode":observed.st_ino,"device":observed.st_dev,
                          "nlink":observed.st_nlink,"stage_names":visible,
                          "size_first_write":len(data)})
            if scenario=="late":
                cmd=[sys.executable,"-c",
                     "from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(bytes.fromhex(sys.argv[2]))",
                     str(leaf),sentinel.hex()]
                result=subprocess.run(cmd,text=True,capture_output=True,timeout=15,check=True)
                stage[0]["actor_pid_distinct"]=result.returncode==0
        return original_write(fd,data)

    err=None
    with CMPCT(src) as reader:
        assert reader.by[name][4]==len(original)
        assert reader.by[name][6][0]==storage
        os.write=spy_write
        try:
            try:reader.extractall(out,metadata=False)
            except Exception as ex:err=type(ex).__name__+": "+str(ex)
        finally:os.write=original_write

    assert stage, (storage,scenario,"never wrote bytes")
    current=leaf.read_bytes() if leaf.exists() else None
    visible=[x.name for x in out.iterdir() if ".cmpct-part-" in x.name]
    if scenario=="fresh":
        assert err is None and current==original
        assert (leaf.stat().st_dev,leaf.stat().st_ino)==(stage[0]["device"],stage[0]["inode"])
        assert stage[0]["nlink"]==0 and not stage[0]["stage_names"]
        assert not visible
        outcome="EXACT_DESCRIPTOR_PUBLISHED"
    elif scenario=="late":
        assert err is not None and ("FileExistsError" in err or "Errno 17" in err),err
        assert current==sentinel and not visible
        assert stage[0]["nlink"]==0 and not stage[0]["stage_names"]
        outcome="CONCURRENT_LEAF_PRESERVED"
    elif scenario=="existing":
        assert err is None and current==original and not visible
        assert stage[0]["stage_names"],"Expected inherited named-stage overwrite"
        outcome="LEGACY_EXISTING_OVERWRITE"
    elif scenario=="corrupt":
        assert err is not None and current is None and not visible
        assert stage[0]["nlink"]==0 and not stage[0]["stage_names"]
        outcome="INDEXED_SHA_REJECTS_CORRUPTION"
    else:raise AssertionError(scenario)
    return {"kind":storage,"scenario":scenario,"outcome":outcome,
            "stage":stage[0],"error":err,
            "logical_sha":sha(original),
            "published_sha":sha(current) if current is not None else None,
            "no_stage_name_after":not visible}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--expected-blob",required=True)
    args=parser.parse_args()
    if not sys.platform.startswith("linux") or not hasattr(os,"O_TMPFILE"):
        raise RuntimeError("J24F11 Linux anonymous-fd court needs O_TMPFILE")
    import cmpct.reader as module
    installed=Path(module.__file__).resolve()
    assert installed.is_relative_to(Path(sys.prefix)), ("not independently installed",installed)
    assert blob_sha(installed.read_bytes())==args.expected_blob
    cases=[]
    with tempfile.TemporaryDirectory(prefix="cmpct-j24f11-") as base:
        for kind in (1,5):
            for scenario in ("fresh","late","existing","corrupt"):
                root=Path(base)/f"{kind}-{scenario}"
                root.mkdir()
                result=run_case(root,kind,scenario)
                cases.append(result)
                print("J24F11_CASE="+json.dumps(result,sort_keys=True),flush=True)
    assert len(cases)==8
    result={"schema":"j24f11-fresh-fd-link-v1",
            "installed_reader_blob":args.expected_blob,
            "host":sys.platform,
            "cases":cases,
            "decision":"SCOPED_LINUX_FRESH_CHUNK_FD_PUBLISH_PASS",
            "nonclaims":["existing destination protection","all filesystem support",
                         "other Reader representations","after-syscall namespace mutation",
                         "complete performance","release authority"]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True))
    print("J24F11_DECISION="+result["decision"],flush=True)


if __name__=="__main__":
    main()
