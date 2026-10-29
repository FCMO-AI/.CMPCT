#!/usr/bin/env python3
"""Independent Linux fork+exec ru_maxrss vs VmHWM discriminator; no CMPCT imports."""
from __future__ import annotations
import json, os, pathlib, resource, subprocess, sys

CHILD = """import json, pathlib, resource
s=pathlib.Path("/proc/self/status").read_text()
d={k.strip():int(v.strip().split()[0]) for k,v in
 (line.split(":",1) for line in s.splitlines() if line.startswith(("VmHWM:","VmRSS:")))}
print(json.dumps({"child_ru_maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 "child_proc_vm_kib":d},sort_keys=True))
"""

def child():
    got=subprocess.run([sys.executable,"-c",CHILD],capture_output=True,text=True,check=True,timeout=30)
    return json.loads(got.stdout)

def main():
    baseline_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    before=child()
    touched=bytearray(160*1024*1024)
    for i in range(0,len(touched),4096):touched[i]=1
    raised_parent=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    del touched
    after=child()
    result={"schema":"cmpct-j24m01e-rusage-exec-inheritance-v1","platform":sys.platform,
     "baseline_parent_kib":baseline_parent,"raised_parent_kib":raised_parent,
     "before":before,"after":after,"product_code_imported":False,"release_credit":0,
     "child_peak_vs_proc_gap_kib": after["child_ru_maxrss_kib"]-after["child_proc_vm_kib"]["VmHWM"]}
    print(json.dumps(result,sort_keys=True))
    if raised_parent<baseline_parent+100*1024:raise AssertionError("parent memory not raised")
    if after["child_ru_maxrss_kib"]<raised_parent-8192:raise AssertionError("exec ru_maxrss not inherited")
    if after["child_ru_maxrss_kib"]-after["child_proc_vm_kib"]["VmHWM"]<100*1024:
        raise AssertionError("no direct ru_maxrss vs child VmHWM disagreement")

if __name__=="__main__":main()
