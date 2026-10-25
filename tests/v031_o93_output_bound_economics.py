"""O93 small authentic-Builder A/B economics; research rung, NEVER release parity.

Same input tree and same installed codec/runtime per host, source-exact O90
Builder versus O93. Separate from process startup; no fsync or cold-cache claim.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from cmpct.core import Builder, CMPCT

O90="1beb733da61da8e1c562e7c3190b1f18f1cc45d1"
O90_BLOB="bfb37fcd06e6ff05742606ece365348150f477fc"


def original_builder():
    source=subprocess.check_output(["git","show",f"{O90}:src/cmpct/builder.py"])
    blob=subprocess.run(["git","hash-object","--stdin"],input=source,stdout=subprocess.PIPE,check=True).stdout.decode().strip()
    assert blob==O90_BLOB,(blob,O90_BLOB)
    spec=importlib.util.spec_from_loader("cmpct._o90_economics_exact",loader=None)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    exec(compile(source.decode(),f"{O90}/src/cmpct/builder.py","exec"),module.__dict__)
    return module.Builder


def cases(base):
    tiny=base/"tiny"
    tiny.mkdir()
    for i in range(25):
        (tiny/f"entry_{i:03d}.txt").write_bytes((b"ABCD0123"*17)+bytes([i]))
    mixed=base/"mixed"
    mixed.mkdir()
    (mixed/"structured.log").write_bytes((b"json-key: %04d value=true\n"*1000)[:200000])
    (mixed/"noise.bin").write_bytes(hashlib.shake_256(b"O93 pinned economic workload").digest(131072))
    (mixed/"repeated.bin").write_bytes(b"ABCDEFGH"*32768)
    return {"tiny25":tiny,"mixed3":mixed}


def run_one(cls,tree,target):
    start_cpu=time.process_time_ns()
    start_wall=time.perf_counter_ns()
    result=cls(tree,workers=1,reproducible=True).build(target)
    wall_ms=(time.perf_counter_ns()-start_wall)/1e6
    cpu_ms=(time.process_time_ns()-start_cpu)/1e6
    assert result["bytes"]==target.stat().st_size
    return {"wall_ms":wall_ms,"cpu_ms":cpu_ms,"bytes":result["bytes"],
            "sha256":hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    baseline=original_builder()
    with tempfile.TemporaryDirectory(prefix="cmpct-o93-economic-") as d:
        base=Path(d)
        observed=[]
        for label,tree in cases(base).items():
            old=base/f"{label}.o90.cmpct"
            new=base/f"{label}.o93.cmpct"
            old.write_bytes(b"existing-output")
            new.write_bytes(b"existing-output")
            rows={"o90":[],"o93":[]}
            for rep in range(5):
                seq=[("o90",baseline,old),("o93",Builder,new)]
                if rep%2:seq.reverse()
                pair={}
                for arm,cls,target in seq:
                    pair[arm]=run_one(cls,tree,target)
                    rows[arm].append(pair[arm])
                assert old.read_bytes()==new.read_bytes(),(label,rep,pair)
                assert pair["o90"]["bytes"]==pair["o93"]["bytes"]
                assert pair["o90"]["sha256"]==pair["o93"]["sha256"]
            with CMPCT(new) as a:
                a.verify()
                if label=="tiny25":
                    assert a.read("entry_003.txt")== (tree/"entry_003.txt").read_bytes()
                else:
                    assert a.read("noise.bin")== (tree/"noise.bin").read_bytes()
            summary={arm:{metric+"_median":statistics.median(x[metric] for x in vals)
                          for metric in ("wall_ms","cpu_ms")} for arm,vals in rows.items()}
            summary["delta_wall_ms"]=summary["o93"]["wall_ms_median"]-summary["o90"]["wall_ms_median"]
            summary["delta_cpu_ms"]=summary["o93"]["cpu_ms_median"]-summary["o90"]["cpu_ms_median"]
            observed.append({"case":label,"repetitions":5,"original_source_sha":O90,
                             "original_blob":O90_BLOB,"identical_archive_bytes":True,
                             "bytes":rows["o93"][0]["bytes"],"sha256":rows["o93"][0]["sha256"],
                             "observations":rows,"summary":summary})
    print("O93_ACTUAL_BUILDER_ECONOMICS="+json.dumps({"platform":sys.platform,
           "python":sys.version.split()[0],"timing_boundary":"Builder.build; no process startup; warm host",
           "scope":"small synthetic installed single-worker A/B; not official release parity",
           "cases":observed},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
