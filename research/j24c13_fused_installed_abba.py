"""J24C13 installed-Reader exact-input A/B court (research, not release authority).

Same installed wheel and signed wire, true independent child processes, only
the optional index-bearing ABI3 entrypoint toggled. Open/read/CPU/process-start
are separated. For published Reader parity use the distinct J24C12 baseline.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time

def sha(data):
    return hashlib.sha256(data).hexdigest()

def worker(cfg, arm):
    import cmpct.reader
    import cmpct._chunk_admission as admission
    from cmpct.reader import CMPCT
    p=Path(cfg["archive"])
    assert sha(p.read_bytes()) == cfg["archive_sha256"]
    assert "site-packages" in Path(cmpct.reader.__file__).parts or "dist-packages" in Path(cmpct.reader.__file__).parts
    assert admission._scan_refs is not None and admission._scan_refs_index is not None, "missing installed ABI3"
    if arm=="native-original":
        admission._scan_refs_index = None
    elif arm!="fused":
        raise ValueError(arm)
    open_wall=time.perf_counter_ns();open_cpu=time.process_time_ns()
    with CMPCT(p) as rd:
        opened_wall=time.perf_counter_ns();opened_cpu=time.process_time_ns()
        marks=rd._chunk_range_marks.get("fixed.bin")
        assert (marks is not None)==(arm=="fused"), (arm,marks)
        assert (len(marks)==(cfg["n"]+255)//256) if marks is not None else True
        out=[]
        for start,length,digest in cfg["queries"]:
            result=rd.read_range("fixed.bin",start,length)
            assert sha(result)==digest, (arm,start,length)
            out.append(result)
        done_wall=time.perf_counter_ns();done_cpu=time.process_time_ns()
    return dict(
        arm=arm,case=cfg["case"],q=len(cfg["queries"]),
        open_wall_ns=opened_wall-open_wall,read_wall_ns=done_wall-opened_wall,
        session_wall_ns=done_wall-open_wall,open_cpu_ns=opened_cpu-open_cpu,
        read_cpu_ns=done_cpu-opened_cpu,session_cpu_ns=done_cpu-open_cpu,
        digest=sha(b"".join(out)),index_count=len(marks) if marks is not None else 0,
        archive_sha256=cfg["archive_sha256"],installed_reader=cmpct.reader.__file__,
        python=sys.version.split()[0],host=platform.platform(),
    )

def run(output, repetitions):
    import cmpct.reader
    import cmpct._chunk_admission as admission
    assert admission._scan_refs is not None and admission._scan_refs_index is not None
    from test_o215_fixed_chunk_admission import _make_archive
    raw=[]
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c13-court-") as td:
        root=Path(td)
        for n in (65536,262144):
            for family,blobs in (("fixed",[b"A"]),("hetero",[b"A",b"BC",b"DEF"])):
                refs=[i%len(blobs) for i in range(n)]
                logical=b"".join(blobs[i] for i in refs)
                archive=_make_archive(refs,logical,blobs=tuple(blobs))
                path=root/f"{family}-{n}.cmpct";path.write_bytes(archive)
                for q in (1,6,32):
                    # Same queries and hash expectations for both arms, with
                    # deterministic early, interior, late and random positions.
                    rnd=random.Random(241300 + n + q + len(blobs))
                    queries=[]
                    starts=[0,len(logical)//2,max(0,len(logical)-1)]
                    while len(starts)<q:
                        starts.append(rnd.randrange(len(logical)+1))
                    for start in starts[:q]:
                        length=min(1+(start%7),len(logical)-start)
                        queries.append((start,length,sha(logical[start:start+length])))
                    cfg=dict(case=f"{family}-{n}-q{q}",n=n,archive=str(path),
                             archive_sha256=sha(archive),queries=queries)
                    manifest=root/(cfg["case"]+".json")
                    manifest.write_text(json.dumps(cfg),encoding="utf-8")
                    for iteration in range(repetitions):
                        order=("native-original","fused") if iteration%2==0 else ("fused","native-original")
                        for arm in order:
                            t0=time.perf_counter_ns()
                            result=subprocess.run(
                                [sys.executable,__file__,"--worker",str(manifest),arm],
                                text=True,capture_output=True,check=False,
                            )
                            t1=time.perf_counter_ns()
                            if result.returncode:
                                raise RuntimeError(f"{cfg['case']} {arm}: {result.stderr}\n{result.stdout}")
                            row=json.loads(result.stdout)
                            row.update(iteration=iteration,process_wall_ns=t1-t0,
                                       source_head=os.getenv("EVIDENCE_SHA","UNBOUND"))
                            raw.append(row)
    summary=[]
    for case in sorted({r["case"] for r in raw}):
        d={arm:[r for r in raw if r["case"]==case and r["arm"]==arm]
           for arm in ("native-original","fused")}
        for field in ("session_wall_ns","session_cpu_ns","open_wall_ns","read_wall_ns","process_wall_ns"):
            base=statistics.median(r[field] for r in d["native-original"])
            fused=statistics.median(r[field] for r in d["fused"])
            summary.append(dict(case=case,field=field,original_ns=base,fused_ns=fused,
                                speedup=base/fused if fused else None))
    decision="MICRO_INSTALLED_RESULT_ONLY_NO_RELEASE_CREDIT"
    data=dict(schema="j24c13-installed-abba-v1",source_head=os.getenv("EVIDENCE_SHA","UNBOUND"),
              baseline="#641 installed native original (same wheel, index helper disabled)",
              distinction="fresh child process; open/read/CPU separate from measured parent subprocess wall",
              repetition=repetitions,raw=raw,summary=summary,decision=decision)
    Path(output).write_text(json.dumps(data,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(dict(decision=decision,observations=len(raw),groups=len(summary)//5,
                          summary=[s for s in summary if s["field"]=="session_wall_ns"]),sort_keys=True))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--worker",nargs=2)
    parser.add_argument("--output",default="j24c13-receipt.json")
    parser.add_argument("--repetitions",type=int,default=3)
    a=parser.parse_args()
    if a.worker: print(json.dumps(worker(json.loads(Path(a.worker[0]).read_text()),a.worker[1])))
    else:run(a.output,a.repetitions)
