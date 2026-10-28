#!/usr/bin/env python3
"""J24G15 source-exact signed-MessagePack expansion court (research only).

Reuses the original J24G14 installed Reader three-arm worker and its
SHA/selection/range/verify court; does NOT change Reader or frozen evaluators.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import msgpack
import cmpct.reader as reader_module
from cmpct.builder import Builder
from cmpct.codec import FTR, FMAGIC, sha
from j24g12_lazy_ancestry_court import PAYLOAD, check_member
from j24g14_adaptive_ancestry_court import run_case, source_guard, RETAINED_RAW_BUDGET

PREREG="3f6dcb04422af2090917f6d421f343b6d7d5656a"
SOURCE="research/j24g15_msgpack_expansion_court.py"

def payloads():
    p={
      "empty":msgpack.packb({"blobs":[],"ops":[]},use_bin_type=True),
      "opaque":msgpack.packb({"blobs":[],"ops":[],"extension":b"z"*800000},use_bin_type=True),
      # Generate in a separate process; a parent-side 200k-object peak pollutes
      # ru_maxrss inherited by fork/exec benchmark workers on Linux.
      "nested":subprocess.check_output([__import__("sys").executable,"-c",
          "import msgpack,sys; sys.stdout.buffer.write(msgpack.packb("
          "{'blobs':[],'ops':[],'extension':[{'x':0} for _ in range(200000)]},"
          "use_bin_type=True))"])
    }
    assert abs(len(p["nested"])-len(p["opaque"]))<100
    assert all(len(v)<RETAINED_RAW_BUDGET for v in p.values())
    # Do not deserialize nested payload in the parent process.
    return p

def main():
    source_guard()
    assert subprocess.run(["git","merge-base","--is-ancestor",PREREG,"HEAD"]).returncode==0
    assert Path(SOURCE).read_bytes()==subprocess.check_output(["git","show","HEAD:"+SOURCE])
    out=Path(os.environ.get("J24G15_ARTIFACTS","j24g15-artifacts"))
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g15-") as td:
        root=Path(td); tree=root/"tree";tree.mkdir()
        (tree/"owner.bin").write_bytes(PAYLOAD)
        base_file=root/"base.cmpct"
        Builder(tree).build(base_file)
        with reader_module.CMPCT(base_file) as rdr:
            checkpoint=rdr.latest_footer_pos
            check_member(rdr,checkpoint,0,"owner.bin")
        base=base_file.read_bytes()
        cases={}; receipts={}
        for name,payload in payloads().items():
            f=root/(name+".cmpct")
            f.write_bytes(base+payload+FTR.pack(FMAGIC,1,0,0,0,len(payload),len(payload),0,sha(payload)))
            receipts[name]={"bytes":len(payload),"sha256":sha(payload).hex(),
                            "maps":200000 if name=="nested" else 0}
            cases[name]=run_case(name,f,checkpoint,0,"owner.bin",3,False)
            print("J24G15_CASE="+json.dumps({"case":name,"medians":cases[name]["median"],
                                             "payload_bytes":len(payload)},sort_keys=True))
        extra=cases["nested"]["median"]["adaptive"]["rss_kib"]-cases["opaque"]["median"]["adaptive"]["rss_kib"]
        similar=sum(abs(cases["nested"]["median"][a]["rss_kib"]-
                        cases["nested"]["median"]["adaptive"]["rss_kib"])<=4096
                    for a in ("eager","guarded","adaptive"))
        decision=("H1_CONFIRMED" if extra>=12288 and similar>=2 else "H1_NOT_CONFIRMED")
        result={"source_head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
                "prereg":PREREG,"reader_blob":"f13c5492f5acfa1cfcfec97cdbe0da71e41e327b",
                "raw_budget":RETAINED_RAW_BUDGET,"checkpoint":checkpoint,
                "payloads":receipts,"cases":cases,"nested_extra_rss_kib":extra,
                "nested_arms_within_4mib":similar,"decision":decision,
                "product_credit":False,"release_credit":0}
        (out/"court.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print("J24G15_RESULT="+json.dumps({"decision":decision,"nested_extra_rss_kib":extra,
                                          "nested_arms_within_4mib":similar},sort_keys=True))
if __name__=="__main__":
    main()
