#!/usr/bin/env python3
"""J24C07b: exact-source same-wire full preflight ABBA, not a release benchmark."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

import msgpack


BASE_VALIDATION_BLOB = "fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8"
CANDIDATE_VALIDATION_BLOB = "0614723549403f398a43552a7c5ad3f00fbec688"
WORKER = r"""
import hashlib, inspect, json, os, pathlib, subprocess, sys, time
from cmpct import validation as v
params=json.loads(sys.argv[1])
path=pathlib.Path(params["archive"])
module=pathlib.Path(inspect.getfile(v)).resolve()
repo=pathlib.Path(params["workspace"]).resolve()
assert not module.is_relative_to(repo), ("editable or in-tree module imported",str(module))
blob=subprocess.check_output(["git","hash-object",str(module)],text=True).strip()
assert blob==params["validation_blob"], ("source mismatch",blob,params["validation_blob"])
first=v.preflight_archive(path)
assert first["files"]==params["count"],("file count mismatch",first)
observations=[]
for _ in range(params["repetitions"]):
    before_w=time.perf_counter_ns();before_c=time.process_time_ns()
    current=v.preflight_archive(path)
    cpu=time.process_time_ns()-before_c
    wall=time.perf_counter_ns()-before_w
    assert current==first,("unstable preflight",)
    observations.append({"wall_ns":wall,"cpu_ns":cpu})
hwm=None
if sys.platform.startswith("linux"):
    try:
        for line in pathlib.Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                hwm=int(line.split()[1])*1024
    except OSError:
        pass
print(json.dumps({"decision":"VALID_SAME_INDEX","blob":blob,"module":str(module),
                  "count":params["count"],"observations":observations,
                  "rss_hwm_bytes":hwm},sort_keys=True))
"""


def build_wire(golden: Path, count: int) -> bytes:
    """Re-authenticate *both* index copies; preserve original payload bytes."""
    from cmpct.codec import HDR, FTR, MAGIC, FMAGIC, VERSION, S_VZIP, zd, zc, sha
    row = json.loads(golden.read_text(encoding="utf-8"))["vector"]
    wire = base64.b64decode(row["archive_base64"], validate=True)
    assert hashlib.sha256(wire).hexdigest() == row["archive_sha256"]
    magic, version, flags, csize, usize, physical_len, digest = HDR.unpack_from(wire)
    assert magic == MAGIC and version == VERSION
    original_packed = wire[HDR.size:HDR.size+csize]
    payload = zd(original_packed, usize)
    assert len(payload) == usize and sha(payload) == digest
    physical = wire[HDR.size+csize:HDR.size+csize+physical_len]
    index = msgpack.unpackb(payload, raw=False)
    assert len(index["recipes"]) == len(index["files"]) == 1
    original_file = index["files"][0]
    original_recipe = index["recipes"][0]
    assert original_file[6][0] == S_VZIP
    index = copy.deepcopy(index)
    index["files"] = []
    index["recipes"] = []
    for i in range(count):
        recipe = copy.deepcopy(original_recipe)
        record = copy.deepcopy(original_file)
        record[0] = f"member-{i:05d}.zip"
        record[6] = [S_VZIP, i]
        index["files"].append(record)
        index["recipes"].append(recipe)
    plain = msgpack.packb(index, use_bin_type=True)
    compressed = zc(plain, 12)
    next_hash = sha(plain)
    head = HDR.pack(MAGIC, VERSION, flags, len(compressed), len(plain),
                    physical_len, next_hash)
    tail = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed),
                    len(plain), 0, next_hash)
    archive = head + compressed + physical + compressed + tail
    assert archive[HDR.size+len(compressed):HDR.size+len(compressed)+physical_len] == physical
    assert sha(zd(compressed, len(plain))) == next_hash
    return archive


def strict_load(text: str):
    def unique(pairs):
        d = {}
        for key, value in pairs:
            if key in d:
                raise ValueError("duplicate JSON receipt key")
            d[key] = value
        return d
    return json.loads(text, object_pairs_hook=unique)


def run_worker(site: Path, path: Path, count: int, workspace: Path, expected: str, repetitions: int):
    params = {"archive":str(path.resolve()),"count":count,"workspace":str(workspace.resolve()),
              "validation_blob":expected,"repetitions":repetitions}
    env = dict(os.environ)
    env["PYTHONPATH"] = str(site.resolve())
    start = time.perf_counter_ns()
    run = subprocess.run([sys.executable,"-c",WORKER,json.dumps(params,sort_keys=True)],
                         cwd=path.parent,env=env,text=True,capture_output=True,check=False)
    external_wall = time.perf_counter_ns() - start
    if run.returncode != 0:
        raise RuntimeError("worker failed, source="+expected+" stderr="+run.stderr+
                           " stdout="+run.stdout)
    payload = strict_load(run.stdout)
    assert payload["blob"] == expected and payload["count"] == count
    assert len(payload["observations"]) == repetitions
    assert all(x["wall_ns"] > 0 and x["cpu_ns"] >= 0 for x in payload["observations"])
    assert all(x["wall_ns"] < external_wall for x in payload["observations"])
    return {**payload,"external_wall_ns":external_wall,
            "worker_wall_median_ns":statistics.median(x["wall_ns"] for x in payload["observations"]),
            "worker_cpu_median_ns":statistics.median(x["cpu_ns"] for x in payload["observations"])}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent-site",required=True,type=Path)
    ap.add_argument("--candidate-site",required=True,type=Path)
    ap.add_argument("--goldens",required=True,type=Path)
    ap.add_argument("--workspace",required=True,type=Path)
    ap.add_argument("--work-dir",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.work_dir.mkdir(parents=True,exist_ok=True)
    archives={}
    for mode,golden in (
        ("stored","v24-virtual-zip.json"),
        ("retained","v24-virtual-zip-deflate-mode1.json"),
    ):
        for count in (32,512,4096):
            path = args.work_dir / f"{mode}-{count}.cmpct"
            data = build_wire(args.goldens/golden,count)
            path.write_bytes(data)
            archives[(mode,count)]={"path":path,
                                    "sha256":hashlib.sha256(data).hexdigest(),
                                    "archive_bytes":len(data),
                                    "count":count,"mode":mode}

    records=[]
    sites={"parent":args.parent_site,"candidate":args.candidate_site}
    expected={"parent":BASE_VALIDATION_BLOB,"candidate":CANDIDATE_VALIDATION_BLOB}
    for mode in ("stored","retained"):
        for count in (32,512,4096):
            fixture=archives[(mode,count)]
            for cycle in range(2):
                for order,arm in enumerate(("parent","candidate","candidate","parent")):
                    result=run_worker(sites[arm],fixture["path"],count,args.workspace,
                                      expected[arm],10)
                    records.append({
                        "mode":mode,"count":count,"cycle":cycle,"order":order,
                        "arm":arm,"archive_sha256":fixture["sha256"],
                        "archive_bytes":fixture["archive_bytes"],**result,
                    })
            print(f"J24C07B_CASE_FINISHED={mode}/{count}",flush=True)
    summary={}
    passed=True
    for mode in ("stored","retained"):
        for count in (32,512,4096):
            samples=[r for r in records if r["mode"]==mode and r["count"]==count]
            assert [r["arm"] for r in samples]==["parent","candidate","candidate","parent"]*2
            control=[r for r in samples if r["arm"]=="parent"]
            candidate=[r for r in samples if r["arm"]=="candidate"]
            pwall=statistics.median(r["worker_wall_median_ns"] for r in control)
            cwall=statistics.median(r["worker_wall_median_ns"] for r in candidate)
            pcpu=statistics.median(r["worker_cpu_median_ns"] for r in control)
            ccpu=statistics.median(r["worker_cpu_median_ns"] for r in candidate)
            ratio_w=cwall/pwall
            ratio_c=ccpu/pcpu if pcpu else None
            ok=(ratio_w<=1.25 and ratio_c is not None and ratio_c<=1.25)
            if count==4096:passed=passed and ok
            summary[f"{mode}-{count}"]={
                "parent_median_wall_ns":pwall,"candidate_median_wall_ns":cwall,
                "candidate_over_parent_wall":ratio_w,
                "parent_median_cpu_ns":pcpu,"candidate_median_cpu_ns":ccpu,
                "candidate_over_parent_cpu":ratio_c,
                "economics_screen_pass":ok,
            }
    receipt={"schema":"j24c07b-abba-1","source":{"baseline":"0a128ff55c7ae0f14c6bdf019a81b40f0d894eff",
             "baseline_validation_blob":BASE_VALIDATION_BLOB,
             "candidate_validation_blob":CANDIDATE_VALIDATION_BLOB},
             "processes":len(records),"calls":sum(len(r["observations"]) for r in records),
             "order":["parent","candidate","candidate","parent"],
             "cycles":2,"repetitions":10,
             "archives":[{k:v for k,v in a.items() if k!="path"} for a in archives.values()],
             "raw":records,"summary":summary,
             "decision":"FOCUSED_ECONOMIC_SCREEN_PASS" if passed else "FOCUSED_ECONOMIC_SCREEN_FAIL",
             "release_credit":False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("J24C07B_DECISION="+receipt["decision"],flush=True)
    for key,value in summary.items():
        print("J24C07B_RATIO="+key+" wall="+str(round(value["candidate_over_parent_wall"],4))+
              " cpu="+str(round(value["candidate_over_parent_cpu"],4)),flush=True)


if __name__=="__main__":
    main()
