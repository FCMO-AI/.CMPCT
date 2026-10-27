#!/usr/bin/env python3
"""O223 real r24 installed Reader futures-cost research-only A/B.
Preregistration fc1b0347. Candidate arms intentionally do NOT change Reader.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, importlib.util, json, os
from pathlib import Path
import random, resource, statistics, subprocess, sys, tempfile, time

REF_HEAD="c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
READER_BLOB="dbd4ac576a05a47eae97e1e40de89cf1de440516"
PREREG="fc1b0347f06ef746d253614b516ead241e29ebed"
NS=(4096,65536,262144)
KINDS=("fixed","cdc")
LAYOUTS=("repeat","eight")
ARMS=("eager","bounded512","bounded64","serial","open_only")
REPEATS=3

def sha(b):return hashlib.sha256(b).hexdigest()

def import_test(path):
    spec=importlib.util.spec_from_file_location("o223_"+path.stem,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

def fixture(root,kind,n,layout):
    if layout=="repeat":
        payloads=(b"Q",)
        refs=[0]*n
    elif layout=="eight":
        payloads=tuple(bytes((65+i,)) for i in range(8))
        refs=[(i*5+i//31)%8 for i in range(n)]
    else:raise ValueError(layout)
    expected=b"".join(payloads[idx] for idx in refs)
    if kind=="fixed":
        mod=import_test(root/"tests/test_o215_fixed_chunk_admission.py")
        wire=mod._make_archive(refs,expected,blobs=payloads)
    else:
        mod=import_test(root/"tests/test_o214_cdc_admission.py")
        wire=mod._r24([[1,idx] for idx in refs],expected,blobs=payloads)
    return wire,expected

def candidate(r,kind,arm):
    row=r.by["fixed.bin" if kind=="fixed" else "cdc.bin"]
    descriptors=row[6][1]
    if kind=="fixed":refs=descriptors
    else:refs=[entry[1] for entry in descriptors]
    if arm=="serial":
        output=b"".join(r._blob(index) for index in refs)
    elif arm.startswith("bounded"):
        limit=int(arm[len("bounded"):])
        # Importantly: no O(N)-futures submission, no skipped references.
        # Same pinned descriptor/index, same authenticated _blob and exact order.
        if r._executor is None:
            r._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))
        assembled=[]
        for lo in range(0,len(refs),limit):
            assembled.extend(r._executor.map(r._blob,refs[lo:lo+limit]))
        output=b"".join(assembled)
    else:raise ValueError(arm)
    if len(output)!=row[4] or sha(output)!=bytes(row[5]).hex():
        raise AssertionError("candidate exact size/SHA mismatch")
    return output

def child(args):
    from cmpct.reader import CMPCT
    start_all_wall=time.perf_counter_ns()
    start_all_cpu=time.process_time_ns()
    with CMPCT(Path(args.archive)) as reader:
        name="fixed.bin" if args.kind=="fixed" else "cdc.bin"
        if len(reader.by[name][6][1])!=args.n:raise AssertionError("wrong ref count")
        after_open_wall=time.perf_counter_ns()
        after_open_cpu=time.process_time_ns()
        if args.arm=="open_only":
            actual=b""
        elif args.arm=="eager":
            actual=reader.read(name)
        else:
            actual=candidate(reader,args.kind,args.arm)
        after_read_wall=time.perf_counter_ns()
        after_read_cpu=time.process_time_ns()
        if args.arm!="open_only":
            if sha(actual)!=args.expected_sha or len(actual)!=args.n:
                raise AssertionError("different logical output")
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({
        "kind":args.kind,"n":args.n,"layout":args.layout,"arm":args.arm,
        "expected_sha256":args.expected_sha,"actual_sha256":sha(actual) if args.arm!="open_only" else None,
        "read_wall_ms":(after_read_wall-after_open_wall)/1e6,
        "read_cpu_ms":(after_read_cpu-after_open_cpu)/1e6,
        "session_wall_ms":(after_read_wall-start_all_wall)/1e6,
        "session_cpu_ms":(after_read_cpu-start_all_cpu)/1e6,
        "open_wall_ms":(after_open_wall-start_all_wall)/1e6,
        "peak_rss_kib":peak,"archive_sha256":args.archive_sha,
        "py":sys.version.split()[0],"pid":os.getpid()
    },sort_keys=True))

def variable_payload_control(root,dir):
    from cmpct.reader import CMPCT
    sizes=(1,2,3,4,5,7,11)
    payloads=tuple(bytes([65+i])*sizes[i] for i in range(len(sizes)))
    refs=[(i*i+i*7+3)%len(sizes) for i in range(113)]
    original=b"".join(payloads[i] for i in refs)
    out=[]
    for kind in KINDS:
        if kind=="fixed":
            m=import_test(root/"tests/test_o215_fixed_chunk_admission.py")
            wire=m._make_archive(refs,original,blobs=payloads)
        else:
            m=import_test(root/"tests/test_o214_cdc_admission.py")
            wire=m._r24([[len(payloads[i]),i] for i in refs],original,blobs=payloads)
        path=dir/("variable-"+kind+".cmpct")
        path.write_bytes(wire)
        with CMPCT(path) as r:
            control=r.read("fixed.bin" if kind=="fixed" else "cdc.bin")
            assert control==original and r.verify()==1
            for arm in ("serial","bounded64","bounded512"):
                got=candidate(r,kind,arm)
                assert got==original
                out.append({"kind":kind,"arm":arm,"sha256":sha(got),"count":len(refs)})
    return out

def run(args):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    root=Path(args.workspace).resolve();out=Path(args.output).resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    rows=[];archives=[]
    with tempfile.TemporaryDirectory(prefix="o223-authenticated-") as td:
        root_temp=Path(td)
        variable=variable_payload_control(root,root_temp)
        for kind in KINDS:
            for layout in LAYOUTS:
                for n in NS:
                    wire,expected=fixture(root,kind,n,layout)
                    path=root_temp/f"{kind}-{layout}-{n}.cmpct"
                    path.write_bytes(wire)
                    assert preflight_archive(path,verify_blob_headers=True)["files"]==1
                    with CMPCT(path) as r:
                        # Independent exact logical control, outside measured samples.
                        assert r.verify()==1
                        assert r.read("fixed.bin" if kind=="fixed" else "cdc.bin")==expected
                    archives.append({"kind":kind,"layout":layout,"n":n,
                                     "archive_bytes":len(wire),"archive_sha256":sha(wire),
                                     "logical_sha256":sha(expected)})
                    for rep in range(args.repeats):
                        order=list(ARMS)
                        random.Random(223000+n+rep*13+len(kind)+len(layout)).shuffle(order)
                        for arm in order:
                            command=[sys.executable,__file__,"--child","--archive",str(path),
                                     "--kind",kind,"--layout",layout,"--n",str(n),
                                     "--arm",arm,"--expected-sha",sha(expected),
                                     "--archive-sha",sha(wire)]
                            start=time.perf_counter_ns()
                            proc=subprocess.run(command,capture_output=True,text=True,check=False)
                            outer=(time.perf_counter_ns()-start)/1e6
                            if proc.returncode:
                                raise RuntimeError(f"failed {kind}/{layout}/{n}/{arm}: {proc.stdout} {proc.stderr}")
                            rec=json.loads(proc.stdout.strip().splitlines()[-1])
                            assert rec["expected_sha256"]==sha(expected)
                            assert rec["archive_sha256"]==sha(wire)
                            rec.update({"rep":rep,"process_wall_ms":outer})
                            rows.append(rec)
                        print("PROGRESS",kind,layout,n,rep,flush=True)
    summaries=[]
    for kind in KINDS:
        for layout in LAYOUTS:
            for n in NS:
                arm_results={}
                for arm in ARMS:
                    samples=[s for s in rows if s["kind"]==kind and s["layout"]==layout and
                             s["n"]==n and s["arm"]==arm]
                    assert len(samples)==args.repeats
                    arm_results[arm]={key:statistics.median(s[key] for s in samples)
                                       for key in ("read_wall_ms","read_cpu_ms","session_wall_ms",
                                                   "session_cpu_ms","peak_rss_kib")}
                eager=arm_results["eager"];bounded=arm_results["bounded512"]
                summaries.append({"kind":kind,"layout":layout,"n":n,"arms":arm_results,
                                  "bounded_rss_save_mib":(eager["peak_rss_kib"]-bounded["peak_rss_kib"])/1024,
                                  "bounded_session_wall_ratio":bounded["session_wall_ms"]/eager["session_wall_ms"],
                                  "serial_session_wall_ratio":arm_results["serial"]["session_wall_ms"]/eager["session_wall_ms"]})
    decisive=[r for r in summaries if r["n"]==262144]
    passed=(len(decisive)==4 and all(r["bounded_rss_save_mib"]>=128.0 and
             r["bounded_session_wall_ratio"]<=1.10 for r in decisive))
    decision="BOUND_FUTURE_HWM_MATERIAL" if passed else "BOUND_FUTURE_PRODUCT_HEADROOM_NOT_PROVEN"
    report={"schema":"o223-r24-futures-rss-v1","scope":"installed genuine Reader; out-of-tree candidate; not product",
            "source_parent":REF_HEAD,"reader_blob":READER_BLOB,"prereg_commit":PREREG,
            "runner":sys.version,"archives":archives,"variable_payload_control":variable,
            "samples":rows,"summary":summaries,"decision":decision,
            "limitations":"RAW tiny member profiles; no Zstd/Deflate, Windows/macOS, true product patch, official release gate, mutable source, journal and fs payload semantics."}
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("DECISION",decision,flush=True)
    for r in decisive:
        print("DECISIVE",r["kind"],r["layout"],round(r["bounded_rss_save_mib"],2),
              round(r["bounded_session_wall_ratio"],4),round(r["serial_session_wall_ratio"],4),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--child",action="store_true")
    p.add_argument("--workspace",default=os.getenv("GITHUB_WORKSPACE","."))
    p.add_argument("--output")
    p.add_argument("--archive");p.add_argument("--kind",choices=KINDS)
    p.add_argument("--layout",choices=LAYOUTS);p.add_argument("--n",type=int)
    p.add_argument("--arm",choices=ARMS);p.add_argument("--expected-sha");p.add_argument("--archive-sha")
    p.add_argument("--repeats",type=int,default=REPEATS)
    args=p.parse_args()
    if args.child:child(args)
    else:
        if not args.output:p.error("--output is required")
        run(args)
