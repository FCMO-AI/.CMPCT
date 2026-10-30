#!/usr/bin/env python3
"""J24P05d: source-exact PEP 427 .data/purelib installed-native collision court.

No modified native payload may be imported/executed. Only inert data, real pip
install destination and SHA-256 comparisons. Independent from zip-name aliases.
"""
from __future__ import annotations
import base64
import csv
import hashlib
import importlib.util
import io
import json
import platform
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from test_macos_wheel_physical_contract import good_fat, wheel as fixture_wheel

spec=importlib.util.spec_from_file_location("physical_guard_j24p05d",ROOT/"tools"/"validate_macos_wheel_abi.py")
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

NAME="cmpct-0.30.0-cp311-cp311-macosx_10_12_universal2.whl"
NATIVE="cmpct/cmpct_core.cpython-311-darwin.so"
DATA_NATIVE="cmpct-0.30.0.data/purelib/"+NATIVE
DATA_OTHER="cmpct-0.30.0.data/purelib/cmpct/UNRELATED.txt"
RECORD="cmpct-0.30.0.dist-info/RECORD"
INERT=b"J24P05D_HOST_INERT_SPREAD_NO_CODE\n"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def make(root:Path,label:str,extra:str|None,first:bool)->Path:
    path=root/label/NAME
    path.parent.mkdir(parents=True,exist_ok=True)
    fixture_wheel(path,good_fat())
    with zipfile.ZipFile(path) as z:
        src={n:z.read(n) for n in z.namelist() if n!=RECORD}
    value=INERT if extra==DATA_NATIVE else b"J24P05D_DISJOINT"
    if extra:
        src=({extra:value,**src} if first else {**src,extra:value})
    entries=[]
    for n,data in src.items():
        entries.append([n,"sha256="+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("="),str(len(data))])
    entries.append([RECORD,"",""])
    buf=io.StringIO()
    csv.writer(buf,lineterminator="\n").writerows(entries)
    src[RECORD]=buf.getvalue().encode()
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_STORED) as z:
        for n,data in src.items():z.writestr(n,data)
    return path

def install(path:Path,target:Path)->dict:
    cmd=[sys.executable,"-m","pip","install","--no-index","--no-deps","--only-binary=:all:",
         "--target",str(target)]
    if platform.system()=="Linux":
        cmd += ["--platform","macosx_10_12_universal2","--python-version","3.11",
                "--implementation","cp","--abi","cp311"]
    cmd.append(str(path))
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    data=(target/NATIVE).read_bytes() if (target/NATIVE).is_file() else None
    return {"returncode":p.returncode,"stdout_tail":p.stdout[-350:],"stderr_tail":p.stderr[-350:],
            "native_sha256":sha(data) if data is not None else None,
            "native_length":len(data) if data is not None else None,
            "original_retained":data==good_fat(),"spread_inert_won":data==INERT}

def main()->None:
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--output-dir",type=Path,default=Path("j24p05d-results"))
    args=a.parse_args()
    root=args.output_dir
    root.mkdir(parents=True,exist_ok=True)
    variants={"original":(None,False),"disjoint":(DATA_OTHER,False),
              "spread_before":(DATA_NATIVE,True),"spread_after":(DATA_NATIVE,False)}
    result={"schema":"cmpct-j24p05d-data-spread-court-v1",
            "host":{"system":platform.system(),"machine":platform.machine(),"python":sys.version.split()[0]},
            "source":{"guard_sha256":sha((ROOT/"tools"/"validate_macos_wheel_abi.py").read_bytes()),
                      "native_original_sha256":sha(good_fat()),"inert_sha256":sha(INERT)},
            "cases":{}}
    for label,(extra,first) in variants.items():
        wheel=make(root,label,extra,first)
        verdict=gate.inspect(wheel)
        dest=root/"installed"/label
        pipe=install(wheel,dest)
        expected_inert=label.startswith("spread")
        assert verdict["pass"],label+" original physical gate unexpectedly rejected"
        assert pipe["returncode"]==0, label+" pip install failed"
        assert pipe["spread_inert_won"] is expected_inert, label+" installed ownership did not meet prospective result"
        assert pipe["original_retained"] is (not expected_inert), label+" positive control native changed"
        # Store physical installed bytes for detached inspection without running any native code.
        raw=(dest/NATIVE).read_bytes()
        saved=root/"installed-native"/(label+".bin")
        saved.parent.mkdir(exist_ok=True)
        saved.write_bytes(raw)
        result["cases"][label]={"wheel":wheel.name,"wheel_sha256":sha(wheel.read_bytes()),
                                "wheel_bytes":wheel.stat().st_size,"validator_pass":True,"pip":pipe}
    (root/"court.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
    print("J24P05d: PEP427 .data spread observable; no native code executed")

if __name__=="__main__":
    main()
