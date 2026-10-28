#!/usr/bin/env python3
"""J24C10 product-level installed-wheel paired late/early selective read court.

Original native admission stays enabled in both arms. Only the NEW private
range-time witness is disabled in the control. No score is a release claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from test_o215_fixed_chunk_admission import _make_archive


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture(n, family):
    if family == "one":
        blobs = (b"ABCD",)
        refs = [0] * n
    elif family == "owners256":
        blobs = tuple(bytes([i]) * 4 for i in range(256))
        refs = [i % 256 for i in range(n)]
    elif family == "ragged":
        blobs = (b"ABCD", b"F", b"XY")
        refs = [i % 3 for i in range(n)]
    else:
        raise AssertionError(family)
    logical = b"".join(blobs[idx] for idx in refs)
    wire = _make_archive(refs, logical, blobs=blobs)
    return wire, logical, len(blobs)


def worker(args):
    # Separate process, same wheel, identical signed archive for both arms.
    import cmpct._chunk_admission as admission
    from cmpct.reader import CMPCT
    from pathlib import Path
    import time
    native = admission._uniform_stride
    if not callable(native):
        raise RuntimeError("J24C10 installed binary witness missing")
    if args.arm == "strict":
        admission._uniform_stride = None
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    with CMPCT(Path(args.archive)) as reader:
        t1 = time.perf_counter_ns()
        c1 = time.process_time_ns()
        size = reader.files[0][4]
        start = size - 32 if args.position == "late" else 12
        length = min(16, size - start)
        result = reader.read_range("fixed.bin", start, length)
        t2 = time.perf_counter_ns()
        c2 = time.process_time_ns()
        cache = reader._chunk_stride_cache.get("fixed.bin")
    t3 = time.perf_counter_ns()
    c3 = time.process_time_ns()
    if os.name != "nt":
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    else:
        rss = None
    return dict(arm=args.arm,position=args.position,wire_sha256=sha(Path(args.archive).read_bytes()),
                result_sha256=sha(result),size=size,start=start,length=length,
                open_wall_ns=t1-t0,read_wall_ns=t2-t1,total_wall_ns=t3-t0,
                open_cpu_ns=c1-c0,read_cpu_ns=c2-c1,total_cpu_ns=c3-c0,
                rss_raw=rss,proof_cache=cache,native_installed=callable(native))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--archive")
    ap.add_argument("--arm", choices=("strict","witness"))
    ap.add_argument("--position", choices=("early","late"))
    ap.add_argument("--output")
    ap.add_argument("--repetitions",type=int,default=6)
    args=ap.parse_args()
    if args.worker:
        print(json.dumps(worker(args),sort_keys=True))
        return
    assert args.output
    import cmpct.reader as reader
    import cmpct._chunk_admission as admission
    if admission._uniform_stride is None:
        raise RuntimeError("installed package lacks native J24C10 function")
    path = Path(reader.__file__).resolve()
    if "site-packages" not in path.parts and "dist-packages" not in path.parts:
        raise RuntimeError("not running installed Reader: " + str(path))
    run=[]
    with tempfile.TemporaryDirectory(prefix="j24c10-court-") as td:
        root=Path(td)
        for n in (65536,262144):
            for family in ("one","owners256","ragged"):
                wire,logical,owners=fixture(n,family)
                archive=root/f"{n}-{family}.cmpct"
                archive.write_bytes(wire)
                hash_wire=sha(wire)
                for position in ("early","late"):
                    start=len(logical)-32 if position=="late" else 12
                    expected=sha(logical[start:start+16])
                    for k in range(args.repetitions):
                        order=("strict","witness") if k%2==0 else ("witness","strict")
                        for arm in order:
                            command=[sys.executable,str(Path(__file__).resolve()),
                                     "--worker","--archive",str(archive),
                                     "--position",position,"--arm",arm]
                            wall=time.perf_counter_ns()
                            child=subprocess.run(command,capture_output=True,text=True,check=True)
                            full=time.perf_counter_ns()-wall
                            item=json.loads(child.stdout)
                            assert item["wire_sha256"]==hash_wire
                            assert item["result_sha256"]==expected, (n,family,position,arm)
                            if family!="ragged" and position=="late" and arm=="witness":
                                assert item["proof_cache"]==4, item
                            item.update(n=n,family=family,owners=owners,repeat=k,
                                        process_wall_ns=full,source_wire_sha256=hash_wire)
                            run.append(item)
    group={}
    for x in run:
        key=f'{x["n"]}/{x["family"]}/{x["position"]}'
        group.setdefault(key,{}).setdefault(x["arm"],[]).append(x)
    summary={}
    import platform
    host=platform.system()
    rss_unit=1 if host=="Linux" else (1024 if host=="Darwin" else None)
    for key, arms in group.items():
        a=statistics.median(z["read_wall_ns"] for z in arms["strict"])
        b=statistics.median(z["read_wall_ns"] for z in arms["witness"])
        ac=statistics.median(z["read_cpu_ns"] for z in arms["strict"])
        bc=statistics.median(z["read_cpu_ns"] for z in arms["witness"])
        rss_delta=None
        if rss_unit is not None and all(z["rss_raw"] is not None
                for xs in arms.values() for z in xs):
            rs=statistics.median(z["rss_raw"] for z in arms["strict"])
            rw=statistics.median(z["rss_raw"] for z in arms["witness"])
            rss_delta=(rw-rs)*rss_unit/(1024*1024)
        summary[key]={"strict_median_read_ns":a,"witness_median_read_ns":b,
                      "ratio_strict_over_witness":a/b if b else None,
                      "strict_median_cpu_ns":ac,"witness_median_cpu_ns":bc,
                      "cpu_ratio":ac/bc if bc else None,
                      "peak_rss_delta_mib":rss_delta}
    late_keys=[f'{n}/{family}/late' for n in (65536,262144)
                for family in ("one","owners256")]
    wall_gate=all(summary[k]["ratio_strict_over_witness"]>=2.0 for k in late_keys)
    cpu_direction=all(summary[k]["cpu_ratio"]>1.0 for k in late_keys)
    negative_keys=[k for k in summary if k.endswith("/early") or "/ragged/" in k]
    no_early_or_ragged_debt=all(summary[k]["ratio_strict_over_witness"]>=1/1.05
                                for k in negative_keys)
    rss_measured=all(summary[k]["peak_rss_delta_mib"] is not None for k in summary)
    rss_gate=rss_measured and all(summary[k]["peak_rss_delta_mib"]<=8.0 for k in summary)
    decision=wall_gate and cpu_direction and no_early_or_ragged_debt and rss_gate
    payload={"schema":"j24c10-installed-range-v1",
             "utc_created":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
             "source_head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
             "reader_sha256":sha(path.read_bytes()),"python":sys.version,
             "repetitions":args.repetitions,"records":run,"summary":summary,
             "late_four_profile_wall_gate":wall_gate,
             "late_four_profile_cpu_direction":cpu_direction,
             "early_ragged_no_gt5pct_debt":no_early_or_ragged_debt,
             "rss_measured":rss_measured,"rss_no_gt8mib_debt":rss_gate if rss_measured else None,
             "scientific_gate_all_preregistered":decision,
             "memory_caveat":"Child VmHWM/resource RSS includes package startup; Windows unavailable",
             "product_release_credit":False}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("J24C10_HONEST_RESULT",len(run),"workers",json.dumps(summary,sort_keys=True),"gate",decision)


if __name__=="__main__":
    main()
